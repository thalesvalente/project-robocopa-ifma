"""I3-03B: trusted service admission -> existing RoboDSL validator -> PostgreSQL.

No HTTP listener, JWT verification, worker authentication or bot execution here.
ServiceActor must be constructed by the FUTURE authenticated caller, not JSON.
The database role is rc_admission, not rc_broker, service_role or a bot role.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import re
from typing import Any, Callable, Protocol
from uuid import UUID, uuid4

from services.worker_agent import contracts as c

SCOPE = re.compile(r'^[a-z][a-z0-9-]{0,31}$')
MAX_REQUEST_BYTES = 1024
STATES = frozenset({'QUEUED', 'LEASED', 'RUNNING', 'CANCELLED', 'EXPIRED', 'FAILED'})
DB_CODES = frozenset({'EXECUTION_DISABLED', 'VERSION_UNAUTHORIZED', 'VERSION_CHANGED',
    'VERSION_MISMATCH', 'POLICY_MISMATCH', 'DESCRIPTOR_INVALID', 'INPUT_INVALID',
    'IDEMPOTENCY_CONFLICT', 'QUEUE_FULL', 'DEADLINE_INVALID'})


class BridgeError(ValueError):
    """A stable error code; never expose source, SQL, DSN or driver messages."""


def _uuid(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        return str(UUID(value)) == value
    except ValueError:
        return False


@dataclass(frozen=True)
class ServiceActor:
    """Internal authorization context, NOT an authentication mechanism."""
    owner_id: str
    scope_id: str

    def __post_init__(self):
        if (not _uuid(self.owner_id) or type(self.scope_id) is not str
                or SCOPE.fullmatch(self.scope_id) is None):
            raise BridgeError('ACTOR_INVALID')


@dataclass(frozen=True)
class VersionSnapshot:
    source_sha256: str
    program_sha256: str
    java_sha256: str
    policy_sha256: str
    revision: int

    def __post_init__(self):
        hashes = (self.source_sha256, self.program_sha256, self.java_sha256, self.policy_sha256)
        if (any(type(x) is not str or c.SHA256.fullmatch(x) is None for x in hashes)
                or type(self.revision) is not int or not 1 <= self.revision < 2**63):
            raise BridgeError('DATABASE_RESPONSE_INVALID')


@dataclass(frozen=True)
class AdmissionReceipt:
    job_id: str
    state: str
    duplicate: bool

    def __post_init__(self):
        if (not _uuid(self.job_id) or type(self.state) is not str or self.state not in STATES
                or type(self.duplicate) is not bool):
            raise BridgeError('DATABASE_RESPONSE_INVALID')


class AdmissionRepository(Protocol):
    def snapshot(self, actor: ServiceActor, version_id: str) -> VersionSnapshot: ...
    def enqueue(self, actor: ServiceActor, key: str, descriptor: dict,
                revision: int) -> AdmissionReceipt: ...


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BridgeError('DUPLICATE_FIELD')
        result[key] = value
    return result


def _constant(_value):
    raise BridgeError('INVALID_JSON')


def _request(raw: bytes) -> dict:
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_REQUEST_BYTES:
        raise BridgeError('REQUEST_SIZE')
    try:
        data = json.loads(raw.decode('utf-8'), object_pairs_hook=_object,
                          parse_constant=_constant)
    except BridgeError:
        raise
    except (ValueError, UnicodeError, RecursionError):
        raise BridgeError('INVALID_JSON') from None
    if type(data) is not dict or set(data) != {'schema_version', 'version_id', 'idempotency_key', 'rounds'}:
        raise BridgeError('FIELDS_INVALID')
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise BridgeError('SCHEMA_INVALID')
    if type(data['rounds']) is not int or not 1 <= data['rounds'] <= 3:
        raise BridgeError('ROUNDS_INVALID')
    if any(type(data[k]) is not str or c.IDENTIFIER.fullmatch(data[k]) is None
           for k in ('version_id', 'idempotency_key')):
        raise BridgeError('IDENTIFIER_INVALID')
    return data


class AdmissionService:
    """No network/DB use unless explicitly enabled by a trusted service caller."""

    def __init__(self, repository: AdmissionRepository, *, enabled: bool = False):
        if type(enabled) is not bool:
            raise BridgeError('GATE_INVALID')
        self._repository, self._enabled = repository, enabled

    def submit(self, raw: bytes, source: str, *, actor: ServiceActor) -> AdmissionReceipt:
        if not self._enabled:
            raise BridgeError('EXECUTION_DISABLED')
        if type(actor) is not ServiceActor:
            raise BridgeError('ACTOR_INVALID')
        request = _request(raw)
        if type(source) is not str:
            raise BridgeError('SOURCE_INVALID')
        try:
            if len(source.encode('utf-8')) > c.DSL.MAX_BYTES:
                raise BridgeError('SOURCE_SIZE')
        except UnicodeError:
            raise BridgeError('SOURCE_INVALID') from None
        snapshot = self._repository.snapshot(actor, request['version_id'])
        if type(snapshot) is not VersionSnapshot:
            raise BridgeError('DATABASE_RESPONSE_INVALID')
        now = datetime.now(timezone.utc)
        # These UUIDs only satisfy the legacy pure validator. They NEVER reach SQL.
        envelope = dict(schema_version=1, job_id=str(uuid4()), attempt_id=str(uuid4()),
            version_id=request['version_id'], source_sha256=snapshot.source_sha256,
            program_sha256=snapshot.program_sha256, policy_sha256=snapshot.policy_sha256,
            engine_ref=c.ENGINE, language_id=c.LANGUAGE, trust_class='T1',
            operation='training', rounds=request['rounds'],
            idempotency_key=request['idempotency_key'],
            deadline_at=(now + timedelta(seconds=240)).isoformat())
        try:
            admitted = c.admit(json.dumps(envelope).encode('utf-8'), source,
                registry={request['version_id']: c.ApprovedVersion(
                    snapshot.source_sha256, snapshot.program_sha256)},
                allowed_policy_sha256=snapshot.policy_sha256, enabled=True, now=now)
        except c.AdmissionError as exc:
            raise BridgeError(str(exc)) from None
        if admitted.java_sha256 != snapshot.java_sha256:
            raise BridgeError('JAVA_MISMATCH')
        descriptor = dict(version_id=admitted.version_id,
            source_sha256=admitted.source_sha256, program_sha256=admitted.program_sha256,
            java_sha256=admitted.java_sha256, policy_sha256=admitted.policy_sha256,
            engine_ref=c.ENGINE, rounds=admitted.rounds)
        # The database rechecks revision, scope, hashes and policy atomically.
        return self._repository.enqueue(actor, admitted.idempotency_key,
                                        descriptor, snapshot.revision)


class PostgresAdmissionRepository:
    """A Psycopg-3-compatible factory supplies a FRESH non-autocommit connection.

    The factory is configured by the service, never from a request. A remote
    factory must use TLS verification and a least-privileged service login.
    Unit tests use explicit doubles; integration tests use Psycopg and SCRAM.
    """
    SNAPSHOT_SQL = 'SELECT rc_control.admission_snapshot(%s::uuid,%s::text,%s::text)'
    ENQUEUE_SQL = 'SELECT rc_control.enqueue_admitted(%s::uuid,%s::text,%s::text,%s::jsonb,%s::bigint)'

    def __init__(self, connect: Callable[[], Any]):
        if not callable(connect):
            raise BridgeError('CONNECTION_FACTORY_INVALID')
        self._connect = connect

    def _query(self, query: str, values: tuple, build: Callable[[dict], Any]):
        try:
            with self._connect() as conn:
                if conn.autocommit is not False:
                    raise BridgeError('CONNECTION_CONFIG_INVALID')
                # Pooler-compatible baseline; not proof of a Supabase deployment.
                conn.prepare_threshold = None
                conn.execute("SET LOCAL statement_timeout = '5s'")
                conn.execute("SET LOCAL lock_timeout = '2s'")
                conn.execute("SET LOCAL idle_in_transaction_session_timeout = '5s'")
                row = conn.execute(query, values, prepare=False).fetchone()
                if row is None or len(row) != 1 or type(row[0]) is not dict:
                    raise BridgeError('DATABASE_RESPONSE_INVALID')
                result = build(row[0])
            # Context manager COMMIT/close has succeeded before reporting success.
            return result
        except BridgeError:
            raise
        except Exception as exc:
            message = getattr(getattr(exc, 'diag', None), 'message_primary', None)
            code = message if type(message) is str and message in DB_CODES else 'STORAGE_UNAVAILABLE'
            raise BridgeError(code) from None

    def snapshot(self, actor: ServiceActor, version_id: str) -> VersionSnapshot:
        def build(row):
            if set(row) != {'source_sha256', 'program_sha256', 'java_sha256', 'policy_sha256', 'revision'}:
                raise BridgeError('DATABASE_RESPONSE_INVALID')
            return VersionSnapshot(**row)
        return self._query(self.SNAPSHOT_SQL, (actor.owner_id, actor.scope_id, version_id), build)

    def enqueue(self, actor: ServiceActor, key: str, descriptor: dict,
                revision: int) -> AdmissionReceipt:
        def build(row):
            if set(row) != {'job_id', 'state', 'duplicate'}:
                raise BridgeError('DATABASE_RESPONSE_INVALID')
            return AdmissionReceipt(**row)
        encoded = json.dumps(descriptor, sort_keys=True, separators=(',', ':'))
        return self._query(self.ENQUEUE_SQL,
                           (actor.owner_id, actor.scope_id, key, encoded, revision), build)
