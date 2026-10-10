"""Canonical progress changes only the authorized macro task, never an approval."""
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from reconcile_isolation_backlog import reconcile

class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT/'docs/planejamento/backlog.json').read_text())
    def test_only_target_changes(self):
        new = reconcile(self.data)
        for s, ns in zip(self.data['sprints'], new['sprints']):
            for t, nt in zip(s['tasks'], ns['tasks']):
                if t['id'] != 'S04-T04': self.assertEqual(t, nt)
                else:
                    self.assertEqual(nt['status'], 'EM_EXECUCAO')
                    self.assertEqual(nt['dependencies'], t['dependencies'])
                    self.assertTrue(nt['evidence'])
    def test_idempotent(self):
        new=reconcile(self.data)
        self.assertEqual(reconcile(new), new)
    def test_does_not_overwrite_review_or_completion(self):
        for s in self.data['sprints']:
            for t in s['tasks']:
                if t['id']=='S04-T04': t['status']='EM_REVISAO'
        with self.assertRaises(ValueError): reconcile(self.data)
