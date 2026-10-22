"""Persistent, unambiguous data-source labels."""
import streamlit as st


def render_fixture_banner(is_fixture):
    title='FIXTURE MODE — SIMULATED PRESENTATION DATA' if is_fixture else 'LIVE MODE — AUTHORITATIVE API RESPONSES ONLY'
    text=('Declared synthetic examples. Actions and results here are simulated.' if is_fixture else
          'Connected mode. Readiness is checked separately; unavailable inspections remain held.')
    st.markdown(f'<div class="mode-banner {"" if is_fixture else "live"}"><span class="mode-dot"></span><div><div class="mode-title">{title}</div><div class="mode-description">{text}</div></div></div>',unsafe_allow_html=True)


def render_windows_capture_notice():
    st.caption('Native text capture runs on the enrolled macOS/Windows desktop with explicit consent. Universal paste blocking is unsupported.')
