"""Explicit unit doubles for I3-03B. Not real database/authentication evidence."""
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from services.execution_control import admission_bridge as b
from services.worker_agent import contracts as c

OWNER = '20000000-0000-4000-8000-000000000001'
JOB = '30000000-0000-4000-8000-000000000001'


class FakeConnection:
    def __init__(self, value, *, commit_fails=False, query_error=None, autocommit=False):
        self.value, self.commit_fails, self.query_error = value, commit_fails, query_error
        self.autocommit = autocommit
        self.prepare_threshold = 5
        self.calls, self.committed, self.rolled_back = [], False, False

    def __enter__(self):
        return self

    def __exit__(self, kind, exc, tb):
        if kind is not None:
            self.rolled_back = True
        elif self.commit_fails:
            raise RuntimeError('postgresql://private:password@internal invalid commit')
        else:
            self.committed = True
        return False

    def execute(self, query, values=None, **options):
        self.calls.append((query, values, options))
        if values is not None and self.query_error:
            raise self.query_error
        return self

    def fetchone(self):
        return (self.value,)


class AdmissionUnitTests(unittest.TestCase):
    def setUp(self):
        self.actor = b.ServiceActor(OWNER, 'lab-a')
        self.source = c.DSL.EXAMPLES['explorador']
        compiled = c.DSL.compile_program(self.source)
        self.snapshot = b.VersionSnapshot(hashlib.sha256(self.source.encode()).hexdigest(),
            compiled['program_sha256'], compiled['java_sha256'], 'a'*64, 1)
        self.repo = Mock()
        self.repo.snapshot.return_value = self.snapshot
        self.repo.enqueue.return_value = b.AdmissionReceipt(JOB, 'QUEUED', False)
        self.request = dict(schema_version=1,version_id='demo-v1',idempotency_key='request-1',rounds=3)
        self.service = b.AdmissionService(self.repo, enabled=True)

    def submit(self, data=None, source=None):
        return self.service.submit(json.dumps(self.request if data is None else data).encode(),
            self.source if source is None else source, actor=self.actor)

    def test_gate_off_never_touches_repository(self):
        service = b.AdmissionService(self.repo)
        with self.assertRaisesRegex(b.BridgeError, '^EXECUTION_DISABLED$'):
            service.submit(b'bad', self.source, actor=self.actor)
        self.repo.snapshot.assert_not_called()
        self.repo.enqueue.assert_not_called()

    def test_truthy_gate_is_not_accepted(self):
        with self.assertRaisesRegex(b.BridgeError, '^GATE_INVALID$'):
            b.AdmissionService(self.repo, enabled=1)

    def test_existing_i1_compiler_used_and_only_descriptor_is_persisted(self):
        with patch.object(c, 'admit', wraps=c.admit) as validator:
            result = self.submit()
        self.assertEqual(result.job_id, JOB)
        validator.assert_called_once()
        actor, key, descriptor, revision = self.repo.enqueue.call_args.args
        self.assertEqual((actor, key, revision), (self.actor, 'request-1', 1))
        self.assertEqual(set(descriptor), {'version_id','source_sha256','program_sha256',
            'java_sha256','policy_sha256','engine_ref','rounds'})
        self.assertNotIn(self.source, json.dumps(descriptor))

    def test_authority_fields_are_not_accepted_in_json(self):
        for name in ('owner_id','scope_id','worker_id','job_id','attempt_id','gate','deadline_at','policy_sha256'):
            with self.subTest(name=name), self.assertRaisesRegex(b.BridgeError,'^FIELDS_INVALID$'):
                self.submit({**self.request, name: 'forged'})
        self.repo.snapshot.assert_not_called()

    def test_duplicate_json_fields_are_denied(self):
        raw = json.dumps(self.request).encode()[:-1] + b',"rounds":2}'
        with self.assertRaisesRegex(b.BridgeError,'^DUPLICATE_FIELD$'):
            self.service.submit(raw, self.source, actor=self.actor)

    def test_invalid_and_nonfinite_json_are_denied(self):
        for raw in (b'\xff',b'{',b'{"rounds":NaN}',b'{"rounds":Infinity}'):
            with self.subTest(raw=raw), self.assertRaisesRegex(b.BridgeError,'^INVALID_JSON$'):
                self.service.submit(raw, self.source, actor=self.actor)
        self.repo.snapshot.assert_not_called()

    def test_oversize_body_is_denied(self):
        with self.assertRaisesRegex(b.BridgeError,'^REQUEST_SIZE$'):
            self.service.submit(b'x'*1025, self.source, actor=self.actor)

    def test_bool_or_invalid_rounds_are_denied(self):
        for rounds in (True,0,4,1.0,'1',None):
            with self.subTest(rounds=rounds), self.assertRaisesRegex(b.BridgeError,'^ROUNDS_INVALID$'):
                self.submit({**self.request,'rounds':rounds})

    def test_bool_or_new_schema_is_denied(self):
        for value in (True,2,'1'):
            with self.subTest(value=value), self.assertRaisesRegex(b.BridgeError,'^SCHEMA_INVALID$'):
                self.submit({**self.request,'schema_version':value})

    def test_identifier_injection_is_denied_before_sql(self):
        with self.assertRaisesRegex(b.BridgeError,'^IDENTIFIER_INVALID$'):
            self.submit({**self.request,'version_id':"x'; DROP SCHEMA rc_control CASCADE;--"})
        self.repo.snapshot.assert_not_called()

    def test_invalid_or_untyped_actor_denied(self):
        with self.assertRaisesRegex(b.BridgeError,'^ACTOR_INVALID$'):
            b.ServiceActor(OWNER,'../../lab-a')
        with self.assertRaisesRegex(b.BridgeError,'^ACTOR_INVALID$'):
            self.service.submit(json.dumps(self.request).encode(),self.source,
                                actor={'owner_id':OWNER,'scope_id':'lab-a'})

    def test_source_mismatch_has_no_enqueue(self):
        with self.assertRaisesRegex(b.BridgeError,'^SOURCE_MISMATCH$'):
            self.submit(source=self.source+' ')
        self.repo.enqueue.assert_not_called()

    def test_oversize_source_has_no_lookup(self):
        with self.assertRaisesRegex(b.BridgeError,'^SOURCE_SIZE$'):
            self.submit(source='x'*(c.DSL.MAX_BYTES+1))
        self.repo.snapshot.assert_not_called()

    def test_java_compiler_drift_denied(self):
        self.repo.snapshot.return_value = replace(self.snapshot,java_sha256='b'*64)
        with self.assertRaisesRegex(b.BridgeError,'^JAVA_MISMATCH$'):
            self.submit()
        self.repo.enqueue.assert_not_called()

    def test_version_revoked_before_lookup_denied(self):
        self.repo.snapshot.side_effect = b.BridgeError('VERSION_UNAUTHORIZED')
        with self.assertRaisesRegex(b.BridgeError,'^VERSION_UNAUTHORIZED$'):
            self.submit()
        self.repo.enqueue.assert_not_called()

    def test_revision_change_during_compile_is_propagated(self):
        self.repo.enqueue.side_effect = b.BridgeError('VERSION_CHANGED')
        with self.assertRaisesRegex(b.BridgeError,'^VERSION_CHANGED$'):
            self.submit()
        self.assertEqual(self.repo.enqueue.call_count,1)

    def test_sql_values_are_bound_not_interpolated(self):
        conn = FakeConnection(asdict(self.snapshot))
        repo = b.PostgresAdmissionRepository(lambda:conn)
        injected = "demo-v1' OR true;--"
        self.assertEqual(repo.snapshot(self.actor,injected),self.snapshot)
        query, values, options = conn.calls[-1]
        self.assertEqual(query,repo.SNAPSHOT_SQL)
        self.assertNotIn(injected,query)
        self.assertEqual(values,(OWNER,'lab-a',injected))
        self.assertEqual(options,{'prepare':False})
        self.assertIsNone(conn.prepare_threshold)
        self.assertTrue(conn.committed)

    def test_receipt_returned_only_after_commit(self):
        conn = FakeConnection(dict(job_id=JOB,state='QUEUED',duplicate=False))
        result = b.PostgresAdmissionRepository(lambda:conn).enqueue(self.actor,'key',{},1)
        self.assertTrue(conn.committed)
        self.assertEqual(result.job_id,JOB)

    def test_commit_failure_never_returns_success_or_secret(self):
        conn = FakeConnection(dict(job_id=JOB,state='QUEUED',duplicate=False),commit_fails=True)
        with self.assertRaisesRegex(b.BridgeError,'^STORAGE_UNAVAILABLE$'):
            b.PostgresAdmissionRepository(lambda:conn).enqueue(self.actor,'key',{},1)
        self.assertFalse(conn.committed)

    def test_invalid_database_response_rolls_back(self):
        conn = FakeConnection(dict(job_id=JOB,state='COMPLETED',duplicate=False))
        with self.assertRaisesRegex(b.BridgeError,'^DATABASE_RESPONSE_INVALID$'):
            b.PostgresAdmissionRepository(lambda:conn).enqueue(self.actor,'key',{},1)
        self.assertTrue(conn.rolled_back)

    def test_domain_errors_are_allowlisted(self):
        for message,expected in [('VERSION_CHANGED','VERSION_CHANGED'),
                                 ('password=private\nSQL data','STORAGE_UNAVAILABLE')]:
            exc = RuntimeError(message)
            exc.diag = SimpleNamespace(message_primary=message)
            conn = FakeConnection(None,query_error=exc)
            with self.subTest(message=message),self.assertRaisesRegex(b.BridgeError,'^'+expected+'$'):
                b.PostgresAdmissionRepository(lambda:conn).snapshot(self.actor,'demo-v1')
            self.assertTrue(conn.rolled_back)

    def test_autocommit_factory_is_refused(self):
        conn = FakeConnection(asdict(self.snapshot),autocommit=True)
        with self.assertRaisesRegex(b.BridgeError,'^CONNECTION_CONFIG_INVALID$'):
            b.PostgresAdmissionRepository(lambda:conn).snapshot(self.actor,'demo-v1')
        self.assertEqual(conn.calls,[])

    def test_connection_failure_never_falls_back_to_sqlite(self):
        connect = Mock(side_effect=OSError('private-dsn'))
        with self.assertRaisesRegex(b.BridgeError,'^STORAGE_UNAVAILABLE$'):
            b.PostgresAdmissionRepository(connect).snapshot(self.actor,'demo-v1')
        connect.assert_called_once_with()

    def test_compilation_does_not_launch_a_bot_or_network(self):
        with patch('subprocess.Popen',side_effect=AssertionError('no process')),
             patch('socket.create_connection',side_effect=AssertionError('no network')):
            self.assertEqual(self.submit().state,'QUEUED')

    def test_snapshot_contract_rejects_invalid_types(self):
        with self.assertRaisesRegex(b.BridgeError,'^DATABASE_RESPONSE_INVALID$'):
            replace(self.snapshot,revision=True)
        with self.assertRaisesRegex(b.BridgeError,'^DATABASE_RESPONSE_INVALID$'):
            replace(self.snapshot,java_sha256='x')
