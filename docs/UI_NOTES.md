# DevGuard UI notes & runbook

**Owner:** Windows 1 (Antigravity)  
**Branch:** `codex/windows-dashboard`  
**Target Paths:** `devguard/ui/`, `tests/ui/`, `docs/UI_NOTES.md`

---

## 1. Overview

The DevGuard UI is an operator-facing presentation dashboard built with [Streamlit](https://streamlit.io). It consumes the shared REST API defined in [API_CONTRACT.md](API_CONTRACT.md) and displays privacy decisions, text clipboard capture states, capability coverage, and sandboxed patch reviews.

### Core Principles
- **No backend logic in UI:** The dashboard does not perform classification, regex filtering, git commits, or clipboard capture. All decisions are requested from the backend.
- **Fixture Mode vs. Live Mode:** A persistent, unmistakable banner is displayed when running in **Fixture Mode**. Synthetic data is never presented as actual model outcomes.
- **Privacy preservation:** No raw secrets, unredacted clipboard history, or reversible mapping tokens are displayed or stored in logs. Session tokens are held in session memory only (`st.session_state`) and never written to disk or repository files.
- **Honest capability claims:** Native clipboard capture is supported on enrolled macOS hosts only (`NSPasteboard`). Windows host native capture is declared **UNSUPPORTED**; the Windows UI functions strictly as an operator dashboard and display viewer.

---

## 2. Launching the Dashboard

### Prerequisites
Install dependencies:
```powershell
python -m pip install -e '.[dev,ui]'
```

### Start Command
Run the Streamlit application from the repository root:
```powershell
python -m streamlit run devguard/ui/app.py
```
By default, the dashboard opens at `http://localhost:8501`.

---

## 3. Dashboard Modes

### A. Fixture Mode (Default)
- **Banner:** `⚠️ FIXTURE MODE — SIMULATED PRESENTATION DATA`
- **Purpose:** Enables offline UI development, operator walkthroughs, and manual acceptance testing without requiring an active Ollama server or running FastAPI instance.
- **Client:** [`FixtureDevGuardClient`](../devguard/ui/client.py) loads declared synthetic scenarios from [`fixtures.py`](../devguard/ui/fixtures.py).

### B. Live Mode (FastAPI Backend)
- **Banner:** `LIVE MODE — AUTHORITATIVE API RESPONSES ONLY`
- **Purpose:** Connects to the local DevGuard API backend (`/api/v1`) powered by local Gemma 4 E4B (`gemma4:e4b-it-q4_K_M`).
- **Configuration (Sidebar):**
  - **Base URL:** `http://127.0.0.1:8765/api/v1`
  - **Operator Session Token:** Bearer token for authenticated operator endpoints. Kept in memory only.
  - **Test Connection:** Queries authenticated `GET /status` to check API access and actual model readiness/digest.

---

## 4. Implemented Views

| View | Endpoints Consumed | Description |
| :--- | :--- | :--- |
| **🛡️ Privacy Gate** | `POST /guard/evaluate`<br>`POST /guard/requests/{id}/deliver` | Submits prompt, tool, or file text for inspection. Displays decision (`ALLOW`, `SANITIZE`, `LOCAL_ONLY`, `REVIEW`, `BLOCK`), reason codes, safe redacted preview, and delivery release receipts. |
| **📋 Text Clipboard** | `GET /clipboard/status`<br>`POST /clipboard/enable`<br>`POST /clipboard/disable`<br>`POST /clipboard/copy-cleaned` | Shows enrolled host, state (`OFF`, `CHECKING`, `SENSITIVE`, `CLEAR_FOR_CAPTURE_SCOPE`, etc.), content version, and safe preview. Includes **Copy Cleaned Text** with 409 conflict detection and a clear notice that Windows host capture is unsupported. |
| **📊 Integration Coverage** | `GET /coverage` | Tabular and pill-filtered view of integration paths matching [COVERAGE.md](COVERAGE.md). Tracks client version and explicit limitation notes. |
| **🔧 Repair & Patches** | `GET /incidents`<br>`GET /runs/{id}`<br>`GET /patches/{id}`<br>`POST /patches/{id}/apply`<br>`POST /patches/{id}/reject` | Displays background repair run progress (without fake progress bars), safe observations, unified diffs, and operator Apply/Reject controls with base-hash verification. |
| **📜 Audit Event Log** | `GET /events?after=...` | Displays structured, privacy-preserving event timeline with severity filtering. |

---

## 5. Error Handling & Edge Cases

- **`401/403 Unauthorized`**: Handled via `AuthenticationError`. Prompts operator to supply or refresh session token.
- **`409 Conflict (Stale Content)`**: Handled via `StaleContentError`. Occurs when the clipboard version or source base-hash changes before an operator action completes. UI presents a clear warning and prevents stale overwrites.
- **`503 Service Unavailable`**: Handled via `ServiceUnavailableError`. Occurs if Ollama or the pinned Gemma model is not ready.
- **Connection Drops**: Handled via `BackendConnectionError` with clear retry guidance.

---

## 6. Running UI Tests

Lightweight unit tests verify client contract conformance, fixture schemas, state transitions, and stale conflict handling:
```powershell
python -m unittest discover -s tests/ui -v
```
Or with pytest:
```powershell
python -m pytest tests/ui/ -v
```

---

## 7. Team Handoff & Coordination

- **Mac 1 (Abhijan / Backend Guard):** Streamlit dependency pin request submitted (`streamlit>=1.35`). When backend `/guard/evaluate`, `/clipboard/status`, and `/coverage` are active, switch UI to Live Mode and configure session token.
- **Mac 2 (Repair & Tests):** Sandbox patch review and incident endpoints conform to `GET /runs/{id}` and `POST /patches/{id}/apply`.
- **Windows 2 (QA & Scenarios):** Synthetic fixtures in `devguard/ui/fixtures.py` can be extended with scenarios from `evals/cases/` and `demo/fixtures/`.

## Mac 1 integration follow-up

The dashboard is integrated on `codex/mac1-integration`. Live mode uses actual backend payloads and never displays fallback fixture decisions. Fixture state remains isolated and labelled. The local Streamlit config binds to loopback and disables usage telemetry. Native enable requires an explicit consent checkbox on the capture Mac. Server-side credentials never enter requests to arbitrary remote hosts. Refer to [measured integration status](INTEGRATION_STATUS.md) for tests, dependency snapshots and remaining live gates.
