"""Control-flow/security unit tests use declared fake model/verifier ports, not model results."""

import json
from dataclasses import replace
from pathlib import Path
from threading import Event

import pytest

from devguard.monitor.files import SavedFileMonitor
from devguard.repair.contracts import SELECTED_MODEL, RepairError
from devguard.repair.contracts import TestResult as CheckResult
from devguard.repair.patches import replace_in_snapshot
from devguard.repair.runner import DockerVerifier
from devguard.repair.service import RepairService
from devguard.repair.workspace import capture, digest, safe_relative


class FakeGuard:
    def __init__(self, redact=False):
        self.calls = []
        self.redact = redact

    def sanitize(self, text, *, purpose):
        self.calls.append(purpose)
        return "REDACTED" if self.redact and purpose == "patch_export" else text


class FakeVerifier:
    def __init__(self, *statuses):
        self.statuses = iter(statuses)
        self.calls = 0

    def run(self, source, spec, name, cancel):
        self.calls += 1
        return CheckResult(next(self.statuses), "declared synthetic verifier output")


class FakeModel:
    metadata = {
        "name": SELECTED_MODEL,
        "digest": "unit-test-only-not-an-installed-model",
    }

    def __init__(self, *actions):
        self.actions = iter(actions)
        self.messages = []

    def next_action(self, messages, tools):
        self.messages.append(list(messages))
        return next(self.actions)


def fake_actions():
    return [
        {"tool": "read_allowed_file", "arguments": {"path": "cart.py"}},
        {
            "tool": "propose_patch",
            "arguments": {
                "path": "cart.py",
                "expected_hash": digest(b"VALUE = 1\n"),
                "content": "VALUE = 2\n",
            },
        },
        {"tool": "finish", "arguments": {}},
    ]


def service_for(spec, tmp_path, *, model=None, guard=None, verifier=None):
    events = []
    service = RepairService(
        model=model or FakeModel(*fake_actions()),
        guard=guard or FakeGuard(),
        verifier=verifier or FakeVerifier("FAIL", "PASS"),
        runtime_root=tmp_path / "private-runtime",
        event_sink=events.append,
        readiness_check=lambda: {
            "foreground_priority": True,
            "durable_events": True,
            "worker_lifecycle": True,
            "trusted_verifier": True,
        },
    )
    service.register_project(spec)
    return service, events


def run_once(service):
    incident = service.create_incident("demo", "cart")
    run = service.queue(incident["incident_id"])
    service.execute(run.run_id)
    return run


@pytest.mark.parametrize(
    "name",
    [
        "../secret",
        "/tmp/secret",
        "a/../../secret",
        ".env",
        "src/.env.local",
        "trusted_tests/test.py",
        ".git/config",
        "a\\secret",
        "a//b",
        "key.pem",
    ],
)
def test_protected_paths_rejected(name):
    with pytest.raises(RepairError):
        safe_relative(name)


def test_snapshot_preserves_saved_uncommitted_bytes(spec, tmp_path):
    import os
    (spec.root / "cart.py").write_text("# saved edit\nVALUE = 7\n", newline="\n")
    snapshot = capture(spec, tmp_path / "runtime")
    try:
        assert (snapshot.source / "cart.py").read_text() == "# saved edit\nVALUE = 7\n"
        assert not (snapshot.source / "trusted_tests").exists()
        if os.name != "nt":
            assert snapshot.directory.stat().st_mode & 0o777 == 0o700
    finally:
        snapshot.close()


def test_symlink_read_rejected(spec, tmp_path):
    (spec.root / "cart.py").unlink()
    (spec.root / "cart.py").symlink_to(spec.root / "main.py")
    with pytest.raises(RepairError, match="SYMLINK_DENIED"):
        capture(spec, tmp_path / "runtime")


def test_hardlink_read_rejected(spec, tmp_path):
    (spec.root / "link.py").hardlink_to(spec.root / "cart.py")
    with pytest.raises(RepairError, match="FILE_TYPE_DENIED"):
        capture(spec, tmp_path / "runtime")


def test_sandbox_cannot_edit_verifier_or_nonwritable_dependency(spec, tmp_path):
    snapshot = capture(spec, tmp_path / "runtime")
    try:
        for name in ("../checks/test_cart.py", "main.py", "trusted_tests/test_cart.py"):
            with pytest.raises(RepairError, match="WRITE_DENIED"):
                replace_in_snapshot(snapshot, spec, name, "bad", digest(b""))
        assert (
            spec.trusted_tests / "test_cart.py"
        ).read_text() == "# protected verifier fixture\n"
    finally:
        snapshot.close()


def test_candidate_leaves_originals_untouched_then_applies_idempotently(spec, tmp_path):
    service, events = service_for(spec, tmp_path)
    run = run_once(service)
    assert run.state == "READY_FOR_REVIEW"
    assert (spec.root / "cart.py").read_text() == "VALUE = 1\n"
    candidate = service.patches.get(run.candidate_id)
    kwargs = dict(
        expected_hash=candidate.candidate_hash,
        expected_base=candidate.base_revision,
        idempotency_key="operator-request-1",
        approved=True,
    )
    result = service.apply(candidate.candidate_id, **kwargs)
    assert result["state"] == "APPLIED"
    assert (spec.root / "cart.py").read_text() == "VALUE = 2\n"
    assert service.apply(candidate.candidate_id, **kwargs)["state"] == "APPLIED"
    with pytest.raises(RepairError, match="PATCH_ALREADY_APPLIED"):
        service.apply(
            candidate.candidate_id, **{**kwargs, "idempotency_key": "another"}
        )
    assert not list((tmp_path / "private-runtime").iterdir())
    assert "VALUE" not in json.dumps(events)


@pytest.mark.parametrize("changed", ["cart.py", "main.py"])
def test_stale_candidate_preserves_newer_edits(spec, tmp_path, changed):
    service, _ = service_for(spec, tmp_path)
    run = run_once(service)
    candidate = service.patches.get(run.candidate_id)
    (spec.root / changed).write_text("# developer's new edit\n")
    with pytest.raises(RepairError, match="STALE_SOURCE"):
        service.apply(
            candidate.candidate_id,
            expected_hash=candidate.candidate_hash,
            expected_base=candidate.base_revision,
            idempotency_key="review",
            approved=True,
        )
    assert run.state == "OBSOLETE"
    assert (spec.root / changed).read_text() == "# developer's new edit\n"


def test_operator_and_hash_required(spec, tmp_path):
    service, _ = service_for(spec, tmp_path)
    run = run_once(service)
    candidate = service.patches.get(run.candidate_id)
    for kwargs, code in [
        (
            {"approved": False, "expected_hash": candidate.candidate_hash},
            "OPERATOR_APPROVAL_REQUIRED",
        ),
        ({"approved": True, "expected_hash": "b" * 64}, "CANDIDATE_CONFLICT"),
    ]:
        with pytest.raises(RepairError, match=code):
            service.apply(
                candidate.candidate_id,
                expected_base=candidate.base_revision,
                idempotency_key="review",
                **kwargs,
            )
    assert (spec.root / "cart.py").read_text() == "VALUE = 1\n"


def test_guard_blocks_exported_candidate(spec, tmp_path):
    service, _ = service_for(spec, tmp_path, guard=FakeGuard(redact=True))
    run = run_once(service)
    assert run.state == "BLOCKED"
    assert run.reason_code == "PATCH_EXPORT_HELD"
    assert not service.patches.candidates
    assert (spec.root / "cart.py").read_text() == "VALUE = 1\n"


@pytest.mark.parametrize(
    ("statuses", "state", "code"),
    [
        (("PASS",), "UNRESOLVED", "NO_REPRODUCIBLE_FAILURE"),
        (("ERROR",), "BLOCKED", "BASELINE_UNAVAILABLE"),
        (("FAIL", "FAIL"), "UNRESOLVED", "VERIFICATION_FAILED"),
    ],
)
def test_no_false_success(spec, tmp_path, statuses, state, code):
    service, _ = service_for(spec, tmp_path, verifier=FakeVerifier(*statuses))
    run = run_once(service)
    assert (run.state, run.reason_code) == (state, code)
    assert run.candidate_id is None


def test_cancel_queued_run_never_calls_verifier(spec, tmp_path):
    verifier = FakeVerifier("FAIL")
    service, _ = service_for(spec, tmp_path, verifier=verifier)
    item = service.create_incident("demo", "cart")
    run = service.queue(item["incident_id"])
    service.cancel(run.run_id)
    service.execute(run.run_id)
    assert run.state == "CANCELED"
    assert verifier.calls == 0


def test_cancel_ready_candidate_prevents_apply(spec, tmp_path):
    service, _ = service_for(spec, tmp_path)
    run = run_once(service)
    service.cancel(run.run_id)
    assert run.state == "CANCELED"
    assert service.patches.get(run.candidate_id).state == "REJECTED"


def test_revision_and_incident_queue_dedup(spec, tmp_path):
    service, _ = service_for(spec, tmp_path)
    one = service.create_incident("demo", "cart")
    two = service.create_incident("demo", "cart")
    assert one == two
    assert service.queue(one["incident_id"]) is service.queue(two["incident_id"])
    (spec.root / "cart.py").write_text("VALUE = 9\n")
    with pytest.raises(RepairError, match="STALE_SOURCE"):
        service.create_incident("demo", "cart", one["source_revision"])


def test_manual_idle_executes_and_pause_stops_new_work(spec, tmp_path):
    service, _ = service_for(spec, tmp_path)
    incident = service.create_incident("demo", "cart")
    run = service.queue(incident["incident_id"])
    assert run.state == "QUEUED"
    service.scheduler.enter_idle()
    service.scheduler.join()
    assert run.state == "READY_FOR_REVIEW"
    service.pause()
    assert service.scheduler.paused


def test_invalid_model_action_fails_closed(spec, tmp_path):
    model = FakeModel({"tool": "run_shell", "arguments": {"command": "anything"}})
    service, _ = service_for(spec, tmp_path, model=model)
    run = run_once(service)
    assert (run.state, run.reason_code) == ("BLOCKED", "INVALID_MODEL_ACTION")


def test_model_error_is_not_reflected(spec, tmp_path):
    class BrokenModel(FakeModel):
        def next_action(self, messages, tools):
            raise RuntimeError("synthetic-private-content")

    service, events = service_for(spec, tmp_path, model=BrokenModel())
    run = run_once(service)
    assert run.reason_code == "DEPENDENCY_ERROR"
    assert "synthetic-private-content" not in json.dumps([run.view(), events])


def test_guard_sanitizes_all_model_bound_tool_evidence(spec, tmp_path):
    guard = FakeGuard()
    service, _ = service_for(spec, tmp_path, guard=guard)
    run_once(service)
    assert guard.calls.count("test_evidence") == 1
    assert guard.calls.count("tool_result") == 2
    assert "patch_export" in guard.calls


def test_tool_step_budget_is_enforced(spec, tmp_path):
    model = FakeModel(*[{"tool": "list_allowed_files", "arguments": {}}] * 9)
    service, _ = service_for(spec, tmp_path, model=model)
    run = run_once(service)
    assert run.reason_code == "TOOL_BUDGET_EXHAUSTED"
    assert len(model.messages) == 8


def test_docker_command_restricts_execution_and_has_no_shell(spec, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/local/bin/docker")
    verifier = DockerVerifier()
    command = verifier.command(Path("/approved"), spec, "cart", "devguard-test")
    for flag in [
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--user=65534:65534",
        "--pull=never",
        "--env=PYTHONPYCACHEPREFIX=/tmp/pycache",
        "--tb=line",
    ]:
        assert flag in command
    assert all("docker.sock" not in arg for arg in command)
    assert "sh" not in command
    assert command[-1] == "/checks/test_cart.py"
    with pytest.raises(RepairError, match="IMAGE_NOT_PINNED"):
        verifier.command(
            Path("/approved"), replace(spec, image_id="python:latest"), "cart", "x"
        )
    with pytest.raises(RepairError, match="TEST_DENIED"):
        verifier.command(Path("/approved"), spec, "../other", "x")


def test_missing_docker_does_not_execute_on_host(spec, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(RepairError, match="DOCKER_UNAVAILABLE"):
        DockerVerifier().run(spec.root, spec, "cart", Event())


def test_file_changes_are_debounced(spec):
    seen = []
    monitor = SavedFileMonitor(
        spec, "cart", lambda *args: seen.append(args), debounce_seconds=2
    )
    monitor.tick(now=0)
    (spec.root / "cart.py").write_text("VALUE = 22\n")
    monitor.tick(now=1)
    monitor.tick(now=2)
    assert not seen
    monitor.tick(now=3.1)
    monitor.tick(now=4)
    assert seen == [("demo", "cart")]


def test_source_guard_holds_before_snapshot_or_verifier(spec, tmp_path):
    class HoldingGuard:
        def sanitize(self, text, *, purpose):
            return "REDACTED"

    verifier = FakeVerifier("FAIL")
    service, _ = service_for(spec, tmp_path, guard=HoldingGuard(), verifier=verifier)
    run = run_once(service)
    assert (run.state, run.reason_code) == ("BLOCKED", "SOURCE_REQUIRES_SANITIZATION")
    assert verifier.calls == 0
    assert not (tmp_path / "private-runtime").exists()


@pytest.mark.parametrize("ready", [True, False])
def test_audit_failure_blocks_and_pauses_without_raw_error(spec, tmp_path, ready):
    service, _ = service_for(spec, tmp_path)
    if not ready:
        service.readiness_check = lambda: {}

    def broken_sink(event):
        raise OSError("synthetic-private-storage-detail")

    service.event_sink = broken_sink
    run = run_once(service)
    assert (run.state, run.reason_code) == ("BLOCKED", "AUDIT_UNAVAILABLE")
    assert service.scheduler.paused
    assert not (tmp_path / "private-runtime").exists()


def test_missing_integration_gates_hold_jobs_and_scheduler(spec, tmp_path):
    service, _ = service_for(spec, tmp_path)
    service.readiness_check = lambda: {"foreground_priority": True}
    incident = service.create_incident("demo", "cart")
    run = service.queue(incident["incident_id"])
    with pytest.raises(RepairError, match="INTEGRATION_NOT_READY"):
        service.enter_idle()
    service.execute(run.run_id)
    assert run.state == "WAITING_FOR_RESOURCES"
    assert run.reason_code == "INTEGRATION_NOT_READY"
    assert service.scheduler.paused
    assert not (tmp_path / "private-runtime").exists()


def test_shutdown_cancels_pending_work_and_prevents_reopening(spec, tmp_path):
    service, _ = service_for(spec, tmp_path)
    incident = service.create_incident("demo", "cart")
    run = service.queue(incident["incident_id"])
    assert service.shutdown(timeout=1)
    assert service.scheduler.paused
    assert run.state == "CANCELED"
    with pytest.raises(RepairError, match="WORKER_CLOSED"):
        service.enter_idle()
    with pytest.raises(RepairError, match="WORKER_CLOSED"):
        service.queue(incident["incident_id"])
