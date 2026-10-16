"""Privacy Gate evaluation and delivery view component.

Owner: Windows 1 (Antigravity).
Renders decision, redacted finding codes, safe preview, and delivery receipts
per docs/API_CONTRACT.md and docs/tasks/WINDOWS_1_DASHBOARD.md.
"""

import json
from pathlib import Path
from typing import Any, Dict
from copy import deepcopy
import streamlit as st
from devguard.ui.client import BaseDevGuardClient, DevGuardError
from devguard.ui.design import heading


DECISION_COLORS = {
    "ALLOW": "green",
    "SANITIZE": "orange",
    "LOCAL_ONLY": "blue",
    "REVIEW": "violet",
    "BLOCK": "red",
}


def render_privacy_view(client: BaseDevGuardClient) -> None:
    heading('Share only the context you need.','Inspect prompts, source excerpts and tool results with local Gemma. Review the decision before supported delivery.','DEVGUARD / PRIVACY GATE')

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Submit Text for Evaluation")

        # Load predefined scenarios from Member 4 evals if present
        cases_file = Path(__file__).resolve().parent.parent.parent.parent / "evals" / "cases" / "privacy_cases.json"
        scenarios = []
        if cases_file.exists():
            try:
                with open(cases_file, "r", encoding="utf-8") as f:
                    scenarios = json.load(f)
            except Exception:
                scenarios = []

        scenario_map = {f"[{s['id']}] {s['scenario_name']}": s for s in scenarios}
        scenario_options = ["Custom Input"] + list(scenario_map.keys())

        selected_label = st.selectbox(
            "Load Predefined Test Scenario",
            options=scenario_options,
            index=0,
            help="Select a synthetic scenario from the Member 4 evaluation suite to prefill inputs.",
        )

        preset = scenario_map.get(selected_label, {})
        default_task = preset.get("task", "Diagnose authentication exception in login handler")
        default_surface = preset.get("surface", "explicit_prompt")
        default_dest = "local-preview"  # Examples inspect locally; real delivery needs an enrolled receiver.
        default_text = preset.get(
            "synthetic_input",
            "ValueError at auth/login.py:42: Auth failed for user customer_alpha@example.invalid with token ghp_ABC123secretKEY456",
        )
        surface_options = ["explicit_prompt", "tool_result", "file_read", "clipboard"]
        surface_index = surface_options.index(default_surface) if default_surface in surface_options else 0

        with st.form("privacy_eval_form"):
            project_id = st.text_input("Project ID", value="project-demo-core")
            task = st.text_input("Active Task Context", value=default_task)
            surface = st.selectbox(
                "Interception Surface",
                options=surface_options,
                index=surface_index,
                help="Surface category authenticated by adapter or submitted by operator.",
            )
            destination_id = st.text_input("Configured Destination", value=default_dest)
            content_version = st.number_input("Content Version", min_value=1, value=7, step=1)
            text_input = st.text_area(
                "Text Payload to Inspect",
                value=default_text,
                height=130,
                help="Sensitive strings are inspected locally and never logged or sent externally.",
            )

            submitted = st.form_submit_button("🔍 Evaluate with DevGuard Gate", use_container_width=True)

        if submitted:
            # A failed replacement check must not leave an older release card active.
            st.session_state.pop("last_eval_result", None)
            try:
                with st.spinner("Inspecting text through policy and local model..."):
                    eval_result = client.evaluate_privacy(
                        project_id=project_id,
                        task=task,
                        surface=surface,
                        destination_id=destination_id,
                        content_version=content_version,
                        text=text_input,
                    )
                st.session_state["last_eval_result"] = eval_result
                st.success("Evaluation completed.")
            except DevGuardError as e:
                st.error(f"Gate Evaluation Error [{e.code}]: {e}")

    with col2:
        st.subheader("Evaluation Decision & Preview")
        eval_result = st.session_state.get("last_eval_result")
        if not eval_result and client.is_fixture_mode():
            try:
                # Load synthetic baseline if available
                from devguard.ui.fixtures import SYNTHETIC_PRIVACY_EVALUATION
                eval_result = deepcopy(SYNTHETIC_PRIVACY_EVALUATION)
            except Exception:
                eval_result = None

        if eval_result and (client.is_fixture_mode() or not eval_result.get("simulated")):
            _render_eval_card(eval_result, client)
        else:
            st.info("No evaluation performed yet. Submit text on the left to see gate decision.")

    with st.expander('Recent active findings · transient inspections'):
        try:
            findings=client.get_findings()
            if not findings:st.caption('No active findings. Completed inspections expire; raw input is not a stored history.')
            else:
                st.dataframe([{'Request':f.get('request_id'),'Decision':f.get('decision'),
                    'Reasons':', '.join(f.get('reason_codes',[])),'Version':f.get('content_version'),
                    'Status':f.get('status')} for f in findings],hide_index=True,use_container_width=True)
        except DevGuardError as error:st.caption('Findings unavailable: '+error.code)


def _render_eval_card(eval_result: Dict[str, Any], client: BaseDevGuardClient) -> None:
    decision = eval_result.get("decision", "REVIEW")
    status = eval_result.get("status", "UNKNOWN")
    color = DECISION_COLORS.get(decision, "gray")

    # Header metric
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Decision", decision)
    with m2:
        st.metric("Status", status)
    with m3:
        st.metric("Version", eval_result.get("content_version", 1))

    # Decision Badge
    st.markdown(f"**Gate Decision:** :{color}[**{decision}**]")

    # Safe Preview
    st.markdown("**Safe Preview (Cleaned / Redacted Output):**")
    safe_preview = eval_result.get("safe_preview") or "(No approved preview available)"
    st.code(safe_preview, language="text")

    # Finding and reasons
    reasons = eval_result.get("reason_codes", [])
    if reasons:
        st.markdown("**Reason Codes Detected:**")
        st.write(", ".join([f"`{r}`" for r in reasons]))

    finding_ids = eval_result.get("finding_ids", [])
    if finding_ids:
        st.markdown("**Redacted Finding References:**")
        st.write(", ".join([f"`{f}`" for f in finding_ids]))

    st.markdown("---")
    # Delivery Receipt Section
    st.subheader("Delivery Status")
    delivered = eval_result.get("delivered", False)
    if delivered:
        st.success("✅ **DELIVERED**: Released to destination through verified gate receipt.")
        if eval_result.get('receipt_id'):
            st.caption('Delivery receipt')
            st.code(eval_result['receipt_id'],language=None)
    else:
        st.warning("⏳ **NOT DELIVERED**: Content is inspected and held. Explicit release required.")
        req_id = eval_result.get("request_id")
        if eval_result.get('destination_id')=='local-preview':
            st.info('Local preview only. No outgoing receiver is enrolled for this destination; inspection does not send the text.')
        elif req_id and status == "READY" and decision in ("ALLOW", "SANITIZE"):
            if st.button(f"🚀 Authorize Delivery ({req_id})", key="deliver_btn", use_container_width=True):
                try:
                    receipt = client.deliver_request(req_id,
                        content_version=eval_result.get("content_version"),
                        destination_id=eval_result.get("destination_id"))
                    if receipt.get("delivered") is not True or not receipt.get("receipt_id"):
                        raise DevGuardError("Delivery was not acknowledged", code="NO_DELIVERY_RECEIPT")
                    eval_result["delivered"] = True
                    eval_result['receipt_id'] = receipt['receipt_id']
                    st.session_state["last_eval_result"] = eval_result
                    st.success(f"Delivery receipt created: `{receipt.get('receipt_id', 'receipt-ok')}`")
                    st.rerun()
                except DevGuardError as err:
                    st.error(f"Delivery blocked: [{err.code}] {err}")
        elif status != "READY":
            st.info("Release unavailable: inspection is not READY. Submit a new evaluation.")
        elif decision == "LOCAL_ONLY":
            st.info("Local-only content cannot be released to an external destination.")
        elif decision in ("BLOCK", "REVIEW"):
            st.error("Release disabled: Decision requires operator review or is blocked by security policy.")
