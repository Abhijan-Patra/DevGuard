"""Actual cross-thread wiring; injected classification is not Gemma evidence."""

import asyncio

import pytest

from devguard.guard.engine import GuardEngine
from devguard.guard.repair_bridge import RepairGuardBridge
from devguard.schemas.guard import Decision, ModelProposal
from devguard.storage.audit import AuditStore
from tests.guard.test_guard import TestInspector, TestScanner


class RepairError(Exception):
    pass


def test_repair_scope_uses_sensitivity_checks_without_conversational_relevance():
    async def run():
        class InspectSource:
            def __init__(self):
                self.seen = []
            async def inspect(self, text, task):
                self.seen.append((text, task))
                return ModelProposal(decision=Decision.ALLOW, spans=[])
        inspector = InspectSource()
        audit = AuditStore()
        guard = GuardEngine(TestScanner(), inspector, audit)
        bridge = RepairGuardBridge(guard, asyncio.get_running_loop(), RepairError)
        source = 'def total(values):\n    return sum(values)\n'
        assert await asyncio.to_thread(bridge.sanitize, source, purpose='snapshot_source') == source
        secret = 'synthetic-only-credential-459834905'
        cleaned = await asyncio.to_thread(bridge.sanitize, 'password=' + secret, purpose='tool_result')
        assert secret not in cleaned
        assert len(inspector.seen) == 2
        assert all(task is None for _, task in inspector.seen)
        assert secret not in inspector.seen[1][0]
        assert not guard.records
        audit.close()
    asyncio.run(run())


def test_worker_bridge_returns_cleaned_text_and_clears_transient_record():
    async def run():
        audit = AuditStore()
        guard = GuardEngine(TestScanner(), TestInspector(ModelProposal(
            decision=Decision.ALLOW, spans=[])), audit)
        bridge = RepairGuardBridge(guard, asyncio.get_running_loop(), RepairError)
        secret = "synthetic-only-credential-342984832"
        cleaned = await asyncio.to_thread(bridge.sanitize, "password=" + secret,
                                          purpose="test_evidence")
        assert secret not in cleaned and "[CREDENTIAL_1]" in cleaned
        assert not guard.records
        audit.close()
    asyncio.run(run())


def test_worker_bridge_holds_missing_model_and_rejects_invalid_call_scope():
    async def run():
        audit = AuditStore()
        guard = GuardEngine(TestScanner(), TestInspector(None), audit)
        bridge = RepairGuardBridge(guard, asyncio.get_running_loop(), RepairError)
        with pytest.raises(RepairError, match="REQUIRES_WORKER_THREAD"):
            bridge.sanitize("benign", purpose="snapshot_source")
        with pytest.raises(RepairError, match="GUARD_PURPOSE_DENIED"):
            await asyncio.to_thread(bridge.sanitize, "benign", purpose="arbitrary")
        with pytest.raises(RepairError, match="GUARD_HELD"):
            await asyncio.to_thread(bridge.sanitize, "benign", purpose="snapshot_source")
        assert not guard.records
        audit.close()
    asyncio.run(run())


def test_worker_bridge_timeout_cancels_inspection():
    async def run():
        stopped = asyncio.Event()
        class SlowGuard:
            async def evaluate(self, *args, **kwargs):
                try:
                    await asyncio.sleep(60)
                finally:
                    stopped.set()
        bridge = RepairGuardBridge(SlowGuard(), asyncio.get_running_loop(), RepairError,
                                  timeout=0.01)
        with pytest.raises(RepairError, match="GUARD_TIMEOUT"):
            await asyncio.to_thread(bridge.sanitize, "benign", purpose="tool_result")
        await asyncio.wait_for(stopped.wait(), timeout=1)
    asyncio.run(run())
