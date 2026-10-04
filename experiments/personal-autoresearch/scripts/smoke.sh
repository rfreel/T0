#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cp -R "$ROOT/." "$TMP/lab"
rm -rf "$TMP/lab/.autoresearch"
cd "$TMP/lab"
python prepare.py --no-git --relock
python run.py --iterations 1 --no-git --agent-cmd 'python {project}/scripts/fake_agent.py'
python evaluate.py
python - <<'PY'
import json
from pathlib import Path
result = json.loads(Path('.autoresearch/runs').glob('*/decision.json').__iter__().__next__().read_text())
assert result['kept'] is True, result
assert result['delta'] > 0, result
print('smoke_status: PASS')
PY
