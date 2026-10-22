"""Local launcher wiring; no real token or native clipboard is read."""

from types import SimpleNamespace

import pytest

from integrations import local_dashboard


def test_launcher_reuses_token_in_session_memory_without_printing(monkeypatch, capsys):
    state = {}
    calls = []
    monkeypatch.chdir(local_dashboard.Path(__file__).resolve().parents[2])
    ui = SimpleNamespace(session_state=state)
    monkeypatch.setenv("DEVGUARD_LOCAL_API_PORT", "8766")
    monkeypatch.setattr(
        local_dashboard,
        "session_token",
        lambda: "synthetic-launcher-unit-token-long-enough",
    )
    monkeypatch.setattr(
        local_dashboard.runpy,
        "run_path",
        lambda path, **kwargs: calls.append((path, kwargs)),
    )
    local_dashboard.main(ui)
    assert state["app_mode"] == "Live Mode (FastAPI Backend)"
    assert state["backend_url"] == "http://127.0.0.1:8766/api/v1"
    assert state["session_token"] == "synthetic-launcher-unit-token-long-enough"
    assert local_dashboard.Path(calls[0][0]).as_posix().endswith("devguard/ui/app.py")
    assert not capsys.readouterr().out


def test_launcher_stops_on_missing_private_session_without_reflecting_errors(
    monkeypatch,
):
    messages = []
    monkeypatch.chdir(local_dashboard.Path(__file__).resolve().parents[2])

    def stop():
        raise RuntimeError("stopped")

    def unavailable():
        raise OSError("synthetic-private-detail")

    ui = SimpleNamespace(error=messages.append, stop=stop)
    monkeypatch.setattr(local_dashboard, "session_token", unavailable)
    with pytest.raises(RuntimeError, match="stopped"):
        local_dashboard.main(ui)
    assert messages == ["The private local operator session is unavailable."]
