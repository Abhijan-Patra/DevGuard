import json
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4


class AuditStore:
    """Only constrained redacted fields are written, never caller/model text."""

    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, data TEXT NOT NULL)")
        self.db.commit()

    def add(self, kind, state, *, request_id=None, content_version=None, reason_codes=()):
        # Do not accept arbitrary summary strings from clients or the model.
        allowed = {"CREDENTIAL", "PERSONAL_DATA", "CONFIDENTIAL", "IRRELEVANT",
                   "MODEL_UNAVAILABLE", "SCANNER_UNAVAILABLE", "INVALID_SPANS",
                   "POLICY_BLOCK", "EXPIRED", "DELIVERED", "CAPTURE_CHANGED"}
        reasons = sorted(set(reason_codes) & allowed)
        event = {
            "schema_version": 1, "event_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(), "project_id": None,
            "kind": kind, "state": state, "severity": "info",
            "redacted_summary": ", ".join(reasons) or state,
            "evidence_refs": [], "request_id": request_id, "content_version": content_version,
        }
        cursor = self.db.execute("INSERT INTO events(data) VALUES(?)", (json.dumps(event),))
        self.db.execute("DELETE FROM events WHERE seq < ?", (max(0, cursor.lastrowid - 4999),))
        self.db.commit()
        return cursor.lastrowid

    def events(self, after=0):
        rows = self.db.execute("SELECT seq,data FROM events WHERE seq>? ORDER BY seq LIMIT 100", (after,)).fetchall()
        return {"events": [json.loads(data) for _, data in rows],
                "next_cursor": str(rows[-1][0] if rows else after)}

    def close(self):
        self.db.close()
