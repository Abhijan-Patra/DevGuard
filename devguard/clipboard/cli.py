"""Explicit local operator controls; never print raw clipboard text."""

import argparse
import json

import httpx

from devguard.__main__ import session_token


def main():
    parser = argparse.ArgumentParser(description="DevGuard local text clipboard controls")
    parser.add_argument("action", choices=["status", "enable", "disable", "copy-cleaned"])
    parser.add_argument("--consent", action="store_true", help="Explicitly permit future copied-text inspection")
    parser.add_argument("--task", help="Brief task context, not clipboard/private content")
    args = parser.parse_args()
    if args.action == "enable" and not args.consent:
        parser.error("enable requires --consent; it observes future copied text locally")
    try:
        headers = {"Authorization": f"Bearer {session_token()}"}
        with httpx.Client(base_url="http://127.0.0.1:8765", headers=headers,
                          trust_env=False, follow_redirects=False, timeout=10) as client:
            if args.action == "status":
                response = client.get("/api/v1/clipboard/status")
            elif args.action == "enable":
                response = client.post("/api/v1/clipboard/enable", json={"consent": True, "task": args.task})
            elif args.action == "disable":
                response = client.post("/api/v1/clipboard/disable")
            else:
                current = client.get("/api/v1/clipboard/status")
                current.raise_for_status()
                response = client.post("/api/v1/clipboard/copy-cleaned",
                                       json={"content_version": current.json()["content_version"]})
            response.raise_for_status()
            result = response.json()
            result.pop("safe_preview", None)
            print(json.dumps(result))
    except (httpx.HTTPError, ValueError, OSError):
        print(json.dumps({"status": "ACTION_HELD", "message": "Check local service, consent and current inspection state"}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
