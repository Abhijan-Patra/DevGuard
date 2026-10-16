# DevGuard — Live Demo Runbook & Presentation Guide

**Owner:** Member 4 (Windows 2 - Scenarios, QA & Demo)  
**Target:** Live Judges & Hackathon Presentation (3 to 5 minutes)  
**Companion Fixtures:** `demo/fixtures/demo_scenarios.json`, `demo/fixtures/sample_events.json`, `demo/fixtures/backend_oracles.json`

---

## 1. Pre-Presentation Setup Checklist

Execute this checklist 15 minutes before the presentation starts:

1. **Verify Local Model Status:**
   ```powershell
   ollama list
   # Verify `gemma4:e4b-it-q4_K_M` is present and active
   curl http://127.0.0.1:11434/api/tags
   ```
2. **Start DevGuard Backend:**
   ```powershell
   python -m devguard.api
   # Confirm GET http://127.0.0.1:8000/api/v1/health returns {"status":"ok","model_ready":true}
   ```
3. **Launch Operator Dashboard:**
   ```powershell
   python -m streamlit run devguard/ui/app.py
   # Opens in browser at http://localhost:8501
   ```
4. **Prepare Demo Repository Snapshot:**
   - Ensure `demo/backend/cart.py` has the deliberate quantity multiplication defect:
     `total += item['price']` instead of `total += item['quantity'] * item['price']`.
   - Ensure `trusted_tests/test_cart.py` is unmodified.
5. **Set Environment to LIVE or FIXTURE Mode:**
   - If Ollama and FastAPI are running: Switch sidebar to **Live Mode** (`http://127.0.0.1:8000/api/v1`).
   - If presenting offline without local GPU/Ollama: Keep default **Fixture Mode** with the persistent, honest disclaimer banner.

---

## 2. 3-Minute Demo Presentation Script

### Act 1: The Problem & Architecture (0:00 – 0:45)
- **Speaker:** *"AI coding assistants supercharge development, but sending entire prompts, error logs, and clipboards to external cloud models leaks private credentials, customer PII, and internal architectural secrets. Traditional security tools are either post-hoc scanners or invasive screen loggers."*
- **Visual:** Point to the DevGuard architecture banner in the UI.
- **Speaker:** *"DevGuard introduces a dual-agent, local-first paradigm powered completely on-device by Gemma 4 E4B. First: a synchronous privacy gate that intercepts and sanitizes developer input before transmission. Second: a background repair agent that investigates code regressions in disposable Docker sandboxes using structured logs and tests—with zero screen recording or visual surveillance."*

---

### Act 2: Privacy Gate & Exact-Span Redaction (0:45 – 1:30)
- **Action in UI:** Navigate to **🛡️ Privacy Gate** view.
- **Input Text:** Paste synthetic diagnostic log from `demo/fixtures/demo_scenarios.json` (Scenario 1):
  ```
  ValueError at auth.py:54 in authenticate: Invalid credentials for user contact@enterprise.invalid with token ghp_synthetic_pat_1234567890abcdef. Please check why validation failed.
  ```
- **Click:** **Evaluate Privacy Gate**.
- **Observable Outcome:**
  - Decision: **`SANITIZE`** (Yellow Badge).
  - Reason Codes: `[PERSONAL_DATA, CREDENTIAL]`.
  - Safe Preview: `ValueError at auth.py:54 in authenticate: Invalid credentials for user [CUSTOMER_EMAIL_1] with token [REDACTED_SECRET_TOKEN_1]. Please check why validation failed.`
- **Speaker:** *"Notice the precision: Gemma 4 and Gitleaks identify the customer email and token, replacing them with type-safe placeholders, while 100% of the debugging facts—the file path, line number, and exception class—remain intact. The assistant can fix the bug without ever seeing private bytes."*

---

### Act 3: Opt-In Text Clipboard & Cleaned Copy (1:30 – 2:15)
- **Action in UI:** Navigate to **📋 Text Clipboard** view.
- **Speaker:** *"Developers constantly copy stack traces and database connection strings. DevGuard includes an opt-in text watcher for macOS."*
- **Visual Cue:** Note the host status: Enrolled macOS host with Windows operator dashboard viewer.
- **Simulate Clipboard Payload:** (Scenario 2 from `demo_scenarios.json`):
  `DATABASE_URL="postgres://demo_admin:SuperSecretPass2026!@db.internal.invalid:5432/app_db"`
- **Observable Outcome:**
  - State: **`SENSITIVE`** (Warning badge).
  - Safe Preview: `DATABASE_URL="postgres://demo_admin:REDACTED_PASSWORD_01@db.internal.invalid:5432/app_db"`
- **Click:** **Copy Cleaned Text**.
- **Speaker:** *"With one click, the sanitized string replaces the OS clipboard without triggering an infinite re-scan loop. The raw password is transiently wiped from memory."*

---

### Act 4: Background Repair Agent & Stale Conflict Protection (2:15 – 3:00)
- **Action in UI:** Navigate to **🔧 Repair & Patches** view.
- **Incident:** `inc-demo-cart-01` ("Cart quantity calculation regression").
- **Visual Cue:**
  - Baseline Test Status: **FAILS** (`3 * 125 returned 125, expected 375`).
  - Observation: Identified line 8 in `demo/backend/cart.py`.
  - Sandbox Test Evidence: `pytest trusted_tests/test_cart.py (3/3 PASSED)`.
  - Unified Diff:
    ```diff
    --- a/demo/backend/cart.py
    +++ b/demo/backend/cart.py
    @@ -6,3 +6,3 @@
    -    total += item['price']
    +    total += item['quantity'] * item['price']
    ```
- **Show Stale Protection:**
  - Mention: *"If the developer concurrently edits `cart.py` while the patch was pending, the backend checks the base hash and immediately rejects application with HTTP 409 Conflict (`STALE_CONTENT`), preventing code loss."*
- **Click:** **Apply Patch** (when base hash matches).
- **Observable Outcome:** Patch state transitions to **`APPLIED`**. Working tree is verified clean.

---

## 3. Failure & Contingency Procedures

| Problem | Contingency Action | Talking Point |
| :--- | :--- | :--- |
| **Ollama connection drops during presentation** | UI displays clean `503 Service Unavailable` banner. Request is held safe (`REVIEW`). | *"This demonstrates our core fail-closed invariant: if the local model is offline, DevGuard halts delivery rather than leaking uninspected data."* |
| **No local GPU available for demo** | Keep dashboard in **Fixture Mode**. | *"We are running under Fixture Mode, which displays synthetic contract data without pretending it is live model output."* |
| **Host is Windows (Native capture unsupported)** | UI clearly displays `Windows (viewer only - local capture UNSUPPORTED)`. | *"We believe in honest capability boundaries: native clipboard interception is supported on macOS; Windows runs as an operator viewer."* |

---

## 4. Key Takeaways for Judges
1. **Real Gemma 4 E4B Utilization:** Efficient local quantization running on developer laptops without cloud telemetry.
2. **Dual Capability:** Unified guard and repair workflows sharing an intelligent FIFO priority queue.
3. **Zero Screen/Video Scraping:** Privacy-first design using structured code diffs, logs, and independent unit tests.
4. **Honest Open-Source Engineering:** Explicit coverage matrices, strict error handling, and complete reproducibility.
