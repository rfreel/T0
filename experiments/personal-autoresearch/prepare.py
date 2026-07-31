#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluate import EvaluationError, evaluate_candidate

ROOT = Path(__file__).resolve().parent
STATE_DIR = ROOT / ".autoresearch"
LOCK_PATH = STATE_DIR / "lock.json"
RESULTS_PATH = STATE_DIR / "results.tsv"
BASELINE_PATH = STATE_DIR / "baseline.json"
RUNS_DIR = STATE_DIR / "runs"


class PreparationError(RuntimeError):
    pass


def load_config() -> dict[str, Any]:
    try:
        return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise PreparationError(f"cannot load config.json: {exc}") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def git_available() -> bool:
    try:
        result = run_git("rev-parse", "--is-inside-work-tree", check=False)
    except FileNotFoundError:
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def current_branch() -> str:
    result = run_git("branch", "--show-current")
    branch = result.stdout.strip()
    if not branch:
        raise PreparationError("detached HEAD is not an experiment branch")
    return branch


def default_branch_candidates() -> set[str]:
    names = {"main", "master"}
    result = run_git("symbolic-ref", "refs/remotes/origin/HEAD", check=False)
    if result.returncode == 0 and result.stdout.strip():
        names.add(result.stdout.strip().rsplit("/", 1)[-1])
    return names


def ensure_clean_worktree() -> None:
    result = run_git("status", "--porcelain")
    lines = [line for line in result.stdout.splitlines() if ".autoresearch/" not in line]
    if lines:
        raise PreparationError(
            "working tree contains uncommitted files; commit or stash them before setup:\n"
            + "\n".join(lines[:20])
        )


def create_experiment_branch(tag: str) -> str:
    if not tag or any(ch.isspace() for ch in tag):
        raise PreparationError("tag must be a nonempty branch-safe token")
    branch = f"autoresearch/{tag}"
    exists = run_git("show-ref", "--verify", f"refs/heads/{branch}", check=False)
    if exists.returncode == 0:
        raise PreparationError(f"branch already exists: {branch}")
    ensure_clean_worktree()
    run_git("checkout", "-b", branch)
    return branch


def lock_input_paths(config: dict[str, Any]) -> list[Path]:
    paths = [ROOT / value for value in config["locked_files"]]
    paths.append(ROOT / config["inventory_file"])
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            unique.append(path)
            seen.add(resolved)
    return unique


def build_lock_manifest(config: dict[str, Any]) -> dict[str, Any]:
    files: dict[str, str] = {}
    for path in lock_input_paths(config):
        if not path.is_file():
            raise PreparationError(f"locked input missing: {path.relative_to(ROOT)}")
        files[str(path.relative_to(ROOT))] = sha256_file(path)
    return {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "target_name": config["target_name"],
        "files": files,
    }


def write_lock(config: dict[str, Any]) -> dict[str, Any]:
    manifest = build_lock_manifest(config)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def verify_lock(config: dict[str, Any]) -> tuple[bool, list[str]]:
    if not LOCK_PATH.is_file():
        return False, ["lock manifest does not exist; run prepare.py"]
    try:
        manifest = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, [f"lock manifest invalid JSON: {exc}"]
    failures: list[str] = []
    expected_paths = {str(path.relative_to(ROOT)) for path in lock_input_paths(config)}
    recorded = manifest.get("files")
    if not isinstance(recorded, dict):
        return False, ["lock manifest files field is invalid"]
    if set(recorded) != expected_paths:
        failures.append("lock manifest file set differs from current config")
    for relative in sorted(expected_paths & set(recorded)):
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"locked file missing: {relative}")
        elif sha256_file(path) != recorded[relative]:
            failures.append(f"locked file changed: {relative}")
    return not failures, failures


def ensure_private_inventory_ignored(config: dict[str, Any], no_git: bool) -> None:
    inventory = ROOT / config["inventory_file"]
    try:
        relative = inventory.relative_to(ROOT / "target" / "private")
    except ValueError:
        return
    if no_git:
        return
    result = run_git("check-ignore", str(inventory), check=False)
    if result.returncode != 0:
        raise PreparationError(
            f"private inventory is not ignored by git: target/private/{relative}"
        )


def initialize_state(config: dict[str, Any], relock: bool) -> dict[str, Any]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    if relock or not LOCK_PATH.exists():
        write_lock(config)
    ok, failures = verify_lock(config)
    if not ok:
        raise PreparationError("lock verification failed:\n- " + "\n- ".join(failures))

    if not RESULTS_PATH.exists():
        RESULTS_PATH.write_text(
            "run_id\tbefore_score\tafter_score\tdelta\tstatus\tcommit\tdescription\n",
            encoding="utf-8",
        )

    candidate = ROOT / config["candidate_file"]
    try:
        baseline = evaluate_candidate(candidate)
    except EvaluationError as exc:
        raise PreparationError(f"baseline candidate is invalid: {exc}") from exc
    if baseline["hard_failures"]:
        raise PreparationError(
            "baseline violates hard constraints:\n- " + "\n- ".join(baseline["hard_failures"])
        )
    BASELINE_PATH.write_text(
        json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return baseline


def setup(
    *,
    tag: str | None,
    relock: bool,
    no_git: bool,
    allow_default_branch: bool,
) -> dict[str, Any]:
    config = load_config()
    if sys.version_info < (3, 10):
        raise PreparationError("Python 3.10 or newer is required")

    branch = "no-git"
    if not no_git:
        if not git_available():
            raise PreparationError("not inside a git repository; use --no-git only for testing")
        if tag:
            branch = create_experiment_branch(tag)
        else:
            branch = current_branch()
            if (
                config.get("require_experiment_branch", True)
                and branch in default_branch_candidates()
                and not allow_default_branch
            ):
                raise PreparationError(
                    f"refusing to prepare on default branch {branch}; pass --tag <name>"
                )
        ensure_private_inventory_ignored(config, no_git=False)

    baseline = initialize_state(config, relock=relock)
    return {
        "branch": branch,
        "target": config["target_name"],
        "baseline_score": baseline["outcome_score"],
        "lock": str(LOCK_PATH.relative_to(ROOT)),
        "results": str(RESULTS_PATH.relative_to(ROOT)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare and lock an autoresearch experiment")
    parser.add_argument("--tag", help="create autoresearch/<tag> before locking")
    parser.add_argument("--relock", action="store_true", help="replace the lock manifest")
    parser.add_argument("--check", action="store_true", help="verify the existing lock and exit")
    parser.add_argument("--no-git", action="store_true", help="test mode; skip branch and git checks")
    parser.add_argument(
        "--allow-default-branch",
        action="store_true",
        help="override the experiment-branch gate",
    )
    args = parser.parse_args()

    try:
        config = load_config()
        if args.check:
            ok, failures = verify_lock(config)
            if not ok:
                print("lock_status: FAIL")
                for failure in failures:
                    print(f"failure: {failure}")
                return 1
            print("lock_status: PASS")
            return 0
        result = setup(
            tag=args.tag,
            relock=args.relock,
            no_git=args.no_git,
            allow_default_branch=args.allow_default_branch,
        )
    except PreparationError as exc:
        print(f"prepare_error: {exc}", file=sys.stderr)
        return 2

    print(f"branch:         {result['branch']}")
    print(f"target:         {result['target']}")
    print(f"baseline_score: {result['baseline_score']:.6f}")
    print(f"lock:           {result['lock']}")
    print(f"results:        {result['results']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
