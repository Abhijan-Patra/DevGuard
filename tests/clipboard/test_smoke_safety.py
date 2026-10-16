"""Consent boundary for the manual native smoke, with no pasteboard access."""

import asyncio

from devguard.clipboard import smoke


def test_system_clipboard_smoke_requires_explicit_consent_before_native_construction(monkeypatch):
    def forbidden():
        raise AssertionError("Native clipboard was constructed without operator consent")

    monkeypatch.setattr(smoke, "MacClipboard", forbidden)
    report, code = asyncio.run(smoke.run(use_system=True, consent=False))
    assert code == 2
    assert report["status"] == "EXPLICIT_SYSTEM_CLIPBOARD_CONSENT_REQUIRED"
    assert report["general_clipboard_accessed"] is False
