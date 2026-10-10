"""Loopback WebSocket tests with fake engines, not real battle evidence."""
import json
import queue
import threading
import time
import unittest
from test_gateway import GatewayTests as _Helpers
from gateway import BotGateway, QUIET
from arena_protocol import BudgetLimits, MAX_MESSAGE
from websockets.sync.server import serve
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosed

CONTROL_TYPES=('StartGame','StopGame','PauseGame','ResumeGame','ChangeTps','NextTurn',
               'ControllerHandshake','ObserverHandshake','BotPolicyUpdate','EnableDebugMode','DisableDebugMode')

class ReconciliationGatewayTests(unittest.TestCase):
    setUp=_Helpers.setUp
    tearDown=_Helpers.tearDown
    connect=_Helpers.connect
    valid_handshake=_Helpers.valid_handshake
    assert_denied=_Helpers.assert_denied
    def drained(self):
        with self.gateway.drained:
            self.assertTrue(self.gateway.drained.wait_for(lambda:not self.gateway.connections,timeout=3))
    def test_all_control_types_before_and_after_handshake(self):
        for kind in CONTROL_TYPES:
            for authenticate in (False,True):
                with self.subTest(kind=kind,authenticate=authenticate),self.connect() as ws:
                    if authenticate:self.valid_handshake(ws);self.received.get(timeout=2)
                    ws.send(json.dumps({'type':kind}));self.assert_denied(ws)
                self.drained();self.assertTrue(self.received.empty())
    def test_reconnect_releases_identity_after_denial(self):
        with self.connect() as ws:
            self.valid_handshake(ws);self.received.get(timeout=2)
            ws.send('{"type":"StopGame"}');self.assert_denied(ws)
        self.drained()
        with self.connect() as ws:
            self.valid_handshake(ws);self.received.get(timeout=2)
            ws.send('{"type":"BotReady"}')
            self.assertEqual(json.loads(ws.recv(timeout=2))['type'],'RoundStartedEvent')
    def test_cross_identity_and_session_never_forwarded(self):
        for key,value in (('name','Spin Bot'),('sessionId','wrong'),('version','2.0')):
            with self.subTest(key=key),self.connect() as ws:
                item={'type':'BotHandshake','sessionId':'test-session','name':'Walls','version':'1.0','secret':'TEST_TOKEN'}
                item[key]=value;ws.send(json.dumps(item));self.assert_denied(ws)
            self.drained();self.assertTrue(self.received.empty())
    def test_bad_json_after_auth_never_forwarded(self):
        for raw in ('{"type":"BotReady","type":"StopGame"}',
                    '{"type":"BotIntent","targetSpeed":1e999}',
                    '{"type":"BotIntent","targetSpeed":true}',
                    '{"type":"TeamMessage"}','{"type":"BotIntent","teamMessages":[{}]}'):
            with self.subTest(raw=raw),self.connect() as ws:
                self.valid_handshake(ws);self.received.get(timeout=2)
                ws.send(raw);self.assert_denied(ws)
            self.drained();self.assertTrue(self.received.empty())
    def test_large_websocket_message_is_closed(self):
        with self.connect() as ws:
            ws.send('x'*(MAX_MESSAGE+1))
            with self.assertRaises(ConnectionClosed) as error:ws.recv(timeout=3)
            self.assertEqual(error.exception.rcvd.code,1009)
        self.drained();self.assertTrue(self.received.empty())
    def test_wrong_path_never_opens_engine_session(self):
        with connect(f'ws://127.0.0.1:{self.port}/other',proxy=None,compression=None,logger=QUIET) as ws:
            self.assert_denied(ws)
        self.drained();self.assertTrue(self.received.empty())
    def test_capacity_exhaustion_and_recovery(self):
        held=[]
        try:
            for _ in range(8):held.append(self.connect())
            with connect(f'ws://127.0.0.1:{self.port}',proxy=None,compression=None,logger=QUIET) as ws:
                self.assert_denied(ws)
            self.assertEqual(len(self.gateway.connections),8)
        finally:
            for ws in held:ws.close()
        self.drained()
        with self.connect() as ws:
            self.valid_handshake(ws);self.received.get(timeout=2)
    def test_session_lifetime_not_extended_by_valid_input(self):
        self.gateway.limits=BudgetLimits(lifetime_seconds=.2,idle_seconds=1)
        with self.connect() as ws:
            self.valid_handshake(ws);self.received.get(timeout=2)
            ws.send('{"type":"BotReady"}');ws.recv(timeout=2);self.received.get(timeout=2)
            self.assert_denied(ws)
        self.drained();self.assertEqual(self.gateway.report()['SESSION_LIMIT'],1)
    def test_shutdown_drains_active_socket_and_identity(self):
        with self.connect() as ws:
            self.valid_handshake(ws);self.received.get(timeout=2)
            self.gateway.close()
            with self.assertRaises(ConnectionClosed):ws.recv(timeout=2)
        self.assertTrue(self.gateway.stopping)
        self.assertFalse(self.gateway.connections);self.assertFalse(self.gateway.active)
        self.assertFalse(self.gateway.thread.is_alive())


class ReconciliationUpstreamTests(unittest.TestCase):
    def test_invalid_engine_greeting_is_fail_closed(self):
        for greeting in ('{"type":"ServerHandshake","sessionId":"s","version":"other"}',
                         '{"type":"ServerHandshake","version":"1.4.0"}',
                         '{"type":"ControllerHandshake"}'):
            received=queue.Queue()
            def fake(ws):
                try:
                    ws.send(greeting)
                    for raw in ws:received.put(raw)
                except ConnectionClosed:pass
            server=serve(fake,'127.0.0.1',0,logger=QUIET,close_timeout=1)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            gateway=BotGateway({'TOKEN':('Walls','1.0')},'ENGINE',port=0,
                               upstream=f'ws://127.0.0.1:{server.socket.getsockname()[1]}')
            gateway.start()
            try:
                with connect(f'ws://127.0.0.1:{gateway.server.socket.getsockname()[1]}',proxy=None,logger=QUIET) as ws:
                    with self.assertRaises(ConnectionClosed) as error:ws.recv(timeout=3)
                    self.assertEqual(error.exception.rcvd.code,1008)
                self.assertTrue(received.empty())
            finally:gateway.close();server.shutdown();thread.join(timeout=3)


del _Helpers

if __name__=='__main__':unittest.main()
