"""I3-03C outbound HTTPS command client; never runs a bot or accepts a DB secret.

A trusted launcher provisions endpoint, own worker/scope and short-lived token.
Persist the request ID when retrying an unknown result; no automatic retry here.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import re
import ssl
import stat
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPSHandler, HTTPRedirectHandler
from uuid import UUID

UUID4 = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')
FENCE = re.compile(r'^[1-9][0-9]{0,18}$')
SHA = re.compile(r'^[0-9a-f]{64}$')
SCOPE = re.compile(r'^[a-z][a-z0-9-]{0,31}$')
TOKEN = re.compile(r'^rcw_[0-9a-f]{64}$')
OPS = frozenset(('claim','start','heartbeat','fail'))
REASONS = frozenset(('WORKER_STOPPED','ENGINE_FAILURE','RESOURCE_LIMIT'))
ERRORS = frozenset(('CREDENTIAL_DENIED','COMMAND_INVALID','REQUEST_DENIED','REQUEST_CONFLICT',
                   'REQUEST_EXPIRED','STALE_LEASE','WORKER_BUSY','RATE_LIMITED','RECEIPT_LIMIT',
                   'EXECUTION_DISABLED','STORAGE_UNAVAILABLE'))

class WorkerClientError(ValueError):
    """Sanitized refusal; never contains token, URL, body or server diagnostics."""

class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise WorkerClientError('REDIRECT_DENIED')

def _unique(pairs):
    data={}
    for key,value in pairs:
        if key in data: raise WorkerClientError('RESPONSE_INVALID')
        data[key]=value
    return data

def _constant(_): raise WorkerClientError('RESPONSE_INVALID')

def _time(value):
    if type(value) is not str: raise WorkerClientError('RESPONSE_INVALID')
    try:
        result=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError: raise WorkerClientError('RESPONSE_INVALID') from None
    if result.tzinfo is None: raise WorkerClientError('RESPONSE_INVALID')
    return result

def _uuid(value): return type(value) is str and UUID4.fullmatch(value) is not None

def _fence(value):
    return type(value) is str and FENCE.fullmatch(value) is not None and int(value)<=9223372036854775807

def read_worker_token(path: Path) -> str:
    """Trusted configuration file only. Do not embed this token in bot inputs."""
    if not isinstance(path,Path) or not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise WorkerClientError('TOKEN_FILE_INVALID')
    if any(p.is_symlink() for p in path.parents) or stat.S_IMODE(path.stat().st_mode)&0o077:
        raise WorkerClientError('TOKEN_FILE_INVALID')
    try:
        with path.open('r',encoding='ascii') as stream: token=stream.read(70).strip()
    except (OSError,UnicodeError): raise WorkerClientError('TOKEN_FILE_INVALID') from None
    if not TOKEN.fullmatch(token): raise WorkerClientError('TOKEN_FILE_INVALID')
    return token

@dataclass(frozen=True)
class Command:
    request_id: str
    operation: str
    arguments: dict = field(default_factory=dict)

    def encode(self) -> bytes:
        if not _uuid(self.request_id) or self.operation not in OPS or type(self.arguments) is not dict:
            raise WorkerClientError('COMMAND_INVALID')
        args=dict(self.arguments)
        expected=set() if self.operation=='claim' else {'job_id','attempt_id','fence'}
        if self.operation=='fail': expected.add('reason')
        if set(args)!=expected: raise WorkerClientError('COMMAND_INVALID')
        if self.operation!='claim' and (not _uuid(args['job_id']) or not _uuid(args['attempt_id']) or not _fence(args['fence'])):
            raise WorkerClientError('COMMAND_INVALID')
        if self.operation=='fail' and args['reason'] not in REASONS: raise WorkerClientError('COMMAND_INVALID')
        return json.dumps(dict(schema_version=1,request_id=self.request_id,operation=self.operation,**args),separators=(',',':')).encode('ascii')

class WorkerControlClient:
    def __init__(self,endpoint: str, *, token: str, worker_id: str, scope_id: str,
                 cafile: Path | None = None, allow_loopback: bool = False) -> None:
        try:
            u=urlsplit(endpoint);port=u.port
        except (ValueError,TypeError): raise WorkerClientError('CONFIG_INVALID') from None
        if (type(endpoint) is not str or u.scheme!='https' or not u.hostname or u.username or u.password
             or u.query or u.fragment or u.path not in ('/worker-control','/functions/v1/worker-control')
             or not _uuid(worker_id) or type(scope_id) is not str or not SCOPE.fullmatch(scope_id)
             or type(token) is not str or not TOKEN.fullmatch(token) or type(allow_loopback) is not bool):
            raise WorkerClientError('CONFIG_INVALID')
        is_loopback=u.hostname=='localhost'
        try: is_loopback=is_loopback or ipaddress.ip_address(u.hostname).is_loopback
        except ValueError: pass
        if is_loopback and not allow_loopback: raise WorkerClientError('CONFIG_INVALID')
        try:
            ctx=ssl.create_default_context(cafile=str(cafile) if cafile else None)
            ctx.minimum_version=ssl.TLSVersion.TLSv1_2
        except (OSError,ssl.SSLError): raise WorkerClientError('TLS_CONFIG_INVALID') from None
        self._opener=build_opener(ProxyHandler({}),_NoRedirect(),HTTPSHandler(context=ctx))
        self._endpoint=endpoint; self._token=token;self.worker_id=worker_id;self.scope_id=scope_id

    def request(self, command: Command) -> dict:
        if type(command) is not Command: raise WorkerClientError('COMMAND_INVALID')
        body=command.encode()
        req=Request(self._endpoint,data=body,method='POST',headers={
            'Content-Type':'application/json','Authorization':'Bearer '+self._token,
            'Accept':'application/json',
        })
        try:
            with self._opener.open(req,timeout=5) as response:
                if response.status!=200 or response.headers.get_content_type()!='application/json':
                    raise WorkerClientError('RESPONSE_INVALID')
                raw=response.read(8193)
        except HTTPError as exc:
            if 300<=exc.code<400: raise WorkerClientError('REDIRECT_DENIED') from None
            raw=exc.read(1025);exc.close()
            try:
                error=json.loads(raw,object_pairs_hook=_unique,parse_constant=_constant)
                code=error.get('error') if type(error) is dict else None
            except (ValueError,UnicodeError): code=None
            raise WorkerClientError(code if type(code) is str and code in ERRORS else 'CHANNEL_UNAVAILABLE') from None
        except (URLError,TimeoutError,OSError):
            # Server may have committed. Reconcile using SAME command.request_id.
            raise WorkerClientError('COMMAND_OUTCOME_UNKNOWN') from None
        if len(raw)>8192: raise WorkerClientError('RESPONSE_INVALID')
        try: result=json.loads(raw,object_pairs_hook=_unique,parse_constant=_constant)
        except (ValueError,UnicodeError): raise WorkerClientError('RESPONSE_INVALID') from None
        return self._validate(result,command)

    def _validate(self, data: dict, command: Command) -> dict:
        if (type(data) is not dict or set(data)!={'schema_version','request_id','operation','worker_id','scope_id','result'}
            or type(data['schema_version']) is not int or data['schema_version']!=1
            or data['request_id']!=command.request_id or data['operation']!=command.operation
            or data['worker_id']!=self.worker_id or data['scope_id']!=self.scope_id):
            raise WorkerClientError('RESPONSE_INVALID')
        r=data['result']
        if command.operation=='claim' and r is None: return data
        if type(r) is not dict: raise WorkerClientError('RESPONSE_INVALID')
        if command.operation=='claim':
            if set(r)!={'job_id','attempt_id','fence','lease_until','deadline_at','descriptor'} or not _uuid(r['job_id']) or not _uuid(r['attempt_id']) or not _fence(r['fence']):
                raise WorkerClientError('RESPONSE_INVALID')
            lease=_time(r['lease_until']);deadline=_time(r['deadline_at'])
            if lease<=datetime.now(timezone.utc) or lease>deadline: raise WorkerClientError('RESPONSE_STALE')
            d=r['descriptor']
            if (type(d) is not dict or set(d)!={'version_id','source_sha256','program_sha256','java_sha256','policy_sha256','engine_ref','rounds'}
                or type(d['version_id']) is not str or re.fullmatch(r'[A-Za-z0-9_-]{1,64}',d['version_id']) is None
                or any(type(d[k]) is not str or not SHA.fullmatch(d[k]) for k in ('source_sha256','program_sha256','java_sha256','policy_sha256'))
                or d['engine_ref']!='tank-royale/1.4.0' or type(d['rounds']) is not int or not 1<=d['rounds']<=3):
                raise WorkerClientError('RESPONSE_INVALID')
        elif command.operation in ('start','heartbeat'):
            allowed=('RUNNING',) if command.operation=='start' else ('LEASED','RUNNING')
            if set(r)!={'state','fence','lease_until'} or r['state'] not in allowed or r['fence']!=command.arguments['fence']:
                raise WorkerClientError('RESPONSE_INVALID')
            if _time(r['lease_until'])<=datetime.now(timezone.utc): raise WorkerClientError('RESPONSE_STALE')
        elif set(r)!={'state'} or r['state'] not in ('QUEUED','FAILED','EXPIRED'):
            raise WorkerClientError('RESPONSE_INVALID')
        return data
