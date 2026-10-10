"""Regression for supervisor arguments and cleanup; no Docker/sudo called."""
import importlib.util,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('separated_arena',ROOT/'scripts/run_separated_arena.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
from services.worker_agent.arena_policy import firewall,LABEL

class SupervisorVectorTests(unittest.TestCase):
    def test_rule_inventory_uses_separate_flag(self):
        run='a'*24;refs='172.19.0.2';peers=['172.19.0.3','172.19.0.4']
        calls=[]
        def mock_command(args,**kwargs):
            calls.append(args)
            if args[-2:]==['readlink','/proc/self/ns/net']:
                return SimpleNamespace(output=b'net:[2]\n')
            if args[-1]=='-S':
                family=args[-2]
                text=firewall('walls',refs,peers,ipv6=family=='ip6tables')
                lines=['-P '+c+' DROP' for c in ('INPUT','OUTPUT','FORWARD')]
                lines += [l for l in text.splitlines() if l.startswith('-A ')]
                return SimpleNamespace(output='\n'.join(lines).encode())
            if args[-3] in ('iptables-restore','ip6tables-restore') or '-C' in args:
                return SimpleNamespace(output=b'')
            raise AssertionError('Unexpected supervisor argument vector: '+repr(args))
        with (patch.object(M,'info',return_value={'State':{'Pid':100,'Running':True},'Config':{'Labels':{LABEL:run}}}),
              patch.object(M,'namespace',return_value='net:[2]'),
              patch.object(M.os,'readlink',return_value='net:[1]'),
              patch.object(M,'command',side_effect=mock_command)):
            result=M.install_firewall('synthetic',run,'walls',refs,peers)
        self.assertTrue(result['verified'])
        self.assertTrue(any(args[-2:]==['iptables','-S'] for args in calls))
        self.assertTrue(any(args[-2:]==['ip6tables','-S'] for args in calls))

class CleanupTests(unittest.TestCase):
    def test_unknown_abort_stage_does_not_call_docker(self):
        with patch.object(M,'docker') as mocked:
            with self.assertRaises(ValueError):M.one_battle({},Path('/not-used'),abort_at='arbitrary')
            mocked.assert_not_called()
    def test_tag_reassigned_is_not_removed(self):
        calls=[]
        def fake(*args,**kwargs):
            calls.append(args)
            return SimpleNamespace(returncode=0,output=b'sha256:'+b'b'*64)
        with patch.object(M,'docker',side_effect=fake):
            self.assertFalse(M.cleanup_images({'walls':'robocopa-i2-'+'a'*12+':walls'}, {'walls':'sha256:'+'a'*64}))
        self.assertFalse(any('rm' in args for args in calls))
    def test_invalid_tag_not_touched(self):
        with patch.object(M,'docker') as mocked:
            self.assertFalse(M.cleanup_images({'walls':'other-project'},{}));mocked.assert_not_called()
    def test_partial_failed_build_records_tags(self):
        import tempfile
        tags={};images={}
        def fake(*args,**kwargs):
            if args[0]=='build':
                return SimpleNamespace(returncode=1 if 'walls' in args else 0,output=b'fixed build output')
            if '--format' in args:return SimpleNamespace(returncode=0,output=b'sha256:'+b'a'*64)
            return SimpleNamespace(returncode=1,output=b'')
        with tempfile.TemporaryDirectory() as tmp,patch.object(M,'docker',side_effect=fake):
            with self.assertRaisesRegex(RuntimeError,'BUILD_FAILED_walls'):M.build_images(Path(tmp),images,tags)
        self.assertEqual(set(tags),{'referee','walls'});self.assertEqual(set(images),{'referee'})
