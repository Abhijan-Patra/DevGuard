"""The public tour must render without enrolling local operator capabilities."""
from pathlib import Path
from streamlit.testing.v1 import AppTest
from devguard.ui.public_demo import public_document


def test_public_tour_never_reads_local_token_and_keeps_provenance(monkeypatch):
    monkeypatch.setenv('DEVGUARD_PUBLIC_DEMO','1')
    def forbidden(*args,**kwargs):raise AssertionError('Public renderer attempted local enrollment')
    monkeypatch.setattr('devguard.ui.session.load_local_token',forbidden)
    app=AppTest.from_file(Path(__file__).resolve().parents[2]/'devguard/ui/app.py',default_timeout=20).run()
    assert not app.exception
    assert not app.sidebar.radio
    assert not any(item.label=='Connect on this Mac' for item in app.button)
    document=public_document()
    assert 'data-public-demo="1"' in document
    assert 'PUBLIC READ-ONLY FEATURE TOUR' in document
    assert 'PUBLIC_TOUR_READ_ONLY' in document
    assert 'actual_receiver_matched_preview' in document
    assert 'decision_matches_expectation' in document
