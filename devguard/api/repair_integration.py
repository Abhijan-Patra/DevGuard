"""Trusted startup/lifecycle wiring for Mac 2's existing worker and routes."""

import asyncio
from pathlib import Path
import re

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from devguard.agent.mac1_bridge import Mac1ModelBridge
from devguard.guard.repair_bridge import RepairGuardBridge
from devguard.repair.contracts import RepairError
from devguard.repair.runner import DockerVerifier
from devguard.repair.service import RepairService


class RepairRuntime:
    def __init__(self, factory=None):
        self.factory = factory
        self.service = None
        self.reason = 'REPAIR_NOT_CONFIGURED'
        self.lifecycle_managed = False
        self._initializing = asyncio.Lock()

    async def initialize(self, app):
        async with self._initializing:
            if self.service is not None or self.factory is None:
                return
            try:
                service = await self.factory(app)
                if not isinstance(service, RepairService):
                    raise RepairError('DEPENDENCY_UNAVAILABLE')
                self.service = service
                self.reason = 'READY'
            except RepairError as error:
                allowed = {'MODEL_NOT_PINNED', 'DOCKER_UNAVAILABLE', 'IMAGE_NOT_PINNED',
                           'AUDIT_UNAVAILABLE', 'VERIFIER_UNAVAILABLE'}
                self.reason = error.code if error.code in allowed else 'DEPENDENCY_UNAVAILABLE'
            except Exception:
                self.reason = 'DEPENDENCY_UNAVAILABLE'

    def status(self):
        return {'configured': self.factory is not None, 'available': self.service is not None,
                'state': ('PAUSED' if self.service.scheduler.paused else 'RUNNING')
                         if self.service is not None else 'UNAVAILABLE',
                'reason_code': self.reason}

    def __getattr__(self, name):
        # Router calls this proxy only from its existing thread-pool boundaries.
        if self.service is None:
            raise RepairError('DEPENDENCY_UNAVAILABLE')
        return getattr(self.service, name)

    def pause(self):
        if self.service is not None:
            self.service.pause()

    async def join(self):
        if self.service is not None:
            stopped = await asyncio.to_thread(self.service.shutdown, 30)
            if not stopped:
                return False
        self.lifecycle_managed = False
        return True

    def incidents(self):
        if self.service is None:
            return []
        service = self.service
        with service._lock:
            items = []
            for incident in service.incidents.values():
                run = next((r for r in reversed(list(service.runs.values()))
                            if r.incident_id == incident['incident_id']), None)
                items.append({**incident, 'title': 'Named check: ' + incident['signal'],
                              'active_run_id': run.run_id if run else None,
                              'status': run.state if run else 'OPEN'})
            return items


def integration_router(runtime, app, operator_auth):
    router = APIRouter(prefix='/api/v1', dependencies=[Depends(operator_auth)])

    @router.get('/incidents')
    def incidents():
        return {'incidents': runtime.incidents(), 'repair': runtime.status()}

    @router.post('/repair/initialize')
    async def initialize():
        await runtime.initialize(app)
        status = runtime.status()
        return JSONResponse(status_code=200 if status['available'] else 503, content=status)

    return router


def demo_repair_factory(repository_root: Path, image_id: str):
    """Opt-in trusted demo configuration; no API/model-selected roots or images."""
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', image_id):
        raise ValueError('Use an actual pinned Docker image ID')
    repository_root = repository_root.resolve()

    async def create(app):
        from demo.backend.config import demo_project
        runtime = await app.state.model_queue.inspect()
        if not runtime.get('model_ready') or not runtime.get('model_digest'):
            raise RepairError('MODEL_NOT_PINNED')
        if not app.state.audit.durable:
            raise RepairError('AUDIT_UNAVAILABLE')
        verifier = DockerVerifier()
        if not verifier.docker:
            raise RepairError('DOCKER_UNAVAILABLE')
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                verifier.docker, 'image', 'inspect', image_id, '--format', '{{.Id}}',
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=10)
            if process.returncode != 0 or stdout.decode().strip() != image_id:
                raise RepairError('VERIFIER_UNAVAILABLE')
        except (OSError, asyncio.TimeoutError):
            raise RepairError('DOCKER_UNAVAILABLE') from None
        finally:
            if process is not None and process.returncode is None:
                process.kill()
                await process.wait()
        loop = asyncio.get_running_loop()
        service = RepairService(
            model=Mac1ModelBridge(app.state.model_queue, loop, runtime),
            guard=RepairGuardBridge(app.state.guard, loop, RepairError),
            verifier=verifier, runtime_root=repository_root/'.devguard'/'repair',
            event_sink=app.state.repair_event_sink,
            readiness_check=lambda: {
                'foreground_priority': (
                    app.state.model_queue.queue.PRIORITIES.get('foreground', 10)
                    < app.state.model_queue.queue.PRIORITIES.get('background', 0)
                    and not app.state.model_queue.queue.status()['closed']),
                'durable_events': app.state.audit.durable is True,
                'worker_lifecycle': app.state.repair.lifecycle_managed is True,
                # The image inspection above and fixed demo manifest are trusted
                # startup checks, never flags supplied by an HTTP/model request.
                'trusted_verifier': True,
            })
        service.register_project(demo_project(repository_root, image_id))
        return service
    return create
