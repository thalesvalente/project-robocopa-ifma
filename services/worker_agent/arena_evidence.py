"""Read-only evidence contracts for I2. Hashes are integrity, not referee trust.

No Docker, networking, process invocation or execution of replay content.
Both a fake manifest and a forged referee can lie; these checks do not constitute
cryptographic attestation of a worker or approval for student submissions.
"""
from __future__ import annotations
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re

ROLES = ('referee', 'walls', 'spin')
BOTS = {'Walls': '1.0', 'Spin Bot': '1.0'}
RESULT_FIELDS = frozenset(('id', 'name', 'isTeam', 'version', 'rank', 'survival',
    'lastSurvivorBonus', 'bulletDamage', 'bulletKillBonus', 'ramDamage', 'ramKillBonus',
    'totalScore', 'firstPlaces', 'secondPlaces', 'thirdPlaces'))
NUMERIC_FIELDS = RESULT_FIELDS - {'name', 'version', 'isTeam'}
POLICY_CHECKS = frozenset(('ownership', 'image_content_id', 'read_only', 'not_privileged',
    'non_root', 'no_host_mounts', 'no_ports', 'no_devices', 'capabilities', 'no_new_privileges',
    'seccomp_not_disabled', 'no_host_namespaces', 'memory', 'swap_disabled', 'cpu', 'pids',
    'init', 'no_persistent_logs', 'tmpfs_bounded', 'private_bridge', 'role',
    'separate_pid_ipc', 'no_metadata_secrets', 'attached_networks_exact'))
PROBE_CHECKS = frozenset(('gateway_tcp_reachable', 'raw_engine_denied', 'wrong_port_denied',
    'host_canary_denied', 'peer_canary_denied', 'testnet_denied', 'docker_dns_denied',
    'udp_dns_denied', 'ipv6_denied', 'referee_file_invisible', 'controller_file_invisible',
    'no_docker_socket', 'no_env_secret', 'controller_before_handshake',
    'observer_before_handshake', 'wrong_token', 'control_after_bot_handshake',
    'controller_after_bot_handshake', 'repeat_bot_handshake'))
SERVER_SHA256 = '16c277795bd823c9eda0b650f1d09a418ff35cfe43d59b820c52d5e6816f905c'
RUNNER_SHA256 = '02f6d1d8e9346a4aeae1b91e7abb278c98ac1f1d30c605f867758566f5f327cf'
FILE_LIMIT = 16 * 1024**2
REPLAY_LIMIT = 48 * 1024**2


class EvidenceError(ValueError):
    """Stable diagnostic only; never include a raw input or credential."""


def integer(value, minimum=0, maximum=2**31-1):
    return type(value) is int and minimum <= value <= maximum


def object_json(raw: bytes | str) -> dict:
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj: raise EvidenceError('DUPLICATE_FIELD')
            obj[key] = value
        return obj
    def finite(value):
        number = float(value)
        if not math.isfinite(number): raise EvidenceError('NON_FINITE')
        return number
    try:
        obj = json.loads(raw, object_pairs_hook=pairs, parse_float=finite,
            parse_constant=lambda _: (_ for _ in ()).throw(EvidenceError('NON_FINITE')))
    except (UnicodeError, ValueError, TypeError, RecursionError, OverflowError) as err:
        if isinstance(err, EvidenceError): raise
        raise EvidenceError('INVALID_JSON') from None
    if not isinstance(obj, dict): raise EvidenceError('OBJECT_REQUIRED')
    return obj


def require_checks(actual: dict, required: set | frozenset):
    if not required or not isinstance(actual, dict) or set(actual) != set(required):
        raise EvidenceError('CHECK_SET_INCOMPLETE')
    if any(value is not True for value in actual.values()):
        raise EvidenceError('CHECK_NOT_TRUE')


def read_file(path: Path, maximum: int) -> bytes:
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise EvidenceError('FILE_UNSAFE_OR_ABSENT')
    if path.stat().st_size > maximum: raise EvidenceError('FILE_LIMIT')
    with path.open('rb') as stream: data = stream.read(maximum + 1)
    if len(data) > maximum: raise EvidenceError('FILE_LIMIT')
    return data


def _rows(rows):
    if not isinstance(rows, list) or len(rows) != 2:
        raise EvidenceError('TWO_RESULTS_REQUIRED')
    ids, ranks, names = set(), set(), set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != RESULT_FIELDS:
            raise EvidenceError('RESULT_FIELD_SET')
        if row['isTeam'] is not False or type(row['name']) is not str or row['name'] not in BOTS or row['version'] != BOTS[row['name']]:
            raise EvidenceError('RESULT_IDENTITY')
        if not all(integer(row[k]) for k in NUMERIC_FIELDS):
            raise EvidenceError('RESULT_NUMERIC_FIELDS')
        if row['id'] < 1 or row['rank'] not in (1, 2):
            raise EvidenceError('RESULT_ID_RANK')
        if any(row[k] > 3 for k in ('firstPlaces', 'secondPlaces', 'thirdPlaces')):
            raise EvidenceError('RESULT_PLACES')
        ids.add(row['id']); ranks.add(row['rank']); names.add(row['name'])
    if len(ids) != 2 or ranks != {1, 2} or names != set(BOTS):
        raise EvidenceError('RESULT_DUPLICATE_IDENTITY')
    # Equal totalScore with ordered ranks is upstream data, not a RoboCopa tiebreaker.
    return {row['id']: (row['name'], row['version']) for row in rows}


def validate_replay(files: dict[str, bytes], secrets_list=(), *, max_uncompressed=REPLAY_LIMIT):
    try:
        result = object_json(files['results.json'])
        replay = files['recordings.battle.gz']
    except KeyError: raise EvidenceError('ARTIFACT_ABSENT') from None
    if len(files['results.json']) > 65536 or len(replay) > FILE_LIMIT:
        raise EvidenceError('FILE_LIMIT')
    if (result.get('schema_version') != 1 or type(result.get('schema_version')) is not int
        or result.get('source') != 'GameEndedEventForObserver'
        or result.get('engine_version') != '1.4.0' or result.get('completed') is not True
        or not integer(result.get('numberOfRounds'), 3, 3)
        or result.get('roundEnds') != [1, 2, 3] or any(type(x) is not int for x in result['roundEnds'])
        or not integer(result.get('ticks'), 1, 100000)
        or not integer(result.get('duration_ms'), 1, 240000)):
        raise EvidenceError('RESULT_ENVELOPE')
    identities = _rows(result.get('results'))
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(replay)) as source:
            raw = source.read(max_uncompressed + 1)
    except (OSError, EOFError, ValueError): raise EvidenceError('REPLAY_GZIP') from None
    if len(raw) > max_uncompressed: raise EvidenceError('REPLAY_LIMIT')
    if any(secret.encode() in raw for secret in secrets_list):
        raise EvidenceError('SECRET_IN_REPLAY')
    lines = raw.splitlines()
    if not 1 <= len(lines) <= 100020: raise EvidenceError('REPLAY_EVENT_COUNT')
    started, finished, current, last_turn, ticks = False, False, 0, 0, 0
    rounds = []
    for line in lines:
        if len(line) > 2 * 1024**2: raise EvidenceError('EVENT_LIMIT')
        item = object_json(line)
        kind = item.get('type')
        if finished: raise EvidenceError('EVENT_AFTER_FINISH')
        if kind == 'GameStartedEventForObserver':
            if started or current or rounds: raise EvidenceError('DUPLICATE_START')
            participants = item.get('participants')
            if (not isinstance(participants, list) or len(participants) != 2
                or not isinstance(item.get('gameSetup'),dict)
                or not integer(item['gameSetup'].get('numberOfRounds'),3,3)):
                raise EvidenceError('START_FIELDS')
            seen = {}
            for row in participants:
                if not isinstance(row, dict) or not integer(row.get('id'), 1):
                    raise EvidenceError('START_IDENTITY')
                seen[row['id']] = (row.get('name'), row.get('version'))
            if seen != identities: raise EvidenceError('START_IDENTITY')
            started = True
        elif kind == 'RoundStartedEvent':
            number = item.get('roundNumber')
            if not started or current or not integer(number, len(rounds) + 1, len(rounds) + 1) or number > 3:
                raise EvidenceError('ROUND_ORDER')
            current, last_turn = number, 0
        elif kind == 'TickEventForObserver':
            if (not started or not current or not integer(item.get('roundNumber'), current, current)
                or not integer(item.get('turnNumber'), last_turn + 1)):
                raise EvidenceError('TICK_ORDER')
            states = item.get('botStates')
            if not isinstance(states, list) or len(states) > 2: raise EvidenceError('TICK_STATES')
            seen = set()
            for row in states:
                if (not isinstance(row, dict) or not integer(row.get('id'), 1)
                    or row['id'] in seen or identities.get(row['id']) != (row.get('name'), row.get('version'))):
                    raise EvidenceError('TICK_IDENTITY')
                seen.add(row['id'])
            last_turn = item['turnNumber']; ticks += 1
        elif kind == 'RoundEndedEventForObserver':
            if not current or not integer(item.get('roundNumber'), current, current) or last_turn < 1:
                raise EvidenceError('ROUND_END_ORDER')
            if not integer(item.get('turnNumber'), last_turn): raise EvidenceError('ROUND_END_TURN')
            if _rows(item.get('results')) != identities: raise EvidenceError('ROUND_IDENTITY')
            rounds.append(current); current = 0
        elif kind == 'GameEndedEventForObserver':
            if current or rounds != [1, 2, 3] or not integer(item.get('numberOfRounds'), 3, 3):
                raise EvidenceError('FINAL_ORDER')
            if _rows(item.get('results')) != identities or item['results'] != result['results']: raise EvidenceError('RESULT_REPLAY_MISMATCH')
            finished = True
        else:
            raise EvidenceError('REPLAY_EVENT_DENIED')
    if not finished or ticks != result['ticks']: raise EvidenceError('REPLAY_INCOMPLETE')
    return {'ticks': ticks, 'round_ends': rounds,
            'sha256': hashlib.sha256(replay).hexdigest(), 'uncompressed_bytes': len(raw)}


def validate_battle(folder: Path):
    files = {name: read_file(folder/name, FILE_LIMIT) for name in
             ('results.json', 'recordings.battle.gz', 'referee-report.json', 'report.json')}
    metrics = validate_replay(files)
    report, referee = object_json(files['report.json']), object_json(files['referee-report.json'])
    if (report.get('schema_version') != 2 or report.get('status') != 'PASS'
        or report.get('host_vm_tested') is not False or report.get('student_submission_enabled') is not False
        or report.get('host_rules_unchanged_during_acl_setup') is not True
        or report.get('positive_host_peer_canaries') is not True):
        raise EvidenceError('BATTLE_SCOPE_OR_RESULT')
    if report.get('cleanup_completed') is not True: raise EvidenceError('CLEANUP_FAILED')
    for flag in ('remaining_owned_containers', 'remaining_owned_networks'):
        if report.get(flag) is not False: raise EvidenceError('RESOURCES_REMAIN')
    policy = report.get('policy', {})
    for role in ROLES: require_checks(policy.get(role), POLICY_CHECKS)
    namespaces = report.get('namespace_ids', {})
    host = report.get('host_namespace_ids', {})
    for kind in ('pid', 'net', 'mnt'):
        items = [namespaces.get(r, {}).get(kind) for r in ROLES] + [host.get(kind)]
        if any(not isinstance(n, str) or not re.fullmatch(kind + r':\[\d+\]', n) for n in items) or len(set(items)) != 4:
            raise EvidenceError('NAMESPACE_NOT_DISTINCT')
    for role in ROLES:
        fw = report.get('firewall', {}).get(role, {})
        if (fw.get('verified') is not True or fw.get('host_netns_distinct') is not True
            or fw.get('netns') != namespaces[role]['net']): raise EvidenceError('ACL_NOT_VERIFIED')
    for role in ('walls', 'spin'):
        probe = report.get('network_and_protocol_probes', {}).get(role, {})
        require_checks(probe.get('checks'), PROBE_CHECKS)
        if not integer(report.get('bot_output_acl_reject_packets', {}).get(role), 1):
            raise EvidenceError('ACL_REJECTION_NOT_OBSERVED')
    if report.get('referee') != referee: raise EvidenceError('REFEREE_REPORT_MISMATCH')
    require_checks(referee.get('upstream_role_secrets_reject_bot_secret'),
                   {'ControllerHandshake', 'ObserverHandshake'})
    if referee.get('gateway_control_did_not_change_engine') is not True:
        raise EvidenceError('CONTROL_NOT_CONTAINED')
    if type(referee.get('raw_engine_control_without_handshake_observed')) is not bool:
        raise EvidenceError('UPSTREAM_OBSERVATION_MISSING')
    for label in ('accepted_handshake', 'BotReady', 'BotIntent'):
        if not integer(referee.get('gateway', {}).get(label), 1): raise EvidenceError('NO_REAL_GATEWAY_TRAFFIC')
    build = referee.get('server_artifact', {})
    if build.get('server_jar_sha256') != SERVER_SHA256 or build.get('derived_from_runner_sha256') != RUNNER_SHA256:
        raise EvidenceError('UPSTREAM_DIGEST_MISMATCH')
    if referee.get('replay_sha256') != metrics['sha256'] or report.get('replay', {}).get('sha256') != metrics['sha256']:
        raise EvidenceError('REPLAY_DIGEST_MISMATCH')
    return {'status': 'PASS', 'ticks': metrics['ticks'], 'rounds': 3,
            'results': object_json(files['results.json'])['results'], 'replay_sha256': metrics['sha256']}


def validate_batch(root: Path):
    batch = object_json(read_file(root/'batch.json', 65536))
    if (batch.get('schema_version') != 2 or batch.get('status') != 'PASS'
        or batch.get('student_submission_enabled') is not False or batch.get('host_vm_tested') is not False
        or batch.get('image_cleanup_completed') is not True
        or batch.get('battles') != ['battle-1', 'battle-2']
        or batch.get('abort_checks') != ['abort-after_containers', 'abort-after_ready']):
        raise EvidenceError('BATCH_STATUS_OR_SCOPE')
    battles = [validate_battle(root/name) for name in batch['battles']]
    for name in batch['abort_checks']:
        report = object_json(read_file(root/name/'report.json', 1024**2))
        if (report.get('status') != 'EXPECTED_ABORT' or report.get('abort_injected') != name.removeprefix('abort-')
            or report.get('cleanup_completed') is not True
            or report.get('remaining_owned_containers') is not False
            or report.get('remaining_owned_networks') is not False):
            raise EvidenceError('ABORT_CLEANUP_NOT_PROVEN')
    return {'status': 'PASS', 'battles': battles, 'abort_checks_passed': 2,
            'meaning': 'I2 reference experiment only; not VM or student approval'}
