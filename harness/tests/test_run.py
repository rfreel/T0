from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from harness.run import execute


class HarnessTests(unittest.TestCase):
    def run_manifest(self, manifest: dict) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "manifest.json"
            results = root / "results"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            code = execute(path, root, results)
            report = json.loads(
                (results / "results.json").read_text(encoding="utf-8")
            )
            self.assertTrue((results / "junit.xml").is_file())
            return code, report

    def test_passing_check_writes_evidence(self) -> None:
        code, report = self.run_manifest(
            {
                "version": 1,
                "checks": [
                    {
                        "id": "pass",
                        "command": [sys.executable, "-c", "print('READY')"],
                        "expect": {"stdout_contains": ["READY"]},
                    }
                ],
            }
        )
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["checks_passed"], 1)

    def test_failed_exit_is_not_false_pass(self) -> None:
        code, report = self.run_manifest(
            {
                "version": 1,
                "checks": [
                    {
                        "id": "fail",
                        "command": [
                            sys.executable,
                            "-c",
                            "raise SystemExit(3)",
                        ],
                    }
                ],
            }
        )
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            "exit code 3",
            report["results"][0]["assertion_failures"][0],
        )

    def test_required_file_is_checked_after_execution(self) -> None:
        code, report = self.run_manifest(
            {
                "version": 1,
                "checks": [
                    {
                        "id": "artifact",
                        "command": [
                            sys.executable,
                            "-c",
                            "from pathlib import Path; "
                            "Path('proof.txt').write_text('ok')",
                        ],
                        "expect": {"required_files": ["proof.txt"]},
                    }
                ],
            }
        )
        self.assertEqual(code, 0)
        self.assertEqual(report["results"][0]["status"], "PASS")

    def test_timeout_is_failure(self) -> None:
        code, report = self.run_manifest(
            {
                "version": 1,
                "checks": [
                    {
                        "id": "timeout",
                        "command": [
                            sys.executable,
                            "-c",
                            "import time; time.sleep(0.2)",
                        ],
                        "timeout_seconds": 0.05,
                    }
                ],
            }
        )
        self.assertEqual(code, 1)
        self.assertTrue(report["results"][0]["timed_out"])


if __name__ == "__main__":
    unittest.main()
