#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ralph/llm_stub.sh [--patch FILE] [--result FILE]

Stub model adapter. Writes a no-op patch and minimal result JSON.
Reads prompt from stdin.

Examples:
  cat loop/prompt.txt | scripts/ralph/llm_stub.sh --patch loop/patch.diff
USAGE
}

fail_expected() {
  echo "llm_stub.sh: $1" >&2
  exit 1
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--self-test" ]]; then
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  echo "prompt" | scripts/ralph/llm_stub.sh --patch "$tmp_dir/patch.diff" --result "$tmp_dir/result.json"
  if [[ -f "$tmp_dir/patch.diff" && -f "$tmp_dir/result.json" ]]; then
    echo "self-test ok"
    exit 0
  fi
  exit 1
fi

PATCH_FILE="loop/patch.diff"
RESULT_FILE="loop/result.json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --patch)
      PATCH_FILE="${2:-}"
      shift 2
      ;;
    --result)
      RESULT_FILE="${2:-}"
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

cat >/dev/null

: > "$PATCH_FILE"
cat <<'JSON' > "$RESULT_FILE"
{"status":"stub","patch_written":true}
JSON
