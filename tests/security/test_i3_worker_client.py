"""Pure response/config tests; no claimed HTTPS or database integration."""
from datetime import datetime,timezone,timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from services.worker_agent.control_client import Command,WorkerControlClient,WorkerClientError,read_worker_token,_NoRedirect

ID='00000000-0000-4000-8000-000000000001'
TOKEN='rcw_'+'a'*64
class ClientTests(unittest.TestCase):
    def setUp(self):
        self.client=WorkerControlClient('https://worker.example.invalid/worker-control',token=TOKEN,worker_id=ID,scope_id='lab-a')
        self.cmd=Command(ID,'claim')
        self.response=dict(schema_version=1,request_id=ID,operation='claim',worker_id=ID,scope_id='lab-a',result=None)
    def test_empty_queue_is_not_error(self):
        self.assertIsNone(self.client._validate(self.response,self.cmd)['result'])
    def test_wrong_scope_worker_correlation_and_schema_rejected(self):
        for key,val in [('scope_id','lab-b'),('worker_id','other'),('request_id','other'),('schema_version',True),('operation','fail')]:
            with self.subTest(key=key),self.assertRaisesRegex(WorkerClientError,'RESPONSE_INVALID'):
                self.client._validate({**self.response,key:val},self.cmd)
    def test_no_silent_authority_fields(self):
        for args in [{'worker_id':ID},{'scope_id':'lab-a'},{'role':'admin'}]:
            with self.assertRaisesRegex(WorkerClientError,'COMMAND_INVALID'):Command(ID,'claim',args).encode()
    def test_no_complete_enqueue_cancel_endpoints(self):
        for op in ['complete','enqueue','cancel','reap','list']:
            with self.assertRaisesRegex(WorkerClientError,'COMMAND_INVALID'):Command(ID,op).encode()
    def test_url_requires_https_and_no_redirect_tricks(self):
        for url in ['http://worker.example.invalid/worker-control','https://u:p@worker.example.invalid/worker-control','https://worker.example.invalid/worker-control?token=x','https://worker.example.invalid/worker-control#x','https://127.0.0.1/worker-control']:
            with self.assertRaisesRegex(WorkerClientError,'CONFIG_INVALID'):
                WorkerControlClient(url,token=TOKEN,worker_id=ID,scope_id='lab-a')
    def test_db_secrets_are_not_valid_worker_tokens(self):
        for token in ['sb_secret_abc','service_role','postgres://user:password@server/db']:
            with self.assertRaisesRegex(WorkerClientError,'CONFIG_INVALID'):
                WorkerControlClient('https://worker.example.invalid/worker-control',token=token,worker_id=ID,scope_id='lab-a')
    def test_request_serialization_stable_for_retry(self):
        self.assertEqual(self.cmd.encode(),self.cmd.encode());self.assertEqual(json.loads(self.cmd.encode())['request_id'],ID)
    def test_fence_string_preserves_bigint(self):
        args=dict(job_id=ID,attempt_id=ID,fence='9223372036854775807')
        self.assertEqual(json.loads(Command(ID,'start',args).encode())['fence'],args['fence'])
        for fence in [1,'0','01','9223372036854775808']:
            with self.assertRaisesRegex(WorkerClientError,'COMMAND_INVALID'):
                Command(ID,'start',{**args,'fence':fence}).encode()
    def test_secure_token_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'token';p.write_text(TOKEN);p.chmod(0o600)
            self.assertEqual(read_worker_token(p),TOKEN)
            p.chmod(0o644)
            with self.assertRaisesRegex(WorkerClientError,'TOKEN_FILE_INVALID'):read_worker_token(p)
            p.chmod(0o600);link=Path(tmp)/'link';link.symlink_to(p)
            with self.assertRaisesRegex(WorkerClientError,'TOKEN_FILE_INVALID'):read_worker_token(link)
    def test_expired_claim_rejected(self):
        result=dict(job_id=ID,attempt_id=ID,fence='1',lease_until=(datetime.now(timezone.utc)-timedelta(seconds=2)).isoformat(),deadline_at=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat(),descriptor={})
        with self.assertRaisesRegex(WorkerClientError,'RESPONSE_STALE'):self.client._validate({**self.response,'result':result},self.cmd)
    def test_network_failure_does_not_retry(self):
        with patch.object(self.client._opener,'open',side_effect=TimeoutError) as mocked:
            with self.assertRaisesRegex(WorkerClientError,'COMMAND_OUTCOME_UNKNOWN'):self.client.request(self.cmd)
            self.assertEqual(mocked.call_count,1)

    def test_redirect_is_not_followed(self):
        with self.assertRaisesRegex(WorkerClientError,'REDIRECT_DENIED'):
            _NoRedirect().redirect_request(None,None,302,'redirect',{},'https://attacker.invalid')
