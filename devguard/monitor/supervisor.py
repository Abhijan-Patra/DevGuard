"""Lifecycle-owned, opt-in saved-file monitoring and quiet-queue scheduling."""
import asyncio
import time

from devguard.monitor.files import SavedFileMonitor
from devguard.repair.contracts import RepairError


class MonitorSupervisor:
    def __init__(self, runtime, model):
        self.runtime, self.model = runtime, model
        self.monitors = {}
        self.errors = {}
        self.automatic = False
        self.quiet_seconds = 60
        self.last_foreground = time.monotonic()

    def changed(self, project_id, signal):
        service = self.runtime.service
        if service is not None:
            item = service.create_incident(project_id, signal)
            service.queue(item['incident_id'])

    def configure(self, project_id, enabled, signal=None):
        service = self.runtime.service
        if service is None:
            raise RepairError('DEPENDENCY_UNAVAILABLE')
        spec = service._project(project_id)
        if not enabled:
            self.monitors.pop(project_id, None)
            self.errors.pop(project_id, None)
        else:
            selected = signal or spec.test_names[0]
            self.monitors[project_id] = SavedFileMonitor(spec, selected, self.changed)
            self.errors.pop(project_id, None)
        return self.project_status(project_id)

    def project_status(self, project_id):
        return {'enabled': project_id in self.monitors,
                'reason_code': self.errors.get(project_id),
                'signal': self.monitors[project_id].signal if project_id in self.monitors else None}

    def status(self):
        return {'automatic': self.automatic, 'quiet_seconds': self.quiet_seconds,
                'mode': 'FOREGROUND_QUEUE_QUIET_TIME', 'watched_projects': len(self.monitors)}

    async def run(self):
        while True:
            await asyncio.sleep(1)
            for identifier, monitor in list(self.monitors.items()):
                try:
                    await asyncio.to_thread(monitor.tick)
                except Exception:
                    # Errors disable this manifest, without logging paths/source.
                    self.errors[identifier] = 'MONITOR_SCOPE_UNAVAILABLE'
                    self.monitors.pop(identifier, None)
            service = self.runtime.service
            if self.automatic and service is not None:
                queue = self.model.queue.status()
                last = max(self.last_foreground, self.model.queue.last_foreground)
                if queue['foreground_waiting']:
                    self.last_foreground = time.monotonic()
                    # Pause future jobs, without cancelling an active inference.
                    service.scheduler.pause()
                elif time.monotonic() - last >= self.quiet_seconds:
                    try:
                        service.enter_idle()
                    except RepairError:
                        self.automatic = False
