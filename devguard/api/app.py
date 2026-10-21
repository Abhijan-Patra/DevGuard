"""Authenticated local guard, explicit clipboard controls and integration ports."""

from contextlib import asynccontextmanager
import asyncio
import contextlib
import secrets

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from devguard.config import Settings
from devguard.models.ollama import OllamaClient
from devguard.api.guard_routes import guard_router
from devguard.clipboard.native import native_clipboard
from devguard.clipboard.service import ClipboardService
from devguard.guard.context import ContextInspector
from devguard.guard.engine import GuardEngine, GuardError
from devguard.guard.scanner import CredentialScanner
from devguard.storage.audit import AuditStore, AuditUnavailable
from devguard.api.body_limit import BodyLimitMiddleware
from devguard.api.repair_integration import RepairRuntime, integration_router
from devguard.api.repair_routes import create_repair_router
from devguard.api.web_session import BrowserSessions
from devguard.api.workspace_routes import workspace_router, client_router, LocalComposer
from devguard.monitor.supervisor import MonitorSupervisor


CAPABILITIES = (
    "privacy_gate", "clipboard_capture", "codex_adapter", "claude_adapter", "managed_client", "backend_repair",
    'managed_source', 'saved_file_monitor', 'quiet_time_scheduler', 'reviewed_rollback',
)


class Unauthorized(Exception):
    pass


def create_app(settings: Settings, *, transport=None, scanner=None, inspector=None,
               clipboard_adapter=None, receivers=None, audit=None, repair_factory=None,
               browser_workspace=False):
    model = OllamaClient(settings, transport=transport)
    audit = audit or AuditStore()
    scanner = scanner or CredentialScanner()
    composer = LocalComposer()
    guard = GuardEngine(scanner, inspector or ContextInspector(model), audit,
                        receivers={'local-composer': composer.receive, **(receivers or {})})
    clipboard = ClipboardService(clipboard_adapter or native_clipboard(), guard, audit)
    repair = RepairRuntime(repair_factory)
    supervisor = MonitorSupervisor(repair, model)
    repair.supervisor = supervisor
    sessions = BrowserSessions(browser_workspace)

    @asynccontextmanager
    async def lifespan(app):
        watcher = asyncio.create_task(clipboard.run())
        monitor_task = asyncio.create_task(supervisor.run())
        repair.lifecycle_managed = True
        try:
            await repair.initialize(app)
            yield
        finally:
            monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await monitor_task
            watcher.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watcher
            repair.pause()
            stopped = await repair.join()
            await model.close()
            # A bounded drain normally stops before resources close. If a model
            # call was still active, closing it cancels inference, then require
            # worker acknowledgement before clearing guard/audit resources.
            if not stopped and not await repair.join():
                raise RuntimeError('WORKER_SHUTDOWN_TIMEOUT')
            guard.close()
            composer.clear()
            sessions.sessions.clear()
            audit.close()

    app = FastAPI(title="DevGuard", version="0.1.0", lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(BodyLimitMiddleware)
    bearer = HTTPBearer(auto_error=False)
    app.state.guard, app.state.clipboard, app.state.audit = guard, clipboard, audit

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, error):
        # FastAPI's default validation errors may echo the original private input.
        return JSONResponse(status_code=400, content={"error": {
            "code": "INVALID_REQUEST", "message": "Request does not match the bounded schema"
        }})

    @app.exception_handler(GuardError)
    async def guard_error(request, error):
        return JSONResponse(status_code=error.status, content={"error": {
            "code": error.code, "message": "Action held; inspect current local status"
        }})

    async def authenticate(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if credentials is None and sessions.authorized(request):
            return 'operator'
        if credentials is None or not secrets.compare_digest(
            credentials.credentials, settings.session_token
        ):
            raise Unauthorized()
        return "operator"

    async def authenticate_guard(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if credentials is None:
            if sessions.authorized(request):
                return 'operator'
            raise Unauthorized()
        if secrets.compare_digest(credentials.credentials, settings.session_token):
            return "operator"
        if settings.adapter_token and secrets.compare_digest(credentials.credentials, settings.adapter_token):
            return "adapter"
        raise Unauthorized()

    # Trusted integration points for Mac 2's injectable worker/router. These
    # are Python objects, not exposed operator/model authority over HTTP.
    app.state.model_queue = model
    app.state.operator_auth = authenticate
    app.state.adapter_auth = authenticate_guard
    app.state.repair_event_sink = audit.add_repair
    app.state.repair = repair
    app.state.supervisor = supervisor

    @app.exception_handler(AuditUnavailable)
    async def audit_unavailable(request, error):
        return JSONResponse(status_code=503, content={"error": {
            "code": "AUDIT_UNAVAILABLE", "message": "Action held; local audit storage is unavailable"
        }})

    app.include_router(guard_router(authenticate, authenticate_guard, guard, clipboard, audit))
    app.include_router(create_repair_router(repair, authenticate))
    app.include_router(integration_router(repair, app, authenticate))
    app.include_router(sessions.router())
    app.include_router(workspace_router(app, authenticate, supervisor, composer))
    app.include_router(client_router(app, authenticate_guard))

    @app.middleware('http')
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self'")
        return response

    assets = Path(__file__).resolve().parents[1] / 'web'
    app.mount('/assets', StaticFiles(directory=assets), name='workspace-assets')

    @app.get('/')
    @app.get('/app')
    def workspace_page():
        return FileResponse(assets / 'index.html')

    @app.exception_handler(Unauthorized)
    async def unauthorized(request: Request, error: Unauthorized):
        return JSONResponse(status_code=401, content={"error": {
            "code": "UNAUTHORIZED", "message": "A valid local session token is required"
        }}, headers={"WWW-Authenticate": "Bearer"})

    @app.get("/health")
    @app.get("/api/v1/health")
    async def health():
        status = await model.inspect()
        return {"service_ready": True, "model_ready": status["model_ready"]}

    @app.get("/api/v1/status", dependencies=[Depends(authenticate)])
    async def status():
        return {
            "phase": "GUARD_AND_CLIPBOARD_IMPLEMENTATION",
            "runtime": await model.inspect(),
            "inference_queue": model.queue.status(),
            "clipboard": {**clipboard.status(), "implemented": True},
            "guard_implemented": True,
            "credential_scanner_available": scanner.available,
            "audit": {"durable": audit.durable, "retention_events": 5000},
            "repair_implemented": True,
            "repair": repair.status(),
            "monitoring": supervisor.status(),
        }

    @app.get("/api/v1/coverage", dependencies=[Depends(authenticate)])
    async def coverage():
        return {"capabilities": [
            {"capability": name,
             "status": "PARTIAL",
             "limitations": {
                 "privacy_gate": "Real Gemma calibration cases and local delivery checks passed; earlier failures retained. General unseen accuracy remains unverified.",
                 "clipboard_capture": "Opt-in macOS text only; starts OFF; recorded native checks exist; current capture is explicit and version-bound.",
                 "backend_repair": "Routes wired; trusted configuration, pinned model/image and Docker engine required; starts paused.",
                 "codex_adapter": "Recorded bundled CLI 0.163.0-alpha.10.2 prompt/tool/MCP boundary trials passed with real Gemma and a synthetic loopback coding provider. Requires explicit profile setup and native hook trust; not universal or cloud-delivery proof.",
                 "claude_adapter": "Recorded Claude Code 2.1.119 prompt and managed MCP trials passed with real Gemma and a synthetic loopback coding provider. Signed-in cloud account workflow and desktop variants remain unverified.",
                 "managed_client": "Two scoped stdio tools list/read registered source. Server scans and checks source before returning approved one-use bytes; no shell, writes, root selection or apply authority.",
                 'managed_source': 'Registered source only; guard-bound final source checks and actual local-composer delivery. No unrestricted tools or external client interception.',
                 'saved_file_monitor': 'Opt-in debounced manifest monitoring, supervised by app lifespan. Starts OFF; changes queue but never grant execution permission.',
                 'quiet_time_scheduler': 'Opt-in foreground-queue quiet time, not OS idle detection. Manual pause disables it. Active inference is not preempted.',
                 'reviewed_rollback': 'Explicit approval and full applied-source hash checks; refuses concurrent edits. Session-only, single-file atomic replacement.',
             }[name],
             "verified_at": None}
            for name in CAPABILITIES
        ]}

    return app
