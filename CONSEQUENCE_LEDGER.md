# Consequence Ledger

T0 originally closed the loop at repository verification. Consequence Ledger adds the external closure path:

```text
objective
  -> draft episode
  -> validated commitment
  -> authorized intervention
  -> append-only observation
  -> outcome assessment
  -> policy update
  -> closure or explicit reopen witness
```

## Enforced invariants

1. Commitment requires situation, decision, baseline, intervention, authority, resources, horizon, prediction, rival prediction, success criterion, and rollback boundary.
2. The committed episode specification is immutable.
3. Observations and events are append-only.
4. Events form a per-episode SHA-256 hash chain.
5. Assessments require outcome, verdict, cost, delay, unintended effects, causal confidence, transfer, and failure notes.
6. Closure requires both a policy update and an exact reopen condition.
7. Time-bearing inputs require a timezone and are normalized to UTC.

## Run one complete episode

```bash
python -m consequence --db consequence.db init

python -m consequence --db consequence.db new \
  --spec examples/episode.json \
  --id latency-trial

python -m consequence --db consequence.db commit latency-trial

python -m consequence --db consequence.db observe latency-trial \
  --metric-value 4 \
  --note "Decision reached action in four days." \
  --evidence-ref "artifact://decision-log/42"

python -m consequence --db consequence.db assess latency-trial \
  --assessment examples/assessment.json

python -m consequence --db consequence.db policy latency-trial \
  --change "Use bounded commitment after verification." \
  --reopen-condition "Reopen if latency exceeds five days or a safety invariant fails."

python -m consequence --db consequence.db close latency-trial
python -m consequence --db consequence.db verify latency-trial
```

## Queries

```bash
python -m consequence --db consequence.db list --state COMMITTED --state OBSERVING
python -m consequence --db consequence.db due
python -m consequence --db consequence.db show latency-trial
python -m consequence --db consequence.db export --output episodes.jsonl
```

## Verification

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

The implementation is one dependency-free Python file using SQLite from the standard library.
