"""Unit test for demo/mock_live_server.py demonstration harness."""

import json
from http.server import HTTPServer
import threading
import unittest
import urllib.request

from demo.mock_live_server import DevGuardMockHandler

TEST_PORT = 18765


class TestMockLiveServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", TEST_PORT), DevGuardMockHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _get(self, path):
        req = urllib.request.Request(f"http://127.0.0.1:{TEST_PORT}{path}")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def _post(self, path, payload):
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{TEST_PORT}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_health_endpoint(self):
        status, data = self._get("/health")
        self.assertEqual(status, 200)
        self.assertTrue(data["model_ready"])
        self.assertIn("gemma4", data["model_name"])

    def test_guard_evaluate_sanitizes_credentials(self):
        status, data = self._post("/api/v1/guard/evaluate", {
            "text": "Auth failure user test@enterprise.invalid with token ghp_secret12345",
            "destination_id": "local-preview",
            "content_version": 1,
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["decision"], "SANITIZE")
        self.assertIn("[REDACTED_SECRET_TOKEN_1]", data["safe_preview"])
        self.assertIn("[CUSTOMER_EMAIL_1]", data["safe_preview"])

    def test_guard_evaluate_benign_text(self):
        status, data = self._post("/api/v1/guard/evaluate", {
            "text": "def calculate_total(a, b): return a + b",
            "destination_id": "local-preview",
            "content_version": 1,
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["decision"], "ALLOW")

    def test_clipboard_status_and_copy_cleaned(self):
        status, data = self._get("/api/v1/clipboard/status")
        self.assertEqual(status, 200)
        self.assertIn("mac-m4-workstation", data["capture_host_id"])

        status, copy_res = self._post("/api/v1/clipboard/copy-cleaned", {"content_version": data["content_version"]})
        self.assertEqual(status, 200)
        self.assertTrue(copy_res["copied"])

    def test_http_client_status_envelope_compatibility(self):
        from devguard.ui.client import HttpDevGuardClient
        client = HttpDevGuardClient(base_url=f"http://127.0.0.1:{TEST_PORT}/api/v1")
        status = client.get_status()
        self.assertEqual(status["phase"], "GUARD_AND_CLIPBOARD_IMPLEMENTATION")
        self.assertTrue(status["runtime"]["model_ready"])
        self.assertEqual(status["runtime"]["model"], "gemma4:e4b-it-q4_K_M")

        health = client.get_health()
        self.assertTrue(health["model_ready"])
        self.assertEqual(health["model_name"], "gemma4:e4b-it-q4_K_M")


if __name__ == "__main__":
    unittest.main()
