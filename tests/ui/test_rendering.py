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
    app.button[0].click().run()
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
