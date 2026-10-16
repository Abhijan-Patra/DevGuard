"""Incident timeline, repair run, and patch review view component.

Owner: Windows 1 (Antigravity).
Renders incident list, run states, verification summaries, unified diffs,
and operator apply/reject controls per docs/API_CONTRACT.md and docs/tasks/WINDOWS_1_DASHBOARD.md.
"""

from typing import Any, Dict
from uuid import uuid4
import streamlit as st
from devguard.ui.client import BaseDevGuardClient, DevGuardError, StaleContentError


RUN_STATE_COLORS = {
    "QUEUED": "blue",
    "WAITING_FOR_RESOURCES": "orange",
    "SNAPSHOTTING": "orange",
    "INVESTIGATING": "orange",
    "PATCHING_SANDBOX": "orange",
    "VERIFYING": "orange",
    "READY_FOR_REVIEW": "green",
    "APPLIED": "green",
    "UNRESOLVED": "violet",
    "BLOCKED": "red",
    "CANCELED": "gray",
    "OBSOLETE": "gray",
    "REJECTED": "red",
}


def render_incident_view(client: BaseDevGuardClient) -> None:
    st.header("🔧 Incident Investigation & Sandboxed Repair")
    st.caption("Inspect background repair runs, isolated verification results, and review candidate diffs.")

    try:
        if not client.is_fixture_mode():
            readiness = client.get_status().get("repair", {})
            if not readiness.get("available"):
                st.info("Repair is unavailable: " + str(readiness.get("reason_code", "NOT_CONFIGURED")))
                st.caption("The privacy and clipboard services remain available. Configure the pinned verifier image on the Mac before starting repair.")
                return
        incidents = client.get_incidents()
    except DevGuardError as e:
        st.error(f"Failed to load incidents [{e.code}]: {e}")
        return

    if not incidents:
        st.info("No active or historical incidents found.")
        return

    incident_titles = [f"{inc.get('incident_id')}: {inc.get('title')}" for inc in incidents]
    selected_idx = st.selectbox(
        "Select Incident to Inspect",
        options=range(len(incidents)),
        format_func=lambda i: incident_titles[i],
    )
    incident = incidents[selected_idx]

    col_details, col_run = st.columns([1, 1])

    with col_details:
        st.subheader("Incident Details")
        st.markdown(f"**ID:** `{incident.get('incident_id')}`")
        st.markdown(f"**Project:** `{incident.get('project_id')}`")
        st.markdown(f"**Status:** `{incident.get('status')}`")
        st.markdown(f"**Base Revision:** `{incident.get('source_revision')}`")

        st.markdown("**Error / Failure Signal:**")
        st.code(incident.get("signal", "(No signal text)"), language="text")

    with col_run:
        st.subheader("Repair Run Status")
        run_id = incident.get("active_run_id")
        if not run_id:
            st.info("No repair run active for this incident.")
            return

        try:
            run_data = client.get_run(run_id)
        except DevGuardError as err:
            st.error(f"Failed to load run {run_id} [{err.code}]: {err}")
            return

        run_state = run_data.get("state", "UNKNOWN")
        state_color = RUN_STATE_COLORS.get(run_state, "gray")

        st.metric("Run State", run_state)
        st.markdown(f"**State:** :{state_color}[**{run_state}**]")
        st.markdown(f"**Model:** `{run_data.get('model_name') or 'not pinned'}` (Digest: `{(run_data.get('model_digest') or 'unpinned')[:16]}`)")

        verification = run_data.get("verification", {})
        if verification:
            st.markdown(f"**Sandbox Verification:** `{verification.get('status')}`")
            v_evidence = verification.get("test_evidence")
            if v_evidence:
                st.caption(f"Evidence: `{v_evidence}`")

        observations = run_data.get("safe_observations", [])
        if observations:
            st.markdown("**Safe Observations:**")
            for obs in observations:
                st.markdown(f"- {obs}")

    # Patch Review Section
    patch_id = run_data.get("candidate_patch_id")
    if patch_id:
        st.markdown("---")
        st.subheader(f"Candidate Patch Review ({patch_id})")

        try:
            patch = client.get_patch(patch_id)
        except DevGuardError as err:
            st.error(f"Failed to load patch {patch_id} [{err.code}]: {err}")
            return

        patch_status = patch.get("status", "READY_FOR_REVIEW")
        st.markdown(f"**Target File:** `{patch.get('target_file')}`")
        st.markdown(f"**Base Hash:** `{patch.get('base_hash')}` | **Candidate Hash:** `{patch.get('candidate_hash')}`")
        st.markdown(f"**Verification:** {patch.get('verification_summary')}")
        st.markdown(f"**Current Patch Status:** **{patch_status}**")

        st.markdown("**Unified Diff (Proposed by local Gemma 4):**")
        st.code(patch.get("diff", "(Empty diff)"), language="diff")

        if patch_status == "READY_FOR_REVIEW":
            st.warning("⚠️ **Operator Authority Required:** The AI model cannot self-apply patches. Confirmation verifies the expected base hash before mutation.")
            col_apply, col_reject = st.columns(2)

            with col_apply:
                if st.button("✅ Apply Patch to Local Source", use_container_width=True):
                    try:
                        key = "apply-key:" + patch_id + ":" + str(patch.get("candidate_hash"))
                        if key not in st.session_state:
                            st.session_state[key] = str(uuid4())
                        resp = client.apply_patch(patch_id,
                            expected_hash=(patch.get("base_hash", "") if client.is_fixture_mode()
                                           else patch.get("candidate_hash", "")),
                            expected_base_revision=patch.get("base_revision") or patch.get("base_hash"),
                            idempotency_key=st.session_state[key], approved=True)
                        st.success(f"Patch applied successfully: {resp.get('message', 'Applied')}")
                        st.rerun()
                    except StaleContentError as err:
                        st.error(f"409 Stale Error: Base code modified since patch generation! ({err})")
                    except DevGuardError as err:
                        st.error(f"Apply failed [{err.code}]: {err}")

            with col_reject:
                if st.button("❌ Reject Candidate Patch", use_container_width=True):
                    try:
                        resp = client.reject_patch(patch_id)
                        st.info(f"Patch rejected: {resp.get('message', 'Rejected')}")
                        st.rerun()
                    except DevGuardError as err:
                        st.error(f"Reject failed [{err.code}]: {err}")
        elif patch_status == "APPLIED":
            st.success("✅ This patch has been APPLIED to local source revision.")
        elif patch_status == "REJECTED":
            st.error("❌ This patch candidate was REJECTED by operator.")
