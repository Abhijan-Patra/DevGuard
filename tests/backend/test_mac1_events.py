import asyncio
import sqlite3

import pytest

from devguard.repair.contracts import RepairError
from devguard.repair.mac1_events import Mac1AuditEventBridge


class FakeAudit:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.received = []
        self.called_loop = None

    def add(self, kind, state):
        self.called_loop = asyncio.get_running_loop()
        self.received.append((kind, state))


def test_audit_bridge_serializes_on_app_loop_and_omits_raw_summaries(loop):
    audit = FakeAudit()
    try:
        bridge = Mac1AuditEventBridge(audit, loop)
        bridge(
            {
                "kind": "tool.completed",
                "state": "INVESTIGATING",
                "redacted_summary": "synthetic-private-text-must-never-be-forwarded",
            }
        )
        assert audit.received == [("tool.completed", "INVESTIGATING")]
        assert audit.called_loop is loop
        assert bridge.durable is False
    finally:
        audit.db.close()


def test_audit_bridge_detects_disk_database_without_exposing_path(loop, tmp_path):
    audit = FakeAudit(tmp_path / "audit.sqlite3")
    try:
        assert Mac1AuditEventBridge(audit, loop).durable is True
    finally:
        audit.db.close()


def test_audit_bridge_rejects_unconstrained_event_values(loop):
    audit = FakeAudit()
    try:
        bridge = Mac1AuditEventBridge(audit, loop)
        with pytest.raises(RepairError, match="AUDIT_EVENT_DENIED"):
            bridge({"kind": "synthetic-private-text", "state": "INVESTIGATING"})
        assert audit.received == []
    finally:
        audit.db.close()
