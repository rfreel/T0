# LLM Planning Report for GitHub Work

## Purpose
Provide a concise brief for an LLM to produce a plan for work in this repository, ensuring the loop contract and verification gates are respected.

## Repo Goal (Current Objective)
- Operate a canonical loop with small context radius and automatic back-pressure. See loop/GOAL.md.

## Loop Contract Summary
- **Center**: loop/ directory.
- **Radius**: last 50 lines of loop/log.txt.
- **Tangent**: pre-commit + CI checks as back-pressure.
- **One PRD item per PR**: only address a single prd.json item where passes=false.

## Key Files & Roles
- loop/GOAL.md: objective statement.
- loop/RULES.md: hard constraints (radius, single item, error vector, no drive-by changes).
- prd.json: source of truth for work items, acceptance criteria, and status.
- loop/log.txt: append-only event log, must stay within 50 lines.
- loop/last_error.txt: most recent failure vector.
- progress.txt: append-only progress ledger.
- scripts/ralph/loop.sh: canonical loop runner (radius + pre-commit check).

## Planning Inputs
- **Select exactly one PRD item** with passes=false.
- **Respect radius**: operate only on last 50 lines of loop/log.txt.
- **No drive-by refactors**: touch only files required for the active item.

## Required Plan Structure (LLM Output)
1. **Goal**: Restate the chosen PRD item and measurable acceptance criteria.
2. **State**: Identify current artifacts (files) and gaps vs. acceptance.
3. **Actions**: Enumerate minimal file edits or scripts to run.
4. **Sensors**: Specify checks/logs to verify results (loop.sh, git diff, file presence).
5. **Evaluator**: Define pass/fail conditions tied to acceptance criteria.
6. **Policy**: Describe next step based on evaluation (retry, escalate, stop).
7. **Artifacts**: List exact files or outputs needed to advance.

## Verification Gates (Must Be Explicit)
- **Precheck**: validate selected PRD item (passes=false) and radius compliance.
- **Postcheck**: run scripts/ralph/loop.sh (or equivalent) and capture output.
- **Acceptance**: ensure artifacts exist and match PRD acceptance criteria.

## Risks & Failure Modes
- **Missing sensors**: no pre-commit installed locally → rely on CI; log limitation.
- **Radius overflow**: too many log lines → must trim via radius.sh.
- **Multiple PRD items**: violates one-item-per-PR rule.

## Required Artifacts for Completion
- Updated prd.json with passes=true + notes.
- progress.txt entry (append-only).
- loop/log.txt entry indicating check outcome.
- Any files specified by the PRD acceptance criteria.

## Suggested Next Steps (Template)
- Identify the next PRD item (passes=false).
- Draft minimal edits to satisfy acceptance.
- Run scripts/ralph/loop.sh and confirm success.
- Update prd.json notes + progress.txt entry.
- Commit and open PR.
