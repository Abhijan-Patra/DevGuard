"""Privacy Gate evaluation and delivery view component.

Owner: Windows 1 (Antigravity).
Renders decision, redacted finding codes, safe preview, and delivery receipts
per docs/API_CONTRACT.md and docs/tasks/WINDOWS_1_DASHBOARD.md.
"""

from typing import Any, Dict
import streamlit as st
from devguard.ui.client import BaseDevGuardClient, DevGuardError


DECISION_COLORS = {
    "ALLOW": "green",
    "SANITIZE": "orange",
    "LOCAL_ONLY": "blue",
    "REVIEW": "violet",
    "BLOCK": "red",
}


def render_privacy_view(client: BaseDevGuardClient) -> None:
    st.header("🛡️ Privacy Gate & Evaluation")
    st.caption("Inspect and evaluate outgoing prompts, tool results, and file reads before external release.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Submit Text for Evaluation")
        with st.form("privacy_eval_form"):
            project_id = st.text_input("Project ID", value="project-demo-core")
            task = st.text_input("Active Task Context", value="Diagnose authentication exception in login handler")
            surface = st.selectbox(
                "Interception Surface",
                options=["explicit_prompt", "tool_result", "file_read", "clipboard"],
                index=0,
                help="Surface category authenticated by adapter or submitted by operator.",
            )
            destination_id = st.text_input("Configured Destination", value="configured-coding-client")
            content_version = st.number_input("Content Version", min_value=1, value=7, step=1)
            text_input = st.text_area(
                "Text Payload to Inspect",
                value="ValueError at auth/login.py:42: Auth failed for user customer_alpha@example.invalid with token ghp_ABC123secretKEY456",
                height=130,
                help="Sensitive strings are inspected locally and never logged or sent externally.",
            )

            submitted = st.form_submit_button("🔍 Evaluate with DevGuard Gate", use_container_width=True)

        if submitted:
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
        if not eval_result:
            try:
                # Load synthetic baseline if available
                from devguard.ui.fixtures import SYNTHETIC_PRIVACY_EVALUATION
                eval_result = SYNTHETIC_PRIVACY_EVALUATION
            except Exception:
                eval_result = None

        if eval_result:
            _render_eval_card(eval_result, client)
        else:
            st.info("No evaluation performed yet. Submit text on the left to see gate decision.")


def _render_eval_card(eval_result: Dict[str, Any], client: BaseDevGuardClient) -> None:
    decision = eval_result.get("decision", "REVIEW")
    color = DECISION_COLORS.get(decision, "gray")

    # Header metric
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Decision", decision)
    with m2:
        st.metric("Status", eval_result.get("status", "READY"))
    with m3:
        st.metric("Version", eval_result.get("content_version", 1))

    # Decision Badge
    st.markdown(f"**Gate Decision:** :{color}[**{decision}**]")

    # Safe Preview
    st.markdown("**Safe Preview (Cleaned / Redacted Output):**")
    safe_preview = eval_result.get("safe_preview", "(No preview available)")
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
    else:
        st.warning("⏳ **NOT DELIVERED**: Content is inspected and held. Explicit release required.")
        req_id = eval_result.get("request_id")
        if req_id and decision in ("ALLOW", "SANITIZE"):
            if st.button(f"🚀 Authorize Delivery ({req_id})", key="deliver_btn", use_container_width=True):
                try:
                    receipt = client.deliver_request(req_id)
                    eval_result["delivered"] = True
                    st.session_state["last_eval_result"] = eval_result
                    st.success(f"Delivery receipt created: `{receipt.get('receipt_id', 'receipt-ok')}`")
                    st.rerun()
                except DevGuardError as err:
                    st.error(f"Delivery blocked: [{err.code}] {err}")
        elif decision in ("BLOCK", "REVIEW"):
            st.error("Release disabled: Decision requires operator review or is blocked by security policy.")
