"""Mount into Mac 1's FastAPI app; deliberately no second server or token store."""

import json
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from devguard.repair.contracts import RepairError
from devguard.repair.service import RepairService


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class IncidentBody(Body):
    project_id: str = Field(min_length=1, max_length=128)
    signal: str = Field(pattern="^[a-zA-Z0-9_]{1,80}$")
    source_revision: str | None = Field(default=None, pattern="^[a-f0-9]{64}$")


class ApplyBody(Body):
    approved: Literal[True]
    expected_candidate_hash: str = Field(pattern="^[a-f0-9]{64}$")
    expected_base_revision: str = Field(pattern="^[a-f0-9]{64}$")
    idempotency_key: str = Field(min_length=1, max_length=128)


def response_error(error: RepairError) -> JSONResponse:
    code = error.code
    status = (
        404
        if code in {"NOT_FOUND", "PROJECT_NOT_FOUND"}
        else 409
        if code
        in {
            "STALE_SOURCE",
            "CANDIDATE_CONFLICT",
            "PATCH_ALREADY_APPLIED",
            "PATCH_NOT_READY",
        }
        else 503
        if code
        in {
            "DEPENDENCY_UNAVAILABLE",
            "DOCKER_UNAVAILABLE",
            "MODEL_NOT_PINNED",
            "CAPACITY_EXHAUSTED",
            "INTEGRATION_NOT_READY",
            "WORKER_CLOSED",
        }
        else 413
        if code == "REQUEST_TOO_LARGE"
        else 400
        if code == "INVALID_REQUEST"
        else 403
    )
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": "Request held; inspect the safe status and retry if permitted.",
                "request_id": "req-" + uuid.uuid4().hex,
            }
        },
    )


def create_repair_router(service: RepairService, require_operator) -> APIRouter:
    """require_operator MUST be Mac 1's scope-checking dependency, never model-accessible."""
    if require_operator is None:
        raise ValueError("An operator-auth dependency is required")
    router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_operator)])

    def invoke(action, status: int = 200):
        try:
            return JSONResponse(status_code=status, content=action())
        except RepairError as error:
            return response_error(error)
        except Exception:
            return response_error(RepairError("DEPENDENCY_UNAVAILABLE"))

    async def with_body(request: Request, schema, action, status: int = 200):
        try:
            data = bytearray()
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data) > 8192:
                    raise RepairError("REQUEST_TOO_LARGE")
            try:
                body = schema.model_validate(json.loads(data or b"{}"))
            except (ValidationError, ValueError, TypeError):
                raise RepairError("INVALID_REQUEST") from None
            return await run_in_threadpool(invoke, lambda: action(body), status)
        except RepairError as error:
            return response_error(error)

    @router.post("/incidents")
    async def create_incident(request: Request):
        return await with_body(
            request,
            IncidentBody,
            lambda b: service.create_incident(
                b.project_id, b.signal, b.source_revision
            ),
        )

    @router.post("/incidents/{incident_id}/investigate")
    async def investigate(incident_id: str, request: Request):
        return await with_body(
            request, Body, lambda b: service.queue(incident_id).view(), 202
        )

    @router.get("/runs/{run_id}")
    def get_run(run_id: str):
        return invoke(lambda: service.get_run(run_id).view())

    @router.post("/runs/{run_id}/cancel")
    async def cancel(run_id: str, request: Request):
        return await with_body(request, Body, lambda b: service.cancel(run_id).view())

    @router.get("/patches/{candidate_id}")
    def get_patch(candidate_id: str):
        return invoke(lambda: service.patch_view(candidate_id))

    @router.post("/patches/{candidate_id}/apply")
    async def apply(candidate_id: str, request: Request):
        return await with_body(
            request,
            ApplyBody,
            lambda b: service.apply(
                candidate_id,
                expected_hash=b.expected_candidate_hash,
                expected_base=b.expected_base_revision,
                idempotency_key=b.idempotency_key,
                approved=b.approved,
            ),
        )

    @router.post("/patches/{candidate_id}/reject")
    async def reject(candidate_id: str, request: Request):
        return await with_body(request, Body, lambda b: service.reject(candidate_id))

    @router.post('/patches/{candidate_id}/rollback')
    async def rollback(candidate_id: str, request: Request):
        return await with_body(request, ApplyBody, lambda b: service.rollback(
            candidate_id, expected_hash=b.expected_candidate_hash,
            expected_base=b.expected_base_revision, idempotency_key=b.idempotency_key,
            approved=b.approved))

    @router.post("/scheduler/pause")
    async def pause(request: Request):
        def action(body):
            if hasattr(service, 'supervisor'):
                service.supervisor.automatic = False
            service.pause()
            return {"paused": True}

        return await with_body(request, Body, action)

    @router.post("/scheduler/enter-idle")
    async def enter_idle(request: Request):
        def action(body):
            service.enter_idle()
            return {"paused": False, "trigger": "manual"}

        return await with_body(request, Body, action)

    return router
