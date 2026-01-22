#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ralph/summarize_log.sh [--file loop/log.txt] [--max-lines N]

Summarize the loop log into stable bullet points on stdout.

Examples:
  scripts/ralph/summarize_log.sh
  scripts/ralph/summarize_log.sh --file loop/log.txt --max-lines 5
USAGE
}

fail_expected() {
  echo "summarize_log.sh: $1" >&2
  exit 1
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--self-test" ]]; then
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  test_file="$tmp_dir/log.txt"
  printf '[OK] 2024-01-01 done\n[ERROR] 2024-01-02 fail\n' > "$test_file"
  output=$(scripts/ralph/summarize_log.sh --file "$test_file" --max-lines 1)
  if [[ "$output" == "- [OK] 2024-01-01 done" ]]; then
    echo "self-test ok"
    exit 0
  fi
  exit 1
fi

LOG_FILE="loop/log.txt"
MAX_LINES=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)
      LOG_FILE="${2:-}"
      shift 2
      ;;
    --max-lines)
      MAX_LINES="${2:-}"
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

if [[ ! -f "$LOG_FILE" ]]; then
  fail_expected "missing log file: $LOG_FILE"
fi

if [[ -n "$MAX_LINES" ]] && ! [[ "$MAX_LINES" =~ ^[0-9]+$ ]]; then
  fail_expected "max-lines must be numeric"
fi

awk -v max_lines="$MAX_LINES" '
  BEGIN{count=0}
  /^\[OK\]|^\[ERROR\]/{
    print "- " $0
    count++
    if (max_lines != "" && count >= max_lines) {exit}
  }
  END{if (count==0) print "- (no events)"}
' "$LOG_FILE"
