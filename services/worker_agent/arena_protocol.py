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
    return name, {'type':'BotHandshake','sessionId':session,'name':name,
                 'version':version,'authors':['RoboCopa I2 reference'],
                 'secret':upstream_secret}

def intent(raw: str) -> dict:
    data = decode(raw)
    if data['type'] == 'BotReady' and set(data) == {'type'}:
        return data
    if data['type'] != 'BotIntent':
        raise ProtocolDenied('BOT_MESSAGE_ONLY')
    # The SDK's empty list has no action; actual team messaging stays denied.
    if 'teamMessages' in data:
        if type(data['teamMessages']) is not list or data['teamMessages']:
            raise ProtocolDenied('TEAM_MESSAGES_DENIED')
        data.pop('teamMessages')
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


# Diagnostic budgets for three-round reference games, not production SLAs.
from dataclasses import dataclass
import time

@dataclass(frozen=True)
class BudgetLimits:
    messages: int = 20000
    input_bytes: int = 16 * 1024**2
    output_bytes: int = 64 * 1024**2
    lifetime_seconds: float = 150
    idle_seconds: float = 30

    def __post_init__(self):
        for value in (self.messages,self.input_bytes,self.output_bytes):
            if type(value) is not int or not 0 < value <= 64 * 1024**2:
                raise ValueError('INVALID_CONNECTION_BUDGET')
        for value in (self.lifetime_seconds,self.idle_seconds):
            if type(value) not in (int,float) or not math.isfinite(value) or not 0 < value <= 240:
                raise ValueError('INVALID_CONNECTION_DEADLINE')

class SessionBudget:
    """One client reader and one engine reader; counters never contain payloads."""
    def __init__(self,limits=None,*,clock=time.monotonic):
        self.limits=limits if limits is not None else BudgetLimits()
        self.clock=clock;self.start=self.last=clock()
        self.messages=0;self.input_bytes=0;self.output_bytes=0
    @staticmethod
    def size(raw):
        if type(raw) is not str:raise ProtocolDenied('TEXT_ONLY')
        try:return len(raw.encode('utf-8'))
        except UnicodeError:raise ProtocolDenied('INVALID_TEXT') from None
    def wait_timeout(self):
        now=self.clock()
        lifetime=self.limits.lifetime_seconds-(now-self.start)
        idle=self.limits.idle_seconds-(now-self.last)
        if lifetime<=0:raise ProtocolDenied('SESSION_LIMIT')
        if idle<=0:raise ProtocolDenied('IDLE_LIMIT')
        return min(lifetime,idle)
    def accept(self,raw):
        self.wait_timeout()
        size=self.size(raw)
        if self.messages>=self.limits.messages:raise ProtocolDenied('MESSAGE_BUDGET')
        if self.input_bytes+size>self.limits.input_bytes:raise ProtocolDenied('INPUT_BUDGET')
        self.messages+=1;self.input_bytes+=size;self.last=self.clock()
    def accept_output(self,raw):
        if self.clock()-self.start>=self.limits.lifetime_seconds:raise ProtocolDenied('SESSION_LIMIT')
        size=self.size(raw)
        if self.output_bytes+size>self.limits.output_bytes:raise ProtocolDenied('OUTPUT_BUDGET')
        self.output_bytes+=size
