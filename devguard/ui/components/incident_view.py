"""Incident timeline, repair run, and patch review view component.

Owner: Windows 1 (Antigravity).
Renders incident list, run states, verification summaries, unified diffs,
and operator apply/reject controls per docs/API_CONTRACT.md and docs/tasks/WINDOWS_1_DASHBOARD.md.
"""

from typing import Any, Dict
from uuid import uuid4
import streamlit as st
from devguard.ui.client import BaseDevGuardClient, DevGuardError, StaleContentError
from devguard.ui.design import heading


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
    heading('Backend repair workspace','Run named checks in an isolated snapshot. Review verified changes before touching original files.','DEVGUARD / REPAIRS')

    try:
        readiness = client.get_status().get('repair',{})
        if not _render_worker_controls(client,readiness):return
        incidents = client.get_incidents()
    except DevGuardError as e:
        st.error(f"Failed to load incidents [{e.code}]: {e}")
        return

    if not incidents:
        st.info("No incidents yet. Queue an investigation above for a project and named check registered by trusted startup.")
        return

    incident_titles = [f"{inc.get('incident_id')}: {inc.get('title')}" for inc in incidents]
    selected_idx = st.selectbox(
        "Select Incident to Inspect",
        options=range(len(incidents)),
        format_func=lambda i: incident_titles[i],
        index=next((i for i,item in enumerate(incidents)
                    if item.get('incident_id')==st.session_state.get('repair_selected_incident')),0),
    )
    incident = incidents[selected_idx]
    if st.button('Investigate selected incident',use_container_width=False):
        try:
            result=client.investigate_incident(incident['incident_id'])
            if not result.get('run_id'):raise DevGuardError('Run was not acknowledged',code='RUN_NOT_QUEUED')
            st.session_state['repair_notice']='Investigation queued. Enter idle to allow background work.'
            st.rerun()
        except DevGuardError as error:st.error(f'{error.code}: {error}')

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

        baseline=run_data.get('baseline')
        if baseline:st.caption('Reproduced baseline: '+baseline)
        if run_data.get('reason_code'):st.warning('Run held: '+run_data['reason_code'])
        tools=run_data.get('completed_tools',[])
        if tools:
            st.markdown('**Completed tools**')
            st.write(' → '.join(tools))
        if run_state not in {'READY_FOR_REVIEW','APPLIED','UNRESOLVED','BLOCKED','CANCELED','OBSOLETE','REJECTED'}:
            if st.button('Cancel this run'):
                try:
                    result=client.cancel_run(run_id)
                    if result.get('run_id')!=run_id:raise DevGuardError('Cancellation was not acknowledged',code='CANCEL_NOT_ACKNOWLEDGED')
                    st.info('Cancellation requested. Refresh to see the worker acknowledgement.')
                except DevGuardError as error:st.error(f'{error.code}: {error}')

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
                        if (resp.get("state") or resp.get("status")) != "APPLIED":
                            raise DevGuardError("Patch application was not acknowledged", code="PATCH_NOT_APPLIED")
                        st.success("Patch application acknowledged by the backend.")
                        st.rerun()
                    except StaleContentError as err:
                        st.error(f"409 Stale Error: Base code modified since patch generation! ({err})")
                    except DevGuardError as err:
                        st.error(f"Apply failed [{err.code}]: {err}")

            with col_reject:
                if st.button("❌ Reject Candidate Patch", use_container_width=True):
                    try:
                        resp = client.reject_patch(patch_id)
                        if (resp.get("state") or resp.get("status")) != "REJECTED":
                            raise DevGuardError("Patch rejection was not acknowledged", code="PATCH_NOT_REJECTED")
                        st.info("Patch rejection acknowledged by the backend.")
                        st.rerun()
                    except DevGuardError as err:
                        st.error(f"Reject failed [{err.code}]: {err}")
        elif patch_status == "APPLIED":
            st.success("✅ This patch has been APPLIED to local source revision.")
        elif patch_status == "REJECTED":
            st.error("❌ This patch candidate was REJECTED by operator.")


def _render_worker_controls(client,readiness):
    available=readiness.get('available') is True
    c1,c2,c3=st.columns([2,1,1])
    with c1:
        state=readiness.get('state','UNAVAILABLE')
        st.markdown('**Worker · '+state.replace('_',' ').title()+'**')
        st.caption('Manual idle trigger. Active model calls are not preempted by queue priority.')
    with c2:
        if st.button('Enter idle',disabled=not available,use_container_width=True):
            try:
                response=client.set_repair_idle(True)
                if response.get('paused') is not False:raise DevGuardError('Idle was not acknowledged',code='IDLE_NOT_ACKNOWLEDGED')
                st.session_state['repair_notice']='Idle execution enabled for queued work.'
                st.rerun()
            except DevGuardError as error:st.error(f'{error.code}: {error}')
    with c3:
        if st.button('Pause repairs',disabled=not available,use_container_width=True):
            try:
                response=client.set_repair_idle(False)
                if response.get('paused') is not True:raise DevGuardError('Pause was not acknowledged',code='PAUSE_NOT_ACKNOWLEDGED')
                st.session_state['repair_notice']='Repairs paused. Active work has been asked to cancel.'
                st.rerun()
            except DevGuardError as error:st.error(f'{error.code}: {error}')
    if 'repair_notice' in st.session_state:st.info(st.session_state.pop('repair_notice'))
    if not available:
        st.warning('Repair unavailable: '+str(readiness.get('reason_code','NOT_CONFIGURED')))
        st.caption('Start the backend with a pinned verifier image. Privacy and clipboard controls remain independent.')
        if readiness.get('configured') and st.button('Retry repair initialization'):
            try:
                response=client.initialize_repair()
                if response.get('available') is not True:raise DevGuardError('Repair remains unavailable',code='REPAIR_UNAVAILABLE')
                st.rerun()
            except DevGuardError as error:st.error(f'{error.code}: {error}')
        return False
    with st.expander('New investigation',expanded=False):
        with st.form('new_investigation'):
            left,right=st.columns(2)
            with left:project=st.text_input('Registered project ID',value='demo-cart')
            with right:signal=st.text_input('Named check',value='cart')
            st.caption('Only projects and checks enrolled at trusted backend startup can run. No arbitrary roots or shell commands.')
            submit=st.form_submit_button('Queue investigation',type='primary')
        if submit:
            try:
                incident=client.create_incident(project,signal)
                if not incident.get('incident_id'):raise DevGuardError('Incident was not acknowledged',code='INCIDENT_NOT_CREATED')
                result=client.investigate_incident(incident['incident_id'])
                if not result.get('run_id'):raise DevGuardError('Run was not acknowledged',code='RUN_NOT_QUEUED')
                st.session_state['repair_notice']='Investigation queued. Enter idle to allow background work.'
                st.session_state['repair_selected_incident']=incident['incident_id']
                st.rerun()
            except DevGuardError as error:st.error(f'{error.code}: {error}')
    return True
