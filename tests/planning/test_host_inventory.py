"""Testes unitários do coletor, sem consultar hardware real nem rede."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'collect_host_inventory.py'
spec = importlib.util.spec_from_file_location('host_inventory', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HostInventoryTest(unittest.TestCase):
    def test_wsl_discards_distribution_names(self):
        fake = '  NAME                   STATE           VERSION\n* JoaoPrivado            Stopped         2\n  Ubuntu                 Running         1\n'
        with patch.object(module.shutil, 'which', return_value='wsl.exe'), patch.object(module, '_run', return_value=fake):
            result = module._wsl_details()
        self.assertEqual(result['distribution_count'], 2)
        self.assertEqual(result['wsl2_distribution_count'], 1)
        self.assertNotIn('JoaoPrivado', repr(result))

    def test_docker_down_is_not_reported_as_ready(self):
        with patch.object(module.shutil, 'which', return_value='docker'), patch.object(module, '_run', return_value=None):
            result = module._docker_details()
        self.assertTrue(result['cli_available'])
        self.assertFalse(result['daemon_accessible'])

    def test_docker_extracts_selected_values_only(self):
        def fake(args, timeout=8):
            return '28.4.1|linux|12|17179869184' if 'info' in args else 'v2.32.0'
        with patch.object(module.shutil, 'which', return_value='docker'), patch.object(module, '_run', side_effect=fake):
            result = module._docker_details()
        self.assertEqual(result['allocated_memory_bytes'], 17179869184)
        self.assertTrue(result['daemon_accessible'])
        self.assertEqual(result['compose_version'], 'v2.32.0')

    def test_invalid_windows_probe_does_not_export_raw_output(self):
        with patch.object(module.shutil, 'which', return_value='powershell.exe'), patch.object(module, '_run', return_value='username=secret'):
            result = module._windows_details()
        self.assertEqual(result, {'status': 'windows_probe_unreadable'})
        self.assertNotIn('secret', repr(result))

    def test_nvidia_output_selected_fields(self):
        fake = 'NVIDIA GeForce RTX 4060 Ti, 16380, 555.90\n'
        with patch.object(module.shutil, 'which', return_value='nvidia-smi'), patch.object(module, '_run', return_value=fake):
            result = module._nvidia_details()
        self.assertEqual(result[0]['vram_mib'], 16380)

    def test_utf16le_output_decoding(self):
        raw = ' Ubuntu       Running        2\r\n'.encode('utf-16-le')
        self.assertIn('Ubuntu', module._decode_stdout(raw))

    def test_output_schema_does_not_collect_identity(self):
        with patch.object(module, '_windows_details', return_value={'status': 'mock'}), patch.object(module, '_nvidia_details', return_value=[]), patch.object(module, '_docker_details', return_value={}), patch.object(module, '_wsl_details', return_value={}):
            result = module.collect(SCRIPT.parent)
        self.assertEqual(result['schema_version'], 2)
        for sensitive in ('hostname', 'username', 'mac_addresses', 'ip_addresses'):
            self.assertNotIn(f'"{sensitive}":', json.dumps(result))
            self.assertIn(sensitive, result['not_collected'])


if __name__ == '__main__':
    unittest.main()
