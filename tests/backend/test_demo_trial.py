"""Operator demo API control flow; declared fake model/verifier ports only."""

from dataclasses import replace

import pytest
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from devguard.api.repair_routes import create_repair_router
from devguard.repair.demo_trial import exercise_api
from tests.backend.test_repair import FakeGuard, service_for

TOKEN = "declared-demo-trial-unit-operator-token"


@pytest.fixture
def trial_api(spec, tmp_path):
    service, _ = service_for(replace(spec, project_id="demo-cart"), tmp_path)

    def authenticate(authorization: str | None = Header(default=None)):
        if authorization != "Bearer " + TOKEN:
            raise HTTPException(status_code=401)
        return "operator"

    app = FastAPI()
    app.include_router(create_repair_router(service, authenticate))
    with TestClient(app) as client:
        yield client, service
    assert service.shutdown(2)


def test_trial_queues_through_api_and_returns_candidate_without_applying(
    trial_api, spec
):
    client, service = trial_api
    report = exercise_api(client, TOKEN, timeout=3)
    assert report["run"]["state"] == "READY_FOR_REVIEW"
    assert report["candidate"]["verification"] == "PASS"
    assert "disposable_apply" not in report
    assert (spec.root / "cart.py").read_text() == "VALUE = 1\n"
    assert service.scheduler.paused


def test_explicit_disposable_apply_exercises_operator_hashes_and_idempotency(
    trial_api, spec
):
    client, _ = trial_api
    report = exercise_api(client, TOKEN, timeout=3, exercise_apply=True)
    assert report["disposable_apply"] == {"state": "APPLIED", "idempotent_repeat": True}
    assert report["applied_to_original_repository"] is False
    assert (spec.root / "cart.py").read_text() == "VALUE = 2\n"


def test_trial_preserves_held_source_and_does_not_substitute_an_answer(trial_api, spec):
    client, service = trial_api

    class SourceHold(FakeGuard):
        def sanitize(self, text, *, purpose):
            return "changed-source" if purpose == "snapshot_source" else text

    service.guard = SourceHold()
    report = exercise_api(client, TOKEN, timeout=3, exercise_apply=True)
    assert report["run"]["state"] == "BLOCKED"
    assert report["run"]["reason_code"] == "SOURCE_REQUIRES_SANITIZATION"
    assert "candidate" not in report
    assert "disposable_apply" not in report
    assert (spec.root / "cart.py").read_text() == "VALUE = 1\n"


def test_later_export_hold_is_reported_without_claiming_a_delivered_patch(trial_api):
    client, service = trial_api

    class LaterHold(FakeGuard):
        exports = 0

        def sanitize(self, text, *, purpose):
            if purpose == "patch_export":
                self.exports += 1
                if self.exports > 1:
                    return "held-export"
            return text

    service.guard = LaterHold()
    report = exercise_api(client, TOKEN, timeout=3)
    assert report["run"]["state"] == "READY_FOR_REVIEW"
    assert report["candidate_export"] == {
        "status": "HELD",
        "reason_code": "PATCH_EXPORT_HELD",
    }
    assert "candidate" not in report
    assert service.scheduler.paused


def test_trial_proves_queued_cancel_then_still_runs_genuine_investigation(trial_api):
    client, service = trial_api
    report = exercise_api(client, TOKEN, timeout=3, queued_cancel=True)
    assert report["queued_cancellation"] == {
        "state": "CANCELED",
        "candidate_created": False,
    }
    assert report["run"]["state"] == "READY_FOR_REVIEW"
    assert len(service.runs) == 2
    assert len(service.model.messages) == 3


def test_trial_stale_check_keeps_concurrent_operator_edit(trial_api, spec):
    client, _ = trial_api

    def edit():
        path = spec.root / "cart.py"
        path.write_text("# new concurrent operator edit\n")
        return path.read_text(), path.read_text

    report = exercise_api(
        client, TOKEN, timeout=3, exercise_stale=True, stale_edit=edit
    )
    assert report["stale_apply"] == {
        "http_status": 409,
        "reason_code": "STALE_SOURCE",
        "concurrent_edit_preserved": True,
        "run_after_attempt": "OBSOLETE",
    }
    assert (spec.root / "cart.py").read_text() == "# new concurrent operator edit\n"
