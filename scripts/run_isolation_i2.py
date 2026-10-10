#!/usr/bin/env python3
"""Run a real Tank Royale 1.4.0 battle with bots/referee in disjoint CI networks.

Only disposable github-hosted Linux runner, not WSL or user's Docker Desktop.
No student programs, no external ports, no host mounts, no Docker socket in jobs.
Gateway blocks controller/admin message types from the bot network.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.worker_agent.bounded import capture
from services.worker_agent.policy import require_disposable_ci, PolicyError

PREFIX = 'rc-i2-'
LABEL = 'org.robocopa.i2-run'
SCOPE = 'trusted_official_bots_separated_ci_only'
TARGETS = ('referee', 'bot', 'gateway', 'controller')
MAX_BYTES = 16 * 1024 * 1024
NAMES = {'referee', 'gateway', 'controller', 'Walls', 'SpinBot', 'probe'}


def docker(args: list[str], *, timeout=30, budget=128 * 1024, check=True) -> bytes:
    result = capture(['docker', *args], timeout=timeout, max_bytes=budget)
    if check and result.returncode:
        raise RuntimeError('DOCKER_' + args[0].upper() + '_FAILED')
    return result.output


def docker_json(args):
    return json.loads(docker(args))


def owned_container(name: str, run: str) -> dict:
    info = docker_json(['inspect', name])[0]
    if info.get('Config', {}).get('Labels', {}).get(LABEL) != run:
        raise RuntimeError('CONTAINER_OWNERSHIP_INVALID')
    return info


def owned_network(name: str, run: str) -> dict:
    info = docker_json(['network', 'inspect', name])[0]
    if info.get('Labels', {}).get(LABEL) != run or info.get('Internal') is not True:
        raise RuntimeError('NETWORK_OWNERSHIP_INVALID')
    return info


def enforce_networks(infos: dict, game_net: str, trusted_net: str, run_id: str) -> dict:
    expected = {
        'referee': {trusted_net},
        'gateway': {game_net, trusted_net},
        'controller': {trusted_net},
        'Walls': {game_net}, 'SpinBot': {game_net}, 'probe': {game_net}
    }
    check = {}
    for name, wanted in expected.items():
        info = infos[name]
        host = info['HostConfig']
        nets = set(info['NetworkSettings']['Networks'])
        cfg = info['Config']
        check[name] = {
            'strict_network_membership': nets == wanted,
            'label_owner': cfg.get('Labels', {}).get(LABEL) == run_id,
            'no_ports': not host.get('PortBindings') and not host.get('PublishAllPorts'),
            'no_host_mounts': not host.get('Binds') and not host.get('Mounts'),
            'not_privileged': host.get('Privileged') is False,
            'readonly_root': host.get('ReadonlyRootfs') is True,
            'no_docker_socket': not any('/var/run/docker.sock' in str(x) for x in
                                        (info.get('Mounts') or [])),
            'no_host_network': host.get('NetworkMode') != 'host',
            'capabilities_dropped': 'ALL' in (host.get('CapDrop') or []),
            'no_new_privileges': 'no-new-privileges' in (host.get('SecurityOpt') or []),
            'memory_limited': 0 < (host.get('Memory') or 0) <= 1024**3,
            'cpu_limited': 0 < (host.get('NanoCpus') or 0) <= 1_000_000_000,
            'pids_limited': 0 < (host.get('PidsLimit') or 0) <= 128,
        }
        if not all(check[name].values()):
            raise RuntimeError('ROLE_OR_CONTAINER_POLICY_INVALID:' + name + ':' +
                               ','.join(k for k, v in check[name].items() if not v))
    return check


def decode_artifacts(output: bytes, directory: Path) -> tuple[dict, str]:
    if len(output) > MAX_BYTES:
        raise ValueError('CONTROLLER_OUTPUT_OVER_BUDGET')
    names = set()
    for line in output.splitlines():
        if not line.startswith(b'ROBOCOPA_I2_ARTIFACT '):
            continue
        parts = line.split(b' ', 2)
        if len(parts) != 3:
            raise ValueError('ARTIFACT_FRAME_INVALID')
        _, raw_name, raw_data = parts
        name = raw_name.decode('ascii')
        if name not in ('results.json', 'reference.battle.gz') or name in names:
            raise ValueError('ARTIFACT_NAME_INVALID')
        payload = base64.b64decode(raw_data, validate=True)
        if len(payload) > 12 * 1024 * 1024:
            raise ValueError('ARTIFACT_LENGTH_INVALID')
        (directory / name).write_bytes(payload)
        names.add(name)
    if names != {'results.json', 'reference.battle.gz'}:
        raise ValueError('OFFICIAL_ARTIFACTS_INCOMPLETE')
    data = json.loads((directory / 'results.json').read_text(encoding='utf-8'))
    if (data.get('source') != 'GameEndedEventForObserver'
            or data.get('engine_version') != '1.4.0'
            or data.get('completed') is not True
            or data.get('numberOfRounds') != 3
            or sorted(data.get('observedRoundEnds', [])) != [1, 2, 3]
            or {x.get('name') for x in data.get('results', [])} != {'Walls', 'Spin Bot'}
            or len(data['results']) != 2):
        raise ValueError('OFFICIAL_BATTLE_RESULT_INVALID')
    events, starts, ends, rounds, ticks = 0, 0, 0, [], 0
    final = None
    with gzip.open(directory / 'reference.battle.gz', 'rb') as stream:
        for line in stream:
            events += 1
            if events > 30000 or len(line) > 1024 * 1024:
                raise ValueError('REPLAY_BUDGET')
            event = json.loads(line)
            kind = event.get('type')
            if kind == 'GameStartedEventForObserver':
                starts += 1
                identities = {(x.get('name'), x.get('version')) for x in event.get('participants', [])}
                if identities != {('Walls', '1.0'), ('Spin Bot', '1.0')}:
                    raise ValueError('REPLAY_IDENTITIES_INVALID')
            elif kind == 'RoundEndedEventForObserver':
                rounds.append(event.get('roundNumber'))
            elif kind == 'TickEventForObserver':
                ticks += 1
            elif kind == 'GameEndedEventForObserver':
                ends += 1
                final = event
    if starts != 1 or ends != 1 or sorted(rounds) != [1, 2, 3] or ticks <= 0:
        raise ValueError('REPLAY_EVENT_INCOMPLETE')
    for row in data['results']:
        others = [x for x in final['results'] if x.get('name') == row['name']]
        if len(others) != 1 or any(row[k] != others[0].get(k) for k in
                                  ('name', 'version', 'rank', 'totalScore', 'firstPlaces')):
            raise ValueError('REPLAY_SCORE_DISAGREEMENT')
    return data, hashlib.sha256((directory / 'reference.battle.gz').read_bytes()).hexdigest()


def local_ci_guard() -> str:
    require_disposable_ci(dict(os.environ), platform.system(), platform.release())
    endpoint = docker(['context', 'inspect', '--format', '{{.Endpoints.docker.Host}}']).decode().strip()
    if endpoint != 'unix:///var/run/docker.sock':
        raise PolicyError('NOT_LOCAL_EPHEMERAL_DOCKER_CONTEXT')
    info = docker(['info', '--format', '{{.OSType}}|{{.OperatingSystem}}|{{.CgroupVersion}}']).decode().strip().split('|')
    if len(info) != 3 or info[0] != 'linux' or 'desktop' in info[1].lower() or info[2] != '2':
        raise PolicyError('LINUX_CGROUP_V2_NON_DESKTOP_REQUIRED')
    return info[1]


def main() -> int:
    platform_name = local_ci_guard()  # BEFORE creating paths, images, networks
    run = uuid.uuid4().hex[:24]
    directory = ROOT / '.local' / 'security-i2' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + run)
    if (ROOT / '.local').is_symlink() or directory.parent.is_symlink():
        raise RuntimeError('SYMLINK_EVIDENCE_ROOT')
    directory.mkdir(parents=True, exist_ok=False)
    network_bot = PREFIX + 'bot-' + run
    network_trusted = PREFIX + 'trusted-' + run
    nets = []
    containers: list[str] = []
    images: dict[str, str] = {}
    image_tags = {}
    label = LABEL + '=' + run
    # Random synthetic credentials generated here, never printed or written to report.
    from secrets import token_urlsafe
    bot_secret = token_urlsafe(32)
    controller_secret = token_urlsafe(32)
    if bot_secret == controller_secret:
        raise RuntimeError('SECRET_GENERATION_INVALID')
    status = {'schema_version': 1, 'status': 'FAILED', 'scope': SCOPE,
              'environment': 'github-hosted-linux', 'upstream_version': '1.4.0',
              'host_vm_tested': False, 'student_submission_enabled': False,
              'kernel': platform.release(), 'docker_operating_system': platform_name,
              'commit': os.getenv('GITHUB_SHA'), 'separate_role_secrets': True,
              'containers': {}, 'network_roles': {}, 'cleanup_verified': False}
    try:
        context = str(ROOT)
        dockerfile = str(ROOT / 'spikes/isolamento/i2/Dockerfile')
        for target in TARGETS:
            tag = PREFIX + target + ':' + run
            docker(['build', '-f', dockerfile, '--target', target, '-t', tag, context],
                   timeout=900, budget=4 * 1024 * 1024)
            image_tags[target] = tag
            images[target] = docker(['image', 'inspect', '--format', '{{.Id}}', tag]).decode().strip()
            if not re.fullmatch('sha256:[a-f0-9]{64}', images[target]):
                raise RuntimeError('IMAGE_ID_NOT_IMMUTABLE')
            print('I2_IMAGE_READY ' + target, flush=True)

        for name in (network_bot, network_trusted):
            docker(['network', 'create', '--driver', 'bridge', '--internal', '--label', label, name])
            nets.append(name)
            owned_network(name, run)

        def create(role: str, target: str, network: str, args: list[str],
                   env: list[str] | None = None, wd: str | None = None,
                   cpu: str = '1', memory: str = '768m', pids: str = '128',
                   alias: str | None = None) -> str:
            name = PREFIX + role.lower() + '-' + run
            command = ['create', '--name', name, '--label', label, '--network', network,
                       '--read-only', '--user', '10001:10001', '--cap-drop', 'ALL',
                       '--security-opt', 'no-new-privileges', '--cpus', cpu,
                       '--memory', memory, '--memory-swap', memory, '--pids-limit', pids,
                       '--tmpfs', '/tmp:rw,nosuid,nodev,size=128m,mode=1777',
                       '--log-driver', 'none']
            if alias is not None:
                command += ['--network-alias', alias]
            if wd is not None:
                command += ['--workdir', wd]
            for nameval in (env or []):
                command += ['--env', nameval]
            command += [images[target], *args]
            docker(command)
            containers.append(name)
            owned_container(name, run)
            return name

        referee = create('referee', 'referee', network_trusted, ['--port=7654',
            '--controller-secrets=' + controller_secret, '--bot-secrets=' + bot_secret,
            '--tps=-1'], memory='768m', alias='referee')
        gateway = create('gateway', 'gateway', network_bot, [],
                         env=['ARENA_URL=ws://referee:7654'], memory='256m',
                         pids='64', alias='gateway')
        docker(['network', 'connect', network_trusted, gateway])
        controller = create('controller', 'controller', network_trusted, [],
                            env=['ARENA_URL=ws://referee:7654',
                                 'CONTROLLER_SECRET=' + controller_secret],
                            memory='256m', pids='64')
        walls = create('Walls', 'bot', network_bot,
            ['-cp', '/opt/bots/classes:/opt/bots/lib/*', 'Walls'],
            env=['SERVER_URL=ws://gateway:7660', 'SERVER_SECRET=' + bot_secret],
            wd='/opt/bots/Walls', memory='512m', pids='64')
        spin = create('SpinBot', 'bot', network_bot,
            ['-cp', '/opt/bots/classes:/opt/bots/lib/*', 'SpinBot'],
            env=['SERVER_URL=ws://gateway:7660', 'SERVER_SECRET=' + bot_secret],
            wd='/opt/bots/SpinBot', memory='512m', pids='64')
        docker(['start', referee]); docker(['start', gateway])
        ip_text = owned_container(referee, run)['NetworkSettings']['Networks'][network_trusted]['IPAddress']
        import ipaddress
        try:
            if ipaddress.ip_address(ip_text).version != 4 or not ipaddress.ip_address(ip_text).is_private:
                raise ValueError('TRUSTED_REFEREE_ADDRESS_INVALID')
        except ValueError as exc:
            raise RuntimeError('TRUSTED_REFEREE_ADDRESS_INVALID') from exc
        probe = create('probe', 'controller', network_bot, ['/app/probe.py'],
            env=['GATEWAY_URL=ws://gateway:7660', 'BOT_SECRET=' + bot_secret,
                 'REFEREE_IP=' + ip_text], memory='256m', pids='32')

        statuses = {'referee': referee, 'gateway': gateway, 'controller': controller,
                    'Walls': walls, 'SpinBot': spin, 'probe': probe}
        infos = {role: owned_container(name, run) for role, name in statuses.items()}
        status['network_roles'] = enforce_networks(infos, network_bot, network_trusted, run)
        status['network_segments_internal'] = all(owned_network(n, run)['Internal'] is True for n in nets)
        status['images_by_role'] = {role: images[t] for role, t in
            (('referee','referee'),('bot','bot'),('gateway','gateway'),('controller','controller'))}

        import time
        time.sleep(2)  # bounded readiness margin before negative probe; never probes LAN
        # Fixed negative probe runs before official bots join, must be denied by gateway.
        result = docker(['start', '-a', probe], timeout=35, budget=32 * 1024, check=False)
        if 'I2_NEGATIVE_PASS' not in result.decode() or owned_container(probe, run)['State']['ExitCode'] != 0:
            raise RuntimeError('NEGATIVE_PROTOCOL_PROBES_FAILED')
        status['role_command_denial'] = True
        print('PASS I2 role commands denied before reaching referee', flush=True)

        docker(['start', walls]); docker(['start', spin])
        # The observer can handle slow bot startup via bounded lobby wait.
        done = docker(['start', '-a', controller], timeout=190, budget=MAX_BYTES, check=False)
        state = owned_container(controller, run)['State']
        if state['ExitCode'] != 0:
            # Retain only a bounded, known error code; never raw secrets/logs.
            match = re.search(rb'I2_FAILED (?:ProtocolError|TimeoutError|OSError) ([A-Z_]+)', done)
            status['controller_error_code'] = match.group(1).decode() if match else 'UNKNOWN'
            raise RuntimeError('CONTROLLER_BATTLE_FAILED')
        results, replay_sha = decode_artifacts(done, directory)
        for role in ('Walls', 'SpinBot'):
            info = owned_container(statuses[role], run)
            if info['State']['ExitCode'] not in (0, None) and not info['State']['Running']:
                raise RuntimeError('OFFICIAL_BOT_EXITED_EARLY')
        status['battle'] = results
        status['replay_sha256'] = replay_sha
        status['source'] = 'official_referee_observer_messages'
        status['role_boundaries_validated'] = True
        status['status'] = 'PASS'
        print('PASS I2 official separated 3 rounds', flush=True)
        print(json.dumps({'scores': [(x['name'], x['totalScore']) for x in results['results']],
                          'rounds': results['numberOfRounds']}, ensure_ascii=False), flush=True)
    except Exception as e:
        status['failure_type'] = type(e).__name__
        status['failure_stage'] = str(e).split(':')[0][:60]
        raise
    finally:
        issues = []
        for name in reversed(containers):
            try:
                owned_container(name, run)
                docker(['rm', '-f', name], timeout=15)
                if docker(['ps', '-aq', '--filter', 'name=^/' + name + '$']):
                    issues.append('CONTAINER_STILL_EXISTS')
            except Exception as e:
                issues.append('CONTAINER_CLEANUP:' + type(e).__name__)
        for name in reversed(nets):
            try:
                owned_network(name, run)
                docker(['network', 'rm', name], timeout=15)
            except Exception as e:
                issues.append('NETWORK_CLEANUP:' + type(e).__name__)
        for tag in image_tags.values():
            try:
                docker(['image', 'rm', tag], timeout=25, check=False)
            except Exception:
                issues.append('IMAGE_CLEANUP')
        status['cleanup_verified'] = not issues
        if issues:
            status['status'] = 'FAILED'
            status['cleanup_error_types'] = issues
        (directory / 'report.json').write_text(json.dumps(status, indent=2, ensure_ascii=False) + '\n')
        print(status['status'] + ': ' + str(directory.relative_to(ROOT)), flush=True)
        if issues:
            raise RuntimeError('OWNED_RESOURCES_CLEANUP_INCOMPLETE')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (PolicyError, OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print('BLOCKED/FAILED I2: ' + str(exc).split(':')[0][:100], file=sys.stderr)
        raise SystemExit(1)
