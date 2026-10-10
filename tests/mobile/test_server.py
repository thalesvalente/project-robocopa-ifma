"""HTTP boundary tests with a fake executor explicitly isolated from real-engine CI."""
import http.client
import json
from pathlib import Path
import sys
import threading
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import serve_mobile_spike as app

class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calls = []
        def fake(source):
            cls.calls.append(source)
            return {'test_fixture': True}
        cls.server = app.LabServer(0, execute=fake)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def request(self, method, path, source=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        h = {'Content-Type':'application/json', 'Origin':f'http://127.0.0.1:{self.server.server_port}',
             'X-Robocopa-CSRF':self.server.token}
        if headers: h.update(headers)
        body = json.dumps({'source':source}) if source is not None else None
        connection.request(method, path, body=body, headers=h)
        result = connection.getresponse(); data = result.read();code=result.status
        connection.close();return code,data
    def test_ui(self): self.assertEqual(self.request('GET','/')[0], 200)
    def test_static_allowlist(self):
        for path in ['/.env','/../.env','/%2e%2e/.env','/scripts/run_mobile_spike.py','/.local/']:
            self.assertEqual(self.request('GET',path)[0],404)
    def test_external_host_blocked(self):
        self.assertEqual(self.request('GET','/',headers={'Host':'evil.example'})[0],403)
    def test_external_origin_blocked(self):
        self.assertEqual(self.request('POST','/api/validate',app.mobile.LANG.EXAMPLES['sentinela'],{'Origin':'http://evil.example'})[0],403)
    def test_bad_token_blocked(self):
        self.assertEqual(self.request('POST','/api/train',app.mobile.LANG.EXAMPLES['sentinela'],{'X-Robocopa-CSRF':'wrong'})[0],403)
    def test_validate_never_executes(self):
        before=len(self.calls)
        self.assertEqual(self.request('POST','/api/validate',app.mobile.LANG.EXAMPLES['sentinela'])[0],200)
        self.assertEqual(len(self.calls),before)
    def test_invalid_rejected_before_executor(self):
        before=len(self.calls)
        self.assertEqual(self.request('POST','/api/train','System.exit(0)')[0],400)
        self.assertEqual(len(self.calls),before)
    def test_train_mock_not_engine(self):
        status,raw=self.request('POST','/api/train',app.mobile.LANG.EXAMPLES['sentinela'])
        self.assertEqual(status,200);self.assertTrue(json.loads(raw)['test_fixture'])
    def test_busy_no_second_job(self):
        with self.server.busy:
            self.assertEqual(self.request('POST','/api/train',app.mobile.LANG.EXAMPLES['sentinela'])[0],409)
    def test_oversize(self):
        self.assertEqual(self.request('POST','/api/train','x'*20000)[0],413)

if __name__ == '__main__': unittest.main()
