#!/usr/bin/env bash
set -euo pipefail

for f in examples/utp/prompt-stack/golden/spec.json examples/utp/prompt-stack/golden/audit_report.json; do
  test -f "$f"
done

echo "golden files present"
