# Canonical Loop Scaffold

Center = `loop/` files, Radius = last 50 lines of `loop/log.txt`, Tangent = pre-commit + CI checks.
Keep the loop small: only radius lines are in context.
Back-pressure comes from pre-commit locally or CI remotely.
The loop is bash-driven and stack-agnostic.
When CI fails, capture the error vector in `loop/last_error.txt`.

## Usage

A) PR-only: push a branch and let CI enforce the tangent.

B) Codespaces/local: run `scripts/ralph/loop.sh` to apply radius + pre-commit.

To intentionally trigger failure: break `prd.json` or exceed 50 lines in `loop/log.txt`.

## Consequence layer

`consequence.py` extends the repository loop into a consequence-bearing episode loop:

```text
commitment -> intervention -> observation -> assessment -> policy update
```

It preserves the pre-action prediction, freezes committed intent, records append-only evidence, verifies a hash-chained event history, and requires an exact reopen condition before closure.

See [CONSEQUENCE_LEDGER.md](CONSEQUENCE_LEDGER.md).
