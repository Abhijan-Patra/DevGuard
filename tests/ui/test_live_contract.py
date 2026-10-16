"""Display client against real FastAPI routes, using synthetic data only."""

import httpx
import pytest
from fastapi.testclient import TestClient

from devguard.api.app import create_app
from devguard.clipboard.native import UnsupportedClipboard
from devguard.config import MODEL, Settings
from devguard.ui.client import DevGuardError, HttpDevGuardClient, AuthenticationError
from tests.guard.test_guard import TestInspector, TestScanner

TOKEN='synthetic-ui-integration-token-not-runtime-1234'


def test_live_client_uses_real_shapes_and_unavailable_model_is_held():
    app=create_app(Settings(TOKEN), scanner=TestScanner(),inspector=TestInspector(None),
                   clipboard_adapter=UnsupportedClipboard(),
                   transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'models':[]})))
    with TestClient(app,base_url='http://127.0.0.1:8765') as api:
        client=HttpDevGuardClient(token=TOKEN,session=api)
        health=client.get_health()
        assert health['model_name']==MODEL and not health['model_ready']
        assert isinstance(client.get_coverage(),list)
        assert client.get_clipboard_status()['state']=='OFF'
        held=client.evaluate_privacy('', 'Debug cart', 'explicit_prompt','local-preview',1,
                                     'password=synthetic-private-credential-3456789')
        assert held['decision']=='REVIEW' and held['safe_preview'] is None
        assert 'synthetic-private' not in str(client.get_events())
        with pytest.raises(DevGuardError) as failure:
            client.deliver_request(held['request_id'],content_version=1,destination_id='local-preview')
        assert failure.value.status_code==403
        assert not isinstance(failure.value,AuthenticationError)
        with pytest.raises(DevGuardError,match='consent'):
            client.enable_clipboard('local-host')
        with pytest.raises(DevGuardError):
            client.copy_cleaned_clipboard(999)
        with pytest.raises(DevGuardError):
            client.deliver_request(held['request_id'])
        with pytest.raises(DevGuardError):
            client.apply_patch('absent','a'*64)


@pytest.mark.parametrize('url',['http://example.invalid/api/v1','http://127.0.0.1:8765/api/v1?token=x',
                                'http://user:password@127.0.0.1:8765/api/v1'])
def test_live_client_rejects_unenrolled_destinations(url):
    with pytest.raises(DevGuardError):
        HttpDevGuardClient(url,token=TOKEN)


@pytest.mark.parametrize('status', [
    [], {}, {'worker_id': 'mock-worker', 'model_state': 'READY'},
    {'phase': 'GUARD_AND_CLIPBOARD_IMPLEMENTATION', 'runtime': {'model': MODEL}},
])
def test_noncontract_rehearsal_servers_are_not_accepted_as_live_backend(status):
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=status))) as session:
        client = HttpDevGuardClient(token=TOKEN, session=session)
        with pytest.raises(DevGuardError) as error:
            client.get_health()
        assert error.value.code == 'LIVE_BACKEND_UNVERIFIED'
