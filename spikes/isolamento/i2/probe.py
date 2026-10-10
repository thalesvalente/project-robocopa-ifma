"""Fixed negative protocol check, only run in disposable GitHub-hosted CI.

The attack is deliberately constrained to a synthetic standalone referee: it
must be stopped by the gateway before a privileged command reaches upstream.
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

URL = 'ws://gateway:7660'

async def main() -> None:
    if os.environ.get('GATEWAY_URL') != URL:
        raise ValueError('GATEWAY_REQUIRED')
    # A client carrying only the (synthetic) bot credential must NEVER use a
    # controller command. The policy gateway rejects the TYPE, irrespective of
    # whether the official referee would validate the role.
    for kind in ('ControllerHandshake', 'StartGame', 'StopGame'):
        async with connect(URL, proxy=None, open_timeout=8) as ws:
            greeting = json.loads(await asyncio.wait_for(ws.recv(), timeout=8))
            if greeting.get('type') != 'ServerHandshake':
                raise ValueError('GATEWAY_DID_NOT_FORWARD_OFFICIAL_HANDSHAKE')
            await ws.send(json.dumps({'type': kind, 'sessionId': greeting['sessionId'],
                                      'name': 'Probe', 'version': '1.0'}))
            try:
                await asyncio.wait_for(ws.recv(), timeout=5)
                raise ValueError('PROTOCOL_VIOLATION_NOT_BLOCKED')
            except ConnectionClosed as err:
                if err.rcvd is None or err.rcvd.code != 1008:
                    raise ValueError('WRONG_GATEWAY_REJECTION') from err
    # A correctly authenticated *bot* connection must still be unable to send
    # StartGame. This is the key role-bypass regression on the upstream 1.4.0
    # message dispatcher. Secrets are synthetic and never logged.
    async with connect(URL, proxy=None, open_timeout=8) as ws:
        greeting = json.loads(await asyncio.wait_for(ws.recv(), timeout=8))
        if greeting.get('type') != 'ServerHandshake':
            raise ValueError('HANDSHAKE_NOT_FORWARDED')
        await ws.send(json.dumps({'type': 'BotHandshake', 'sessionId': greeting['sessionId'],
                                  'name': 'Walls', 'version': '1.0', 'authors': ['CI'],
                                  'secret': os.environ['BOT_SECRET']}))
        await asyncio.sleep(0.2)
        await ws.send(json.dumps({'type': 'StartGame', 'gameSetup': {},
                                  'botAddresses': []}))
        try:
            await asyncio.wait_for(ws.recv(), timeout=5)
            raise ValueError('BOT_ROLE_ESCALATION_ALLOWED')
        except ConnectionClosed as err:
            if err.rcvd is None or err.rcvd.code != 1008:
                raise ValueError('WRONG_AUTHENTICATED_BOT_DENIAL') from err

    # Name isolation alone is insufficient: test direct TCP to the official
    # referee's numeric address while its server process is running. This
    # synthetic probe knows the address, unlike actual participants.
    import errno
    import ipaddress
    import socket
    try:
        socket.getaddrinfo('referee', 7654)
    except socket.gaierror:
        pass
    else:
        raise ValueError('REFEREE_NAME_LEAKS_TO_BOT_NETWORK')
    referee_ip = os.environ.get('REFEREE_IP', '')
    try:
        ip = ipaddress.ip_address(referee_ip)
        if ip.version != 4 or not ip.is_private:
            raise ValueError('REFEREE_IP_INVALID')
    except ValueError as exc:
        raise ValueError('REFEREE_IP_INVALID') from exc
    try:
        with socket.create_connection((referee_ip, 7654), timeout=0.9):
            pass
    except OSError as exc:
        if exc.errno not in (errno.ETIMEDOUT, errno.EHOSTUNREACH, errno.ENETUNREACH, errno.EACCES):
            raise ValueError('REFEREE_DIRECT_ROUTE_INCONCLUSIVE') from exc
    else:
        raise ValueError('REFEREE_DIRECT_IP_REACHABLE')
    print('I2_NEGATIVE_PASS: admin types denied, DNS and numeric referee route blocked')

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (OSError, ValueError, asyncio.TimeoutError) as exc:
        print('I2_NEGATIVE_FAILED ' + str(exc), file=sys.stderr)
        sys.exit(1)
