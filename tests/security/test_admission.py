"""Admission tests use synthetic programs/IDs, no execution or student data."""
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from services.worker_agent import contracts as c


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.source = c.DSL.EXAMPLES['explorador']
        program = c.DSL.compile_program(self.source)
        self.policy = 'a' * 64
        self.now = datetime(2026, 10, 10, tzinfo=timezone.utc)
        self.approved = c.ApprovedVersion(hashlib.sha256(self.source.encode()).hexdigest(),
                                          program['program_sha256'])
        self.data = {'schema_version': 1,
            'job_id': '5fd435a1-a6a1-4f5a-923d-703537df5be2',
            'attempt_id': 'eacdd8d4-7a24-4070-91c8-d6bdc58c223b',
            'version_id': 'demo-v1', 'program_sha256': self.approved.program_sha256,
            'source_sha256': self.approved.source_sha256, 'engine_ref': c.ENGINE,
            'policy_sha256': self.policy, 'language_id': c.LANGUAGE, 'trust_class': 'T1',
            'operation': 'training', 'rounds': 3,
            'deadline_at': (self.now + timedelta(seconds=120)).isoformat(),
            'idempotency_key': 'synthetic-job-1'}

    def call(self, raw=None, source=None, **kwargs):
        options = dict(registry={'demo-v1': self.approved}, allowed_policy_sha256=self.policy,
                       enabled=True, now=self.now)
        options.update(kwargs)
        return c.admit(json.dumps(self.data).encode() if raw is None else raw,
                       self.source if source is None else source, **options)

    def reject(self, field, value):
        self.data[field] = value
        with self.assertRaises(c.AdmissionError): self.call()

    def test_valid_program_and_frozen_descriptor(self):
        out = self.call()
        self.assertEqual(out.program_sha256, self.approved.program_sha256)
        with self.assertRaises(FrozenInstanceError): out.rounds = 5

    def test_disabled_by_default(self):
        with self.assertRaisesRegex(c.AdmissionError, 'EXECUTION_DISABLED'):
            c.admit(json.dumps(self.data).encode(), self.source,
                    registry={'demo-v1':self.approved}, allowed_policy_sha256=self.policy)

    def test_no_process_is_created_by_admission(self):
        with patch('subprocess.Popen', side_effect=AssertionError('unexpected process')):
            self.call()

    def test_unknown_field_command_denied(self): self.reject('command', 'print(1)')
    def test_user_docker_flags_denied(self): self.reject('docker_args', ['--privileged'])
    def test_user_image_denied(self): self.reject('image', 'unapproved')
    def test_request_cannot_enable_worker(self): self.reject('enabled', True)
    def test_language_java_denied(self): self.reject('language_id', 'java/21')
    def test_trust_class_cannot_bypass(self): self.reject('trust_class', 'T0')
    def test_competition_not_implemented(self): self.reject('operation', 'competition')
    def test_engine_change_denied(self): self.reject('engine_ref', 'tank-royale/latest')
    def test_boolean_rounds_rejected(self): self.reject('rounds', True)
    def test_rounds_out_of_range(self): self.reject('rounds', 4)
    def test_boolean_schema_rejected(self): self.reject('schema_version', True)
    def test_invalid_uuid(self): self.reject('job_id', '../../elsewhere')
    def test_invalid_idempotency(self): self.reject('idempotency_key', 'x'*65)
    def test_bad_hash(self): self.reject('program_sha256', 'X'*64)
    def test_changed_policy(self): self.reject('policy_sha256', 'b'*64)
    def test_expired_deadline(self): self.reject('deadline_at', self.now.isoformat())
    def test_excessive_deadline(self):
        self.reject('deadline_at', (self.now + timedelta(seconds=241)).isoformat())
    def test_naive_deadline(self): self.reject('deadline_at', '2026-10-10T00:01:00')
    def test_unknown_version(self): self.reject('version_id', 'unknown')
    def test_version_cannot_self_authorize_hash(self): self.reject('source_sha256', 'c'*64)
    def test_source_changed_since_approval(self):
        with self.assertRaisesRegex(c.AdmissionError, 'SOURCE_MISMATCH'):
            self.call(source=self.source + '#changed')

    def test_registry_is_not_enough_to_allow_general_code(self):
        source='public class Arbitrary {}'
        self.data['source_sha256'] = hashlib.sha256(source.encode()).hexdigest()
        reg={'demo-v1':c.ApprovedVersion(self.data['source_sha256'], self.data['program_sha256'])}
        with self.assertRaisesRegex(c.AdmissionError, 'DSL_INVALID'):
            self.call(source=source, registry=reg)

    def test_duplicate_keys_denied(self):
        raw=json.dumps(self.data).encode()[:-1]+b',"rounds":3}'
        with self.assertRaisesRegex(c.AdmissionError, 'DUPLICATE_FIELD'): self.call(raw=raw)

    def test_non_finite_json_denied(self):
        raw=json.dumps(self.data).replace('"rounds": 3', '"rounds": NaN').encode()
        with self.assertRaisesRegex(c.AdmissionError, 'NON_FINITE_JSON'): self.call(raw=raw)

    def test_invalid_utf8(self):
        with self.assertRaisesRegex(c.AdmissionError, 'INVALID_JSON'): self.call(raw=b'\xff')

    def test_deep_json(self):
        with self.assertRaises(c.AdmissionError): self.call(raw=b'['*1500+b']'*1500)

    def test_oversized_envelope(self):
        with self.assertRaisesRegex(c.AdmissionError, 'ENVELOPE_SIZE'): self.call(raw=b'x'*4097)

    def test_error_does_not_echo_source(self):
        with self.assertRaises(c.AdmissionError) as ctx: self.call(source='private-user-secret')
        self.assertNotIn('private-user-secret', str(ctx.exception))

    def test_lone_surrogate_source(self):
        with self.assertRaises(c.AdmissionError): self.call(source='\ud800')
