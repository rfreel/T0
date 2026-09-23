from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluate import EvaluationError, ROOT, evaluate_candidate
from run import immutable_workspace_failures, workspace_structure_failures


class EvaluatorTests(unittest.TestCase):
    def write_candidate(self, payload: dict) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        with handle:
            json.dump(payload, handle)
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return Path(handle.name)

    def test_baseline_is_valid(self) -> None:
        result = evaluate_candidate(ROOT / "target/candidate/portfolio.json")
        self.assertTrue(result["accepted_by_evaluator"])
        self.assertEqual(result["hard_failures"], [])
        self.assertAlmostEqual(result["outcome_score"], 70.25, places=6)

    def test_verified_replacements_improve_score(self) -> None:
        candidate = self.write_candidate(
            {
                "version": 1,
                "decisions": [
                    {"service_id": "notes", "option_id": "notes_local_sync"},
                    {"service_id": "cloud_storage", "option_id": "cloud_bundle"},
                    {
                        "service_id": "automation",
                        "option_id": "automation_managed_lowcost",
                    },
                ],
            }
        )
        result = evaluate_candidate(candidate)
        self.assertTrue(result["accepted_by_evaluator"], result["hard_failures"])
        self.assertGreater(result["outcome_score"], 70.25)

    def test_unknown_option_is_rejected(self) -> None:
        candidate = self.write_candidate(
            {
                "version": 1,
                "decisions": [
                    {"service_id": "notes", "option_id": "invented"},
                    {"service_id": "cloud_storage", "option_id": "cloud_current"},
                    {"service_id": "automation", "option_id": "automation_current"},
                ],
            }
        )
        result = evaluate_candidate(candidate)
        self.assertFalse(result["accepted_by_evaluator"])
        self.assertTrue(any("unknown option" in x for x in result["hard_failures"]))

    def test_missing_service_is_rejected(self) -> None:
        candidate = self.write_candidate(
            {
                "version": 1,
                "decisions": [
                    {"service_id": "notes", "option_id": "notes_current"},
                    {"service_id": "cloud_storage", "option_id": "cloud_current"},
                ],
            }
        )
        result = evaluate_candidate(candidate)
        self.assertFalse(result["accepted_by_evaluator"])
        self.assertIn("missing decision for service automation", result["hard_failures"])

    def test_candidate_schema_is_closed(self) -> None:
        candidate = self.write_candidate(
            {
                "version": 1,
                "decisions": [],
                "claimed_score": 100,
            }
        )
        with self.assertRaises(EvaluationError):
            evaluate_candidate(candidate)


class WorkspaceIntegrityTests(unittest.TestCase):
    def test_immutable_change_is_detected(self) -> None:
        before = {
            "AGENTS.md": "a",
            "context/evaluate.py": "b",
            "candidate/portfolio.json": "c",
        }
        after = {
            "AGENTS.md": "changed",
            "context/evaluate.py": "b",
            "candidate/portfolio.json": "new",
        }
        failures = immutable_workspace_failures(
            before,
            after,
            {"candidate/portfolio.json"},
        )
        self.assertEqual(failures, ["immutable file changed: AGENTS.md"])

    def test_unexpected_file_is_detected(self) -> None:
        before = {"AGENTS.md": "a"}
        after = {"AGENTS.md": "a", "escape.txt": "x"}
        failures = immutable_workspace_failures(before, after, set())
        self.assertEqual(failures, ["unexpected file created: escape.txt"])

    def test_symbolic_link_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "real.txt").write_text("x", encoding="utf-8")
            (root / "link.txt").symlink_to(root / "real.txt")
            failures = workspace_structure_failures(root)
            self.assertIn("symbolic link is forbidden: link.txt", failures)


if __name__ == "__main__":
    unittest.main()
