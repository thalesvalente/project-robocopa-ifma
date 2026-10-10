"""Actual Python outbound HTTPS -> Deno -> private Postgres commands, CI only.

Synthetic credentials, DB/CA in temporary runner directories. No cloud deployment.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import secrets
import ssl
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from uuid import uuid4
from urllib.request import Request,build_opener,ProxyHandler,HTTPSHandler
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import psycopg
from services.worker_agent.control_client import Command,WorkerControlClient,WorkerClientError
from services.execution_control import admission_bridge as admission
from services.worker_agent import contracts
from test_control import sql,lit,command,NAME,RUN,OWNER,OTHER,W1,W2,DatabaseError
MIGRATIONS=[ROOT/'services/execution_control/postgres'/n for n in ('001_control.sql','002_admission.sql','003_worker_api.sql')]

def openssl(*args):
    r=command(['openssl',*args],timeout=30)
    if r.returncode:raise AssertionError('CERT_FIXTURE_FAILED')

class WorkerApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('RUNNER_ENVIRONMENT')=='github-hosted'
        assert sys.platform=='linux'
        obj=json.loads(command(['docker','inspect',NAME]).stdout)[0]
        assert obj['Config']['Labels'].get('org.robocopa.i3pg.run')==RUN
        assert obj['HostConfig']['NetworkMode']=='none' and not obj['HostConfig']['PortBindings']
        cls.temp=Path(os.environ['RC_ADMISSION_ROOT']);cls.socket=Path(os.environ['RC_PG_SOCKET'])
        assert cls.socket==cls.temp/'socket' and cls.temp.parent==Path(os.environ['RUNNER_TEMP'])
        assert {m['Destination'] for m in obj['Mounts']}=={'/var/lib/postgresql/data','/var/run/postgresql','/etc/rc-ci-hba.conf'}
        cls.pg=sql('SHOW server_version','postgres')
        for p in MIGRATIONS:sql(p.read_text(),'postgres',wrap=False)
        cls.password=secrets.token_hex(32);cls.admission_password=secrets.token_hex(32)
        for role,group,password in [('rc_worker_api_ci','rc_worker_api',cls.password),('rc_admission_ci','rc_admission',cls.admission_password)]:
            sql('CREATE ROLE '+role+' LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE PASSWORD '+lit(password)+'; GRANT '+group+' TO '+role+';','postgres')
        cls.ca=cls.temp/'ca.crt';cls.key=cls.temp/'server.key';cls.cert=cls.temp/'server.crt'
        openssl('req','-x509','-newkey','rsa:2048','-nodes','-sha256','-days','1','-keyout',str(cls.temp/'ca.key'),'-out',str(cls.ca),'-subj','/CN=RoboCopa-CI-Only','-addext','basicConstraints=critical,CA:TRUE','-addext','keyUsage=critical,keyCertSign,cRLSign')
        openssl('req','-newkey','rsa:2048','-nodes','-sha256','-keyout',str(cls.key),'-out',str(cls.temp/'server.csr'),'-subj','/CN=localhost')
        ext=cls.temp/'ext';ext.write_text('basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName=DNS:localhost,IP:127.0.0.1\n')
        openssl('x509','-req','-in',str(cls.temp/'server.csr'),'-CA',str(cls.ca),'-CAkey',str(cls.temp/'ca.key'),'-CAcreateserial','-days','1','-sha256','-extfile',str(ext),'-out',str(cls.cert))
        cls.key.chmod(0o600);(cls.temp/'ca.key').chmod(0o600)
        cls.source=contracts.DSL.EXAMPLES['explorador'];cls.compiled=contracts.DSL.compile_program(cls.source)
        cls.server=cls.start_server(True)

    @classmethod
    def start_server(cls,enabled):
        identifier=secrets.token_hex(4);portfile=cls.temp/('port-'+identifier+'.json');config=cls.temp/('config-'+identifier+'.json')
        config.write_text(json.dumps(dict(socket=str(cls.socket),password=cls.password,cert=str(cls.cert),key=str(cls.key),enabled=enabled,portFile=str(portfile))))
        config.chmod(0o600)
        log=(cls.temp/('server-'+identifier+'.log')).open('wb')
        proc=subprocess.Popen(['deno','run','--no-config','--lock='+str(ROOT/'supabase/functions/worker-control/deno.lock'),'--allow-net=127.0.0.1','--allow-env','--allow-read','--allow-write','--allow-sys',str(ROOT/'tests/worker_api/server.mjs'),str(config)],stdout=log,stderr=log,cwd=ROOT)
        cls.addClassCleanup(cls.stop_server,proc,log)
        for _ in range(100):
            if portfile.exists():return (proc,log,json.loads(portfile.read_text())['port'])
            if proc.poll() is not None:raise AssertionError('HTTPS_FIXTURE_START_FAILED')
            time.sleep(.1)
        raise AssertionError('HTTPS_FIXTURE_TIMEOUT')

    @staticmethod
    def stop_server(proc,log):
        if proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
        log.close()

    def setUp(self):
        sql('TRUNCATE rc_control.worker_receipts,rc_control.worker_request_clock,rc_control.worker_credentials,rc_control.attempts,rc_control.jobs,rc_control.workers,rc_control.approved_versions; '
            "UPDATE rc_control.settings SET enabled=true,capacity=32,lease_seconds=30,policy_sha256=repeat('a',64); "
            f"INSERT INTO rc_control.workers VALUES ('{W1}','lab-a',true),('{W2}','lab-b',true); "
            'INSERT INTO rc_control.approved_versions(owner_id,scope_id,version_id,source_sha256,program_sha256,java_sha256,active) VALUES ('+
            ','.join(lit(x) for x in (OWNER,'lab-a','demo-v1',hashlib.sha256(self.source.encode()).hexdigest(),self.compiled['program_sha256'],self.compiled['java_sha256']))+',true);','postgres')
        self.token=self.issue(W1,'lab-a');self.other_token=self.issue(W2,'lab-b')
        self.client=self.make_client(self.token)
        self.key='request-'+secrets.token_hex(5)
        def connect():return psycopg.connect(host=str(self.socket),dbname='robocopa_i3_ci',user='rc_admission_ci',password=self.admission_password,prepare_threshold=None)
        self.admission=admission.AdmissionService(admission.PostgresAdmissionRepository(connect),enabled=True)

    def issue(self,worker,scope):
        token='rcw_'+secrets.token_hex(32);digest=hashlib.sha256(token.encode()).hexdigest()
        sql('INSERT INTO rc_control.worker_credentials(credential_sha256,worker_id,scope_id,expires_at) VALUES ('+
            ','.join(lit(x) for x in (digest,worker,scope))+",clock_timestamp()+interval '5 minutes');",'postgres')
        return token
    def make_client(self,token,worker=W1,scope='lab-a',port=None,ca=True):
        return WorkerControlClient(f'https://127.0.0.1:{port or self.server[2]}/worker-control',token=token,worker_id=worker,scope_id=scope,cafile=self.ca if ca else None,allow_loopback=True)
    def submit(self,key=None):
        return self.admission.submit(json.dumps(dict(schema_version=1,version_id='demo-v1',idempotency_key=key or self.key,rounds=3)).encode(),self.source,actor=admission.ServiceActor(OWNER,'lab-a'))
    def call(self,operation='claim',args=None,request_id=None,client=None):
        return (client or self.client).request(Command(request_id or str(uuid4()),operation,args or {}))
    def pause(self):time.sleep(.12)
    def claim(self):return self.call()['result']
    def leaseargs(self,j):return {k:j[k] for k in ('job_id','attempt_id','fence')}
    def revoke(self,token):
        sql('UPDATE rc_control.worker_credentials SET revoked=true WHERE credential_sha256='+lit(hashlib.sha256(token.encode()).hexdigest()),'postgres')

    def test_real_i1_https_deno_postgres_claim_start_heartbeat_fail(self):
        queued=self.submit();j=self.claim();self.assertEqual(j['job_id'],queued.job_id)
        self.pause();self.assertEqual(self.call('start',self.leaseargs(j))['result']['state'],'RUNNING')
        self.pause();self.assertEqual(self.call('heartbeat',self.leaseargs(j))['result']['fence'],j['fence'])
        self.pause();self.assertEqual(self.call('fail',{**self.leaseargs(j),'reason':'WORKER_STOPPED'})['result']['state'],'QUEUED')
        self.assertEqual(sql('SELECT count(*) FROM rc_control.attempts','postgres'),'1')
    def test_empty_queue_authenticated(self):self.assertIsNone(self.claim())
    def test_unknown_credential_refused(self):
        with self.assertRaisesRegex(WorkerClientError,'^CREDENTIAL_DENIED$'):self.call(client=self.make_client('rcw_'+'0'*64))
    def test_revoked_credential_refused(self):
        self.revoke(self.token)
        with self.assertRaisesRegex(WorkerClientError,'^CREDENTIAL_DENIED$'):self.call()
    def test_expired_credential_refused_by_database_clock(self):
        sql("UPDATE rc_control.worker_credentials SET issued_at=clock_timestamp()-interval '20 seconds',expires_at=clock_timestamp()-interval '1 second'",'postgres')
        with self.assertRaisesRegex(WorkerClientError,'^CREDENTIAL_DENIED$'):self.call()
    def test_future_credential_refused(self):
        sql("UPDATE rc_control.worker_credentials SET issued_at=clock_timestamp()+interval '10 seconds',expires_at=clock_timestamp()+interval '2 minutes'",'postgres')
        with self.assertRaisesRegex(WorkerClientError,'^CREDENTIAL_DENIED$'):self.call()
    def test_maximum_credential_lifetime_enforced(self):
        with self.assertRaises(DatabaseError):sql("UPDATE rc_control.worker_credentials SET expires_at=issued_at+interval '901 seconds'",'postgres')
    def test_revoked_worker_refused(self):
        sql(f"UPDATE rc_control.workers SET active=false WHERE worker_id='{W1}'",'postgres')
        with self.assertRaisesRegex(WorkerClientError,'^CREDENTIAL_DENIED$'):self.call()
    def test_scope_change_invalidates_credential(self):
        sql(f"UPDATE rc_control.workers SET scope_id='lab-other' WHERE worker_id='{W1}'",'postgres')
        with self.assertRaisesRegex(WorkerClientError,'^CREDENTIAL_DENIED$'):self.call()
    def test_other_scope_gets_no_job(self):
        self.submit();self.assertIsNone(self.call(client=self.make_client(self.other_token,W2,'lab-b'))['result'])
        self.assertEqual(sql('SELECT state FROM rc_control.jobs','postgres'),'QUEUED')
    def test_cross_worker_cannot_start_or_heartbeat_known_job(self):
        self.submit();j=self.claim()
        for op in ('start','heartbeat'):
            with self.assertRaisesRegex(WorkerClientError,'^STALE_LEASE$'):self.call(op,self.leaseargs(j),client=self.make_client(self.other_token,W2,'lab-b'))
    def test_duplicate_claim_recovers_lost_response_without_second_lease(self):
        self.submit();rid=str(uuid4());first=self.call(request_id=rid);again=self.call(request_id=rid)
        self.assertEqual(first,again);self.assertEqual(sql('SELECT count(*) FROM rc_control.attempts','postgres'),'1')
    def test_concurrent_duplicate_claim_exactly_one_reservation(self):
        self.submit();rid=str(uuid4())
        with ThreadPoolExecutor(max_workers=6) as pool:out=list(pool.map(lambda _:self.call(request_id=rid),range(8)))
        self.assertTrue(all(x==out[0] for x in out));self.assertEqual(sql('SELECT count(*) FROM rc_control.attempts','postgres'),'1')
    def test_same_request_different_content_refused(self):
        self.submit();rid=str(uuid4());j=self.call(request_id=rid)['result']
        with self.assertRaisesRegex(WorkerClientError,'^REQUEST_CONFLICT$'):self.call('start',self.leaseargs(j),request_id=rid)
    def test_worker_one_active_lease_not_multiple(self):
        self.submit('first');self.submit('second');self.claim();self.pause()
        with self.assertRaisesRegex(WorkerClientError,'^WORKER_BUSY$'):self.claim()
        self.assertEqual(sql("SELECT count(*) FROM rc_control.jobs WHERE state='LEASED'",'postgres'),'1')
    def test_new_poll_rate_limited_but_duplicate_is_not(self):
        self.submit();rid=str(uuid4());self.call(request_id=rid)
        sql("UPDATE rc_control.worker_request_clock SET next_allowed_at=clock_timestamp()+interval '10 seconds'",'postgres')
        self.assertIsNotNone(self.call(request_id=rid)['result'])
        with self.assertRaisesRegex(WorkerClientError,'^RATE_LIMITED$'):self.call()
    def test_revoke_before_duplicate_denies_cached_receipt(self):
        self.submit();rid=str(uuid4());self.call(request_id=rid);self.revoke(self.token)
        with self.assertRaisesRegex(WorkerClientError,'^CREDENTIAL_DENIED$'):self.call(request_id=rid)
    def test_expired_lease_cannot_be_replayed(self):
        self.submit();rid=str(uuid4());self.call(request_id=rid)
        sql("UPDATE rc_control.jobs SET lease_until=clock_timestamp()-interval '1 second'",'postgres')
        with self.assertRaisesRegex(WorkerClientError,'^STALE_LEASE$'):self.call(request_id=rid)
    def test_old_fence_denied(self):
        self.submit();j=self.claim();self.pause()
        with self.assertRaisesRegex(WorkerClientError,'^STALE_LEASE$'):self.call('start',{**self.leaseargs(j),'fence':str(int(j['fence'])+1)})
    def test_cancelled_job_cannot_replay_claim(self):
        self.submit();rid=str(uuid4());j=self.call(request_id=rid)['result'];sql('SELECT rc_control.cancel('+lit(j['job_id'])+','+lit(OWNER)+');')
        with self.assertRaisesRegex(WorkerClientError,'^STALE_LEASE$'):self.call(request_id=rid)
    def test_rotation_overlap_and_persistent_revocation(self):
        newer=self.issue(W1,'lab-a');self.assertIsNone(self.call()['result']);self.pause();self.assertIsNone(self.call(client=self.make_client(newer))['result'])
        self.revoke(self.token)
        with self.assertRaisesRegex(WorkerClientError,'^CREDENTIAL_DENIED$'):self.call()
        self.pause();self.assertIsNone(self.call(client=self.make_client(newer))['result'])
    def test_gate_off(self):
        sql('UPDATE rc_control.settings SET enabled=false','postgres')
        with self.assertRaisesRegex(WorkerClientError,'^EXECUTION_DISABLED$'):self.call()
    def test_tls_unknown_ca_rejected(self):
        with self.assertRaisesRegex(WorkerClientError,'^COMMAND_OUTCOME_UNKNOWN$'):self.call(client=self.make_client(self.token,ca=False))
        self.assertEqual(sql('SELECT count(*) FROM rc_control.worker_receipts','postgres'),'0')
    def test_tls_wrong_hostname_real_handshake_denied(self):
        ctx=ssl.create_default_context(cafile=str(self.ca))
        with socket.create_connection(('127.0.0.1',self.server[2]),timeout=3) as raw:
            with self.assertRaises(ssl.SSLCertVerificationError):ctx.wrap_socket(raw,server_hostname='wrong.example.invalid')
        self.assertEqual(sql('SELECT count(*) FROM rc_control.worker_receipts','postgres'),'0')
    def test_unknown_request_after_commit_rollback_can_retry_same_id(self):
        self.submit();rid=str(uuid4());digest=hashlib.sha256(self.token.encode()).hexdigest()
        with psycopg.connect(host=str(self.socket),dbname='robocopa_i3_ci',user='rc_worker_api_ci',password=self.password) as conn:
            row=conn.execute("SELECT rc_control.worker_command(%s,%s,'claim','{}'::jsonb)",(digest,rid)).fetchone()[0]
            self.assertIsNotNone(row['result']);conn.rollback()
        self.assertEqual(sql('SELECT count(*) FROM rc_control.worker_receipts','postgres'),'0')
        self.assertEqual(sql("SELECT count(*) FROM rc_control.jobs WHERE state='LEASED'",'postgres'),'0')
        self.assertIsNotNone(self.call(request_id=rid)['result'])
    def test_raw_http_missing_auth_and_extra_fields_never_change_db(self):
        ctx=ssl.create_default_context(cafile=str(self.ca));opener=build_opener(ProxyHandler({}),HTTPSHandler(context=ctx))
        for auth,body in [('',dict(schema_version=1,request_id=str(uuid4()),operation='claim')),('Bearer '+self.token,dict(schema_version=1,request_id=str(uuid4()),operation='claim',worker_id=W2))]:
            req=Request(f'https://127.0.0.1:{self.server[2]}/worker-control',data=json.dumps(body).encode(),headers={'content-type':'application/json','authorization':auth},method='POST')
            with self.assertRaises(HTTPError) as out:opener.open(req,timeout=5)
            self.assertIn(out.exception.code,(400,401));out.exception.close()
        self.assertEqual(sql('SELECT count(*) FROM rc_control.worker_receipts','postgres'),'0')
    def test_api_db_login_cannot_read_tables_or_call_legacy_functions(self):
        with psycopg.connect(host=str(self.socket),dbname='robocopa_i3_ci',user='rc_worker_api_ci',password=self.password,autocommit=True) as c:
            self.assertEqual(c.execute('SELECT current_user').fetchone()[0],'rc_worker_api_ci')
            for query in ['SELECT * FROM rc_control.worker_credentials','SELECT * FROM rc_control.jobs',f"SELECT rc_control.claim('{W1}')",'SELECT rc_control.reap()']:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute(query)
    def test_reapplying_003_refuses_without_data_loss(self):
        self.submit();self.claim()
        with self.assertRaises(DatabaseError):sql(MIGRATIONS[2].read_text(),'postgres',wrap=False)
        self.assertEqual(sql('SELECT count(*) FROM rc_control.worker_receipts','postgres'),'1')
    def test_revocation_and_receipts_survive_database_restart(self):
        self.submit();rid=str(uuid4());j=self.call(request_id=rid);self.revoke(self.other_token)
        out=command(['docker','restart',NAME],timeout=30);self.assertEqual(out.returncode,0)
        for _ in range(50):
            if command(['docker','exec','--user','postgres',NAME,'pg_isready','-U','postgres','-d','robocopa_i3_ci']).returncode==0:break
            time.sleep(.1)
        self.assertEqual(sql('SELECT count(*) FROM rc_control.worker_receipts','postgres'),'1')
        with self.assertRaisesRegex(WorkerClientError,'^CREDENTIAL_DENIED$'):self.call(client=self.make_client(self.other_token,W2,'lab-b'))
        self.assertEqual(self.call(request_id=rid)['result']['job_id'],j['result']['job_id'])

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(WorkerApiTests))
    report=dict(schema_version=1,status='PASS' if result.wasSuccessful() and result.testsRun else 'FAIL',tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),source_commit=os.environ.get('RC_SOURCE_COMMIT'),workflow_run_id=RUN,postgres_version=getattr(WorkerApiTests,'pg',None),real_https=True,real_deno=True,real_postgres=True,cloud_deployed=False,worker_vm=False,student_data=False,cleanup='PENDING',migration_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in MIGRATIONS})
    p=ROOT/'.local/i3-worker-api/report.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if report['status']=='PASS' else 1)
