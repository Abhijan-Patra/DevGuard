"""Injectable repair service; Mac 1 supplies model/guard/auth and durable event storage."""

import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path

from devguard.agent.repair_agent import investigate
from devguard.monitor.scheduler import Scheduler

from .contracts import GuardPort, ModelPort, ProjectSpec, RepairError, Run, VerifierPort
from .patches import PatchStore, build_candidate
from .workspace import capture, read_source, revision

TERMINAL = {
    'ROLLED_BACK',
    "APPLIED",
    "UNRESOLVED",
    "BLOCKED",
    "CANCELED",
    "OBSOLETE",
    "REJECTED",
    "READY_FOR_REVIEW",
}


class RepairService:
    def __init__(
        self,
        *,
        model: ModelPort,
        guard: GuardPort,
        verifier: VerifierPort,
        runtime_root: Path,
        event_sink,
        readiness_check=None,
    ):
        self.model, self.guard, self.verifier = model, guard, verifier
        self.runtime_root = runtime_root.absolute()
        if not callable(event_sink):
            raise RepairError("AUDIT_UNAVAILABLE")
        self.event_sink = event_sink
        self.readiness_check = readiness_check or (lambda: {})
        self.projects: dict[str, ProjectSpec] = {}
        self.incidents: dict[str, dict] = {}
        self.runs: dict[str, Run] = {}
        self.patches = PatchStore()
        self.scheduler = Scheduler(self.execute)
        self._lock = threading.RLock()
        self._execution_lock = threading.Lock()
        self._dedupe: dict[tuple, str] = {}
        self._closed = False

    def _assert_open(self) -> None:
        if self._closed:
            raise RepairError("WORKER_CLOSED")

    def register_project(self, spec: ProjectSpec) -> None:
        """Trusted supervisor configuration only; not exposed as a model tool."""
        self._assert_open()
        if spec.project_id in self.projects:
            raise RepairError("PROJECT_ALREADY_REGISTERED")
        self.projects[spec.project_id] = spec

    def _project(self, project_id: str) -> ProjectSpec:
        try:
            return self.projects[project_id]
        except KeyError:
            raise RepairError("PROJECT_NOT_FOUND") from None

    def create_incident(
        self, project_id: str, signal: str, source_revision: str | None = None
    ) -> dict:
        with self._lock:
            self._assert_open()
            spec = self._project(project_id)
            if signal not in spec.test_names:
                raise RepairError("TEST_DENIED")
            current = revision(
                {n: read_source(spec.root, n) for n in spec.source_files}
            )
            if source_revision is not None and source_revision != current:
                raise RepairError("STALE_SOURCE")
            key = (project_id, signal, current)
            if key in self._dedupe:
                return dict(self.incidents[self._dedupe[key]])
            if len(self.incidents) >= 256:
                raise RepairError("CAPACITY_EXHAUSTED")
            incident_id = "incident-" + uuid.uuid4().hex
            item = {
                "incident_id": incident_id,
                "project_id": project_id,
                "signal": signal,
                "source_revision": current,
            }
            self.incidents[incident_id] = item
            self._dedupe[key] = incident_id
            return dict(item)

    def queue(self, incident_id: str) -> Run:
        with self._lock:
            self._assert_open()
            if incident_id not in self.incidents:
                raise RepairError("NOT_FOUND")
            for run in self.runs.values():
                if run.incident_id == incident_id and (
                    run.state not in TERMINAL or run.state == "READY_FOR_REVIEW"
                ):
                    return run
            if len(self.runs) >= 64:
                raise RepairError("CAPACITY_EXHAUSTED")
            item = self.incidents[incident_id]
            run = Run("run-" + uuid.uuid4().hex, incident_id, item["project_id"])
            self.runs[run.run_id] = run
            self.scheduler.enqueue(run.run_id)
            return run

    def get_run(self, run_id: str) -> Run:
        try:
            return self.runs[run_id]
        except KeyError:
            raise RepairError("NOT_FOUND") from None

    def _event(self, run: Run, kind: str, summary: str) -> None:
        event = {
            "schema_version": "1",
            "event_id": "event-" + uuid.uuid4().hex,
            "timestamp": datetime.now(UTC).isoformat(),
            "project_id": run.project_id,
            "kind": kind,
            "state": run.state,
            "severity": "info",
            "redacted_summary": summary,
            "evidence_refs": [],
            "run_id": run.run_id,
        }
        try:
            self.event_sink(event)
        except Exception:
            raise RepairError("AUDIT_UNAVAILABLE") from None

    def _state(self, run: Run, state: str) -> None:
        run.state = state
        self._event(run, "run.state", "Repair state: " + state)

    def _failed(self, run: Run, state: str, reason: str) -> None:
        run.reason_code = reason
        run.state = state
        if run.candidate_id:
            self.patches.reject(run.candidate_id)
        try:
            self._event(run, "run.state", "Repair state: " + state)
        except RepairError:
            run.reason_code = "AUDIT_UNAVAILABLE"
            run.state = "BLOCKED"
            self.scheduler.pause()

    def cancel(self, run_id: str) -> Run:
        run = self.get_run(run_id)
        run.cancel.set()
        if run.state == "READY_FOR_REVIEW" and run.candidate_id:
            self.patches.reject(run.candidate_id)
            self._state(run, "CANCELED")
        elif run.state not in TERMINAL:
            # Active Docker/model work observes the flag; terminal acknowledgement follows cleanup.
            if run.state in {"QUEUED", "WAITING_FOR_RESOURCES"}:
                self._state(run, "CANCELED")
        return run

    def pause(self) -> None:
        current = self.scheduler.pause()
        if current:
            self.cancel(current)

    def integration_ready(self) -> bool:
        """Trusted startup reports verified capabilities; HTTP cannot enable them."""
        try:
            flags = self.readiness_check()
            return all(
                flags.get(name) is True
                for name in (
                    "foreground_priority",
                    "durable_events",
                    "worker_lifecycle",
                    "trusted_verifier",
                )
            )
        except Exception:
            return False

    def enter_idle(self) -> None:
        self._assert_open()
        if not self.integration_ready():
            raise RepairError("INTEGRATION_NOT_READY")
        with self._lock:
            for run in self.runs.values():
                if run.state in {"QUEUED", "WAITING_FOR_RESOURCES"}:
                    self.scheduler.enqueue(run.run_id)
            self.scheduler.enter_idle()

    def shutdown(self, timeout: float = 30) -> bool:
        """Call via asyncio.to_thread before closing the app's guard/model/audit."""
        with self._lock:
            self._closed = True
            self.scheduler.pause()
            for run in self.runs.values():
                run.cancel.set()
        self.scheduler.join(timeout)
        if not self.scheduler.stopped():
            return False
        for run in self.runs.values():
            if run.state not in TERMINAL or run.state == "READY_FOR_REVIEW":
                run.state = "CANCELED"
        for candidate in self.patches.candidates.values():
            candidate.originals.clear()
            candidate.replacements.clear()
            if candidate.state == "READY_FOR_REVIEW":
                candidate.state = "REJECTED"
        return True

    def execute(self, run_id: str) -> None:
        with self._execution_lock:
            run = self.get_run(run_id)
            if run.state in TERMINAL:
                return
            run.reason_code = None
            snapshot = None
            try:
                if not self.integration_ready():
                    run.reason_code = "INTEGRATION_NOT_READY"
                    self._state(run, "WAITING_FOR_RESOURCES")
                    return
                if run.cancel.is_set():
                    raise RepairError("CANCELED")
                spec = self._project(run.project_id)
                item = self.incidents[run.incident_id]
                self._state(run, "SNAPSHOTTING")
                snapshot = capture(spec, self.runtime_root, self.guard)
                if snapshot.base_revision != item["source_revision"]:
                    raise RepairError("STALE_SOURCE")
                self._state(run, "INVESTIGATING")
                baseline = self.verifier.run(
                    snapshot.source, spec, item["signal"], run.cancel
                )
                run.baseline = baseline.status
                if baseline.status == "PASS":
                    run.reason_code = "NO_REPRODUCIBLE_FAILURE"
                    self._state(run, "UNRESOLVED")
                    return
                if baseline.status != "FAIL":
                    raise RepairError(
                        "CANCELED" if run.cancel.is_set() else "BASELINE_UNAVAILABLE"
                    )
                # Only approved, sanitized bytes reach the shared model queue.
                run.model = {
                    k: self.model.metadata[k]
                    for k in ("name", "digest")
                    if k in self.model.metadata
                }

                def completed(tool: str) -> None:
                    run.completed_tools.append(tool)
                    if tool == "propose_patch":
                        self._state(run, "PATCHING_SANDBOX")
                    self._event(
                        run, "tool.completed", "Completed permitted tool: " + tool
                    )

                changed = investigate(
                    model=self.model,
                    guard=self.guard,
                    verifier=self.verifier,
                    spec=spec,
                    snapshot=snapshot,
                    test_name=item["signal"],
                    baseline_output=baseline.output,
                    cancel=run.cancel,
                    on_tool=completed,
                )
                if not changed:
                    raise RepairError("NO_PATCH")
                self._state(run, "VERIFYING")
                verification = self.verifier.run(
                    snapshot.source, spec, item["signal"], run.cancel
                )
                run.verification = verification.status
                self._event(
                    run,
                    "verification.completed",
                    "Independent check: " + verification.status,
                )
                if run.cancel.is_set():
                    raise RepairError("CANCELED")
                if verification.status != "PASS":
                    raise RepairError("VERIFICATION_FAILED")
                candidate = build_candidate(snapshot, spec, run.run_id, self.guard)
                if run.cancel.is_set():
                    raise RepairError("CANCELED")
                self.patches.candidates[candidate.candidate_id] = candidate
                run.candidate_id = candidate.candidate_id
                self._state(run, "READY_FOR_REVIEW")
            except RepairError as error:
                state = (
                    "CANCELED"
                    if error.code == "CANCELED"
                    else "OBSOLETE"
                    if error.code == "STALE_SOURCE"
                    else "UNRESOLVED"
                    if error.code
                    in {
                        "NO_PATCH",
                        "VERIFICATION_FAILED",
                        "RUN_BUDGET_EXHAUSTED",
                        "TOOL_BUDGET_EXHAUSTED",
                        "PATCH_BUDGET_EXHAUSTED",
                    }
                    else "BLOCKED"
                )
                self._failed(run, state, error.code)
            except Exception:
                # No raw third-party exception/source/log text in public results.
                self._failed(run, "BLOCKED", "DEPENDENCY_ERROR")
            finally:
                if snapshot:
                    snapshot.close()

    def apply(self, candidate_id: str, **kwargs) -> dict:
        self._assert_open()
        candidate = self.patches.get(candidate_id)
        run = self.get_run(candidate.run_id)
        self.patch_view(candidate_id)
        self._event(run, "patch.state", "Operator requested candidate application")
        try:
            candidate = self.patches.apply(
                candidate_id, self._project(run.project_id), **kwargs
            )
        finally:
            if candidate.state == "OBSOLETE":
                self._state(run, "OBSOLETE")
        self._state(run, candidate.state)
        return candidate.view()

    def patch_view(self, candidate_id: str) -> dict:
        candidate = self.patches.get(candidate_id)
        if (
            self.guard.sanitize(candidate.diff, purpose="patch_export")
            != candidate.diff
        ):
            raise RepairError("PATCH_EXPORT_HELD")
        return candidate.view()

    def reject(self, candidate_id: str) -> dict:
        candidate = self.patches.reject(candidate_id)
        self._state(self.get_run(candidate.run_id), candidate.state)
        return candidate.view()

    def rollback(self, candidate_id, **kwargs):
        self._assert_open()
        candidate = self.patches.get(candidate_id)
        run = self.get_run(candidate.run_id)
        self._event(run, 'patch.state', 'Operator requested rollback')
        candidate = self.patches.rollback(candidate_id, self._project(run.project_id), **kwargs)
        self._state(run, candidate.state)
        return candidate.view()
