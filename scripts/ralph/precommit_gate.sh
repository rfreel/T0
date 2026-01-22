#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ralph/precommit_gate.sh [--output FILE] [--require]

Run pre-commit on all files and capture deterministic output.

Examples:
  scripts/ralph/precommit_gate.sh --output loop/precommit.out
  scripts/ralph/precommit_gate.sh --require
USAGE
}

fail_expected() {
  echo "precommit_gate.sh: $1" >&2
  exit 1
}

fail_unexpected() {
  echo "precommit_gate.sh: $1" >&2
  exit 2
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--self-test" ]]; then
  output=$(mktemp)
  trap 'rm -f "$output"' EXIT
  scripts/ralph/precommit_gate.sh --output "$output" >/dev/null || exit 1
  if [[ -s "$output" ]]; then
    echo "self-test ok"
    exit 0
  fi
  exit 1
fi

OUTPUT_FILE="loop/precommit.out"
REQUIRE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      OUTPUT_FILE="${2:-}"
      shift 2
      ;;
    --require)
      REQUIRE=1
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

if ! command -v pre-commit >/dev/null 2>&1; then
  echo "pre-commit not installed" > "$OUTPUT_FILE"
  if [[ "$REQUIRE" -eq 1 ]]; then
    exit 1
  fi
  exit 0
fi

set +e
pre-commit run --all-files --color=never > "$OUTPUT_FILE" 2>&1
status=$?
set -e

if [[ "$status" -ne 0 ]]; then
  exit 1
fi
