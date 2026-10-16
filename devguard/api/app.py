"""Authenticated local guard, explicit clipboard controls and integration ports."""

from contextlib import asynccontextmanager
import asyncio
import contextlib
import secrets

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from devguard.config import Settings
from devguard.models.ollama import OllamaClient
from devguard.api.guard_routes import guard_router
from devguard.clipboard.native import native_clipboard
from devguard.clipboard.service import ClipboardService
from devguard.guard.context import ContextInspector
from devguard.guard.engine import GuardEngine, GuardError
from devguard.guard.scanner import CredentialScanner
from devguard.storage.audit import AuditStore
from devguard.api.body_limit import BodyLimitMiddleware


CAPABILITIES = (
    "privacy_gate", "clipboard_capture", "codex_adapter", "backend_repair",
)


class Unauthorized(Exception):
    pass


def create_app(settings: Settings, *, transport=None, scanner=None, inspector=None,
               clipboard_adapter=None, receivers=None, audit=None):
    model = OllamaClient(settings, transport=transport)
    audit = audit or AuditStore()
    scanner = scanner or CredentialScanner()
    guard = GuardEngine(scanner, inspector or ContextInspector(model), audit, receivers=receivers)
    clipboard = ClipboardService(clipboard_adapter or native_clipboard(), guard, audit)

    @asynccontextmanager
    async def lifespan(app):
        watcher = asyncio.create_task(clipboard.run())
        try:
            yield
        finally:
            watcher.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watcher
            guard.close()
            audit.close()
            await model.close()

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

    async def authenticate(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if credentials is None or not secrets.compare_digest(
            credentials.credentials, settings.session_token
        ):
            raise Unauthorized()
        return "operator"

    async def authenticate_guard(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if credentials is None:
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

    app.include_router(guard_router(authenticate, authenticate_guard, guard, clipboard, audit))

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
            "repair_implemented": False,
        }

    @app.get("/api/v1/coverage", dependencies=[Depends(authenticate)])
    async def coverage():
        return {"capabilities": [
            {"capability": name,
             "status": "PARTIAL" if name in {"privacy_gate", "clipboard_capture"} else "UNIMPLEMENTED",
             "verified_at": None}
            for name in CAPABILITIES
        ]}

    return app
