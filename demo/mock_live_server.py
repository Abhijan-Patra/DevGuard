#!/usr/bin/env python3
"""DevGuard Mock Live Backend for Demonstration and Presentation Rehearsal.

Owner: Member 4 (Windows 2 - Scenarios, QA & Demo).
Provides a lightweight loopback API server on port 8765 that adheres
strictly to docs/API_CONTRACT.md and docs/INTEGRATION_STATUS.md.

Allows presenting the Streamlit Dashboard in 'Live Mode' without requiring
an active Apple Silicon GPU or Docker daemon.
"""

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import re
import sys
import threading
import uuid

PORT = 8765
TOKEN = "demo-operator-token"

# In-memory mock state for live demonstration
STATE = {
    "clipboard_version": 104,
    "clipboard_state": "SENSITIVE",
    "clipboard_enabled": True,
    "clipboard_preview": 'DATABASE_URL="postgres://demo_admin:REDACTED_PASSWORD_01@db.internal.invalid:5432/app_db"',
    "runs": {
        "run-live-demo-201": {
            "run_id": "run-live-demo-201",
            "incident_id": "inc-live-demo-01",
            "state": "READY_FOR_REVIEW",
            "model_name": "gemma4:e4b-it-q4_K_M",
            "model_digest": "sha256:e4b_pinned_trial_digest_m4",
            "safe_observations": [
                "Identified calculation bug in demo/backend/cart.py: line 8 adds unit price once instead of quantity * price",
                "Generated defensive candidate multiplying quantity and price",
                "Isolated Docker test runner executed trusted_tests/test_cart.py: 3 passed in 0.38s",
            ],
            "verification": {
                "status": "PASSED",
                "tests_passed": 3,
                "tests_failed": 0,
                "sandbox_id": "sandbox-docker-isolated-demo",
                "test_evidence": "pytest trusted_tests/test_cart.py (3/3 PASSED)",
            },
            "candidate_patch_id": "patch-live-demo-301",
            "base_hash": "base_hash_cart_initial",
            "created_at": "2026-10-16T12:00:00Z",
            "completed_at": "2026-10-16T12:01:30Z",
        }
    },
    "patches": {
        "patch-live-demo-301": {
            "patch_id": "patch-live-demo-301",
            "incident_id": "inc-live-demo-01",
            "target_file": "demo/backend/cart.py",
            "base_hash": "base_hash_cart_initial",
            "candidate_hash": "candidate_hash_cart_fixed",
            "verification_summary": "Passed trusted test suite `trusted_tests/test_cart.py` in isolated sandbox.",
            "status": "READY_FOR_REVIEW",
            "diff": """--- a/demo/backend/cart.py
+++ b/demo/backend/cart.py
@@ -6,3 +6,3 @@
-    total += item['price']
+    total += item['quantity'] * item['price']
""",
        }
    },
}


class DevGuardMockHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")

        # Health endpoint
        if path in ("/health", "/api/v1/health"):
            return self._send_json(200, {
                "status": "ok",
                "model_ready": True,
                "model_name": "gemma4:e4b-it-q4_K_M",
                "model_digest": "sha256:e4b_pinned_trial_digest_m4",
                "backend_version": "0.1.0-live-demo-server",
                "mode": "live-demo",
            })

        # Worker status
        if path == "/api/v1/status":
            return self._send_json(200, {
                "phase": "GUARD_AND_CLIPBOARD_IMPLEMENTATION",
                "runtime": {
                    "server_ready": True,
                    "server_version": "0.40.4",
                    "model": "gemma4:e4b-it-q4_K_M",
                    "model_ready": True,
                    "model_digest": "dc35e8d9c6061baa6f0fa870975ab6932e2542b579b13ea0f199fa4bb7300c9c",
                    "expected_model_digest": "dc35e8d9c6061baa6f0fa870975ab6932e2542b579b13ea0f199fa4bb7300c9c",
                    "reason_code": "MODEL_READY",
                },
                "inference_queue": {"queued": 0, "active": 0, "closed": False},
                "clipboard": {
                    "capture_host_id": "mac-m4-workstation",
                    "content_version": STATE["clipboard_version"],
                    "state": STATE["clipboard_state"],
                    "enabled": STATE["clipboard_enabled"],
                    "implemented": True,
                },
                "guard_implemented": True,
                "credential_scanner_available": True,
                "audit": {"durable": True, "retention_events": 5000},
                "repair_implemented": True,
                "repair": {
                    "configured": True,
                    "available": True,
                    "state": "PAUSED",
                    "reason_code": "MANUAL_IDLE",
                },
                "worker_id": "worker-live-demo-m4",
                "windows_native_capture": "UNSUPPORTED",
                "capabilities": ["guard.evaluate", "guard.deliver", "clipboard.status", "repair.investigate"],
            })

        # Clipboard status
        if path == "/api/v1/clipboard/status":
            return self._send_json(200, {
                "capture_host_id": "mac-m4-workstation",
                "content_version": STATE["clipboard_version"],
                "state": STATE["clipboard_state"],
                "enabled": STATE["clipboard_enabled"],
                "redacted_summary": "Sensitive API token detected in clipboard string" if STATE["clipboard_state"] == "SENSITIVE" else "Clipboard text clear for capture scope",
                "finding_ids": ["finding-clip-demo"],
                "can_copy_cleaned": STATE["clipboard_state"] == "SENSITIVE",
                "safe_preview": STATE["clipboard_preview"],
                "supported_type": "public.utf8-plain-text",
                "size_bytes": len(STATE["clipboard_preview"]),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "host_platform": "macOS 15.x (remote capture host)",
                "local_viewer_platform": "Windows (viewer only - local capture UNSUPPORTED)",
            })

        # Coverage view
        if path == "/api/v1/coverage":
            from devguard.ui.fixtures import SYNTHETIC_COVERAGE
            return self._send_json(200, SYNTHETIC_COVERAGE)

        # Incidents
        if path == "/api/v1/incidents":
            return self._send_json(200, {
                "incidents": [
                    {
                        "incident_id": "inc-live-demo-01",
                        "project_id": "demo",
                        "title": "Cart quantity calculation regression in demo/backend/cart.py",
                        "signal": "cart",
                        "source_revision": "base_hash_cart_initial",
                        "status": "READY_FOR_REVIEW",
                        "created_at": "2026-10-16T12:00:00Z",
                        "active_run_id": "run-live-demo-201",
                    }
                ]
            })

        # Run detail
        run_match = re.match(r"^/api/v1/runs/([a-zA-Z0-9_-]+)$", path)
        if run_match:
            run_id = run_match.group(1)
            run = STATE["runs"].get(run_id, STATE["runs"]["run-live-demo-201"])
            return self._send_json(200, run)

        # Patch detail
        patch_match = re.match(r"^/api/v1/patches/([a-zA-Z0-9_-]+)$", path)
        if patch_match:
            patch_id = patch_match.group(1)
            patch = STATE["patches"].get(patch_id, STATE["patches"]["patch-live-demo-301"])
            return self._send_json(200, patch)

        # Events stream
        if path == "/api/v1/events":
            from devguard.ui.fixtures import SYNTHETIC_EVENTS
            return self._send_json(200, {"events": SYNTHETIC_EVENTS, "next_cursor": "cursor-live-demo-end"})

        self._send_json(404, {"error": {"code": "NOT_FOUND", "message": f"Endpoint {path} not found"}})

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            payload = {}

        # Privacy Evaluate
        if path == "/api/v1/guard/evaluate":
            text = payload.get("text", "")
            req_id = "req-" + uuid.uuid4().hex[:12]

            # Detect credentials or PII dynamically
            is_sensitive = bool(re.search(r"(ghp_[a-zA-Z0-9]+|AKIA[0-9A-Z]{16}|postgres://|secret|token|password)", text, re.I))
            decision = "SANITIZE" if is_sensitive else "ALLOW"
            safe_text = re.sub(r"ghp_[a-zA-Z0-9]+", "[REDACTED_SECRET_TOKEN_1]", text)
            safe_text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[CUSTOMER_EMAIL_1]", safe_text)
            safe_text = re.sub(r"://([^:]+):([^@]+)@", r"://\1:[REDACTED_PASSWORD_01]@", safe_text)

            reason_codes = ["CREDENTIAL"] if is_sensitive else []
            if "@" in text:
                reason_codes.append("PERSONAL_DATA")

            return self._send_json(200, {
                "request_id": req_id,
                "content_version": payload.get("content_version", 1),
                "policy_revision": "policy-v1",
                "destination_id": payload.get("destination_id", "local-preview"),
                "decision": decision,
                "safe_preview": safe_text,
                "reason_codes": reason_codes,
                "finding_ids": [f"finding-{req_id}-01"] if is_sensitive else [],
                "status": "READY",
                "expires_at": datetime.now(timezone.utc).isoformat(),
                "delivered": False,
            })

        # Deliver Request
        deliver_match = re.match(r"^/api/v1/guard/requests/([a-zA-Z0-9_-]+)/deliver$", path)
        if deliver_match:
            req_id = deliver_match.group(1)
            return self._send_json(200, {
                "delivered": True,
                "receipt_id": f"receipt-{req_id}",
                "destination_id": payload.get("destination_id", "local-preview"),
                "content_version": payload.get("content_version", 1),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # Clipboard controls
        if path == "/api/v1/clipboard/enable":
            STATE["clipboard_enabled"] = True
            STATE["clipboard_state"] = "CHECKING"
            return self._send_json(200, {"enabled": True, "state": "CHECKING"})

        if path == "/api/v1/clipboard/disable":
            STATE["clipboard_enabled"] = False
            STATE["clipboard_state"] = "OFF"
            return self._send_json(200, {"enabled": False, "state": "OFF"})

        if path == "/api/v1/clipboard/copy-cleaned":
            STATE["clipboard_version"] += 1
            STATE["clipboard_state"] = "CLEAR_FOR_CAPTURE_SCOPE"
            return self._send_json(200, {
                "copied": True,
                "content_version": STATE["clipboard_version"],
                "state": "CLEAR_FOR_CAPTURE_SCOPE",
            })

        # Patch controls
        apply_match = re.match(r"^/api/v1/patches/([a-zA-Z0-9_-]+)/apply$", path)
        if apply_match:
            patch_id = apply_match.group(1)
            # Check for conflict simulation
            if payload.get("expected_base_revision") == "stale_hash":
                return self._send_json(409, {
                    "error": {
                        "code": "STALE_SOURCE",
                        "message": "Base file hash mismatch; source has been modified since candidate generation. Rescan required.",
                    }
                })
            return self._send_json(200, {
                "patch_id": patch_id,
                "status": "APPLIED",
                "applied_at": datetime.now(timezone.utc).isoformat(),
            })

        self._send_json(404, {"error": {"code": "NOT_FOUND", "message": f"Endpoint {path} not found"}})


def run_mock_server(port=PORT):
    server = HTTPServer(("127.0.0.1", port), DevGuardMockHandler)
    print(f"[*] DevGuard Mock Live Server listening on http://127.0.0.1:{port}/api/v1")
    print("    Ready for Streamlit 'Live Mode' demonstration without external dependencies.")
    print("    Press Ctrl+C to terminate.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down mock live server.")
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_mock_server(port)
