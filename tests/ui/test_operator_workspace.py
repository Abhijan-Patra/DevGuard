"""UI operator boundaries; injected inference/verifier ports are not real repair proof."""
import asyncio
from pathlib import Path
import httpx
import pytest
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from devguard.api.app import create_app
from devguard.clipboard.native import UnsupportedClipboard
from devguard.config import Settings
from devguard.repair.contracts import ProjectSpec
from devguard.storage.audit import AuditStore
from devguard.ui.client import DevGuardError,FixtureDevGuardClient,HttpDevGuardClient
import devguard.ui.session as enrolment
import devguard.ui.client as ui_client
from tests.backend.test_repair import service_for

APP=Path(__file__).resolve().parents[2]/'devguard/ui/app.py'
TOKEN='synthetic-operator-workspace-test-token-0000000'


def button(app,label):return next(item for item in app.button if item.label==label)


def test_overview_navigation_reaches_all_real_feature_views():
    app=AppTest.from_file(APP,default_timeout=20).run()
    assert not app.exception
    assert any('Your development safety workspace' in item.value for item in app.markdown)
    button(app,'Open backend repairs').click().run()
    assert not app.exception
    assert any(item.label=='Queue investigation' for item in app.button)
    assert any(item.label=='Enter idle' for item in app.button)
    assert any(item.label=='Pause repairs' for item in app.button)
    app.sidebar.radio[1].set_value('📜 Audit Event Log').run()
    assert not app.exception and app.get('download_button')
    app.sidebar.radio[1].set_value('📊 Integration Coverage').run()
    assert not app.exception
    assert any('Recorded Mac 1 verification' in item.label for item in app.expander)


def test_fixture_queue_never_turns_into_a_fabricated_successful_repair():
    app=AppTest.from_file(APP,default_timeout=20).run()
    app.sidebar.radio[1].set_value('🔧 Repair & Patches').run()
    button(app,'Queue investigation').click().run()
    assert not app.exception
    fixture=app.session_state['fixture_client']
    newest=fixture.get_incidents()[-1]
    run=fixture.get_run(newest['active_run_id'])
    assert run['state']=='QUEUED' and run['simulated'] is True
    assert run['candidate_patch_id'] is None
    button(app,'Enter idle').click().run()
    assert fixture.get_status()['repair']['state']=='RUNNING'
    assert fixture.get_run(run['run_id'])['state']=='QUEUED'
    button(app,'Pause repairs').click().run()
    assert fixture.get_status()['repair']['state']=='PAUSED'


def test_live_control_client_uses_authorized_routes_without_starting_model_work(tmp_path):
    root=tmp_path/'source';root.mkdir()
    (root/'cart.py').write_text('VALUE = 1\n');(root/'main.py').write_text('# dependency\n')
    checks=tmp_path/'checks';checks.mkdir()
    spec=ProjectSpec('demo',root.resolve(),('cart.py','main.py'),('cart.py',),checks,('cart',),'sha256:'+'a'*64)
    async def factory(app):
        service,_=service_for(spec,tmp_path)
        service.event_sink=app.state.repair_event_sink
        return service
    app=create_app(Settings(TOKEN),repair_factory=factory,
        clipboard_adapter=UnsupportedClipboard(),
        transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'models':[]})))
    with TestClient(app,base_url='http://127.0.0.1:8765') as api:
        client=HttpDevGuardClient(token=TOKEN,session=api)
        assert client.initialize_repair()['available'] is True
        assert client.get_findings()==[]
        assert client.set_repair_idle(True)['paused'] is False
        assert client.set_repair_idle(False)['paused'] is True
        incident=client.create_incident('demo','cart')
        run=client.investigate_incident(incident['incident_id'])
        assert run['state']=='QUEUED'
        assert client.cancel_run(run['run_id'])['state']=='CANCELED'
        assert client.get_run(run['run_id'])['completed_tools']==[]
        assert (root/'cart.py').read_text()=='VALUE = 1\n'
        unauth=HttpDevGuardClient(session=api)
        with pytest.raises(DevGuardError):unauth.set_repair_idle(True)


@pytest.mark.parametrize('url',['http://127.0.0.1:8766/api/v1','http://example.invalid/api/v1',
                               'http://127.0.0.1:8765/api/v1?token=foo'])
def test_local_token_cannot_be_enrolled_for_another_destination(url):
    with pytest.raises(DevGuardError,match='default DevGuard endpoint'):
        enrolment.load_local_token(url)


@pytest.mark.parametrize('url',['http://[::1','http://localhost:abc/api/v1','http://localhost:99999/api/v1'])
def test_malformed_connection_urls_produce_safe_errors(url):
    with pytest.raises(DevGuardError):HttpDevGuardClient(url)
    with pytest.raises(DevGuardError):enrolment.load_local_token(url)


def test_local_token_file_must_be_private_regular_and_not_linked(tmp_path,monkeypatch):
    root=tmp_path/'app';runtime=root/'.devguard';runtime.mkdir(parents=True,mode=0o700)
    monkeypatch.setenv('DEVGUARD_HOME', str(root.resolve()))
    path=runtime/'session-token';path.write_text(TOKEN);path.chmod(0o600)
    assert enrolment.load_local_token('http://127.0.0.1:8765/api/v1')==TOKEN
    path.chmod(0o644)
    with pytest.raises(DevGuardError):enrolment.load_local_token('http://127.0.0.1:8765/api/v1')
    path.unlink();path.symlink_to(tmp_path/'absent')
    with pytest.raises(DevGuardError):enrolment.load_local_token('http://127.0.0.1:8765/api/v1')


def test_local_enrolment_never_populates_password_widget_and_url_change_revokes_it(monkeypatch):
    client=FixtureDevGuardClient()
    monkeypatch.setattr(client,'is_fixture_mode',lambda:False)
    calls=[]
    def connect(**kwargs):calls.append(kwargs);return client
    monkeypatch.setattr(ui_client,'HttpDevGuardClient',connect)
    import devguard.ui.session
    monkeypatch.setattr(devguard.ui.session,'load_local_token',lambda url:TOKEN)
    app=AppTest.from_file(APP,default_timeout=20).run()
    app.sidebar.radio[0].set_value('Live Mode (FastAPI Backend)').run()
    button(app,'Connect on this Mac').click().run()
    assert not app.exception
    assert app.session_state['local_operator_token']==TOKEN
    password=next(item for item in app.text_input if item.label=='Operator Session Token')
    assert password.value==''
    assert not any(TOKEN in item.value for item in app.markdown)
    app.session_state['last_eval_result']={'decision':'ALLOW'}
    next(item for item in app.text_input if item.label=='Base URL').set_value('http://127.0.0.1:8766/api/v1').run()
    assert not app.exception
    assert 'local_operator_token' not in app.session_state
    assert 'last_eval_result' not in app.session_state
    assert calls[-1]['token'] is None
    # Manually entered credentials must also be re-enrolled for a new endpoint.
    next(item for item in app.text_input if item.label=='Operator Session Token').set_value(TOKEN).run()
    assert calls[-1]['token']==TOKEN
    next(item for item in app.text_input if item.label=='Base URL').set_value('http://127.0.0.1:8765/api/v1').run()
    assert calls[-1]['token'] is None


@pytest.mark.parametrize('method,label,code',[
    ('set_repair_idle','Enter idle','IDLE_NOT_ACKNOWLEDGED'),
    ('set_repair_idle','Pause repairs','PAUSE_NOT_ACKNOWLEDGED'),
])
def test_worker_controls_require_backend_acknowledgement(monkeypatch,method,label,code):
    monkeypatch.setattr(FixtureDevGuardClient,method,lambda *args,**kwargs:{})
    app=AppTest.from_file(APP,default_timeout=20).run()
    app.sidebar.radio[1].set_value('🔧 Repair & Patches').run()
    button(app,label).click().run()
    assert not app.exception
    assert any(code in item.value for item in app.error)
