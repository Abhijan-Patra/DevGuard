"""Real operator/API trial on a disposable copy of the public cart demo only."""

import argparse
import asyncio
import hashlib
import json
import re
import secrets
import sys
import tempfile
import time
from contextlib import asynccontextmanager
from dataclasses import replace
from pathlib import Path
from subprocess import run

from fastapi.testclient import TestClient

from demo.backend.config import demo_project
from devguard.api.app import create_app
from devguard.clipboard.native import UnsupportedClipboard
from devguard.config import Settings
from devguard.repair.contracts import RepairError
from devguard.repair.mac1_binding import build_mac1_binding
from devguard.repair.runner import DockerVerifier
from devguard.repair.service import TERMINAL
from devguard.repair.workspace import read_source
from devguard.storage.audit import AuditStore


def source_hashes(root: Path, names: tuple[str, ...]) -> dict[str, str]:
    return {name: hashlib.sha256(read_source(root, name)).hexdigest() for name in names}


def exercise_api(
    client,
    token: str,
    *,
    timeout: float = 300,
    exercise_apply: bool = False,
    on_state=None,
):
    """Uses only operator routes; never installs a fake model or bypasses a hold."""
    headers = {"Authorization": "Bearer " + token}

    def request(method, path, body=None, expected=200):
        response = client.request(method, "/api/v1" + path, headers=headers, json=body)
        data = response.json()
        if response.status_code != expected:
            error = data.get("error", {})
            raise RepairError(error.get("code", "TRIAL_API_UNAVAILABLE"))
        return data

    incident = request(
        "POST", "/incidents", {"project_id": "demo-cart", "signal": "cart"}
    )
    queued = request(
        "POST", "/incidents/" + incident["incident_id"] + "/investigate", {}, 202
    )
    run_id = queued["run_id"]
    request("POST", "/scheduler/enter-idle", {})
    deadline = time.monotonic() + timeout
    previous = None
    while True:
        state = request("GET", "/runs/" + run_id)
        marker = (state["state"], tuple(state.get("completed_tools", ())))
        if marker != previous and on_state:
            on_state(
                {
                    "state": state["state"],
                    "completed_tools": state.get("completed_tools", []),
                    "reason_code": state.get("reason_code"),
                }
            )
        previous = marker
        if state["state"] in TERMINAL:
            break
        if time.monotonic() >= deadline:
            request("POST", "/runs/" + run_id + "/cancel", {})
            raise RepairError("TRIAL_TIMEOUT")
        time.sleep(0.2)
    report = {"run": state, "applied_to_original_repository": False}
    if state["state"] == "READY_FOR_REVIEW":
        try:
            patch = request("GET", "/patches/" + state["candidate_id"])
        except RepairError as error:
            request("POST", "/scheduler/pause", {})
            report["candidate_export"] = {"status": "HELD", "reason_code": error.code}
            return report
        report["candidate"] = patch
        if exercise_apply:
            body = {
                "approved": True,
                "expected_candidate_hash": patch["candidate_hash"],
                "expected_base_revision": patch["base_revision"],
                "idempotency_key": "disposable-trial-" + secrets.token_hex(12),
            }
            path = "/patches/" + state["candidate_id"] + "/apply"
            applied = request("POST", path, body)
            repeated = request("POST", path, body)
            report["disposable_apply"] = {
                "state": applied["state"],
                "idempotent_repeat": repeated["state"] == "APPLIED",
            }
    request("POST", "/scheduler/pause", {})
    return report


def trial(
    image_id: str,
    *,
    docker: str = "docker",
    exercise_apply: bool = False,
    on_state=None,
) -> dict:
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        raise RepairError("IMAGE_NOT_PINNED")
    repository = Path(__file__).resolve().parents[2]
    spec = demo_project(repository, image_id)
    before = source_hashes(spec.root, spec.source_files)
    test_names = tuple("test_" + name + ".py" for name in spec.test_names)
    tests_before = source_hashes(spec.trusted_tests, test_names)
    verifier = DockerVerifier(docker)
    if not verifier.docker:
        raise RepairError("DOCKER_UNAVAILABLE")
    inspected = run(
        [verifier.docker, "image", "inspect", image_id, "--format", "{{.Id}}"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if inspected.returncode or inspected.stdout.strip() != image_id:
        raise RepairError("VERIFIER_UNAVAILABLE")
    with tempfile.TemporaryDirectory(prefix="devguard-public-cart-trial-") as temporary:
        private = Path(temporary).resolve()
        private.chmod(0o700)
        # Only the declared public demo manifest is copied, never a user-selected repo.
        source = private / "source"
        source.mkdir(mode=0o755)  # The containing private directory remains 0700.
        for name in spec.source_files:
            (source / name).write_bytes(read_source(spec.root, name))
        disposable = replace(spec, root=source)
        audit_path = private / "audit" / "metadata.sqlite3"
        audit = AuditStore(audit_path)
        token = secrets.token_urlsafe(32)
        observations = []
        services = []

        async def factory(app):
            model = app.state.model_queue
            runtime = await model.inspect()
            if not runtime.get("model_ready") or not runtime.get("model_digest"):
                raise RepairError("MODEL_NOT_PINNED")
            original_evaluate = app.state.guard.evaluate

            async def observe(request, **kwargs):
                record = await original_evaluate(request, **kwargs)
                observations.append(
                    {
                        "surface": request.surface,
                        "input_bytes": len(request.text.encode()),
                        "decision": record.decision.value,
                        "reason_codes": record.reasons,
                    }
                )
                return record

            app.state.guard.evaluate = observe
            app.state.trial_runtime = runtime
            service, _ = build_mac1_binding(
                app,
                loop=asyncio.get_running_loop(),
                runtime_root=private / "snapshots",
                project_specs=(disposable,),
                verifier=verifier,
                readiness_check=lambda: {
                    "foreground_priority": model.queue.PRIORITIES
                    == {"foreground": 0, "background": 10},
                    "durable_events": audit.durable,
                    # This operator harness owns and verifies shutdown below.
                    "worker_lifecycle": True,
                    "trusted_verifier": inspected.stdout.strip() == image_id,
                },
            )
            services.append(service)
            return service

        app = create_app(
            Settings(session_token=token),
            audit=audit,
            clipboard_adapter=UnsupportedClipboard(),
            repair_factory=factory,
        )
        original_lifespan = app.router.lifespan_context
        stopped = []

        @asynccontextmanager
        async def supervised(application):
            async with original_lifespan(application):
                try:
                    yield
                finally:
                    for service in services:
                        ok = await asyncio.to_thread(service.shutdown, 30)
                        if not ok:
                            await app.state.model_queue.close()
                            ok = await asyncio.to_thread(service.shutdown, 30)
                        stopped.append(ok)

        app.router.lifespan_context = supervised
        with TestClient(app) as client:
            if not app.state.repair.status()["available"]:
                raise RepairError(app.state.repair.status()["reason_code"])
            report = exercise_api(
                client, token, exercise_apply=exercise_apply, on_state=on_state
            )
            report["model_runtime"] = app.state.trial_runtime
            report["audit_event_count"] = len(audit.events()["events"])
            report["guard_checks"] = observations
            if report.get("disposable_apply"):
                from threading import Event

                result = verifier.run(disposable.root, disposable, "cart", Event())
                report["post_apply_verification"] = result.status
        report["worker_stopped"] = bool(stopped) and all(stopped)
        report["original_source_unchanged"] = before == source_hashes(
            spec.root, spec.source_files
        )
        report["trusted_tests_unchanged"] = tests_before == source_hashes(
            spec.trusted_tests, test_names
        )
        reopened = AuditStore(audit_path)
        try:
            report["audit_reopen_event_count"] = len(reopened.events()["events"])
        finally:
            reopened.close()
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--docker", default="docker")
    parser.add_argument(
        "--exercise-apply",
        action="store_true",
        help="Exercise approved/idempotent apply only on the disposable public demo copy",
    )
    args = parser.parse_args()
    try:
        report = trial(
            args.image_id,
            docker=args.docker,
            exercise_apply=args.exercise_apply,
            on_state=lambda state: print(
                json.dumps({"progress": state}), file=sys.stderr, flush=True
            ),
        )
        print(json.dumps(report, indent=2))
        succeeded = (
            report["run"]["state"] == "READY_FOR_REVIEW"
            and "candidate" in report
            and report["worker_stopped"]
            and report["original_source_unchanged"]
            and report["trusted_tests_unchanged"]
        )
        if args.exercise_apply:
            succeeded = succeeded and report.get("post_apply_verification") == "PASS"
        return 0 if succeeded else 2
    except Exception as error:
        code = (
            error.code if isinstance(error, RepairError) else "TRIAL_DEPENDENCY_ERROR"
        )
        print(json.dumps({"status": "BLOCKED", "reason_code": code}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
