#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ralph/ci_gate.sh

Run local CI invariants and pre-commit gate.

Examples:
  scripts/ralph/ci_gate.sh
USAGE
}

fail_expected() {
  echo "ci_gate.sh: $1" >&2
  exit 1
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--self-test" ]]; then
  if scripts/ralph/invariants.sh >/dev/null; then
    echo "self-test ok"
    exit 0
  fi
  exit 1
fi

scripts/ralph/invariants.sh
scripts/ralph/precommit_gate.sh --require
