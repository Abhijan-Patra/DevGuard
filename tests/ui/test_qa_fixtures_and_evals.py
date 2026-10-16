"""Unit tests for Member 4 (Windows 2 - Scenarios, QA & Demo) deliverables.

Validates that:
- All scenario specifications load and adhere to synthetic testing invariants.
- No scenario contains unredacted or live secrets.
- All evaluation results are marked UNRUN.
- Demo fixtures and backend repair oracles match API Contract v1.
"""

import json
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestMember4ScenariosAndQA(unittest.TestCase):
    def test_privacy_scenarios_schema(self):
        cases_file = REPO_ROOT / "evals" / "cases" / "privacy_cases.json"
        self.assertTrue(cases_file.exists(), "privacy_cases.json must exist")

        with open(cases_file, "r", encoding="utf-8") as f:
            cases = json.load(f)

        self.assertGreaterEqual(len(cases), 7, "Must contain at least P01-P07")
        case_ids = {c["id"] for c in cases}
        for expected_id in ["P01", "P02", "P03", "P04", "P05", "P06", "P07"]:
            self.assertIn(expected_id, case_ids)

        for case in cases:
            self.assertTrue(case["synthetic_fixture"], f"{case['id']} must declare synthetic_fixture=True")
            self.assertEqual(case["execution_status"], "UNRUN", f"{case['id']} status must be UNRUN")
            self.assertIn(case["expected_decision"], ["ALLOW", "SANITIZE", "LOCAL_ONLY", "REVIEW", "BLOCK"])
            # Invariant: example domains should use .invalid
            if "@" in case["synthetic_input"]:
                self.assertIn(".invalid", case["synthetic_input"], f"{case['id']} email must use .invalid domain")

    def test_clipboard_scenarios_schema(self):
        cases_file = REPO_ROOT / "evals" / "cases" / "clipboard_cases.json"
        self.assertTrue(cases_file.exists(), "clipboard_cases.json must exist")

        with open(cases_file, "r", encoding="utf-8") as f:
            cases = json.load(f)

        self.assertGreaterEqual(len(cases), 6, "Must contain at least C01-C06")
        case_ids = {c["id"] for c in cases}
        for expected_id in ["C01", "C02", "C03", "C04", "C05", "C06"]:
            self.assertIn(expected_id, case_ids)

        for case in cases:
            self.assertTrue(case["synthetic_fixture"])
            self.assertEqual(case["execution_status"], "UNRUN")

    def test_repair_scenarios_schema(self):
        cases_file = REPO_ROOT / "evals" / "cases" / "repair_cases.json"
        self.assertTrue(cases_file.exists(), "repair_cases.json must exist")

        with open(cases_file, "r", encoding="utf-8") as f:
            cases = json.load(f)

        self.assertGreaterEqual(len(cases), 8, "Must contain at least B01-B08")
        case_ids = {c["id"] for c in cases}
        for expected_id in ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08"]:
            self.assertIn(expected_id, case_ids)

        for case in cases:
            self.assertTrue(case["synthetic_fixture"])
            self.assertEqual(case["execution_status"], "UNRUN")

    def test_withheld_variants_present(self):
        withheld_file = REPO_ROOT / "evals" / "cases" / "withheld_variants.json"
        self.assertTrue(withheld_file.exists(), "withheld_variants.json must exist")

        with open(withheld_file, "r", encoding="utf-8") as f:
            variants = json.load(f)

        self.assertGreaterEqual(len(variants), 5, "Must contain withheld variants W01-W05")
        for v in variants:
            self.assertTrue(v["withheld_variant"])
            self.assertEqual(v["execution_status"], "UNRUN")

    def test_results_registry_consistency(self):
        registry_file = REPO_ROOT / "evals" / "results" / "results_registry.json"
        self.assertTrue(registry_file.exists(), "results_registry.json must exist")

        with open(registry_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        results = data["results"]
        registered_ids = {r["case_id"] for r in results}

        # Check all core cases exist in registry
        for cid in ["P01", "P02", "P03", "P04", "P05", "P06", "P07",
                    "C01", "C02", "C03", "C04", "C05", "C06",
                    "B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08"]:
            self.assertIn(cid, registered_ids)

        for entry in results:
            self.assertEqual(entry["status"], "UNRUN", "All results must initially be marked UNRUN")
            self.assertIsNotNone(entry["limitations"])

    def test_demo_fixtures_and_oracles(self):
        events_file = REPO_ROOT / "demo" / "fixtures" / "sample_events.json"
        scenarios_file = REPO_ROOT / "demo" / "fixtures" / "demo_scenarios.json"
        oracles_file = REPO_ROOT / "demo" / "fixtures" / "backend_oracles.json"

        self.assertTrue(events_file.exists())
        self.assertTrue(scenarios_file.exists())
        self.assertTrue(oracles_file.exists())

        with open(events_file, "r", encoding="utf-8") as f:
            events = json.load(f)
        for ev in events:
            self.assertEqual(ev["schema_version"], "v1")
            self.assertIn("event_id", ev)
            self.assertIn("kind", ev)

        with open(oracles_file, "r", encoding="utf-8") as f:
            oracles_data = json.load(f)
        self.assertIn("oracles", oracles_data)
        self.assertGreaterEqual(len(oracles_data["oracles"]), 6)


if __name__ == "__main__":
    unittest.main()
