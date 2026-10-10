"""Compiler unit tests: synthetic programs, not evidence of a real battle."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from run_mobile_spike import LANG

class LanguageTest(unittest.TestCase):
    def test_examples(self):
        for source in LANG.EXAMPLES.values():
            self.assertIn('while (isRunning())', LANG.compile_program(source)['java'])
    def test_grammar_controls_actual_movement(self):
        code = LANG.compile_program(LANG.EXAMPLES['explorador'])['java']
        self.assertIn('setTargetSpeed(6);', code)
        self.assertIn('setTurnRate(8);', code)
    def test_conditions_are_code_not_appearance(self):
        code = LANG.compile_program(LANG.EXAMPLES['sentinela'])['java']
        self.assertIn('if (distanceTo(e.getX(), e.getY()) < 250)', code)
        self.assertIn('} else {', code)
        self.assertIn('setFire(3);', code)
    def test_hash_is_semantic(self):
        a = LANG.EXAMPLES['sentinela']
        self.assertEqual(LANG.compile_program(a)['program_sha256'],
                         LANG.compile_program('# comentário\n'+a.replace('canhao', 'canhão'))['program_sha256'])
    def test_action_edit_changes_hash(self):
        a = LANG.EXAMPLES['explorador']
        self.assertNotEqual(LANG.compile_program(a)['program_sha256'],
                            LANG.compile_program(a.replace('velocidade 6', 'velocidade 2'))['program_sha256'])
    def test_no_source_injection(self):
        for command in ['import java.io.File;', 'System.exit(0);', 'atirar NaN',
                        'atirar Infinity', 'atirar 1; Runtime.getRuntime()', 'velocidade 1e50',
                        'abrir /etc/passwd', 'atirar "1"', 'eval(1)']:
            with self.subTest(command=command), self.assertRaises(LANG.ProgramError):
                LANG.parse(LANG.EXAMPLES['explorador'].replace('velocidade 6', command))
    def test_bounds(self):
        for command in ['velocidade 9', 'atirar 0', 'atirar 4', 'girar -11', 'canhao 21']:
            with self.subTest(command=command), self.assertRaises(LANG.ProgramError):
                LANG.parse(LANG.EXAMPLES['explorador'].replace('velocidade 6', command))
    def test_sensor_scoping(self):
        with self.assertRaises(LANG.ProgramError):
            LANG.parse('sempre\nse distancia < 100\natirar 1\nfim\nfim\nao detectar\natirar 1\nfim')
    def test_missing_event(self):
        with self.assertRaises(LANG.ProgramError): LANG.parse('sempre\ngirar 1\nfim')
    def test_unclosed(self):
        with self.assertRaises(LANG.ProgramError): LANG.parse(LANG.EXAMPLES['sentinela'].rstrip()[:-3])
    def test_duplicate_event(self):
        with self.assertRaises(LANG.ProgramError): LANG.parse(LANG.EXAMPLES['sentinela']+'sempre\ngirar 1\nfim')
    def test_size(self):
        with self.assertRaises(LANG.ProgramError): LANG.parse('#' * 8193)
    def test_node_budget(self):
        with self.assertRaises(LANG.ProgramError):
            LANG.parse('sempre\n'+'girar 1\n'*81+'fim\nao detectar\natirar 1\nfim')
    def test_nesting_budget(self):
        with self.assertRaises(LANG.ProgramError):
            LANG.parse('sempre\n'+'se energia > 1\n'*4+'girar 1\n'+'fim\n'*5+'ao detectar\natirar 1\nfim')
    def test_error_line(self):
        with self.assertRaises(LANG.ProgramError) as found:
            LANG.parse(LANG.EXAMPLES['explorador'].replace('velocidade 6', 'velocidade 90'))
        self.assertEqual(found.exception.line, 2)
    def test_comments_never_emitted(self):
        self.assertNotIn('Runtime', LANG.compile_program('# Runtime.getRuntime()\n'+LANG.EXAMPLES['sentinela'])['java'])
    def test_false_type_rejected(self):
        with self.assertRaises(LANG.ProgramError): LANG.parse({})

if __name__ == '__main__': unittest.main()
