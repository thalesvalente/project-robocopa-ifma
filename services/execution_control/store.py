"""I3-01: persistent SQLite queue for disposable, OFFLINE experiments only.

No worker claim, public HTTP, Docker, credentials or student data. Transactions
are on one local SQLite file, not a distributed production queue.
"""
from __future__ import annotations
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from services.worker_agent.contracts import AdmittedJob, ENGINE, SHA256

OWNER = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
SCHEMA = 2

class QueueError(ValueError):
    """Only stable codes, never client-controlled text."""

@dataclass(frozen=True)
class QueueReceipt:
    job_id: str
    state: str
    duplicate: bool

class SQLiteQueue:
    """Transactional, bounded lab enqueue; no consumer or score writer."""

    def __init__(self, path: Path, *, capacity: int = 8) -> None:
        if (not isinstance(path, Path) or not path.is_absolute()
                or path.is_symlink() or not path.parent.is_dir()
                or path.parent.is_symlink()
                or type(capacity) is not int or not 1 <= capacity <= 256):
            raise QueueError("STORE_CONFIG_INVALID")
        self.path, self.capacity = path, capacity
        try:
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                try:
                    version = db.execute("PRAGMA user_version").fetchone()[0]
                    if version not in (0, SCHEMA):
                        raise QueueError("STORE_SCHEMA_UNSUPPORTED")
                    db.execute("""
                        CREATE TABLE IF NOT EXISTS jobs (
                            job_id TEXT PRIMARY KEY,
                            attempt_id TEXT NOT NULL UNIQUE,
                            owner_ref TEXT NOT NULL,
                            idempotency_key TEXT NOT NULL,
                            fingerprint TEXT NOT NULL CHECK(length(fingerprint)=64),
                            version_id TEXT NOT NULL,
                            source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),
                            program_sha256 TEXT NOT NULL CHECK(length(program_sha256)=64),
                            java_sha256 TEXT NOT NULL CHECK(length(java_sha256)=64),
                            policy_sha256 TEXT NOT NULL CHECK(length(policy_sha256)=64),
                            engine_ref TEXT NOT NULL,
                            rounds INTEGER NOT NULL CHECK(rounds BETWEEN 1 AND 3),
                            deadline_utc TEXT NOT NULL,
                            created_utc TEXT NOT NULL,
                            state TEXT NOT NULL CHECK(state='QUEUED'),
                            UNIQUE(owner_ref, idempotency_key)
                        )
                    """)

                    db.execute("""
                        CREATE TABLE IF NOT EXISTS queue_config (
                            singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                            capacity INTEGER NOT NULL CHECK(capacity BETWEEN 1 AND 256)
                        )
                    """)
                    config = db.execute(
                        "SELECT capacity FROM queue_config WHERE singleton=1"
                    ).fetchone()
                    if config is None:
                        if version != 0:
                            raise QueueError("STORE_CONFIG_MISSING")
                        db.execute(
                            "INSERT INTO queue_config(singleton,capacity) VALUES (1,?)",
                            (self.capacity,),
                        )
                    elif config[0] != self.capacity:
                        raise QueueError("STORE_CONFIG_MISMATCH")
                    db.execute("PRAGMA user_version=2")
                    db.commit()
                except BaseException:
                    db.rollback()
                    raise
        except QueueError:
            raise
        except sqlite3.Error:
            raise QueueError("STORAGE_UNAVAILABLE") from None

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(str(self.path), timeout=5.0, isolation_level=None)
        try:
            db.execute("PRAGMA busy_timeout=5000")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("PRAGMA foreign_keys=ON")
            mode = db.execute("PRAGMA journal_mode=WAL").fetchone()[0]
            if mode.lower() != "wal":
                raise QueueError("STORAGE_UNAVAILABLE")
            return db
        except BaseException:
            db.close()
            raise

    @staticmethod
    def _fingerprint(job: AdmittedJob, owner_ref: str) -> str:
        fields = {
            "owner_ref": owner_ref, "job_id": job.job_id,
            "attempt_id": job.attempt_id, "version_id": job.version_id,
            "source_sha256": job.source_sha256,
            "program_sha256": job.program_sha256, "java_sha256": job.java_sha256,
            "policy_sha256": job.policy_sha256, "engine_ref": ENGINE,
            "rounds": job.rounds,
            "deadline_at": job.deadline_at.astimezone(timezone.utc).isoformat(),
            "idempotency_key": job.idempotency_key,
        }
        canonical = json.dumps(fields, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("ascii")).hexdigest()

    def enqueue(self, job: AdmittedJob, *, owner_ref: str,
                now: datetime | None = None) -> QueueReceipt:
        if type(job) is not AdmittedJob:
            raise QueueError("JOB_INVALID")
        if type(owner_ref) is not str or OWNER.fullmatch(owner_ref) is None:
            raise QueueError("OWNER_INVALID")
        current = now if now is not None else datetime.now(timezone.utc)
        if (not isinstance(current, datetime) or current.tzinfo is None
                or job.deadline_at.tzinfo is None or job.deadline_at <= current
                or any(not SHA256.fullmatch(v) for v in (
                    job.source_sha256, job.program_sha256,
                    job.java_sha256, job.policy_sha256,
                ))):
            raise QueueError("JOB_INVALID")
        fingerprint = self._fingerprint(job, owner_ref)
        try:
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                try:
                    previous = db.execute(
                        "SELECT job_id,fingerprint FROM jobs "
                        "WHERE owner_ref=? AND idempotency_key=?",
                        (owner_ref, job.idempotency_key),
                    ).fetchone()
                    if previous:
                        if previous[1] != fingerprint:
                            raise QueueError("IDEMPOTENCY_CONFLICT")
                        db.commit()
                        return QueueReceipt(previous[0], "QUEUED", True)
                    if db.execute(
                        "SELECT 1 FROM jobs WHERE job_id=? OR attempt_id=?",
                        (job.job_id, job.attempt_id),
                    ).fetchone():
                        raise QueueError("IDENTITY_COLLISION")
                    if db.execute(
                        "SELECT COUNT(*) FROM jobs WHERE state='QUEUED'"
                    ).fetchone()[0] >= self.capacity:
                        raise QueueError("QUEUE_FULL")
                    db.execute(
                        "INSERT INTO jobs (job_id,attempt_id,owner_ref,idempotency_key,"
                        "fingerprint,version_id,source_sha256,program_sha256,"
                        "java_sha256,policy_sha256,engine_ref,rounds,deadline_utc,"
                        "created_utc,state) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (job.job_id,job.attempt_id,owner_ref,job.idempotency_key,
                         fingerprint,job.version_id,job.source_sha256,
                         job.program_sha256,job.java_sha256,job.policy_sha256,
                         ENGINE,job.rounds,
                         job.deadline_at.astimezone(timezone.utc).isoformat(),
                         current.astimezone(timezone.utc).isoformat(),"QUEUED"),
                    )
                    db.commit()
                    return QueueReceipt(job.job_id, "QUEUED", False)
                except BaseException:
                    db.rollback()
                    raise
        except QueueError:
            raise
        except sqlite3.IntegrityError:
            raise QueueError("IDENTITY_COLLISION") from None
        except sqlite3.Error:
            raise QueueError("STORAGE_UNAVAILABLE") from None

    def count(self) -> int:
        """Offline diagnostic only; no worker claim or user listing."""
        try:
            with closing(self._connect()) as db:
                return db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        except sqlite3.Error:
            raise QueueError("STORAGE_UNAVAILABLE") from None
