"""Render checks use Streamlit's element tree, never screenshots/recordings."""

import httpx
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

streamlit=pytest.importorskip('streamlit')
from streamlit.testing.v1 import AppTest

from devguard.api.app import create_app
from devguard.clipboard.native import UnsupportedClipboard
from devguard.config import Settings
import devguard.ui.client as ui_client
from tests.guard.test_guard import TestInspector, TestScanner

TOKEN='render-test-only-operator-token-not-runtime-123456'
VIEWS=['📋 Text Clipboard','📊 Integration Coverage','🔧 Repair & Patches','📜 Audit Event Log']
APP=Path(__file__).resolve().parents[2]/'devguard/ui/app.py'


def test_all_fixture_views_render_and_actions_keep_fixture_state():
    app=AppTest.from_file(APP,default_timeout=15).run()
    assert not app.exception
    for view in VIEWS:
        app.sidebar.radio[1].set_value(view).run()
        assert not app.exception
    app.sidebar.radio[1].set_value('📋 Text Clipboard').run()
    _button(app,'Disable Clipboard').click().run()
    assert not app.exception


def test_live_mode_never_loads_fixture_results_and_displays_held_evaluation(monkeypatch):
    backend=create_app(Settings(TOKEN),scanner=TestScanner(),inspector=TestInspector(None),
        clipboard_adapter=UnsupportedClipboard(),
        transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'models':[]})))
    live_class=ui_client.HttpDevGuardClient
    with TestClient(backend,base_url='http://127.0.0.1:8765') as api:
        monkeypatch.setattr(ui_client,'HttpDevGuardClient',lambda base_url,token:
                            live_class(base_url,token,session=api))
        app=AppTest.from_file(APP,default_timeout=15).run()
        app.session_state['last_eval_result']={'simulated':True,'decision':'SANITIZE'}
        app.session_state['session_token']=TOKEN
        app.sidebar.radio[0].set_value('Live Mode (FastAPI Backend)').run()
        assert not app.exception
        app.sidebar.radio[1].set_value('🛡️ Privacy Gate').run()
        assert not app.metric
        assert any('No evaluation' in item.value for item in app.info)
        for view in VIEWS:
            app.sidebar.radio[1].set_value(view).run()
            assert not app.exception
        app.sidebar.radio[1].set_value('🛡️ Privacy Gate').run()
        button=next(button for button in app.button if 'Evaluate with DevGuard' in button.label)
        button.click().run()
        assert not app.exception
        assert app.session_state['last_eval_result']['decision']=='REVIEW'
        assert app.session_state['last_eval_result']['safe_preview'] is None
        assert not app.session_state['last_eval_result'].get('simulated')


def _button(app, label):
    return next(button for button in app.button if label in button.label)


def test_failed_replacement_evaluation_clears_previous_release_card(monkeypatch):
    client = ui_client.FixtureDevGuardClient()
    monkeypatch.setattr(client, 'is_fixture_mode', lambda: False)
    evaluate = client.evaluate_privacy

    def evaluated(**kwargs):
        result = evaluate(**kwargs)
        result.pop('simulated')
        return result

    monkeypatch.setattr(client, 'evaluate_privacy', evaluated)
    monkeypatch.setattr(ui_client, 'HttpDevGuardClient', lambda **kwargs: client)
    app = AppTest.from_file(APP, default_timeout=15).run()
    app.sidebar.radio[0].set_value('Live Mode (FastAPI Backend)').run()
    app.sidebar.radio[1].set_value('🛡️ Privacy Gate').run()
    next(item for item in app.text_input if item.label=='Configured Destination').set_value('configured-coding-client')
    # Use synthetic responses to exercise display state, not model accuracy.
    _button(app, 'Evaluate with DevGuard').click().run()
    assert any('Authorize Delivery' in button.label for button in app.button)

    def unavailable(**kwargs):
        raise ui_client.ServiceUnavailableError()

    monkeypatch.setattr(client, 'evaluate_privacy', unavailable)
    _button(app, 'Evaluate with DevGuard').click().run()
    assert not app.exception
    assert app.error
    assert 'last_eval_result' not in app.session_state
    assert not app.metric
    assert not any('Authorize Delivery' in button.label for button in app.button)


@pytest.mark.parametrize('status,decision', [
    ('CHECKING', 'ALLOW'), ('FAILED', 'SANITIZE'), ('EXPIRED', 'ALLOW'),
    (None, 'ALLOW'), ('READY', 'LOCAL_ONLY'),
])
def test_incomplete_or_local_only_evaluations_offer_no_release(status, decision):
    from copy import deepcopy
    from devguard.ui.fixtures import SYNTHETIC_PRIVACY_EVALUATION

    app = AppTest.from_file(APP, default_timeout=15).run()
    app.sidebar.radio[1].set_value('🛡️ Privacy Gate').run()
    result = deepcopy(SYNTHETIC_PRIVACY_EVALUATION)
    result['decision'] = decision
    if status is None:
        result.pop('status')
    else:
        result['status'] = status
    app.session_state['last_eval_result'] = result
    app.run()
    assert not app.exception
    assert not any('Authorize Delivery' in button.label for button in app.button)


def test_fixture_delivery_does_not_leak_into_new_dashboard_session():
    from devguard.ui.fixtures import SYNTHETIC_PRIVACY_EVALUATION

    app = AppTest.from_file(APP, default_timeout=15).run()
    app.sidebar.radio[1].set_value('🛡️ Privacy Gate').run()
    _button(app, 'Authorize Delivery').click().run()
    assert app.session_state['last_eval_result']['delivered'] is True
    assert app.session_state['last_eval_result']['receipt_id'].startswith('receipt-')
    assert SYNTHETIC_PRIVACY_EVALUATION['delivered'] is False
    fresh = AppTest.from_file(APP, default_timeout=15).run()
    fresh.sidebar.radio[1].set_value('🛡️ Privacy Gate').run()
    assert not fresh.exception
    assert any('Authorize Delivery' in button.label for button in fresh.button)


def _component_app(module, function):
    return AppTest.from_string(
        f'from devguard.ui.client import FixtureDevGuardClient\n'
        f'from devguard.ui.components.{module} import {function}\n'
        f'{function}(FixtureDevGuardClient())', default_timeout=15,
    )


@pytest.mark.parametrize('response,acknowledged', [
    ({'copied': True, 'content_version': 15}, True),
    ({'copied': False, 'content_version': 14}, False),
    ({}, False),
])
def test_cleaned_copy_displays_only_acknowledged_returned_version(monkeypatch, response, acknowledged):
    monkeypatch.setattr(ui_client.FixtureDevGuardClient, 'copy_cleaned_clipboard',
                        lambda self, expected_version: response)
    app = _component_app('clipboard_view', 'render_clipboard_view').run()
    _button(app, 'Copy Cleaned Text').click().run()
    assert not app.exception
    if acknowledged:
        assert any('version is 15' in item.value for item in app.success)
    else:
        assert not app.success
        assert any('COPY_NOT_ACKNOWLEDGED' in item.value for item in app.error)


@pytest.mark.parametrize('action,label,error', [
    ('apply_patch', 'Apply Patch', 'PATCH_NOT_APPLIED'),
    ('reject_patch', 'Reject Candidate', 'PATCH_NOT_REJECTED'),
])
def test_patch_actions_do_not_report_unacknowledged_success(monkeypatch, action, label, error):
    monkeypatch.setattr(ui_client.FixtureDevGuardClient, action, lambda *args, **kwargs: {})
    app = _component_app('incident_view', 'render_incident_view').run()
    _button(app, label).click().run()
    assert not app.exception
    assert not app.success
    assert any(error in item.value for item in app.error)


def test_capture_disable_requires_backend_acknowledgement(monkeypatch):
    monkeypatch.setattr(ui_client.FixtureDevGuardClient, 'is_fixture_mode', lambda self: False)
    monkeypatch.setattr(ui_client.FixtureDevGuardClient, 'disable_clipboard', lambda self: {})
    app = _component_app('clipboard_view', 'render_clipboard_view').run()
    _button(app, 'Disable Capture').click().run()
    assert not app.exception
    assert not any(item.value == 'Capture disabled.' for item in app.info)
    assert any('CAPTURE_NOT_DISABLED' in item.value for item in app.error)


def test_unverified_live_backend_stops_before_input_or_action_controls(monkeypatch):
    client = ui_client.FixtureDevGuardClient()
    monkeypatch.setattr(client, 'is_fixture_mode', lambda: False)
    def unavailable():
        raise ui_client.DevGuardError('Use fixture mode', code='LIVE_BACKEND_UNVERIFIED')
    monkeypatch.setattr(client, 'get_health', unavailable)
    monkeypatch.setattr(ui_client, 'HttpDevGuardClient', lambda **kwargs: client)
    app = AppTest.from_file(APP, default_timeout=15).run()
    app.sidebar.radio[0].set_value('Live Mode (FastAPI Backend)').run()
    assert not app.exception
    assert any('LIVE_BACKEND_UNVERIFIED' in item.value for item in app.error)
    assert not any('Evaluate with DevGuard' in button.label for button in app.button)
    assert not app.text_area
