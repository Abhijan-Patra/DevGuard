"""Synthetic presentation fixtures for DevGuard UI.

Owner: Windows 1 (Antigravity).
Per AGENTS.md, API_CONTRACT.md, and WINDOWS_1_DASHBOARD.md:
- These are declared synthetic presentation fixtures used for development and offline demo.
- They are NEVER to be treated as actual runtime classification or proof of model delivery.
- No real private inputs, secrets, or reversible maps are contained here.
"""

from typing import Any, Dict, List

FIXTURE_BANNER_TEXT = "FIXTURE MODE — simulated presentation data (not an actual model or gate outcome)"

SYNTHETIC_HEALTH: Dict[str, Any] = {
    "status": "ok",
    "model_ready": True,
    "model_name": "gemma4:e4b",
    "model_digest": "sha256:e4b_synthetic_pinned_trial_digest",
    "backend_version": "0.1.0-synthetic-fixture",
    "mode": "fixture",
}

SYNTHETIC_STATUS: Dict[str, Any] = {
    "worker_id": "worker-synthetic-mac1",
    "model_state": "READY",
    "model_name": "gemma4:e4b",
    "clipboard_watcher": "ACTIVE_SIMULATED",
    "enrolled_host": "mac-local-workstation-01",
    "windows_native_capture": "UNSUPPORTED",
    "capabilities": [
        "guard.evaluate",
        "guard.deliver",
        "clipboard.status",
        "clipboard.copy_cleaned",
        "repair.investigate",
        "repair.patch_review",
    ],
}

SYNTHETIC_COVERAGE: List[Dict[str, Any]] = [
    {
        "capability": "DevGuard explicit text/prompt gate",
        "client": "Local Reference Gate",
        "client_version": "v1-reference",
        "status": "UNIMPLEMENTED",
        "verified_at": None,
        "evidence_ref": None,
        "limitations": "First controlled reference path; evaluates and releases inspected bytes.",
    },
    {
        "capability": "macOS text clipboard capture",
        "client": "NSPasteboard Adapter",
        "client_version": "macOS 15.x",
        "status": "UNIMPLEMENTED",
        "verified_at": None,
        "evidence_ref": None,
        "limitations": "Advisory text watcher only until guarded send is invoked. Images/history excluded.",
    },
    {
        "capability": "Clipboard paste into unrelated app",
        "client": "System-wide",
        "client_version": "N/A",
        "status": "UNSUPPORTED",
        "verified_at": None,
        "evidence_ref": None,
        "limitations": "OS architecture does not permit universal paste blocking before analysis.",
    },
    {
        "capability": "Clipboard images/history collection",
        "client": "System-wide",
        "client_version": "N/A",
        "status": "UNSUPPORTED",
        "verified_at": None,
        "evidence_ref": None,
        "limitations": "Excluded by design. Only text in active capture budget is observed.",
    },
    {
        "capability": "Codex prompt submission hook",
        "client": "OpenAI Codex CLI",
        "client_version": "installed client check pending",
        "status": "UNVERIFIED",
        "verified_at": None,
        "evidence_ref": None,
        "limitations": "UserPromptSubmit tested for blocking/warning; does not imply arbitrary prompt rewrite.",
    },
    {
        "capability": "Codex selected tool calls hook",
        "client": "OpenAI Codex CLI",
        "client_version": "installed client check pending",
        "status": "UNVERIFIED",
        "verified_at": None,
        "evidence_ref": None,
        "limitations": "PreToolUse hook tested on file/shell; alternative access paths checked separately.",
    },
    {
        "capability": "Codex automatic context & transcripts",
        "client": "OpenAI Codex CLI",
        "client_version": "installed client check pending",
        "status": "UNVERIFIED",
        "verified_at": None,
        "evidence_ref": None,
        "limitations": "Do not claim complete wire-payload interception.",
    },
    {
        "capability": "Claude Code prompt/tool integration",
        "client": "Claude Code CLI",
        "client_version": "optional-mac",
        "status": "UNIMPLEMENTED",
        "verified_at": None,
        "evidence_ref": None,
        "limitations": "Optional evaluation path; no new commercial subscription required.",
    },
    {
        "capability": "Antigravity protected runtime gate",
        "client": "Antigravity IDE",
        "client_version": "current",
        "status": "UNSUPPORTED",
        "verified_at": None,
        "evidence_ref": None,
        "limitations": "Antigravity is development assistant for Windows UI; not a protected runtime client.",
    },
    {
        "capability": "Windows host native clipboard capture",
        "client": "Windows OS",
        "client_version": "Windows 11",
        "status": "UNSUPPORTED",
        "verified_at": None,
        "evidence_ref": None,
        "limitations": "Native capture is implemented for macOS only. Windows dashboard is a remote viewer.",
    },
    {
        "capability": "DevGuard guarded file/log tools",
        "client": "Internal runner",
        "client_version": "v1",
        "status": "UNIMPLEMENTED",
        "verified_at": None,
        "evidence_ref": None,
        "limitations": "Pre-delivery redaction on managed tools; unmanaged shell tools bypass this.",
    },
    {
        "capability": "Independent backend repair",
        "client": "Local Gemma 4 E4B",
        "client_version": "gemma4:e4b",
        "status": "UNIMPLEMENTED",
        "verified_at": None,
        "evidence_ref": None,
        "limitations": "Uses source, diffs, logs, and tests. No screenshot/video dependency.",
    },
    {
        "capability": "Screenshots & screen recordings",
        "client": "N/A",
        "client_version": "N/A",
        "status": "UNSUPPORTED",
        "verified_at": None,
        "evidence_ref": None,
        "limitations": "Excluded by design. Privacy-first architecture rejects screen capture.",
    },
    {
        "capability": "Pre-commit scanner",
        "client": "Git hook",
        "client_version": "pre-commit v3",
        "status": "UNIMPLEMENTED",
        "verified_at": None,
        "evidence_ref": None,
        "limitations": "Bypassable by developer; does not remediate past history.",
    },
]

SYNTHETIC_CLIPBOARD: Dict[str, Any] = {
    "capture_host_id": "mac-developer-workstation-01",
    "content_version": 14,
    "state": "SENSITIVE",
    "enabled": True,
    "redacted_summary": "High-entropy API token pattern detected and replaced with synthetic marker",
    "finding_ids": ["finding-clip-14a"],
    "can_copy_cleaned": True,
    "safe_preview": 'DATABASE_URL="postgres://app_user:REDACTED_PASSWORD_01@db.internal:5432/production"',
    "supported_type": "public.utf8-plain-text",
    "size_bytes": 84,
    "timestamp": "2026-10-16T12:00:00Z",
    "host_platform": "macOS (remote capture host)",
    "local_viewer_platform": "Windows (viewer only - local capture UNSUPPORTED)",
}

SYNTHETIC_PRIVACY_EVALUATION: Dict[str, Any] = {
    "request_id": "req-synthetic-privacy-77",
    "content_version": 7,
    "policy_revision": "policy-v1-synthetic",
    "destination_id": "configured-coding-client",
    "decision": "SANITIZE",
    "original_length": 112,
    "safe_preview": "ValueError at auth/login.py:42: Authentication failed for user customer_alpha@example.invalid with token [REDACTED_SECRET_TOKEN_1]",
    "reason_codes": ["PERSONAL_DATA", "HIGH_ENTROPY_SECRET"],
    "finding_ids": ["finding-77-email", "finding-77-token"],
    "status": "READY",
    "expires_at": "2026-10-16T12:30:00Z",
    "delivered": False,
    "surface": "explicit_prompt",
    "task": "Diagnose authentication exception in login handler",
}

SYNTHETIC_INCIDENTS: List[Dict[str, Any]] = [
    {
        "incident_id": "inc-synthetic-101",
        "project_id": "project-synthetic-core",
        "title": "ZeroDivisionError in metrics_collector.py during zero-traffic interval",
        "signal": "ZeroDivisionError: division by zero in calculate_error_rate() at metrics_collector.py:88",
        "source_revision": "git-commit-e12f34a",
        "status": "INVESTIGATING",
        "created_at": "2026-10-16T11:45:00Z",
        "active_run_id": "run-synthetic-501",
    },
    {
        "incident_id": "inc-synthetic-102",
        "project_id": "project-synthetic-core",
        "title": "Uncaught FileNotFoundError when cache directory is unmounted",
        "signal": "FileNotFoundError: [Errno 2] No such file or directory: '/var/cache/app/tokens.json'",
        "source_revision": "git-commit-b78c90d",
        "status": "READY_FOR_REVIEW",
        "created_at": "2026-10-16T10:15:00Z",
        "active_run_id": "run-synthetic-502",
    },
]

SYNTHETIC_RUN: Dict[str, Any] = {
    "run_id": "run-synthetic-502",
    "incident_id": "inc-synthetic-102",
    "state": "READY_FOR_REVIEW",
    "model_name": "gemma4:e4b",
    "model_digest": "sha256:e4b_synthetic_pinned_trial_digest",
    "safe_observations": [
        "Identified missing exist_ok=True and directory pre-check in CacheManager.load()",
        "Generated candidate patch targeting safe defensive directory creation",
        "Sandboxed pytest execution ran independent test test_cache_fallback: PASSED",
    ],
    "verification": {
        "status": "PASSED",
        "tests_passed": 3,
        "tests_failed": 0,
        "sandbox_id": "sandbox-synthetic-isolated-04",
        "test_evidence": "pytest trusted_tests/test_cache.py -> 3 passed in 0.42s",
    },
    "candidate_patch_id": "patch-synthetic-901",
    "base_hash": "b78c90de4f5a6b",
    "created_at": "2026-10-16T10:16:30Z",
    "completed_at": "2026-10-16T10:18:00Z",
}

SYNTHETIC_PATCH: Dict[str, Any] = {
    "patch_id": "patch-synthetic-901",
    "incident_id": "inc-synthetic-102",
    "target_file": "devguard/cache/manager.py",
    "base_hash": "b78c90de4f5a6b",
    "candidate_hash": "c89d01ef23a45b",
    "verification_summary": "Passed trusted test suite `trusted_tests/test_cache.py` in isolated sandbox.",
    "status": "READY_FOR_REVIEW",
    "diff": """--- a/devguard/cache/manager.py
+++ b/devguard/cache/manager.py
@@ -14,6 +14,9 @@ class CacheManager:
     def ensure_directory(self) -> None:
-        os.mkdir(self.cache_dir)
+        # Defensive check against unmounted or missing cache parent directories
+        os.makedirs(self.cache_dir, exist_ok=True)
 
     def load(self, key: str) -> Optional[dict]:
+        if not os.path.exists(self.cache_path):
+            return None
         with open(self.cache_path, "r", encoding="utf-8") as f:
             return json.load(f)
""",
}

SYNTHETIC_EVENTS: List[Dict[str, Any]] = [
    {
        "schema_version": "v1",
        "event_id": "evt-synthetic-001",
        "timestamp": "2026-10-16T11:50:00Z",
        "project_id": "project-synthetic-core",
        "kind": "clipboard.changed",
        "state": "CHECKING",
        "severity": "INFO",
        "redacted_summary": "macOS clipboard change detected (counter: 14, size: 84 bytes). Running fast pattern scanner.",
        "evidence_refs": ["finding-clip-14a"],
    },
    {
        "schema_version": "v1",
        "event_id": "evt-synthetic-002",
        "timestamp": "2026-10-16T11:50:01Z",
        "project_id": "project-synthetic-core",
        "kind": "clipboard.decision",
        "state": "SENSITIVE",
        "severity": "WARNING",
        "redacted_summary": "Sensitive pattern identified. Cleaned preview generated. Raw original held transiently.",
        "evidence_refs": ["finding-clip-14a"],
    },
    {
        "schema_version": "v1",
        "event_id": "evt-synthetic-003",
        "timestamp": "2026-10-16T11:55:00Z",
        "project_id": "project-synthetic-core",
        "kind": "guard.decision",
        "state": "READY",
        "severity": "WARNING",
        "redacted_summary": "Evaluated prompt for task 'login handler'. Decision: SANITIZE. Replaced 2 sensitive spans.",
        "evidence_refs": ["finding-77-email", "finding-77-token"],
    },
    {
        "schema_version": "v1",
        "event_id": "evt-synthetic-004",
        "timestamp": "2026-10-16T10:18:00Z",
        "project_id": "project-synthetic-core",
        "kind": "patch.state",
        "state": "READY_FOR_REVIEW",
        "severity": "INFO",
        "redacted_summary": "Sandboxed repair for incident inc-synthetic-102 passed trusted tests. Operator confirmation required.",
        "evidence_refs": ["patch-synthetic-901"],
    },
]
