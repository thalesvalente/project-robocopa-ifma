"""Strict I2 reconciliation evidence gate; no Docker, network or code execution.

Historical schema-2 batches stay readable with arena_evidence.validate_batch.
They do not satisfy this gate without fresh, source-bound reconciliation proof.
Hashes detect inconsistent bytes, not a dishonest or compromised referee.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import re
from .arena_evidence import (EvidenceError, FILE_LIMIT, ROLES, integer, object_json,
                             read_file, validate_batch)

PROFILE = 'I2_RECONCILED_CI_V1'
BATTLES = ('battle-1', 'battle-2')
ABORTS = ('abort-after_containers', 'abort-after_ready')
TIMEOUT = 'timeout-cleanup'
SCENARIOS = (*BATTLES, *ABORTS, TIMEOUT)
BATTLE_FILES = ('results.json', 'recordings.battle.gz', 'referee-report.json', 'report.json')
FILES = ('batch.json', *(f'{name}/{file}' for name in BATTLES for file in BATTLE_FILES),
         *(f'{name}/report.json' for name in (*ABORTS, TIMEOUT)))
FIELDS = {'schema_version', 'profile', 'source_commit', 'checkout_commit',
          'workflow_run_id', 'workflow_run_attempt', 'images', 'files', 'scenario_run_ids'}


def matches(value, pattern):
    return type(value) is str and re.fullmatch(pattern, value) is not None


def require_images(images):
    if (type(images) is not dict or set(images) != set(ROLES)
        or any(not matches(value, r'sha256:[0-9a-f]{64}') for value in images.values())
        or len(set(images.values())) != len(ROLES)):
        raise EvidenceError('RECONCILIATION_IMAGES')


def _hashes(root):
    return {name: hashlib.sha256(read_file(root/name, FILE_LIMIT)).hexdigest() for name in FILES}


def write_manifest(root: Path, *, source_commit: str, checkout_commit: str,
                   workflow_run_id: int, workflow_run_attempt: int):
    """Called only by the owned CI supervisor after all five scenarios/cleanup."""
    import json
    batch = object_json(read_file(root/'batch.json', 65536))
    document = {'schema_version': 1, 'profile': PROFILE, 'source_commit': source_commit,
        'checkout_commit': checkout_commit, 'workflow_run_id': workflow_run_id,
        'workflow_run_attempt': workflow_run_attempt, 'images': batch.get('images'),
        'files': _hashes(root), 'scenario_run_ids': {
            name: object_json(read_file(root/name/'report.json', FILE_LIMIT)).get('run_id')
            for name in SCENARIOS}}
    destination = root/'reconciliation.json'
    if destination.exists() or destination.is_symlink():
        raise EvidenceError('RECONCILIATION_ALREADY_EXISTS')
    # Parent paths were verified by read_file; create without overwriting anything.
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(document, stream, indent=2); stream.write('\n')
    return validate_reconciled_batch(root, expected_source_commit=source_commit,
                                    expected_workflow_run_id=workflow_run_id)


def validate_reconciled_batch(root: Path, *, expected_source_commit: str | None = None,
                              expected_workflow_run_id: int | None = None):
    manifest = object_json(read_file(root/'reconciliation.json', 65536))
    if (set(manifest) != FIELDS or not integer(manifest.get('schema_version'), 1, 1)
        or manifest.get('profile') != PROFILE
        or not matches(manifest.get('source_commit'), r'[0-9a-f]{40}')
        or not matches(manifest.get('checkout_commit'), r'[0-9a-f]{40}')
        or not integer(manifest.get('workflow_run_id'), 1, 2**63-1)
        or not integer(manifest.get('workflow_run_attempt'), 1, 100000)):
        raise EvidenceError('RECONCILIATION_PROVENANCE')
    if expected_source_commit is not None and (not matches(expected_source_commit, r'[0-9a-f]{40}')
            or manifest['source_commit'] != expected_source_commit):
        raise EvidenceError('RECONCILIATION_SOURCE_MISMATCH')
    if expected_workflow_run_id is not None and (not integer(expected_workflow_run_id, 1, 2**63-1)
            or manifest['workflow_run_id'] != expected_workflow_run_id):
        raise EvidenceError('RECONCILIATION_RUN_MISMATCH')
    require_images(manifest['images'])
    if (type(manifest['files']) is not dict or set(manifest['files']) != set(FILES)
        or any(not matches(value, r'[0-9a-f]{64}') for value in manifest['files'].values())
        or manifest['files'] != _hashes(root)):
        raise EvidenceError('RECONCILIATION_FILE_DIGEST')
    ids = manifest['scenario_run_ids']
    if (type(ids) is not dict or set(ids) != set(SCENARIOS)
        or any(not matches(value, r'[0-9a-f]{24}') for value in ids.values())
        or len(set(ids.values())) != len(SCENARIOS)):
        raise EvidenceError('RECONCILIATION_RUN_IDS')
    batch = object_json(read_file(root/'batch.json', 65536))
    if (not integer(batch.get('schema_version'), 2, 2)
        or batch.get('project_commit') != manifest['checkout_commit']
        or batch.get('images') != manifest['images'] or batch.get('timeout_check') != TIMEOUT):
        raise EvidenceError('RECONCILIATION_BATCH_BINDING')
    historical = validate_batch(root)
    for name in SCENARIOS:
        report = object_json(read_file(root/name/'report.json', FILE_LIMIT))
        if (not integer(report.get('schema_version'), 2, 2) or report.get('run_id') != ids[name]
            or report.get('images') != manifest['images']
            or report.get('host_vm_tested') is not False
            or report.get('student_submission_enabled') is not False
            or report.get('cleanup_completed') is not True
            or report.get('remaining_owned_containers') is not False
            or report.get('remaining_owned_networks') is not False):
            raise EvidenceError('RECONCILIATION_SCENARIO_SCOPE')
        if name in BATTLES:
            processes = report.get('bot_processes')
            if (report.get('bot_processes_verified') is not True
                or type(processes) is not dict or set(processes) != {'walls', 'spin'}):
                raise EvidenceError('RECONCILIATION_BOT_PROCESSES')
            for item in processes.values():
                if (type(item) is not dict or type(item.get('completed_before_cleanup')) is not bool
                    or not integer(item.get('output_bytes'), 0, 24*1024**2)
                    or not matches(item.get('output_sha256'), r'[0-9a-f]{64}')
                    or not integer(item.get('returncode'), -255, 255)):
                    raise EvidenceError('RECONCILIATION_BOT_PROCESSES')
                expected = 'completed' if item['completed_before_cleanup'] else 'owned_cleanup'
                if item.get('termination') != expected or (expected == 'completed' and item['returncode'] != 0):
                    raise EvidenceError('RECONCILIATION_BOT_PROCESSES')
        else:
            if any((root/name/file).exists() or (root/name/file).is_symlink() for file in BATTLE_FILES[:-1]):
                raise EvidenceError('RECONCILIATION_NON_BATTLE_HAS_RESULTS')
    timeout = object_json(read_file(root/TIMEOUT/'report.json', FILE_LIMIT))
    if (timeout.get('status') != 'EXPECTED_TIMEOUT' or timeout.get('scenario') != TIMEOUT
        or timeout.get('timeout_observed') is not True
        or timeout.get('deadline_fixture_started') is not True
        or timeout.get('battle_completed') is not False
        or type(timeout.get('deadline_seconds')) is not float or timeout['deadline_seconds'] != .5
        or not integer(timeout.get('fixture_sleep_seconds'), 5, 5)):
        raise EvidenceError('RECONCILIATION_TIMEOUT_NOT_PROVEN')
    return {'status': 'PASS', 'profile': PROFILE, 'source_commit': manifest['source_commit'],
        'checkout_commit': manifest['checkout_commit'], 'workflow_run_id': manifest['workflow_run_id'],
        'workflow_run_attempt': manifest['workflow_run_attempt'], 'battles': historical['battles'],
        'abort_checks_passed': 2, 'timeout_cleanup_passed': True, 'unique_scenarios': 5,
        'files_verified': len(FILES), 'expected_source_verified': expected_source_commit is not None,
        'expected_workflow_verified': expected_workflow_run_id is not None,
        'meaning': 'I2 experimental reconciliation only; no independent/production approval'}
