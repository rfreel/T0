# Acceptance Harness

This is the repository-level test harness the assistant can operate through GitHub. It verifies executable work rather than accepting plans, claims, or manually written evidence.

## Run

```bash
python harness/run.py
```

Run one check:

```bash
python harness/run.py --check identifier-contract
```

List checks:

```bash
python harness/run.py --list
```

The runner writes:

- `harness/results/results.json`: complete machine-readable evidence;
- `harness/results/junit.xml`: standard test report for CI systems.

It exits nonzero when any command, output assertion, timeout, or required-file assertion fails.

## Add a check

Edit `harness/manifest.json`:

```json
{
  "id": "example-capability",
  "cwd": ".",
  "command": ["python", "-m", "pytest", "tests/example", "-q"],
  "timeout_seconds": 120,
  "expect": {
    "exit_code": 0,
    "stdout_contains": ["passed"],
    "required_files": ["src/example.py", "tests/example/test_contract.py"]
  }
}
```

Commands are argument arrays and are executed without a shell. Check working directories and required files cannot escape the repository root. Captured output is bounded, and every run records the commit SHA when GitHub provides it.

## GitHub operating loop

1. Commit the implementation and its manifest check to a branch.
2. GitHub Actions runs the harness on the actual branch state.
3. Inspect the check status, failed step, logs, `results.json`, or JUnit artifact.
4. Repair the same branch and run again.
5. Merge only after the required checks pass.

This gives the assistant a usable verification surface through the GitHub connector: it can create branch changes, inspect workflow runs and logs, and revise failures without claiming that unexecuted work passed.

## Scope

This harness is intentionally smaller than model-evaluation platforms such as Promptfoo or Inspect AI. Those remain candidates for prompt/model evaluations. This runner covers the broader repository contract: tests, builds, generated artifacts, command output, timeouts, and required files. Specialized evaluators can be invoked as ordinary manifest commands when needed.
