"""First authenticated readiness API; no capture or release side effects."""

from contextlib import asynccontextmanager
import secrets

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from devguard.config import Settings
from devguard.models.ollama import OllamaClient


CAPABILITIES = (
    "privacy_gate", "clipboard_capture", "codex_adapter", "backend_repair",
)


class Unauthorized(Exception):
    pass


def create_app(settings: Settings, *, transport=None):
    model = OllamaClient(settings, transport=transport)

    @asynccontextmanager
    async def lifespan(app):
        yield
        await model.close()

    app = FastAPI(title="DevGuard", version="0.1.0", lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)
    bearer = HTTPBearer(auto_error=False)

    async def authenticate(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if credentials is None or not secrets.compare_digest(
            credentials.credentials, settings.session_token
        ):
            raise Unauthorized()

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
            "phase": "FOUNDATION",
            "runtime": await model.inspect(),
            "clipboard": {"enabled": False, "state": "OFF", "implemented": False},
            "guard_implemented": False,
            "repair_implemented": False,
        }

    @app.get("/api/v1/coverage", dependencies=[Depends(authenticate)])
    async def coverage():
        return {"capabilities": [
            {"capability": name, "status": "UNIMPLEMENTED", "verified_at": None}
            for name in CAPABILITIES
        ]}

    return app
