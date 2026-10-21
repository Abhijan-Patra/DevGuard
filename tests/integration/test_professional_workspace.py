"""Security/lifecycle boundaries with declared model/verifier doubles, not accuracy proof."""
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from devguard.api.app import create_app
from devguard.clipboard.native import UnsupportedClipboard
from devguard.config import Settings
from devguard.schemas.guard import Decision, ModelProposal
from devguard.repair.contracts import ProjectSpec, RepairError
from devguard.repair.projects import load_projects
from devguard.repair.workspace import digest
from tests.backend.test_repair import service_for, run_once
from tests.guard.test_guard import TestScanner, TestInspector

TOKEN='synthetic-workspace-operator-token-000000000000'
AUTH={'Authorization':'Bearer '+TOKEN}
BROWSER={'Origin':'http://127.0.0.1:8765','X-DevGuard-Workspace':'1'}


def app_for(tmp_path, *, browser=True, adapter_token=None):
    root=tmp_path/'project';root.mkdir()
    (root/'cart.py').write_text('VALUE = 1\n')
    (root/'main.py').write_text('# independent dependency\n')
    checks=tmp_path/'checks';checks.mkdir()
    (checks/'test_cart.py').write_text('# independent test definition\n')
    spec=ProjectSpec('demo',root.resolve(),('cart.py','main.py'),('cart.py',),checks.resolve(),('cart',),'sha256:'+'a'*64)
    services=[]
    async def factory(app):
        service,_=service_for(spec,tmp_path)
        services.append(service)
        return service
    app=create_app(Settings(TOKEN,adapter_token=adapter_token),repair_factory=factory,browser_workspace=browser,
                   scanner=TestScanner(),inspector=TestInspector(ModelProposal(decision=Decision.ALLOW,spans=[])),
                   clipboard_adapter=UnsupportedClipboard(),
                   transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'models':[]})))
    return app,spec,services


def test_browser_pairing_requires_exact_local_origin_and_never_returns_operator_token(tmp_path):
    app,_,_=app_for(tmp_path)
    with TestClient(app,base_url='http://127.0.0.1:8765',client=('127.0.0.1',1234)) as client:
        assert client.get('/api/v1/projects').status_code==401
        for headers in [{}, {'Origin':'https://evil.invalid','X-DevGuard-Workspace':'1'},
                        {'Origin':'http://127.0.0.1:9999','X-DevGuard-Workspace':'1'}]:
            assert client.post('/api/v1/session/connect',headers=headers).status_code==403
        response=client.post('/api/v1/session/connect',headers=BROWSER)
        assert response.status_code==200 and TOKEN not in response.text
        assert 'HttpOnly' in response.headers['set-cookie'] and 'SameSite=strict' in response.headers['set-cookie']
        assert client.get('/api/v1/projects',headers={'X-DevGuard-Workspace':'1'}).status_code==200
        assert client.get('/api/v1/projects').status_code==401
        assert client.post('/api/v1/scheduler/enter-idle',headers={'Origin':'http://evil.invalid','X-DevGuard-Workspace':'1'},json={}).status_code==401
        assert client.post('/api/v1/session/disconnect',headers=BROWSER).json()=={'connected':False}
        assert client.get('/api/v1/projects',headers=BROWSER).status_code==401


def test_browser_pairing_is_disabled_by_default_and_for_remote_hosts(tmp_path):
    app,_,_=app_for(tmp_path,browser=False)
    with TestClient(app,base_url='http://127.0.0.1:8765',client=('127.0.0.1',1234)) as client:
        assert client.post('/api/v1/session/connect',headers=BROWSER).status_code==403
    with TestClient(app,base_url='http://127.0.0.1:8765',client=('192.0.2.10',1234)) as client:
        assert client.post('/api/v1/session/connect',headers=BROWSER).status_code==403


def test_managed_source_read_delivers_exact_bytes_once_and_refuses_changed_source(tmp_path):
    app,spec,_=app_for(tmp_path)
    with TestClient(app) as client:
        body={'project_id':'demo','path':'cart.py','content_version':3,'task':None}
        result=client.post('/api/v1/context/read',json=body,headers=AUTH).json()
        assert result['decision']=='ALLOW' and result['safe_preview']=='VALUE = 1\n'
        url='/api/v1/context/requests/'+result['request_id']+'/deliver'
        delivery={'content_version':3,'destination_id':'local-composer'}
        assert client.post(url,json=delivery,headers=AUTH).json()['delivered'] is True
        assert client.get('/api/v1/composer',headers=AUTH).json()['text']=='VALUE = 1\n'
        assert client.post(url,json=delivery,headers=AUTH).status_code==409
        result=client.post('/api/v1/context/read',json=body,headers=AUTH).json()
        (spec.root/'cart.py').write_text('VALUE = 9\n')
        response=client.post('/api/v1/context/requests/'+result['request_id']+'/deliver',json=delivery,headers=AUTH)
        assert response.status_code==409 and response.json()['error']['code']=='STALE_SOURCE'
        result=client.post('/api/v1/context/read',json=body,headers=AUTH).json()
        (spec.root/'cart.py').write_text('VALUE = 11\n')
        bypass=client.post('/api/v1/guard/requests/'+result['request_id']+'/deliver',json=delivery,headers=AUTH)
        assert bypass.status_code==409 and bypass.json()['error']['code']=='STALE_SOURCE'
        assert 'VALUE' not in json.dumps(client.get('/api/v1/events',headers=AUTH).json())
        assert client.delete('/api/v1/composer',headers=AUTH).json()['cleared']
        assert client.get('/api/v1/composer',headers=AUTH).json()['text'] is None


@pytest.mark.parametrize('path',['../cart.py','.env','tests/test_cart.py','not-enrolled.py'])
def test_managed_read_cannot_expand_manifest(tmp_path,path):
    app,_,_=app_for(tmp_path)
    with TestClient(app) as client:
        response=client.post('/api/v1/context/read',json={'project_id':'demo','path':path,'content_version':1},headers=AUTH)
        assert response.status_code==403 and response.json()['error']['code']=='PATH_DENIED'


def test_watcher_debounces_saved_changes_and_is_off_on_startup(tmp_path):
    app,spec,services=app_for(tmp_path)
    with TestClient(app) as client:
        service=services[0]
        project=client.get('/api/v1/projects',headers=AUTH).json()['projects'][0]
        assert project['watch']['enabled'] is False
        client.post('/api/v1/projects/demo/watch',headers=AUTH,json={'enabled':True})
        monitor=app.state.supervisor.monitors['demo']
        (spec.root/'cart.py').write_text('VALUE = 3\n')
        monitor.tick(now=0);monitor.tick(now=3);monitor.tick(now=5)
        assert len(service.incidents)==1 and len(service.runs)==1
        assert service.scheduler.paused
        assert client.post('/api/v1/scheduler/automatic',headers=AUTH,json={'enabled':True,'quiet_seconds':60}).json()['automatic']
        client.post('/api/v1/scheduler/pause',headers=AUTH,json={})
        assert not app.state.supervisor.automatic
        client.post('/api/v1/projects/demo/watch',headers=AUTH,json={'enabled':False})
        assert not app.state.supervisor.monitors


def test_apply_rollback_is_idempotent_and_preserves_concurrent_edits(tmp_path):
    app,spec,services=app_for(tmp_path)
    with TestClient(app) as client:
        service=services[0];run=run_once(service)
        patch=service.patch_view(run.candidate_id)
        body={'approved':True,'expected_candidate_hash':patch['candidate_hash'],'expected_base_revision':patch['base_revision'],'idempotency_key':'apply-test'}
        base='/api/v1/patches/'+run.candidate_id
        assert client.post(base+'/apply',headers=AUTH,json=body).json()['state']=='APPLIED'
        (spec.root/'cart.py').write_text('VALUE = 999\n')
        body['idempotency_key']='rollback-test'
        assert client.post(base+'/rollback',headers=AUTH,json=body).status_code==409
        assert (spec.root/'cart.py').read_text()=='VALUE = 999\n'
        (spec.root/'cart.py').write_text('VALUE = 2\n')
        assert client.post(base+'/rollback',headers=AUTH,json=body).json()['state']=='ROLLED_BACK'
        assert (spec.root/'cart.py').read_text()=='VALUE = 1\n'
        assert client.post(base+'/rollback',headers=AUTH,json=body).json()['state']=='ROLLED_BACK'


def test_startup_manifest_validates_paths_tests_and_docker_pin(tmp_path):
    _,spec,_=app_for(tmp_path)
    config={'projects':[{'project_id':'demo','root':str(spec.root),'source_files':['cart.py','main.py'],
                         'writable_files':['cart.py'],'trusted_tests':str(spec.trusted_tests),
                         'test_names':['cart'],'image_id':spec.image_id}]}
    path=tmp_path/'projects.json';path.write_text(json.dumps(config))
    assert load_projects(path)[0].project_id=='demo'
    config['projects'][0]['source_files']=['../private.py'];config['projects'][0]['writable_files']=['../private.py'];path.write_text(json.dumps(config))
    with pytest.raises(RepairError):load_projects(path)
    config['projects'][0]['source_files']=['cart.py'];config['projects'][0]['writable_files']=['cart.py'];config['projects'][0]['image_id']='latest';path.write_text(json.dumps(config))
    with pytest.raises(ValueError):load_projects(path)


def test_workspace_assets_ship_with_strict_headers(tmp_path):
    app,_,_=app_for(tmp_path)
    with TestClient(app) as client:
        response=client.get('/app')
        assert response.status_code==200 and 'workspace.js' in response.text
        assert 'frame-ancestors' in response.headers['content-security-policy']
        assert response.headers['cache-control']=='no-store'
        assert client.get('/assets/workspace.js').status_code==200
        assert client.get('/assets/../config.py').status_code==404
