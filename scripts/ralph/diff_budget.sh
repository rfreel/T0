#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ralph/diff_budget.sh

Enforce one PRD item transition per change by inspecting prd.json diff.

Examples:
  scripts/ralph/diff_budget.sh
USAGE
}

fail_expected() {
  echo "diff_budget.sh: $1" >&2
  exit 1
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--self-test" ]]; then
  scripts/ralph/diff_budget.sh >/dev/null
  echo "self-test ok"
  exit 0
fi

if command -v rg >/dev/null 2>&1; then
  if ! git diff --name-only | rg -q "^prd.json$"; then
    exit 0
  fi
else
  if ! git diff --name-only | grep -q "^prd.json$"; then
    exit 0
  fi
fi

added_true=$(git diff -U0 -- prd.json | awk '/^\+.*"passes": true/{count++} END{print count+0}')

if [[ "$added_true" -gt 1 ]]; then
  fail_expected "more than one PRD item set to passes=true"
fi
