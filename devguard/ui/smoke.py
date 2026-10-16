"""Actual local backend/model/UI smoke using declared synthetic text only.

Starts a temporary loopback backend with an in-process reference receiver and
private audit database. Uses the Streamlit element tree, never screenshots.
Does not enable the system clipboard, configure repair or apply source changes.
"""

import json
from pathlib import Path
import secrets
import socket
import stat
import tempfile
import threading
import time

import uvicorn
from streamlit.testing.v1 import AppTest

from devguard.api.app import create_app
from devguard.config import Settings
from devguard.storage.audit import AuditStore
from devguard.ui.client import HttpDevGuardClient, StaleContentError


def run():
    report = {"scope": "Actual loopback API, real pinned Gemma, Streamlit element tree; synthetic input only",
              "general_clipboard_enabled": False, "source_patch_applied": False}
    received = []

    async def receiver(text):
        received.append(text)

    token = secrets.token_urlsafe(32)
    with tempfile.TemporaryDirectory(prefix="devguard-live-ui-") as directory:
        database = Path(directory) / "audit.sqlite3"
        backend = create_app(Settings(token), audit=AuditStore(database),
                             receivers={"synthetic-reference": receiver})
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(backend, host="127.0.0.1", port=port,
                                             log_level="critical", access_log=False))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and thread.is_alive() and time.monotonic() < deadline:
                time.sleep(0.02)
            assert server.started
            url = f"http://127.0.0.1:{port}/api/v1"
            client = HttpDevGuardClient(url, token)
            status = client.get_status()
            report["runtime"] = status["runtime"]
            assert status["runtime"]["model_ready"]

            app_path = Path(__file__).with_name("app.py")
            app = AppTest.from_file(app_path, default_timeout=45).run()
            app.session_state["session_token"] = token
            app.session_state["backend_url"] = url
            app.sidebar.radio[0].set_value("Live Mode (FastAPI Backend)").run()
            assert not app.exception
            app.sidebar.radio[1].set_value('🛡️ Privacy Gate').run()
            assert not app.exception

            def field(label):
                return next(item for item in app.text_input if item.label == label)

            field("Configured Destination").set_value("synthetic-reference")
            field("Active Task Context").set_value("Debug the webhook HTTP 403")
            secret = "synthetic-dashboard-fixture-492817"
            app.text_area[0].set_value(f"api_key={secret}; webhook returned HTTP 403.")
            started = time.monotonic()
            next(button for button in app.button if "Evaluate with DevGuard" in button.label).click().run()
            assert not app.exception
            result = app.session_state["last_eval_result"]
            report["evaluation_seconds"] = round(time.monotonic() - started, 3)
            report["decision"] = result["decision"]
            assert result["status"] == "READY" and result["decision"] == "SANITIZE"
            assert secret not in result["safe_preview"] and "403" in result["safe_preview"]
            expected = result["safe_preview"]
            request_id, version = result["request_id"], result["content_version"]
            assert not received
            next(button for button in app.button if "Authorize Delivery" in button.label).click().run()
            assert not app.exception
            assert app.session_state["last_eval_result"]["delivered"] is True
            assert app.session_state["last_eval_result"].get('receipt_id')
            report['delivery_receipt_recorded']=True
            assert received == [expected]
            report["receiver_got_only_inspected_cleaned_bytes"] = True
            try:
                client.deliver_request(request_id, content_version=version, destination_id="synthetic-reference")
                raise AssertionError("Replay was not held")
            except StaleContentError:
                pass
            report["replay_held"] = True

            for view in ("Overview", "📋 Text Clipboard", "📊 Integration Coverage", "🔧 Repair & Patches", "📜 Audit Event Log"):
                app.sidebar.radio[1].set_value(view).run()
                assert not app.exception
            assert client.get_clipboard_status()["enabled"] is False
            assert client.get_status()["repair"]["configured"] is False
            assert secret not in json.dumps(client.get_events())
            report["all_six_live_views_rendered"] = True
            report["audit_omits_synthetic_secret"] = True
            report["audit_file_mode"] = oct(stat.S_IMODE(database.stat().st_mode))
            report["status"] = "PASS"
        except Exception:
            report["status"] = "FAILED"
        finally:
            server.should_exit = True
            thread.join(35)
            report["backend_shutdown_acknowledged"] = not thread.is_alive()
            if thread.is_alive():
                report["status"] = "FAILED"
            sock.close()
    return report, (0 if report["status"] == "PASS" else 1)


def main():
    report, code = run()
    print(json.dumps(report, indent=2))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
