#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ralph/apply_patch.sh [--patch FILE]

Apply a unified diff patch safely. Uses git apply --check before applying.

Examples:
  scripts/ralph/apply_patch.sh --patch loop/patch.diff
USAGE
}

fail_expected() {
  echo "apply_patch.sh: $1" >&2
  exit 1
}

fail_unexpected() {
  echo "apply_patch.sh: $1" >&2
  exit 2
}

PATCH_FILE="loop/patch.diff"

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--self-test" ]]; then
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  echo "" > "$tmp_dir/empty.diff"
  if scripts/ralph/apply_patch.sh --patch "$tmp_dir/empty.diff" >/dev/null; then
    echo "self-test ok"
    exit 0
  fi
  exit 1
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --patch)
      PATCH_FILE="${2:-}"
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

if [[ ! -f "$PATCH_FILE" ]]; then
  fail_expected "missing patch file: $PATCH_FILE"
fi

if [[ ! -s "$PATCH_FILE" ]]; then
  echo "apply_patch.sh: empty patch; no changes applied"
  exit 0
fi

if ! git apply --check "$PATCH_FILE" >/dev/null 2>&1; then
  fail_expected "patch did not apply cleanly"
fi

git apply "$PATCH_FILE" >/dev/null 2>&1 || fail_unexpected "failed to apply patch"

echo "apply_patch.sh: patch applied"
