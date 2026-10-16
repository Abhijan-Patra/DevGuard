"""Local operator launcher; reuse the private session token without displaying it."""

import os
import runpy
from pathlib import Path

from devguard.__main__ import session_token
from devguard.config import Settings


def main(st=None):
    if st is None:
        import streamlit as st

    root = Path(__file__).resolve().parents[1]
    if Path.cwd().resolve() != root:
        st.error(
            "Launch the local operator dashboard from the DevGuard repository root."
        )
        st.stop()
    try:
        port = int(os.environ.get("DEVGUARD_LOCAL_API_PORT", "8765"))
        if not 1024 <= port <= 65535:
            raise ValueError("Invalid local port")
        token = session_token()
        Settings(session_token=token)
    except (OSError, ValueError):
        st.error("The private local operator session is unavailable.")
        st.stop()
    # Only the same local operator/capture host uses this launcher. Credentials
    # stay in the existing dashboard's session memory, never stdout/model input.
    st.session_state.setdefault("app_mode", "Live Mode (FastAPI Backend)")
    st.session_state.setdefault("backend_url", f"http://127.0.0.1:{port}/api/v1")
    st.session_state.setdefault("session_token", token)
    runpy.run_path(str(root / "devguard/ui/app.py"), run_name="__main__")


if __name__ == "__main__":
    main()
