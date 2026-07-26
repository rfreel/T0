#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${GITHUB_WORKSPACE:-$PWD}"
WORK="${RUNNER_TEMP:-/tmp}/pufferlib-src"
OUT="$ROOT/pufferlib-results"
LOG="$OUT/training.log"
PUFFER_COMMIT="c5d3c637446047a6efbcaa74c039c5295d201ab0"
ENV_NAME="minimal"

rm -rf "$WORK" "$OUT"
mkdir -p "$OUT"
exec > >(tee "$LOG") 2>&1

printf 'started_utc=%s\n' "$(date -u +%FT%TZ)"
printf 'runner=%s\n' "$(uname -a)"
printf 'pufferlib_commit=%s\n' "$PUFFER_COMMIT"
printf 'environment=%s\n' "$ENV_NAME"

python --version
python -m pip --version

# Install an explicitly CPU-only Torch build before installing PufferLib's
# remaining Python dependencies. This avoids silently downloading CUDA wheels.
python -m pip install --upgrade pip setuptools wheel
python -m pip install --index-url https://download.pytorch.org/whl/cpu 'torch>=2.9,<2.11'
python -m pip install numpy rich rich-argparse gpytorch scikit-learn wandb pybind11

git clone --filter=blob:none --no-checkout https://github.com/PufferAI/PufferLib.git "$WORK"
cd "$WORK"
git checkout --detach "$PUFFER_COMMIT"
python -m pip install -e . --no-deps

# PufferLib 4.0 has an explicit CPU binding path. The PyTorch trainer is selected
# later with --slowly; the native extension still supplies the vectorized C env.
# The upstream OneStateWorld binding at this commit references a removed legacy
# header, so use the maintained `minimal` environment with the current vecenv API.
bash build.sh "$ENV_NAME" --cpu

python - "$ENV_NAME" "$OUT/runtime.json" <<'PY'
import json
import pathlib
import sys
import torch
import pufferlib
from pufferlib import _C

env_name = sys.argv[1]
out = pathlib.Path(sys.argv[2])
info = {
    'pufferlib_version': pufferlib.__version__,
    'torch_version': torch.__version__,
    'torch_cuda_available': torch.cuda.is_available(),
    'compiled_env': _C.env_name,
    'compiled_gpu_backend': bool(_C.gpu),
    'precision_bytes': int(_C.precision_bytes),
}
out.write_text(json.dumps(info, indent=2, sort_keys=True) + '\n')
print(json.dumps(info, indent=2, sort_keys=True))
assert info['compiled_env'] == env_name
assert info['compiled_gpu_backend'] is False
assert info['precision_bytes'] == 4
PY

# Four complete optimization epochs plus one or more evaluation rollouts.
# `minimal` is an upstream vectorized 8-agent coordination environment;
# 256 agents correspond to 32 parallel worlds on a hosted CPU runner.
puffer train "$ENV_NAME" \
  --slowly \
  --vec.total-agents 256 \
  --vec.num-buffers 2 \
  --vec.num-threads 4 \
  --train.horizon 256 \
  --train.minibatch-size 8192 \
  --train.total-timesteps 262144 \
  --train.replay-ratio 1.0 \
  --policy.hidden-size 32 \
  --policy.num-layers 1 \
  --checkpoint-interval 1 \
  --eval-episodes 64

checkpoint="$(find "checkpoints/$ENV_NAME" -type f -name '*.bin' -size +0c | sort | tail -n 1)"
metric_log="$(find "logs/$ENV_NAME" -type f -name '*.json' -size +0c | sort | tail -n 1)"
test -n "$checkpoint"
test -n "$metric_log"

cp "$checkpoint" "$OUT/model.bin"
cp "$metric_log" "$OUT/metrics.json"
git rev-parse HEAD > "$OUT/pufferlib-commit.txt"
(
  cd "$OUT"
  sha256sum model.bin > model.sha256
)

python - "$OUT/metrics.json" "$OUT/summary.json" <<'PY'
import json
import pathlib
import sys

src, dst = map(pathlib.Path, sys.argv[1:])
data = json.loads(src.read_text())
metrics = data.get('metrics', {})

def last(name):
    value = metrics.get(name)
    if isinstance(value, list) and value:
        return value[-1]
    return value

summary = {
    'status': 'trained_and_checkpointed',
    'environment': data.get('env_name'),
    'configured_training_steps': data.get('train', {}).get('total_timesteps'),
    'final_agent_steps_including_eval': last('agent_steps'),
    'optimizer_epochs': last('epoch'),
    'score': last('env/score'),
    'performance': last('env/perf'),
    'sps': last('SPS'),
    'uptime_seconds': last('uptime'),
    'policy_loss': last('loss/policy_loss'),
    'value_loss': last('loss/value_loss'),
    'entropy': last('loss/entropy'),
    'approx_kl': last('loss/approx_kl'),
    'explained_variance': last('loss/explained_variance'),
}
dst.write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
print(json.dumps(summary, indent=2, sort_keys=True))
assert summary['environment'] == 'minimal'
assert summary['configured_training_steps'] == 262144
assert summary['final_agent_steps_including_eval'] >= 262144
assert summary['optimizer_epochs'] == 4
assert summary['policy_loss'] is not None
assert summary['value_loss'] is not None
PY

printf 'finished_utc=%s\n' "$(date -u +%FT%TZ)"
echo 'PUFFERLIB_TRAINING_VERIFIED'
