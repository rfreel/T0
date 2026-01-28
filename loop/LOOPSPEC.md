# LoopSpec (DECIDE)

## ObjectiveMetric
A task is complete when the specified verifier output matches the declared DoneCondition for the chosen PRD item.

## DoneCondition
All acceptance criteria for the active PRD item are satisfied, backed by artifacts (diffs/logs/tests) recorded in the loop log or referenced files.

## StateSchema
- prd.json: source of truth for item status (passes, notes).
- loop/log.txt: append-only event log (radius-limited).
- loop/last_error.txt: most recent failure vector.
- progress.txt: append-only progress ledger.

## ActionsAllowed
- Edit files strictly required by the active PRD item.
- Run scripts/ralph/loop.sh or equivalent checks.
- Update prd.json passes/notes and append progress.txt after success.

## SensorsAvailable
- pre-commit output (local) or CI output (remote).
- loop/log.txt and loop/last_error.txt contents.
- git diff/status for change detection.

## PrecheckGate
- Ensure exactly one PRD item is selected with passes=false.
- Ensure radius constraint (last 50 lines of loop/log.txt) holds.

## PostcheckGate
- Run loop checks (scripts/ralph/loop.sh) and confirm pre-commit/CI status.
- Confirm artifacts required by acceptance criteria exist and are referenced.

## EvaluatorRules (binary)
- PASS if: postcheck gate succeeds AND acceptance criteria are met with artifacts.
- FAIL otherwise; capture failure vector in loop/last_error.txt.

## RetryPolicy
- Up to 2 retries per failure type.
- Each retry must narrow scope or change one variable (e.g., re-run check after fix).

## Budgets (time/tokens/loops)
- Max loops per PRD item: 3.
- Max retries per check failure: 2.

## EscalationCondition
- Exceed loop budget or encounter missing sensors; record diagnostics and stop.

## ArtifactsRequired to advance
- Updated PRD item (passes=true + notes).
- loop/log.txt entry for the check outcome.
- progress.txt entry when passing.

## AcceptanceTest
For a representative task, produce:
1) A change artifact (diff) satisfying acceptance criteria.
2) A verifier output (pre-commit/CI log or loop.sh output).
3) A decision update (prd.json + progress.txt).

## StopRule
Stop after the loop budget is exhausted or the DoneCondition is met.
