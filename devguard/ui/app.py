"""Main Streamlit application for DevGuard.

Owner: Windows 1 (Antigravity).
Implements the operator dashboard per docs/tasks/WINDOWS_1_DASHBOARD.md,
supporting both declared synthetic fixtures and live FastAPI backend endpoints.
"""

import streamlit as st
from devguard.config import MODEL

from devguard.ui.client import (
    BaseDevGuardClient,
    DevGuardError,
    FixtureDevGuardClient,
    HttpDevGuardClient,
)
from devguard.ui.components.banner import render_fixture_banner
from devguard.ui.components.clipboard_view import render_clipboard_view
from devguard.ui.components.coverage_view import render_coverage_view
from devguard.ui.components.events_view import render_events_view
from devguard.ui.components.incident_view import render_incident_view
from devguard.ui.components.privacy_view import render_privacy_view


st.set_page_config(
    page_title="DevGuard Operator Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_client() -> BaseDevGuardClient:
    """Instantiates and caches the active client in Streamlit session state."""
    mode = st.session_state.get("app_mode", "Fixture Mode (Simulated)")
    if mode == "Fixture Mode (Simulated)":
        if "fixture_client" not in st.session_state:
            st.session_state["fixture_client"] = FixtureDevGuardClient()
        return st.session_state["fixture_client"]
    else:
        base_url = st.session_state.get("backend_url", "http://127.0.0.1:8765/api/v1")
        token = st.session_state.get("session_token", "")
        return HttpDevGuardClient(base_url=base_url, token=token or None)


def main() -> None:
    # Sidebar Configuration
    with st.sidebar:
        st.title("🛡️ DevGuard")
        st.caption("Local Gemma 4 Privacy & Repair Companion")

        st.markdown("---")
        st.subheader("Runtime Mode")
        mode = st.radio(
            "Select Data Mode",
            options=["Fixture Mode (Simulated)", "Live Mode (FastAPI Backend)"],
            index=0 if st.session_state.get("app_mode") != "Live Mode (FastAPI Backend)" else 1,
            help="Fixture mode runs against declared synthetic scenarios without a running backend.",
        )
        if st.session_state.get("app_mode") != mode:
            st.session_state.pop("last_eval_result", None)
        st.session_state["app_mode"] = mode

        if mode == "Live Mode (FastAPI Backend)":
            st.markdown("#### Backend Connection")
            backend_url = st.text_input(
                "Base URL",
                value=st.session_state.get("backend_url", "http://127.0.0.1:8765/api/v1"),
                help="Base endpoint prefix per API_CONTRACT.md",
            )
            if st.session_state.get("backend_url") != backend_url:
                st.session_state.pop("last_eval_result", None)
            st.session_state["backend_url"] = backend_url

            session_token = st.text_input(
                "Operator Session Token",
                type="password",
                value=st.session_state.get("session_token", ""),
                help="Bearer token kept in session memory only; never logged or saved to Git.",
            )
            if st.session_state.get("session_token") != session_token:
                st.session_state.pop("last_eval_result", None)
            st.session_state["session_token"] = session_token

            try:
                client = get_client()
            except DevGuardError as error:
                st.error(str(error))
                st.stop()
            if st.button("🔌 Test Connection", use_container_width=True):
                try:
                    health = client.get_health()
                    st.success("Authenticated API connection established.")
                    if not health.get("model_ready"):
                        st.warning("Gemma is unavailable; contextual privacy checks remain held.")
                except DevGuardError as e:
                    st.error(f"Connection Error [{e.code}]: {e}")
        else:
            client = get_client()

        st.markdown("---")
        st.subheader("Navigation")
        active_tab = st.radio(
            "Go to View",
            options=[
                "🛡️ Privacy Gate",
                "📋 Text Clipboard",
                "📊 Integration Coverage",
                "🔧 Repair & Patches",
                "📜 Audit Event Log",
            ],
            index=0,
        )

        st.markdown("---")
        st.subheader("Model & Readiness")
        try:
            health_info = client.get_health()
            st.markdown(f"**Status:** `{health_info.get('status', 'unknown')}`")
            st.markdown(f"**Model:** `{health_info.get('model_name') or MODEL}`")
            st.caption(f"Digest: `{(health_info.get('model_digest') or 'unpinned')[:20]}`")
        except DevGuardError as error:
            if not client.is_fixture_mode():
                st.error(f"Live backend unavailable [{error.code}]: {error}")
                st.stop()
            st.caption("Readiness check unavailable")

        st.markdown("---")
        st.caption("DevGuard v0.1.0 • Windows 1 UI")

    # Main Area
    is_fixture = client.is_fixture_mode()
    render_fixture_banner(is_fixture)

    if active_tab == "🛡️ Privacy Gate":
        render_privacy_view(client)
    elif active_tab == "📋 Text Clipboard":
        render_clipboard_view(client)
    elif active_tab == "📊 Integration Coverage":
        render_coverage_view(client)
    elif active_tab == "🔧 Repair & Patches":
        render_incident_view(client)
    elif active_tab == "📜 Audit Event Log":
        render_events_view(client)


if __name__ == "__main__":
    main()
