from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from devguard.repair.contracts import RepairError
from devguard.repair.mac1_binding import build_mac1_binding


def test_binding_uses_published_ports_and_stays_paused_without_readiness(
    spec, tmp_path
):
    queue, guard, loop = object(), object(), object()

    async def authenticate():
        return "operator"

    class FakeBridge:
        def __init__(self, actual_guard, actual_loop, error_factory):
            assert (actual_guard, actual_loop, error_factory) == (
                guard,
                loop,
                RepairError,
            )

    app = FastAPI()
    app.state.model_queue, app.state.guard, app.state.operator_auth = (
        queue,
        guard,
        authenticate,
    )
    service, router = build_mac1_binding(
        app,
        loop=loop,
        runtime_root=tmp_path / "runtime",
        project_specs=(spec,),
        event_sink=lambda event: None,
        guard_bridge_factory=FakeBridge,
    )
    assert service.model.client is queue
    assert service.model._bridge is None
    assert service.scheduler.paused
    app.include_router(router)
    with TestClient(app) as client:
        response = client.post("/api/v1/scheduler/enter-idle")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "INTEGRATION_NOT_READY"


def test_binding_rejects_missing_published_ports_without_inference(tmp_path):
    app = SimpleNamespace(state=SimpleNamespace())
    with pytest.raises(RepairError, match="INTEGRATION_PORTS_UNAVAILABLE"):
        build_mac1_binding(
            app,
            loop=object(),
            runtime_root=tmp_path,
            project_specs=(),
            event_sink=lambda event: None,
            guard_bridge_factory=lambda *args: None,
        )
