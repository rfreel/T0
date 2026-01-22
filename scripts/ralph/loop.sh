#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ralph/loop.sh [--id PRD_ID] [--watch]

Run one canonical loop iteration (PATCH-ONLY pipeline).

Examples:
  scripts/ralph/loop.sh
  scripts/ralph/loop.sh --id SHELL-001
USAGE
}

fail_expected() {
  echo "loop.sh: $1" >&2
  exit 1
}

fail_unexpected() {
  echo "loop.sh: $1" >&2
  exit 2
}

RADIUS_LINES="${RADIUS_LINES:-50}"
B_CMD="${B_CMD:-scripts/ralph/llm_stub.sh}"
PATCH_FILE="${PATCH_FILE:-loop/patch.diff}"
RESULT_FILE="${RESULT_FILE:-loop/result.json}"
WATCH=0
STEP_ID=""

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--self-test" ]]; then
  scripts/ralph/invariants.sh >/dev/null
  first_id=$(python - <<'PY'
import json
data = json.load(open("prd.json","r",encoding="utf-8"))
items = data.get("items", [])
print(items[0]["id"] if items else "")
PY
)
  if [[ -n "$first_id" ]]; then
    scripts/ralph/step.sh --id "$first_id" >/dev/null
  fi
  echo "self-test ok"
  exit 0
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --id)
      STEP_ID="${2:-}"
      shift 2
      ;;
    --watch)
      WATCH=1
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      fail_expected "unknown argument: $1"
      ;;
  esac
done

run_once() {
  scripts/ralph/invariants.sh
  scripts/ralph/radius.sh loop/log.txt "$RADIUS_LINES"

  if [[ -n "$STEP_ID" ]]; then
    step_json=$(scripts/ralph/step.sh --id "$STEP_ID")
  else
    step_json=$(scripts/ralph/step.sh)
  fi
  printf '%s\n' "$step_json" > loop/step.json

  prompt_file="loop/prompt.txt"
  {
    echo "=== GOAL ==="
    cat loop/GOAL.md
    echo
    echo "=== RULES ==="
    cat loop/RULES.md
    echo
    echo "=== PRD ITEM ==="
    cat loop/step.json
    echo
    echo "=== LOG (last ${RADIUS_LINES} lines) ==="
    tail -n "$RADIUS_LINES" loop/log.txt
  } > "$prompt_file"

  set +e
  cat "$prompt_file" | "$B_CMD" --patch "$PATCH_FILE" --result "$RESULT_FILE"
  b_status=$?
  set -e

  if [[ "$b_status" -ne 0 ]]; then
    echo "B_CMD failed with exit $b_status" > loop/last_error.txt
    echo "[ERROR] $(date -u +%F) B_CMD exit=$b_status" >> loop/log.txt
    scripts/ralph/radius.sh loop/log.txt "$RADIUS_LINES"
    return 1
  fi

  set +e
  apply_output=$(scripts/ralph/apply_patch.sh --patch "$PATCH_FILE" 2>&1)
  apply_status=$?
  set -e
  if [[ "$apply_status" -ne 0 ]]; then
    printf '%s\n' "$apply_output" > loop/last_error.txt
    echo "[ERROR] $(date -u +%F) patch apply failed" >> loop/log.txt
    scripts/ralph/radius.sh loop/log.txt "$RADIUS_LINES"
    return 1
  fi

  set +e
  scripts/ralph/precommit_gate.sh --output loop/precommit.out
  gate_status=$?
  set -e

  if [[ "$gate_status" -ne 0 ]]; then
    cat loop/precommit.out > loop/last_error.txt
    echo "[ERROR] $(date -u +%F) pre-commit failed" >> loop/log.txt
    scripts/ralph/radius.sh loop/log.txt "$RADIUS_LINES"
    return 1
  fi

  echo "[OK] $(date -u +%F) loop iteration complete" >> loop/log.txt
  scripts/ralph/radius.sh loop/log.txt "$RADIUS_LINES"
  return 0
}

if [[ "$WATCH" -eq 1 ]]; then
  while true; do
    if ! run_once; then
      exit 1
    fi
    sleep "${WATCH_INTERVAL:-5}"
  done
else
  run_once
fi
