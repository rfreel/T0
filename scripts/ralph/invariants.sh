#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ralph/invariants.sh [--radius N]

Validate loop invariants: required files, JSON validity, no conflict markers,
log radius <= N (default 50).

Examples:
  scripts/ralph/invariants.sh
  scripts/ralph/invariants.sh --radius 50
USAGE
}

fail_expected() {
  echo "invariants.sh: $1" >&2
  exit 1
}

fail_unexpected() {
  echo "invariants.sh: $1" >&2
  exit 2
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--self-test" ]]; then
  scripts/ralph/invariants.sh >/dev/null
  echo "self-test ok"
  exit 0
fi

RADIUS="${RADIUS_LINES:-50}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --radius)
      RADIUS="${2:-}"
      shift 2
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

if ! [[ "$RADIUS" =~ ^[0-9]+$ ]]; then
  fail_expected "radius must be numeric"
fi

required=(
  "loop/GOAL.md"
  "loop/RULES.md"
  "loop/log.txt"
  "loop/last_error.txt"
  "prd.json"
  "progress.txt"
)

for file in "${required[@]}"; do
  if [[ ! -f "$file" ]]; then
    fail_expected "missing required file: $file"
  fi
done

python - <<'PY' || fail_unexpected "prd.json invalid"
import json
json.load(open("prd.json","r",encoding="utf-8"))
PY

lines=$(wc -l < loop/log.txt)
if [[ "$lines" -gt "$RADIUS" ]]; then
  fail_expected "loop/log.txt exceeds radius ($lines > $RADIUS)"
fi

if command -v rg >/dev/null 2>&1; then
  if rg -n "^(<<<<<<<|=======|>>>>>>>)" -g'*' . >/dev/null; then
    fail_expected "merge conflict markers detected"
  fi
else
  if git ls-files -z | xargs -0 grep -n "^(<<<<<<<|=======|>>>>>>>)" >/dev/null 2>&1; then
    fail_expected "merge conflict markers detected"
  fi
fi
