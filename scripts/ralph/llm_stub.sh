#!/usr/bin/env bash
set -euo pipefail

PROMPT_OUT="${1:-loop/last_error.txt}"
cat > /dev/null

echo "LLM_STUB: No model configured. Set B_CMD to your model binary." > "$PROMPT_OUT"
exit 0
