# AGENTS (Operating Manual)

This repo runs a canonical loop:
- Center: loop/ directory.
- Radius: last N lines of loop/log.txt (N=50).
- Tangent: pre-commit + CI back-pressure.
- PATCH-ONLY pipeline: loop.sh -> step.sh -> llm_stub.sh -> apply_patch.sh -> invariants.sh/precommit_gate.sh.

## One iteration (operator checklist)
1) Read loop/GOAL.md and prd.json (pick ONE item where passes=false).
2) Run scripts/ralph/loop.sh (or perform the same steps manually).
3) If checks fail: capture the error vector into loop/last_error.txt and append a short summary to loop/log.txt.
4) If checks pass: update prd.json (passes=true + notes) and append one line to progress.txt.
5) Commit and merge.

## Non-negotiables
- One PRD item per PR.
- Keep loop/log.txt within radius (enforced).
- Back-pressure must run before merge (CI required).
