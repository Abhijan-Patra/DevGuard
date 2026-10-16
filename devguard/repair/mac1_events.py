"""Constrained event-loop adapter to Mac 1's existing audit writer/schema."""

import asyncio
from concurrent.futures import TimeoutError as FutureTimeout

from .contracts import RepairError

KINDS = {"run.state", "tool.completed", "verification.completed", "patch.state"}
STATES = {
    "QUEUED",
    "WAITING_FOR_RESOURCES",
    "SNAPSHOTTING",
    "INVESTIGATING",
    "PATCHING_SANDBOX",
    "VERIFYING",
    "READY_FOR_REVIEW",
    "APPLIED",
    "UNRESOLVED",
    "BLOCKED",
    "CANCELED",
    "OBSOLETE",
    "REJECTED",
}


class Mac1AuditEventBridge:
    def __init__(self, audit, loop, timeout: float = 5):
        self.audit, self.loop, self.timeout = audit, loop, timeout
        # Call construction on the app loop. Expose only a boolean, never database paths.
        try:
            databases = audit.db.execute("PRAGMA database_list").fetchall()
            self.durable = any(row[1] == "main" and bool(row[2]) for row in databases)
        except (AttributeError, TypeError):
            self.durable = False

    def __call__(self, event: dict) -> None:
        kind, state = event.get("kind"), event.get("state")
        if kind not in KINDS or state not in STATES:
            raise RepairError("AUDIT_EVENT_DENIED")
        try:
            if asyncio.get_running_loop() is self.loop:
                raise RepairError("AUDIT_CALL_REQUIRES_WORKER_THREAD")
        except RuntimeError:
            pass
        if not self.loop.is_running():
            raise RepairError("AUDIT_UNAVAILABLE")

        async def add():
            # The current Mac 1 schema has no run_id/project/tool-name fields.
            # Do not smuggle them into request_id/reasons or accept arbitrary text.
            self.audit.add(kind, state)

        future = asyncio.run_coroutine_threadsafe(add(), self.loop)
        try:
            future.result(timeout=self.timeout)
        except FutureTimeout:
            future.cancel()
            raise RepairError("AUDIT_UNAVAILABLE") from None
        except Exception:
            raise RepairError("AUDIT_UNAVAILABLE") from None
