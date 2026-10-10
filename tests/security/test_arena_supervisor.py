"""Regression for constructing supervisor utility argv; no Docker or sudo called."""
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
