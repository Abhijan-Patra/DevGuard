"""Actual Mac 1 app/guard/auth binding; run after combining the two branches."""

import asyncio
import inspect
from contextlib import asynccontextmanager
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

mac1 = pytest.importorskip(
    "devguard.api.app",
    reason="Combine Mac 1 and Mac 2 branches for real app binding checks",
)

from devguard.config import Settings  # noqa: E402
from devguard.repair.mac1_binding import build_mac1_binding  # noqa: E402


def test_real_app_binding_preserves_auth_and_holds_unready_repairs(spec, tmp_path):
    operator_token = "declared-synthetic-operator-token-for-tests"
    adapter_token = "declared-synthetic-adapter-token-for-tests"

    def handler(request):
        if request.url.path == "/api/version":
            return httpx.Response(200, json={"version": "synthetic-test-runtime"})
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": []})
        raise AssertionError("No inference may run before model/readiness gates pass")

    async def factory(application):
        service, router = build_mac1_binding(
            application,
            loop=asyncio.get_running_loop(),
            runtime_root=tmp_path / "runtime",
            project_specs=(spec,),
        )
        application.state.repair_service = service
        return service, router

    async def mounted_factory(application):
        service, _ = await factory(application)
        return service

    supports_factory = "repair_factory" in inspect.signature(mac1.create_app).parameters
    options = {"repair_factory": mounted_factory} if supports_factory else {}
    app = mac1.create_app(
        Settings(session_token=operator_token, adapter_token=adapter_token),
        transport=httpx.MockTransport(handler),
        scanner=SimpleNamespace(available=True),
        inspector=object(),
        clipboard_adapter=SimpleNamespace(available=False),
        **options,
    )
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application):
        async with original_lifespan(application):
            if not supports_factory:
                service, router = await factory(application)
                app.include_router(router)
            service = app.state.repair_service
            try:
                yield
            finally:
                assert await asyncio.to_thread(service.shutdown, 2)

    app.router.lifespan_context = lifespan
    with TestClient(app) as client:
        assert client.get("/health").json()["model_ready"] is False
        assert client.post("/api/v1/scheduler/enter-idle").status_code == 401
        assert (
            client.post(
                "/api/v1/scheduler/enter-idle",
                headers={
                    "Authorization": "Bearer " + adapter_token,
                },
            ).status_code
            == 401
        )
        held = client.post(
            "/api/v1/scheduler/enter-idle",
            headers={
                "Authorization": "Bearer " + operator_token,
            },
        )
        assert held.status_code == 503
        assert held.json()["error"]["code"] == "INTEGRATION_NOT_READY"
        assert app.state.repair_service.scheduler.paused
        assert app.state.repair_service.model._bridge is None
    assert not (tmp_path / "runtime").exists()
