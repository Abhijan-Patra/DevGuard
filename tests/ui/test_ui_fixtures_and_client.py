"""Unit tests for DevGuard UI client, synthetic fixtures, and error handling.

Owner: Windows 1 (Antigravity).
Validates UI display client contracts, fixture integrity, and error mapping
per docs/API_CONTRACT.md, docs/tasks/WINDOWS_1_DASHBOARD.md, and docs/COVERAGE.md.
"""

import unittest
from devguard.ui.client import (
    AuthenticationError,
    DevGuardError,
    FixtureDevGuardClient,
    HttpDevGuardClient,
    StaleContentError,
)
from devguard.ui.fixtures import FIXTURE_BANNER_TEXT, SYNTHETIC_COVERAGE


class TestDevGuardUIFixturesAndClient(unittest.TestCase):
    """Test suite for UI client, presentation fixtures, and contract adherence."""

    def setUp(self) -> None:
        self.client = FixtureDevGuardClient()

    def test_fixture_mode_flag(self) -> None:
        """Fixture client must always explicitly identify as running in fixture mode."""
        self.assertTrue(self.client.is_fixture_mode())
        self.assertIn("FIXTURE MODE", FIXTURE_BANNER_TEXT)

    def test_health_schema(self) -> None:
        """Health check response must provide readiness and pinned model information."""
        health = self.client.get_health()
        self.assertEqual(health.get("status"), "ok")
        self.assertTrue(health.get("model_ready"))
        self.assertEqual(health.get("model_name"), "gemma4:e4b")
        self.assertIn("sha256:", health.get("model_digest", ""))

    def test_coverage_matrix_honesty(self) -> None:
        """Coverage matrix must not contain premature VERIFIED claims and must mark unsupported paths."""
        coverage = self.client.get_coverage()
        self.assertGreater(len(coverage), 5)

        capabilities = {c["capability"]: c for c in coverage}

        # Validate that Windows host native capture is honestly declared UNSUPPORTED
        self.assertIn("Windows host native clipboard capture", capabilities)
        win_cap = capabilities["Windows host native clipboard capture"]
        self.assertEqual(win_cap["status"], "UNSUPPORTED")
        self.assertIn("remote viewer", win_cap["limitations"].lower())

        # Validate that screenshots/recordings are UNSUPPORTED by design
        self.assertIn("Screenshots & screen recordings", capabilities)
        self.assertEqual(capabilities["Screenshots & screen recordings"]["status"], "UNSUPPORTED")

        # In initial state, no capability should be marked VERIFIED without proof
        verified_entries = [c for c in coverage if c["status"] == "VERIFIED"]
        self.assertEqual(len(verified_entries), 0, "Initial package must not claim VERIFIED without real test runs")

    def test_clipboard_status_and_stale_detection(self) -> None:
        """Clipboard actions must handle version checks and 409 stale conflict."""
        clip = self.client.get_clipboard_status()
        self.assertIn("capture_host_id", clip)
        self.assertIn("state", clip)
        self.assertIn("content_version", clip)
        self.assertIn("safe_preview", clip)

        # Ensure raw clipboard text/history is not exposed
        self.assertNotIn("raw_history", clip)
        self.assertNotIn("raw_text", clip)

        current_ver = clip["content_version"]

        # Attempting to copy cleaned text with outdated version must raise StaleContentError (409)
        with self.assertRaises(StaleContentError):
            self.client.copy_cleaned_clipboard(expected_version=current_ver - 1)

        # Copying with matching version succeeds
        res = self.client.copy_cleaned_clipboard(expected_version=current_ver)
        self.assertEqual(res.get("status"), "copied")
        self.assertEqual(res.get("content_version"), current_ver)

    def test_clipboard_lifecycle(self) -> None:
        """Disabling clipboard clears safe preview and sets state to OFF."""
        self.client.enable_clipboard("mac-host-01")
        status_after_enable = self.client.get_clipboard_status()
        self.assertTrue(status_after_enable["enabled"])

        self.client.disable_clipboard()
        status_after_disable = self.client.get_clipboard_status()
        self.assertFalse(status_after_disable["enabled"])
        self.assertEqual(status_after_disable["state"], "OFF")
        self.assertEqual(status_after_disable["safe_preview"], "")

    def test_privacy_evaluation_and_delivery(self) -> None:
        """Privacy gate must sanitize sensitive tokens and require explicit delivery authorization."""
        # Test input with secret
        eval_result = self.client.evaluate_privacy(
            project_id="test-proj",
            task="diagnose issue",
            surface="explicit_prompt",
            destination_id="test-dest",
            content_version=1,
            text="Here is my secret token: ghp_1234567890",
        )
        self.assertEqual(eval_result["decision"], "SANITIZE")
        self.assertIn("HIGH_ENTROPY_SECRET", eval_result["reason_codes"])
        self.assertFalse(eval_result["delivered"])

        # Test delivery authorization
        req_id = eval_result["request_id"]
        delivery = self.client.deliver_request(req_id)
        self.assertTrue(delivery["delivered"])
        self.assertIn("receipt_id", delivery)

    def test_incident_and_patch_review_authority(self) -> None:
        """Applying a patch must check base hash authority and prevent stale application."""
        incidents = self.client.get_incidents()
        self.assertGreater(len(incidents), 0)

        patch = self.client.get_patch("patch-synthetic-901")
        self.assertEqual(patch["status"], "READY_FOR_REVIEW")
        self.assertIn("--- a/", patch["diff"])
        self.assertIn("+++ b/", patch["diff"])

        # Attempt to apply with mismatched base hash must raise StaleContentError
        with self.assertRaises(StaleContentError):
            self.client.apply_patch(patch["patch_id"], expected_hash="wrong-stale-hash")

        # Applying with matching base hash succeeds
        apply_res = self.client.apply_patch(patch["patch_id"], expected_hash=patch["base_hash"])
        self.assertEqual(apply_res["status"], "APPLIED")

    def test_audit_event_stream_fields(self) -> None:
        """Audit log events must include required contract fields without raw sensitive payload."""
        events_resp = self.client.get_events()
        events = events_resp.get("events", [])
        self.assertGreater(len(events), 0)

        for ev in events:
            self.assertIn("schema_version", ev)
            self.assertIn("event_id", ev)
            self.assertIn("timestamp", ev)
            self.assertIn("kind", ev)
            self.assertIn("state", ev)
            self.assertIn("severity", ev)
            self.assertIn("redacted_summary", ev)
            self.assertNotIn("raw_payload", ev)
            self.assertNotIn("secret", ev.get("redacted_summary", "").lower())


if __name__ == "__main__":
    unittest.main()
