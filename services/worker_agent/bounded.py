"""Bound output while reading, not after writing an unbounded file.

No shell. This component does not itself sandbox a process; Docker lifecycle
cleanup belongs to the owner of the invocation. POSIX implementation for worker.
"""
from __future__ import annotations
from dataclasses import dataclass
import os
import selectors
import signal
import subprocess
import time
from pathlib import Path


class ProcessBoundError(RuntimeError):
    def __init__(self, reason: str, output: bytes = b''):
        super().__init__(reason)
        self.reason = reason
        self.output = output


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    output: bytes
    elapsed_seconds: float


def capture(args: list[str], *, timeout: float, max_bytes: int,
            cwd: Path | None = None, env: dict | None = None,
            input_bytes: bytes | None = None) -> ProcessResult:
    if os.name != 'posix':
        raise ProcessBoundError('LINUX_WORKER_REQUIRED')
    if not isinstance(args, list) or not args or any(not isinstance(x, str) for x in args):
        raise ValueError('Argument vector required')
    if timeout <= 0 or max_bytes < 1:
        raise ValueError('Positive bounds required')
    if input_bytes is not None and (type(input_bytes) is not bytes or len(input_bytes)>65536):
        raise ValueError('Bounded bytes input required')
    started, data = time.monotonic(), bytearray()
    pending = memoryview(input_bytes or b'')
    with subprocess.Popen(args, stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, shell=False, close_fds=True,
                          start_new_session=True, cwd=cwd, env=env) as process:
        try:
            with selectors.DefaultSelector() as selector:
                os.set_blocking(process.stdout.fileno(), False)
                selector.register(process.stdout, selectors.EVENT_READ)
                if input_bytes is not None:
                    if pending:
                        os.set_blocking(process.stdin.fileno(), False)
                        selector.register(process.stdin, selectors.EVENT_WRITE)
                    else:
                        process.stdin.close()
                while selector.get_map():
                    remaining = timeout - (time.monotonic() - started)
                    if remaining <= 0:
                        raise ProcessBoundError('TIMEOUT', bytes(data))
                    for key, event in selector.select(min(remaining, 0.1)):
                        if event & selectors.EVENT_WRITE:
                            try:
                                sent = os.write(key.fd, pending[:4096])
                                pending = pending[sent:]
                            except BrokenPipeError:
                                pending = memoryview(b'')
                            if not pending:
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                            continue
                        block = os.read(key.fd, min(4096, max_bytes - len(data) + 1))
                        if not block:
                            selector.unregister(key.fileobj)
                            break
                        if len(data) + len(block) > max_bytes:
                            raise ProcessBoundError('OUTPUT_LIMIT', bytes(data))
                        data.extend(block)
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise ProcessBoundError('TIMEOUT', bytes(data))
                try:
                    result = process.wait(timeout=remaining)
                except subprocess.TimeoutExpired:
                    raise ProcessBoundError('TIMEOUT', bytes(data)) from None
                return ProcessResult(result, bytes(data), time.monotonic() - started)
        finally:
            # Only the private process group started above, never a global PID search.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
