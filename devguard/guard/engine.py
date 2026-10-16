"""Immutable inspections and one-use delivery; missing checks hold requests."""

import asyncio
from dataclasses import dataclass, field
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import secrets
import time
from uuid import uuid4

from devguard.guard.redaction import redact
from devguard.schemas.guard import Decision, GuardInput


class GuardError(Exception):
    def __init__(self, code, status=409):
        self.code, self.status = code, status
        super().__init__(code)


@dataclass
class Inspection:
    request_id: str
    owner: str
    version: int
    destination: str
    policy_revision: str
    decision: Decision
    reasons: list[str]
    deadline: float
    expires_at: str
    candidate: str | None = field(default=None, repr=False)
    delivered: bool = False
    consumed: bool = False

    def view(self):
        return {
            "request_id": self.request_id, "content_version": self.version,
            "policy_revision": self.policy_revision, "destination_id": self.destination,
            "decision": self.decision.value, "safe_preview": self.candidate,
            "reason_codes": self.reasons, "finding_ids": [self.request_id] if self.reasons else [],
            "status": "READY" if self.candidate is not None else "FAILED",
            "expires_at": self.expires_at, "delivered": self.delivered,
        }


class GuardEngine:
    def __init__(self, scanner, inspector, audit, *, receivers=None, clock=time.monotonic, ttl=60):
        self.scanner, self.inspector, self.audit = scanner, inspector, audit
        self.receivers = dict(receivers or {})
        self.clock, self.ttl = clock, ttl
        self.policy_revision = "policy-v1"
        self.records = {}
        self.key = secrets.token_bytes(32)
        self._release_lock = asyncio.Lock()
        self._inflight = 0

    def fingerprint(self, text, *, task=None):
        material = json.dumps([task, text], ensure_ascii=False, separators=(",", ":")).encode()
        return hmac.new(self.key, material, hashlib.sha256).hexdigest()

    def expire(self):
        for identifier, record in list(self.records.items()):
            if record.deadline <= self.clock():
                record.candidate = None
                del self.records[identifier]

    def revoke(self, identifier):
        record = self.records.pop(identifier, None)
        if record:
            record.candidate = None

    def get(self, identifier, owner):
        self.expire()
        record = self.records.get(identifier)
        if record is None or record.owner != owner:
            raise GuardError("INSPECTION_EXPIRED_OR_UNKNOWN", 404)
        return record

    def clone_for_version(self, identifier, *, owner, version):
        record = self.get(identifier, owner)
        if record.candidate is None or record.policy_revision != self.policy_revision:
            raise GuardError("CACHED_INSPECTION_UNAVAILABLE")
        clone = replace(record, request_id=str(uuid4()), version=version,
                        delivered=False, consumed=False)
        self.records[clone.request_id] = clone
        return clone

    async def evaluate(self, request: GuardInput, *, owner="operator"):
        self.expire()
        if self._inflight >= 4:
            raise GuardError("INSPECTION_BUSY", 503)
        self._inflight += 1
        try:
            return await self._evaluate(request, owner, self.clock())
        finally:
            self._inflight -= 1

    async def _evaluate(self, request, owner, started):
        # No API allows registering arbitrary outbound URLs or receivers.
        if request.destination_id not in {"local-preview", *self.receivers}:
            raise GuardError("DESTINATION_NOT_ENROLLED", 403)
        result = await self.scanner.scan(request.text)
        reasons = sorted({s.category.value for s in result.spans})
        cleaned = redact(request.text, result.spans, permit_overlap=True)
        decision, candidate = Decision.REVIEW, None
        if not result.complete:
            reasons.append("SCANNER_UNAVAILABLE")
        else:
            proposal = await self.inspector.inspect(cleaned, request.task)
            if proposal is None:
                reasons.append("MODEL_UNAVAILABLE")
            else:
                decision = proposal.decision
                try:
                    candidate = redact(cleaned, proposal.spans)
                except ValueError:
                    reasons.append("INVALID_SPANS")
                    decision, candidate = Decision.REVIEW, None
                if candidate is not None:
                    reasons.extend(s.category.value for s in proposal.spans)
                    if decision in {Decision.REVIEW, Decision.BLOCK, Decision.LOCAL_ONLY}:
                        candidate = None
                    elif result.spans or proposal.spans:
                        decision = Decision.SANITIZE
                    if candidate is not None:
                        final = await self.scanner.scan(candidate)
                        if not final.complete or final.spans:
                            decision, candidate = Decision.REVIEW, None
                            reasons.append("POLICY_BLOCK")
        record = Inspection(
            request_id=str(uuid4()), owner=owner, version=request.content_version,
            destination=request.destination_id, policy_revision=self.policy_revision,
            decision=decision, reasons=sorted(set(reasons)), deadline=started + self.ttl,
            expires_at=(datetime.now(timezone.utc) + timedelta(seconds=max(0, started + self.ttl - self.clock()))).isoformat(),
            candidate=candidate,
        )
        if len(self.records) >= 128:
            self.revoke(next(iter(self.records)))
        self.records[record.request_id] = record
        self.audit.add("guard.decision", decision.value, request_id=record.request_id,
                       content_version=record.version, reason_codes=record.reasons)
        return record

    async def deliver(self, identifier, *, owner, version, destination):
        async with self._release_lock:
            record = self.get(identifier, owner)
            if record.version != version or record.destination != destination:
                raise GuardError("STALE_CONTENT")
            if record.policy_revision != self.policy_revision:
                raise GuardError("STALE_POLICY")
            if record.consumed:
                raise GuardError("ALREADY_CONSUMED")
            if record.candidate is None or record.decision not in {Decision.ALLOW, Decision.SANITIZE}:
                raise GuardError("REQUEST_HELD", 403)
            receiver = self.receivers.get(destination)
            if receiver is None:
                raise GuardError("RECEIVER_NOT_IMPLEMENTED", 503)
            checked = await self.scanner.scan(record.candidate)
            # Recheck after an awaited scanner call; expiry/policy can change.
            if (self.clock() >= record.deadline or record.policy_revision != self.policy_revision
                    or self.records.get(identifier) is not record or record.candidate is None):
                self.revoke(identifier)
                raise GuardError("INSPECTION_EXPIRED_OR_CHANGED")
            if not checked.complete or checked.spans:
                raise GuardError("RELEASE_SCAN_HELD", 403)
            record.consumed = True
            content, record.candidate = record.candidate, None
            try:
                await asyncio.wait_for(receiver(content), timeout=10)
            except Exception:
                raise GuardError("DELIVERY_FAILED_NO_AUTOMATIC_RETRY", 503) from None
            record.delivered = True
            self.audit.add("guard.decision", "DELIVERED", request_id=identifier,
                           reason_codes=["DELIVERED"], content_version=version)
            return {"request_id": identifier, "delivered": True, "receipt_id": str(uuid4())}

    def close(self):
        for record in self.records.values():
            record.candidate = None
        self.records.clear()
