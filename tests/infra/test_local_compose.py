"""Testes unitários independentes de Docker, que também rodam no Windows."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_SPEC = spec_from_file_location("validate_local_compose", ROOT / "scripts" / "validate_local_compose.py")
VALIDATOR = module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(VALIDATOR)


def sample_config():
    return {
        "name": "robocopa-ifma-local",
        "networks": {"data": {"internal": True}, "edge": {}},
        "services": {
            "database": {
                "environment": {"POSTGRES_PASSWORD": "fake-for-test"},
                "networks": {"data": None}, "cpus": 2, "mem_limit": 2147483648,
                "pids_limit": 256,
                "volumes": [{"type": "volume", "target": "/var/lib/postgresql/data"}],
            },
            "infra-probe": {
                "networks": {"edge": None}, "cpus": 0.5, "mem_limit": 536870912,
                "pids_limit": 64, "read_only": True, "cap_drop": ["ALL"],
                "ports": [{"host_ip": "127.0.0.1", "target": 8080, "published": "18080", "protocol": "tcp"}],
                "volumes": [{"type": "bind", "source": "/test", "target": "/app"}],
            },
        },
    }


class ComposeContractTest(unittest.TestCase):
    def test_good_compose(self):
        self.assertEqual(VALIDATOR.validate(sample_config()), [])

    def test_postgres_exposure_rejected(self):
        cfg = sample_config()
        cfg["services"]["database"]["ports"] = [{"host_ip": "0.0.0.0", "target": 5432}]
        self.assertTrue(VALIDATOR.validate(cfg))

    def test_probe_public_exposure_rejected(self):
        cfg = sample_config()
        cfg["services"]["infra-probe"]["ports"][0]["host_ip"] = "0.0.0.0"
        self.assertTrue(VALIDATOR.validate(cfg))

    def test_docker_socket_rejected(self):
        cfg = sample_config()
        cfg["services"]["infra-probe"]["volumes"].append({
            "type": "bind", "source": "/var/run/docker.sock", "target": "/var/run/docker.sock"})
        self.assertTrue(VALIDATOR.validate(cfg))

    def test_persistent_volume_required(self):
        cfg = sample_config()
        cfg["services"]["database"]["volumes"] = []
        self.assertTrue(VALIDATOR.validate(cfg))

    def test_missing_resource_limits_rejected(self):
        cfg = sample_config()
        cfg["services"]["database"]["mem_limit"] = None
        self.assertTrue(VALIDATOR.validate(cfg))

    def test_init_env_generates_random_secret_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "scripts"
            folder.mkdir()
            source = ROOT / "scripts" / "init_local_env.py"
            target = folder / "init_local_env.py"
            target.write_bytes(source.read_bytes())
            first = subprocess.run([sys.executable, str(target)], cwd=root,
                                   capture_output=True, text=True, check=False)
            self.assertEqual(first.returncode, 0, first.stderr)
            data = (root / ".env").read_text(encoding="utf-8")
            password = next(l.split("=", 1)[1] for l in data.splitlines()
                            if l.startswith("ROBOCOPA_DB_PASSWORD="))
            self.assertGreaterEqual(len(password), 48)
            self.assertNotIn(password, first.stdout)
            second = subprocess.run([sys.executable, str(target)], cwd=root,
                                    capture_output=True, text=True, check=False)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual((root / ".env").read_text(encoding="utf-8"), data)


if __name__ == "__main__":
    unittest.main()
