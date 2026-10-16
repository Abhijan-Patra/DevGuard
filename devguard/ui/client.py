"""DevGuard display API client.

Owner: Windows 1 (Antigravity).
Provides client implementations for both synthetic fixture mode and
live backend mode consuming endpoints per docs/API_CONTRACT.md.
"""

from abc import ABC, abstractmethod
import json
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request


class DevGuardError(Exception):
    """Base exception for DevGuard client operations."""

    def __init__(self, message: str, code: Optional[str] = None, status_code: Optional[int] = None):
        super().__init__(message)
        self.code = code or "UNKNOWN_ERROR"
        self.status_code = status_code


class AuthenticationError(DevGuardError):
    """Raised on 401/403 authorization/session token errors."""

    def __init__(self, message: str = "Invalid or expired session token"):
        super().__init__(message, code="UNAUTHORIZED", status_code=401)


class StaleContentError(DevGuardError):
    """Raised on 409 conflict when content version or base hash has changed."""

    def __init__(self, message: str = "Content or base version changed; rescan required"):
        super().__init__(message, code="STALE_CONTENT", status_code=409)


class ServiceUnavailableError(DevGuardError):
    """Raised on 503 when Ollama, Gemma, or backend service is unavailable."""

    def __init__(self, message: str = "Required service or local model is currently unavailable"):
        super().__init__(message, code="SERVICE_UNAVAILABLE", status_code=503)


class BackendConnectionError(DevGuardError):
    """Raised when the backend server cannot be reached."""

    def __init__(self, message: str = "Could not connect to DevGuard backend server"):
        super().__init__(message, code="CONNECTION_FAILED", status_code=0)


class BaseDevGuardClient(ABC):
    """Abstract interface for DevGuard display client."""

    @abstractmethod
    def is_fixture_mode(self) -> bool:
        """Returns True if the client is running against synthetic fixture data."""
        pass

    @abstractmethod
    def get_health(self) -> Dict[str, Any]:
        """Check backend readiness and model status."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Fetch worker, capture, and model capability status."""
        pass

    @abstractmethod
    def get_coverage(self) -> List[Dict[str, Any]]:
        """Retrieve capability and client integration coverage matrix."""
        pass

    @abstractmethod
    def get_clipboard_status(self) -> Dict[str, Any]:
        """Fetch current enrolled host clipboard state and safe preview."""
        pass

    @abstractmethod
    def enable_clipboard(self, host_id: str, task: Optional[str] = None) -> Dict[str, Any]:
        """Enable text clipboard capture on target host."""
        pass

    @abstractmethod
    def disable_clipboard(self) -> Dict[str, Any]:
        """Disable clipboard capture and cancel pending scans."""
        pass

    @abstractmethod
    def copy_cleaned_clipboard(self, expected_version: int) -> Dict[str, Any]:
        """Trigger copy of cleaned text for expected version."""
        pass

    @abstractmethod
    def evaluate_privacy(
        self,
        project_id: str,
        task: str,
        surface: str,
        destination_id: str,
        content_version: int,
        text: str,
    ) -> Dict[str, Any]:
        """Submit text to privacy gate for evaluation."""
        pass

    @abstractmethod
    def deliver_request(self, request_id: str) -> Dict[str, Any]:
        """Trigger delivery of sanitized request to destination."""
        pass

    @abstractmethod
    def get_incidents(self) -> List[Dict[str, Any]]:
        """List active and reviewed bug incidents."""
        pass

    @abstractmethod
    def get_run(self, run_id: str) -> Dict[str, Any]:
        """Fetch details and verification status of a repair run."""
        pass

    @abstractmethod
    def get_patch(self, patch_id: str) -> Dict[str, Any]:
        """Fetch unified diff and verification summary for a patch candidate."""
        pass

    @abstractmethod
    def apply_patch(self, patch_id: str, expected_hash: str) -> Dict[str, Any]:
        """Operator action to apply candidate patch."""
        pass

    @abstractmethod
    def reject_patch(self, patch_id: str) -> Dict[str, Any]:
        """Operator action to reject candidate patch."""
        pass

    @abstractmethod
    def get_events(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Fetch audit log event stream."""
        pass


class FixtureDevGuardClient(BaseDevGuardClient):
    """Synthetic presentation client operating on declared test fixtures."""

    def __init__(self) -> None:
        from devguard.ui.fixtures import (
            SYNTHETIC_CLIPBOARD,
            SYNTHETIC_COVERAGE,
            SYNTHETIC_EVENTS,
            SYNTHETIC_HEALTH,
            SYNTHETIC_INCIDENTS,
            SYNTHETIC_PATCH,
            SYNTHETIC_PRIVACY_EVALUATION,
            SYNTHETIC_RUN,
            SYNTHETIC_STATUS,
        )

        self._health = dict(SYNTHETIC_HEALTH)
        self._status = dict(SYNTHETIC_STATUS)
        self._coverage = [dict(c) for c in SYNTHETIC_COVERAGE]
        self._clipboard = dict(SYNTHETIC_CLIPBOARD)
        self._privacy = dict(SYNTHETIC_PRIVACY_EVALUATION)
        self._incidents = [dict(i) for i in SYNTHETIC_INCIDENTS]
        self._run = dict(SYNTHETIC_RUN)
        self._patch = dict(SYNTHETIC_PATCH)
        self._events = [dict(e) for e in SYNTHETIC_EVENTS]

    def is_fixture_mode(self) -> bool:
        return True

    def get_health(self) -> Dict[str, Any]:
        return self._health

    def get_status(self) -> Dict[str, Any]:
        return self._status

    def get_coverage(self) -> List[Dict[str, Any]]:
        return self._coverage

    def get_clipboard_status(self) -> Dict[str, Any]:
        return self._clipboard

    def enable_clipboard(self, host_id: str, task: Optional[str] = None) -> Dict[str, Any]:
        self._clipboard["enabled"] = True
        self._clipboard["state"] = "CHECKING"
        self._clipboard["capture_host_id"] = host_id
        return {
            "status": "enabled",
            "capture_host_id": host_id,
            "simulated": True,
            "message": "Simulated local consent granted on fixture capture host.",
        }

    def disable_clipboard(self) -> Dict[str, Any]:
        self._clipboard["enabled"] = False
        self._clipboard["state"] = "OFF"
        self._clipboard["safe_preview"] = ""
        return {
            "status": "disabled",
            "simulated": True,
            "message": "Simulated clipboard capture stopped; transient buffers cleared.",
        }

    def copy_cleaned_clipboard(self, expected_version: int) -> Dict[str, Any]:
        if expected_version != self._clipboard["content_version"]:
            raise StaleContentError(
                f"Clipboard version mismatch (expected: {expected_version}, current: {self._clipboard['content_version']})"
            )
        return {
            "status": "copied",
            "content_version": expected_version,
            "simulated": True,
            "message": "Cleaned text copied to simulated clipboard buffer.",
        }

    def evaluate_privacy(
        self,
        project_id: str,
        task: str,
        surface: str,
        destination_id: str,
        content_version: int,
        text: str,
    ) -> Dict[str, Any]:
        # Return synthetic evaluation with redacted preview
        has_secret = any(k in text.lower() for k in ["secret", "password", "key", "token", "auth"])
        decision = "SANITIZE" if has_secret else "ALLOW"
        safe_preview = text
        reason_codes = []
        if has_secret:
            safe_preview = "[REDACTED_CREDENTIAL]"
            reason_codes.append("HIGH_ENTROPY_SECRET")

        return {
            "request_id": f"req-simulated-{content_version}",
            "content_version": content_version,
            "policy_revision": "policy-v1-simulated",
            "destination_id": destination_id,
            "decision": decision,
            "safe_preview": safe_preview,
            "reason_codes": reason_codes,
            "finding_ids": [f"finding-sim-{content_version}"],
            "status": "READY",
            "expires_at": "2026-10-16T13:00:00Z",
            "delivered": False,
            "simulated": True,
        }

    def deliver_request(self, request_id: str) -> Dict[str, Any]:
        if request_id == self._privacy.get("request_id"):
            self._privacy["delivered"] = True
        return {
            "request_id": request_id,
            "delivered": True,
            "simulated": True,
            "receipt_id": f"receipt-{request_id}",
        }

    def get_incidents(self) -> List[Dict[str, Any]]:
        return self._incidents

    def get_run(self, run_id: str) -> Dict[str, Any]:
        return self._run

    def get_patch(self, patch_id: str) -> Dict[str, Any]:
        return self._patch

    def apply_patch(self, patch_id: str, expected_hash: str) -> Dict[str, Any]:
        if expected_hash != self._patch.get("base_hash"):
            raise StaleContentError(
                f"Base hash mismatch (expected: {expected_hash}, current: {self._patch.get('base_hash')})"
            )
        self._patch["status"] = "APPLIED"
        self._run["state"] = "APPLIED"
        return {
            "patch_id": patch_id,
            "status": "APPLIED",
            "simulated": True,
            "message": "Patch applied successfully in simulated environment.",
        }

    def reject_patch(self, patch_id: str) -> Dict[str, Any]:
        self._patch["status"] = "REJECTED"
        self._run["state"] = "REJECTED"
        return {
            "patch_id": patch_id,
            "status": "REJECTED",
            "simulated": True,
            "message": "Patch candidate rejected by operator.",
        }

    def get_events(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        return {
            "events": self._events,
            "next_cursor": "cursor-simulated-end",
        }


class HttpDevGuardClient(BaseDevGuardClient):
    """Live HTTP display client connecting to FastAPI backend per API_CONTRACT.md."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000/api/v1", token: Optional[str] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def is_fixture_mode(self) -> bool:
        return False

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw_body = resp.read().decode("utf-8")
                if not raw_body:
                    return {}
                return json.loads(raw_body)
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="replace")
            err_code = "HTTP_ERROR"
            err_msg = f"HTTP {err.code}: {err.reason}"
            try:
                parsed = json.loads(err_body)
                if "error" in parsed:
                    err_code = parsed["error"].get("code", err_code)
                    err_msg = parsed["error"].get("message", err_msg)
            except Exception:
                pass

            if err.code in (401, 403):
                raise AuthenticationError(err_msg) from err
            elif err.code == 409:
                raise StaleContentError(err_msg) from err
            elif err.code == 503:
                raise ServiceUnavailableError(err_msg) from err
            else:
                raise DevGuardError(err_msg, code=err_code, status_code=err.code) from err
        except urllib.error.URLError as err:
            raise BackendConnectionError(f"Connection failed: {err.reason}") from err
        except Exception as err:
            raise DevGuardError(f"Unexpected transport error: {err}") from err

    def get_health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")

    def get_status(self) -> Dict[str, Any]:
        return self._request("GET", "/status")

    def get_coverage(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/coverage")

    def get_clipboard_status(self) -> Dict[str, Any]:
        return self._request("GET", "/clipboard/status")

    def enable_clipboard(self, host_id: str, task: Optional[str] = None) -> Dict[str, Any]:
        payload = {"capture_host_id": host_id, "task": task}
        return self._request("POST", "/clipboard/enable", payload)

    def disable_clipboard(self) -> Dict[str, Any]:
        return self._request("POST", "/clipboard/disable")

    def copy_cleaned_clipboard(self, expected_version: int) -> Dict[str, Any]:
        payload = {"expected_content_version": expected_version}
        return self._request("POST", "/clipboard/copy-cleaned", payload)

    def evaluate_privacy(
        self,
        project_id: str,
        task: str,
        surface: str,
        destination_id: str,
        content_version: int,
        text: str,
    ) -> Dict[str, Any]:
        payload = {
            "project_id": project_id,
            "task": task,
            "surface": surface,
            "destination_id": destination_id,
            "content_version": content_version,
            "text": text,
        }
        return self._request("POST", "/guard/evaluate", payload)

    def deliver_request(self, request_id: str) -> Dict[str, Any]:
        return self._request("POST", f"/guard/requests/{request_id}/deliver")

    def get_incidents(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/incidents")

    def get_run(self, run_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/runs/{run_id}")

    def get_patch(self, patch_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/patches/{patch_id}")

    def apply_patch(self, patch_id: str, expected_hash: str) -> Dict[str, Any]:
        payload = {"expected_base_hash": expected_hash}
        return self._request("POST", f"/patches/{patch_id}/apply", payload)

    def reject_patch(self, patch_id: str) -> Dict[str, Any]:
        return self._request("POST", f"/patches/{patch_id}/reject")

    def get_events(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        path = f"/events?after={cursor}" if cursor else "/events"
        return self._request("GET", path)
