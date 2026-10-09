#!/usr/bin/env python3
"""Run only the pinned official bots in an offline, disposable Docker container.

Leaves Compose/PostgreSQL/.env untouched. This is NOT a student-code sandbox.
Evidence is transferred through stdout; no host directories are mounted.
"""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

IMAGE = 'robocopa-ifma/tank-spike:1.4.0'
TIMEOUT = 240


def docker(args: list[str], *, timeout: int = 30) -> str:
    result = subprocess.run(['docker', *args], capture_output=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError('Docker operation failed: ' + args[0])
    return result.stdout.decode('utf-8-sig').strip()


def inspect_contract(info: dict) -> dict:
    host = info.get('HostConfig', {})
    checks = {
        'network_none': host.get('NetworkMode') == 'none',
        'root_read_only': host.get('ReadonlyRootfs') is True,
        'not_privileged': host.get('Privileged') is False,
        'non_root': info.get('Config', {}).get('User') == '10001:10001',
        'no_host_mounts': not host.get('Binds') and not host.get('Mounts'),
        'no_host_ports': not host.get('PortBindings'),
        'capabilities_dropped': 'ALL' in host.get('CapDrop', []),
        'no_new_privileges': 'no-new-privileges' in host.get('SecurityOpt', []),
        'memory_limited': 0 < host.get('Memory', 0) <= 2 * 1024**3,
        'cpus_limited': 0 < host.get('NanoCpus', 0) <= 2_000_000_000,
        'pids_limited': 0 < (host.get('PidsLimit') or 0) <= 256,
    }
    if not all(checks.values()):
        raise ValueError('Container policy failed: ' + ', '.join(k for k,v in checks.items() if not v))
    return checks


def verify_results(data: dict) -> None:
    if (data.get('completed') is not True or data.get('source') != 'BattleResults'
            or data.get('engine_version') != '1.4.0' or data.get('numberOfRounds') != 5):
        raise ValueError('A completed five-round official battle is required')
    rows = data.get('results', [])
    if len(rows) != 2 or {r.get('name') for r in rows} != {'Walls', 'Spin Bot'}:
        raise ValueError('Unexpected reference bot identities')
    for row in rows:
        if row.get('version') != '1.0':
            raise ValueError('Unexpected reference bot version')
        for field in ('rank','totalScore','survival','bulletDamage','ramDamage','firstPlaces','secondPlaces'):
            if type(row.get(field)) is not int or row[field] < 0:
                raise ValueError('Invalid score field: ' + field)
        if row['rank'] not in (1,2) or row['firstPlaces'] > 5 or row['secondPlaces'] > 5:
            raise ValueError('Invalid rank or places')
    if sum(r['totalScore'] for r in rows) <= 0 or data.get('observedTicks', 0) <= 0:
        raise ValueError('No positive score/tick evidence')
    if data.get('duration_ms', 0) <= 0:
        raise ValueError('Missing real duration')


def extract_stream(stream: Path, out: Path) -> None:
    if stream.stat().st_size > 32 * 1024**2:
        raise ValueError('Runtime output exceeded evidence budget')
    names = set()
    with stream.open('rb') as source, (out / 'engine.log').open('xb') as log:
        for line in source:
            if not line.startswith(b'ROBOCOPA_ARTIFACT '):
                log.write(line)
                continue
            _, encoded_name, payload = line.rstrip(b'\r\n').split(b' ', 2)
            name = encoded_name.decode('ascii')
            if not (name == 'results.json' or re.fullmatch(r'recordings/[A-Za-z0-9_.-]+\.battle\.gz', name)):
                raise ValueError('Unsafe artifact path')
            if name in names:
                raise ValueError('Duplicate artifact')
            target = out / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as file:
                file.write(base64.b64decode(payload, validate=True))
            names.add(name)
    if 'results.json' not in names or len(names) != 2:
        raise ValueError('Missing result/replay output frames')
    stream.unlink()


def verify_replay(path: Path) -> dict:
    count = 0
    with gzip.open(path, 'rb') as replay:
        while block := replay.read(1024**2):
            count += len(block)
            if count > 128 * 1024**2:
                raise ValueError('Replay exceeded spike evidence budget')
    if count < 1000:
        raise ValueError('Replay is empty or implausibly small')
    return {'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'compressed_bytes': path.stat().st_size, 'uncompressed_bytes': count}


def run(root: Path, skip_build: bool = False) -> Path:
    local = root / '.local'
    folder = local / 'tank-royale'
    if local.is_symlink() or folder.is_symlink():
        raise ValueError('Refusing symlinked evidence directory')
    folder.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    out = folder / run_id
    out.mkdir()
    name = 'robocopa-tank-spike-' + uuid.uuid4().hex[:16]
    created = False
    status = {'schema_version': 1, 'status': 'FAILED', 'stage': 'preflight', 'run_id': run_id,
              'environment': 'github-actions' if os.getenv('GITHUB_ACTIONS') == 'true' else 'operator-host',
              'evidence_scope': 'trusted_reference_bots_only'}
    try:
        if docker(['info', '--format', '{{.OSType}}']) != 'linux':
            raise RuntimeError('A running Linux Docker engine is required')
        if not skip_build:
            status['stage'] = 'build'
            print('Building pinned reference image; details are saved in build.log.', flush=True)
            with (out / 'build.log').open('wb') as log:
                subprocess.run(['docker', 'build', '-t', IMAGE, str(root / 'spikes/tank-royale')],
                               stdout=log, stderr=subprocess.STDOUT, check=True, timeout=900)
        image_id = docker(['image', 'inspect', '--format', '{{.Id}}', IMAGE])
        status['stage'] = 'create'
        docker(['create', '--name', name, '--label', 'org.robocopa.scope=reference-spike',
                '--network', 'none', '--read-only', '--user', '10001:10001', '--cap-drop', 'ALL',
                '--security-opt', 'no-new-privileges', '--cpus', '2', '--memory', '2g',
                '--pids-limit', '256', '--init', '--tmpfs', '/tmp:rw,nosuid,nodev,size=768m,mode=1777', image_id])
        created = True
        info = json.loads(docker(['inspect', name]))[0]
        status['runtime_checks'] = inspect_contract(info)
        status['image_id'] = info['Image']
        status['stage'] = 'battle'
        print('Running Walls vs Spin Bot: five real rounds, no external network.', flush=True)
        stream = out / 'runtime.stream'
        with stream.open('wb') as log:
            process = subprocess.run(['docker', 'start', '-a', name], stdout=log,
                                     stderr=subprocess.STDOUT, timeout=TIMEOUT, check=False)
        exit_code = int(docker(['inspect', '--format', '{{.State.ExitCode}}', name]))
        if process.returncode or exit_code:
            raise RuntimeError('Battle container failed; inspect runtime.stream locally')
        status['stage'] = 'evidence'
        extract_stream(stream, out)
        results = json.loads((out / 'results.json').read_text())
        verify_results(results)
        replays = list((out / 'recordings').glob('*.battle.gz'))
        if len(replays) != 1:
            raise ValueError('Expected exactly one official replay')
        status['replay'] = verify_replay(replays[0])
        lock = json.loads((root / 'spikes/tank-royale/upstream.lock.json').read_text())
        status['engine_version'] = lock['engine_version']
        status['upstream_artifacts'] = {k: v['sha256'] for k,v in lock['artifacts'].items()}
        revision = subprocess.run(['git','rev-parse','HEAD'], cwd=root, capture_output=True, text=True, check=False)
        status['project_commit'] = revision.stdout.strip() if revision.returncode == 0 else 'unavailable'
        status['stage'] = 'completed'
        status['status'] = 'PASS'
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return out
    finally:
        try:
            if created:
                docker(['rm', '-f', name])
            status['cleanup_completed'] = True
        except (OSError, RuntimeError, subprocess.SubprocessError):
            status['status'] = 'FAILED'
            status['cleanup_completed'] = False
            print('FAIL: cleanup not confirmed for ' + name, file=sys.stderr)
            raise
        finally:
            (out / 'manifest.json').write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
            print(status['status'] + ': .local/tank-royale/' + run_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-build', action='store_true', help='Reuse the current spike image; not after code changes')
    args = parser.parse_args()
    if not shutil.which('docker'):
        print('BLOCKED: Docker CLI unavailable', file=sys.stderr)
        return 2
    try:
        run(Path(__file__).resolve().parents[1], args.skip_build)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print('FAIL: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
