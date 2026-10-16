"""Real Cocoa + local model check using a private synthetic pasteboard only.

Defaults to a unique private board and never inspects existing user content.
Does not enable capture in a running DevGuard app. Run explicitly with
``python -m devguard.clipboard.smoke`` on the enrolled Mac. The separate
``--system-clipboard --consent`` option requires operator approval, replaces
the clipboard with synthetic text, and disables the test service afterward.
Avoid other copy operations during that controlled test.
"""

import argparse
import asyncio
import json
import platform
import sys
import time

from devguard.clipboard.native import MacClipboard
from devguard.clipboard.service import ClipboardService
from devguard.config import Settings
from devguard.guard.context import ContextInspector
from devguard.guard.engine import GuardEngine, GuardError
from devguard.guard.scanner import CredentialScanner
from devguard.models.ollama import OllamaClient
from devguard.storage.audit import AuditStore


async def run(*, use_system=False, consent=False):
    report = {"scope": "Private named NSPasteboard; declared synthetic data only",
              "general_clipboard_accessed": False, "macOS": platform.mac_ver()[0]}
    if use_system and not consent:
        return {**report, "status": "EXPLICIT_SYSTEM_CLIPBOARD_CONSENT_REQUIRED"}, 2
    if use_system:
        report["scope"] = "Operator-consented system NSPasteboard; declared synthetic copies only"
    if sys.platform != "darwin":
        return {**report, "status": "UNSUPPORTED"}, 2
    try:
        adapter = MacClipboard()
        # A unique named board is independent of the user's general clipboard.
        adapter.board = (adapter.appkit.NSPasteboard.generalPasteboard() if use_system else
                         adapter.appkit.NSPasteboard.pasteboardWithUniqueName())
        report["general_clipboard_accessed"] = use_system
        if adapter.board is None:
            return {**report, "status": "UNAVAILABLE"}, 2
    except (ImportError, OSError):
        return {**report, "status": "UNAVAILABLE"}, 2

    model = OllamaClient(Settings("synthetic-native-smoke-not-an-operator-token-000"))
    audit = AuditStore()
    guard = GuardEngine(CredentialScanner(), ContextInspector(model), audit)
    clipboard = ClipboardService(adapter, guard, audit, debounce=0.25)
    reads = [0]
    fixture_counter = [None]
    read = adapter.read_text

    def counted_read(limit):
        reads[0] += 1
        return read(limit)

    adapter.read_text = counted_read

    def copy_synthetic(text, kind=None):
        with adapter.objc.autorelease_pool():
            adapter.board.clearContents()
            assert adapter.board.setString_forType_(text, kind or adapter.appkit.NSPasteboardTypeString)
            fixture_counter[0] = int(adapter.board.changeCount())

    async def settle():
        if clipboard._job:
            await asyncio.wait_for(clipboard._job, 30)

    checks = {}
    try:
        report["runtime"] = await model.inspect()
        if not report["runtime"]["model_ready"]:
            return {**report, "status": "MODEL_UNAVAILABLE"}, 2
        assert guard.scanner.available, "SCANNER_UNAVAILABLE"
        await clipboard.poll_once()
        checks["off_does_not_read"] = reads[0] == 0
        copy_synthetic("Declared initial synthetic item; do not inspect at enable")
        await clipboard.enable(consent=True, task="Debug the HTTP 500 at cart.py:17")
        await clipboard.poll_once()
        checks["enable_skips_existing_item"] = reads[0] == 0
        started, cpu = time.monotonic(), time.process_time()
        for _ in range(4):
            await asyncio.sleep(0.75)
            await clipboard.poll_once()
        report["unchanged_poll_wall_seconds"] = round(time.monotonic() - started, 3)
        report["unchanged_poll_process_cpu_seconds"] = round(time.process_time() - cpu, 4)
        checks["unchanged_counter_does_not_read"] = reads[0] == 0

        secret = "synthetic-native-fixture-710938"
        copy_synthetic(f"password={secret}; HTTP 500 at cart.py:17.")
        started = time.monotonic()
        await clipboard.poll_once()
        await settle()
        status = clipboard.status()
        preview = status["safe_preview"]
        report["copy_to_finding_seconds"] = round(time.monotonic() - started, 3)
        checks["real_model_cleaned_preview"] = (status["state"] == "SENSITIVE"
            and status["can_copy_cleaned"] and preview is not None
            and secret not in preview and "HTTP 500" in preview and "cart.py:17" in preview)
        assert checks["real_model_cleaned_preview"]
        previous = clipboard.version
        copied = await clipboard.copy_cleaned(previous)
        checks["native_cleaned_write"] = (copied["copied"] and copied["content_version"] > previous
                                          and read(32768) == ("TEXT", preview))
        before = reads[0]
        await clipboard.poll_once()
        checks["own_write_not_rescanned"] = reads[0] == before

        copy_synthetic("HTTP 500 at cart.py:17; second declared synthetic item")
        await clipboard.poll_once()
        await settle()
        previous = clipboard.version
        copy_synthetic("Newer declared synthetic copy; must remain unchanged")
        try:
            await clipboard.copy_cleaned(previous)
            checks["stale_write_rejected"] = False
        except GuardError as error:
            checks["stale_write_rejected"] = error.code == "STALE_CLIPBOARD"
        checks["newer_copy_preserved"] = read(32768) == ("TEXT", "Newer declared synthetic copy; must remain unchanged")

        copy_synthetic("x" * (32768 + 1))
        await clipboard.poll_once()
        checks["oversize_skipped"] = clipboard.status()["state"] == "SKIPPED"
        copy_synthetic("Declared non-text fixture", adapter.appkit.NSPasteboardTypePNG)
        await clipboard.poll_once()
        checks["nontext_skipped"] = clipboard.status()["state"] == "SKIPPED"

        await clipboard.disable()
        before = reads[0]
        copy_synthetic("Declared copy after capture disabled")
        await clipboard.poll_once()
        checks["disable_stops_reads_and_clears_records"] = reads[0] == before and not guard.records
        checks["audit_omits_synthetic_secret"] = secret not in json.dumps(audit.events())
        return {**report, "status": "PASS" if all(checks.values()) else "FAILED", "checks": checks}, (0 if all(checks.values()) else 1)
    except Exception:
        # No native exception text, input, previews or model content in reports.
        return {**report, "status": "FAILED", "checks": checks}, 1
    finally:
        await clipboard.disable()
        guard.close()
        audit.close()
        await model.close()
        with adapter.objc.autorelease_pool():
            # Never erase a newer external copy during cleanup.
            if not use_system or int(adapter.board.changeCount()) == fixture_counter[0]:
                adapter.board.clearContents()
            if not use_system:
                adapter.board.releaseGlobally()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system-clipboard", action="store_true",
                        help="Use the general clipboard; replaces its contents with synthetic text")
    parser.add_argument("--consent", action="store_true",
                        help="Explicit local operator consent for the controlled system clipboard test")
    args = parser.parse_args()
    report, code = asyncio.run(run(use_system=args.system_clipboard, consent=args.consent))
    print(json.dumps(report, indent=2))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
