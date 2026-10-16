"""Public hosting must never expose local operator enrolment."""
from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_public_demo_has_only_fixture_mode_and_all_views(monkeypatch):
    monkeypatch.setenv('DEVGUARD_PUBLIC_DEMO','1')
    app=AppTest.from_file(Path(__file__).resolve().parents[2]/'devguard/ui/app.py',default_timeout=20).run()
    assert not app.exception
    assert app.sidebar.radio[0].options==['Fixture Mode (Simulated)']
    assert not any(item.label=='Connect on this Mac' for item in app.button)
    assert any('PUBLIC INTERACTIVE DEMO' in item.value for item in app.info)
    for view in app.sidebar.radio[1].options:
        app.sidebar.radio[1].set_value(view).run()
        assert not app.exception
