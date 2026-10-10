"""Trusted standalone observer/controller for official Tank Royale 1.4.0.

Does not import or execute BooterManager. Only this process receives the
controller secret; bots connect exclusively through a role-filtered gateway.
The replay stores official observer events without adding simulated physics.
"""
from __future__ import annotations

import asyncio
import base64
from contextlib import AsyncExitStack
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

ARENA = 'ws://referee:7654'
EXPECTED = {('Walls', '1.0'), ('Spin Bot', '1.0')}
ROUNDS = 3
MAX_EVENT_BYTES = 1024 * 1024
MAX_RECORD_BYTES = 40 * 1024 * 1024
MAX_TICKS = 30000
RECORD_TYPES = {'GameStartedEventForObserver', 'RoundStartedEvent',
                'TickEventForObserver', 'RoundEndedEventForObserver',
                'GameEndedEventForObserver'}


class ProtocolError(ValueError):
    pass


def validate_bot_roster(value: object) -> list[dict]:
    if not isinstance(value, list) or len(value) != 2:
        raise ProtocolError('EXPECTED_TWO_BOTS')
    identities = set()
    addresses = set()
    out = []
    for bot in value:
        if not isinstance(bot, dict):
            raise ProtocolError('INVALID_BOT')
        identity = (bot.get('name'), bot.get('version'))
        if identity not in EXPECTED or identity in identities:
            raise ProtocolError('UNEXPECTED_OR_DUPLICATE_BOT')
        identities.add(identity)
        host, port = bot.get('host'), bot.get('port')
        if not isinstance(host, str) or len(host) > 128 or not host:
            raise ProtocolError('INVALID_BOT_HOST')
        if type(port) is not int or not 1 <= port <= 65535:
            raise ProtocolError('INVALID_BOT_PORT')
        if (host, port) in addresses:
            raise ProtocolError('REPEATED_BOT_ADDRESS')
        addresses.add((host, port))
        out.append({'host': host, 'port': port})
    if identities != EXPECTED:
        raise ProtocolError('INCOMPLETE_BOTS')
    return out


def setup_classic() -> dict:
    return {
        'gameType': 'classic', 'arenaWidth': 800, 'isArenaWidthLocked': False,
        'arenaHeight': 600, 'isArenaHeightLocked': False,
        'minNumberOfParticipants': 2, 'isMinNumberOfParticipantsLocked': False,
        'maxNumberOfParticipants': 2, 'isMaxNumberOfParticipantsLocked': False,
        'numberOfRounds': ROUNDS, 'isNumberOfRoundsLocked': False,
        'gunCoolingRate': 0.1, 'isGunCoolingRateLocked': False,
        'maxInactivityTurns': 450, 'isMaxInactivityTurnsLocked': False,
        'turnTimeout': 2_000_000, 'isTurnTimeoutLocked': False,
        'readyTimeout': 10_000_000, 'isReadyTimeoutLocked': False,
        'defaultTurnsPerSecond': -1
    }


def validate_final(event: dict, rounds: list[int], started: int, ticks: int) -> dict:
    if event.get('type') != 'GameEndedEventForObserver' or event.get('numberOfRounds') != ROUNDS:
        raise ProtocolError('OFFICIAL_GAME_END_REQUIRED')
    if sorted(rounds) != list(range(1, ROUNDS + 1)) or started != 1 or ticks <= 0:
        raise ProtocolError('ROUNDS_OR_TICKS_INCOMPLETE')
    rows = event.get('results')
    if not isinstance(rows, list) or len(rows) != 2:
        raise ProtocolError('RESULT_COUNT_INVALID')
    names = set()
    clean = []
    for row in rows:
        if not isinstance(row, dict) or (row.get('name'), row.get('version')) not in EXPECTED:
            raise ProtocolError('RESULT_IDENTITY_INVALID')
        if row['name'] in names:
            raise ProtocolError('RESULT_DUPLICATE_NAME')
        names.add(row['name'])
        score = row.get('totalScore')
        if (type(score) not in (int, float) or not math.isfinite(score) or score < 0
                or type(row.get('rank')) is not int or row['rank'] not in (1, 2)):
            raise ProtocolError('RESULT_SCORE_INVALID')
        clean.append({'name': row['name'], 'version': row['version'],
                      'rank': row['rank'], 'totalScore': score,
                      'firstPlaces': row.get('firstPlaces')})
    if names != {x[0] for x in EXPECTED} or sum(x['totalScore'] for x in clean) <= 0:
        raise ProtocolError('EMPTY_RESULTS')
    return {'schema_version': 1, 'engine_version': '1.4.0',
            'source': 'GameEndedEventForObserver', 'numberOfRounds': ROUNDS,
            'observedTicks': ticks, 'observedRoundEnds': rounds,
            'results': clean, 'completed': True}


async def role_handshake(ws, role: str, secret: str) -> None:
    data = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
    if (data.get('type') != 'ServerHandshake' or data.get('version') != '1.4.0'
            or not isinstance(data.get('sessionId'), str) or not data['sessionId']):
        raise ProtocolError('OFFICIAL_SERVER_HANDSHAKE_REQUIRED')
    await ws.send(json.dumps({'type': role + 'Handshake',
                             'sessionId': data['sessionId'],
                             'name': 'RoboCopa I2 experiment', 'version': '0.1',
                             'secret': secret}))


def frame_artifact(path: Path, name: str) -> None:
    value = path.read_bytes()
    if len(value) > 16 * 1024 * 1024:
        raise ProtocolError('ARTIFACT_OVER_BUDGET')
    print('ROBOCOPA_I2_ARTIFACT ' + name + ' ' + base64.b64encode(value).decode('ascii'), flush=True)


async def battle() -> None:
    if os.environ.get('ARENA_URL') != ARENA:
        raise ProtocolError('TRUSTED_ARENA_URL_REQUIRED')
    secret = os.environ.get('CONTROLLER_SECRET', '')
    if not secret or len(secret) < 24:
        raise ProtocolError('CONTROLLER_SECRET_REQUIRED')
    if 'BOT_SECRET' in os.environ:
        raise ProtocolError('BOT_SECRET_MUST_NOT_BE_VISIBLE_TO_CONTROLLER')
    started = 0
    ticks = 0
    rounds = []
    total = 0
    finish = None
    out = Path('/tmp/i2')
    out.mkdir(mode=0o700)
    replay_file = out / 'reference.battle.gz'
    try:
        async with AsyncExitStack() as stack:
            observer = await stack.enter_async_context(connect(ARENA, proxy=None,
                open_timeout=10, max_size=MAX_EVENT_BYTES, max_queue=8))
            await role_handshake(observer, 'Observer', secret)
            controller = await stack.enter_async_context(connect(ARENA, proxy=None,
                open_timeout=10, max_size=MAX_EVENT_BYTES, max_queue=8))
            await role_handshake(controller, 'Controller', secret)
            addresses = None
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                data = json.loads(await asyncio.wait_for(observer.recv(), timeout=deadline - time.monotonic()))
                if data.get('type') == 'BotListUpdate':
                    if len(data.get('bots', [])) == 2:
                        addresses = validate_bot_roster(data['bots'])
                        break
            if addresses is None:
                raise ProtocolError('OFFICIAL_BOT_LOBBY_TIMEOUT')
            await controller.send(json.dumps({'type': 'StartGame',
                'gameSetup': setup_classic(), 'botAddresses': addresses}))
            deadline = time.monotonic() + 150
            with gzip.open(replay_file, 'wt', encoding='utf-8', compresslevel=6) as replay:
                while time.monotonic() < deadline:
                    message = await asyncio.wait_for(observer.recv(),
                        timeout=min(12, deadline - time.monotonic()))
                    if not isinstance(message, str):
                        raise ProtocolError('BINARY_EVENT_DENIED')
                    total += len(message.encode('utf-8')) + 1
                    if total > MAX_RECORD_BYTES:
                        raise ProtocolError('REPLAY_TOO_LARGE')
                    data = json.loads(message)
                    kind = data.get('type')
                    if kind == 'GameAbortedEvent':
                        raise ProtocolError('OFFICIAL_GAME_ABORTED')
                    if kind == 'GameStartedEventForObserver':
                        started += 1
                        if started != 1 or data.get('gameSetup', {}).get('numberOfRounds') != ROUNDS:
                            raise ProtocolError('START_INVALID')
                    elif kind == 'RoundEndedEventForObserver':
                        rounds.append(data.get('roundNumber'))
                    elif kind == 'TickEventForObserver':
                        ticks += 1
                        if ticks > MAX_TICKS:
                            raise ProtocolError('TICK_BUDGET_EXCEEDED')
                    if kind in RECORD_TYPES:
                        replay.write(message + '\n')
                    if kind == 'GameEndedEventForObserver':
                        finish = validate_final(data, rounds, started, ticks)
                        break
            if finish is None:
                raise ProtocolError('OFFICIAL_GAME_END_TIMEOUT')
    except ConnectionClosed as err:
        raise ProtocolError('OFFICIAL_CONNECTION_CLOSED') from err
    results_file = out / 'results.json'
    results_file.write_text(json.dumps(finish, sort_keys=True, ensure_ascii=False), encoding='utf-8')
    finish['replay_sha256'] = hashlib.sha256(replay_file.read_bytes()).hexdigest()
    # stdout contains ONLY length-bounded, typed artifacts; no server/controller secrets.
    frame_artifact(results_file, 'results.json')
    frame_artifact(replay_file, 'reference.battle.gz')
    print('I2_COMPLETED_ROUNDS=' + str(ROUNDS), flush=True)


if __name__ == '__main__':
    try:
        asyncio.run(battle())
    except (OSError, ValueError, asyncio.TimeoutError, ConnectionClosed) as err:
        print('I2_FAILED ' + type(err).__name__ + ' ' + str(err)[:128], file=sys.stderr)
        sys.exit(1)
