# LLM Planning Report: GitHub Loop Master Prompt

## Purpose
Guide an LLM to plan implementation of the Ralph loop master prompt in a local-only GitHub repo while respecting the canonical loop rules.

## Prompt Summary (What Must Be Built)
- Offline Ralph loop orchestrator (loop.sh) with promise detection and iteration control.
- Full testing infrastructure: unit, integration, property, fault injection, E2E.
- Sample target project: Task Manager CLI specs and plan.
- Local CI/CD simulation scripts + verification checklist.
- Required files: 23 files with exact contents (see Required Files List).

## Non-Negotiable Constraints
- No external services or remote Git (local repo only).
- No dependencies beyond the AI agent for orchestration.
- One task per iteration; verification before commit.
- Emit `<promise>COMPLETE</promise>` only after all checks pass.

## Required Files List (High Level)
1. Root: `.gitignore`, `loop.sh`, `PROMPT.md`, `IMPLEMENTATION_PLAN.md`, `AGENTS.md`, `README.md`.
2. Specs: `specs/01-core-requirements.md`, `specs/02-cli-interface.md`, `specs/03-data-model.md`, `specs/04-acceptance-criteria.md`.
3. Tests: `tests/test_loop_unit.sh`, `tests/mocks/mock-agent.sh`, `tests/test_loop_integration.sh`, `tests/property-loop-invariants.test.js`, `tests/test_fault_git_corruption.sh`, `tests/test_fault_disk_full.sh`, `tests/test_fault_timeout.sh`, `tests/test_e2e_real_agent.sh`.
4. Tooling: `TESTING.md`, `.github/workflows/test-loop.yml`, `package.json`, `.eslintrc.js`, `jest.config.js`.

## Planning Steps (One Task Per Iteration)
1. **Precheck**: verify loop/log.txt radius and select the single PRD item to implement.
2. **Create skeleton**: add directories and root files (one task at a time).
3. **Add specs**: populate specs/ files per prompt.
4. **Add tests**: add unit/integration/property/fault/E2E scripts in order.
5. **Add tooling**: testing docs, CI workflow, package.json, ESLint/Jest configs.
6. **Verification**: run loop.sh, then local test commands as available.
7. **Postcheck**: confirm required artifacts and update PRD/progress.

## Verification Checklist (Highlights)
- loop.sh is executable.
- All required files exist with correct content.
- Tests pass (BATS, Jest, fault scripts) when dependencies are available.
- No uncommitted changes before completion.

## Risks & Mitigations
- **Missing local dependencies**: note when BATS/Jest are unavailable; rely on CI.
- **Large edits**: keep each commit scoped to one task and one PRD item.
- **Promise misuse**: emit only when acceptance criteria and verification succeed.

## Artifacts Required to Advance
- Updated prd.json (passes=true + notes for active item).
- progress.txt entry for the completed item.
- loop/log.txt entry showing check outcome.
- Newly added files for the task.

## Loop Contract Mapping
- **Sensors**: loop.sh output, git status, test logs.
- **Evaluator**: acceptance criteria + verification checklist.
- **Policy**: retry on failure (capture error vector), stop on success.
