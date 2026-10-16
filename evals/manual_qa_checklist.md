# DevGuard Manual QA Checklist & Verification Runbook

**Owner:** Member 4 (Windows 2 — Scenarios, QA & Demo)  
**Target:** Manual Acceptance Verification across Streamlit Dashboard & Client APIs  
**Companion References:** `evals/cases/`, `demo/fixtures/`, `docs/API_CONTRACT.md`  

---

## 1. Overview & Verification Rules

This checklist guides manual quality assurance across the DevGuard operator interface. Tests must be performed in both **Fixture Mode** and **Live Mode** (when local FastAPI and Gemma 4 backend are active).

### Mandatory Compliance Rules
- [x] **Unmistakable Mode Banners:** Fixture mode must display the warning banner; live mode must show the green connected indicator.
- [x] **Zero Raw Secret Leaks:** No unredacted tokens, customer passwords, or API keys should appear in form inputs, previews, event logs, or terminal outputs.
- [x] **Honest Capability Declarations:** Native clipboard capture on Windows must always be flagged `UNSUPPORTED`.
- [x] **Fail-Closed on Error:** 401 Unauthorized, 409 Stale Conflict, 503 Service Unavailable, and connection drops must show descriptive, user-friendly alerts.

---

## 2. Test Execution Checklist

### Section A: General Navigation & Runtime Mode

| Step | Action | Expected Visual & Functional Behavior | Status |
| :---: | :--- | :--- | :---: |
| A.1 | Launch Streamlit dashboard (`python -m streamlit run devguard/ui/app.py`) | Browser opens to `http://localhost:8501`. Sidebar displays `🛡️ DevGuard` title, runtime mode radio, navigation list, and model readiness status. | [ ] |
| A.2 | Check default mode | Persistent banner displays: `⚠️ FIXTURE MODE — simulated presentation data (not an actual model or gate outcome)`. | [ ] |
| A.3 | Toggle to Live Mode in Sidebar | Base URL input (`http://127.0.0.1:8765/api/v1`) and password-masked session token field appear. Persistent banner switches to `🟢 LIVE MODE`. | [ ] |
| A.4 | Click "🔌 Test Connection" with backend offline | Clean, non-crashing error displays: `Connection Error [CONNECTION_FAILED]: Could not connect to DevGuard backend server`. | [ ] |

---

### Section B: Privacy Gate View (`🛡️ Privacy Gate`)

| Step | Action | Expected Visual & Functional Behavior | Status |
| :--- | :--- | :--- | :---: |
| B.1 | Submit benign code (Scenario P02) | Decision badge: `ALLOW` (Green). Safe preview matches input. No sensitive findings reported. | [ ] |
| B.2 | Submit diagnostic trace with customer email and token (Scenario P04) | Decision badge: `SANITIZE` (Orange). Reason codes list `PERSONAL_DATA`, `CREDENTIAL`. Safe preview replaces email with `[CUSTOMER_EMAIL_1]` and token with `[REDACTED_SECRET_TOKEN_1]`. Diagnostic trace and line numbers intact. | [ ] |
| B.3 | Submit prompt injection override (Scenario P05) | Decision badge: `BLOCK` (Red). Prompt injection and credential tags present. Safe preview displays redacted marker or blocked notice. | [ ] |
| B.4 | Click "🚀 Authorize & Deliver to Client" on evaluated request | Release receipt generated showing request ID, destination ID, content version, and timestamp. Delivered flag toggles to `True`. | [ ] |
| B.5 | Repeat delivery on same request | Handled cleanly; one-use delivery controller prevents duplicate replay. | [ ] |

---

### Section C: Text Clipboard View (`📋 Text Clipboard`)

| Step | Action | Expected Visual & Functional Behavior | Status |
| :--- | :--- | :--- | :---: |
| C.1 | Verify Enrolled Host Information | Displays capture host ID (`mac-developer-workstation-01`). Local viewer platform clearly notes `Windows (viewer only - local capture UNSUPPORTED)`. | [ ] |
| C.2 | View SENSITIVE State (Scenario C04) | State badge displays `SENSITIVE` (Orange warning). Safe preview masks database password. Redacted summary explains detected high-entropy pattern. | [ ] |
| C.3 | Click "📋 Copy Cleaned Text" | In fixture mode, simulates sanitized copy; updates content version counter. Success toast appears without triggering recursive re-scan loop. | [ ] |
| C.4 | Toggle "Enable Text Capture" on/off | Toggles watcher status. Disabling clears transient previews and returns state to `OFF`. | [ ] |

---

### Section D: Capability Coverage Matrix (`📊 Integration Coverage`)

| Step | Action | Expected Visual & Functional Behavior | Status |
| :--- | :--- | :--- | :---: |
| D.1 | Inspect Coverage Table | Table lists all 12 planned paths per `docs/COVERAGE.md`. Status column uses distinct visual pills (`UNIMPLEMENTED`, `UNVERIFIED`, `VERIFIED`, `UNSUPPORTED`). | [ ] |
| D.2 | Verify Windows Capture Entry | Explicitly marked `UNSUPPORTED` with limitation: *"Native capture is implemented for macOS only. Windows dashboard is a remote viewer."* | [ ] |
| D.3 | Verify Screen Recording Entry | Explicitly marked `UNSUPPORTED` with limitation: *"Excluded by design. Privacy-first architecture rejects screen capture."* | [ ] |
| D.4 | Test Pill Filter | Selecting "UNSUPPORTED" filters table to show only unsupported boundary capabilities. | [ ] |

---

### Section E: Repair & Patches View (`🔧 Repair & Patches`)

| Step | Action | Expected Visual & Functional Behavior | Status |
| :--- | :--- | :--- | :---: |
| E.1 | Select Incident `inc-synthetic-102` | Incident title, failing signal, and status `READY_FOR_REVIEW` load. | [ ] |
| E.2 | Review Sandboxed Verification | Displays passed trusted tests (`pytest trusted_tests/test_cache.py -> 3 passed`). Safe observations list targeted defensive fix. | [ ] |
| E.3 | Inspect Candidate Patch Diff | Syntax-highlighted unified diff displays line additions and deletions in `devguard/cache/manager.py`. | [ ] |
| E.4 | Click "✅ Apply Patch to Repository" | Base hash is verified. Status transitions to `APPLIED`. Success notification confirms patch applied cleanly. | [ ] |
| E.5 | Click "❌ Reject Candidate" | Candidate status transitions to `REJECTED`. Working files remain untouched. | [ ] |

---

### Section F: Audit Event Log (`📜 Audit Event Log`)

| Step | Action | Expected Visual & Functional Behavior | Status |
| :--- | :--- | :--- | :---: |
| F.1 | View Event Timeline | Chronological event cards display timestamp, kind (`guard.decision`, `clipboard.changed`, `patch.state`), severity pill, and redacted summary. | [ ] |
| F.2 | Filter by Severity | Selecting `WARNING` hides `INFO` events and reveals sensitive pattern alerts. | [ ] |
| F.3 | Verify Safe Evidence Refs | Evidence references resolve to sanitized finding IDs (`finding-77-email`), never raw strings. | [ ] |

---

## 3. Automated dashboard regression coverage

The current integrated suite passed 210 tests, including all 44 collected UI tests; these are separate from live model experiments. The Streamlit operator dashboard invariants requested in `docs/tasks/MAC_2_WINDOWS_2_CONTINUATION.md` are continuously automated and verified under `tests/ui/`:

| Invariant / Check | Test Name | Result |
| :--- | :--- | :---: |
| **Failed replacement evaluation clears previous release cards** | `test_failed_replacement_evaluation_clears_previous_release_card` | **PASS** |
| **Incomplete, expired, or local-only evaluations offer no delivery release** | `test_incomplete_or_local_only_evaluations_offer_no_release` | **PASS** |
| **Fixture delivery state never leaks into freshly started sessions** | `test_fixture_delivery_does_not_leak_into_new_dashboard_session` | **PASS** |
| **Cleaned copy displays only acknowledged returned clipboard versions** | `test_cleaned_copy_displays_only_acknowledged_returned_version` | **PASS** |
| **Apply and reject actions never report unacknowledged success** | `test_patch_actions_do_not_report_unacknowledged_success` | **PASS** |
| **Disabling clipboard capture requires backend acknowledgement** | `test_capture_disable_requires_backend_acknowledgement` | **PASS** |
| **Live mode never loads fixture results; uninspected inputs are held** | `test_live_mode_never_loads_fixture_results_and_displays_held_evaluation` | **PASS** |
| **Unenrolled or malicious destination URLs rejected** | `test_live_client_rejects_unenrolled_destinations` | **PASS** |
| **Audit event timeline stream conforms to schema v1** | `test_audit_event_stream_fields` | **PASS** |
| **Incident review authority prevents unauthorized modification** | `test_incident_and_patch_review_authority` | **PASS** |

---

## 4. Results Recording & Live Trial Reporting

When executing live checks, record observations into `evals/results/results_registry.json` using the schema template `evals/results/template.json`. Leave unrun items strictly marked `UNRUN`. Reference trials executed on Apple Silicon hardware (e.g. Mac 1's 4 local reference checks and 38.24s Docker repair run) are documented with their exact digest and setup in `docs/MAC_1_READINESS_HANDOFF.md` and `docs/SUBMISSION_FINAL.md`.
