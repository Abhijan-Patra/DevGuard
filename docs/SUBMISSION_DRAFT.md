# DevGuard — Hackathon Submission Draft

**Track Categories:** Best Use of Gemma 4 | Open Source AI  
**Repository:** [https://github.com/Abhijan-Patra/DevGuard](https://github.com/Abhijan-Patra/DevGuard)  
**License:** MIT (Original Code) | Gemma Model Terms & Third-Party Dependencies Retain Respective Licenses  

---

## 1. Project Summary

**DevGuard** is an open-source, local-first privacy guard and automated backend repair agent designed for developers using AI coding assistants. Powered entirely by a locally hosted **Gemma 4 E4B** model (`gemma4:e4b-it-q4_K_M` via Ollama), DevGuard ensures sensitive corporate credentials, confidential prose, and customer data never leak into AI prompt channels, while autonomously investigating backend failures and preparing verified patches in disposable sandboxes.

Unlike tools that rely on privacy-invasive screen recordings, keyboard loggers, or post-hoc detections, DevGuard operates on strict synchronous gates before delivery and diagnoses software defects through structured logs, source diffs, and independent test oracles.

---

## 2. Key Innovations & Architecture

```
                   ┌──────────────────────────────────────────────┐
                   │               Developer Task                 │
                   └──────────────────────┬───────────────────────┘
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    ▼                                           ▼
      [ 🛡️ Privacy Guard Gate ]                   [ 🔧 Backend Repair Agent ]
   • Synchronous pre-delivery inspection        • Reproducible test failure signal
   • Gitleaks regex + Gemma 4 reasoning         • Isolated Docker sandbox execution
   • Precision span redaction & masking         • Independent test runner oracle
   • Fail-closed delivery authorization         • Base-hash stale conflict checking
                    │                                           │
                    ▼                                           ▼
      [ 📋 Opt-In Text Clipboard ]                [ 🖥️ Operator Dashboard ]
   • macOS text watcher (opt-in consent)        • Streamlit presentation viewer
   • Fast deduplication & cancel on overwrite   • Unmistakable FIXTURE vs LIVE mode
   • Cleaned text copy (anti-scan loop)         • Zero credential leakage in UI state
```

### A. Dual Local-Gemma Architecture
DevGuard uses a single quantized Gemma 4 E4B model (`gemma4:e4b-it-q4_K_M`) for two complementary developer protection workflows:
1. **Foreground Privacy Gate:** Synchronous inspection of prompts, tool outputs, and file snippets. Foreground inference takes priority in a bounded queue, ensuring real-time editor responsiveness.
2. **Background Repair Agent:** Diagnostic reasoning over structured pytest traces and source diffs in isolated Docker containers, generating candidate patches verified against immutable trusted tests.

### B. Fail-Closed Privacy Policy
If Gemma, Ollama, or the Gitleaks scanner encounters a timeout or internal error, DevGuard's policy engine immediately **holds** the request (decision: `REVIEW`). Uninspected bytes are never passed downstream to third-party model APIs.

### C. Opt-In macOS Clipboard Protection
Clipboard inspection is strictly opt-in and restricted to text payloads on enrolled hosts (`NSPasteboard`). An operator can inspect the sanitized preview and click **Copy Cleaned Text** to safely paste debugging snippets without production credentials.

### D. Honest Boundaries & Zero Screen Scraping
DevGuard deliberately avoids visual screen monitoring, video understanding, and universal paste interception. Bug diagnosis relies entirely on deterministic code facts, structured JSON traces, and pytest execution reports.

---

## 3. Technology Stack & Runtime Specs

| Component | Technology | Rationale / Notes |
| :--- | :--- | :--- |
| **Model** | Gemma 4 E4B (`gemma4:e4b-it-q4_K_M`) | Low-latency local Apple Silicon & desktop GPU inference via Ollama |
| **Backend API** | FastAPI / Pydantic v2 / Python 3.11+ | Strict input validation, zero extra attributes, bounded text budget (32 KiB) |
| **Secret Scanning** | Gitleaks + Gemma Contextual Engine | High-entropy regex scanning paired with semantic confidential prose detection |
| **Sandbox Isolation** | Docker containers / Disposable worktrees | Isolated pytest execution; immutable trusted test suites |
| **Operator UI** | Streamlit | Responsive dashboard; strictly presentation client; zero security decisions in UI |
| **Audit Storage** | Bounded in-memory SQLite | Zero raw secrets stored on disk, in logs, or in Git |

---

## 4. Evaluation & Verification Metrics

Our evaluation suite encompasses 26 structured test scenarios across privacy, clipboard, backend repair, and unseen withheld cases:

| Suite Category | Cases | Target Capabilities | Status |
| :--- | :---: | :--- | :---: |
| **Privacy Guard (`evals/cases/privacy_cases.json`)** | P01–P07 | Synthetic AWS tokens, benign constants, confidential prose, stack traces with customer PII, prompt injections, traversal escapes, model timeouts. | Spec Complete (`UNRUN` live trial) |
| **Clipboard Protection (`evals/cases/clipboard_cases.json`)** | C01–C06 | Consent lifecycle (OFF/ON), duplicate counter bypass, rapid overwrite cancellation, copy-cleaned cycle, non-text skip, unmanaged paste boundary. | Spec Complete (`UNRUN` live trial) |
| **Backend Repair (`evals/cases/repair_cases.json`)** | B01–B08 | Null item handling, quantity multiplication regression, empty cart calculation, missing dependency handling, stale 409 conflict, verifier immutability, idempotent actions, healthy backend no-op. | Spec Complete (`UNRUN` live trial) |
| **Withheld Evaluation (`evals/cases/withheld_variants.json`)** | W01–W05 | Non-standard token delimitation, health PII in SQL comments, percentage discount math bug, zero-width obfuscated injection, boundary off-by-one index. | Withheld from prompts |

*All synthetic evaluation records are catalogued in `evals/results/results_registry.json`.*

---

## 5. Honest Capability & Coverage Matrix

In accordance with our commitment to honest open-source documentation, we explicitly distinguish verified, partial, and unsupported capabilities:

- ✅ **Explicit Text/Prompt Inspection:** Implemented via synchronous `/guard/evaluate` endpoint and verified with deterministic Gitleaks regex and local Gemma proposals.
- 🟡 **macOS Native Clipboard:** Text capture implemented with opt-in consent; advisory watcher; universal paste prevention into unmanaged third-party apps is **UNSUPPORTED** by OS architecture.
- 🟡 **Codex CLI Adapter:** Documented hook points (`UserPromptSubmit`, `PreToolUse`) integrated for blocking and warning; arbitrary prompt rewriting without user notice is unverified.
- 🔴 **Windows Native Clipboard Capture:** Declared **UNSUPPORTED**. Windows acts strictly as an operator dashboard viewer.
- 🔴 **Screenshots & Video Scraping:** Declared **UNSUPPORTED BY DESIGN**. DevGuard treats visual screen scraping as an unacceptable privacy and security liability.

---

## 6. How to Run Locally

### 1. Prerequisites
- Python 3.11+
- Ollama installed with Gemma 4: `ollama pull gemma4:e4b-it-q4_K_M`
- Optional: Docker (for isolated repair sandboxes)

### 2. Install & Start Backend
```powershell
python -m pip install -r requirements.lock.txt
python -m devguard
# Default port: http://127.0.0.1:8765/api/v1 (session token generated in .devguard/session-token)
```

### 3. Launch Operator Dashboard
```powershell
python -m pip install -r requirements-ui.lock.txt
python -m streamlit run devguard/ui/app.py
# Opens dashboard at http://localhost:8501
```

### 4. Run Verification Tests
```powershell
# Run the complete test suite (132 backend/repair tests + 20 UI/QA tests)
python -m pytest tests/ -v
```

---

## 7. Submission Checklist & Declarations
- [x] Code is original, MIT-licensed, and public on GitHub.
- [x] Pinned Gemma 4 model (`gemma4:e4b-it-q4_K_M`) runs locally without cloud inference dependency.
- [x] No private user data, personal tokens, or production API keys are included in repository commits or fixtures.
- [x] Unmistakable separation between synthetic presentation fixtures and live model execution.
