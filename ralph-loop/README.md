# Ralph Loop

The Ralph loop is a tiny, repeatable tracer-bullet cycle: change one thing, verify fast, and record the outcome to build a durable learning ledger.

## Quickstart

1. Run the verifier:

   ```sh
   python verify.py
   ```

2. If it prints PASS, append a ledger entry to `ledger.jsonl` using this exact schema:

   ```json
   {"ts":"<ISO-8601 local time>","delta":"...","acceptance":"...","action":"...","verify":"...","outcome":"pass|fail","root_causes":["..."],"fix":"...","lesson":"..."}
   ```

## Next loop

Change only one thing, verify immediately, then log the result in the ledger.
