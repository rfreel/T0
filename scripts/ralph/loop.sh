#!/usr/bin/env bash
set -euo pipefail

RADIUS_LINES="${RADIUS_LINES:-50}"
B_CMD="${B_CMD:-scripts/ralph/llm_stub.sh}"

LOG_FILE="loop/log.txt"
ERR_FILE="loop/last_error.txt"

bash scripts/ralph/radius.sh "$LOG_FILE" "$RADIUS_LINES"

PROMPT="$(mktemp)"
{
  echo "=== GOAL ==="
  cat loop/GOAL.md
  echo
  echo "=== RULES ==="
  cat loop/RULES.md
  echo
  echo "=== LOG (last ${RADIUS_LINES} lines) ==="
  cat "$LOG_FILE"
} > "$PROMPT"

set +e
cat "$PROMPT" | bash -c "$B_CMD '$ERR_FILE'"
B_EXIT=$?
set -e

PC_OUT="$(mktemp)"
PC_EXIT=0
set +e
bash scripts/ralph/tangent.sh >"$PC_OUT" 2>&1
PC_EXIT=$?
set -e

if [ "$B_EXIT" -ne 0 ] || [ "$PC_EXIT" -ne 0 ]; then
  {
    echo
    echo "---- ERROR VECTOR (B_EXIT=$B_EXIT, PRECOMMIT_EXIT=$PC_EXIT) ----"
    cat "$PC_OUT"
  } > "$ERR_FILE"

  {
    echo
    echo "[ERROR] $(date -u +%F) B_EXIT=$B_EXIT PRECOMMIT_EXIT=$PC_EXIT"
    echo "See loop/last_error.txt"
  } >> "$LOG_FILE"

  bash scripts/ralph/radius.sh "$LOG_FILE" "$RADIUS_LINES"
  echo "Loop failed; error vector captured in $ERR_FILE"
  exit 1
fi

{
  echo
  echo "[OK] $(date -u +%F) pre-commit passed"
} >> "$LOG_FILE"
bash scripts/ralph/radius.sh "$LOG_FILE" "$RADIUS_LINES"

echo "Loop OK; consider updating prd.json/progress.txt, then commit."
