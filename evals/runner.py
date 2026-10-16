#!/usr/bin/env python3
"""DevGuard catalogue and registry status reporter; does not execute scenarios.

Owner: Member 4 (Windows 2 - Scenarios & QA).
Provides command-line catalogue consistency reporting,
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
    """Report catalogue/registry consistency; this does not execute scenarios."""
    registry = json.loads((RESULTS_DIR / "results_registry.json").read_text())["results"]
    expected = [case["id"] for cases in scenarios.values() for case in cases]
    observed = [record["case_id"] for record in registry]
    if (len(expected) != len(set(expected)) or len(observed) != len(set(observed))
            or set(expected) != set(observed)):
        raise ValueError("Catalogue and result registry IDs do not match uniquely")
    statuses = {"UNRUN": 0, "PASS": 0, "FAIL": 0, "BLOCKED": 0}
    by_id = {record["case_id"]: record for record in registry}
    for cases in scenarios.values():
        for case in cases:
            status = by_id[case["id"]]["status"]
            if status not in statuses or status != case.get("execution_status", "UNRUN"):
                raise ValueError("Catalogue and result status disagree")
            statuses[status] += 1
    rows = "\n".join(f"| {name} | {len(cases)} |" for name, cases in sorted(scenarios.items()))
    return f"""# DevGuard QA status — 16 October 2026

Catalogue reporting is separate from real-model experiments. This command does not run the scenarios or mark any pass. Mac 2 continues Windows 2's assigned QA/demo scope.

| Catalogue file | Cases |
|---|---:|
{rows}

**Registry:** {len(registry)} unique records; UNRUN {statuses['UNRUN']}, PASS {statuses['PASS']}, FAIL {statuses['FAIL']}, BLOCKED {statuses['BLOCKED']}. Catalogue IDs/statuses match the registry. Withheld inputs remain outside runtime prompts/tuning. Fixture/schema tests do not execute these cases.

## Separate measured evidence

- Integrated automated suite: **209 passed**, one existing dependency deprecation warning; pip check clean. These include mocked model/verifier ports and are not an accuracy benchmark.
- Real Gemma/guard/API/Docker cart trial: baseline FAIL -> genuine patch -> independent PASS -> disposable approved apply -> idempotent repeat -> post-apply PASS; 46.07 s; original/tests unchanged and worker stopped. See [repair evidence](../devguard/repair/README.md).
- Real stale/cancel trial: 409 STALE_SOURCE, concurrent edit preserved, state OBSOLETE; queued cancel produced no candidate; 42.19 s.
- Mac 2 isolated named pasteboard: all 12 checks passed, 1.550 s copy-to-finding, no general clipboard access. See [metadata](results/mac2-private-pasteboard.json).
- Mac 2 consented general clipboard combined input: HELD/REVIEW, cleaned-copy not executed; capture OFF. The failed input remains in [metadata](../devguard/repair/verification/mac2-system-clipboard-held.json).
- Mac 2 real local reference receiver + five live views: PASS, replay held, 1.282 s synthetic privacy evaluation; see [metadata](results/mac2-live-dashboard.json). Mac 1 separately records its own [measurements](../docs/MAC_1_WINDOWS_1_COMPLETION.md).

These experiments are not retrospectively assigned catalogue passes: some older catalogue test names/field names are conceptual and do not match the cart manifest. Preserve expected behavior and reconcile each mapping before future execution. No privacy precision/recall, full unseen evaluation, production recovery or installed-client interception result is claimed.

See [runbook](../docs/DEMO_RUNBOOK.md), [evaluation](../docs/EVALUATION.md) and [submission text](../docs/SUBMISSION_FINAL.md). Mock server data is rehearsal only; the live UI requires the actual backend contract.
"""


def check_live_health(base_url="http://127.0.0.1:8765/api/v1"):
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
    parser.add_argument("--base-url", default="http://127.0.0.1:8765/api/v1", help="DevGuard API Base URL")
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
