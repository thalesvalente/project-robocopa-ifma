"""Oracle of the controlled cleanup scenario: no mock is labeled as a battle."""
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location('separation_modes',ROOT/'scripts/run_engine_separation.py')
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)
class DeadlineOracleTests(unittest.TestCase):
    def test_expected_timeout(self):
        def action():raise M.ProcessBoundError('TIMEOUT')
        self.assertIsNone(M.expect_deadline(action))
    def test_output_limit_is_not_timeout(self):
        def action():raise M.ProcessBoundError('OUTPUT_LIMIT')
        with self.assertRaises(M.ProcessBoundError):M.expect_deadline(action)
    def test_generic_error_is_not_pass(self):
        def action():raise RuntimeError('fixture failure')
        with self.assertRaises(RuntimeError):M.expect_deadline(action)
    def test_normal_exit_does_not_prove_timeout(self):
        with self.assertRaisesRegex(RuntimeError,'DEADLINE_NOT_OBSERVED'):M.expect_deadline(lambda:None)
if __name__=='__main__':unittest.main()
