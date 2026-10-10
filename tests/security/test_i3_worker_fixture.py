"""F01: SQL wrapper unit test with a fake executor, NOT PostgreSQL integration."""
import ast
from pathlib import Path
import unittest
from unittest.mock import Mock

class FixtureTests(unittest.TestCase):
    def test_sql_terminator_is_added_without_changing_old_fixture_or_migration(self):
        source=Path(__file__).resolve().parents[1]/'postgres/test_worker_api.py'
        tree=ast.parse(source.read_text())
        helper=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='sql')
        fake=Mock(return_value='17.11');env={'base_sql':fake}
        exec(compile(ast.Module(body=[helper],type_ignores=[]),str(source),'exec'),env)
        self.assertEqual(env['sql']('SHOW server_version','postgres'),'17.11')
        fake.assert_called_with('SHOW server_version;','postgres',wrap=True)
        env['sql']('BEGIN; SELECT 1; COMMIT;\n','postgres',wrap=False)
        fake.assert_called_with('BEGIN; SELECT 1; COMMIT;\n','postgres',wrap=False)
