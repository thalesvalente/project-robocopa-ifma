"""Testes do preflight de leitura, sem interagir com Docker real."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "preflight_local.py"
spec = importlib.util.spec_from_file_location("preflight_local", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PreflightTest(unittest.TestCase):
    def test_other_project_is_not_blocked(self):
        self.assertTrue(module.check_docker_projects(
            '[{"Name":"other-app","Status":"running(2)"}]'))

    def test_existing_robocopa_name_is_blocked(self):
        self.assertFalse(module.check_docker_projects(
            '[{"Name":"robocopa-ifma-local","Status":"exited(2)"}]'))

    def test_invalid_docker_projects_is_blocked(self):
        self.assertFalse(module.check_docker_projects("some unsafe raw text"))
        self.assertFalse(module.check_docker_projects('{"Name":"x"}'))

    def test_port_read_without_exposing_secret(self):
        with tempfile.TemporaryDirectory() as temp:
            env = Path(temp) / ".env"
            env.write_text("ROBOCOPA_HOST_PORT=18080\nROBOCOPA_DB_PASSWORD=private_value\n")
            self.assertEqual(module.env_port(env), 18080)
            self.assertNotIn("private_value", str(module.env_port(env)))

    def test_invalid_port_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            env = Path(temp) / ".env"
            env.write_text("ROBOCOPA_HOST_PORT=not_a_port\n")
            self.assertIsNone(module.env_port(env))

    def test_preflight_read_only_with_mocked_commands(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".env").write_text("ROBOCOPA_HOST_PORT=18080\nROBOCOPA_DB_PASSWORD=secret\n")
            with (patch.object(module.shutil, "which", return_value="docker"),
                  patch.object(module, "run", side_effect=[
                      (True, "28.1.1"), (True, "[]")]),
                  patch.object(module, "port_is_free", return_value=True),
                  patch.object(module.shutil, "disk_usage",
                               return_value=type("Disk", (), {"free": 20*1024**3})())):
                checks = module.check_local(root)
            self.assertTrue(all(status for _, status in checks), checks)
            self.assertNotIn("secret", str(checks))


if __name__ == "__main__":
    unittest.main()
