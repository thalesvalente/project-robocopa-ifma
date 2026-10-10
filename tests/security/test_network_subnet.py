"""Regression: Docker static endpoints require user-configured subnets."""
import ipaddress
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from services.worker_agent.game_policy import network_args, CI_SUBNETS, PolicyError

class ExplicitSubnetTests(unittest.TestCase):
    def test_subnet_required_for_static_addresses(self):
        run='a'*24
        for role,subnet in CI_SUBNETS.items():
            args=network_args(f'rc-i2-{run}-{role}',run)
            self.assertEqual(args[args.index('--subnet')+1],subnet)
            self.assertIn('--internal',args)
    def test_ranges_do_not_overlap(self):
        nets=[ipaddress.ip_network(v) for v in CI_SUBNETS.values()]
        self.assertEqual(len(nets),3)
        for i,a in enumerate(nets):
            self.assertTrue(a.is_private)
            self.assertEqual(a.prefixlen,28)
            for b in nets[i+1:]:self.assertFalse(a.overlaps(b))
    def test_no_user_supplied_cidr_argument(self):
        run='a'*24
        with self.assertRaises(PolicyError):network_args(f'rc-i2-{run}-172.0.0.0/8',run)
    def test_partial_run_id_cannot_authorize_name(self):
        with self.assertRaises(PolicyError):network_args('rc-i2-'+'a'*24+'-a','a')
    def test_different_run_denied(self):
        with self.assertRaises(PolicyError):network_args('rc-i2-'+'a'*24+'-a','b'*24)

if __name__=='__main__':unittest.main()
