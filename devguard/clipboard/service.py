"""Versioned clipboard lifecycle with cancellation and bounded transient text."""

import asyncio
import contextlib
import time

from devguard.clipboard.native import ClipboardBusy
from devguard.guard.engine import GuardError
from devguard.schemas.guard import Category, Decision, GuardInput, MAX_TEXT_BYTES


class ClipboardService:
    def __init__(self, adapter, guard, audit, *, clock=time.monotonic, debounce=0.25):
        self.adapter, self.guard, self.audit = adapter, guard, audit
        self.clock, self.debounce = clock, debounce
        self.enabled = False
        self.state, self.summary = "OFF", "CAPTURE_DISABLED"
        self.version = 0
        self._generation = 0
        self._seen = None
        self._job = None
        self._request_id = None
        self._key = None
        self._task_context = None
        self._deadline = 0
        self._control_lock = asyncio.Lock()

    def status(self):
        self._expire()
        record = None
        if self._request_id:
            with contextlib.suppress(GuardError):
                record = self.guard.get(self._request_id, "clipboard")
        preview = record.candidate if record else None
        kind = ('SANITIZED' if record.decision == Decision.SANITIZE else 'APPROVED') if preview is not None else None
        display = preview
        if self.enabled and preview is None and self.state in {'SENSITIVE', 'REVIEW', 'ERROR'}:
            # Display-only marker, never an approved candidate or copy authority.
            # Mask the whole copy: partial scanner output may still contain
            # contextual facts when the model holds/fails. No original is kept.
            display = ('[INSPECTION_EXPIRED]' if self.summary == 'INSPECTION_EXPIRED' else
                       '[SENSITIVE_CONTENT_REMOVED]' if record and set(record.reasons).intersection(Category)
                       else '[CONTENT_WITHHELD]')
            kind = 'WITHHELD'
        return {
            "capture_host_id": "local-host", "supported": self.adapter.available,
            "enabled": self.enabled, "state": self.state, "content_version": self.version,
            "redacted_summary": self.summary,
            "safe_preview": preview,
            "display_preview": display, "preview_kind": kind,
            "finding_ids": [record.request_id] if record else [],
            "can_copy_cleaned": bool(record and record.candidate is not None and self.enabled),
        }

    def _expire(self):
        if self._request_id and self.clock() >= self._deadline:
            self.guard.revoke(self._request_id)
            self._request_id, self._key = None, None
            self.state, self.summary = "REVIEW", "INSPECTION_EXPIRED"

    async def _cancel_job(self):
        if self._job:
            self._job.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._job
            self._job = None

    async def enable(self, *, consent, task=None):
        async with self._control_lock:
            return await self._enable(consent=consent, task=task)

    async def _enable(self, *, consent, task=None):
        if consent is not True:
            raise GuardError("EXPLICIT_CAPTURE_CONSENT_REQUIRED", 403)
        if not self.adapter.available:
            raise GuardError("NATIVE_CAPTURE_UNSUPPORTED", 503)
        await self._disable()
        # Baseline counter only: do not collect the clipboard already present.
        try:
            self._seen = self.adapter.counter()
        except Exception:
            raise GuardError("NATIVE_CAPTURE_UNAVAILABLE", 503) from None
        self._task_context = task
        self.enabled = True
        self.state, self.summary = "CHECKING", "WAITING_FOR_NEW_COPY"
        return self.status()

    async def disable(self):
        async with self._control_lock:
            return await self._disable()

    async def _disable(self):
        self.enabled = False
        self._generation += 1
        await self._cancel_job()
        if self._request_id:
            self.guard.revoke(self._request_id)
        self._request_id, self._key, self._task_context = None, None, None
        self._seen = None
        self.state, self.summary = "OFF", "CAPTURE_DISABLED"
        return self.status()

    async def poll_once(self):
        self.guard.expire()
        self._expire()
        if not self.enabled:
            return
        try:
            current = self.adapter.counter()
            if current == self._seen:
                return
            previous_id, previous_key = self._request_id, self._key
            self._seen = current
            self.version += 1
            version, generation = self.version, self._generation
            self.state, self.summary = "CHECKING", "INSPECTION_PENDING"
            self._request_id, self._key = None, None
            await self._cancel_job()
            if not self.enabled or generation != self._generation:
                return
            try:
                kind, text = self.adapter.read_text(MAX_TEXT_BYTES)
            except ClipboardBusy:
                if previous_id:
                    self.guard.revoke(previous_id)
                self._seen = None
                self.summary = "CLIPBOARD_BUSY_RETRYING"
                return
            if self.adapter.counter() != current:
                if previous_id:
                    self.guard.revoke(previous_id)
                self._seen = None
                return
            if kind != "TEXT" or text is None:
                if previous_id:
                    self.guard.revoke(previous_id)
                self.state, self.summary = "SKIPPED", "NON_TEXT_OR_OVERSIZE"
                return
            if not text.strip():
                if previous_id:
                    self.guard.revoke(previous_id)
                self.state, self.summary = "SKIPPED", "EMPTY_TEXT"
                return
            if len(text.encode()) > MAX_TEXT_BYTES:
                if previous_id:
                    self.guard.revoke(previous_id)
                self.state, self.summary = "SKIPPED", "NON_TEXT_OR_OVERSIZE"
                return
            key = self.guard.fingerprint(text, task=self._task_context)
            if key == previous_key and previous_id:
                try:
                    clone = self.guard.clone_for_version(previous_id, owner="clipboard", version=version)
                    self.guard.revoke(previous_id)
                    self._accept(clone, key, generation, version)
                    return
                except GuardError:
                    pass
            if previous_id:
                self.guard.revoke(previous_id)
            self._deadline = self.clock() + 60
            self._job = asyncio.create_task(self._analyse(text, key, generation, version))
        except asyncio.CancelledError:
            raise
        except Exception:
            await self.disable()
            self.state, self.summary = "ERROR", "CAPTURE_CHECK_FAILED"

    async def _analyse(self, text, key, generation, version):
        record = None
        try:
            await asyncio.sleep(self.debounce)
            request = GuardInput(text=text, task=self._task_context, surface="clipboard",
                                 destination_id="local-preview", content_version=version)
            record = await asyncio.wait_for(self.guard.evaluate(request, owner="clipboard"), timeout=25)
            self._accept(record, key, generation, version)
        except asyncio.CancelledError:
            if record:
                self.guard.revoke(record.request_id)
            raise
        except Exception:
            if record:
                self.guard.revoke(record.request_id)
            if self.enabled and generation == self._generation and version == self.version:
                self.state, self.summary = "REVIEW", "INSPECTION_UNAVAILABLE"

    def _accept(self, record, key, generation, version):
        if not self.enabled or generation != self._generation or version != self.version:
            self.guard.revoke(record.request_id)
            return
        self._request_id = record.request_id
        self._key = key
        self._deadline = min(record.deadline, self._deadline or self.clock() + 60)
        if record.candidate is None:
            self.state = "SENSITIVE" if record.decision == Decision.BLOCK else "REVIEW"
        else:
            self.state = "SENSITIVE" if record.decision == Decision.SANITIZE else "CLEAR_FOR_CAPTURE_SCOPE"
        self.summary = ", ".join(record.reasons) or record.decision.value
        self.audit.add("clipboard.decision", self.state, content_version=self.version,
                       request_id=record.request_id, reason_codes=record.reasons)

    async def copy_cleaned(self, expected_version):
        async with self._control_lock:
            return await self._copy_cleaned(expected_version)

    async def _copy_cleaned(self, expected_version):
        self._expire()
        if not self.enabled or expected_version != self.version or not self._request_id:
            raise GuardError("STALE_CLIPBOARD")
        record = self.guard.get(self._request_id, "clipboard")
        if record.policy_revision != self.guard.policy_revision:
            raise GuardError("STALE_POLICY")
        if record.candidate is None:
            raise GuardError("CLIPBOARD_INSPECTION_HELD", 403)
        try:
            new_counter = self.adapter.write_text(self._seen, record.candidate)
        except Exception:
            raise GuardError("CLIPBOARD_WRITE_FAILED", 503) from None
        if new_counter is None:
            raise GuardError("STALE_CLIPBOARD")
        self.guard.revoke(self._request_id)
        self._request_id, self._key = None, None
        self._seen = new_counter
        self.version += 1
        self.state, self.summary = "CLEAR_FOR_CAPTURE_SCOPE", "CLEANED_COPY_WRITTEN"
        return {"copied": True, "content_version": self.version}

    async def run(self):
        try:
            while True:
                await self.poll_once()
                await asyncio.sleep(0.75)
        finally:
            await self.disable()
