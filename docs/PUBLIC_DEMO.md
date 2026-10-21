# Public read-only tour

The Render service uses `DEVGUARD_PUBLIC_DEMO=1`. Streamlit hosts the same custom browser design as a self-contained, read-only iframe. It never creates the local FastAPI app, loads the operator token, contacts Ollama or accesses a native clipboard.

The tour supports feature navigation, dark/light theme and export of recorded redacted verification evidence. Model/scanner/repair runtime readiness is unavailable on the public site; example project metadata is illustrative. All inspection, capture, scheduler and apply controls are disabled. A separate JavaScript API boundary refuses mutations without sending them to any backend. No public text input is accepted for inspection, and no fixture decision is substituted for model inference.

The Verification view contains measured local experiments, including known privacy calibration mismatches. Those values are presentation evidence only and never participate in the local guard/repair policy.

Build: `pip install '.[ui]'`

Start: `streamlit run devguard/ui/app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true --browser.gatherUsageStats false`

The existing Render deployment branch is `codex/public-demo`. Local actual execution uses `./scripts/devguard-local start` and `http://127.0.0.1:8765/app`; it requires no Streamlit frontend process.
