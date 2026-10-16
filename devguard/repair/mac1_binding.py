"""Exact published Mac 1 ports, without edits to Mac 1's startup/storage/schema files."""

from pathlib import Path

from devguard.agent.mac1_bridge import DeferredMac1ModelBridge
from devguard.api.repair_routes import create_repair_router

from .contracts import ProjectSpec, RepairError
from .mac1_events import Mac1AuditEventBridge
from .runner import DockerVerifier
from .service import RepairService


def build_mac1_binding(
    app,
    *,
    loop,
    runtime_root: Path,
    project_specs: tuple[ProjectSpec, ...],
    event_sink=None,
    readiness_check=None,
    verifier=None,
    guard_bridge_factory=None,
):
    """Return service/router for Mac 1 to mount and supervise once.

    event_sink must be a constrained adapter, never audit.add directly. Missing
    readiness flags keep execution paused. Construction performs no inference.
    """
    if guard_bridge_factory is None:
        from devguard.guard.repair_bridge import RepairGuardBridge

        guard_bridge_factory = RepairGuardBridge
    try:
        state = app.state
        queue, guard, auth = state.model_queue, state.guard, state.operator_auth
    except AttributeError:
        raise RepairError("INTEGRATION_PORTS_UNAVAILABLE") from None
    if event_sink is None:
        event_sink = Mac1AuditEventBridge(state.audit, loop)

    def ready():
        flags = dict(readiness_check() if readiness_check else {})
        if isinstance(event_sink, Mac1AuditEventBridge):
            flags["durable_events"] = (
                flags.get("durable_events") is True and event_sink.durable
            )
        return flags

    service = RepairService(
        model=DeferredMac1ModelBridge(queue, loop),
        guard=guard_bridge_factory(guard, loop, RepairError),
        verifier=verifier or DockerVerifier(),
        runtime_root=runtime_root,
        event_sink=event_sink,
        readiness_check=ready,
    )
    for spec in project_specs:
        service.register_project(spec)
    return service, create_repair_router(service, auth)
