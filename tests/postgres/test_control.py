"""Real PostgreSQL integration in an owned, network-none GitHub CI container.

No SQLite substitution, no Supabase account, no VM/user data. Test connections
impersonate SQL roles with SET LOCAL ROLE; this is NOT HTTP authentication.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
NAME = os.environ.get('RC_PG_CONTAINER', '')
RUN = os.environ.get('GITHUB_RUN_ID', '')
W1 = '10000000-0000-4000-8000-000000000001'
W2 = '10000000-0000-4000-8000-000000000002'
OWNER = '20000000-0000-4000-8000-000000000001'
OTHER = '20000000-0000-4000-8000-000000000002'
MIGRATION = ROOT/'services/execution_control/postgres/001_control.sql'


def command(args, *, body=None, timeout=20):
    return subprocess.run(args, input=body, text=True, capture_output=True,
                          timeout=timeout, check=False)


def psql():
    return ['docker','exec','-i','--user','postgres',NAME,'psql','-XqAt',
            '-v','ON_ERROR_STOP=1','-U','postgres','-d','robocopa_i3_ci','-f','-']


class DatabaseError(ValueError):
    pass


def sql(body, role='rc_broker', *, wrap=True):
    if role not in ('rc_broker','postgres','anon','authenticated','rc_worker_client'):
        raise ValueError('ROLE_NOT_A_FIXTURE')
    query = (f"BEGIN; SET LOCAL ROLE {role}; SET LOCAL statement_timeout='10s';\n"
             + body + '\nCOMMIT;') if wrap else body
    out = command(psql(), body=query)
    if out.returncode:
        if 'permission denied' in out.stderr or 'must be' in out.stderr:
            raise DatabaseError('PERMISSION_DENIED')
        codes = re.findall(r'ERROR:\s+([A-Z][A-Z_]{3,})', out.stderr)
        raise DatabaseError(codes[0] if codes else 'SQL_OPERATION_FAILED')
    return out.stdout.strip()


def lit(value):
    return "'"+str(value).replace("'", "''")+"'"


class ControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if (sys.platform != 'linux' or os.environ.get('GITHUB_ACTIONS') != 'true'
            or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted'
            or not re.fullmatch(r'robocopa-i3pg-[0-9]+-[0-9]+', NAME)):
            raise AssertionError('DISPOSABLE_CI_REQUIRED')
        inspected = command(['docker','inspect',NAME])
        if inspected.returncode:
            raise AssertionError('OWNED_DATABASE_MISSING')
        obj = json.loads(inspected.stdout)[0]
        assert obj['Config']['Labels'].get('org.robocopa.i3pg.run') == RUN
        assert obj['HostConfig']['NetworkMode'] == 'none'
        assert not obj['HostConfig']['PortBindings']
        assert all(m['Type']=='volume' and m['Destination']=='/var/lib/postgresql/data'
                   for m in obj['Mounts'])
        cls.version = sql('SHOW server_version;', 'postgres')
        assert int(sql('SHOW server_version_num;', 'postgres')) // 10000 == 17
        cls.image_id = obj['Image']
        sql(MIGRATION.read_text(), 'postgres', wrap=False)
        sql('CREATE ROLE anon NOLOGIN; CREATE ROLE authenticated NOLOGIN; '
            'CREATE ROLE rc_worker_client NOLOGIN;', 'postgres')

    def setUp(self):
        sql("TRUNCATE rc_control.attempts,rc_control.jobs,rc_control.workers; "
            "UPDATE rc_control.settings SET enabled=true,capacity=32,lease_seconds=30,"
            "attempt_limit=3,policy_sha256=repeat('a',64); "
            f"INSERT INTO rc_control.workers VALUES ('{W1}','lab-a',true),"
            f"('{W2}','lab-b',true);", 'postgres')
        self.deadline = sql("SELECT (clock_timestamp()+interval '120 seconds')::text;", 'postgres')
        self.descriptor = dict(version_id='demo-v1',source_sha256='1'*64,
            program_sha256='2'*64,java_sha256='3'*64,policy_sha256='a'*64,
            engine_ref='tank-royale/1.4.0',rounds=3)

    def enq_query(self, key='demo', owner=OWNER, scope='lab-a', descriptor=None, deadline=None):
        args = [lit(owner),lit(scope),lit(key),lit(json.dumps(
            self.descriptor if descriptor is None else descriptor))+'::jsonb',
            lit(self.deadline if deadline is None else deadline)+'::timestamptz']
        return 'SELECT rc_control.enqueue('+','.join(args)+');'

    def enq(self, **kw):
        return json.loads(sql(self.enq_query(**kw)))

    def claim(self, worker=W1):
        result = sql(f"SELECT rc_control.claim('{worker}');")
        return json.loads(result) if result else None

    def beat(self, job, *, worker=W1, start=False, fence=None, attempt=None):
        args=[lit(worker),lit(job['job_id']),lit(attempt or job['attempt_id']),
              str(job['fence'] if fence is None else fence),str(start).lower()]
        return json.loads(sql('SELECT rc_control.heartbeat('+','.join(args)+');'))

    def count(self, table='jobs'):
        assert table in ('jobs','attempts')
        return int(sql(f'SELECT count(*) FROM rc_control.{table};','postgres'))

    def state(self, job):
        return sql(f"SELECT state FROM rc_control.jobs WHERE job_id={lit(job['job_id'])};",'postgres')

    def expire_lease(self, job):
        # Deterministic administrative fixture. One separate test waits for real time.
        sql("UPDATE rc_control.jobs SET lease_until=clock_timestamp()-interval '1 second' "
            f"WHERE job_id={lit(job['job_id'])};",'postgres')

    def test_gate_off_refuses_allocation(self):
        sql('UPDATE rc_control.settings SET enabled=false;','postgres')
        with self.assertRaisesRegex(DatabaseError,'EXECUTION_DISABLED'): self.enq()
        with self.assertRaisesRegex(DatabaseError,'EXECUTION_DISABLED'): self.claim()
        self.assertEqual(self.count(),0)

    def test_migration_defaults_disabled_and_not_reapplied(self):
        value=sql("SELECT pg_get_expr(d.adbin,d.adrelid) FROM pg_attrdef d "
            "JOIN pg_attribute a ON a.attrelid=d.adrelid AND a.attnum=d.adnum "
            "WHERE d.adrelid='rc_control.settings'::regclass AND a.attname='enabled';",'postgres')
        self.assertEqual(value,'false')
        self.enq()
        with self.assertRaises(DatabaseError): sql(MIGRATION.read_text(),'postgres',wrap=False)
        self.assertEqual(self.count(),1)

    def test_idempotence_and_conflict(self):
        a,b=self.enq(),self.enq()
        self.assertEqual(a['job_id'],b['job_id']); self.assertTrue(b['duplicate'])
        with self.assertRaisesRegex(DatabaseError,'IDEMPOTENCY_CONFLICT'):
            self.enq(descriptor={**self.descriptor,'rounds':2})
        self.assertEqual(self.count(),1)

    def test_owner_scoped_idempotency(self):
        self.assertNotEqual(self.enq()['job_id'],self.enq(owner=OTHER)['job_id'])

    def test_repeated_concurrent_requests_insert_once(self):
        with ThreadPoolExecutor(max_workers=6) as p:
            rows=list(p.map(lambda _:self.enq(),range(12)))
        self.assertEqual(len({r['job_id'] for r in rows}),1)
        self.assertEqual(sum(not r['duplicate'] for r in rows),1)
        self.assertEqual(self.count(),1)

    def test_capacity_atomic_across_connections(self):
        sql('UPDATE rc_control.settings SET capacity=3;','postgres')
        def submit(i):
            try: self.enq(key=f'k{i}'); return 'OK'
            except DatabaseError as e: return str(e)
        with ThreadPoolExecutor(max_workers=8) as p: out=list(p.map(submit,range(8)))
        self.assertEqual(out.count('OK'),3); self.assertEqual(out.count('QUEUE_FULL'),5)
        self.assertEqual(self.count(),3)

    def test_duplicate_still_works_at_capacity(self):
        sql('UPDATE rc_control.settings SET capacity=1;','postgres')
        self.enq(); self.assertTrue(self.enq()['duplicate'])
        with self.assertRaisesRegex(DatabaseError,'QUEUE_FULL'): self.enq(key='other')

    def test_one_claim_for_one_job_under_race(self):
        self.enq()
        with ThreadPoolExecutor(max_workers=6) as p: rows=list(p.map(lambda _:self.claim(),range(12)))
        self.assertEqual(sum(r is not None for r in rows),1)
        self.assertEqual(self.count('attempts'),1)

    def test_skip_locked_picks_other_row(self):
        first=self.enq(key='first'); second=self.enq(key='second')
        proc=subprocess.Popen(psql(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,text=True)
        try:
            proc.stdin.write("BEGIN; SELECT job_id FROM rc_control.jobs WHERE job_id="+
                lit(first['job_id'])+" FOR UPDATE;\n\\echo LOCKED\nSELECT pg_sleep(3); COMMIT;\n")
            proc.stdin.flush()
            for _ in range(4):
                if proc.stdout.readline().strip()=='LOCKED': break
            else: self.fail('LOCK_FIXTURE_NOT_READY')
            self.assertEqual(self.claim()['job_id'],second['job_id'])
        finally:
            proc.stdin.close(); proc.stdin=None
            proc.communicate(timeout=10)
        self.assertEqual(proc.returncode,0)

    def test_scopes_do_not_cross(self):
        b=self.enq(scope='lab-b')
        self.assertIsNone(self.claim(W1)); self.assertEqual(self.claim(W2)['job_id'],b['job_id'])

    def test_revoked_worker_denied(self):
        self.enq(); sql(f"UPDATE rc_control.workers SET active=false WHERE worker_id='{W1}';",'postgres')
        with self.assertRaisesRegex(DatabaseError,'WORKER_DENIED'): self.claim()
        self.assertEqual(self.count('attempts'),0)

    def test_start_and_heartbeat_keep_generation_and_deadline(self):
        self.enq(); j=self.claim(); response=self.beat(j,start=True)
        self.assertEqual(response['state'],'RUNNING'); self.assertEqual(response['fence'],j['fence'])
        response=self.beat(j); self.assertEqual(response['state'],'RUNNING')
        self.assertLessEqual(datetime.fromisoformat(response['lease_until']),
                             datetime.fromisoformat(j['deadline_at']))

    def test_wrong_worker_attempt_and_fence_denied(self):
        self.enq(); j=self.claim()
        for opts in ({'worker':W2},{'attempt':OTHER},{'fence':j['fence']+1}):
            with self.subTest(opts=opts),self.assertRaisesRegex(DatabaseError,'STALE_LEASE'):
                self.beat(j,**opts)
        self.assertEqual(self.state(j),'LEASED')

    def test_expired_lease_reclaimed_with_new_fence(self):
        self.enq(); old=self.claim(); self.expire_lease(old)
        with self.assertRaisesRegex(DatabaseError,'STALE_LEASE'): self.beat(old)
        self.assertEqual(sql('SELECT rc_control.reap();'),'1')
        new=self.claim()
        self.assertGreater(new['fence'],old['fence']); self.assertNotEqual(new['attempt_id'],old['attempt_id'])
        with self.assertRaisesRegex(DatabaseError,'STALE_LEASE'): self.beat(old)
        self.assertEqual(self.count('attempts'),2)

    def test_real_clock_expiration(self):
        sql('UPDATE rc_control.settings SET lease_seconds=1;','postgres')
        self.enq(); j=self.claim(); time.sleep(1.2)
        with self.assertRaisesRegex(DatabaseError,'STALE_LEASE'): self.beat(j)
        self.assertEqual(sql('SELECT rc_control.reap();'),'1')
        self.assertGreater(self.claim()['fence'],j['fence'])

    def test_deadline_and_attempt_exhaustion_terminal(self):
        sql('UPDATE rc_control.settings SET attempt_limit=1;','postgres')
        self.enq(); j=self.claim(); self.expire_lease(j)
        sql('SELECT rc_control.reap();'); self.assertEqual(self.state(j),'FAILED')
        self.assertIsNone(self.claim())
        other=self.enq(key='expired')
        sql("UPDATE rc_control.jobs SET deadline_at=clock_timestamp()-interval '1 second' "
            f"WHERE job_id={lit(other['job_id'])};",'postgres')
        sql('SELECT rc_control.reap();'); self.assertEqual(self.state(other),'EXPIRED')
        self.assertIsNone(self.claim())

    def test_cancel_is_idempotent_and_not_claimable(self):
        j=self.enq()
        for _ in range(2): self.assertEqual(sql(f"SELECT rc_control.cancel({lit(j['job_id'])},'{OWNER}');"),'CANCELLED')
        self.assertIsNone(self.claim())

    def test_cancel_wrong_owner_denied(self):
        j=self.enq()
        with self.assertRaisesRegex(DatabaseError,'JOB_NOT_OWNED'):
            sql(f"SELECT rc_control.cancel({lit(j['job_id'])},'{OTHER}');")
        self.assertEqual(self.state(j),'QUEUED')

    def test_cancel_heartbeat_race_leaves_no_active_lease(self):
        self.enq(); j=self.claim()
        def beat():
            try: self.beat(j,start=True); return 'OK'
            except DatabaseError as e: return str(e)
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(beat)
            b=pool.submit(sql,f"SELECT rc_control.cancel({lit(j['job_id'])},'{OWNER}');")
            self.assertIn(a.result(),('OK','STALE_LEASE')); self.assertEqual(b.result(),'CANCELLED')
        self.assertEqual(self.state(j),'CANCELLED')
        with self.assertRaisesRegex(DatabaseError,'STALE_LEASE'): self.beat(j)

    def test_failure_retries_after_backoff_without_reusing_attempt(self):
        self.enq(); j=self.claim()
        args=f"'{W1}',{lit(j['job_id'])},{lit(j['attempt_id'])},{j['fence']}"
        with self.assertRaisesRegex(DatabaseError,'REASON_INVALID'):
            sql(f"SELECT rc_control.fail_attempt({args},'private-raw-error');")
        self.assertEqual(sql(f"SELECT rc_control.fail_attempt({args},'ENGINE_FAILURE');"),'QUEUED')
        self.assertIsNone(self.claim()); time.sleep(1.1)
        self.assertGreater(self.claim()['fence'],j['fence'])
        with self.assertRaisesRegex(DatabaseError,'STALE_LEASE'): self.beat(j)

    def test_revocation_invalidates_existing_authority(self):
        self.enq(); j=self.claim()
        sql(f"UPDATE rc_control.workers SET active=false WHERE worker_id='{W1}';",'postgres')
        with self.assertRaisesRegex(DatabaseError,'WORKER_DENIED'): self.beat(j)
        self.assertEqual(sql('SELECT rc_control.reap();'),'1'); self.assertEqual(self.state(j),'QUEUED')

    def test_transaction_rollback_has_no_job(self):
        sql('BEGIN; SET LOCAL ROLE rc_broker; '+self.enq_query()+' ROLLBACK;','postgres',wrap=False)
        self.assertEqual(self.count(),0)

    def test_restart_preserves_jobs_and_lease(self):
        receipt=self.enq(); j=self.claim()
        result=command(['docker','restart',NAME],timeout=30)
        self.assertEqual(result.returncode,0)
        for _ in range(50):
            if command(['docker','exec',NAME,'pg_isready','-U','postgres','-d','robocopa_i3_ci']).returncode==0: break
            time.sleep(.1)
        else: self.fail('DATABASE_RESTART_NOT_READY')
        self.assertEqual(self.count(),1)
        self.assertEqual(self.enq()['job_id'],receipt['job_id'])
        self.assertEqual(self.beat(j,start=True)['state'],'RUNNING')

    def test_public_and_worker_roles_have_no_access(self):
        self.enq()
        for role in ('anon','authenticated','rc_worker_client'):
            for query in ('SELECT * FROM rc_control.jobs;',f"SELECT rc_control.claim('{W1}');"):
                with self.subTest(role=role),self.assertRaisesRegex(DatabaseError,'PERMISSION_DENIED'):
                    sql(query,role)

    def test_broker_has_no_dml_gate_or_internal_helper_access(self):
        for query in ('SELECT * FROM rc_control.jobs;',
            'UPDATE rc_control.settings SET enabled=true;',
            'DELETE FROM rc_control.workers;',
            f"SELECT rc_control.lock_lease('{W1}','{W1}','{W1}',1);"):
            with self.subTest(query=query),self.assertRaisesRegex(DatabaseError,'PERMISSION_DENIED'): sql(query)

    def test_rls_defends_accidental_select_grant(self):
        self.enq()
        sql('GRANT USAGE ON SCHEMA rc_control TO anon; GRANT SELECT ON rc_control.jobs TO anon;','postgres')
        try: self.assertEqual(sql('SELECT count(*) FROM rc_control.jobs;','anon'),'0')
        finally: sql('REVOKE ALL ON rc_control.jobs FROM anon; REVOKE USAGE ON SCHEMA rc_control FROM anon;','postgres')

    def test_definer_owner_is_not_superuser_or_login(self):
        self.assertEqual(sql("SELECT rolcanlogin OR rolsuper OR rolbypassrls OR rolcreaterole "
            "FROM pg_roles WHERE rolname='rc_control_owner';",'postgres'),'f')
        self.assertEqual(sql("SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON p.pronamespace=n.oid "
            "WHERE n.nspname='rc_control' AND (NOT prosecdef OR "
            "NOT 'search_path=pg_catalog'=ANY(proconfig));",'postgres'),'0')

    def test_no_user_fields_or_unsupported_descriptor(self):
        for changes in ({'source':'some-source'},{'rounds':True},{'rounds':4},
                        {'policy_sha256':'b'*64},{'engine_ref':'arbitrary'},
                        {'program_sha256':123},{'owner_ref':OTHER}):
            with self.subTest(changes=changes),self.assertRaisesRegex(DatabaseError,'DESCRIPTOR_INVALID'):
                self.enq(descriptor={**self.descriptor,**changes})
        self.assertEqual(self.count(),0)

    def test_deadline_and_identifiers_rejected(self):
        with self.assertRaisesRegex(DatabaseError,'DEADLINE_INVALID'): self.enq(deadline='2000-01-01 00:00:00+00')
        far=sql("SELECT (clock_timestamp()+interval '1 hour')::text;",'postgres')
        with self.assertRaisesRegex(DatabaseError,'DEADLINE_INVALID'): self.enq(deadline=far)
        with self.assertRaisesRegex(DatabaseError,'INPUT_INVALID'): self.enq(scope='../host')
        self.assertEqual(self.count(),0)


class RecordingResult(unittest.TextTestResult):
    def startTest(self,test):
        self._started=time.monotonic(); super().startTest(test)
    def addSuccess(self,test):
        self.records.append({'test':str(test),'status':'PASS','seconds':round(time.monotonic()-self._started,4)})
        super().addSuccess(test)
    def addFailure(self,test,err):
        self.records.append({'test':str(test),'status':'FAIL'})
        super().addFailure(test,err)
    def addError(self,test,err):
        self.records.append({'test':str(test),'status':'ERROR'})
        super().addError(test,err)
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw); self.records=[]


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ControlTests)
    result=unittest.TextTestRunner(verbosity=2,resultclass=RecordingResult).run(suite)
    report={'schema_version':1,'scope':'POSTGRES_CONTROL_CI_NOT_CLOUD_OR_VM',
        'status':'PASS' if result.wasSuccessful() else 'FAIL','tests_run':result.testsRun,
        'source_commit':os.environ.get('RC_SOURCE_COMMIT'),
        'checkout_commit':os.environ.get('GITHUB_SHA'),'run_id':RUN,
        'postgres_version':getattr(ControlTests,'version',None),
        'postgres_image_id':getattr(ControlTests,'image_id',None),
        'migration_sha256':hashlib.sha256(MIGRATION.read_bytes()).hexdigest(),
        'tests':result.records,'cleanup':'REQUIRED_IN_WORKFLOW',
        'cloud_deployed':False,'worker_authenticated':False,'students_enabled':False}
    dest=ROOT/'.local/i3-postgres'; dest.mkdir(parents=True,exist_ok=True)
    (dest/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    sys.exit(0 if result.wasSuccessful() else 1)
