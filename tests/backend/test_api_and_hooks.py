"""API authorization and hook-process contract tests, not live Codex coverage evidence."""

import asyncio
import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from devguard.api.repair_routes import create_repair_router
from integrations.codex import hook

from .test_repair import run_once, service_for


@pytest.fixture
def api(spec, tmp_path):
    service, _ = service_for(spec, tmp_path)

    def operator(authorization: str | None = Header(default=None)):
        if authorization != "Bearer synthetic-operator-unit-test-token":
            raise HTTPException(status_code=403, detail="Operator scope required")

    app = FastAPI()
    app.include_router(create_repair_router(service, operator))
    with TestClient(app) as client:
        yield client, service


AUTH = {"Authorization": "Bearer synthetic-operator-unit-test-token"}


def test_all_repair_routes_require_operator_scope(api):
    client, _ = api
    assert (
        client.post(
            "/api/v1/incidents", json={"project_id": "demo", "signal": "cart"}
        ).status_code
        == 403
    )
    assert client.get("/api/v1/runs/absent").status_code == 403
    assert client.post("/api/v1/scheduler/enter-idle").status_code == 403


def test_incident_and_repair_route_contract(api):
    client, service = api
    incident = client.post(
        "/api/v1/incidents", headers=AUTH, json={"project_id": "demo", "signal": "cart"}
    )
    assert incident.status_code == 200
    queued = client.post(
        f"/api/v1/incidents/{incident.json()['incident_id']}/investigate", headers=AUTH
    )
    assert queued.status_code == 202
    run_id = queued.json()["run_id"]
    service.execute(run_id)
    result = client.get(f"/api/v1/runs/{run_id}", headers=AUTH)
    assert result.json()["state"] == "READY_FOR_REVIEW"
    patch = client.get(f"/api/v1/patches/{result.json()['candidate_id']}", headers=AUTH)
    assert patch.status_code == 200
    assert patch.json()["verification"] == "PASS"


def test_api_does_not_reflect_invalid_private_input(api):
    client, _ = api
    response = client.post(
        "/api/v1/incidents",
        headers=AUTH,
        json={
            "project_id": "demo",
            "signal": "cart",
            "secret": "synthetic-private-value",
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert "synthetic-private-value" not in response.text


def test_api_rejects_oversized_bodies(api):
    client, _ = api
    response = client.post("/api/v1/incidents", headers=AUTH, content=b"x" * 9000)
    assert response.status_code == 413


def test_api_stale_apply_returns_409(api, spec):
    client, service = api
    run = run_once(service)
    patch = service.patches.get(run.candidate_id)
    (spec.root / "cart.py").write_text("# newer work\n")
    response = client.post(
        f"/api/v1/patches/{patch.candidate_id}/apply",
        headers=AUTH,
        json={
            "approved": True,
            "expected_candidate_hash": patch.candidate_hash,
            "expected_base_revision": patch.base_revision,
            "idempotency_key": "operator-review",
        },
    )
    assert response.status_code == 409
    assert (spec.root / "cart.py").read_text() == "# newer work\n"


def test_api_apply_does_not_block_the_shared_model_guard_event_loop(api):
    client, service = api
    run = run_once(service)
    patch = service.patches.get(run.candidate_id)

    class ThreadAwareGuard:
        def sanitize(self, text, *, purpose):
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return text
            raise AssertionError(
                "Synchronous guard bridge must run outside the application loop"
            )

    service.guard = ThreadAwareGuard()
    response = client.post(
        f"/api/v1/patches/{patch.candidate_id}/apply",
        headers=AUTH,
        json={
            "approved": True,
            "expected_candidate_hash": patch.candidate_hash,
            "expected_base_revision": patch.base_revision,
            "idempotency_key": "thread-safe-review",
        },
    )
    assert response.status_code == 200
    assert response.json()["state"] == "APPLIED"


def test_router_cannot_be_created_without_auth_dependency(api):
    _, service = api
    with pytest.raises(ValueError):
        create_repair_router(service, None)


@pytest.mark.parametrize("decision", ["SANITIZE", "BLOCK", "LOCAL_ONLY", "REVIEW"])
def test_hook_holds_every_non_allow_decision(decision):
    output = hook.handle(
        {"hook_event_name": "UserPromptSubmit", "prompt": "synthetic text"},
        lambda text, surface: False,
    )
    assert output["decision"] == "block"
    assert "synthetic text" not in json.dumps(output)


def test_hook_allows_unchanged_approved_prompt():
    seen = []

    def evaluate(text, surface):
        seen.append((text, surface))
        return True

    assert (
        hook.handle(
            {"hook_event_name": "UserPromptSubmit", "prompt": "benign input"}, evaluate
        )
        == {}
    )
    assert seen == [("benign input", "explicit_prompt")]


@pytest.mark.parametrize("tool", ["Bash", "apply_patch", "mcp__other__read", "unknown"])
def test_initial_pretool_adapter_denies_unmanaged_execution(tool):
    def forbidden(*args):
        raise AssertionError("Classifier opinion must not grant unrestricted execution")

    output = hook.handle(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": tool,
            "tool_input": {"command": "synthetic command"},
        },
        forbidden,
    )
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_hook_blocks_tool_result_without_echo():
    output = hook.handle(
        {"hook_event_name": "PostToolUse", "tool_response": "synthetic-private"},
        lambda text, surface: False,
    )
    assert output["decision"] == "block"
    assert "synthetic-private" not in json.dumps(output)


def test_hook_process_missing_guard_configuration_blocks_without_echo():
    path = Path(__file__).resolve().parents[2] / "integrations/codex/hook.py"
    process = subprocess.run(
        [sys.executable, str(path)],
        input=json.dumps(
            {
                "hook_event_name": "UserPromptSubmit",
                "prompt": "synthetic-private-stdin",
            }
        ),
        capture_output=True,
        text=True,
        env={"PATH": os.environ.get("PATH", "")},
        timeout=5,
        check=False,
    )
    assert process.returncode == 0
    assert json.loads(process.stdout)["decision"] == "block"
    assert "synthetic-private-stdin" not in process.stdout + process.stderr


def test_hook_process_malformed_stdin_uses_blocking_exit_code():
    path = Path(__file__).resolve().parents[2] / "integrations/codex/hook.py"
    process = subprocess.run(
        [sys.executable, str(path)],
        input="not-json-synthetic",
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert process.returncode == 2
    assert "not-json-synthetic" not in process.stdout + process.stderr


def test_hook_rejects_remote_guard_before_sending():
    assert not hook.evaluate(
        "synthetic",
        "explicit_prompt",
        config={
            "base_url": "https://outside.example.invalid/api/v1",
            "token": "synthetic",
            "project_id": "demo",
            "destination_id": "codex",
        },
    )


@pytest.mark.parametrize(
    ("changed_field", "value", "expected"),
    [
        (None, None, True),
        ("decision", "SANITIZE", False),
        ("status", "CHECKING", False),
        ("content_version", -1, False),
        ("destination_id", "another-client", False),
        ("expires_at", "2020-01-01T00:00:00Z", False),
    ],
)
def test_hook_validates_bound_guard_response(
    monkeypatch, changed_field, value, expected
):
    class Reply:
        def __init__(self, data):
            self.data = data

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, limit):
            return json.dumps(self.data).encode()

    class Opener:
        def open(self, request, timeout):
            sent = json.loads(request.data)
            result = {
                "decision": "ALLOW",
                "status": "READY",
                "request_id": "synthetic-request",
                "policy_revision": "unit-test-policy",
                "safe_preview": json.loads(request.data)['text'],
                "content_version": sent["content_version"],
                "destination_id": sent["destination_id"],
                "expires_at": (datetime.now(UTC) + timedelta(seconds=60)).isoformat(),
            }
            if changed_field:
                result[changed_field] = value
            return Reply(result)

    monkeypatch.setattr(hook.urllib.request, "build_opener", lambda *args: Opener())
    assert (
        hook.evaluate(
            "synthetic",
            "explicit_prompt",
            config={
                "base_url": "http://127.0.0.1:8000/api/v1",
                "token": "synthetic-adapter-token",
                "project_id": "demo",
                "destination_id": "codex",
            },
        )
        is expected
    )
