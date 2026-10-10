"""Internal I3-01 admission broker: offline only, fail-closed by default.

LabGate and owner_ref are supplied solely by trusted TEST fixture code, not
student input or HTTP. No actual worker identity/authentication is claimed.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping
from services.worker_agent.contracts import AdmissionError, ApprovedVersion, admit
from .store import QueueError, QueueReceipt, SQLiteQueue

class BrokerError(ValueError):
    """Sanitized, stable refusal code."""

@dataclass(frozen=True)
class LabGate:
    enabled: bool = False
    synthetic_worker_ready: bool = False

class InternalBroker:
    def __init__(self, queue: SQLiteQueue, *,
                 registry: Mapping[str, ApprovedVersion],
                 policy_sha256: str, gate: LabGate = LabGate()) -> None:
        if not isinstance(queue, SQLiteQueue):
            raise BrokerError("QUEUE_INVALID")
        if (type(gate) is not LabGate or type(gate.enabled) is not bool
                or type(gate.synthetic_worker_ready) is not bool):
            raise BrokerError("GATE_INVALID")
        self._queue = queue
        self._registry = registry
        self._policy_sha256 = policy_sha256
        self._gate = gate

    def submit(self, raw: bytes, source: str, *, owner_ref: str,
               now: datetime | None = None) -> QueueReceipt:
        if self._gate.enabled is not True:
            raise BrokerError("EXECUTION_DISABLED")
        if self._gate.synthetic_worker_ready is not True:
            raise BrokerError("WORKER_UNAVAILABLE")
        try:
            job = admit(raw, source, registry=self._registry,
                        allowed_policy_sha256=self._policy_sha256,
                        enabled=True, now=now)
            return self._queue.enqueue(job, owner_ref=owner_ref, now=now)
        except (AdmissionError, QueueError) as exc:
            raise BrokerError(str(exc)) from None
