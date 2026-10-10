"""Synthetic contracts for reconciliation. No Docker, network or real game."""
from concurrent.futures import Future
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from services.worker_agent import arena_protocol as protocol
from services.worker_agent import arena_reconciliation as gate
from services.worker_agent.arena_evidence import EvidenceError
from services.worker_agent.bounded import ProcessBoundError
from test_arena_manifest import make_batch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('i2_reconciled_supervisor',ROOT/'scripts/run_separated_arena.py')
SUPERVISOR=importlib.util.module_from_spec(spec);spec.loader.exec_module(SUPERVISOR)
SOURCE='a'*40;CHECKOUT='b'*40
IMAGES={role:'sha256:'+str(i)*64 for i,role in enumerate(gate.ROLES,1)}


def read(path):return json.loads(path.read_text())
def write(path,data):path.write_text(json.dumps(data))
def completed(code=0,output=b''):
    result=Future();result.set_result(SimpleNamespace(returncode=code,output=output));return result


def fixture(root):
    make_batch(root)
    timeout=root/gate.TIMEOUT;timeout.mkdir()
    write(timeout/'report.json',{'schema_version':2,'status':'EXPECTED_TIMEOUT','scenario':gate.TIMEOUT,
        'cleanup_completed':True,'remaining_owned_containers':False,'remaining_owned_networks':False,
        'timeout_observed':True,'deadline_fixture_started':True,'battle_completed':False,
        'deadline_seconds':.5,'fixture_sleep_seconds':5})
    batch=read(root/'batch.json');batch.update(project_commit=CHECKOUT,images=IMAGES,timeout_check=gate.TIMEOUT)
    write(root/'batch.json',batch)
    for index,name in enumerate(gate.SCENARIOS,1):
        path=root/name/'report.json';report=read(path)
        report.update(schema_version=2,run_id=f'{index:024x}',images=IMAGES,
                      host_vm_tested=False,student_submission_enabled=False)
        if name in gate.BATTLES:
            report['bot_processes_verified']=True
            report['bot_processes']=SUPERVISOR.collect_bot_processes(
                {'walls':completed(),'spin':completed(137)}, {'walls'}, [])
        write(path,report)
    gate.write_manifest(root,source_commit=SOURCE,checkout_commit=CHECKOUT,
                        workflow_run_id=100,workflow_run_attempt=1)


class ReconciliationManifestTests(unittest.TestCase):
    def test_full_contract_and_independent_expected_values(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root)
            result=gate.validate_reconciled_batch(root,expected_source_commit=SOURCE,expected_workflow_run_id=100)
            self.assertEqual(result['unique_scenarios'],5)
            self.assertEqual(result['files_verified'],12)
            self.assertTrue(result['timeout_cleanup_passed'])
    def test_historical_batch_cannot_close_reconciliation(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);make_batch(root)
            with self.assertRaises(EvidenceError):gate.validate_reconciled_batch(root)
    def test_expected_source_and_workflow_are_not_self_asserted(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root)
            for kwargs in ({'expected_source_commit':'c'*40},{'expected_source_commit':''},
                           {'expected_workflow_run_id':101},{'expected_workflow_run_id':True}):
                with self.subTest(kwargs=kwargs),self.assertRaises(EvidenceError):
                    gate.validate_reconciled_batch(root,**kwargs)
    def test_missing_or_invalid_manifest_fields(self):
        changes=[lambda m:m.pop('source_commit'),lambda m:m.update(source_commit='unavailable'),
            lambda m:m.update(schema_version=True),lambda m:m.update(workflow_run_id=True),
            lambda m:m.update(workflow_run_attempt=0),lambda m:m.update(checkout_commit='c'*40),
            lambda m:m.update(images={'referee':IMAGES['referee']}),
            lambda m:m['images'].update(spin=IMAGES['walls']),lambda m:m['files'].pop('batch.json'),
            lambda m:m['files'].update({'../outside':'d'*64}),lambda m:m.update(unplanned=True)]
        for change in changes:
            with self.subTest(change=changes.index(change)),TemporaryDirectory() as tmp:
                root=Path(tmp);fixture(root);path=root/'reconciliation.json';manifest=read(path)
                change(manifest);write(path,manifest)
                with self.assertRaises(EvidenceError):gate.validate_reconciled_batch(root)
    def test_repeated_scenario_ids_rejected(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root);path=root/'reconciliation.json';manifest=read(path)
            manifest['scenario_run_ids']['battle-2']=manifest['scenario_run_ids']['battle-1'];write(path,manifest)
            with self.assertRaisesRegex(EvidenceError,'RUN_IDS'):gate.validate_reconciled_batch(root)
    def test_every_indexed_file_is_checked(self):
        for name in gate.FILES:
            with self.subTest(name=name),TemporaryDirectory() as tmp:
                root=Path(tmp);fixture(root);path=root/name;path.write_bytes(path.read_bytes()+b' ')
                with self.assertRaisesRegex(EvidenceError,'FILE_DIGEST'):gate.validate_reconciled_batch(root)
    def test_scenario_semantics_even_with_recomputed_hash(self):
        changes=[('abort-after_ready',lambda r:r.pop('host_vm_tested')),
            ('abort-after_containers',lambda r:r.update(student_submission_enabled=True)),
            ('battle-1',lambda r:r.update(images={'walls':IMAGES['walls']})),
            ('battle-2',lambda r:r.update(bot_processes_verified=False)),
            ('battle-1',lambda r:r['bot_processes']['walls'].update(returncode=137)),
            ('battle-2',lambda r:r['bot_processes']['spin'].update(returncode=True)),
            ('timeout-cleanup',lambda r:r.update(timeout_observed=1)),
            ('timeout-cleanup',lambda r:r.update(deadline_fixture_started=False)),
            ('timeout-cleanup',lambda r:r.update(battle_completed=True)),
            ('timeout-cleanup',lambda r:r.update(status='EXPECTED_ABORT')),
            ('timeout-cleanup',lambda r:r.update(fixture_sleep_seconds=True)),
            ('timeout-cleanup',lambda r:r.update(schema_version=2.0))]
        for name,change in changes:
            with self.subTest(name=name,change=changes.index((name,change))),TemporaryDirectory() as tmp:
                root=Path(tmp);fixture(root);path=root/name/'report.json';report=read(path)
                change(report);write(path,report)
                path=root/'reconciliation.json';manifest=read(path);manifest['files']=gate._hashes(root);write(path,manifest)
                with self.assertRaises(EvidenceError):gate.validate_reconciled_batch(root)
    def test_timeout_cannot_masquerade_as_battle(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root);write(root/gate.TIMEOUT/'results.json',{})
            with self.assertRaisesRegex(EvidenceError,'NON_BATTLE_HAS_RESULTS'):gate.validate_reconciled_batch(root)
    def test_manifest_is_never_overwritten(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root)
            with self.assertRaisesRegex(EvidenceError,'ALREADY_EXISTS'):
                gate.write_manifest(root,source_commit=SOURCE,checkout_commit=CHECKOUT,workflow_run_id=100,workflow_run_attempt=1)
    def test_indexed_symlink_is_rejected(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root);target=root/'batch.json';saved=root/'elsewhere'
            saved.write_bytes(target.read_bytes());target.unlink();target.symlink_to(saved)
            with self.assertRaises(EvidenceError):gate.validate_reconciled_batch(root)


class ReconciliationSupervisorTests(unittest.TestCase):
    def test_real_timeout_reason_and_started_fixture_required(self):
        with patch.object(SUPERVISOR,'docker',side_effect=[ProcessBoundError('TIMEOUT'),SimpleNamespace(returncode=0)]) as mock:
            result=SUPERVISOR.observe_fixed_timeout('owned')
        self.assertTrue(result['timeout_observed']);self.assertFalse(result['battle_completed'])
        self.assertEqual(mock.call_args_list[0].kwargs['timeout'],.5)
    def test_other_failures_never_count_as_timeout(self):
        for error in (ProcessBoundError('OUTPUT_LIMIT'),RuntimeError('DAEMON_UNAVAILABLE'),OSError()):
            with self.subTest(error=type(error)),patch.object(SUPERVISOR,'docker',side_effect=error):
                with self.assertRaises((RuntimeError,OSError)):SUPERVISOR.observe_fixed_timeout('owned')
    def test_normal_exit_is_not_timeout(self):
        for code in (0,1,137):
            with self.subTest(code=code),patch.object(SUPERVISOR,'docker',return_value=SimpleNamespace(returncode=code)):
                with self.assertRaisesRegex(RuntimeError,'TIMEOUT_NOT_OBSERVED'):SUPERVISOR.observe_fixed_timeout('owned')
    def test_fixture_not_started_is_not_proof(self):
        with patch.object(SUPERVISOR,'docker',side_effect=[ProcessBoundError('TIMEOUT'),SimpleNamespace(returncode=1)]):
            with self.assertRaisesRegex(RuntimeError,'FIXTURE_NOT_STARTED'):SUPERVISOR.observe_fixed_timeout('owned')
    def test_collects_normal_and_controlled_termination(self):
        report=SUPERVISOR.collect_bot_processes({'walls':completed(),'spin':completed(137)}, {'walls'}, [])
        self.assertEqual(report['walls']['termination'],'completed');self.assertEqual(report['spin']['termination'],'owned_cleanup')
    def test_bot_errors_and_secrets_cannot_be_discarded(self):
        bad=Future();bad.set_exception(ProcessBoundError('OUTPUT_LIMIT'))
        for tasks,early in (({},set()),({'walls':completed(1),'spin':completed()}, {'walls'}),
                            ({'walls':bad,'spin':completed()},set()),
                            ({'walls':completed(output=b'PRIVATE'),'spin':completed()},set())):
            with self.subTest(early=early),self.assertRaises(RuntimeError):
                SUPERVISOR.collect_bot_processes(tasks,early,['PRIVATE'])
    def test_early_bot_exit_before_official_end_rejected(self):
        ref=Future()
        with self.assertRaisesRegex(RuntimeError,'BOT_EXITED_BEFORE_GAME_END'):
            SUPERVISOR.wait_referee(ref,{'walls':completed()},lambda:False,timeout=1)
    def test_bot_crash_during_referee_execution_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'BOT_PROCESS_FAILED'):
            SUPERVISOR.wait_referee(Future(),{'walls':completed(1)},lambda:True,timeout=1)
    def test_valid_completion_uses_referee_result(self):
        result=SUPERVISOR.wait_referee(completed(output=b'official'),{},lambda:False)
        self.assertEqual(result.output,b'official')


class ReconciliationProtocolTests(unittest.TestCase):
    def test_global_nonfinite_and_excessive_integer_are_stable(self):
        for text in ('{"type":"BotHandshake","authors":[1e999]}',
                     '{"type":"BotIntent","x":'+'9'*5000+'}'):
            with self.subTest(text=text[:40]),self.assertRaises(protocol.ProtocolDenied):protocol.decode(text)
    def test_complete_reference_setup(self):
        setup=protocol.reference_setup()
        self.assertEqual((setup['gameType'],setup['numberOfRounds'],setup['minNumberOfParticipants'],setup['maxNumberOfParticipants']),('classic',3,2,2))
    def roster(self):return [{'name':'Walls','version':'1.0','host':'127.0.0.1','port':2000},
                            {'name':'Spin Bot','version':'1.0','host':'127.0.0.1','port':2001}]
    def test_engine_roster_addresses_preserved(self):
        self.assertEqual(protocol.reference_roster(self.roster()),[{'host':'127.0.0.1','port':2000},{'host':'127.0.0.1','port':2001}])
    def test_roster_mutations_rejected(self):
        mutations=[lambda r:r.pop(),lambda r:r[1].update(name='Walls'),lambda r:r[1].update(name='Other'),
            lambda r:r[0].update(version='2.0'),lambda r:r[1].update(port=2000),
            lambda r:r[0].update(port=True),lambda r:r[0].update(port=0),lambda r:r[0].update(port=65536),
            lambda r:r[0].update(host='referee'),lambda r:r[0].update(host='224.0.0.1'),lambda r:r[0].update(host=1)]
        for change in mutations:
            with self.subTest(change=mutations.index(change)):
                rows=self.roster();change(rows)
                with self.assertRaises(protocol.ProtocolDenied):protocol.reference_roster(rows)


if __name__=='__main__':unittest.main()
