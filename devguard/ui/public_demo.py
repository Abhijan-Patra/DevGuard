"""Render the same custom workspace as a self-contained, read-only public tour."""
import json
from pathlib import Path

import streamlit as st


def public_document():
    root = Path(__file__).resolve().parents[1] / 'web'
    css = (root / 'workspace.css').read_text()
    script = (root / 'workspace.js').read_text()
    evidence = json.dumps(json.loads((root / 'evidence.json').read_text())).replace('<', '\\u003c')
    return ('<!doctype html><html lang="en" data-theme="dark"><head>'
            '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>DevGuard · Public feature tour</title><style>' + css + '</style></head>'
            '<body data-public-demo="1"><div id="app"></div><div id="notifications" role="status" aria-live="polite"></div>'
            '<dialog id="review-dialog" aria-labelledby="dialog-title"></dialog>'
            '<script>window.DEVGUARD_RECORDED_EVIDENCE=' + evidence + ';</script>'
            '<script type="module">' + script.replace('</script', '<\\/script') + '</script></body></html>')


def render_public_workspace():
    st.markdown('''<style>
    header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] {display:none!important}
    .stMainBlockContainer {max-width:none!important;padding:0!important}
    .stApp {background:#111315}.stElementContainer {margin:0!important}
    iframe {border:0;width:100%}
    </style>''', unsafe_allow_html=True)
    if hasattr(st, 'iframe'):
        st.iframe(public_document(), height='content', alt='DevGuard public read-only feature tour')
    else:
        import streamlit.components.v1 as components
        components.html(public_document(), height=1250, scrolling=True)
