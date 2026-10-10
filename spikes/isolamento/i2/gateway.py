"""CI-only role-filtering WebSocket gateway: bot-side -> official Tank Royale server.

Bot messages cannot reach the trusted server unless explicitly allowed.  The
upstream server 1.4.0 dispatches control messages without checking socket role
in its message switch; this gateway is mandatory defense-in-depth, not a
production-grade security boundary. A dedicated VM and protocol audit remain.
"""
from __future__ import annotations

import asyncio
import json
import os
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

BOT_TYPES = frozenset({'BotHandshake', 'BotReady', 'BotIntent', 'TeamMessage'})
CONTROL_TYPES = frozenset({'StartGame', 'StopGame', 'PauseGame', 'ResumeGame',
                           'ChangeTps', 'NextTurn', 'ControllerHandshake',
                           'ObserverHandshake', 'BotPolicyUpdate',
                           'EnableDebugMode', 'DisableDebugMode'})
EXPECTED_NAMES = frozenset({'Walls', 'Spin Bot'})
MAX_INBOUND = 32 * 1024
MAX_CLIENTS = 3  # two official bots plus one negative-policy probe
ACTIVE = 0


class FilterError(ValueError):
    pass


def check_bot_payload(message: str | bytes, *, first: bool) -> str:
    if not isinstance(message, str):
        raise FilterError('BINARY_DENIED')
    if len(message.encode('utf-8')) > MAX_INBOUND:
        raise FilterError('MESSAGE_TOO_LARGE')
    try:
        obj = json.loads(message)
    except (TypeError, ValueError):
        raise FilterError('MALFORMED_JSON') from None
    if not isinstance(obj, dict):
        raise FilterError('NOT_OBJECT')
    kind = obj.get('type')
    if not isinstance(kind, str) or kind not in BOT_TYPES:
        raise FilterError('TYPE_DENIED')
    if first:
        if kind != 'BotHandshake':
            raise FilterError('HANDSHAKE_REQUIRED')
        if obj.get('name') not in EXPECTED_NAMES or obj.get('version') != '1.0':
            raise FilterError('IDENTITY_DENIED')
        if not isinstance(obj.get('sessionId'), str) or not obj['sessionId']:
            raise FilterError('SESSION_REQUIRED')
    elif kind == 'BotHandshake':
        raise FilterError('DUPLICATE_HANDSHAKE')
    return kind


async def handle_bot(bot):
    global ACTIVE
    if ACTIVE >= MAX_CLIENTS:
        await bot.close(code=1008, reason='CAPACITY_DENIED')
        return
    ACTIVE += 1
    upstream = None
    try:
        async with connect(os.environ['ARENA_URL'], proxy=None, open_timeout=8,
                           max_size=512 * 1024, max_queue=8) as upstream:
            async def inbound():
                first = True
                async for message in bot:
                    try:
                        check_bot_payload(message, first=first)
                    except FilterError as error:
                        await bot.close(code=1008, reason=str(error))
                        return
                    first = False
                    await upstream.send(message)

            async def outbound():
                async for message in upstream:
                    await bot.send(message)

            jobs = {asyncio.create_task(inbound()), asyncio.create_task(outbound())}
            done, pending = await asyncio.wait(jobs, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            await asyncio.gather(*jobs, return_exceptions=True)
            for task in done:
                if task.exception() is not None and not isinstance(task.exception(), ConnectionClosed):
                    raise task.exception()
    except (OSError, ConnectionClosed, asyncio.TimeoutError):
        pass  # No network paths/credentials in logs; connection is closed by context.
    finally:
        ACTIVE -= 1
        try:
            await bot.close(code=1000)
        except ConnectionClosed:
            pass


async def main():
    url = os.environ.get('ARENA_URL', '')
    if url != 'ws://referee:7654':
        raise SystemExit('ARENA_POLICY_DENIED')
    async with serve(handle_bot, '0.0.0.0', 7660, max_size=MAX_INBOUND,
                     max_queue=8, ping_interval=20, compression=None):
        print('GATEWAY_READY', flush=True)
        await asyncio.Future()


if __name__ == '__main__':
    asyncio.run(main())
