# Canonical Loop Scaffold

Center = loop/ files, Radius = last 50 lines of loop/log.txt, Tangent = pre-commit + CI.
PATCH-ONLY pipeline: loop.sh -> step.sh -> llm_stub.sh -> apply_patch.sh -> invariants.sh/precommit_gate.sh.
loop.sh runs one iteration unless --watch is set.
Use scripts/ralph/invariants.sh to validate required files and radius.
CI enforces invariants and pre-commit across all files.
If a gate fails, capture details in loop/last_error.txt and append a short log entry.
Keep loop/log.txt within radius and update prd.json/progress.txt after passing.
