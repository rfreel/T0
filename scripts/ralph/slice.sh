#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ralph/slice.sh --file FILE [--start-line N] [--end-line N]
                             [--start-anchor REGEX] [--end-anchor REGEX]
                             [--max-lines N]

Extract a bounded window from a file by line numbers or regex anchors.

Examples:
  scripts/ralph/slice.sh --file loop/log.txt --start-line 1 --end-line 10
  scripts/ralph/slice.sh --file loop/log.txt --start-anchor '^\[ERROR\]' --max-lines 5
USAGE
}

fail_expected() {
  echo "slice.sh: $1" >&2
  exit 1
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--self-test" ]]; then
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  test_file="$tmp_dir/test.txt"
  printf 'one\ntwo\nthree\n' > "$test_file"
  output=$(scripts/ralph/slice.sh --file "$test_file" --start-line 2 --end-line 2)
  if [[ "$output" == "two" ]]; then
    echo "self-test ok"
    exit 0
  fi
  exit 1
fi

FILE=""
START_LINE=""
END_LINE=""
START_ANCHOR=""
END_ANCHOR=""
MAX_LINES=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)
      FILE="${2:-}"
      shift 2
      ;;
    --start-line)
      START_LINE="${2:-}"
      shift 2
      ;;
    --end-line)
      END_LINE="${2:-}"
      shift 2
      ;;
    --start-anchor)
      START_ANCHOR="${2:-}"
      shift 2
      ;;
    --end-anchor)
      END_ANCHOR="${2:-}"
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

if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  fail_expected "missing file: $FILE"
fi

if [[ -z "$START_LINE" && -z "$START_ANCHOR" ]]; then
  START_LINE=1
fi

awk -v start_line="$START_LINE" \
    -v end_line="$END_LINE" \
    -v start_anchor="$START_ANCHOR" \
    -v end_anchor="$END_ANCHOR" \
    -v max_lines="$MAX_LINES" \
    'BEGIN{capture=0; count=0}
     {
       if (start_anchor != "" && capture == 0 && $0 ~ start_anchor) {capture=1}
       if (start_line != "" && NR >= start_line) {capture=1}
       if (capture == 1) {
         print $0
         count++
       }
       if (end_anchor != "" && capture == 1 && $0 ~ end_anchor) {exit}
       if (end_line != "" && NR >= end_line && capture == 1) {exit}
       if (max_lines != "" && count >= max_lines) {exit}
     }' "$FILE"
