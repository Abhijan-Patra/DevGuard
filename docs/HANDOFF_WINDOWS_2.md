# Member 4 (Windows 2) Handoff Note & Integration Guide

**Author:** Member 4 (Windows 2 — Scenarios, QA & Demo)  
**Branch:** `codex/windows-qa`  
**PR:** [https://github.com/Abhijan-Patra/DevGuard/pull/new/codex/windows-qa](https://github.com/Abhijan-Patra/DevGuard/pull/new/codex/windows-qa)  
**Compliance Invariants:** AGENTS.md, API_CONTRACT.md, EVALUATION.md  

---

## 1. Deliverables Summary

Member 4 has completed the scenario specifications, results registry, demo fixtures, test runner, runbook, and submission draft:

| Component | Path | Status |
| :--- | :--- | :---: |
| **Privacy Scenarios (P01–P07)** | [`evals/cases/privacy_cases.json`](../evals/cases/privacy_cases.json) | Ready |
| **Clipboard Scenarios (C01–C06)** | [`evals/cases/clipboard_cases.json`](../evals/cases/clipboard_cases.json) | Ready |
| **Backend Repair Scenarios (B01–B08)** | [`evals/cases/repair_cases.json`](../evals/cases/repair_cases.json) | Ready |
| **Withheld Scenarios (W01–W05)** | [`evals/cases/withheld_variants.json`](../evals/cases/withheld_variants.json) | Ready (Withheld from prompts) |
| **Results Registry & Template** | [`evals/results/results_registry.json`](../evals/results/results_registry.json)<br>[`evals/results/template.json`](../evals/results/template.json) | Ready (`UNRUN`) |
| **Contract Timeline Events** | [`demo/fixtures/sample_events.json`](../demo/fixtures/sample_events.json) | Ready |
| **Demonstration Script & Scenarios** | [`demo/fixtures/demo_scenarios.json`](../demo/fixtures/demo_scenarios.json) | Ready |
| **Backend Repair Oracles** | [`demo/fixtures/backend_oracles.json`](../demo/fixtures/backend_oracles.json) | Ready |
| **Evaluation Test Harness** | [`evals/runner.py`](../evals/runner.py)<br>[`tests/ui/test_qa_fixtures_and_evals.py`](../tests/ui/test_qa_fixtures_and_evals.py) | Verified (25/25 tests PASS) |
| **Live Demo Runbook** | [`docs/DEMO_RUNBOOK.md`](DEMO_RUNBOOK.md) | Ready |
| **1-Click Demo Launchers** | [`demo/run_demo.ps1`](../demo/run_demo.ps1)<br>[`demo/run_demo.bat`](../demo/run_demo.bat) | Ready |
| **Mock Live Server (Offline)** | [`demo/mock_live_server.py`](../demo/mock_live_server.py) | Ready (Port 8765) |
| **Hackathon Submission Final** | [`docs/SUBMISSION_FINAL.md`](SUBMISSION_FINAL.md) | Complete |
| **Pre-Submission Freeze Checklist** | [`docs/FINAL_FREEZE_CHECKLIST.md`](FINAL_FREEZE_CHECKLIST.md) | Verified |
| **QA Summary Report** | [`evals/QA_SUMMARY.md`](../evals/QA_SUMMARY.md) | Ready |

---

## 2. Instructions for Teammates

### For Member 1 (Mac 1 — Backend Guard & Gemma)
1. **Live Model Validation:** Run local Gemma 4 E4B (`gemma4:e4b-it-q4_K_M`) against the inputs in `evals/cases/privacy_cases.json`.
2. **Measurement Recording:** Confirm cold/warm token latency and detector TP/FP counts; update `evals/results/results_registry.json`.
3. **Withheld Check:** Test against `evals/cases/withheld_variants.json` to verify model generalization on unseen prompts.

### For Member 2 (Mac 2 — Backend Repair & Sandbox)
1. **Oracle Conformance:** Use `demo/fixtures/backend_oracles.json` to define and verify your independent trusted tests in `trusted_tests/`.
2. **Reproducible Failure:** Verify that `demo/backend/cart.py` fails on baseline and passes after candidate patch application in Docker sandbox.
3. **Stale Safety:** Verify that modifying working tree files triggers HTTP 409 `STALE_CONTENT` on patch apply.

### For Member 3 (Windows 1 — Streamlit UI)
1. **Event Timeline:** Load sample contract events from `demo/fixtures/sample_events.json`.
2. **Demo Sequence:** Follow the 4-step sequence in `demo/fixtures/demo_scenarios.json` and `docs/DEMO_RUNBOOK.md`.

---

## 3. Current Gaps & Unrun Items

Per AGENTS.md, synthetic fixture specifications are not model proof:
- **All 26 cases are currently catalogued as `UNRUN`**.
- They will be updated to `PASS`/`FAIL` once Mac 1 and Mac 2 run live validation runs on Apple Silicon hardware with active Ollama inference.
- Final latency figures and memory profiles should be added to `docs/SUBMISSION_DRAFT.md` right before final submission freeze.
