# GitHub Planning Report: Ralph Loop Master Prompt

## Objective
Produce a plan for building a fully local Ralph loop system (orchestrator, tests, sample CLI project, specs, CI simulation) exactly as specified by the master prompt, while enforcing the loop contract and one-task-per-iteration rule.

## Hard Constraints
- Local-only operation (no GitHub/GitLab/remote services).
- No external dependencies beyond the AI agent (except explicitly listed dev tools in the spec).
- One task per iteration; run verification before committing.
- Completion requires emitting `<promise>COMPLETE</promise>` only after all checks pass.
- Favor GitHub autocommit zero-friction flow: each iteration should auto-commit successful changes with minimal manual steps.

## Required File Manifest (23 files)
- Core loop: `.gitignore`, `loop.sh`, `PROMPT.md`, `IMPLEMENTATION_PLAN.md`, `AGENTS.md`, `README.md`.
- Specs: `specs/01-core-requirements.md`, `specs/02-cli-interface.md`, `specs/03-data-model.md`, `specs/04-acceptance-criteria.md`.
- Tests: `tests/test_loop_unit.sh`, `tests/mocks/mock-agent.sh`, `tests/test_loop_integration.sh`, `tests/property-loop-invariants.test.js`, `tests/test_fault_git_corruption.sh`, `tests/test_fault_disk_full.sh`, `tests/test_fault_timeout.sh`, `tests/test_e2e_real_agent.sh`.
- Test docs + CI: `TESTING.md`, `.github/workflows/test-loop.yml`.
- Tooling: `package.json`, `.eslintrc.js`, `jest.config.js`.

## Planning Inputs
- Treat the master prompt as the source of truth for file contents.
- Preserve exact filenames/paths and required content sections.
- Keep commits small and tied to one task in the plan.

## Step-by-Step Plan (One Task per Iteration)
1. **Bootstrap structure**: create directories (`specs/`, `tests/`, `tests/mocks/`) and add `.gitignore`.
2. **Core loop files**: add `loop.sh`, `PROMPT.md`, `IMPLEMENTATION_PLAN.md`, `AGENTS.md`, `README.md`.
3. **Specs**: add the four `specs/*.md` files.
4. **Test harness**: add unit/integration test scripts and mock agent.
5. **Property + fault tests**: add JS property tests and fault injection scripts.
6. **E2E + docs**: add `tests/test_e2e_real_agent.sh` and `TESTING.md`.
7. **Tooling + CI**: add `package.json`, `.eslintrc.js`, `jest.config.js`, and workflow.
8. **Verification pass**: run unit/integration/property/fault tests per checklist, fix failures, then emit completion promise.
9. **Autocommit safeguard**: after each verified change, auto-commit with a single-purpose message; avoid batching unrelated tasks to keep GitHub autocommit frictionless.

## Verification Gates
- **Precheck**: confirm task selection (single plan item), required directories exist.
- **Postcheck**: run specified tests (`bats`, `npm test`, fault tests) and verify artifacts.
- **Acceptance**: confirm all 23 files exist with correct paths and that `loop.sh` is executable.

## Risks & Mitigations
- **Exact content drift**: cross-check against master prompt before commit.
- **Test dependencies**: BATS/Jest may not be installed; document prerequisites in TESTING.md.
- **Disk-full test**: requires root; ensure skip behavior is documented.
- **Promise emission**: only after all checks pass to avoid premature completion.
- **Autocommit churn**: keep commits scoped to one plan item to reduce review friction.

## Required Artifacts
- All 23 files with the specified content.
- Execution logs for the verification checklist.
- Clean git status after completion.
