"""Synthetic clipboard adapter tests; these never read the user's clipboard."""

import asyncio
import pytest

from devguard.clipboard.service import ClipboardService
from devguard.guard.engine import GuardEngine, GuardError
from devguard.guard.scanner import ScanResult, baseline_spans
from devguard.schemas.guard import Decision, ModelProposal
from devguard.storage.audit import AuditStore


class FakeClipboard:
    available = True
    def __init__(self):
        self.change, self.text, self.reads, self.writes = 0, "initial private text", 0, 0
    def counter(self):
        return self.change
    def read_text(self, limit):
        self.reads += 1
        return ("NON_TEXT", None) if self.text is None else ("TEXT", self.text)
    def copy(self, text):
        self.change += 1
        self.text = text
    def write_text(self, expected, text):
        if expected != self.change:
            return None
        self.copy(text)
        self.writes += 1
        return self.change


class FakeScanner:
    available = True
    async def scan(self, text):
        return ScanResult(baseline_spans(text), complete=True)


class FakeInspector:
    def __init__(self):
        self.calls = 0
    async def inspect(self, text, task):
        self.calls += 1
        return ModelProposal(decision=Decision.ALLOW, spans=[])


def setup(inspector=None, clock=None):
    adapter, audit = FakeClipboard(), AuditStore()
    inspector = inspector or FakeInspector()
    options = {"clock": clock} if clock else {}
    guard = GuardEngine(FakeScanner(), inspector, audit, **options)
    clipboard = ClipboardService(adapter, guard, audit, debounce=0, **options)
    return clipboard, adapter, guard, inspector


async def settle(clipboard):
    if clipboard._job:
        await clipboard._job


def test_disabled_unchanged_and_initial_clipboard_are_not_read():
    async def run():
        clipboard, adapter, guard, inspector = setup()
        await clipboard.poll_once()
        assert adapter.reads == 0
        with pytest.raises(GuardError, match="CONSENT"):
            await clipboard.enable(consent=False)
        await clipboard.enable(consent=True)
        for _ in range(10):
            await clipboard.poll_once()
        assert adapter.reads == 0 and inspector.calls == 0
        await clipboard.disable()
        adapter.copy("new private copy")
        await clipboard.poll_once()
        assert adapter.reads == 0
    asyncio.run(run())


def test_duplicate_content_reuses_short_lived_decision_and_own_write_does_not_loop():
    async def run():
        clipboard, adapter, guard, inspector = setup()
        await clipboard.enable(consent=True, task="Debug login")
        adapter.copy("password=synthetic-only-value-876543; stack at line 42")
        await clipboard.poll_once()
        await settle(clipboard)
        assert clipboard.status()["state"] == "SENSITIVE"
        assert "synthetic-only" not in clipboard.status()["safe_preview"]
        adapter.copy(adapter.text)
        await clipboard.poll_once()
        assert inspector.calls == 1
        version = clipboard.version
        result = await clipboard.copy_cleaned(version)
        assert result["copied"] and adapter.writes == 1 and "synthetic-only" not in adapter.text
        reads = adapter.reads
        await clipboard.poll_once()
        assert adapter.reads == reads and inspector.calls == 1
        await clipboard.disable()
        assert not guard.records
    asyncio.run(run())


def test_new_copy_wins_and_stale_copy_action_never_overwrites_it():
    async def run():
        clipboard, adapter, guard, inspector = setup()
        await clipboard.enable(consent=True)
        adapter.copy("first benign copy")
        await clipboard.poll_once()
        await settle(clipboard)
        old_version = clipboard.version
        adapter.copy("newer user content not yet polled")
        with pytest.raises(GuardError, match="STALE_CLIPBOARD"):
            await clipboard.copy_cleaned(old_version)
        assert adapter.text == "newer user content not yet polled" and adapter.writes == 0
        await clipboard.poll_once()
        await settle(clipboard)
        with pytest.raises(GuardError, match="STALE_CLIPBOARD"):
            await clipboard.copy_cleaned(old_version)
        await clipboard.disable()
    asyncio.run(run())


def test_disabling_cancels_inflight_analysis_and_discards_late_results():
    async def run():
        entered = asyncio.Event()
        class WaitingInspector:
            async def inspect(self, text, task):
                entered.set()
                await asyncio.Event().wait()
        clipboard, adapter, guard, inspector = setup(WaitingInspector())
        await clipboard.enable(consent=True)
        adapter.copy("sensitive pending input")
        await clipboard.poll_once()
        await entered.wait()
        await clipboard.disable()
        assert clipboard.status()["state"] == "OFF" and not guard.records
        assert adapter.writes == 0
    asyncio.run(run())


def test_oversize_binary_and_expired_copy_are_never_declared_safe():
    async def run():
        now = [0]
        clipboard, adapter, guard, inspector = setup(clock=lambda: now[0])
        await clipboard.enable(consent=True)
        for text in ("X" * (32 * 1024 + 1), None, ""):
            adapter.copy(text)
            await clipboard.poll_once()
            assert clipboard.status()["state"] == "SKIPPED"
        assert inspector.calls == 0
        adapter.copy("benign copy")
        await clipboard.poll_once()
        await settle(clipboard)
        assert clipboard.status()["can_copy_cleaned"]
        now[0] = 61
        assert clipboard.status()["state"] == "REVIEW"
        assert not clipboard.status()["can_copy_cleaned"]
        assert not guard.records
        await clipboard.disable()
    asyncio.run(run())


def test_sensitive_copy_returns_placeholder_preview_and_copy_uses_only_approved_bytes():
    async def run():
        clipboard, adapter, guard, _ = setup()
        await clipboard.enable(consent=True)
        adapter.copy('password=synthetic-clipboard-credential-982401')
        await clipboard.poll_once(); await settle(clipboard)
        status=clipboard.status()
        assert status['state']=='SENSITIVE' and status['preview_kind']=='SANITIZED'
        assert status['display_preview']==status['safe_preview']
        assert '[CREDENTIAL_1]' in status['display_preview']
        assert 'synthetic-clipboard-credential' not in str(status)
        assert status['can_copy_cleaned'] and adapter.writes==0
        await clipboard.copy_cleaned(status['content_version'])
        assert adapter.text==status['safe_preview'] and adapter.writes==1
        await clipboard.disable()
        assert clipboard.status()['display_preview'] is None
    asyncio.run(run())


@pytest.mark.parametrize('decision',[Decision.REVIEW,Decision.BLOCK,Decision.LOCAL_ONLY])
def test_held_sensitive_copy_shows_whole_copy_marker_without_granting_copy_authority(decision):
    async def run():
        class HeldInspector:
            async def inspect(self,text,task):
                return ModelProposal(decision=decision,spans=[])
        clipboard,adapter,guard,_=setup(HeldInspector())
        await clipboard.enable(consent=True)
        adapter.copy('password=synthetic-hidden-clipboard-502938; private prose')
        await clipboard.poll_once();await settle(clipboard)
        status=clipboard.status()
        assert status['safe_preview'] is None and not status['can_copy_cleaned']
        assert status['display_preview']=='[SENSITIVE_CONTENT_REMOVED]'
        assert status['preview_kind']=='WITHHELD' and 'private prose' not in str(status)
        with pytest.raises(GuardError,match='CLIPBOARD_INSPECTION_HELD'):
            await clipboard.copy_cleaned(status['content_version'])
        assert adapter.writes==0
        await clipboard.disable()
    asyncio.run(run())


def test_expiry_hides_old_approved_preview_and_new_copy_clears_display_marker():
    async def run():
        now=[0]
        clipboard,adapter,guard,_=setup(clock=lambda:now[0])
        await clipboard.enable(consent=True)
        adapter.copy('password=synthetic-expiring-copy-378401')
        await clipboard.poll_once();await settle(clipboard)
        assert clipboard.status()['preview_kind']=='SANITIZED'
        now[0]=61
        expired=clipboard.status()
        assert expired['display_preview']=='[INSPECTION_EXPIRED]'
        assert expired['safe_preview'] is None and not expired['can_copy_cleaned']
        adapter.copy('new ordinary public text')
        await clipboard.poll_once()
        assert clipboard.status()['display_preview'] is None
        await settle(clipboard)
        assert clipboard.status()['display_preview']=='new ordinary public text'
        assert clipboard.status()['preview_kind']=='APPROVED'
        await clipboard.disable()
    asyncio.run(run())
