#!/usr/bin/env python3
"""Build, run trusted bots offline in Docker, verify and retain evidence.

Does not touch compose.local.yaml, PostgreSQL, .env, firewall or other containers.
Never use this experiment to run student submissions.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
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
        'no_new_privileges': any(str(x).startswith('no-new-privileges') for x in host.get('SecurityOpt', [])),
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
        for field in ('rank','totalScore','survival','bulletDamage','ramDamage','firstPlaces','secondPlaces'):
            if type(row.get(field)) is not int or row[field] < 0:
                raise ValueError('Invalid score field: ' + field)
        if row['rank'] not in (1,2) or row['firstPlaces'] > 5 or row['secondPlaces'] > 5:
            raise ValueError('Invalid rank or places')
    if sum(r['totalScore'] for r in rows) <= 0 or data.get('observedTicks', 0) <= 0:
        raise ValueError('No positive score/tick evidence')
    if data.get('duration_ms', 0) <= 0:
        raise ValueError('Missing real duration')


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
    if docker(['info', '--format', '{{.OSType}}']) != 'linux':
        raise RuntimeError('A running Linux Docker engine is required')
    if not skip_build:
        subprocess.run(['docker', 'build', '-t', IMAGE, str(root / 'spikes/tank-royale')],
                       check=True, timeout=900)
    name = 'robocopa-tank-spike-' + uuid.uuid4().hex[:16]
    created = False
    status = {'schema_version': 1, 'status': 'FAILED', 'run_id': run_id,
              'environment': 'github-actions' if os.getenv('GITHUB_ACTIONS') == 'true' else 'operator-host',
              'evidence_scope': 'trusted_reference_bots_only'}
    try:
        docker(['create', '--name', name, '--label', 'org.robocopa.scope=reference-spike',
                '--network', 'none', '--read-only', '--user', '10001:10001', '--cap-drop', 'ALL',
                '--security-opt', 'no-new-privileges', '--cpus', '2', '--memory', '2g',
                '--pids-limit', '256', '--init', '--tmpfs', '/tmp:rw,nosuid,nodev,size=768m,mode=1777', IMAGE])
        created = True
        info = json.loads(docker(['inspect', name]))[0]
        status['runtime_checks'] = inspect_contract(info)
        status['image_id'] = info['Image']
        with (out / 'engine.log').open('wb') as log:
            process = subprocess.run(['docker', 'start', '-a', name], stdout=log,
                                     stderr=subprocess.STDOUT, timeout=TIMEOUT, check=False)
        exit_code = int(docker(['inspect', '--format', '{{.State.ExitCode}}', name]))
        docker(['cp', name + ':/tmp/evidence/.', str(out)])
        if process.returncode or exit_code:
            raise RuntimeError('Real battle container failed; inspect engine.log locally')
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
        status['status'] = 'PASS'
        print(json.dumps(results, ensure_ascii=False, indent=2))
        print('PASS: real battle, results, replay and runtime policy verified.')
        return out
    finally:
        (out / 'manifest.json').write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
        if created:
            docker(['rm', '-f', name])
        print('Evidence: .local/tank-royale/' + run_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-build', action='store_true', help='Reuse the already built spike image')
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
