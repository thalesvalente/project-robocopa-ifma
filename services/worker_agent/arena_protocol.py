"""I2 bot-channel allowlist. Not general authentication or public API.

The official engine remains unchanged. Only BotHandshake then BotReady/BotIntent
may traverse this channel. Controller/observer sessions stay referee-local.
"""
from __future__ import annotations
import json
import math
import re
import secrets

MAX_MESSAGE = 16384
BOT_OUTPUT_TYPES = frozenset({'GameStartedEventForBot', 'GameEndedEventForBot',
    'RoundStartedEvent', 'RoundEndedEventForBot', 'TickEventForBot',
    'SkippedTurnEvent', 'GameAbortedEvent'})
HANDSHAKE_FIELDS = frozenset({'type','sessionId','name','version','authors','secret',
    'teamMemberName','description','homepage','countryCodes','gameTypes','platform',
    'programmingLang','debuggerAttached','teamMessageBatchVersion','isDroid'})
NUMBERS = frozenset({'turnRate','gunTurnRate','radarTurnRate','targetSpeed','firepower'})
BOOLEANS = frozenset({'adjustGunForBodyTurn','adjustRadarForBodyTurn',
    'adjustRadarForGunTurn','rescan','fireAssist'})
COLORS = frozenset({'bodyColor','turretColor','radarColor','bulletColor','scanColor',
    'tracksColor','gunColor'})
TEXT = frozenset({'stdOut','stdErr'})

class ProtocolDenied(ValueError):
    """Stable code only: never echo a token or raw input."""

def _pairs(items):
    obj = {}
    for key, value in items:
        if key in obj:
            raise ProtocolDenied('DUPLICATE_FIELD')
        obj[key] = value
    return obj

def decode(raw: str, *, limit=MAX_MESSAGE) -> dict:
    if not isinstance(raw, str):
        raise ProtocolDenied('TEXT_ONLY')
    try:
        if len(raw.encode('utf-8')) > limit:
            raise ProtocolDenied('MESSAGE_LIMIT')
        data = json.loads(raw, object_pairs_hook=_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ProtocolDenied('NON_FINITE')))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ProtocolDenied('INVALID_JSON') from None
    if not isinstance(data, dict) or not isinstance(data.get('type'), str):
        raise ProtocolDenied('MESSAGE_SHAPE')
    return data

def handshake(raw: str, *, session: str, identities: dict[str, tuple[str,str]],
              upstream_secret: str) -> tuple[str, dict]:
    data = decode(raw)
    if data['type'] != 'BotHandshake' or set(data) - HANDSHAKE_FIELDS:
        raise ProtocolDenied('BOT_HANDSHAKE_ONLY')
    if 'isDroid' in data and data['isDroid'] is not False:
        raise ProtocolDenied('REFERENCE_DROID_MODE_ONLY')
    token = data.get('secret')
    if not isinstance(token, str) or len(token) > 128 or not token.isascii():
        raise ProtocolDenied('CREDENTIAL_INVALID')
    match = next((key for key in identities if secrets.compare_digest(key,token)), None)
    if match is None:
        raise ProtocolDenied('CREDENTIAL_INVALID')
    if data.get('sessionId') != session:
        raise ProtocolDenied('SESSION_MISMATCH')
    name, version = identities[match]
    if data.get('name') != name or data.get('version') != version:
        raise ProtocolDenied('IDENTITY_MISMATCH')
    # Only known public metadata are sent; no caller text beyond verified identity.
    return name, {'type':'BotHandshake','sessionId':session,'name':name,
                 'version':version,'authors':['RoboCopa I2 reference'],
                 'secret':upstream_secret}

def intent(raw: str) -> dict:
    data = decode(raw)
    if data['type'] == 'BotReady' and set(data) == {'type'}:
        return data
    if data['type'] != 'BotIntent':
        raise ProtocolDenied('BOT_MESSAGE_ONLY')
    if set(data) - (NUMBERS | BOOLEANS | COLORS | TEXT | {'type'}):
        raise ProtocolDenied('INTENT_FIELD_DENIED')
    for key,value in data.items():
        if key in NUMBERS:
            if type(value) not in (int,float) or abs(value)>1e6 or not math.isfinite(value):
                raise ProtocolDenied('INTENT_NUMBER')
        elif key in BOOLEANS and type(value) is not bool:
            raise ProtocolDenied('INTENT_BOOLEAN')
        elif key in COLORS and (not isinstance(value,str) or not re.fullmatch(r'#[a-fA-F0-9]{6}',value)):
            raise ProtocolDenied('INTENT_COLOR')
        elif key in TEXT and (not isinstance(value,str) or len(value)>2048):
            raise ProtocolDenied('INTENT_TEXT')
    return data
