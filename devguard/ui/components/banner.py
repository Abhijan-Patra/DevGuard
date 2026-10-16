"""Banner and alert components for DevGuard Streamlit dashboard.

Owner: Windows 1 (Antigravity).
Ensures clear, persistent visual distinction between Fixture Mode (simulated data)
and Live Mode, as required by docs/tasks/WINDOWS_1_DASHBOARD.md and AGENTS.md.
"""

import streamlit as st


def render_fixture_banner(is_fixture: bool) -> None:
    """Renders prominent status indicator for fixture vs live mode."""
    if is_fixture:
        st.markdown(
            """
            <div style="background-color: #2b1f00; border: 2px solid #e69500; border-radius: 8px; padding: 12px 18px; margin-bottom: 20px; color: #ffebcc;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.4rem;">⚠️</span>
                    <div>
                        <strong style="color: #ffa500; font-size: 1.05rem;">FIXTURE MODE — SIMULATED PRESENTATION DATA</strong>
                        <div style="font-size: 0.88rem; color: #eeddcc; margin-top: 2px;">
                            Displaying declared synthetic scenarios. Fixtures do not represent live model execution,
                            backend gate decisions, or actual clipboard interception.
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background-color: #0d2616; border: 2px solid #28a745; border-radius: 8px; padding: 10px 16px; margin-bottom: 20px; color: #d4edda;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.2rem;">🟢</span>
                    <div>
                        <strong style="color: #28a745; font-size: 0.95rem;">LIVE MODE — AUTHORITATIVE API RESPONSES ONLY</strong>
                        <div style="font-size: 0.85rem; color: #c3e6cb;">
                            Connection and model readiness are checked separately. Unavailable checks stay held.
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_windows_capture_notice() -> None:
    """Displays honest architectural limitation regarding Windows clipboard capture."""
    st.info(
        "**Host Notice:** Windows host native clipboard capture is **UNSUPPORTED** in this build. "
        "This dashboard operates as a display viewer and remote operator interface. "
        "Native text capture is implemented for enrolled macOS hosts (`NSPasteboard`). "
        "Clipboard capture actions must be confirmed on the capture host.",
        icon="ℹ️",
    )
