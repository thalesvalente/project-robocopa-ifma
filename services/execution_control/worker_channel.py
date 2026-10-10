"""I3-02: genuine mutual TLS worker identity *probe* for disposable CI.

Not a public server, production PKI, job claim, worker, or student endpoint.
Certificates are supplied by a trusted local test harness, never by frames.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import socket
import ssl
import stat
import sys
from threading import Lock

BROKER_DNS = "broker.robocopa.invalid"
PROTOCOL = 1
MAX_FRAME = 512
TIMEOUT_SECONDS = 3.0
SHA = re.compile(r"^[0-9a-f]{64}$")
SCOPE = re.compile(r"^lab-[a-z0-9_-]{1,24}$")
WORKER_URI = re.compile(r"^urn:robocopa:worker:([a-z0-9_-]{1,32})$")
BROKER_URI = re.compile(r"^urn:robocopa:broker:([a-z0-9_-]{1,32})$")


class ChannelError(ValueError):
    """Stable code only; never echo peer input, certificates or paths."""


@dataclass(frozen=True)
class PeerGrant:
    """A certificate pin and one exact authorized lab scope/operation."""
    uri: str
    leaf_sha256: str
    scope_id: str
    operations: frozenset[str] = frozenset({"probe"})


@dataclass(frozen=True)
class LabChannelGate:
    enabled: bool = False


class TrustRegistry:
    """Trusted in-process allowlist with monotonic, atomic replacement.

    Revocation affects the next one-frame connection. Not a durable CRL,
    PKI enrollment service, or an RPC for changing access permissions.
    """

    def __init__(self, role: str, grants: tuple[PeerGrant, ...], *, revision: int = 1):
        if role not in ("worker", "broker") or type(revision) is not int or revision < 1:
            raise ChannelError("TRUST_CONFIG_INVALID")
        self.role = role
        self._lock = Lock()
        self._grants = self._validate(grants)
        self._revision = revision

    def _validate(self, grants: tuple[PeerGrant, ...]) -> dict[str, PeerGrant]:
        if type(grants) is not tuple:
            raise ChannelError("TRUST_CONFIG_INVALID")
        rule = WORKER_URI if self.role == "worker" else BROKER_URI
        result = {}
        for grant in grants:
            if (type(grant) is not PeerGrant
                    or not isinstance(grant.uri, str) or rule.fullmatch(grant.uri) is None
                    or type(grant.leaf_sha256) is not str or SHA.fullmatch(grant.leaf_sha256) is None
                    or type(grant.scope_id) is not str or SCOPE.fullmatch(grant.scope_id) is None
                    or type(grant.operations) is not frozenset
                    or grant.operations != frozenset({"probe"})
                    or grant.leaf_sha256 in result):
                raise ChannelError("TRUST_CONFIG_INVALID")
            result[grant.leaf_sha256] = grant
        return result

    def replace(self, grants: tuple[PeerGrant, ...], *, revision: int) -> None:
        """Local privileged call only; NEVER expose through a network frame."""
        new_grants = self._validate(grants)
        with self._lock:
            if type(revision) is not int or revision <= self._revision:
                raise ChannelError("TRUST_REVISION_INVALID")
            self._grants, self._revision = new_grants, revision

    def authorize(self, tls: ssl.SSLSocket, *, scope_id: str, operation: str) -> PeerGrant:
        if (not isinstance(tls, ssl.SSLSocket)
                or tls.context.verify_mode != ssl.CERT_REQUIRED
                or tls.version() != "TLSv1.3"):
            raise ChannelError("TLS_NOT_VERIFIED")
        if (type(scope_id) is not str or SCOPE.fullmatch(scope_id) is None
                or operation != "probe"):
            raise ChannelError("SCOPE_DENIED")
        leaf = tls.getpeercert(binary_form=True)
        info = tls.getpeercert()
        if not leaf or not isinstance(info, dict):
            raise ChannelError("PEER_DENIED")
        names = info.get("subjectAltName", ())
        uris = [value for kind, value in names if kind == "URI"]
        if len(uris) != 1:
            raise ChannelError("PEER_DENIED")
        digest = hashlib.sha256(leaf).hexdigest()
        with self._lock:
            grant = self._grants.get(digest)
        if (grant is None or uris[0] != grant.uri or grant.scope_id != scope_id
                or operation not in grant.operations):
            raise ChannelError("PEER_DENIED")
        return grant


def _paths(cafile: Path, certfile: Path, keyfile: Path) -> tuple[str, str, str]:
    paths = (cafile, certfile, keyfile)
    if any(not isinstance(p, Path) or not p.is_absolute()
           or not p.is_file() or p.is_symlink()
           or p.parent.is_symlink() for p in paths):
        raise ChannelError("TLS_CONFIG_INVALID")
    if stat.S_IMODE(keyfile.stat().st_mode) & 0o077:
        raise ChannelError("TLS_KEY_PERMISSIONS")
    return tuple(str(p) for p in paths)


def broker_tls_context(*, cafile: Path, certfile: Path, keyfile: Path) -> ssl.SSLContext:
    ca, cert, key = _paths(cafile, certfile, keyfile)
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(cafile=ca)
        context.load_cert_chain(certfile=cert, keyfile=key)
        return context
    except (OSError, ssl.SSLError):
        raise ChannelError("TLS_CONFIG_INVALID") from None


def worker_tls_context(*, cafile: Path, certfile: Path, keyfile: Path) -> ssl.SSLContext:
    ca, cert, key = _paths(cafile, certfile, keyfile)
    try:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_cert_chain(certfile=cert, keyfile=key)
        return context
    except (OSError, ssl.SSLError):
        raise ChannelError("TLS_CONFIG_INVALID") from None


def _unique_fields(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ChannelError("FRAME_INVALID")
        result[key] = value
    return result


def _reject_json_constant(_value: str):
    raise ChannelError("FRAME_INVALID")


def _read_json(tls: ssl.SSLSocket) -> dict:
    data = bytearray()
    while True:
        try:
            part = tls.recv(min(128, MAX_FRAME + 1 - len(data)))
        except (OSError, TimeoutError):
            raise ChannelError("FRAME_TIMEOUT") from None
        if not part:
            raise ChannelError("FRAME_INCOMPLETE")
        data.extend(part)
        if len(data) > MAX_FRAME:
            raise ChannelError("FRAME_TOO_LARGE")
        if b"\n" in part:
            if data.count(b"\n") != 1 or not data.endswith(b"\n"):
                raise ChannelError("FRAME_INVALID")
            break
    try:
        content = json.loads(bytes(data[:-1]).decode("utf-8"),
                             object_pairs_hook=_unique_fields,
                             parse_constant=_reject_json_constant)
    except ChannelError:
        raise
    except (ValueError, UnicodeError, RecursionError):
        raise ChannelError("FRAME_INVALID") from None
    if type(content) is not dict:
        raise ChannelError("FRAME_INVALID")
    return content


def _write_json(tls: ssl.SSLSocket, body: dict) -> None:
    encoded = (json.dumps(body, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")
    if len(encoded) > MAX_FRAME:
        raise ChannelError("FRAME_TOO_LARGE")
    tls.sendall(encoded)


def _runner_allowed() -> bool:
    return (sys.platform == "linux"
            and "microsoft" not in platform.release().lower()
            and os.environ.get("GITHUB_ACTIONS") == "true"
            and os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted")


def lab_listener(*, gate: LabChannelGate = LabChannelGate()) -> socket.socket:
    """Only 127.0.0.1 and ephemeral port in a disposable CI fixture."""
    if type(gate) is not LabChannelGate or gate.enabled is not True or not _runner_allowed():
        raise ChannelError("LAB_CHANNEL_DISABLED")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        sock.settimeout(TIMEOUT_SECONDS)
        return sock
    except BaseException:
        sock.close()
        raise


def serve_probe_once(listener: socket.socket, *, context: ssl.SSLContext,
                     authorized_workers: TrustRegistry) -> str:
    """Exactly one mTLS request; never accesses a queue or launches a worker."""
    if (not _runner_allowed() or not isinstance(listener, socket.socket)
            or listener.getsockname()[0] != "127.0.0.1"
            or context.verify_mode != ssl.CERT_REQUIRED
            or context.minimum_version != ssl.TLSVersion.TLSv1_3
            or authorized_workers.role != "worker"):
        raise ChannelError("LAB_CHANNEL_DISABLED")
    try:
        raw, _ = listener.accept()
    except OSError:
        return "CONNECTION_DENIED"
    try:
        with raw:
            raw.settimeout(TIMEOUT_SECONDS)
            with context.wrap_socket(raw, server_side=True) as tls:
                frame = _read_json(tls)
                if (set(frame) != {"schema_version", "operation", "scope_id"}
                        or type(frame["schema_version"]) is not int
                        or frame["schema_version"] != PROTOCOL
                        or frame["operation"] != "probe"):
                    raise ChannelError("REQUEST_DENIED")
                grant = authorized_workers.authorize(
                    tls, scope_id=frame["scope_id"], operation="probe")
                worker_id = WORKER_URI.fullmatch(grant.uri).group(1)
                _write_json(tls, {
                    "schema_version": PROTOCOL, "operation": "probe_ack",
                    "worker_id": worker_id, "scope_id": grant.scope_id,
                    "job_claim_enabled": False,
                })
                return "PROBE_OK"
    except (ssl.SSLError, OSError, ChannelError):
        return "REQUEST_DENIED"


def worker_probe(port: int, *, context: ssl.SSLContext,
                 authorized_brokers: TrustRegistry, scope_id: str,
                 raw_frame: bytes | None = None) -> dict:
    """Worker-initiated mTLS probe to the *loopback* CI broker, never remote."""
    if (not _runner_allowed() or type(port) is not int or not 1 <= port <= 65535
            or authorized_brokers.role != "broker"
            or context.verify_mode != ssl.CERT_REQUIRED
            or context.check_hostname is not True
            or context.minimum_version != ssl.TLSVersion.TLSv1_3):
        raise ChannelError("LAB_CHANNEL_DISABLED")
    if type(scope_id) is not str or SCOPE.fullmatch(scope_id) is None:
        raise ChannelError("SCOPE_DENIED")
    if raw_frame is not None and type(raw_frame) is not bytes:
        raise ChannelError("FRAME_INVALID")
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=TIMEOUT_SECONDS) as raw:
            raw.settimeout(TIMEOUT_SECONDS)
            with context.wrap_socket(raw, server_hostname=BROKER_DNS) as tls:
                authorized_brokers.authorize(tls, scope_id=scope_id, operation="probe")
                if raw_frame is None:
                    _write_json(tls, {
                        "schema_version": PROTOCOL, "operation": "probe",
                        "scope_id": scope_id,
                    })
                else:
                    if not 1 <= len(raw_frame) <= MAX_FRAME + 1:
                        raise ChannelError("FRAME_TOO_LARGE")
                    tls.sendall(raw_frame)
                response = _read_json(tls)
                if (set(response) != {"schema_version", "operation", "worker_id",
                                     "scope_id", "job_claim_enabled"}
                        or type(response["schema_version"]) is not int
                        or response["schema_version"] != PROTOCOL
                        or response["operation"] != "probe_ack"
                        or response["scope_id"] != scope_id
                        or response["job_claim_enabled"] is not False
                        or type(response["worker_id"]) is not str
                        or WORKER_URI.fullmatch("urn:robocopa:worker:"+response["worker_id"]) is None):
                    raise ChannelError("RESPONSE_INVALID")
                return response
    except ChannelError:
        raise
    except (ssl.SSLError, OSError):
        raise ChannelError("CHANNEL_UNAVAILABLE") from None
