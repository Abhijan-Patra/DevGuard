# DevGuard Evaluation & QA Summary Report

**Owner:** Member 4 (Windows 2 - Scenarios, QA & Demo)  
**Branch:** `codex/windows-qa`  
**Compliance Standard:** AGENTS.md, API_CONTRACT.md, EVALUATION.md  

---

## 1. Executive Summary

| Metric | Count | Notes |
| :--- | :---: | :--- |
| **Total Test Scenarios** | **26** | Defined across 4 catalog files in `evals/cases/` |
| **Execution Status: UNRUN** | **26** | Marked UNRUN per AGENTS.md invariant (synthetic data is not model proof) |
| **Execution Status: PASS** | **0** | Requires live Mac 1 / Mac 2 execution harness |
| **Execution Status: FAIL/BLOCKED** | **0** | Zero simulated failures |
| **Withheld Evaluation Scenarios** | **5** | Kept out of model prompt tuning (`W01`–`W05`) |

---

## 2. Breakdown by Category

| Category | File | Cases | Target Capabilities |
| :--- | :--- | :---: | :--- |
| **PRIVACY_GUARD** | `evals/cases/privacy_cases.json` | 7 | P01–P07: Credential detection, benign constants, confidential prose, customer PII stack trace, prompt injection override, path traversal, model timeout |
| **CLIPBOARD** | `evals/cases/clipboard_cases.json` | 6 | C01–C06: Opt-in consent, counter deduplication, rapid copy overwrite, copy-cleaned cycle, oversize skip, unmanaged paste boundary |
| **BACKEND_REPAIR** | `evals/cases/repair_cases.json` | 8 | B01–B08: Null item crash, quantity multiplication, empty cart, missing dependencies, stale 409 conflict, verifier immutability, idempotency, healthy backend |
| **WITHHELD_VARIANTS** | `evals/cases/withheld_variants.json` | 5 | W01–W05: Custom delimitation secret, health PII in SQL comments, discount calculation, zero-width injection, off-by-one boundary |

---

## 3. Demo Fixtures & Backend Oracles

| Asset | Path | Intended Consumer | Purpose |
| :--- | :--- | :--- | :--- |
| **Sample Events** | `demo/fixtures/sample_events.json` | Windows 1 (UI) | Contract v1 timeline presentation |
| **Walkthrough Scenarios** | `demo/fixtures/demo_scenarios.json` | Judges / Operators | Rehearsable live demonstration steps |
| **Repair Test Oracles** | `demo/fixtures/backend_oracles.json` | Mac 2 (Repair) | Ground-truth expected output specs |

---

## 4. Current Gaps & Live Handoff Next Steps

1. **Mac 1 Live Trial:** Run `gemma4:e4b-it-q4_K_M` trial against `privacy_cases.json`. Record actual TP/FP counts and token-to-decision latency in `evals/results/results_registry.json`.
2. **Mac 2 Repair Sandbox:** Mount `trusted_tests/test_cart.py` against `backend_oracles.json` inside Docker container and execute baseline failure.
3. **Windows 1 UI Connection:** Connect Streamlit client to live backend; test 409 stale conflict alert and copy-cleaned flow.
