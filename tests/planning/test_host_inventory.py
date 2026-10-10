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
        self.assertEqual(result['schema_version'], 3)
        for sensitive in ('hostname', 'username', 'mac_addresses', 'ip_addresses'):
            self.assertNotIn(f'"{sensitive}":', json.dumps(result))
            self.assertIn(sensitive, result['not_collected'])


    def test_docker_df_selects_numbers_without_names(self):
        raw = '\n'.join([
            json.dumps({'Type': 'Images', 'TotalCount': '6', 'Active': '4',
                        'Size': '20.51GB', 'Reclaimable': '15.42MB (0%)',
                        'UnexpectedSecret': 'container-secret'}),
            json.dumps({'Type': 'Local Volumes', 'TotalCount': '6', 'Active': '6',
                        'Size': '342.3MB', 'Reclaimable': '0B (0%)'}),
        ])
        with patch.object(module, '_run', return_value=raw):
            data = module._docker_storage_usage('docker')
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['categories'][0]['active'], 4)
        self.assertEqual(data['categories'][1]['size'], '342.3MB')
        self.assertNotIn('container-secret', json.dumps(data))

    def test_docker_df_rejects_unexpected_text(self):
        raw = json.dumps({'Type': 'Images', 'TotalCount': 1, 'Active': 1,
                          'Size': '1GB /home/username', 'Reclaimable': '0B (0%)'})
        with patch.object(module, '_run', return_value=raw):
            self.assertEqual(module._docker_storage_usage('docker')['status'], 'unreadable')

    def test_wsl_includes_known_distro_state_and_redacts_custom_names(self):
        raw = ('  NAME               STATE           VERSION\n'
               '* docker-desktop     Running         2\n'
               '  Ubuntu             Running         2\n'
               '  Private-Lab        Stopped         2\n')
        status = 'Distribuição Padrão: docker-desktop\nVersão Padrão: 2\n'
        def fake(args, timeout=8):
            return status if '--status' in args else raw
        with patch.object(module.shutil, 'which', return_value='wsl.exe'), patch.object(module, '_run', side_effect=fake):
            data = module._wsl_details()
        self.assertEqual(data['status']['default_distribution'], 'docker-desktop')
        self.assertEqual(data['status']['default_version'], 2)
        self.assertEqual(data['distribution_count'], 3)
        self.assertEqual(data['wsl2_distribution_count'], 3)
        self.assertEqual(data['distributions'][1]['distribution'], 'Ubuntu')
        self.assertNotIn('Private-Lab', json.dumps(data))

    def test_docker_root_path_is_sanitized(self):
        def fake(args, timeout=8):
            joined = ' '.join(args)
            if 'compose' in args:
                return 'v2.35.1'
            if 'DockerRootDir' in joined:
                return '/home/private-user/docker'
            if 'system' in args:
                return json.dumps({'Type': 'Images', 'TotalCount': '0', 'Active': '0',
                                   'Size': '0B', 'Reclaimable': '0B'})
            return '28.1.1|linux|32|67253637120'
        with patch.object(module.shutil, 'which', return_value='docker'), patch.object(module, '_run', side_effect=fake):
            data = module._docker_details()
        self.assertEqual(data['docker_root_dir'], '[custom_path_redacted]')
        self.assertNotIn('private-user', json.dumps(data))
        self.assertEqual(data['storage_usage']['status'], 'ok')



if __name__ == '__main__':
    unittest.main()
