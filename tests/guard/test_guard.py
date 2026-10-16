"""Boundary tests with explicitly injected test doubles, not inference evidence."""

import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
import httpx
import pytest

from devguard.api.app import create_app
from devguard.clipboard.native import UnsupportedClipboard
from devguard.config import Settings
from devguard.guard.engine import GuardEngine, GuardError
from devguard.guard.redaction import redact
from devguard.guard.scanner import CredentialScanner, ScanResult, baseline_spans
from devguard.schemas.guard import Category, Decision, GuardInput, ModelProposal, Span
from devguard.storage.audit import AuditStore

TOKEN = "test-only-operator-token-not-for-runtime-123"


def test_exported_operator_dependency_protects_an_injected_sync_router():
    adapter = "test-only-adapter-credential-not-for-runtime-321"
    app = create_app(Settings(TOKEN, adapter_token=adapter),
                     clipboard_adapter=UnsupportedClipboard())
    router = APIRouter()

    @router.post("/injected-operator-action")
    def action(principal=Depends(app.state.operator_auth)):
        return {"principal": principal}

    app.include_router(router)
    assert callable(app.state.model_queue.chat)
    with TestClient(app) as api:
        assert api.post("/injected-operator-action").status_code == 401
        assert api.post("/injected-operator-action", headers={
            "Authorization": "Bearer " + adapter}).status_code == 401
        response = api.post("/injected-operator-action", headers={
            "Authorization": "Bearer " + TOKEN})
        assert response.status_code == 200 and response.json() == {"principal": "operator"}


class TestScanner:
    __test__ = False
    available = True

    async def scan(self, text):
        return ScanResult(baseline_spans(text), complete=True)


class TestInspector:
    __test__ = False

    def __init__(self, proposal=None):
        self.proposal = proposal
        self.inputs = []

    async def inspect(self, text, task):
        self.inputs.append(text)
        return self.proposal


def request(text="benign code", **overrides):
    return GuardInput(**{"text": text, "task": "Debug login", "surface": "explicit_prompt",
                        "destination_id": "test-sink", "content_version": 1, **overrides})


def allowed():
    return ModelProposal(decision=Decision.ALLOW, spans=[])


def test_detected_values_never_reach_context_or_receiver_and_delivery_is_one_use():
    async def run():
        captured = []

        async def receiver(text):
            captured.append(text)

        inspector = TestInspector(allowed())
        audit = AuditStore()
        engine = GuardEngine(TestScanner(), inspector, audit, receivers={"test-sink": receiver})
        secret = "synthetic-only-credential-value-987654"
        record = await engine.evaluate(request(f"password={secret}; login error at line 42"))
        assert record.decision == Decision.SANITIZE
        assert secret not in inspector.inputs[0]
        assert "line 42" in record.candidate
        assert secret not in json.dumps(audit.events())
        with pytest.raises(GuardError, match="STALE_CONTENT"):
            await engine.deliver(record.request_id, owner="operator", version=2, destination="test-sink")
        assert captured == []
        result = await engine.deliver(record.request_id, owner="operator", version=1, destination="test-sink")
        assert result["delivered"] and len(captured) == 1 and secret not in captured[0]
        with pytest.raises(GuardError, match="ALREADY_CONSUMED"):
            await engine.deliver(record.request_id, owner="operator", version=1, destination="test-sink")
        assert len(captured) == 1
        audit.close()
    asyncio.run(run())


@pytest.mark.parametrize("proposal", [None, ModelProposal(decision=Decision.REVIEW, spans=[]),
                                         ModelProposal(decision=Decision.LOCAL_ONLY, spans=[]),
                                         ModelProposal(decision=Decision.BLOCK, spans=[])])
def test_missing_or_held_context_cannot_release(proposal):
    async def run():
        async def forbidden_receiver(text):
            pytest.fail("A held request reached the receiver")
        engine = GuardEngine(TestScanner(), TestInspector(proposal), AuditStore(),
                             receivers={"test-sink": forbidden_receiver})
        record = await engine.evaluate(request("Unknown private prose"))
        assert record.candidate is None
        with pytest.raises(GuardError, match="REQUEST_HELD"):
            await engine.deliver(record.request_id, owner="operator", version=1, destination="test-sink")
    asyncio.run(run())


def test_exact_spans_and_invalid_model_offsets_hold():
    async def run():
        proposal = ModelProposal(decision=Decision.SANITIZE,
                                 spans=[Span(start=0, end=999, category=Category.CONFIDENTIAL)])
        engine = GuardEngine(TestScanner(), TestInspector(proposal), AuditStore(), receivers={"test-sink": None})
        record = await engine.evaluate(request("short"))
        assert record.decision == Decision.REVIEW and record.candidate is None
        assert "INVALID_SPANS" in record.reasons
    asyncio.run(run())
    assert redact("🙂Alice error", [Span(start=1, end=6, category=Category.PERSONAL_DATA)]) == "🙂[REDACTED_1] error"
    with pytest.raises(ValueError):
        redact("abc", [Span(start=0, end=2, category=Category.CONFIDENTIAL),
                       Span(start=1, end=3, category=Category.CONFIDENTIAL)])


def test_owner_expiry_destination_and_policy_are_checked():
    async def run():
        now = [0]
        sink = []
        async def receiver(text):
            sink.append(text)
        engine = GuardEngine(TestScanner(), TestInspector(allowed()), AuditStore(),
                             receivers={"test-sink": receiver}, clock=lambda: now[0])
        with pytest.raises(GuardError, match="DESTINATION_NOT_ENROLLED"):
            await engine.evaluate(request(destination_id="arbitrary-host"))
        record = await engine.evaluate(request())
        with pytest.raises(GuardError, match="UNKNOWN"):
            engine.get(record.request_id, "another-owner")
        engine.policy_revision = "changed"
        with pytest.raises(GuardError, match="STALE_POLICY"):
            await engine.deliver(record.request_id, owner="operator", version=1, destination="test-sink")
        engine.policy_revision = "policy-v1"
        now[0] = 61
        with pytest.raises(GuardError, match="UNKNOWN"):
            await engine.deliver(record.request_id, owner="operator", version=1, destination="test-sink")
        assert sink == [] and record.candidate is None
    asyncio.run(run())


def test_revocation_during_release_scan_and_failed_receiver_cannot_retry():
    async def run():
        captured = []
        async def receiver(text):
            captured.append(text)
            raise RuntimeError("private receiver failure text")
        scanner = TestScanner()
        engine = GuardEngine(scanner, TestInspector(allowed()), AuditStore(),
                             receivers={"test-sink": receiver})
        record = await engine.evaluate(request())
        original = scanner.scan
        async def revoke(text):
            engine.revoke(record.request_id)
            return await original(text)
        scanner.scan = revoke
        with pytest.raises(GuardError, match="EXPIRED_OR_CHANGED"):
            await engine.deliver(record.request_id, owner="operator", version=1, destination="test-sink")
        assert captured == []
        scanner.scan = original
        next_record = await engine.evaluate(request())
        with pytest.raises(GuardError, match="NO_AUTOMATIC_RETRY"):
            await engine.deliver(next_record.request_id, owner="operator", version=1, destination="test-sink")
        with pytest.raises(GuardError, match="ALREADY_CONSUMED"):
            await engine.deliver(next_record.request_id, owner="operator", version=1, destination="test-sink")
        assert len(captured) == 1
    asyncio.run(run())


def test_api_rejects_oversize_and_invalid_input_without_echoing_secrets():
    fake_model = httpx.MockTransport(lambda request: httpx.Response(200, json={"models": []}))
    app = create_app(Settings(TOKEN), transport=fake_model, scanner=TestScanner(),
                     inspector=TestInspector(None), clipboard_adapter=UnsupportedClipboard())
    with TestClient(app) as api:
        headers = {"Authorization": f"Bearer {TOKEN}"}
        payload = request().model_dump()
        payload["content_version"] = "PRIVATE_INPUT_SHOULD_NOT_BE_ECHOED"
        response = api.post("/api/v1/guard/evaluate", json=payload, headers=headers)
        assert response.status_code == 400 and "PRIVATE_INPUT" not in response.text
        payload["content_version"] = 1
        payload["text"] = "A" * (193 * 1024)
        assert api.post("/api/v1/guard/evaluate", json=payload, headers=headers).status_code == 413
        assert api.post("/api/v1/guard/evaluate", json=request().model_dump()).status_code == 401
        payload = request(destination_id="local-preview").model_dump()
        response = api.post("/api/v1/guard/evaluate", json=payload, headers=headers)
        assert response.status_code == 200 and response.json()["decision"] == "REVIEW"
        assert response.json()["safe_preview"] is None


def test_actual_gitleaks_detects_provider_token_when_installed():
    scanner = CredentialScanner()
    if not scanner.available:
        pytest.skip("Gitleaks not installed; not counted as live scanner verification")
    async def run():
        import random, string
        synthetic = "gh" + "p_" + "".join(random.Random(728).choices(string.ascii_letters + string.digits, k=36))
        result = await scanner.scan("copied value: " + synthetic + " # gitleaks:allow")
        assert result.complete
        assert any(span.category == Category.CREDENTIAL for span in result.spans)
        assert synthetic not in redact("copied value: " + synthetic + " # gitleaks:allow", result.spans, permit_overlap=True)
    asyncio.run(run())


def test_adapter_scope_cannot_control_capture_or_deliver_another_owners_request():
    adapter_token = "scoped-test-adapter-token-not-real-987654321"
    app = create_app(Settings(TOKEN, adapter_token=adapter_token), scanner=TestScanner(),
                     inspector=TestInspector(allowed()), clipboard_adapter=UnsupportedClipboard())
    with TestClient(app) as api:
        headers = {"Authorization": f"Bearer {adapter_token}"}
        assert api.get("/api/v1/status", headers=headers).status_code == 401
        assert api.post("/api/v1/clipboard/enable", json={"consent": True}, headers=headers).status_code == 401
        payload = request(destination_id="local-preview").model_dump()
        response = api.post("/api/v1/guard/evaluate", json=payload, headers=headers)
        assert response.status_code == 200
        identifier = response.json()["request_id"]
        operator_headers = {"Authorization": f"Bearer {TOKEN}"}
        response = api.post(f"/api/v1/guard/requests/{identifier}/deliver",
                            json={"content_version": 1, "destination_id": "local-preview"},
                            headers=operator_headers)
        assert response.status_code == 404


def test_missing_scanner_and_final_rescan_failure_both_hold_delivery():
    async def run():
        class MissingScanner:
            available = False
            async def scan(self, text):
                return ScanResult([], complete=False)
        inspector = TestInspector(allowed())
        engine = GuardEngine(MissingScanner(), inspector, AuditStore(), receivers={"test-sink": None})
        record = await engine.evaluate(request())
        assert record.candidate is None and not inspector.inputs
        assert "SCANNER_UNAVAILABLE" in record.reasons
        class FailingFinalScanner(TestScanner):
            def __init__(self):
                self.count = 0
            async def scan(self, text):
                self.count += 1
                return ScanResult([], complete=self.count == 1)
        engine = GuardEngine(FailingFinalScanner(), TestInspector(allowed()), AuditStore(),
                             receivers={"test-sink": None})
        assert (await engine.evaluate(request())).candidate is None
    asyncio.run(run())


def test_concurrent_delivery_attempts_release_at_most_once():
    async def run():
        received = []
        async def receiver(text):
            await asyncio.sleep(0)
            received.append(text)
        engine = GuardEngine(TestScanner(), TestInspector(allowed()), AuditStore(),
                             receivers={"test-sink": receiver})
        record = await engine.evaluate(request())
        async def deliver():
            return await engine.deliver(record.request_id, owner="operator", version=1, destination="test-sink")
        results = await asyncio.gather(deliver(), deliver(), return_exceptions=True)
        assert len(received) == 1
        assert sum(isinstance(result, GuardError) for result in results) == 1
    asyncio.run(run())


def test_remote_operator_request_cannot_enable_native_clipboard():
    class MustNotRead:
        available = True
        def counter(self):
            pytest.fail("Remote request reached the native clipboard")
    app = create_app(Settings(TOKEN), scanner=TestScanner(), inspector=TestInspector(None),
                     clipboard_adapter=MustNotRead())
    with TestClient(app, client=("203.0.113.4", 12345)) as api:
        response = api.post("/api/v1/clipboard/enable", json={"consent": True},
                            headers={"Authorization": f"Bearer {TOKEN}"})
        assert response.status_code == 403
        assert api.get("/api/v1/clipboard/status", headers={"Authorization": f"Bearer {TOKEN}"}).json()["enabled"] is False
