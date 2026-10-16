"""Opt-in Codex command hook. No config/trust is installed automatically."""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime

REASON = "DevGuard held this request. Review the local guard; use cleaned input if permitted."
MAX_INPUT = 65536


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def evaluate(text: str, surface: str, *, config: dict) -> bool:
    """Only an unchanged ready ALLOW permits the existing hook input to continue."""
    base = config.get("base_url", "")
    parsed = urllib.parse.urlsplit(base)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "::1"}
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path.rstrip("/") != "/api/v1"
        or not config.get("token")
        or not config.get("project_id")
        or not config.get("destination_id")
    ):
        return False
    version = time.time_ns()
    payload = {
        "project_id": config["project_id"],
        "task": None,
        "surface": surface,
        "destination_id": config["destination_id"],
        "content_version": version,
        "text": text,
    }
    request = urllib.request.Request(
        base.rstrip("/") + "/guard/evaluate",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + config["token"],
        },
        method="POST",
    )
    opener = urllib.request.build_opener(NoRedirects(), urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=3) as response:
            raw = response.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            return False
        decision = json.loads(raw)
        expiry = datetime.fromisoformat(
            decision.get("expires_at", "").replace("Z", "+00:00")
        )
        return (
            decision.get("decision") == "ALLOW"
            and decision.get("status") == "READY"
            and decision.get("content_version") == version
            and decision.get("destination_id") == config["destination_id"]
            and isinstance(decision.get("request_id"), str)
            and bool(decision["request_id"])
            and bool(decision.get("policy_revision"))
            and expiry > datetime.now(UTC)
        )
    except (OSError, ValueError, TypeError, AttributeError, urllib.error.URLError):
        return False


def handle(event: dict, guard_evaluate) -> dict:
    name = event.get("hook_event_name")
    if name == "UserPromptSubmit":
        prompt = event.get("prompt")
        allowed = isinstance(prompt, str) and guard_evaluate(prompt, "explicit_prompt")
        return {} if allowed else {"decision": "block", "reason": REASON}
    if name == "PreToolUse":
        # No arbitrary shell/file/MCP execution is authorized by text classification.
        # A later enrolled managed-tool adapter must prove its own path/output gate.
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": REASON,
            }
        }
    if name == "PostToolUse":
        result = json.dumps(event.get("tool_response"), ensure_ascii=False)
        return (
            {}
            if guard_evaluate(result, "tool_result")
            else {"decision": "block", "reason": REASON}
        )
    return {"decision": "block", "reason": REASON}


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            raise ValueError
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise ValueError
        config = {
            "base_url": os.environ.get(
                "DEVGUARD_BASE_URL", "http://127.0.0.1:8765/api/v1"
            ),
            "token": os.environ.get("DEVGUARD_ADAPTER_TOKEN", ""),
            "project_id": os.environ.get("DEVGUARD_PROJECT_ID", ""),
            "destination_id": os.environ.get("DEVGUARD_DESTINATION_ID", ""),
        }
        output = handle(
            event, lambda text, surface: evaluate(text, surface, config=config)
        )
        print(json.dumps(output))
        return 0
    except Exception:
        # Exit 2 is the documented blocking path, with a constant redacted reason.
        print(REASON, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
