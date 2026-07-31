#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluate import EvaluationError, evaluate_candidate
from prepare import (
    RESULTS_PATH,
    ROOT,
    RUNS_DIR,
    PreparationError,
    current_branch,
    default_branch_candidates,
    git_available,
    load_config,
    run_git,
    verify_lock,
)


class RunError(RuntimeError):
    pass


STOP_REQUESTED = False


def _request_stop(_signum: int, _frame: object) -> None:
    global STOP_REQUESTED
    STOP_REQUESTED = True


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            hashes[str(path.relative_to(root))] = sha256_file(path)
    return hashes


def read_history(limit: int) -> str:
    if not RESULTS_PATH.exists():
        return "No prior experiments."
    rows = RESULTS_PATH.read_text(encoding="utf-8").splitlines()
    if len(rows) <= 1:
        return "No prior experiments."
    return "\n".join([rows[0], *rows[-limit:]])


def validate_research_artifacts(workspace: Path) -> list[str]:
    failures: list[str] = []
    notes = workspace / "candidate/RESEARCH_NOTES.md"
    queue = workspace / "candidate/research_queue.json"
    if not notes.is_file():
        failures.append("missing candidate/RESEARCH_NOTES.md")
    elif notes.stat().st_size > 50_000:
        failures.append("RESEARCH_NOTES.md exceeds 50,000 bytes")
    if not queue.is_file():
        failures.append("missing candidate/research_queue.json")
    else:
        try:
            raw = json.loads(queue.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"research_queue.json invalid JSON: {exc}")
        else:
            if not isinstance(raw, dict) or set(raw) != {"version", "proposals"}:
                failures.append(
                    "research_queue.json must contain exactly version and proposals"
                )
            elif raw.get("version") != 1 or not isinstance(raw.get("proposals"), list):
                failures.append("research_queue.json requires version=1 and proposals=list")
            else:
                for index, proposal in enumerate(raw["proposals"]):
                    if not isinstance(proposal, dict):
                        failures.append(f"research proposal {index} is not an object")
                        continue
                    if proposal.get("status") not in {None, "unverified"}:
                        failures.append(
                            f"research proposal {index} status must be unverified"
                        )
    return failures


def actual_candidate_paths(config: dict[str, Any]) -> dict[str, Path]:
    return {
        "candidate/portfolio.json": ROOT / config["candidate_file"],
        "candidate/RESEARCH_NOTES.md": ROOT / config["research_notes_file"],
        "candidate/research_queue.json": ROOT / config["research_queue_file"],
    }


def build_workspace(
    run_dir: Path,
    config: dict[str, Any],
    current_score: dict[str, Any],
) -> tuple[Path, dict[str, str]]:
    workspace = run_dir / "workspace"
    (workspace / "context").mkdir(parents=True)
    (workspace / "candidate").mkdir(parents=True)

    copies = {
        ROOT / "PROGRAM.md": workspace / "context/PROGRAM.md",
        ROOT / "target/OBJECTIVE.md": workspace / "context/OBJECTIVE.md",
        ROOT / "target/CONSTRAINTS.md": workspace / "context/CONSTRAINTS.md",
        ROOT / config["catalog_file"]: workspace / "context/catalog.json",
        ROOT / config["inventory_file"]: workspace / "context/inventory.csv",
        ROOT / "evaluate.py": workspace / "context/evaluate.py",
        ROOT / "config.json": workspace / "context/config.json",
    }
    for source, destination in copies.items():
        shutil.copy2(source, destination)

    for relative, source in actual_candidate_paths(config).items():
        destination = workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    (workspace / "context/current_score.json").write_text(
        json.dumps(current_score, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (workspace / "context/HISTORY.md").write_text(
        "# Experiment history\n\n```tsv\n"
        + read_history(int(config["history_rows_in_prompt"]))
        + "\n```\n",
        encoding="utf-8",
    )
    (workspace / "AGENTS.md").write_text(
        "# Isolated experiment workspace\n\n"
        "Read context/PROGRAM.md first. Work exactly one experiment. "
        "Only these files may be modified:\n\n"
        "- candidate/portfolio.json\n"
        "- candidate/RESEARCH_NOTES.md\n"
        "- candidate/research_queue.json\n\n"
        "Everything under context/ and this AGENTS.md file is immutable. "
        "Do not create extra files. Do not access paths outside this workspace.\n",
        encoding="utf-8",
    )
    return workspace, tree_hashes(workspace)


def build_prompt() -> str:
    return """Execute one autoresearch experiment now.

Read AGENTS.md and all context files. Inspect the current candidate, generate rival moves, select one coherent experiment, and edit only the declared mutable files. Optimize the locked evaluator rather than your own prose. Preserve every hard constraint. Record the hypothesis, expected component changes, principal failure mode, and reversal condition in RESEARCH_NOTES.md. Put unverified discoveries only in research_queue.json. Do not ask questions and do not stop for a progress report. End after the candidate files are internally consistent.
"""


def render_command(template: str, workspace: Path) -> str:
    token = shlex.quote(str(workspace))
    project = shlex.quote(str(ROOT))
    return (
        template.replace('"{workspace}"', token)
        .replace("{workspace}", token)
        .replace('"{project}"', project)
        .replace("{project}", project)
    )


def run_agent(
    command: str,
    workspace: Path,
    prompt: str,
    timeout_seconds: int,
    run_dir: Path,
) -> tuple[int, str | None]:
    stdout_path = run_dir / "agent.stdout.log"
    stderr_path = run_dir / "agent.stderr.log"
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=workspace,
            input=prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        return 124, f"agent timeout after {timeout_seconds} seconds"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    return result.returncode, None


def workspace_structure_failures(workspace: Path) -> list[str]:
    failures: list[str] = []
    for path in sorted(workspace.rglob("*")):
        relative = str(path.relative_to(workspace))
        if path.is_symlink():
            failures.append(f"symbolic link is forbidden: {relative}")
        elif not path.is_dir() and not path.is_file():
            failures.append(f"special filesystem object is forbidden: {relative}")
    return failures


def immutable_workspace_failures(
    before_hashes: dict[str, str],
    after_hashes: dict[str, str],
    mutable_files: set[str],
) -> list[str]:
    failures: list[str] = []
    before_paths = set(before_hashes)
    after_paths = set(after_hashes)
    for path in sorted(before_paths | after_paths):
        if path in mutable_files:
            continue
        if path not in before_paths:
            failures.append(f"unexpected file created: {path}")
        elif path not in after_paths:
            failures.append(f"immutable file deleted: {path}")
        elif before_hashes[path] != after_hashes[path]:
            failures.append(f"immutable file changed: {path}")
    return failures


def append_result(
    run_id: str,
    before_score: float,
    after_score: float,
    status: str,
    commit: str,
    description: str,
) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not RESULTS_PATH.exists():
        RESULTS_PATH.write_text(
            "run_id\tbefore_score\tafter_score\tdelta\tstatus\tcommit\tdescription\n",
            encoding="utf-8",
        )
    clean_description = " ".join(description.replace("\t", " ").split())[:240]
    delta = after_score - before_score
    with RESULTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(
            f"{run_id}\t{before_score:.6f}\t{after_score:.6f}\t{delta:.6f}\t"
            f"{status}\t{commit}\t{clean_description}\n"
        )


def first_note_line(path: Path) -> str:
    if not path.is_file():
        return "no research notes"
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped:
            return stripped
    return "empty research notes"


def ensure_git_run_state(config: dict[str, Any], no_git: bool) -> None:
    if no_git:
        return
    if not git_available():
        raise RunError("not inside a git repository")
    branch = current_branch()
    if config.get("require_experiment_branch", True) and branch in default_branch_candidates():
        raise RunError(f"refusing to run on default branch {branch}; run prepare.py --tag <name>")
    status = run_git("status", "--porcelain", "--untracked-files=no")
    if status.stdout.strip():
        raise RunError(
            "tracked working tree is not clean before experiment:\n" + status.stdout.strip()
        )


def commit_candidate(config: dict[str, Any], message: str) -> str:
    paths = [str(path.relative_to(ROOT)) for path in actual_candidate_paths(config).values()]
    run_git("add", "--", *paths)
    staged = run_git("diff", "--cached", "--quiet", check=False)
    if staged.returncode == 0:
        return "no-change"
    result = run_git("commit", "-m", message, check=False)
    if result.returncode != 0:
        run_git("reset", check=False)
        raise RunError(f"git commit failed: {result.stderr.strip() or result.stdout.strip()}")
    return run_git("rev-parse", "--short", "HEAD").stdout.strip()


def restore_candidate(backups: dict[Path, bytes]) -> None:
    for path, content in backups.items():
        path.write_bytes(content)


def execute_iteration(
    index: int,
    config: dict[str, Any],
    agent_command: str,
    no_git: bool,
) -> dict[str, Any]:
    ok, lock_failures = verify_lock(config)
    if not ok:
        raise RunError("locked evaluator changed:\n- " + "\n- ".join(lock_failures))
    ensure_git_run_state(config, no_git=no_git)

    current_path = ROOT / config["candidate_file"]
    try:
        before = evaluate_candidate(current_path)
    except EvaluationError as exc:
        raise RunError(f"current candidate invalid: {exc}") from exc
    if before["hard_failures"]:
        raise RunError("current candidate violates hard constraints")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{timestamp}-{index:04d}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    workspace, before_hashes = build_workspace(run_dir, config, before)
    rendered_command = render_command(agent_command, workspace)
    (run_dir / "command.txt").write_text(rendered_command + "\n", encoding="utf-8")
    (run_dir / "prompt.md").write_text(build_prompt(), encoding="utf-8")

    exit_code, agent_error = run_agent(
        rendered_command,
        workspace,
        build_prompt(),
        int(config["agent_timeout_seconds"]),
        run_dir,
    )
    after_hashes = tree_hashes(workspace)
    mutable = set(config["mutable_files"])
    tamper_failures = immutable_workspace_failures(before_hashes, after_hashes, mutable)
    artifact_failures = workspace_structure_failures(workspace)
    artifact_failures.extend(validate_research_artifacts(workspace))

    try:
        after = evaluate_candidate(workspace / "candidate/portfolio.json")
    except EvaluationError as exc:
        after = {
            "outcome_score": 0.0,
            "instrument_integrity_score": 0.0,
            "hard_failures": [str(exc)],
            "accepted_by_evaluator": False,
            "metrics": {},
            "decisions": [],
        }

    minimum_delta = float(config["minimum_score_delta"])
    delta = float(after["outcome_score"]) - float(before["outcome_score"])
    gate_failures: list[str] = []
    if exit_code != 0:
        gate_failures.append(agent_error or f"agent exited {exit_code}")
    gate_failures.extend(tamper_failures)
    gate_failures.extend(artifact_failures)
    gate_failures.extend(after["hard_failures"])
    if float(after["instrument_integrity_score"]) != 100.0:
        gate_failures.append("instrument integrity score is not 100")
    if delta + 1e-12 < minimum_delta:
        gate_failures.append(
            f"score delta {delta:.6f} is below minimum {minimum_delta:.6f}"
        )

    kept = not gate_failures
    status = "keep" if kept else ("tamper" if tamper_failures else "discard")
    commit = ""
    description = first_note_line(workspace / "candidate/RESEARCH_NOTES.md")

    if kept:
        destinations = actual_candidate_paths(config)
        backups = {path: path.read_bytes() for path in destinations.values()}
        try:
            for relative, destination in destinations.items():
                shutil.copy2(workspace / relative, destination)
            if not no_git and config.get("autocommit_kept_iterations", True):
                commit = commit_candidate(
                    config,
                    f"autoresearch: {run_id} {before['outcome_score']:.3f} -> {after['outcome_score']:.3f}",
                )
            else:
                commit = "not-committed"
        except Exception:
            restore_candidate(backups)
            if not no_git:
                run_git(
                    "reset",
                    "--",
                    *[str(path.relative_to(ROOT)) for path in destinations.values()],
                    check=False,
                )
            raise
    else:
        commit = "rejected"

    decision = {
        "run_id": run_id,
        "status": status,
        "kept": kept,
        "before": before,
        "after": after,
        "delta": round(delta, 6),
        "gate_failures": gate_failures,
        "agent_exit_code": exit_code,
        "command": rendered_command,
        "commit": commit,
    }
    (run_dir / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    append_result(
        run_id,
        float(before["outcome_score"]),
        float(after["outcome_score"]),
        status,
        commit,
        description,
    )
    return decision


def main() -> int:
    parser = argparse.ArgumentParser(description="Run fresh-context autoresearch iterations")
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="number of iterations; 0 means run until interrupted",
    )
    parser.add_argument(
        "--agent-cmd",
        help="override AUTORESEARCH_AGENT_CMD and config default",
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="test mode; do not require or commit git",
    )
    args = parser.parse_args()
    if args.iterations < 0:
        print("run_error: --iterations must be >= 0", file=sys.stderr)
        return 2

    signal.signal(signal.SIGINT, _request_stop)
    signal.signal(signal.SIGTERM, _request_stop)

    try:
        config = load_config()
        command = (
            args.agent_cmd
            or os.environ.get("AUTORESEARCH_AGENT_CMD")
            or config["default_agent_command"]
        )
        ok, failures = verify_lock(config)
        if not ok:
            raise RunError("prepare step is incomplete:\n- " + "\n- ".join(failures))

        index = 1
        while not STOP_REQUESTED and (args.iterations == 0 or index <= args.iterations):
            decision = execute_iteration(index, config, command, no_git=args.no_git)
            print(
                f"run={decision['run_id']} status={decision['status']} "
                f"before={decision['before']['outcome_score']:.6f} "
                f"after={decision['after']['outcome_score']:.6f} "
                f"delta={decision['delta']:.6f} commit={decision['commit']}"
            )
            if decision["gate_failures"]:
                for failure in decision["gate_failures"]:
                    print(f"  gate_failure: {failure}")
            index += 1
    except (RunError, PreparationError, OSError) as exc:
        print(f"run_error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
