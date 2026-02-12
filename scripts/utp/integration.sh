#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="runs/integration"
mkdir -p "$OUT_DIR"

node --import tsx src/utp/cli.ts run --source examples/utp/prompt-stack/inputs/source.txt --source-domain prompt-stack --target-domain prompt-stack --target-env local --out "$OUT_DIR" >/tmp/utp_run_path.txt
RUN_PATH=$(cat /tmp/utp_run_path.txt)

python - <<'PY'
import json,sys,glob,os
run_path=open('/tmp/utp_run_path.txt').read().strip()
audit=json.load(open(f"{run_path}/audit_report.json"))
if audit.get('discrepancies'):
    print('discrepancies detected')
    sys.exit(1)
print('integration pass')
PY
