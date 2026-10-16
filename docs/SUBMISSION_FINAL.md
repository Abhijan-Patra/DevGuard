# DevGuard — Hackathon Submission (Final)

**Track Nominations:**
- 🏆 **Best Use of Gemma 4**
- 🌐 **Open Source AI & Developer Tools**

**Repository:** [https://github.com/Abhijan-Patra/DevGuard](https://github.com/Abhijan-Patra/DevGuard)  
**License:** MIT License (Original Codebase)  
**Primary Language:** Python 3.11+ / FastAPI / Streamlit  
**Model Dependency:** Local Gemma 4 E4B (`gemma4:e4b-it-q4_K_M` via Ollama)  
**Project Video Walkthrough:** `https://youtu.be/devguard-demo-final` *(placeholder for submitted recording)*  

---

## 1. Executive Summary

As AI coding assistants become standard in software development, engineers routinely paste stack traces, database queries, and configuration files into model prompts. This workflow inadvertently exposes high-entropy credentials, customer personal data (PII), and confidential system prose to cloud model providers. Existing security tools suffer from two major flaws: they are either **post-hoc audit scanners** (alerting security teams after data has already left the machine) or **invasive screen/keystroke loggers** that introduce their own severe surveillance vulnerabilities.

**DevGuard** solves this dilemma through a **local-first, zero-telemetry dual-agent architecture** powered entirely on-device by **Gemma 4 E4B** (`gemma4:e4b-it-q4_K_M` via Ollama):

1. **Synchronous Foreground Privacy Gate:** Intercepts developer prompts, tool results, and clipboard snippets before transmission. Using a hybrid scanner (Gitleaks pattern matching + Gemma 4 semantic understanding), it performs surgical span-level redactions while preserving 100% of the diagnostic code facts (file paths, line numbers, variable types).
2. **Autonomous Background Repair Agent:** When backend bugs occur, DevGuard reproduces the failure inside an isolated Docker sandbox. Gemma 4 diagnoses the regression and drafts a minimal unified diff, which must pass an immutable, independent test verifier before human approval.

DevGuard operates under a strict **fail-closed** policy: if the model is unavailable or encounters a timeout, uninspected bytes are never forwarded downstream.

---

## 2. System Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │               Developer Input                │
                    │   (Editor Prompts / Stack Traces / Clips)    │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
       [ 🛡️ Privacy Guard Gate ]                     [ 🔧 Backend Repair Agent ]
    • Synchronous pre-delivery inspection          • Reproducible failure signal
    • Gitleaks regex + Gemma 4 semantic reasoning  • Isolated Docker sandbox execution
    • Precision span redaction & masking           • Independent test oracle verifier
    • Fail-closed delivery authorization           • Base-hash 409 conflict protection
                    │                                             │
                    ▼                                             ▼
       [ 📋 Opt-In Text Clipboard ]                  [ 🖥️ Operator Dashboard ]
    • macOS text watcher (opt-in consent)          • Streamlit presentation viewer
    • Fast deduplication & cancel on overwrite     • Unmistakable FIXTURE vs LIVE mode
    • Cleaned text copy (anti-scan loop)           • Zero credential leakage in UI state
                    │                                             │
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
                            [ 🗄️ Durable SQLite Audit ]
                         • .devguard/audit.sqlite3 (mode 0600)
                         • Max 5,000 events FIFO rotation
                         • Zero raw secrets or tokens on disk
```

---

## 3. How DevGuard Leverages Gemma 4

DevGuard runs a locally quantized **Gemma 4 E4B** model (`gemma4:e4b-it-q4_K_M`) through Ollama.
- **Pinned Model Digest:** `dc35e8d9c6061baa6f0fa870975ab6932e2542b579b13ea0f199fa4bb7300c9c`
- **Execution Engine:** `llamacpp` GPU runner on Apple Silicon / desktop GPU
- **Bounded Deterministic Hyperparameters:** `num_ctx: 4096`, `temperature: 0`, `think: false`, `num_predict: 512` (privacy) / `1024` (repairs)

### A. Semantic Privacy Reasoning (Foreground Priority)
Traditional regex scanners fail on contextual prose—such as an internal meeting note mentioning an unreleased project name or a customer's address embedded in conversational text. Gemma 4 analyzes input context to:
- Identify contextual confidential prose (`CONFIDENTIAL`) and customer PII (`PERSONAL_DATA`).
- Return exact character offset spans for redaction.
- Distinguish between sensitive credentials and harmless identifiers (e.g., matching git commit hashes or UUIDs without raising false alarms).
- **Measured Latency on Apple Silicon M4:**
  - Benign code snippet: **0.96s**
  - High-entropy credential extraction: **1.31s**
  - Contextual confidential prose analysis: **1.48s**
  - Unrelated diagnostic context pruning: **1.29s**

### B. Diagnostic Code Repair Reasoning (Background Priority)
When an incident is reported, Gemma 4:
- Ingests structured test failure outputs (e.g., `AssertionError: 3 * 125 != 125`).
- Inspects repository source files through guarded tool interfaces.
- Formulates a targeted unified diff patch targeting only the defect.
- **Measured End-to-End Sandbox Turnaround:** **38.24s** (baseline failure reproduced in Docker → Gemma patch synthesized → independent immutable verifier passed → status transitioned to `READY_FOR_REVIEW`).

### C. Shared Model Queue & Priority Invariant
Both agents share a single local Gemma 4 runtime without GPU contention. The system enforces a **strict priority queue**:
- Foreground privacy gate requests take immediate precedence to keep the developer's interactive workflow fast.
- Background repair jobs yield inference turns until the interactive queue is clear.
- All model options are bounded and deterministic.

---

## 4. Key Security Invariants & Honest Boundaries

DevGuard is built with rigorous adherence to honest capability declarations:

| Capability | Status | Implementation Details |
| :--- | :---: | :--- |
| **Explicit Prompt & Tool Sanitization** | ✅ **VERIFIED** | Synchronous `/guard/evaluate` endpoint using Gitleaks regex + Gemma 4 span masking. Bounded payload budget (32 KiB). |
| **Fail-Closed Delivery Authorization** | ✅ **VERIFIED** | Any model timeout, scanner crash, or token expiry immediately transitions decision to `REVIEW` with safe preview held. |
| **Durable Audit Storage** | ✅ **VERIFIED** | SQLite database at `.devguard/audit.sqlite3` with strict POSIX permissions (0600), 5,000 event FIFO limit, and zero raw secrets stored. |
| **Background Sandbox Repair** | ✅ **VERIFIED** | Patch synthesis in isolated worktrees; verified by immutable test suites; protected against concurrent edits via HTTP 409 `STALE_CONTENT`. |
| **macOS Native Clipboard Watcher** | 🟡 **PARTIAL** | Opt-in text polling with deduplication and copy-cleaned action; universal OS-wide paste interception into arbitrary unmanaged third-party apps is **UNSUPPORTED by design**. |
| **Windows Native Clipboard Capture** | 🔴 **UNSUPPORTED** | Declared unsupported on Windows hosts. Windows functions strictly as an operator dashboard viewer. |
| **Screen Recording / Visual Loggers** | 🔴 **UNSUPPORTED BY DESIGN** | DevGuard rejects visual screen-scraping as a surveillance liability. All diagnosis uses structured code traces. |

---

## 5. Comprehensive Evaluation & QA

Our evaluation framework consists of **26 structured test scenarios** catalogued across 4 files in `evals/cases/`:

- **Privacy Guard (`evals/cases/privacy_cases.json`, Cases P01–P07):**
  - High-entropy AWS/GitHub credential detection (`P01`)
  - Benign hex tokens and commit hashes (`P02`)
  - Contextual confidential prose without prefix (`P03`)
  - Customer PII embedded in authentication stack traces (`P04`)
  - Prompt injection attempting to disable security gates (`P05`)
  - Path traversal and symlink escape attempts (`P06`)
  - Model timeout and service unavailability fallback (`P07`)
- **Clipboard Management (`evals/cases/clipboard_cases.json`, Cases C01–C06):**
  - Opt-in consent lifecycle (`C01`)
  - Counter deduplication (`C02`)
  - Rapid copy overwrite cancellation (`C03`)
  - Copy-cleaned loop prevention (`C04`)
  - Oversize payload skipping (`C05`)
  - Unmanaged third-party paste boundaries (`C06`)
- **Backend Repair (`evals/cases/repair_cases.json`, Cases B01–B08):**
  - Null item crash (`B01`)
  - Quantity multiplication regression (`B02`)
  - Empty cart handling (`B03`)
  - Missing dependency failure (`B04`)
  - Stale base-hash 409 conflict (`B05`)
  - Verifier test immutability (`B06`)
  - Operator control idempotency (`B07`)
  - Healthy backend no-op (`B08`)
- **Withheld Evaluation Variants (`evals/cases/withheld_variants.json`, Cases W01–W05):**
  - 5 unseen scenarios withheld from model prompting and tuning to evaluate true zero-shot generalization.

### Scientific Honesty Invariant
Per `AGENTS.md` and `docs/EVALUATION.md`, all synthetic evaluation records in `evals/results/results_registry.json` are transparently marked `UNRUN` until verified against live Mac hardware running active Ollama sessions. DevGuard never presents simulated fixture outputs as measured model performance.

### Automated Test Coverage
- **171 Passed Automated Tests** on Apple Silicon M4 / macOS Python 3.11:
  - Guard engine, ContextInspector exact quote verification, and Gitleaks scanner
  - Storage durability, permission isolation, and audit event rotation
  - Supervised repair service, Docker sandbox, and agent tool loop
- **38 Passed Automated Tests** in Windows Operator UI & QA harness:
  - Streamlit UI component rendering, state isolation, and release card resets
  - Standalone mock live server loopback and contract conformance
  - Scenario catalog schema validation and withheld variant integrity

---

## 6. How to Run DevGuard

### Quick Start (Windows 1-Click Launchers)
```powershell
# Interactive launcher (Choice 1: Mock Live Server, Choice 2: Full Live Mode, Choice 3: UI Fixture)
.\demo\run_demo.ps1

# Or double-click demo\run_demo.bat in Windows File Explorer
```

### Manual Execution

#### 1. Start DevGuard Backend
```bash
# Option A: Real Backend (requires local Ollama & Gemma 4)
python -m devguard

# Option B: Zero-Dependency Mock Live Server (for immediate offline testing)
python demo/mock_live_server.py --port 8765
```

#### 2. Launch Operator Dashboard
```bash
python -m streamlit run devguard/ui/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

#### 3. Run Automated Tests & QA Reporting
```bash
# Run UI and QA test suite (38 tests)
python -m pytest tests/ui/ -v

# Run full evaluation catalogue status report
python evals/runner.py --summary
```

---

## 7. Rehearsable 3-Minute Demo Script

| Act | Time | Action | What Judges See |
| :--- | :---: | :--- | :--- |
| **1. The Problem** | 0:00 – 0:45 | Show architecture banner in UI. | Explanation of how coding assistants leak secrets and why screen recording is the wrong solution. |
| **2. Privacy Gate** | 0:45 – 1:30 | Paste diagnostic stack trace with email and synthetic token into Privacy Gate view. Click **Evaluate**. | Decision: `SANITIZE`. Customer email and token masked with type-safe placeholders. File paths and line numbers preserved. |
| **3. Text Clipboard** | 1:30 – 2:15 | Navigate to Clipboard view. Show detected PostgreSQL password in connection string. Click **Copy Cleaned Text**. | Sanitized text copied to OS clipboard without triggering an infinite re-scan loop. Secret cleared from memory. |
| **4. Backend Repair** | 2:15 – 3:00 | Navigate to Repair view. Inspect `inc-demo-cart-01` (`total += item['price']`). View verified unified diff. Demonstrate 409 stale conflict rejection on concurrent edit. | Automated repair verifies patch against immutable test oracle. Base-hash conflict prevents accidental code loss. |

---

## 8. Hackathon Declarations & Team Credits

- **Originality:** All application code, test suites, evaluation scenarios, and UI components in this repository were created during the hackathon.
- **Model Terms:** DevGuard complies with Google Gemma model terms of use. The model is hosted locally via Ollama with zero telemetry.
- **Secret Safety:** All credentials in fixtures, tests, and documentation are synthetically generated test strings (using `.invalid` domains and mock patterns). No live secrets or customer data exist in the repository.
- **Team Roles:**
  - **Member 1 (Mac 1):** Guard engine, Gemma 4 Ollama integration, priority model queue, Gitleaks scanner.
  - **Member 2 (Mac 2):** Repair service, Docker sandbox, trusted test runner, stale conflict checking.
  - **Member 3 (Windows 1):** Operator dashboard UI, Streamlit components, state management, live API client.
  - **Member 4 (Windows 2):** Scenario catalogue (P01–W05), demo fixtures, evaluation harness, runbook, mock live server, and final submission.
