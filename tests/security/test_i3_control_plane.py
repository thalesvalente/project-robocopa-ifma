"""I3-01: synthetic offline queue; no Docker, external network or student data."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from services.worker_agent import contracts as c
from services.execution_control import (
    BrokerError, InternalBroker, LabGate, QueueError, SQLiteQueue,
)

class I3ControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="i3-fixture-")
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "queue.sqlite3"
        self.source = c.DSL.EXAMPLES["explorador"]
        compiled = c.DSL.compile_program(self.source)
        self.registry = {"demo-v1": c.ApprovedVersion(
            hashlib.sha256(self.source.encode("utf-8")).hexdigest(),
            compiled["program_sha256"],
        )}
        self.policy = "a" * 64
        self.now = datetime(2026, 10, 10, 12, tzinfo=timezone.utc)
        self.data = {
            "schema_version":1, "job_id":str(uuid4()), "attempt_id":str(uuid4()),
            "version_id":"demo-v1", "source_sha256":self.registry["demo-v1"].source_sha256,
            "program_sha256":self.registry["demo-v1"].program_sha256,
            "engine_ref":c.ENGINE, "policy_sha256":self.policy,
            "language_id":c.LANGUAGE, "trust_class":"T1",
            "operation":"training", "rounds":3, "idempotency_key":"synthetic-key",
            "deadline_at":(self.now + timedelta(seconds=180)).isoformat(),
        }
        self.queue = SQLiteQueue(self.path, capacity=8)

    def broker(self, gate=None, queue=None, policy=None):
        return InternalBroker(
            self.queue if queue is None else queue,
            registry=self.registry, policy_sha256=self.policy if policy is None else policy,
            gate=LabGate(True, True) if gate is None else gate,
        )

    def submit(self, *, broker=None, data=None, owner="fixture_a"):
        raw = json.dumps(self.data if data is None else data).encode()
        return (self.broker() if broker is None else broker).submit(
            raw, self.source, owner_ref=owner, now=self.now,
        )

    def new_job(self, key):
        return {**self.data, "job_id":str(uuid4()), "attempt_id":str(uuid4()),
                "idempotency_key":key}

    def test_disabled_by_default_does_not_enqueue(self):
        with self.assertRaisesRegex(BrokerError, "^EXECUTION_DISABLED$"):
            self.submit(broker=self.broker(gate=LabGate()))
        self.assertEqual(self.queue.count(), 0)

    def test_worker_unavailable_fails_closed(self):
        with self.assertRaisesRegex(BrokerError, "^WORKER_UNAVAILABLE$"):
            self.submit(broker=self.broker(gate=LabGate(True, False)))
        self.assertEqual(self.queue.count(), 0)

    def test_success_is_queued_only(self):
        r = self.submit()
        self.assertEqual((r.state, r.duplicate, r.job_id),
                         ("QUEUED", False, self.data["job_id"]))
        with self.assertRaises(FrozenInstanceError):
            r.state = "RUNNING"
        self.assertEqual(self.queue.count(), 1)

    def test_source_and_secrets_not_persisted(self):
        self.submit()
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT state FROM jobs").fetchone()[0], "QUEUED")
            cols = {x[1] for x in db.execute("PRAGMA table_info(jobs)")}
        self.assertFalse({"source", "password", "token", "docker_args",
                          "participant_name", "ip_address"} & cols)
        self.assertNotIn(self.source.encode("utf-8"), self.path.read_bytes())

    def test_identical_request_is_idempotent(self):
        r1, r2 = self.submit(), self.submit()
        self.assertFalse(r1.duplicate)
        self.assertTrue(r2.duplicate)
        self.assertEqual(r1.job_id, r2.job_id)
        self.assertEqual(self.queue.count(), 1)

    def test_key_with_new_job_rejected(self):
        self.submit()
        different = {**self.data, "job_id":str(uuid4()), "attempt_id":str(uuid4())}
        with self.assertRaisesRegex(BrokerError, "^IDEMPOTENCY_CONFLICT$"):
            self.submit(data=different)
        self.assertEqual(self.queue.count(), 1)

    def test_same_key_but_different_rounds_rejected(self):
        self.submit()
        with self.assertRaisesRegex(BrokerError, "^IDEMPOTENCY_CONFLICT$"):
            self.submit(data={**self.data, "rounds":2})

    def test_owners_have_separate_idempotency_scope(self):
        self.submit(owner="fixture_a")
        self.submit(owner="fixture_b", data=self.new_job(self.data["idempotency_key"]))
        self.assertEqual(self.queue.count(), 2)

    def test_reused_job_id_other_owner_rejected(self):
        self.submit()
        other = {**self.new_job("key-two"), "job_id":self.data["job_id"]}
        with self.assertRaisesRegex(BrokerError, "^IDENTITY_COLLISION$"):
            self.submit(data=other, owner="fixture_b")

    def test_reused_attempt_id_rejected(self):
        self.submit()
        other = {**self.new_job("key-two"), "attempt_id":self.data["attempt_id"]}
        with self.assertRaisesRegex(BrokerError, "^IDENTITY_COLLISION$"):
            self.submit(data=other)

    def test_bounded_queue_and_existing_duplicate(self):
        q = SQLiteQueue(self.path, capacity=1)
        b = self.broker(queue=q)
        self.submit(broker=b)
        with self.assertRaisesRegex(BrokerError, "^QUEUE_FULL$"):
            self.submit(broker=b, data=self.new_job("key-two"))
        self.assertTrue(self.submit(broker=b).duplicate)
        self.assertEqual(q.count(), 1)

    def test_process_reopen_preserves_queue(self):
        first = self.submit()
        reopened = SQLiteQueue(self.path, capacity=8)
        duplicate = self.submit(broker=self.broker(queue=reopened))
        self.assertTrue(duplicate.duplicate)
        self.assertEqual(first.job_id, duplicate.job_id)
        self.assertEqual(reopened.count(), 1)

    def test_concurrent_identical_submissions_only_once(self):
        b = self.broker()
        with ThreadPoolExecutor(max_workers=8) as pool:
            items = list(pool.map(lambda _:self.submit(broker=b), range(12)))
        self.assertEqual(sum(not x.duplicate for x in items), 1)
        self.assertEqual(len({x.job_id for x in items}), 1)
        self.assertEqual(self.queue.count(), 1)

    def test_concurrent_unique_requests_reject_overflow(self):
        q = SQLiteQueue(self.path, capacity=3)
        b = self.broker(queue=q)
        items = [self.new_job("key-" + str(i)) for i in range(9)]
        def invoke(item):
            try:
                self.submit(broker=b, data=item)
                return "OK"
            except BrokerError as exc:
                return str(exc)
        with ThreadPoolExecutor(max_workers=9) as pool:
            outcomes = list(pool.map(invoke, items))
        self.assertEqual(outcomes.count("OK"), 3)
        self.assertEqual(outcomes.count("QUEUE_FULL"), 6)
        self.assertEqual(q.count(), 3)

    def test_wrong_policy_rejected_before_enqueue(self):
        with self.assertRaisesRegex(BrokerError, "^POLICY_MISMATCH$"):
            self.submit(broker=self.broker(policy="b"*64))
        self.assertEqual(self.queue.count(), 0)

    def test_untrusted_T2_rejected(self):
        with self.assertRaisesRegex(BrokerError, "^LANGUAGE_DENIED$"):
            self.submit(data={**self.data, "trust_class":"T2"})
        self.assertEqual(self.queue.count(), 0)

    def test_docker_flags_denied(self):
        with self.assertRaisesRegex(BrokerError, "^FIELDS_INVALID$"):
            self.submit(data={**self.data, "docker_args":["--privileged"]})
        self.assertEqual(self.queue.count(), 0)

    def test_does_not_launch_process_or_network(self):
        with patch("subprocess.Popen", side_effect=AssertionError("process")), patch(
                "socket.create_connection", side_effect=AssertionError("network")):
            self.submit()
        self.assertEqual(self.queue.count(), 1)

    def test_bad_owner_rejected_and_sanitized(self):
        injected = "../student-private-value"
        with self.assertRaises(BrokerError) as ctx:
            self.submit(owner=injected)
        self.assertEqual(str(ctx.exception), "OWNER_INVALID")
        self.assertNotIn("student", str(ctx.exception))
        self.assertEqual(self.queue.count(), 0)

    def test_missing_directory_denied(self):
        with self.assertRaisesRegex(QueueError, "^STORE_CONFIG_INVALID$"):
            SQLiteQueue(Path(self.tmp.name) / "absent" / "queue.sqlite3")

    def test_boolean_capacity_denied(self):
        with self.assertRaisesRegex(QueueError, "^STORE_CONFIG_INVALID$"):
            SQLiteQueue(self.path, capacity=True)

    def test_symlink_db_file_denied(self):
        target = Path(self.tmp.name) / "raw"
        target.write_text("fixture")
        alias = Path(self.tmp.name) / "alias.sqlite3"
        alias.symlink_to(target)
        with self.assertRaisesRegex(QueueError, "^STORE_CONFIG_INVALID$"):
            SQLiteQueue(alias)

    def test_wrong_database_schema_denied(self):
        with sqlite3.connect(self.path) as db:
            db.execute("PRAGMA user_version=99")
        with self.assertRaisesRegex(QueueError, "^STORE_SCHEMA_UNSUPPORTED$"):
            SQLiteQueue(self.path)

    def test_duplicate_json_field_denied_without_write(self):
        bad = json.dumps(self.data).encode()[:-1] + b',"rounds":1}'
        with self.assertRaisesRegex(BrokerError, "^DUPLICATE_FIELD$"):
            self.broker().submit(bad, self.source, owner_ref="fixture_a", now=self.now)
        self.assertEqual(self.queue.count(), 0)
