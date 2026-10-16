"""Synchronous worker port onto the existing event-loop-owned privacy guard."""

import asyncio
from concurrent.futures import TimeoutError as FutureTimeout

from devguard.schemas.guard import Decision, GuardInput


class RepairGuardBridge:
    """Call from a worker thread; inject Mac 2's fixed-code RepairError class."""

    PURPOSES = {
        "snapshot_source": "file_read",
        "test_evidence": "tool_result",
        "tool_result": "tool_result",
        "patch_export": "tool_result",
    }

    def __init__(self, guard, loop, error_factory, *, timeout=25):
        self.guard, self.loop, self.error_factory = guard, loop, error_factory
        self.timeout = timeout

    def sanitize(self, text: str, *, purpose: str) -> str:
        try:
            if asyncio.get_running_loop() is self.loop:
                raise self.error_factory("GUARD_CALL_REQUIRES_WORKER_THREAD")
        except RuntimeError:
            pass
        if purpose not in self.PURPOSES:
            raise self.error_factory("GUARD_PURPOSE_DENIED")
        if not self.loop.is_running():
            raise self.error_factory("GUARD_LOOP_UNAVAILABLE")

        async def call():
            record = await self.guard.evaluate(GuardInput(
                task="Inspect backend repair evidence; preserve source and debugging facts",
                surface=self.PURPOSES[purpose], destination_id="local-preview",
                content_version=0, text=text,
            ), owner="repair-worker")
            try:
                current = self.guard.get(record.request_id, "repair-worker")
                if (current.policy_revision != self.guard.policy_revision
                        or current.decision not in {Decision.ALLOW, Decision.SANITIZE}
                        or current.candidate is None):
                    raise self.error_factory("GUARD_HELD")
                return current.candidate
            finally:
                # Do not retain an additional preview/history of worker evidence.
                self.guard.revoke(record.request_id)

        coroutine = call()
        try:
            future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        except Exception:
            coroutine.close()
            raise self.error_factory("GUARD_LOOP_UNAVAILABLE") from None
        try:
            return future.result(timeout=self.timeout)
        except FutureTimeout:
            future.cancel()
            raise self.error_factory("GUARD_TIMEOUT") from None
        except Exception:
            raise self.error_factory("GUARD_HELD") from None
