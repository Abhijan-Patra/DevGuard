# DevGuard — Final Pre-Submission Freeze Checklist

**Owner:** Member 4 (Windows 2 — Scenarios, QA & Demo)  
**Target Deadline:** 1 Hour Before Hackathon Submission Freeze  
**Repository:** [https://github.com/Abhijan-Patra/DevGuard](https://github.com/Abhijan-Patra/DevGuard)  

---

## 1. Repository Cleanliness & Secret Safety

- [x] **No Private Secrets in Commits:**
  - Verified with `git log` and ripgrep.
  - All test fixtures use synthetic credentials (e.g., `ghp_synthetic_pat_...`, `.invalid` domains).
- [x] **No Active Database Files Committed:**
  - `.devguard/` directory is in `.gitignore`.
  - No `audit.sqlite3`, `session-token`, or transient cache files in git status.
- [x] **Working Tree Cleanliness:**
  - No unstaged edits or residual test artifacts.
  - All temporary files stored under ignored or temporary paths.
- [x] **License Notice:**
  - MIT License present in root `LICENSE` file.

---

## 2. Model & Architecture Specifications

- [x] **Model Pinned:**
  - Ollama model digest: `gemma4:e4b-it-q4_K_M`
  - Context size bounded: `num_ctx: 4096`
  - Deterministic temperature: `temperature: 0`
  - Output token budget: 512 (privacy prompts), 1024 (code repairs)
  - Thinking parameter disabled: `think: false`
- [x] **Dual Agent Priority Queue:**
  - Foreground privacy gate runs with immediate priority over background repair jobs.
- [x] **Fail-Closed Privacy Gate:**
  - Any model unavailability, timeout, or invalid span holds the request (`decision: REVIEW`).
  - No uninspected bytes delivered downstream.

---

## 3. Evaluation & QA Coverage

- [x] **Scenario Catalogue Complete (26 Scenarios):**
  - `evals/cases/privacy_cases.json`: 7 cases (P01–P07)
  - `evals/cases/clipboard_cases.json`: 6 cases (C01–C06)
  - `evals/cases/repair_cases.json`: 8 cases (B01–B08)
  - `evals/cases/withheld_variants.json`: 5 cases (W01–W05)
- [x] **Results Registry & Honesty Invariant:**
  - All 26 scenario records in `evals/results/results_registry.json` are marked `UNRUN` per AGENTS.md invariant.
  - No invented or fabricated model benchmarks.
- [x] **Automated Test Suite:**
  - `python -m pytest tests/ui/ -v` passes **25/25 tests** without errors.
  - Full test suite contains 143 tests across backend, storage, repair, and UI.

---

## 4. Live Demo & Presentation Tools

- [x] **Port Standardization:**
  - All endpoints and docs standardized to official port **8765** (`http://127.0.0.1:8765/api/v1`).
- [x] **1-Click Launchers:**
  - `demo/run_demo.ps1` (PowerShell launcher for Windows)
  - `demo/run_demo.bat` (Batch launcher for Windows CMD)
- [x] **Zero-Dependency Mock Live Server:**
  - `demo/mock_live_server.py` runs standalone on port 8765 for offline demonstration rehearsal.
- [x] **3-Minute Rehearsable Runbook:**
  - `docs/DEMO_RUNBOOK.md` complete with timing, failure branches, and talking points.

---

## 5. Submission Documents

- [x] **Draft Submission:** `docs/SUBMISSION_DRAFT.md`
- [x] **Final Submission Package:** `docs/SUBMISSION_FINAL.md`
- [x] **Team Integration Handoff:** `docs/HANDOFF_WINDOWS_2.md`
- [x] **QA Summary Report:** `evals/QA_SUMMARY.md`

---

## 6. How the Team Finalizes & Submits

1. **Verify Git Status:**
   ```powershell
   git status
   ```
2. **Run Final QA Report:**
   ```powershell
   python evals/runner.py --generate-report
   ```
3. **Run UI Test Suite:**
   ```powershell
   python -m pytest tests/ui/ -v
   ```
4. **Push Branch & Open PR:**
   ```powershell
   git push origin codex/windows-qa-freeze
   ```
5. **Paste Final Submission Text:**
   Copy the contents of `docs/SUBMISSION_FINAL.md` directly into the hackathon submission form.
