"""Operator-controlled text inspection; no arbitrary remote destination registration."""

from fastapi import APIRouter, Depends, Query, Request

from devguard.guard.engine import GuardError
from devguard.schemas.guard import ClipboardCopy, ClipboardEnable, DeliveryInput, GuardInput


def guard_router(authenticate, authenticate_guard, guard, clipboard, audit):
    router = APIRouter(prefix="/api/v1")

    def local_operator(request):
        if request.client is None or request.client.host not in {"127.0.0.1", "::1"}:
            raise GuardError("LOCAL_CAPTURE_OPERATOR_REQUIRED", 403)

    @router.post("/guard/evaluate")
    async def evaluate(body: GuardInput, owner: str = Depends(authenticate_guard)):
        return (await guard.evaluate(body, owner=owner)).view()

    @router.post("/guard/requests/{identifier}/deliver")
    async def deliver(identifier: str, body: DeliveryInput, owner: str = Depends(authenticate_guard)):
        return await guard.deliver(identifier, owner=owner, version=body.content_version,
                                   destination=body.destination_id)

    @router.get("/findings", dependencies=[Depends(authenticate)])
    async def findings():
        guard.expire()
        return {"findings": [record.view() for record in guard.records.values()
                             if record.reasons and record.owner == "operator"]}

    @router.get("/events", dependencies=[Depends(authenticate)])
    async def events(after: int = Query(default=0, ge=0, le=2**63-1)):
        return audit.events(after)

    @router.get("/clipboard/status", dependencies=[Depends(authenticate)])
    async def clipboard_status():
        return clipboard.status()

    @router.post("/clipboard/enable", dependencies=[Depends(authenticate)])
    async def enable(request: Request, body: ClipboardEnable):
        local_operator(request)
        return await clipboard.enable(consent=body.consent, task=body.task)

    @router.post("/clipboard/disable", dependencies=[Depends(authenticate)])
    async def disable(request: Request):
        local_operator(request)
        return await clipboard.disable()

    @router.post("/clipboard/copy-cleaned", dependencies=[Depends(authenticate)])
    async def copy_cleaned(request: Request, body: ClipboardCopy):
        local_operator(request)
        return await clipboard.copy_cleaned(body.content_version)

    return router
