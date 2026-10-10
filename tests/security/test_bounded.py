"""Real, small local subprocess tests; not a Docker sandbox claim."""
import os
from pathlib import Path
import sys
import time
import unittest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from services.worker_agent.bounded import capture, ProcessBoundError


@unittest.skipUnless(os.name=='posix', 'POSIX worker component')
class BoundedTests(unittest.TestCase):
    def test_normal_output(self):
        result=capture([sys.executable,'-c','print("hello")'],timeout=3,max_bytes=100)
        self.assertEqual(result.returncode,0); self.assertEqual(result.output,b'hello\n')
    def test_nonzero_status_retained(self):
        result=capture([sys.executable,'-c','raise SystemExit(7)'],timeout=3,max_bytes=100)
        self.assertEqual(result.returncode,7)
    def test_exact_output_budget(self):
        result=capture([sys.executable,'-c','import os;os.write(1,b"X"*64)'],timeout=3,max_bytes=64)
        self.assertEqual(len(result.output),64)
    def test_output_over_budget_stops(self):
        with self.assertRaises(ProcessBoundError) as ctx:
            capture([sys.executable,'-c','import os;os.write(1,b"X"*4096)'],timeout=3,max_bytes=64)
        self.assertEqual(ctx.exception.reason,'OUTPUT_LIMIT')
        self.assertLessEqual(len(ctx.exception.output),64)
    def test_timeout_kills_process_group(self):
        start=time.monotonic()
        with self.assertRaises(ProcessBoundError) as ctx:
            capture([sys.executable,'-c','import time;time.sleep(20)'],timeout=.2,max_bytes=64)
        self.assertEqual(ctx.exception.reason,'TIMEOUT'); self.assertLess(time.monotonic()-start,3)
    def test_stderr_uses_same_budget(self):
        with self.assertRaises(ProcessBoundError) as ctx:
            capture([sys.executable,'-c','import os;os.write(2,b"X"*4096)'],timeout=3,max_bytes=64)
        self.assertEqual(ctx.exception.reason,'OUTPUT_LIMIT')
    def test_rejects_shell_string(self):
        with self.assertRaises(ValueError): capture('echo x',timeout=1,max_bytes=64)
    def test_rejects_unbounded_configuration(self):
        with self.assertRaises(ValueError): capture(['echo','x'],timeout=0,max_bytes=64)
