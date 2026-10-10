"""Pure admission contract for the basic RoboDSL experiment.

No filesystem writes, network or Docker operations. The caller supplies an
already-authorized version registry; this is not authentication or a public API.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from typing import Mapping
from uuid import UUID

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    'robocopa_basic_dsl', ROOT / 'spikes/autoria-mobile/language.py')
DSL = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(DSL)
MAX_ENVELOPE_BYTES = 4096
ENGINE = 'tank-royale/1.4.0'
LANGUAGE = 'robodsl/0.1'
FIELDS = frozenset({
    'schema_version', 'job_id', 'attempt_id', 'version_id', 'program_sha256',
    'source_sha256', 'engine_ref', 'policy_sha256', 'language_id', 'trust_class',
    'operation', 'rounds', 'deadline_at', 'idempotency_key',
})
SHA256 = re.compile(r'^[0-9a-f]{64}$')
IDENTIFIER = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')


class AdmissionError(ValueError):
    """Stable, non-sensitive error code; never echoes participant input."""


@dataclass(frozen=True)
class ApprovedVersion:
    source_sha256: str
    program_sha256: str


@dataclass(frozen=True)
class AdmittedJob:
    job_id: str
    attempt_id: str
    version_id: str
    program_sha256: str
    source_sha256: str
    policy_sha256: str
    java_sha256: str
    rounds: int
    deadline_at: datetime
    idempotency_key: str


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise AdmissionError('DUPLICATE_FIELD')
        result[key] = value
    return result


def _reject_constant(_value: str):
    raise AdmissionError('NON_FINITE_JSON')


def _is_uuid(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return str(UUID(value)) == value
    except ValueError:
        return False


def admit(raw: bytes, source: str, *, registry: Mapping[str, ApprovedVersion],
          allowed_policy_sha256: str, enabled: bool = False,
          now: datetime | None = None) -> AdmittedJob:
    """Validate an internal request, failing closed unless explicitly enabled.

    'enabled' and 'registry' are trusted control-plane inputs, not JSON fields.
    No worker is launched even on success. Result is an immutable descriptor.
    """
    if enabled is not True:
        raise AdmissionError('EXECUTION_DISABLED')
    if not SHA256.fullmatch(allowed_policy_sha256):
        raise AdmissionError('POLICY_INVALID')
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= MAX_ENVELOPE_BYTES:
        raise AdmissionError('ENVELOPE_SIZE')
    try:
        data = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object,
                          parse_constant=_reject_constant)
    except AdmissionError:
        raise
    except (ValueError, UnicodeError, RecursionError):
        raise AdmissionError('INVALID_JSON') from None
    if not isinstance(data, dict) or set(data) != FIELDS:
        raise AdmissionError('FIELDS_INVALID')
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise AdmissionError('SCHEMA_INVALID')
    if data['language_id'] != LANGUAGE or data['trust_class'] != 'T1':
        raise AdmissionError('LANGUAGE_DENIED')
    if data['operation'] != 'training' or data['engine_ref'] != ENGINE:
        raise AdmissionError('OPERATION_DENIED')
    if not _is_uuid(data['job_id']) or not _is_uuid(data['attempt_id']):
        raise AdmissionError('IDENTITY_INVALID')
    for name in ('version_id', 'idempotency_key'):
        if not isinstance(data[name], str) or not IDENTIFIER.fullmatch(data[name]):
            raise AdmissionError('IDENTITY_INVALID')
    for name in ('program_sha256', 'source_sha256', 'policy_sha256'):
        if not isinstance(data[name], str) or not SHA256.fullmatch(data[name]):
            raise AdmissionError('HASH_INVALID')
    if data['policy_sha256'] != allowed_policy_sha256:
        raise AdmissionError('POLICY_MISMATCH')
    if type(data['rounds']) is not int or not 1 <= data['rounds'] <= 3:
        raise AdmissionError('ROUNDS_INVALID')
    current = now if now is not None else datetime.now(timezone.utc)
    if current.tzinfo is None or not isinstance(data['deadline_at'], str):
        raise AdmissionError('DEADLINE_INVALID')
    try:
        deadline = datetime.fromisoformat(data['deadline_at'].replace('Z', '+00:00'))
        if deadline.tzinfo is None or not 0 < (deadline - current).total_seconds() <= 240:
            raise ValueError
    except (ValueError, OverflowError):
        raise AdmissionError('DEADLINE_INVALID') from None
    approved = registry.get(data['version_id'])
    if not isinstance(approved, ApprovedVersion):
        raise AdmissionError('VERSION_UNAUTHORIZED')
    if (data['source_sha256'], data['program_sha256']) != (
            approved.source_sha256, approved.program_sha256):
        raise AdmissionError('VERSION_MISMATCH')
    if not isinstance(source, str):
        raise AdmissionError('SOURCE_INVALID')
    try:
        source_bytes = source.encode('utf-8')
        if len(source_bytes) > DSL.MAX_BYTES:
            raise AdmissionError('SOURCE_SIZE')
        if hashlib.sha256(source_bytes).hexdigest() != approved.source_sha256:
            raise AdmissionError('SOURCE_MISMATCH')
        compiled = DSL.compile_program(source)
    except AdmissionError:
        raise
    except (ValueError, UnicodeError, RecursionError):
        raise AdmissionError('DSL_INVALID') from None
    if compiled['program_sha256'] != approved.program_sha256:
        raise AdmissionError('PROGRAM_MISMATCH')
    return AdmittedJob(
        data['job_id'], data['attempt_id'], data['version_id'],
        approved.program_sha256, approved.source_sha256, allowed_policy_sha256,
        compiled['java_sha256'], data['rounds'], deadline, data['idempotency_key'])
