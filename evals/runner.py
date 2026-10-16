#!/usr/bin/env python3
"""DevGuard Member 4 Evaluation Runner & Status Reporter.

Owner: Member 4 (Windows 2 - Scenarios & QA).
Provides command-line evaluation reporting, scenario verification,
and live backend integration checks per docs/EVALUATION.md and AGENTS.md.
"""

import argparse
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

REPO_ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = REPO_ROOT / "evals" / "cases"
RESULTS_DIR = REPO_ROOT / "evals" / "results"
FIXTURES_DIR = REPO_ROOT / "demo" / "fixtures"


def load_all_scenarios():
    scenarios = {}
    for case_file in CASES_DIR.glob("*.json"):
        with open(case_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            scenarios[case_file.stem] = data
    return scenarios


def generate_qa_summary(scenarios):
    total_cases = 0
    categories = {}
    status_counts = {"UNRUN": 0, "PASS": 0, "FAIL": 0, "BLOCKED": 0}

    for group, case_list in scenarios.items():
        for case in case_list:
            total_cases += 1
            cat = case.get("category", "OTHER")
            categories[cat] = categories.get(cat, 0) + 1
            status = case.get("execution_status", "UNRUN")
            status_counts[status] = status_counts.get(status, 0) + 1

    summary_text = f"""# DevGuard Evaluation & QA Summary Report

**Owner:** Member 4 (Windows 2 - Scenarios, QA & Demo)  
**Branch:** `codex/windows-qa`  
**Compliance Standard:** AGENTS.md, API_CONTRACT.md, EVALUATION.md  

---

## 1. Executive Summary

| Metric | Count | Notes |
| :--- | :---: | :--- |
| **Total Test Scenarios** | **{total_cases}** | Defined across 4 catalog files in `evals/cases/` |
| **Execution Status: UNRUN** | **{status_counts.get('UNRUN', 0)}** | Marked UNRUN per AGENTS.md invariant (synthetic data is not model proof) |
| **Execution Status: PASS** | **{status_counts.get('PASS', 0)}** | Requires live Mac 1 / Mac 2 execution harness |
| **Execution Status: FAIL/BLOCKED** | **{status_counts.get('FAIL', 0) + status_counts.get('BLOCKED', 0)}** | Zero simulated failures |
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
"""
    return summary_text


def check_live_health(base_url="http://127.0.0.1:8000/api/v1"):
    url = f"{base_url.rstrip('/')}/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DevGuard-QA-Runner"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return True, data
    except Exception as exc:
        return False, str(exc)


def main():
    parser = argparse.ArgumentParser(description="DevGuard Evaluation & QA Harness")
    parser.add_argument("--summary", action="store_true", help="Print summary of all test scenarios")
    parser.add_argument("--generate-report", action="store_true", help="Generate evals/QA_SUMMARY.md")
    parser.add_argument("--check-live", action="store_true", help="Check local backend health")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1", help="DevGuard API Base URL")
    args = parser.parse_args()

    scenarios = load_all_scenarios()
    total_cases = sum(len(cases) for cases in scenarios.values())

    print(f"[*] DevGuard QA Harness loaded {total_cases} scenarios from {len(scenarios)} catalog files.")

    if args.check_live:
        print(f"[*] Checking live backend health at {args.base_url}...")
        alive, info = check_live_health(args.base_url)
        if alive:
            print(f"[+] Backend is ONLINE: {info}")
        else:
            print(f"[-] Backend is OFFLINE: {info}")
            print("    (Normal if Mac 1 server is not running locally on this machine).")

    if args.generate_report or len(sys.argv) == 1:
        report_path = REPO_ROOT / "evals" / "QA_SUMMARY.md"
        content = generate_qa_summary(scenarios)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] QA Summary Report generated at: {report_path}")

    if args.summary:
        print("\n--- SCENARIO CATALOGUE SUMMARY ---")
        for group, case_list in scenarios.items():
            print(f"\nGroup: {group} ({len(case_list)} scenarios)")
            for case in case_list:
                cid = case.get("id", "N/A")
                name = case.get("scenario_name", "N/A")
                status = case.get("execution_status", "UNRUN")
                print(f"  [{cid}] {name} (Status: {status})")


if __name__ == "__main__":
    main()
