import sys,unittest
from services.worker_agent.bounded import capture,ProcessBoundError
class InputBoundTests(unittest.TestCase):
    def test_echo(self):
        r=capture([sys.executable,'-c','import sys;sys.stdout.buffer.write(sys.stdin.buffer.read())'],
                  timeout=3,max_bytes=65536,input_bytes=b'x'*65536)
        self.assertEqual(len(r.output),65536)
    def test_empty_input_closes(self):
        r=capture([sys.executable,'-c','import sys;print(len(sys.stdin.buffer.read()))'],timeout=3,max_bytes=100,input_bytes=b'')
        self.assertEqual(r.output.strip(),b'0')
    def test_timeout_while_input_not_read(self):
        with self.assertRaises(ProcessBoundError) as e:
            capture([sys.executable,'-c','import time;time.sleep(2)'],timeout=.15,max_bytes=100,input_bytes=b'a'*65536)
        self.assertEqual(e.exception.reason,'TIMEOUT')
    def test_stdout_limit_with_input(self):
        with self.assertRaises(ProcessBoundError) as e:
            capture([sys.executable,'-c','import sys;sys.stdout.write("x"*5000);sys.stdin.buffer.read()'],
                    timeout=2,max_bytes=100,input_bytes=b'a'*5000)
        self.assertEqual(e.exception.reason,'OUTPUT_LIMIT')
    def test_reject_unbounded_input(self):
        for data in ('text',b'a'*65537):
            with self.assertRaises(ValueError):capture([sys.executable],timeout=1,max_bytes=1,input_bytes=data)
    def test_early_exit(self):
        self.assertEqual(capture([sys.executable,'-c','pass'],timeout=3,max_bytes=10,input_bytes=b'x'*65536).returncode,0)
