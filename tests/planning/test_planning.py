from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import bootstrap_speckit as bootstrap
import verify_planning as verifier
import render_planning as renderer


class BacklogTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'docs/planejamento/backlog.json').read_text(encoding='utf-8'))

    def test_valid_baseline(self):
        self.assertEqual(verifier.validate(self.data), (10, 60))

    def test_duplicate_rejected(self):
        self.data['sprints'][0]['tasks'][1]['id'] = 'S00-T01'
        with self.assertRaisesRegex(ValueError, 'duplicado'):
            verifier.validate(self.data)

    def test_missing_dependency_rejected(self):
        self.data['sprints'][0]['tasks'][0]['dependencies'] = ['S99-T99']
        with self.assertRaisesRegex(ValueError, 'inexistente'):
            verifier.validate(self.data)

    def test_cycle_rejected(self):
        self.data['sprints'][0]['tasks'][0]['dependencies'] = ['S00-T02']
        with self.assertRaisesRegex(ValueError, 'Ciclo'):
            verifier.validate(self.data)

    def test_completion_without_evidence_rejected(self):
        task = self.data['sprints'][1]['tasks'][0]
        task['status'] = 'CONCLUIDA'
        task['evidence'] = []
        with self.assertRaisesRegex(ValueError, 'sem evidência'):
            verifier.validate(self.data)

    def test_lock_matches_official_source(self):
        lock = bootstrap.load_lock(ROOT)
        self.assertEqual(lock['release'], 'v1.1.2')
        self.assertEqual(lock['commit'], '959e866caa3618bf3dc290d5dca33394365af9c6')

    def test_command_does_not_force_project_overwrite(self):
        cmd = bootstrap.command(bootstrap.load_lock(ROOT), Path('/tmp/example'), 'ps')
        self.assertNotIn('--force', cmd)
        self.assertNotIn('--here', cmd)
        self.assertIn('--non-interactive', cmd)
        self.assertIn('--integration-options=--commands-dir .agents/commands', cmd)

    def test_render_covers_ids(self):
        text = renderer.sprint_markdown(self.data['sprints'][0])
        for task in self.data['sprints'][0]['tasks']:
            self.assertIn(f"| {task['id']} |", text)

    def test_render_is_deterministic(self):
        self.assertEqual(renderer.sprint_markdown(self.data['sprints'][0]), renderer.sprint_markdown(self.data['sprints'][0]))

    def test_markdown_cells_escape_pipes(self):
        self.assertEqual(renderer.cell('A|B\nC'), 'A\\|B<br>C')


class BootstrapFilesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repo'
        self.stage = Path(self.tmp.name) / 'stage'
        self.root.mkdir()
        self.stage.mkdir()
        for relative in bootstrap.REQUIRED:
            self.put(self.stage, relative, 'generated-content\n')
        self.put(self.stage, bootstrap.PRESERVED, 'upstream-template\n')

    @staticmethod
    def put(root, relative, content):
        p = root / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')

    def test_preserves_constitution(self):
        self.put(self.root, bootstrap.PRESERVED, 'minha constituicao\n')
        created = bootstrap.copy_generated(self.root, self.stage)
        self.assertEqual((self.root / bootstrap.PRESERVED).read_text(), 'minha constituicao\n')
        self.assertNotIn(bootstrap.PRESERVED.as_posix(), created)

    def test_conflict_aborts_before_copy(self):
        relative = bootstrap.REQUIRED[1]
        self.put(self.root, relative, 'documento existente\n')
        with self.assertRaisesRegex(ValueError, 'Conflitos'):
            bootstrap.copy_generated(self.root, self.stage)
        self.assertFalse((self.root / bootstrap.REQUIRED[0]).exists())
        self.assertEqual((self.root / relative).read_text(), 'documento existente\n')

    def test_repeated_same_files_are_noop(self):
        bootstrap.copy_generated(self.root, self.stage)
        self.assertEqual(bootstrap.copy_generated(self.root, self.stage), [])

    def test_missing_upstream_file_rejected(self):
        (self.stage / bootstrap.REQUIRED[0]).unlink()
        with self.assertRaisesRegex(ValueError, 'não gerou'):
            bootstrap.copy_generated(self.root, self.stage)

    @unittest.skipIf(sys.platform == 'win32', 'Symlink pode exigir privilégio.')
    def test_destination_symlink_rejected(self):
        elsewhere = Path(self.tmp.name) / 'external'
        elsewhere.mkdir()
        (self.root / '.specify').symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'simbólico'):
            bootstrap.copy_generated(self.root, self.stage)
        self.assertFalse(list(elsewhere.rglob('*')))

    @unittest.skipIf(sys.platform == 'win32', 'Symlink pode exigir privilégio.')
    def test_source_symlink_rejected(self):
        (self.stage / '.agents' / 'linked').symlink_to(self.stage / bootstrap.REQUIRED[0])
        with self.assertRaisesRegex(ValueError, 'simbólico'):
            bootstrap.copy_generated(self.root, self.stage)


if __name__ == '__main__':
    unittest.main()
