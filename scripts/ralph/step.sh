#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ralph/step.sh [--id ID] [--format json|text] [--file prd.json]

Select the next PRD item where passes=false, or a specific item by --id.
Outputs the selected item in JSON (default) or text format.

Examples:
  scripts/ralph/step.sh
  scripts/ralph/step.sh --id SHELL-001 --format text
USAGE
}

fail_expected() {
  echo "step.sh: $1" >&2
  exit 1
}

fail_unexpected() {
  echo "step.sh: $1" >&2
  exit 2
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--self-test" ]]; then
  first_id=$(python - <<'PY'
import json
data = json.load(open("prd.json","r",encoding="utf-8"))
items = data.get("items", [])
print(items[0]["id"] if items else "")
PY
)
  if [[ -n "$first_id" ]]; then
    scripts/ralph/step.sh --file prd.json --id "$first_id" >/dev/null
  fi
  echo "self-test ok"
  exit 0
fi

FORMAT="json"
PRD_FILE="prd.json"
REQUEST_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --id)
      REQUEST_ID="${2:-}"
      shift 2
      ;;
    --format)
      FORMAT="${2:-}"
      shift 2
      ;;
    --file)
      PRD_FILE="${2:-}"
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

if [[ ! -f "$PRD_FILE" ]]; then
  fail_expected "missing PRD file: $PRD_FILE"
fi

python - <<'PY' "$PRD_FILE" "$REQUEST_ID" "$FORMAT" || exit 2
import json
import sys
from pathlib import Path

prd_path = Path(sys.argv[1])
req_id = sys.argv[2]
fmt = sys.argv[3]

try:
  data = json.loads(prd_path.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
  print(f"invalid JSON: {exc}", file=sys.stderr)
  sys.exit(2)

items = data.get("items", [])
selected = None
if req_id:
  for item in items:
    if item.get("id") == req_id:
      selected = item
      break
else:
  for item in items:
    if item.get("passes") is False:
      selected = item
      break

if not selected:
  print("no matching PRD item found", file=sys.stderr)
  sys.exit(1)

if fmt == "text":
  print(f"{selected.get('id','')}\t{selected.get('title','')}")
elif fmt == "json":
  print(json.dumps(selected, sort_keys=True))
else:
  print(f"unknown format: {fmt}", file=sys.stderr)
  sys.exit(2)
PY
