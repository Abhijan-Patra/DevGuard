"""DevGuard display API client.

Owner: Windows 1 (Antigravity).
Provides client implementations for both synthetic fixture mode and
live backend mode consuming endpoints per docs/API_CONTRACT.md.
"""

from abc import ABC, abstractmethod
from copy import deepcopy
import json
import re
from urllib.parse import urlsplit
import httpx
from typing import Any, Dict, List, Optional
from uuid import uuid4


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
    def enable_clipboard(self, host_id: str, task: Optional[str] = None, *, consent: bool = False) -> Dict[str, Any]:
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
    def deliver_request(self, request_id: str, *, content_version: Optional[int] = None, destination_id: Optional[str] = None) -> Dict[str, Any]:
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
    def apply_patch(self, patch_id: str, expected_hash: str, *, expected_base_revision: Optional[str] = None, idempotency_key: Optional[str] = None, approved: bool = False) -> Dict[str, Any]:
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

    def get_findings(self):
        raise DevGuardError('Findings are unavailable',code='FEATURE_UNAVAILABLE')

    def initialize_repair(self):
        raise DevGuardError('Repair controls are unavailable',code='FEATURE_UNAVAILABLE')

    def create_incident(self,project_id,signal):
        raise DevGuardError('Repair controls are unavailable',code='FEATURE_UNAVAILABLE')

    def investigate_incident(self,incident_id):
        raise DevGuardError('Repair controls are unavailable',code='FEATURE_UNAVAILABLE')

    def set_repair_idle(self,idle):
        raise DevGuardError('Repair controls are unavailable',code='FEATURE_UNAVAILABLE')

    def cancel_run(self,run_id):
        raise DevGuardError('Repair controls are unavailable',code='FEATURE_UNAVAILABLE')


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

        self._health = deepcopy(SYNTHETIC_HEALTH)
        self._status = deepcopy(SYNTHETIC_STATUS)
        self._coverage = deepcopy(SYNTHETIC_COVERAGE)
        self._clipboard = deepcopy(SYNTHETIC_CLIPBOARD)
        self._privacy = deepcopy(SYNTHETIC_PRIVACY_EVALUATION)
        self._incidents = deepcopy(SYNTHETIC_INCIDENTS)
        self._run = deepcopy(SYNTHETIC_RUN)
        self._patch = deepcopy(SYNTHETIC_PATCH)
        self._events = deepcopy(SYNTHETIC_EVENTS)
        self._repair={'configured':True,'available':True,'state':'PAUSED','reason_code':'SIMULATED'}
        self._queued_runs={}

    def is_fixture_mode(self) -> bool:
        return True

    def get_health(self) -> Dict[str, Any]:
        return self._health

    def get_status(self) -> Dict[str, Any]:
        return {**self._status,'repair':self._repair,
                'runtime':{'model_ready':self._health.get('model_ready'),
                           'model':self._health.get('model_name'),'model_digest':self._health.get('model_digest')},
                'audit':{'durable':False},'simulated':True}

    def get_coverage(self) -> List[Dict[str, Any]]:
        return self._coverage

    def get_clipboard_status(self) -> Dict[str, Any]:
        return self._clipboard

    def enable_clipboard(self, host_id: str, task: Optional[str] = None, *, consent: bool = False) -> Dict[str, Any]:
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
            "copied": True,
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
        # A declared presentation fixture is not a classifier. Never echo or
        # classify arbitrary typed text while the model is unavailable.
        result = deepcopy(self._privacy)
        result.update(request_id=f"req-simulated-{content_version}",
                      content_version=content_version, destination_id=destination_id,
                      delivered=False, simulated=True)
        return result

    def deliver_request(self, request_id: str, *, content_version: Optional[int] = None, destination_id: Optional[str] = None) -> Dict[str, Any]:
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
        return self._queued_runs.get(run_id,self._run)

    def get_patch(self, patch_id: str) -> Dict[str, Any]:
        return self._patch

    def apply_patch(self, patch_id: str, expected_hash: str, *, expected_base_revision: Optional[str] = None, idempotency_key: Optional[str] = None, approved: bool = False) -> Dict[str, Any]:
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

    def get_findings(self):
        return [deepcopy(self._privacy)]

    def initialize_repair(self):
        return {**self._repair,'simulated':True}

    def create_incident(self,project_id,signal):
        incident={'incident_id':'incident-simulated-'+uuid4().hex,'project_id':project_id,
                  'signal':signal,'title':'Synthetic named check: '+signal,'status':'OPEN',
                  'source_revision':'synthetic-presentation-revision','simulated':True}
        self._incidents.append(incident)
        return incident

    def investigate_incident(self,incident_id):
        incident=next(i for i in self._incidents if i['incident_id']==incident_id)
        run={'run_id':'run-simulated-'+uuid4().hex,'state':'QUEUED','verification':{'status':'NOT_RUN'},
             'completed_tools':[],'candidate_patch_id':None,'simulated':True}
        incident['active_run_id']=run['run_id']
        self._queued_runs[run['run_id']]=run
        return run

    def set_repair_idle(self,idle):
        self._repair['state']='RUNNING' if idle else 'PAUSED'
        return {'paused':not idle,'simulated':True}

    def cancel_run(self,run_id):
        run=self.get_run(run_id)
        run['state']='CANCELED'
        return run


class HttpDevGuardClient(BaseDevGuardClient):
    """Local display client; actions retain backend version/scope/approval checks."""

    def __init__(self, base_url: str = "http://127.0.0.1:8765/api/v1", token: Optional[str] = None, *, session=None) -> None:
        url = urlsplit(base_url)
        if (url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost", "::1"}
                or url.username or url.password or url.query or url.fragment
                or url.path.rstrip("/") != "/api/v1"):
            raise BackendConnectionError("Use the enrolled loopback API at http://127.0.0.1:8765/api/v1")
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = session

    def is_fixture_mode(self) -> bool:
        return False

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        try:
            if self.session is not None:
                response = self.session.request(method, self.base_url + path, headers=headers, json=payload)
            else:
                with httpx.Client(trust_env=False, follow_redirects=False, timeout=30) as session:
                    response = session.request(method, self.base_url + path, headers=headers, json=payload)
            if response.status_code >= 300:
                code = "HTTP_ERROR"
                try:
                    candidate = response.json().get("error", {}).get("code")
                    if isinstance(candidate, str) and re.fullmatch(r"[A-Z_]{1,60}", candidate):
                        code = candidate
                except (ValueError, AttributeError):
                    pass
                if response.status_code == 401:
                    raise AuthenticationError()
                if response.status_code == 409:
                    raise StaleContentError()
                if response.status_code == 503:
                    raise ServiceUnavailableError()
                raise DevGuardError("Action held by the local backend", code=code,
                                    status_code=response.status_code)
            return response.json() if response.content else {}
        except DevGuardError:
            raise
        except httpx.HTTPError:
            raise BackendConnectionError() from None
        except (ValueError, TypeError, AttributeError):
            raise DevGuardError("Backend returned an invalid response", code="INVALID_RESPONSE") from None

    def get_health(self) -> Dict[str, Any]:
        status = self.get_status()  # Authenticated readiness, including actual digest.
        runtime = status.get("runtime", {})
        return {"service_ready": True, "model_ready": runtime.get("model_ready", False),
                "status": "ready" if runtime.get("model_ready") else "model_unavailable",
                "model_name": runtime.get("model"), "model_digest": runtime.get("model_digest")}

    def get_status(self) -> Dict[str, Any]:
        return self._request("GET", "/status")

    def get_coverage(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/coverage")["capabilities"]

    def get_clipboard_status(self) -> Dict[str, Any]:
        return self._request("GET", "/clipboard/status")

    def enable_clipboard(self, host_id: str, task: Optional[str] = None, *, consent: bool = False) -> Dict[str, Any]:
        if host_id != "local-host" or consent is not True:
            raise DevGuardError("Explicit consent on the capture Mac is required", code="CAPTURE_CONSENT_REQUIRED")
        return self._request("POST", "/clipboard/enable", {"consent": True, "task": task})

    def disable_clipboard(self) -> Dict[str, Any]:
        return self._request("POST", "/clipboard/disable")

    def copy_cleaned_clipboard(self, expected_version: int) -> Dict[str, Any]:
        return self._request("POST", "/clipboard/copy-cleaned", {"content_version": expected_version})

    def evaluate_privacy(self, project_id: str, task: str, surface: str, destination_id: str,
                         content_version: int, text: str) -> Dict[str, Any]:
        return self._request("POST", "/guard/evaluate", {
            "project_id": project_id or None, "task": task, "surface": surface,
            "destination_id": destination_id, "content_version": content_version, "text": text,
        })

    def deliver_request(self, request_id: str, *, content_version: Optional[int] = None,
                        destination_id: Optional[str] = None) -> Dict[str, Any]:
        if content_version is None or not destination_id:
            raise DevGuardError("Use the inspected content version and destination", code="INSPECTION_BINDING_REQUIRED")
        return self._request("POST", f"/guard/requests/{request_id}/deliver", {
            "content_version": content_version, "destination_id": destination_id,
        })

    def get_incidents(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/incidents")["incidents"]

    def get_run(self, run_id: str) -> Dict[str, Any]:
        run = self._request("GET", f"/runs/{run_id}")
        model = run.get("model") or {}
        run.update(model_name=model.get("name"), model_digest=model.get("digest"),
                   candidate_patch_id=run.get("candidate_id"))
        run["verification"] = {"status": run.get("verification") or "NOT_RUN"}
        return run

    def get_patch(self, patch_id: str) -> Dict[str, Any]:
        patch = self._request("GET", f"/patches/{patch_id}")
        patch.update(patch_id=patch.get("candidate_id"), status=patch.get("state"),
                     base_hash=patch.get("base_revision"),
                     target_file=", ".join(patch.get("base_hashes", {})),
                     verification_summary=patch.get("verification"))
        return patch

    def apply_patch(self, patch_id: str, expected_hash: str, *, expected_base_revision: Optional[str] = None,
                    idempotency_key: Optional[str] = None, approved: bool = False) -> Dict[str, Any]:
        if approved is not True or not expected_base_revision or not idempotency_key:
            raise DevGuardError("Explicit approval and inspected candidate/base versions are required", code="PATCH_APPROVAL_REQUIRED")
        return self._request("POST", f"/patches/{patch_id}/apply", {
            "approved": True, "expected_candidate_hash": expected_hash,
            "expected_base_revision": expected_base_revision, "idempotency_key": idempotency_key,
        })

    def reject_patch(self, patch_id: str) -> Dict[str, Any]:
        return self._request("POST", f"/patches/{patch_id}/reject")

    def get_events(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        if cursor is not None and not re.fullmatch(r"[0-9]{1,19}", cursor):
            raise DevGuardError("Invalid audit cursor", code="INVALID_CURSOR")
        return self._request("GET", f"/events?after={cursor}" if cursor else "/events")

    def get_findings(self):
        return self._request('GET','/findings')['findings']

    def initialize_repair(self):
        return self._request('POST','/repair/initialize')

    def create_incident(self,project_id,signal):
        return self._request('POST','/incidents',{'project_id':project_id,'signal':signal})

    def investigate_incident(self,incident_id):
        return self._request('POST',f'/incidents/{incident_id}/investigate',{})

    def set_repair_idle(self,idle):
        return self._request('POST','/scheduler/enter-idle' if idle else '/scheduler/pause',{})

    def cancel_run(self,run_id):
        return self._request('POST',f'/runs/{run_id}/cancel',{})
