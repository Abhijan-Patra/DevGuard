"""Clipboard state and action view component.

Owner: Windows 1 (Antigravity).
Renders enrolled host, capture status, version, safe preview, and copy-cleaned action
per docs/CLIPBOARD.md, docs/API_CONTRACT.md, and docs/tasks/WINDOWS_1_DASHBOARD.md.
"""

from typing import Any, Dict
import streamlit as st
from devguard.ui.client import BaseDevGuardClient, DevGuardError, StaleContentError
from devguard.ui.components.banner import render_windows_capture_notice


STATE_BADGES = {
    "OFF": ("🔘 OFF", "gray"),
    "CHECKING": ("⏳ CHECKING", "orange"),
    "SENSITIVE": ("⚠️ SENSITIVE", "red"),
    "REVIEW": ("🔍 REVIEW REQUIRED", "violet"),
    "CLEAR_FOR_CAPTURE_SCOPE": ("✅ CLEAR FOR SCOPE", "green"),
    "SKIPPED": ("⏭️ SKIPPED (NON-TEXT/OVERSIZE)", "blue"),
    "ERROR": ("❌ ERROR", "red"),
}


def render_clipboard_view(client: BaseDevGuardClient) -> None:
    st.header("📋 Text Clipboard Guard")
    st.caption("Opt-in background text clipboard inspection and safe cleaned-copy controls.")

    render_windows_capture_notice()

    try:
        status_data = client.get_clipboard_status()
    except DevGuardError as e:
        st.error(f"Failed to fetch clipboard status [{e.code}]: {e}")
        return

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Capture Host & Controls")
        enrolled_host = status_data.get("capture_host_id", "Unknown host")
        enabled = status_data.get("enabled", False)
        state = status_data.get("state", "OFF")
        version = status_data.get("content_version", 0)

        st.markdown(f"**Enrolled Host:** `{enrolled_host}`")
        badge_text, badge_color = STATE_BADGES.get(state, (state, "gray"))
        st.markdown(f"**Current State:** :{badge_color}[**{badge_text}**]")
        st.markdown(f"**Content Version:** `v{version}`")

        st.markdown("---")
        st.subheader("Capture Activation")
        if client.is_fixture_mode():
            st.caption("Simulating capture enable/disable on synthetic macOS host.")
            if not enabled:
                if st.button("🟢 Enable Clipboard Protection (Simulated)", use_container_width=True):
                    client.enable_clipboard(host_id=enrolled_host)
                    st.success("Simulated capture enabled.")
                    st.rerun()
            else:
                if st.button("🔴 Disable Clipboard Protection (Simulated)", use_container_width=True):
                    client.disable_clipboard()
                    st.info("Simulated capture stopped.")
                    st.rerun()
        else:
            st.warning(
                "⚠️ **Host Confirmation Required:** Native clipboard activation must be authorized "
                f"locally on the capture host (`{enrolled_host}`). Remote viewers cannot silently enable capture."
            )
            col_en, col_dis = st.columns(2)
            with col_en:
                consent = st.checkbox("I am on the capture Mac and consent to inspect future text copies")
                if st.button("Enable on This Mac", disabled=not consent, use_container_width=True):
                    try:
                        response = client.enable_clipboard(host_id=enrolled_host, consent=consent)
                        if response.get("enabled") is not True:
                            raise DevGuardError("Capture was not enabled", code="CAPTURE_NOT_ENABLED")
                        st.success("Capture enabled for future copies on this Mac.")
                        st.rerun()
                    except DevGuardError as err:
                        st.error(f"Cannot enable [{err.code}]: {err}")
            with col_dis:
                if st.button("Disable Capture", use_container_width=True):
                    try:
                        client.disable_clipboard()
                        st.info("Capture disabled.")
                        st.rerun()
                    except DevGuardError as err:
                        st.error(f"Disable error [{err.code}]: {err}")

    with col2:
        st.subheader("Inspected Content & Safe Preview")

        if not enabled:
            st.info("Clipboard protection is currently OFF. No text is observed or analyzed.")
        elif state == "CHECKING":
            st.warning("Analysis in progress... Pending scans are not certified safe.")
        elif state == "SKIPPED":
            st.info("Content was SKIPPED (non-text or exceeded 32 KiB text budget). Never labeled safe.")
        else:
            safe_preview = status_data.get("safe_preview", "")
            if safe_preview:
                st.markdown("**Safe Redacted Preview:**")
                st.code(safe_preview, language="text")
            else:
                st.info("No text preview available.")

            summary = status_data.get("redacted_summary")
            if summary:
                st.markdown(f"**Detector Summary:** {summary}")

            can_copy = status_data.get("can_copy_cleaned", False)
            if can_copy and safe_preview:
                st.markdown("---")
                if st.button(f"📋 Copy Cleaned Text (v{version})", use_container_width=True):
                    try:
                        resp = client.copy_cleaned_clipboard(expected_version=version)
                        st.success(f"✅ Cleaned version {version} copied! (Audit reference recorded)")
                    except StaleContentError as err:
                        st.error(f"⚠️ 409 Conflict: Clipboard changed before copy completed ({err})")
                    except DevGuardError as err:
                        st.error(f"Copy failed [{err.code}]: {err}")
