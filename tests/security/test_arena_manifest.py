"""Synthetic complete evidence trees, not real Docker/game observations."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib,json,unittest
from services.worker_agent import arena_evidence as e
from test_arena_evidence import fixture,payload


def make_battle(folder):
    folder.mkdir()
    r,events=fixture();files=payload(r,events);metrics=e.validate_replay(files)
    ns={role:{kind:f'{kind}:[{100+idx}]' for kind in ('pid','net','mnt')}
        for idx,role in enumerate(e.ROLES)}
    ref={'upstream_role_secrets_reject_bot_secret':{'ControllerHandshake':True,'ObserverHandshake':True},
         'gateway_control_did_not_change_engine':True,'raw_engine_control_without_handshake_observed':True,
         'gateway':{'accepted_handshake':8,'BotReady':8,'BotIntent':10},
         'server_artifact':{'server_jar_sha256':e.SERVER_SHA256,'derived_from_runner_sha256':e.RUNNER_SHA256},
         'replay_sha256':metrics['sha256']}
    report={'schema_version':2,'run_id':'a'*24,'status':'PASS',
        'host_vm_tested':False,'student_submission_enabled':False,
        'host_rules_unchanged_during_acl_setup':True,'positive_host_peer_canaries':True,
        'cleanup_completed':True,'remaining_owned_containers':False,'remaining_owned_networks':False,
        'policy':{role:{check:True for check in e.POLICY_CHECKS} for role in e.ROLES},
        'namespace_ids':ns,'host_namespace_ids':{kind:f'{kind}:[1]' for kind in ('pid','net','mnt')},
        'firewall':{role:{'verified':True,'host_netns_distinct':True,'netns':ns[role]['net']} for role in e.ROLES},
        'network_and_protocol_probes':{role:{'checks':{check:True for check in e.PROBE_CHECKS}} for role in ('walls','spin')},
        'bot_output_acl_reject_packets':{'walls':6,'spin':6},'referee':ref,'replay':metrics}
    files.update({'referee-report.json':json.dumps(ref).encode(),'report.json':json.dumps(report).encode()})
    for name,raw in files.items():(folder/name).write_bytes(raw)
    return report


def make_batch(root):
    for name in ('battle-1','battle-2'):make_battle(root/name)
    for point in ('after_containers','after_ready'):
        folder=root/('abort-'+point);folder.mkdir()
        (folder/'report.json').write_text(json.dumps({'status':'EXPECTED_ABORT','abort_injected':point,
            'cleanup_completed':True,'remaining_owned_containers':False,'remaining_owned_networks':False}))
    (root/'batch.json').write_text(json.dumps({'schema_version':2,'status':'PASS',
        'host_vm_tested':False,'student_submission_enabled':False,'image_cleanup_completed':True,
        'battles':['battle-1','battle-2'],'abort_checks':['abort-after_containers','abort-after_ready']}))

class ManifestTests(unittest.TestCase):
    def test_complete_synthetic_batch(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp);make_batch(p);self.assertEqual(e.validate_batch(p)['abort_checks_passed'],2)
    def reject(self,mutate):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'battle';report=make_battle(p);mutate(report)
            (p/'report.json').write_text(json.dumps(report))
            with self.assertRaises(e.EvidenceError):e.validate_battle(p)
    def test_cleanup_false(self):self.reject(lambda r:r.update(cleanup_completed=False))
    def test_cleanup_truthy(self):self.reject(lambda r:r.update(cleanup_completed=1))
    def test_production_claim_denied(self):self.reject(lambda r:r.update(student_submission_enabled=True))
    def test_missing_probe_for_second_bot(self):self.reject(lambda r:r['network_and_protocol_probes'].pop('spin'))
    def test_missing_policy(self):self.reject(lambda r:r['policy']['referee'].pop('read_only'))
    def test_empty_probe_no_false_positive(self):self.reject(lambda r:r['network_and_protocol_probes']['walls'].update(checks={}))
    def test_host_shared_namespace(self):self.reject(lambda r:r['namespace_ids']['walls'].update(net=r['host_namespace_ids']['net']))
    def test_bots_shared_namespace(self):self.reject(lambda r:r['namespace_ids']['walls'].update(pid=r['namespace_ids']['spin']['pid']))
    def test_no_actual_reject_counter(self):self.reject(lambda r:r['bot_output_acl_reject_packets'].update(spin=0))
    def test_report_embedded_referee_mismatch(self):self.reject(lambda r:r['referee'].update(gateway_control_did_not_change_engine=False))
    def test_replay_digest_mismatch(self):self.reject(lambda r:r['replay'].update(sha256='a'*64))
    def test_abort_not_reached(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp);make_batch(p);path=p/'abort-after_ready/report.json'
            report=json.loads(path.read_text());report['status']='FAILED';path.write_text(json.dumps(report))
            with self.assertRaises(e.EvidenceError):e.validate_batch(p)
    def test_batch_cannot_point_outside_its_root(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp);make_batch(p);path=p/'batch.json';report=json.loads(path.read_text())
            report['battles']=['../other','battle-2'];path.write_text(json.dumps(report))
            with self.assertRaises(e.EvidenceError):e.validate_batch(p)

if __name__=='__main__':unittest.main()
