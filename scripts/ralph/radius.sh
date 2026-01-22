#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ralph/radius.sh <file> [max_lines]

Trim a file to the last N lines (default 50). Idempotent.

Examples:
  scripts/ralph/radius.sh loop/log.txt 50
USAGE
}

fail_expected() {
  echo "radius.sh: $1" >&2
  exit 1
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--self-test" ]]; then
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  test_file="$tmp_dir/test.log"
  printf 'a\n' > "$test_file"
  printf 'b\n' >> "$test_file"
  scripts/ralph/radius.sh "$test_file" 1 >/dev/null
  if [[ "$(cat "$test_file")" == "b" ]]; then
    echo "self-test ok"
    exit 0
  fi
  exit 1
fi

FILE="${1:-}"
MAX_LINES="${2:-50}"

if [[ -z "$FILE" ]]; then
  fail_expected "missing file"
fi

if [[ ! -f "$FILE" ]]; then
  fail_expected "missing file: $FILE"
fi

if ! [[ "$MAX_LINES" =~ ^[0-9]+$ ]]; then
  fail_expected "max_lines must be numeric"
fi

lines=$(wc -l < "$FILE")
if [[ "$lines" -le "$MAX_LINES" ]]; then
  exit 0
fi

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

tail -n "$MAX_LINES" "$FILE" > "$tmp_file"
cat "$tmp_file" > "$FILE"
