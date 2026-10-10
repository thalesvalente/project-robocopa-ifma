"""Real TLS 1.3/mTLS integration tests, synthetic ephemeral certificates only.

OpenSSL runs locally in temp directories; nothing is uploaded or logged.
Never tests an actual VM, application API, student workload or public endpoint.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import ssl
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from services.execution_control import worker_channel as channel

def _openssl(*args: str) -> None:
    try:
        result = subprocess.run(["openssl", *args], capture_output=True,
                                timeout=30, check=False)
        if result.returncode:
            raise RuntimeError("TEST_CERT_PREPARATION_FAILED")
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError("TEST_CERT_PREPARATION_FAILED") from None

@unittest.skipUnless(sys.platform == "linux", "mTLS proof runs on disposable Ubuntu CI")
class I3MutualTLSLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("openssl") is None:
            raise AssertionError("OpenSSL is required; no mock identity fallback")
        cls.directory = tempfile.TemporaryDirectory(prefix="robocopa-mtls-fixture-")
        cls.root = Path(cls.directory.name)
        for suffix in ("primary", "other"):
            key, crt = cls.root / (suffix+".key"), cls.root / (suffix+".crt")
            _openssl("req", "-x509", "-newkey", "rsa:2048", "-nodes",
                     "-sha256", "-days", "1", "-keyout", str(key),
                     "-out", str(crt), "-subj", "/CN=CI-"+suffix,
                     "-addext", "basicConstraints=critical,CA:TRUE",
                     "-addext", "keyUsage=critical,keyCertSign,cRLSign")
            key.chmod(0o600)
        for name, role, dns, ca in [
            ("server", "broker", channel.BROKER_DNS, "primary"),
            ("bad-server", "broker", "fake.robocopa.invalid", "primary"),
            ("worker-a", "worker", None, "primary"),
            ("worker-a-next", "worker", None, "primary"),
            ("worker-b", "worker", None, "primary"),
            ("stranger", "worker", None, "primary"),
            ("wrong-role", "broker", None, "primary"),
            ("wrong-ca", "worker", None, "other"),
        ]:
            cls._issue(name, role, dns=dns, issuer=ca)

        cls.server_context = cls._server_context("server")
        cls.clients = {key:cls._client_context(key) for key in (
            "worker-a", "worker-a-next", "worker-b", "stranger", "wrong-role"
        )}
        cls.clients["wrong-ca"] = cls._client_context("wrong-ca", issuer="other")
        cls.worker_a = cls._worker_grant("worker-a")
        cls.worker_next = cls._worker_grant("worker-a-next", uri="urn:robocopa:worker:worker-a")
        cls.broker = cls._broker_grant("server")

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    @classmethod
    def _issue(cls, name: str, role: str, *, dns: str | None, issuer: str):
        key, csr, crt = (cls.root / (name + ending) for ending in (".key", ".csr", ".crt"))
        subject = "worker-a" if name == "worker-a-next" else name
        uri = "urn:robocopa:" + role + ":" + subject
        _openssl("req", "-newkey", "rsa:2048", "-nodes", "-sha256",
                 "-keyout", str(key), "-out", str(csr), "-subj", "/CN="+subject)
        key.chmod(0o600)
        ext = cls.root / (name + ".ext")
        san = "URI:"+uri + (",DNS:"+dns if dns is not None else "")
        ext.write_text(
            "basicConstraints=critical,CA:FALSE\n"
            "keyUsage=critical,digitalSignature,keyEncipherment\n"
            "extendedKeyUsage="+("serverAuth" if dns is not None else "clientAuth")+"\n"
            "subjectAltName="+san+"\n",
            encoding="ascii",
        )
        _openssl("x509", "-req", "-in", str(csr), "-CA", str(cls.root/(issuer+".crt")),
                 "-CAkey", str(cls.root/(issuer+".key")), "-CAcreateserial",
                 "-days", "1", "-sha256", "-extfile", str(ext), "-out", str(crt))

    @classmethod
    def _cert_digest(cls, name):
        return hashlib.sha256(
            ssl.PEM_cert_to_DER_cert((cls.root/(name+".crt")).read_text())
        ).hexdigest()

    @classmethod
    def _server_context(cls, name):
        return channel.broker_tls_context(
            cafile=cls.root/"primary.crt", certfile=cls.root/(name+".crt"),
            keyfile=cls.root/(name+".key"),
        )

    @classmethod
    def _client_context(cls, name, issuer="primary"):
        return channel.worker_tls_context(
            cafile=cls.root/(issuer+".crt"), certfile=cls.root/(name+".crt"),
            keyfile=cls.root/(name+".key"),
        )

    @classmethod
    def _worker_grant(cls, name, uri=None, scope="lab-a"):
        return channel.PeerGrant(
            uri or "urn:robocopa:worker:"+name,
            cls._cert_digest(name), scope,
        )

    @classmethod
    def _broker_grant(cls, name, scope="lab-a"):
        return channel.PeerGrant(
            "urn:robocopa:broker:"+name,
            cls._cert_digest(name), scope,
        )

    def setUp(self):
        self.allowed_workers = channel.TrustRegistry("worker", (self.worker_a,))
        self.allowed_brokers = channel.TrustRegistry("broker", (self.broker,))

    def exchange(self, *, client="worker-a", server="server", scope="lab-a",
                 request=None, workers=None, brokers=None, client_context=None):
        # CI default environment is github-hosted; patch is for local offline
        # reexecution in a container, NOT permission to run against a host VM.
        with patch.dict(os.environ, {"GITHUB_ACTIONS":"true",
                                     "RUNNER_ENVIRONMENT":"github-hosted"}):
            with closing(channel.lab_listener(gate=channel.LabChannelGate(True))) as listener:
                port = listener.getsockname()[1]
                server_context = (self.server_context if server=="server"
                                  else self._server_context(server))
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(
                        channel.serve_probe_once, listener, context=server_context,
                        authorized_workers=workers if workers is not None else self.allowed_workers,
                    )
                    error = None
                    reply = None
                    try:
                        reply = channel.worker_probe(
                            port, context=(self.clients[client] if client_context is None
                                           else client_context),
                            authorized_brokers=(self.allowed_brokers if brokers is None
                                                else brokers),
                            scope_id=scope, raw_frame=request,
                        )
                    except channel.ChannelError as exc:
                        error = str(exc)
                    result = future.result(timeout=10)
        return reply, error, result

    def assert_denied(self, **kwargs):
        reply, error, result = self.exchange(**kwargs)
        self.assertIsNone(reply)
        self.assertIsNotNone(error)
        self.assertNotEqual(result, "PROBE_OK")
        self.assertIn(result, ("REQUEST_DENIED", "CONNECTION_DENIED"))

    def test_real_mtls_tls13_positive(self):
        reply, error, server = self.exchange()
        self.assertIsNone(error)
        self.assertEqual(server, "PROBE_OK")
        self.assertEqual(reply, {"schema_version":1, "operation":"probe_ack",
                                 "scope_id":"lab-a", "worker_id":"worker-a",
                                 "job_claim_enabled":False})

    def test_lab_listener_disabled_by_default(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS":"true",
                                     "RUNNER_ENVIRONMENT":"github-hosted"}):
            with self.assertRaisesRegex(channel.ChannelError,"LAB_CHANNEL_DISABLED"):
                channel.lab_listener()

    def test_local_or_selfhosted_runner_fails_closed(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS":"false",
                                     "RUNNER_ENVIRONMENT":"self-hosted"}):
            with self.assertRaisesRegex(channel.ChannelError,"LAB_CHANNEL_DISABLED"):
                channel.lab_listener(gate=channel.LabChannelGate(True))

    def test_wsl_release_rejected(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS":"true",
                                     "RUNNER_ENVIRONMENT":"github-hosted"}), patch.object(
                                         channel.platform, "release", return_value="5.15-Microsoft-WSL2"):
            with self.assertRaisesRegex(channel.ChannelError, "LAB_CHANNEL_DISABLED"):
                channel.lab_listener(gate=channel.LabChannelGate(True))

    def test_tls_contexts_are_strict(self):
        self.assertEqual(self.server_context.verify_mode, ssl.CERT_REQUIRED)
        self.assertEqual(self.server_context.minimum_version, ssl.TLSVersion.TLSv1_3)
        self.assertEqual(self.server_context.maximum_version, ssl.TLSVersion.TLSv1_3)
        c = self.clients["worker-a"]
        self.assertTrue(c.check_hostname)
        self.assertEqual(c.verify_mode, ssl.CERT_REQUIRED)
        self.assertEqual(c.minimum_version, ssl.TLSVersion.TLSv1_3)
        self.assertEqual(c.maximum_version, ssl.TLSVersion.TLSv1_3)

    def test_client_without_certificate_rejected_in_handshake(self):
        ctx = ssl.create_default_context(
            ssl.Purpose.SERVER_AUTH, cafile=str(self.root/"primary.crt"))
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        ctx.maximum_version = ssl.TLSVersion.TLSv1_3
        self.assert_denied(client_context=ctx)

    def test_wrong_ca_rejected(self):
        self.assert_denied(client="wrong-ca")

    def test_wrong_broker_hostname_rejected(self):
        self.assert_denied(server="bad-server")

    def test_wrong_broker_leaf_pin_rejected(self):
        pinned = channel.TrustRegistry(
            "broker", (channel.PeerGrant(self.broker.uri, "a"*64, "lab-a"),))
        self.assert_denied(brokers=pinned)

    def test_unregistered_client_rejected_even_with_valid_ca(self):
        self.assert_denied(client="stranger")

    def test_wrong_client_role_rejected(self):
        self.assert_denied(client="wrong-role")

    def test_wrong_client_scope_rejected(self):
        brokers = channel.TrustRegistry(
            "broker", (self._broker_grant("server", scope="lab-b"),))
        self.assert_denied(scope="lab-b", brokers=brokers)

    def test_claim_never_authorized(self):
        self.assert_denied(request=b'{"schema_version":1,"operation":"claim","scope_id":"lab-a"}\n')

    def test_complete_never_authorized(self):
        self.assert_denied(request=b'{"schema_version":1,"operation":"complete","scope_id":"lab-a"}\n')

    def test_worker_identity_from_payload_rejected(self):
        self.assert_denied(request=b'{"schema_version":1,"operation":"probe","scope_id":"lab-a","worker_id":"worker-b"}\n')

    def test_duplicate_json_key_rejected(self):
        self.assert_denied(request=b'{"schema_version":1,"operation":"probe","operation":"probe","scope_id":"lab-a"}\n')

    def test_non_finite_json_rejected(self):
        self.assert_denied(request=b'{"schema_version":NaN,"operation":"probe","scope_id":"lab-a"}\n')

    def test_unknown_fields_denied(self):
        self.assert_denied(request=b'{"schema_version":1,"operation":"probe","scope_id":"lab-a","docker_args":"--privileged"}\n')

    def test_binary_garbage_denied(self):
        self.assert_denied(request=b'\xff\x00\n')

    def test_extra_frame_denied(self):
        self.assert_denied(request=b'{"schema_version":1,"operation":"probe","scope_id":"lab-a"}\n{"x":1}\n')

    def test_oversize_frame_denied(self):
        self.assert_denied(request=b"x"*513)

    def test_missing_newline_times_out_with_no_job(self):
        self.assert_denied(request=b'{"schema_version":1,"operation":"probe","scope_id":"lab-a"}')

    def test_allowlist_rotation_overlap_then_revoke_old(self):
        self.allowed_workers.replace((self.worker_a, self.worker_next), revision=2)
        reply_old, _, state_old = self.exchange()
        reply_new, _, state_new = self.exchange(client="worker-a-next")
        self.assertEqual(state_old, "PROBE_OK")
        self.assertEqual(state_new, "PROBE_OK")
        self.assertEqual(reply_old["worker_id"], reply_new["worker_id"])
        self.allowed_workers.replace((self.worker_next,), revision=3)
        self.assert_denied(client="worker-a")
        self.assertEqual(self.exchange(client="worker-a-next")[2], "PROBE_OK")

    def test_revocation_fails_closed_to_empty_registry(self):
        self.allowed_workers.replace((), revision=2)
        self.assert_denied()

    def test_rollback_revision_rejected(self):
        with self.assertRaisesRegex(channel.ChannelError,"TRUST_REVISION_INVALID"):
            self.allowed_workers.replace((), revision=1)

    def test_cannot_allow_claim_in_trust_registry(self):
        grant = channel.PeerGrant(self.worker_a.uri, self.worker_a.leaf_sha256,
                                  "lab-a", frozenset({"probe","claim"}))
        with self.assertRaisesRegex(channel.ChannelError, "TRUST_CONFIG_INVALID"):
            channel.TrustRegistry("worker", (grant,))

    def test_wrong_leaf_digest_cannot_bypass_issuer(self):
        wrong = channel.TrustRegistry("worker", (
            channel.PeerGrant(self.worker_a.uri, "a"*64, "lab-a"),))
        self.assert_denied(workers=wrong)

    def test_leaves_generated_only_in_temp_and_key_private(self):
        for name in ("server","worker-a","worker-a-next","worker-b","wrong-role"):
            mode = stat.S_IMODE((self.root/(name+".key")).stat().st_mode)
            self.assertEqual(mode & 0o077, 0)
        self.assertTrue(str(self.root).startswith("/tmp/"))

    def test_no_job_execution_or_queue_side_effect(self):
        with patch("subprocess.Popen", side_effect=AssertionError("no process")), patch(
            "services.execution_control.store.SQLiteQueue.enqueue",
            side_effect=AssertionError("no enqueue")
        ):
            reply, _, server = self.exchange()
        self.assertEqual(server, "PROBE_OK")
        self.assertFalse(reply["job_claim_enabled"])
