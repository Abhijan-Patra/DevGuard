"""Combined API/worker/guard/audit wiring with declared fake inference/verifier ports."""

import asyncio
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from devguard.api.app import create_app
from devguard.clipboard.native import UnsupportedClipboard
from devguard.config import Settings
from devguard.guard.repair_bridge import RepairGuardBridge
from devguard.repair.contracts import ProjectSpec, RepairError
from devguard.schemas.guard import Decision, ModelProposal
from devguard.storage.audit import AuditStore
from devguard.ui.client import HttpDevGuardClient
from tests.backend.test_repair import service_for
from tests.guard.test_guard import TestInspector, TestScanner

TOKEN='synthetic-integration-operator-token-not-runtime-1234'
ADAPTER='synthetic-integration-adapter-token-not-runtime-5678'
AUTH={'Authorization':'Bearer '+TOKEN}


def test_unconfigured_worker_routes_are_visible_and_scope_protected():
    app=create_app(Settings(TOKEN,adapter_token=ADAPTER),clipboard_adapter=UnsupportedClipboard())
    with TestClient(app) as api:
        status=api.get('/api/v1/status',headers=AUTH).json()
        assert status['repair']['reason_code']=='REPAIR_NOT_CONFIGURED'
        assert api.get('/api/v1/incidents',headers=AUTH).json()['incidents']==[]
        assert api.get('/api/v1/runs/absent',headers=AUTH).status_code==503
        assert api.post('/api/v1/repair/initialize',headers=AUTH).status_code==503
        assert api.get('/api/v1/incidents').status_code==401
        assert api.post('/api/v1/scheduler/enter-idle',headers={
            'Authorization':'Bearer '+ADAPTER}).status_code==401


def test_model_missing_factory_does_not_prevent_privacy_startup():
    async def unavailable(app):
        raise RepairError('MODEL_NOT_PINNED')
    app=create_app(Settings(TOKEN),repair_factory=unavailable,clipboard_adapter=UnsupportedClipboard())
    with TestClient(app) as api:
        status=api.get('/api/v1/status',headers=AUTH).json()
        assert status['repair']['reason_code']=='MODEL_NOT_PINNED'
        assert status['clipboard']['state']=='OFF'


def test_real_worker_ports_bridge_audit_and_display_client_without_touching_originals(tmp_path):
    root=tmp_path/'project'
    root.mkdir()
    (root/'cart.py').write_bytes(b'VALUE = 1\n')
    (root/'main.py').write_bytes(b'# independent dependency\n')
    checks=tmp_path/'checks'
    checks.mkdir()
    spec=ProjectSpec('demo',root.resolve(),('cart.py','main.py'),('cart.py',),checks,
                     ('cart',),'sha256:'+'a'*64)
    audit=AuditStore(tmp_path/'private'/'audit.sqlite3')
    services=[]
    async def factory(app):
        service,_=service_for(spec,tmp_path)
        service.guard=RepairGuardBridge(app.state.guard,asyncio.get_running_loop(),RepairError)
        service.event_sink=app.state.repair_event_sink
        services.append(service)
        return service
    app=create_app(Settings(TOKEN),repair_factory=factory,audit=audit,
                   scanner=TestScanner(),inspector=TestInspector(ModelProposal(decision=Decision.ALLOW,spans=[])),
                   clipboard_adapter=UnsupportedClipboard())
    with TestClient(app,base_url='http://127.0.0.1:8765') as api:
        client=HttpDevGuardClient(token=TOKEN,session=api)
        assert client.get_status()['repair']['state']=='PAUSED'
        incident=api.post('/api/v1/incidents',headers=AUTH,json={'project_id':'demo','signal':'cart'}).json()
        run=api.post('/api/v1/incidents/'+incident['incident_id']+'/investigate',headers=AUTH).json()
        # Calling the actual service from a thread also exercises the async guard bridge.
        import threading
        worker=threading.Thread(target=services[0].execute,args=(run['run_id'],))
        worker.start()
        worker.join(timeout=5)
        assert not worker.is_alive()
        result=client.get_run(run['run_id'])
        assert result['state']=='READY_FOR_REVIEW'
        patch=client.get_patch(result['candidate_patch_id'])
        assert patch['status']=='READY_FOR_REVIEW' and patch['verification_summary']=='PASS'
        assert (root/'cart.py').read_text()=='VALUE = 1\n'
        assert client.get_incidents()[0]['active_run_id']==run['run_id']
        assert any(e['kind']=='run.state' for e in client.get_events()['events'])
        # The real apply API still enforces approval and both inspected hashes.
        rejected=api.post('/api/v1/patches/'+patch['patch_id']+'/apply',headers=AUTH,json={
            'expected_candidate_hash':patch['candidate_hash'],
            'expected_base_revision':patch['base_revision'],'idempotency_key':'test-only'})
        assert rejected.status_code==400 and (root/'cart.py').read_text()=='VALUE = 1\n'
        approved=client.apply_patch(patch['patch_id'],patch['candidate_hash'],
            expected_base_revision=patch['base_revision'],idempotency_key='test-only',approved=True)
        assert approved['state']=='APPLIED' and (root/'cart.py').read_text()=='VALUE = 2\n'
    assert services[0].scheduler.paused
    assert services[0].scheduler.stopped()
    assert services[0]._closed


@pytest.mark.parametrize('first_drain_stops', [True, False])
def test_shutdown_waits_for_worker_acknowledgement_before_clearing_resources(tmp_path, first_drain_stops):
    audit = AuditStore(tmp_path/'private'/'audit.sqlite3')
    observed = []
    async def factory(app):
        # An actual service is required by startup. No work/model is executed;
        # the injected shutdown result exercises the resource-order boundary.
        from devguard.repair.service import RepairService
        service = RepairService(model=object(), guard=object(), verifier=object(),
            runtime_root=tmp_path/'work', event_sink=app.state.repair_event_sink)
        original_shutdown = service.shutdown
        def shutdown(timeout):
            assert app.state.guard.records.get('sentinel') is not None
            assert audit.events()['events'] == []
            closed = app.state.model_queue.queue.status()['closed']
            observed.append(closed)
            if not first_drain_stops and len(observed) == 1:
                return False
            return original_shutdown(timeout)
        service.shutdown = shutdown
        app.state.guard.records['sentinel'] = SimpleNamespace(candidate=None, deadline=float('inf'))
        return service
    app = create_app(Settings(TOKEN), audit=audit, repair_factory=factory,
        clipboard_adapter=UnsupportedClipboard())
    with TestClient(app):
        assert app.state.repair.lifecycle_managed
    assert observed == ([False] if first_drain_stops else [False, True])
    assert not app.state.repair.lifecycle_managed
    assert not app.state.guard.records
