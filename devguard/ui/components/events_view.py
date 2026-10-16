"""Audit event stream component.

Owner: Windows 1 (Antigravity).
Renders structured, redacted timeline events per docs/API_CONTRACT.md.
"""

from typing import Any, Dict
from html import escape
import streamlit as st
from devguard.ui.client import BaseDevGuardClient, DevGuardError


SEVERITY_COLORS = {
    "INFO": "blue",
    "WARNING": "orange",
    "ERROR": "red",
    "CRITICAL": "red",
}


def render_events_view(client: BaseDevGuardClient) -> None:
    st.header("📜 Redacted Event Stream & Audit Log")
    st.caption("Structured, privacy-preserving event timeline. Raw payloads and secrets are excluded.")

    try:
        events_data = client.get_events()
        events = events_data.get("events", [])
    except DevGuardError as e:
        st.error(f"Failed to fetch audit events [{e.code}]: {e}")
        return

    if not events:
        st.info("No audit events recorded yet.")
        return

    # Severity filter
    col_filter, _ = st.columns([1, 2])
    with col_filter:
        selected_severities = st.multiselect(
            "Filter Severity",
            options=["INFO", "WARNING", "ERROR", "CRITICAL"],
            default=[],
        )

    filtered = [e for e in events if str(e.get("severity", "info")).upper() in selected_severities] if selected_severities else events

    for ev in reversed(filtered):
        sev = str(ev.get("severity", "info")).upper()
        color = SEVERITY_COLORS.get(sev, "gray")
        kind = escape(str(ev.get("kind", "event")))
        ts = escape(str(ev.get("timestamp", "")))
        summary = escape(str(ev.get("redacted_summary", "(No summary)")))
        state = escape(str(ev.get("state", "")))

        with st.container():
            st.markdown(
                f"""
                <div style="border-left: 4px solid {color}; padding-left: 12px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem; color: #888;">
                        <span><strong>{kind}</strong> ({state})</span>
                        <span>{ts}</span>
                    </div>
                    <div style="margin-top: 4px; font-size: 0.95rem;">{summary}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
