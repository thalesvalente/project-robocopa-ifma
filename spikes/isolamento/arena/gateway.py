"""I2 trusted, bot-only protocol gateway. Engine remains unmodified.

Private fixed upstream only. Never run as public/student-facing production API.
"""
from __future__ import annotations
from collections import Counter
import json
import logging
import threading
from websockets.sync.client import connect
from websockets.sync.server import serve
from websockets.exceptions import ConnectionClosed
from arena_protocol import decode,handshake,intent,BOT_OUTPUT_TYPES,ProtocolDenied,MAX_MESSAGE,SessionBudget,BudgetLimits

QUIET=logging.getLogger('robocopa.i2.ws');QUIET.disabled=True

class BotGateway:
    def __init__(self,identities,upstream_secret,port=7654,upstream='ws://127.0.0.1:7655',limits=None):
        self.limits=limits if limits is not None else BudgetLimits()
        self.identities=identities
        self.secret=upstream_secret
        self.port=port
        self.upstream=upstream
        self.lock=threading.Lock()
        self.active=set()
        self.connections=set()
        self.budget=threading.BoundedSemaphore(8)
        self.counts=Counter()
        self.server=None
    def count(self,key):
        with self.lock:self.counts[key]+=1
    def handle(self,client):
        if not self.budget.acquire(blocking=False):
            client.close(1008,'CAPACITY');return
        identity=None
        session_budget=SessionBudget(self.limits)
        try:
            with self.lock:self.connections.add(client)
            if client.request.path!='/':raise ProtocolDenied('PATH_DENIED')
            with connect(self.upstream,open_timeout=3,close_timeout=1,max_size=2*1024**2,
                         max_queue=16,compression=None,proxy=None,logger=QUIET) as upstream:
                greeting=decode(upstream.recv(timeout=3),limit=2*1024**2)
                if greeting['type']!='ServerHandshake':raise ProtocolDenied('SERVER_HANDSHAKE_REQUIRED')
                greeting_text=json.dumps(greeting)
                session_budget.accept_output(greeting_text);client.send(greeting_text)
                first=client.recv(timeout=min(4,session_budget.wait_timeout()))
                session_budget.accept(first)
                identity,body=handshake(first,session=greeting['sessionId'],
                    identities=self.identities,upstream_secret=self.secret)
                with self.lock:
                    if identity in self.active:
                        identity=None
                        raise ProtocolDenied('IDENTITY_BUSY')
                    self.active.add(identity)
                upstream.send(json.dumps(body))
                self.count('accepted_handshake')
                def forward_engine():
                    try:
                        for raw in upstream:
                            item=decode(raw,limit=2*1024**2)
                            if item['type'] not in BOT_OUTPUT_TYPES:
                                raise ProtocolDenied('ENGINE_EVENT_DENIED')
                            session_budget.accept_output(raw)
                            client.send(raw)
                    except ProtocolDenied as e:
                        self.count(str(e));client.close(1008,str(e))
                    except (ConnectionClosed,OSError):pass
                    finally:client.close()
                thread=threading.Thread(target=forward_engine,daemon=True)
                thread.start()
                try:
                    while True:
                        try:raw=client.recv(timeout=session_budget.wait_timeout())
                        except TimeoutError:
                            session_budget.wait_timeout()
                            raise ProtocolDenied('IDLE_LIMIT') from None
                        session_budget.accept(raw)
                        message=intent(raw)
                        upstream.send(json.dumps(message,allow_nan=False))
                        self.count(message['type'])
                except ProtocolDenied as e:
                    self.count(str(e));client.close(1008,str(e))
                finally:
                    upstream.close();thread.join(timeout=3)
        except ProtocolDenied as e:
            self.count(str(e));client.close(1008,str(e))
        except (ConnectionClosed,OSError,TimeoutError,ValueError):
            self.count('CONNECTION_ENDED');client.close(1008,'SESSION_ENDED')
        finally:
            with self.lock:
                self.connections.discard(client)
                if identity:self.active.discard(identity)
            self.budget.release()
    def start(self):
        self.server=serve(self.handle,'0.0.0.0',self.port,compression=None,
            open_timeout=3,close_timeout=1,ping_interval=20,ping_timeout=10,
            max_size=MAX_MESSAGE,max_queue=8,logger=QUIET,server_header=None)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
    def close(self):
        with self.lock:connections=list(self.connections)
        for sock in connections:sock.close(1001,'END')
        if self.server:self.server.shutdown();self.thread.join(timeout=3)
    def report(self):
        with self.lock:return dict(self.counts)
