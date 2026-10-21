"""Manifest-scoped context reads and ephemeral, actual local receiver delivery."""
import hashlib
import time

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import Field

from devguard.api.repair_routes import Body, response_error
from devguard.guard.engine import GuardError
from devguard.repair.contracts import RepairError
from devguard.repair.workspace import read_source
from devguard.schemas.guard import GuardInput, DeliveryInput


class WatchInput(Body):
    enabled: bool
    signal: str | None = Field(default=None, pattern='^[a-zA-Z0-9_]{1,80}$')


class AutomaticInput(Body):
    enabled: bool
    quiet_seconds: int = Field(default=60, ge=15, le=3600)


class ContextInput(Body):
    project_id: str = Field(pattern='^[a-zA-Z0-9_-]{1,100}$')
    path: str = Field(min_length=1, max_length=256)
    task: str | None = Field(default=None, max_length=512)
    content_version: int = Field(ge=0)


class LocalComposer:
    def __init__(self):
        self.text = None
        self.expiry = 0

    async def receive(self, text):
        self.text, self.expiry = text, time.monotonic() + 600

    def clear(self):
        self.text, self.expiry = None, 0

    def view(self):
        if time.monotonic() >= self.expiry:
            self.clear()
        return {'text': self.text, 'destination_id': 'local-composer', 'external_delivery': False,
                'expires_in_seconds': max(0, int(self.expiry - time.monotonic())),
                'retention': 'memory-only; expires after ten minutes'}


def workspace_router(app, require_operator, supervisor, composer):
    router = APIRouter(prefix='/api/v1', dependencies=[Depends(require_operator)])

    @router.get('/projects')
    def projects():
        service = app.state.repair.service
        if service is None:
            return {'projects': [], 'repair': app.state.repair.status()}
        with service._lock:
            return {'projects': [{'project_id': spec.project_id, 'source_files': list(spec.source_files),
                                  'writable_files': list(spec.writable_files), 'checks': list(spec.test_names),
                                  'image_id': spec.image_id, 'watch': supervisor.project_status(spec.project_id)}
                                 for spec in service.projects.values()]}

    @router.post('/projects/{identifier}/watch')
    async def watch(identifier: str, body: WatchInput):
        try:
            return await run_in_threadpool(supervisor.configure, identifier, body.enabled, body.signal)
        except RepairError as error:
            return response_error(error)

    @router.get('/scheduler/status')
    def scheduler_status():
        return supervisor.status()

    @router.post('/scheduler/automatic')
    def automatic(body: AutomaticInput):
        if app.state.repair.service is None:
            return response_error(RepairError('DEPENDENCY_UNAVAILABLE'))
        supervisor.automatic, supervisor.quiet_seconds = body.enabled, body.quiet_seconds
        supervisor.last_foreground = time.monotonic()
        app.state.repair.service.scheduler.pause()
        return supervisor.status()

    @router.post('/context/read')
    async def context_read(body: ContextInput):
        try:
            service = app.state.repair.service
            if service is None:
                raise RepairError('DEPENDENCY_UNAVAILABLE')
            spec = service._project(body.project_id)
            if body.path not in spec.source_files:
                raise RepairError('PATH_DENIED')
            data = await run_in_threadpool(read_source, spec.root, body.path)
            if len(data) > 32768:
                raise RepairError('SOURCE_TOO_LARGE')
            result = await app.state.guard.evaluate(GuardInput(
                project_id=body.project_id, task=body.task, surface='file_read',
                destination_id='local-composer', content_version=body.content_version,
                text=data.decode()), owner='operator')
            expected = hashlib.sha256(data).hexdigest()
            async def source_unchanged():
                try:
                    current = await run_in_threadpool(read_source, spec.root, body.path)
                except RepairError:
                    app.state.guard.revoke(result.request_id)
                    raise GuardError('STALE_SOURCE') from None
                if hashlib.sha256(current).hexdigest() != expected:
                    app.state.guard.revoke(result.request_id)
                    raise GuardError('STALE_SOURCE')
            # Attach to the inspection itself. Generic /guard/deliver cannot
            # bypass source validation by avoiding the context route.
            result.before_release = source_unchanged
            return {**result.view(), 'source_hash': hashlib.sha256(data).hexdigest()}
        except RepairError as error:
            return response_error(error)

    @router.post('/context/requests/{identifier}/deliver')
    async def deliver_context(identifier: str, body: DeliveryInput):
        record = app.state.guard.get(identifier, 'operator')
        if record.before_release is None:
            raise GuardError('CONTEXT_BINDING_REQUIRED')
        return await app.state.guard.deliver(identifier, owner='operator', version=body.content_version,
                                             destination=body.destination_id)

    @router.get('/composer')
    def composer_status():
        return composer.view()

    @router.delete('/composer')
    def clear_composer():
        composer.clear()
        return {'cleared': True}

    return router
