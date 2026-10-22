"""Bounded metadata-only SQLite audit shared by the API and repair worker."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import threading
from devguard.platform_io import private_directory, private_open
from uuid import uuid4


class AuditUnavailable(Exception):
    def __init__(self):
        super().__init__("AUDIT_UNAVAILABLE")


REASONS = {"CREDENTIAL", "PERSONAL_DATA", "CONFIDENTIAL", "IRRELEVANT", "PROMPT_INJECTION",
           "MODEL_UNAVAILABLE", "SCANNER_UNAVAILABLE", "INVALID_SPANS",
           "POLICY_BLOCK", "EXPIRED", "DELIVERED", "CAPTURE_CHANGED"}
GUARD_STATES = {"ALLOW", "SANITIZE", "LOCAL_ONLY", "REVIEW", "BLOCK", "DELIVERED"}
CLIPBOARD_STATES = {"OFF", "CHECKING", "SENSITIVE", "REVIEW", "CLEAR_FOR_CAPTURE_SCOPE",
                    "SKIPPED", "ERROR"}
REPAIR_STATES = {"ROLLED_BACK", "QUEUED", "WAITING_FOR_RESOURCES", "SNAPSHOTTING", "INVESTIGATING",
                 "PATCHING_SANDBOX", "VERIFYING", "READY_FOR_REVIEW", "APPLIED",
                 "UNRESOLVED", "BLOCKED", "CANCELED", "OBSOLETE", "REJECTED"}
REPAIR_KINDS = {"run.state", "tool.completed", "verification.completed", "patch.state"}


def private_database(path):
    """Trusted local path only, inside a private directory; no API selects it."""
    path = Path(path).absolute()
    private_directory(path.parent)
    parent = path.parent.lstat()
    if not stat.S_ISDIR(parent.st_mode) or (
        os.name != "nt" and (parent.st_mode & 0o077 or parent.st_uid != os.getuid())
    ):
        raise AuditUnavailable()
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = private_open(path, flags, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or (
            os.name != "nt" and (info.st_mode & 0o077 or info.st_nlink != 1 or info.st_uid != os.getuid())
        ):
            raise AuditUnavailable()
        for suffix in ("-journal", "-wal", "-shm"):
            if Path(str(path) + suffix).is_symlink():
                raise AuditUnavailable()
    finally:
        os.close(fd)
    return str(path)


class AuditStore:
    """No raw inputs, previews, model prose or supplied repair summaries persist."""

    def __init__(self, path=":memory:"):
        self._lock = threading.RLock()
        self.durable = str(path) != ":memory:"
        try:
            target = private_database(path) if self.durable else ":memory:"
            self.db = sqlite3.connect(target, check_same_thread=False, timeout=5)
            self.db.execute("PRAGMA synchronous=FULL")
            self.db.execute("PRAGMA journal_mode=DELETE")
            self.db.execute("CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, data TEXT NOT NULL)")
            self.db.commit()
        except (sqlite3.Error, OSError, RuntimeError):
            raise AuditUnavailable() from None

    def _append(self, event):
        with self._lock:
            try:
                with self.db:
                    cursor = self.db.execute("INSERT INTO events(data) VALUES(?)", (json.dumps(event),))
                    self.db.execute("DELETE FROM events WHERE seq < ?", (max(0, cursor.lastrowid - 4999),))
                return cursor.lastrowid
            except sqlite3.Error:
                raise AuditUnavailable() from None

    @staticmethod
    def _event(kind, state):
        return {
            "schema_version": 1, "event_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(), "project_id": None,
            "kind": kind, "state": state, "severity": "info",
            "redacted_summary": state, "evidence_refs": [],
        }

    def add(self, kind, state, *, request_id=None, content_version=None, reason_codes=()):
        valid = ((kind == "guard.decision" and state in GUARD_STATES)
                 or (kind == "clipboard.decision" and state in CLIPBOARD_STATES))
        if (not valid or (request_id is not None and not re.fullmatch(r"[a-zA-Z0-9_-]{1,128}", request_id))
                or (content_version is not None and (type(content_version) is not int or content_version < 0))):
            raise AuditUnavailable()
        event = self._event(kind, state)
        event.update(request_id=request_id, content_version=content_version,
                     redacted_summary=", ".join(sorted(set(reason_codes) & REASONS)) or state)
        return self._append(event)

    def add_repair(self, event):
        """Mac 2's synchronous event_sink(event); thread-safe and fail-closed."""
        kind, state = event.get("kind"), event.get("state")
        run_id, project_id = event.get("run_id"), event.get("project_id")
        if (kind not in REPAIR_KINDS or state not in REPAIR_STATES
                or not isinstance(run_id, str) or not re.fullmatch(r"run-[0-9a-f]{32}", run_id)
                or not isinstance(project_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", project_id)):
            raise AuditUnavailable()
        # Rebuild canonical metadata. Ignore supplied summaries, evidence, timestamps
        # and extra fields so even a mistaken raw payload never reaches SQLite.
        safe = self._event(kind, state)
        safe.update(run_id=run_id, project_id=project_id,
                    redacted_summary="Repair event: " + kind + "; state: " + state)
        return self._append(safe)

    def events(self, after=0):
        with self._lock:
            try:
                rows = self.db.execute("SELECT seq,data FROM events WHERE seq>? ORDER BY seq LIMIT 100", (after,)).fetchall()
                return {"events": [json.loads(data) for _, data in rows],
                        "next_cursor": str(rows[-1][0] if rows else after)}
            except (sqlite3.Error, ValueError):
                raise AuditUnavailable() from None

    def close(self):
        with self._lock:
            self.db.close()
