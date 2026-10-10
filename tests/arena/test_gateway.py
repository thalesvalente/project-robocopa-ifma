"""Real loopback WebSocket transport against a FAKE engine, NOT battle evidence."""
import json,queue,sys,threading,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'spikes/isolamento/arena'),str(ROOT/'services/worker_agent')]
from gateway import BotGateway,QUIET
from websockets.sync.server import serve
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosed

class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.received=queue.Queue()
        def fake(ws):
            try:
                ws.send('{"type":"ServerHandshake","sessionId":"test-session","version":"1.4.0"}')
                for raw in ws:
                    data=json.loads(raw);self.received.put(data)
                    if data['type']=='BotReady':ws.send('{"type":"RoundStartedEvent","roundNumber":1}')
                    elif data['type']=='BotIntent':ws.send('{"type":"TickEventForBot","turnNumber":1}')
            except ConnectionClosed:pass
        self.fake=serve(fake,'127.0.0.1',0,logger=QUIET,compression=None,close_timeout=1)
        self.thread=threading.Thread(target=self.fake.serve_forever,daemon=True);self.thread.start()
        port=self.fake.socket.getsockname()[1]
        self.gateway=BotGateway({'TEST_TOKEN':('Walls','1.0')},'RAW_ENGINE_SECRET',port=0,upstream=f'ws://127.0.0.1:{port}')
        self.gateway.start();self.port=self.gateway.server.socket.getsockname()[1]
    def tearDown(self):
        self.gateway.close();self.fake.shutdown();self.thread.join(timeout=2)
    def connect(self):
        ws=connect(f'ws://127.0.0.1:{self.port}',proxy=None,compression=None,close_timeout=1,logger=QUIET)
        ws.recv(timeout=2);return ws
    def valid_handshake(self,ws):
        ws.send(json.dumps({'type':'BotHandshake','sessionId':'test-session','name':'Walls',
                           'version':'1.0','secret':'TEST_TOKEN','authors':['test']}))
    def assert_denied(self,ws):
        with self.assertRaises(ConnectionClosed) as e:ws.recv(timeout=3)
        self.assertEqual(e.exception.rcvd.code,1008)
    def test_valid_transport_and_secret_rewrite(self):
        with self.connect() as ws:
            self.valid_handshake(ws);handshake=self.received.get(timeout=2)
            self.assertEqual(handshake['secret'],'RAW_ENGINE_SECRET')
            self.assertNotIn('TEST_TOKEN',repr(handshake))
            ws.send('{"type":"BotReady"}');self.assertEqual(json.loads(ws.recv(timeout=2))['type'],'RoundStartedEvent')
            ws.send('{"type":"BotIntent","targetSpeed":6}')
            self.assertEqual(json.loads(ws.recv(timeout=2))['type'],'TickEventForBot')
    def test_controller_rejected_first(self):
        with self.connect() as ws:
            ws.send('{"type":"ControllerHandshake","secret":"TEST_TOKEN"}');self.assert_denied(ws)
        self.assertTrue(self.received.empty())
    def test_invalid_token(self):
        with self.connect() as ws:
            ws.send('{"type":"BotHandshake","sessionId":"test-session","name":"Walls","version":"1.0","secret":"wrong"}')
            self.assert_denied(ws)
        self.assertTrue(self.received.empty())
    def test_admin_message_after_handshake_never_forwarded(self):
        with self.connect() as ws:
            self.valid_handshake(ws);self.received.get(timeout=2)
            ws.send('{"type":"ChangeTps","tps":23}');self.assert_denied(ws)
        self.assertTrue(self.received.empty())
        self.assertEqual(self.gateway.report()['BOT_MESSAGE_ONLY'],1)
    def test_second_handshake_denied(self):
        with self.connect() as ws:
            self.valid_handshake(ws);self.received.get(timeout=2)
            self.valid_handshake(ws);self.assert_denied(ws)
        self.assertTrue(self.received.empty())
    def test_duplicate_identity_denied(self):
        with self.connect() as a:
            self.valid_handshake(a);self.received.get(timeout=2)
            with self.connect() as b:
                self.valid_handshake(b);self.assert_denied(b)
            a.send('{"type":"BotReady"}');self.assertEqual(json.loads(a.recv(timeout=2))['type'],'RoundStartedEvent')
    def test_binary_denied(self):
        with self.connect() as ws:
            ws.send(b'abc');self.assert_denied(ws)
        self.assertTrue(self.received.empty())
    def test_unknown_intent_denied(self):
        with self.connect() as ws:
            self.valid_handshake(ws);self.received.get(timeout=2)
            ws.send('{"type":"BotIntent","command":"shell"}');self.assert_denied(ws)
        self.assertTrue(self.received.empty())

if __name__=='__main__':unittest.main()
