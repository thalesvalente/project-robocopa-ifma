"""Real I1 -> Psycopg -> PostgreSQL integration in a disposable GitHub runner.

Only synthetic identities/certified examples. Database password authentication
is real, but NOT HTTP/JWT user authentication. No host VM or remote Supabase.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import psycopg
from services.execution_control import admission_bridge as b
from services.worker_agent import contracts as c
from test_control import sql, lit, command, NAME, RUN, OWNER, OTHER, W1, DatabaseError

MIGRATIONS = [ROOT/'services/execution_control/postgres'/name
              for name in ('001_control.sql','002_admission.sql')]


class AdmissionIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if (sys.platform!='linux' or os.environ.get('GITHUB_ACTIONS')!='true'
                or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted'
                or not re.fullmatch(r'robocopa-i3pg-[0-9]+-[0-9]+',NAME)):
            raise AssertionError('DISPOSABLE_CI_REQUIRED')
        inspected = command(['docker','inspect',NAME])
        if inspected.returncode:
            raise AssertionError('DATABASE_MISSING')
        obj = json.loads(inspected.stdout)[0]
        assert obj['Config']['Labels'].get('org.robocopa.i3pg.run') == RUN
        assert obj['HostConfig']['NetworkMode']=='none' and not obj['HostConfig']['PortBindings']
        cls.socket = Path(os.environ['RC_PG_SOCKET'])
        cls.temp_root = Path(os.environ['RC_ADMISSION_ROOT'])
        assert cls.socket == cls.temp_root/'socket'
        assert cls.temp_root.parent == Path(os.environ['RUNNER_TEMP'])
        assert cls.temp_root.name == 'robocopa-admission-'+RUN+'-'+os.environ['GITHUB_RUN_ATTEMPT']
        expected = {'/var/lib/postgresql/data','/var/run/postgresql','/etc/rc-ci-hba.conf'}
        assert {m['Destination'] for m in obj['Mounts']} == expected
        for m in obj['Mounts']:
            if m['Destination']=='/var/run/postgresql':
                assert m['Type']=='bind' and m['Source']==str(cls.socket)
            if m['Destination']=='/etc/rc-ci-hba.conf':
                assert m['Type']=='bind' and not m['RW']
        cls.image_id = obj['Image']
        cls.pg_version = sql('SHOW server_version;','postgres')
        for path in MIGRATIONS:
            sql(path.read_text(),'postgres',wrap=False)
        cls.password = secrets.token_hex(32)
        # Constant role name, random synthetic hex password. SQL travels only via stdin.
        sql('CREATE ROLE rc_admission_ci LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE '
            'NOREPLICATION NOBYPASSRLS PASSWORD '+lit(cls.password)+'; '
            'GRANT rc_admission TO rc_admission_ci;','postgres')
        with cls.connect() as conn:
            assert conn.execute('SELECT current_user,session_user').fetchone() == (
                'rc_admission_ci','rc_admission_ci')
        cls.source = c.DSL.EXAMPLES['explorador']
        cls.compiled = c.DSL.compile_program(cls.source)
        cls.hash_source = hashlib.sha256(cls.source.encode()).hexdigest()

    @classmethod
    def connect(cls):
        return psycopg.connect(host=str(cls.socket), dbname='robocopa_i3_ci',
            user='rc_admission_ci',password=cls.password,connect_timeout=3,
            autocommit=False,prepare_threshold=None)

    def setUp(self):
        sql('TRUNCATE rc_control.attempts,rc_control.jobs,rc_control.workers,rc_control.approved_versions; '
            "UPDATE rc_control.settings SET enabled=true,capacity=32,policy_sha256=repeat('a',64); "
            f"INSERT INTO rc_control.workers VALUES ('{W1}','lab-a',true); "
            'INSERT INTO rc_control.approved_versions(owner_id,scope_id,version_id,source_sha256,'
            'program_sha256,java_sha256,active) VALUES ('+
            ','.join(lit(v) for v in (OWNER,'lab-a','demo-v1',self.hash_source,
              self.compiled['program_sha256'],self.compiled['java_sha256']))+',true);','postgres')
        self.actor = b.ServiceActor(OWNER,'lab-a')
        self.repo = b.PostgresAdmissionRepository(self.connect)
        self.service = b.AdmissionService(self.repo,enabled=True)
        self.request = dict(schema_version=1,version_id='demo-v1',idempotency_key='request-1',rounds=3)

    def submit(self, *, service=None, actor=None, request=None, source=None):
        return (self.service if service is None else service).submit(
            json.dumps(self.request if request is None else request).encode(),
            self.source if source is None else source,
            actor=self.actor if actor is None else actor)

    def jobs(self):
        return int(sql('SELECT count(*) FROM rc_control.jobs;','postgres'))

    def descriptor(self):
        return dict(version_id='demo-v1',source_sha256=self.hash_source,
            program_sha256=self.compiled['program_sha256'],java_sha256=self.compiled['java_sha256'],
            policy_sha256='a'*64,engine_ref=c.ENGINE,rounds=3)

    def test_real_end_to_end_admit_enqueue_claim_start_cancel(self):
        receipt = self.submit()
        self.assertEqual(receipt.state,'QUEUED')
        leased = json.loads(sql(f"SELECT rc_control.claim('{W1}');"))
        self.assertEqual(leased['job_id'],receipt.job_id)
        self.assertEqual(leased['descriptor'],self.descriptor())
        args = ','.join(lit(x) for x in (W1,receipt.job_id,leased['attempt_id']))
        started = json.loads(sql('SELECT rc_control.heartbeat('+args+','+str(leased['fence'])+',true);'))
        self.assertEqual(started['state'],'RUNNING')
        self.assertEqual(sql('SELECT rc_control.cancel('+lit(receipt.job_id)+','+lit(OWNER)+');'),'CANCELLED')

    def test_restricted_login_uses_scram_not_set_role(self):
        with self.connect() as conn:
            self.assertEqual(conn.execute('SELECT current_user,session_user').fetchone(),
                             ('rc_admission_ci','rc_admission_ci'))
        with self.assertRaises(psycopg.OperationalError):
            psycopg.connect(host=str(self.socket),dbname='robocopa_i3_ci',
                user='rc_admission_ci',password='wrong-fixture-password',connect_timeout=3)
        self.assertEqual(sql("SELECT rolpassword LIKE 'SCRAM-SHA-256$%' FROM pg_authid "
                             "WHERE rolname='rc_admission_ci';",'postgres'),'t')

    def test_duplicate_through_driver_keeps_job_and_deadline(self):
        first = self.submit()
        deadline = sql('SELECT deadline_at FROM rc_control.jobs;','postgres')
        second = self.submit(service=b.AdmissionService(b.PostgresAdmissionRepository(self.connect),enabled=True))
        self.assertTrue(second.duplicate)
        self.assertEqual(first.job_id,second.job_id)
        self.assertEqual(sql('SELECT deadline_at FROM rc_control.jobs;','postgres'),deadline)
        self.assertEqual(self.jobs(),1)

    def test_concurrent_driver_requests_create_one_job(self):
        with ThreadPoolExecutor(max_workers=6) as pool:
            replies = list(pool.map(lambda _:self.submit(),range(12)))
        self.assertEqual(len({r.job_id for r in replies}),1)
        self.assertEqual(sum(not r.duplicate for r in replies),1)
        self.assertEqual(self.jobs(),1)

    def test_same_key_different_rounds_conflicts(self):
        self.submit()
        with self.assertRaisesRegex(b.BridgeError,'^IDEMPOTENCY_CONFLICT$'):
            self.submit(request={**self.request,'rounds':2})
        self.assertEqual(self.jobs(),1)

    def test_queue_full_allows_existing_duplicate(self):
        sql('UPDATE rc_control.settings SET capacity=1;','postgres')
        self.submit()
        with self.assertRaisesRegex(b.BridgeError,'^QUEUE_FULL$'):
            self.submit(request={**self.request,'idempotency_key':'second'})
        self.assertTrue(self.submit().duplicate)

    def test_owner_or_scope_cannot_read_another_version(self):
        for actor in (b.ServiceActor(OTHER,'lab-a'),b.ServiceActor(OWNER,'lab-b')):
            with self.subTest(actor=actor),self.assertRaisesRegex(b.BridgeError,'^VERSION_UNAUTHORIZED$'):
                self.submit(actor=actor)
        self.assertEqual(self.jobs(),0)

    def test_unregistered_version_refused(self):
        with self.assertRaisesRegex(b.BridgeError,'^VERSION_UNAUTHORIZED$'):
            self.submit(request={**self.request,'version_id':'absent'})

    def test_revocation_during_compilation_prevents_enqueue(self):
        original = c.admit
        def revoke(*args,**kwargs):
            sql('UPDATE rc_control.approved_versions SET active=false;','postgres')
            return original(*args,**kwargs)
        with patch.object(c,'admit',side_effect=revoke):
            with self.assertRaisesRegex(b.BridgeError,'^VERSION_UNAUTHORIZED$'):
                self.submit()
        self.assertEqual(self.jobs(),0)

    def test_revoke_reactivate_does_not_reuse_snapshot_revision(self):
        snapshot = self.repo.snapshot(self.actor,'demo-v1')
        sql('UPDATE rc_control.approved_versions SET active=false; '
            'UPDATE rc_control.approved_versions SET active=true;','postgres')
        with self.assertRaisesRegex(b.BridgeError,'^VERSION_CHANGED$'):
            self.repo.enqueue(self.actor,'key',self.descriptor(),snapshot.revision)
        self.assertEqual(self.jobs(),0)

    def test_policy_change_during_compile_is_rechecked(self):
        original = c.admit
        def change_policy(*args,**kwargs):
            sql("UPDATE rc_control.settings SET policy_sha256=repeat('b',64);",'postgres')
            return original(*args,**kwargs)
        with patch.object(c,'admit',side_effect=change_policy):
            with self.assertRaisesRegex(b.BridgeError,'^POLICY_MISMATCH$'):
                self.submit()
        self.assertEqual(self.jobs(),0)

    def test_disabled_service_makes_no_database_connection(self):
        with patch.object(self.repo,'_connect',side_effect=AssertionError('must not connect')):
            with self.assertRaisesRegex(b.BridgeError,'^EXECUTION_DISABLED$'):
                self.submit(service=b.AdmissionService(self.repo))

    def test_disabled_database_gate_refuses_snapshot(self):
        sql('UPDATE rc_control.settings SET enabled=false;','postgres')
        with self.assertRaisesRegex(b.BridgeError,'^EXECUTION_DISABLED$'):
            self.submit()
        self.assertEqual(self.jobs(),0)

    def test_source_hash_mismatch_has_no_job(self):
        with self.assertRaisesRegex(b.BridgeError,'^SOURCE_MISMATCH$'):
            self.submit(source=self.source+' ')
        self.assertEqual(self.jobs(),0)

    def test_java_hash_mismatch_is_rejected_by_database(self):
        snapshot = self.repo.snapshot(self.actor,'demo-v1')
        with self.assertRaisesRegex(b.BridgeError,'^VERSION_MISMATCH$'):
            self.repo.enqueue(self.actor,'key',{**self.descriptor(),'java_sha256':'b'*64},snapshot.revision)

    def test_version_hashes_are_immutable_even_to_normal_admin_update(self):
        with self.assertRaisesRegex(DatabaseError,'VERSION_IMMUTABLE'):
            sql("UPDATE rc_control.approved_versions SET java_sha256=repeat('b',64);",'postgres')
        self.assertEqual(self.repo.snapshot(self.actor,'demo-v1').revision,1)

    def test_admission_role_has_no_table_claim_or_gate_permissions(self):
        for query in ('SELECT * FROM rc_control.jobs','SELECT * FROM rc_control.approved_versions',
                      'UPDATE rc_control.settings SET enabled=true',
                      "SELECT rc_control.claim('"+W1+"')"):
            with self.subTest(query=query),self.connect() as conn:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    conn.execute(query)
                conn.rollback()

    def test_execution_role_cannot_bypass_version_admission(self):
        query = "SELECT rc_control.enqueue('"+OWNER+"','lab-a','k','{}'::jsonb,clock_timestamp());"
        with self.assertRaisesRegex(DatabaseError,'PERMISSION_DENIED'):
            sql(query)

    def test_rls_still_denies_if_select_was_accidentally_granted(self):
        sql('GRANT SELECT ON rc_control.approved_versions TO rc_admission;','postgres')
        try:
            with self.connect() as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM rc_control.approved_versions').fetchone()[0],0)
        finally:
            sql('REVOKE SELECT ON rc_control.approved_versions FROM rc_admission;','postgres')

    def test_parameter_injection_reaches_database_as_data_only(self):
        with self.assertRaisesRegex(b.BridgeError,'^VERSION_UNAUTHORIZED$'):
            self.repo.snapshot(self.actor,"demo-v1'; DROP SCHEMA rc_control CASCADE;--")
        self.assertEqual(self.jobs(),0)
        self.assertEqual(self.submit().state,'QUEUED')

    def test_reapplying_migration_refuses_without_losing_jobs(self):
        self.submit()
        with self.assertRaises(DatabaseError):
            sql(MIGRATIONS[1].read_text(),'postgres',wrap=False)
        self.assertEqual(self.jobs(),1)

    def test_postgres_and_python_do_not_persist_source(self):
        self.submit()
        result = sql('SELECT descriptor::text FROM rc_control.jobs;','postgres')
        self.assertNotIn(self.source,result)
        self.assertEqual(set(json.loads(result)),set(self.descriptor()))


if __name__=='__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AdmissionIntegrationTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    path = ROOT/'.local/i3-admission/report.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    report = dict(schema_version=1,status='PASS' if result.wasSuccessful() and result.testsRun else 'FAIL',
        tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        source_commit=os.environ.get('RC_SOURCE_COMMIT'),workflow_run_id=RUN,
        postgres_version=getattr(AdmissionIntegrationTests,'pg_version',None),
        psycopg_version=psycopg.__version__,real_postgres=True,real_driver=True,
        authentication='SCRAM_DATABASE_LOGIN_ONLY_NOT_USER_JWT',
        migration_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in MIGRATIONS},
        deploy=False,student_data=False,host_vm=False,cleanup='PENDING')
    path.write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if report['status']=='PASS' else 1)
