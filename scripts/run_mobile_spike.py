#!/usr/bin/env python3
"""Compile bounded Portuguese DSL and run a real owner-only battle in Docker.

Never accepts Java source, shell, image names, container IDs or filesystem paths
from browser requests. Uses the unchanged pinned reference-spike image and policy.
"""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('robodsl', ROOT / 'spikes/autoria-mobile/language.py')
LANG = importlib.util.module_from_spec(spec)
spec.loader.exec_module(LANG)
IMAGE = 'robocopa-ifma/mobile-spike:0.1'


def baseline():
    # Lazy import makes parser/replay tests independent of Docker availability.
    import run_tank_spike
    return run_tank_spike


def prepare_images(root: Path = ROOT) -> None:
    ref = baseline()
    if ref.docker(['info', '--format', '{{.OSType}}']) != 'linux':
        raise RuntimeError('Inicie o Docker Desktop com o mecanismo Linux.')
    print('Preparando imagens verificadas; o cache Docker será reutilizado.', flush=True)
    for tag, folder in [('robocopa-ifma/tank-spike:1.4.0', 'spikes/tank-royale'),
                        (IMAGE, 'spikes/autoria-mobile')]:
        subprocess.run(['docker', 'build', '-t', tag, str(root / folder)],
                       check=True, timeout=900)


def validate_result(data: dict, program_sha: str) -> None:
    if (data.get('completed') is not True or data.get('source') != 'BattleResults'
        or data.get('engine_version') != '1.4.0' or data.get('numberOfRounds') != 3
        or data.get('program_sha256') != program_sha
        or sorted(data.get('observedRoundEnds', [])) != [1, 2, 3]):
        raise ValueError('Resultado sem vínculo com o programa ou batalha incompleta.')
    rows = data.get('results', [])
    if len(rows) != 2 or {r.get('name') for r in rows} != {'Aprendiz', 'Walls'}:
        raise ValueError('Identidades inesperadas.')
    for row in rows:
        expected = program_sha[:12] if row['name'] == 'Aprendiz' else '1.0'
        if row.get('version') != expected:
            raise ValueError('A versão executada diverge da versão submetida.')
        if any(type(row.get(f)) is not int or row[f] < 0
               for f in ('rank', 'totalScore', 'firstPlaces', 'secondPlaces')):
            raise ValueError('Pontuação inválida.')
        if row['rank'] not in (1, 2):
            raise ValueError('Classificação inválida.')
    if data.get('observedTicks', 0) <= 0:
        raise ValueError('Sem evidência de turnos do motor.')


def replay_summary(path: Path, results: dict) -> dict:
    """Read real engine events, verify exported results, retain a bounded visual sample."""
    size, ticks, speed_sum, speed_count, moving = 0, 0, 0., 0, 0
    frames, rounds, finals, starts = [], [], [], 0
    with gzip.open(path, 'rb') as stream:
        for line in stream:
            size += len(line)
            if size > 128 * 1024**2 or len(line) > 2 * 1024**2:
                raise ValueError('Replay ultrapassa o limite de inspeção.')
            event = json.loads(line)
            kind = event.get('type')
            if kind == 'GameStartedEventForObserver':
                starts += 1
                setup = event['gameSetup']
                if setup.get('numberOfRounds') != 3:
                    raise ValueError('Número de rounds do replay incorreto.')
                identities = {(p['name'], p['version']) for p in event['participants']}
                if identities != {(r['name'], r['version']) for r in results['results']}:
                    raise ValueError('Identidade do replay diverge do resultado.')
            elif kind == 'RoundEndedEventForObserver':
                rounds.append(event['roundNumber'])
            elif kind == 'GameEndedEventForObserver':
                finals.append(event)
            elif kind == 'TickEventForObserver':
                ticks += 1
                bots = []
                for bot in event.get('botStates', []):
                    row = {f: bot[f] for f in ('id', 'name', 'x', 'y', 'direction', 'energy', 'speed')}
                    if row['name'] not in ('Aprendiz', 'Walls') or any(
                        not isinstance(row[f], (int, float)) or not math.isfinite(row[f])
                        for f in ('x', 'y', 'direction', 'energy', 'speed')):
                        raise ValueError('Estado do replay inválido.')
                    if bot['name'] == 'Aprendiz':
                        speed_count += 1
                        speed_sum += abs(bot['speed'])
                        moving += abs(bot['speed']) > .1
                    bots.append(row)
                if ticks % 8 == 0 and len(frames) < 1500:
                    frames.append({'round': event['roundNumber'], 'turn': event['turnNumber'], 'bots': bots})
    if starts != 1 or sorted(rounds) != [1, 2, 3] or len(finals) != 1 or speed_count == 0:
        raise ValueError('Replay incompleto.')
    final_rows = finals[0].get('results', [])
    for row in results['results']:
        matches = [r for r in final_rows if r.get('name') == row['name']]
        if len(matches) != 1 or any(matches[0].get(k) != v for k, v in row.items()):
            raise ValueError('Replay e BattleResults divergentes.')
    return {'source': 'official_replay', 'ticks': ticks, 'rounds': rounds,
            'mean_abs_speed': round(speed_sum / speed_count, 4),
            'moving_tick_fraction': round(moving / speed_count, 4),
            'frames': frames, 'sample_every_ticks': 8, 'sample_truncated': ticks > 12000,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def run_program(source: str, root: Path = ROOT) -> dict:
    compiled = LANG.compile_program(source)  # reject input before Docker or filesystem mutation
    ref = baseline()
    local, folder = root / '.local', root / '.local/mobile-spike'
    if local.is_symlink() or folder.is_symlink():
        raise ValueError('Diretório de evidências não pode ser link simbólico.')
    folder.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    out = folder / run_id
    out.mkdir()
    (out / 'programa.robo').write_text(source, encoding='utf-8')
    (out / 'ast.json').write_text(json.dumps(compiled['ast'], indent=2), encoding='utf-8')
    name, created = 'robocopa-mobile-' + uuid.uuid4().hex[:16], False
    status = {'schema_version': 1, 'status': 'FAILED', 'run_id': run_id,
              'environment': 'github-actions' if os.getenv('GITHUB_ACTIONS') == 'true' else 'operator-host',
              'program_sha256': compiled['program_sha256'], 'java_sha256': compiled['java_sha256'],
              'source_text_sha256': hashlib.sha256(source.encode()).hexdigest(),
              'scope': 'owner-only-bounded-dsl-experiment'}
    try:
        image_id = ref.docker(['image', 'inspect', '--format', '{{.Id}}', IMAGE])
        ref.docker(['create', '-i', '--name', name, '--label', 'org.robocopa.scope=mobile-spike',
            '--network', 'none', '--read-only', '--user', '10001:10001', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--cpus', '2', '--memory', '2g',
            '--pids-limit', '256', '--init', '--tmpfs', '/tmp:rw,nosuid,nodev,size=768m,mode=1777', image_id])
        created = True
        info = json.loads(ref.docker(['inspect', name]))[0]
        status['runtime_checks'] = ref.inspect_contract(info)
        status['image_id'] = info['Image']
        payload = compiled['program_sha256'].encode() + b'\n' + base64.b64encode(compiled['java'].encode()) + b'\n'
        stream = out / 'runtime.stream'
        with stream.open('wb') as output:
            task = subprocess.run(['docker', 'start', '-ai', name], input=payload, stdout=output,
                                  stderr=subprocess.STDOUT, timeout=240, check=False)
        if task.returncode or int(ref.docker(['inspect', '--format', '{{.State.ExitCode}}', name])):
            raise RuntimeError('Falha no contêiner. Consulte runtime.stream na pasta da execução.')
        ref.extract_stream(stream, out)
        results = json.loads((out / 'results.json').read_text(encoding='utf-8'))
        validate_result(results, compiled['program_sha256'])
        paths = list((out / 'recordings').glob('*.battle.gz'))
        if len(paths) != 1:
            raise ValueError('Um replay oficial é obrigatório.')
        replay = replay_summary(paths[0], results)
        status['replay'] = {k: v for k, v in replay.items() if k != 'frames'}
        (out / 'preview.json').write_text(json.dumps(replay), encoding='utf-8')
        status['status'] = 'PASS'
        return {'run_id': run_id, 'results': results, 'replay': replay}
    finally:
        try:
            if created:
                ref.docker(['rm', '-f', name])
            status['cleanup_completed'] = True
        except (OSError, RuntimeError, subprocess.SubprocessError):
            status.update(status='FAILED', cleanup_completed=False)
            raise
        finally:
            (out / 'manifest.json').write_text(json.dumps(status, indent=2), encoding='utf-8')
            print(status['status'] + ': .local/mobile-spike/' + run_id, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true', help='Construir somente as duas imagens de laboratório.')
    parser.add_argument('--example', choices=LANG.EXAMPLES, default='explorador')
    parser.add_argument('--file', type=Path, help='Arquivo .robo local (não recebido pela interface web).')
    args = parser.parse_args()
    if args.prepare:
        prepare_images()
        return
    source = args.file.read_text(encoding='utf-8') if args.file else LANG.EXAMPLES[args.example]
    result = run_program(source)
    print(json.dumps(result['results'], indent=2))
    print('Velocidade média absoluta:', result['replay']['mean_abs_speed'])

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
