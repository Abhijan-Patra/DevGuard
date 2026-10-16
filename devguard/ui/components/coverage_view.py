"""Integration coverage view component.

Owner: Windows 1 (Antigravity).
Renders capability statuses, client versions, and limitation notes
per docs/COVERAGE.md and docs/tasks/WINDOWS_1_DASHBOARD.md.
"""

from typing import Any, Dict, List
import streamlit as st
from devguard.ui.client import BaseDevGuardClient, DevGuardError
from devguard.ui.design import heading
from pathlib import Path
import json


STATUS_COLORS = {
    "VERIFIED": "green",
    "PARTIAL": "orange",
    "UNVERIFIED": "blue",
    "UNIMPLEMENTED": "gray",
    "UNSUPPORTED": "red",
}


def render_coverage_view(client: BaseDevGuardClient) -> None:
    heading('Capabilities, with clear boundaries.','See what is implemented, what has been exercised, and which paths remain unsupported.','DEVGUARD / COVERAGE')
    _recorded_evidence()

    try:
        entries = client.get_coverage()
    except DevGuardError as e:
        st.error(f"Failed to load coverage matrix [{e.code}]: {e}")
        return

    # Filter controls
    col_filter, col_stats = st.columns([1, 2])
    with col_filter:
        selected_status = st.multiselect(
            "Filter by Status",
            options=["VERIFIED", "PARTIAL", "UNVERIFIED", "UNIMPLEMENTED", "UNSUPPORTED"],
            default=[],
        )

    # Render summary metric pills
    counts: Dict[str, int] = {}
    for entry in entries:
        s = entry.get("status", "UNIMPLEMENTED")
        counts[s] = counts.get(s, 0) + 1

    with col_stats:
        m_cols = st.columns(5)
        for idx, status_key in enumerate(["VERIFIED", "PARTIAL", "UNVERIFIED", "UNIMPLEMENTED", "UNSUPPORTED"]):
            with m_cols[idx]:
                st.metric(status_key, counts.get(status_key, 0))

    st.markdown("---")

    filtered_entries = (
        [e for e in entries if e.get("status") in selected_status] if selected_status else entries
    )

    for entry in filtered_entries:
        status = entry.get("status", "UNIMPLEMENTED")
        color = STATUS_COLORS.get(status, "gray")
        cap = entry.get("capability", "Unknown Capability")
        client_name = entry.get("client", "Generic")
        version = entry.get("client_version") or "Not pinned"
        limitations = entry.get("limitations", "No limitation notes provided.")
        evidence = entry.get("evidence_ref")

        with st.expander(f":{color}[●] **{cap}** — *{status}* ({client_name})", expanded=False):
            st.markdown(f"**Target Client:** `{client_name}` (Version: `{version}`)")
            st.markdown(f"**Current Status:** :{color}[**{status}**]")
            st.markdown(f"**Limitation / Scope Note:** {limitations}")
            if evidence:
                st.markdown(f"**Verification Evidence:** `{evidence}`")
            else:
                st.caption("No live verification evidence attached yet.")


def _recorded_evidence():
    with st.expander('Recorded Mac 1 verification · individual trials, not continuous monitoring'):
        st.caption('Recorded on 16 October 2026 using declared synthetic data. These reports do not establish broad accuracy, universal paste blocking or installed-client interception.')
        root=Path(__file__).resolve().parents[3]/'docs/evidence'
        dashboard_report='mac1-modern-dashboard.json' if (root/'mac1-modern-dashboard.json').is_file() else 'mac1-live-dashboard.json'
        for name,title in [('mac1-system-clipboard.json','Native macOS clipboard'),
                           (dashboard_report,'Live API, Gemma and reference delivery')]:
            path=root/name
            if not path.is_file():continue
            try:data=json.loads(path.read_text())
            except (OSError,ValueError):continue
            st.markdown('**'+title+' · '+str(data.get('status','UNKNOWN'))+'**')
            st.caption(data.get('scope','Recorded synthetic trial'))
            checks=data.get('checks',{})
            if checks:
                st.write(f"{sum(value is True for value in checks.values())} / {len(checks)} recorded checks passed.")
            st.json(data,expanded=False)
