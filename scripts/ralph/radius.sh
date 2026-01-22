#!/usr/bin/env bash
set -euo pipefail

FILE="${1:?usage: radius.sh <file> <max_lines>}"
MAX_LINES="${2:?usage: radius.sh <file> <max_lines>}"

mkdir -p "$(dirname "$FILE")"
touch "$FILE"

tmp="$(mktemp)"
tail -n "$MAX_LINES" "$FILE" > "$tmp" || true
cat "$tmp" > "$FILE"
rm -f "$tmp"
