from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

CHECK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
MAX_CAPTURE_CHARS = 50_000


class ManifestError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _within(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _require_list_of_strings(
    value: Any, field: str, *, allow_empty: bool = True
) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ManifestError(f"{field} must be a list of strings")
    if not allow_empty and not value:
        raise ManifestError(f"{field} must not be empty")
    return value


def load_manifest(path: Path, repo_root: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ManifestError("manifest root must be an object")
    if data.get("version") != 1:
        raise ManifestError("manifest version must be 1")

    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ManifestError("manifest checks must be a non-empty list")

    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(checks):
        prefix = f"checks[{index}]"
        if not isinstance(raw, dict):
            raise ManifestError(f"{prefix} must be an object")

        check_id = raw.get("id")
        if not isinstance(check_id, str) or not CHECK_ID.fullmatch(check_id):
            raise ManifestError(f"{prefix}.id is invalid")
        if check_id in seen:
            raise ManifestError(f"duplicate check id: {check_id}")
        seen.add(check_id)

        command = _require_list_of_strings(
            raw.get("command"), f"{prefix}.command", allow_empty=False
        )

        cwd_text = raw.get("cwd", ".")
        if not isinstance(cwd_text, str) or not cwd_text:
            raise ManifestError(f"{prefix}.cwd must be a non-empty string")
        cwd = (repo_root / cwd_text).resolve()
        if not _within(repo_root, cwd):
            raise ManifestError(f"{prefix}.cwd escapes repository root")

        timeout = raw.get("timeout_seconds", 300)
        if (
            not isinstance(timeout, (int, float))
            or isinstance(timeout, bool)
            or timeout <= 0
        ):
            raise ManifestError(f"{prefix}.timeout_seconds must be positive")
        if timeout > 3600:
            raise ManifestError(f"{prefix}.timeout_seconds exceeds 3600")

        expect = raw.get("expect", {})
        if not isinstance(expect, dict):
            raise ManifestError(f"{prefix}.expect must be an object")
        exit_code = expect.get("exit_code", 0)
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            raise ManifestError(f"{prefix}.expect.exit_code must be an integer")

        required_files = _require_list_of_strings(
            expect.get("required_files", []),
            f"{prefix}.expect.required_files",
        )
        assertion_fields = (
            "stdout_contains",
            "stderr_contains",
            "combined_contains",
            "stdout_not_contains",
            "stderr_not_contains",
            "combined_not_contains",
        )
        for field in assertion_fields:
            _require_list_of_strings(expect.get(field, []), f"{prefix}.expect.{field}")

        normalized.append(
            {
                "id": check_id,
                "command": command,
                "cwd": cwd,
                "cwd_display": cwd.relative_to(repo_root.resolve()).as_posix() or ".",
                "timeout_seconds": float(timeout),
                "expect": {
                    "exit_code": exit_code,
                    "required_files": required_files,
                    **{field: expect.get(field, []) for field in assertion_fields},
                },
            }
        )

    return {"version": 1, "checks": normalized}


def _clip(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_CAPTURE_CHARS:
        return text, False
    return text[-MAX_CAPTURE_CHARS:], True


def _assertions(
    check: dict[str, Any],
    returncode: int | None,
    stdout: str,
    stderr: str,
    timed_out: bool,
) -> list[str]:
    expect = check["expect"]
    failures: list[str] = []
    if timed_out:
        failures.append(f"timed out after {check['timeout_seconds']:g}s")
    if returncode != expect["exit_code"]:
        failures.append(f"exit code {returncode} != expected {expect['exit_code']}")

    combined = stdout + "\n" + stderr
    for stream_name, text in (
        ("stdout", stdout),
        ("stderr", stderr),
        ("combined", combined),
    ):
        for needle in expect[f"{stream_name}_contains"]:
            if needle not in text:
                failures.append(f"{stream_name} missing required text: {needle!r}")
        for needle in expect[f"{stream_name}_not_contains"]:
            if needle in text:
                failures.append(f"{stream_name} contains forbidden text: {needle!r}")

    for relative in expect["required_files"]:
        candidate = (check["cwd"] / relative).resolve()
        if not _within(check["cwd"], candidate):
            failures.append(f"required file escapes check cwd: {relative}")
        elif not candidate.is_file():
            failures.append(f"required file missing: {relative}")
    return failures


def run_check(check: dict[str, Any]) -> dict[str, Any]:
    started_at = utc_now()
    start = time.monotonic()
    timed_out = False
    returncode: int | None
    stdout = ""
    stderr = ""

    if not check["cwd"].is_dir():
        returncode = None
        failures = [f"cwd does not exist: {check['cwd_display']}"]
    else:
        try:
            completed = subprocess.run(
                check["command"],
                cwd=check["cwd"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=check["timeout_seconds"],
                check=False,
                env=os.environ.copy(),
            )
            returncode = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            returncode = None
            stdout = (
                exc.stdout.decode()
                if isinstance(exc.stdout, bytes)
                else (exc.stdout or "")
            )
            stderr = (
                exc.stderr.decode()
                if isinstance(exc.stderr, bytes)
                else (exc.stderr or "")
            )
        except OSError as exc:
            returncode = None
            stderr = f"{type(exc).__name__}: {exc}"
        failures = _assertions(check, returncode, stdout, stderr, timed_out)

    duration = time.monotonic() - start
    stdout, stdout_truncated = _clip(stdout)
    stderr, stderr_truncated = _clip(stderr)
    return {
        "id": check["id"],
        "status": "PASS" if not failures else "FAIL",
        "command": check["command"],
        "cwd": check["cwd_display"],
        "started_at": started_at,
        "duration_seconds": round(duration, 6),
        "returncode": returncode,
        "timed_out": timed_out,
        "assertion_failures": failures,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
    }


def write_junit(path: Path, results: list[dict[str, Any]]) -> None:
    failures = sum(result["status"] == "FAIL" for result in results)
    suite = ET.Element(
        "testsuite",
        {
            "name": "t0-acceptance-harness",
            "tests": str(len(results)),
            "failures": str(failures),
            "errors": "0",
            "time": f"{sum(r['duration_seconds'] for r in results):.6f}",
        },
    )
    for result in results:
        case = ET.SubElement(
            suite,
            "testcase",
            {
                "classname": "acceptance",
                "name": result["id"],
                "time": f"{result['duration_seconds']:.6f}",
            },
        )
        if result["status"] == "FAIL":
            failure = ET.SubElement(
                case,
                "failure",
                {"message": "; ".join(result["assertion_failures"])},
            )
            failure.text = "\n".join(result["assertion_failures"])
        stdout = ET.SubElement(case, "system-out")
        stdout.text = result["stdout"]
        stderr = ET.SubElement(case, "system-err")
        stderr.text = result["stderr"]
    ET.ElementTree(suite).write(path, encoding="utf-8", xml_declaration=True)


def execute(
    manifest_path: Path,
    repo_root: Path,
    results_dir: Path,
    selected_ids: set[str] | None = None,
    fail_fast: bool = False,
) -> int:
    manifest = load_manifest(manifest_path, repo_root)
    checks = manifest["checks"]
    if selected_ids:
        available = {check["id"] for check in checks}
        missing = sorted(selected_ids - available)
        if missing:
            raise ManifestError("unknown check id(s): " + ", ".join(missing))
        checks = [check for check in checks if check["id"] in selected_ids]

    results_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for check in checks:
        result = run_check(check)
        results.append(result)
        print(f"[{result['status']}] {result['id']} ({result['duration_seconds']:.3f}s)")
        if result["status"] == "FAIL":
            for failure in result["assertion_failures"]:
                print(f"  - {failure}")
            if fail_fast:
                break

    report = {
        "schema_version": 1,
        "status": "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL",
        "generated_at": utc_now(),
        "repository": os.getenv("GITHUB_REPOSITORY"),
        "git_sha": os.getenv("GITHUB_SHA"),
        "manifest": str(manifest_path),
        "selected_ids": sorted(selected_ids) if selected_ids else None,
        "checks_run": len(results),
        "checks_passed": sum(r["status"] == "PASS" for r in results),
        "checks_failed": sum(r["status"] == "FAIL" for r in results),
        "results": results,
    }
    (results_dir / "results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_junit(results_dir / "junit.xml", results)
    return 0 if report["status"] == "PASS" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run repository acceptance checks from a JSON manifest."
    )
    parser.add_argument("--manifest", default="harness/manifest.json")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--results-dir", default="harness/results")
    parser.add_argument(
        "--check",
        action="append",
        dest="checks",
        help="Run only this check id; repeatable.",
    )
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--list", action="store_true", dest="list_checks")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    manifest_path = (repo_root / args.manifest).resolve()
    results_dir = (repo_root / args.results_dir).resolve()
    try:
        manifest = load_manifest(manifest_path, repo_root)
        if args.list_checks:
            for check in manifest["checks"]:
                print(check["id"])
            return 0
        return execute(
            manifest_path,
            repo_root,
            results_dir,
            set(args.checks) if args.checks else None,
            args.fail_fast,
        )
    except ManifestError as exc:
        print(f"manifest error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
