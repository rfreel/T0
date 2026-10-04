# Personal Autoresearch Lab

A domain-general, fresh-context autoresearch loop adapted from Karpathy's `program.md + prepare.py + mutable target` pattern for personal optimization work.

This scaffold separates five objects that must not collapse into one another:

1. **PROGRAM.md** — human-owned objective, operating rules, and stop conditions.
2. **prepare.py** — cleans the experiment, hashes locked files, creates the baseline, and refuses unsafe branch state.
3. **Locked evaluator** — `evaluate.py`, `config.json`, the objective, constraints, and verified option catalog.
4. **Mutable target** — files under `target/candidate/` that the agent may change.
5. **Evidence ledger** — `.autoresearch/results.tsv`, immutable run snapshots, hashes, scores, and keep/discard decisions.

The included first target is a **service-replacement portfolio**: select keep, replace, rebuild, or cancel options for recurring services while preserving required capabilities and accounting for cost, privacy, reliability, migration effort, and maintenance burden. The supplied inventory is synthetic. Replace it with your own only after choosing whether cloud or local inference may see it.

## Operating shape

```text
human objective + forbidden actions
            ↓
locked inputs + verified catalog + evaluator
            ↓
fresh isolated agent workspace (one iteration)
            ↓
mutable candidate files only
            ↓
out-of-workspace deterministic evaluation
            ↓
score improves and every hard gate passes?
        yes: keep + atomic commit
         no: preserve snapshot + discard
            ↓
next fresh model instance
```

The agent cannot promote changes to the evaluator because every invocation is rooted in a temporary workspace containing copies of context and only the candidate files. The runner accepts only declared mutable paths and verifies every other workspace file by hash before considering the result. This is an acceptance and write-containment boundary, not a host confidentiality boundary.

## Security boundary

`codex --sandbox workspace-write` restricts writes to the workspace and configured writable roots, but it does not prevent reads elsewhere on the host. Therefore:

- run the included synthetic inventory directly on a normal workstation;
- run pseudonymous personal inputs from a disposable OS account, container, or VM that exposes only this lab;
- keep credentials, browser profiles, SSH keys, cloud-drive mounts, and identifying crosswalks outside that environment;
- use local inference when inputs must not be sent to a cloud model;
- treat external actions such as cancellation, purchasing, messaging, or form submission as a separate supervised actuation system.

The run workspace and hash gates protect the accepted repository state. Only an OS-level container or VM can make the input-read boundary correspond to the visible lab directory.

## First run

Requirements: Python 3.10+, Git, and an agent CLI. No Python packages are required.

```bash
cd experiments/personal-autoresearch

# Creates autoresearch/<tag>, locks the evaluator, and records the baseline.
python prepare.py --tag jul30

# Inspect the deterministic baseline.
python evaluate.py

# One fresh Codex process per experiment.
python run.py --iterations 10
```

The default command is equivalent to:

```bash
codex exec \
  --ephemeral \
  --sandbox workspace-write \
  --ask-for-approval never \
  --skip-git-repo-check \
  -C "{workspace}" \
  -
```

`{workspace}` is replaced by the runner with a new isolated directory for each iteration.

## Run locally with Ollama

```bash
ollama pull qwen3.6:27b

export AUTORESEARCH_AGENT_CMD='codex exec --ephemeral --oss --local-provider ollama -m qwen3.6:27b --sandbox workspace-write --ask-for-approval never --skip-git-repo-check -C "{workspace}" -'
python run.py --iterations 20
```

Any other non-interactive coding-agent command can be supplied through `AUTORESEARCH_AGENT_CMD`. It must read the prompt from stdin, operate in `{workspace}`, and exit nonzero on failure.

## Use private inputs deliberately

The default `config.json` points to the committed synthetic inventory:

```json
"inventory_file": "target/inventory.example.csv"
```

For personal data:

```bash
cp target/inventory.example.csv target/private/inventory.csv
# edit target/private/inventory.csv
```

Use opaque service IDs and keep any identifying crosswalk outside this repository. Candidate files repeat service IDs and accepted iterations may be committed, so do not place names, account numbers, email addresses, URLs containing identifiers, credentials, or free-text personal notes in the inventory.

Then change `inventory_file` to `target/private/inventory.csv` and run:

```bash
python prepare.py --relock
```

`target/private/` and `.autoresearch/` are ignored by Git. The selected inventory is copied into the isolated prompt workspace, and candidate outputs remain repository artifacts; pseudonymization is therefore mandatory in a public repository. A cloud model will still receive the selected inventory in its isolated prompt workspace. Use the local Ollama command when the inventory must remain on your machine.

## Verify the harness

```bash
python -m unittest discover -s tests -v
bash scripts/smoke.sh
```

The smoke test uses a deterministic fake agent and does not call an LLM.

## Create another target

Duplicate this directory and replace four things:

1. `target/OBJECTIVE.md` — exact desired state and non-goals.
2. `target/CONSTRAINTS.md` — hard limits, authority boundary, and stop rules.
3. `target/catalog.json` or equivalent verified world model.
4. `evaluate.py` — deterministic outcome score and hard gates.

Keep the runner and preparation contract unchanged until the new evaluator passes adversarial tests. For domains without a natural metric, use two scores: an **outcome score** and an **instrument-integrity score**. Never reward changes to the ruler in the same loop that optimizes the measured object.

## What this setup will not do

It will not cancel subscriptions, send applications, contact data brokers, spend money, expose private inputs by default, or modify external systems. Those are separate actuation stages requiring their own authorization, observation, rollback, and acceptance gates.
