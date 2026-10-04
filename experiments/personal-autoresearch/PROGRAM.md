# PROGRAM — Personal Autoresearch

## Mission

Improve the mutable candidate for the declared target through repeated, measurable, reversible experiments. Each iteration is a fresh model instance. The evidence ledger, not the model's narrative, determines whether a result advances.

## Authority boundary

You may edit only:

- `candidate/portfolio.json`
- `candidate/RESEARCH_NOTES.md`
- `candidate/research_queue.json`

You may read every file in the isolated workspace. You may run local read-only inspection commands. You may not access credentials, contact third parties, make purchases, cancel services, submit forms, send messages, or modify anything outside the workspace.

## Non-negotiable distinctions

- A proposal is not an executed change.
- An executed file edit is not an improved outcome.
- An improved score is not accepted unless every hard gate passes.
- An unverified catalog proposal is not a verified option and receives no outcome credit.
- A prior experiment is evidence only for the environment and inputs under which it ran.
- The agent may not alter the evaluator, objective, constraints, inventory, verified catalog, or acceptance threshold.

## One-iteration procedure

1. Read `context/OBJECTIVE.md`, `context/CONSTRAINTS.md`, `context/catalog.json`, `context/inventory.csv`, `context/current_score.json`, and `context/HISTORY.md`.
2. Inspect the current candidate.
3. Generate materially different candidate moves before selecting one. Prefer the move with the largest predicted score increase that preserves every hard constraint.
4. Change one coherent decision set. Do not make unrelated edits.
5. Update `candidate/RESEARCH_NOTES.md` with:
   - hypothesis;
   - exact changed decisions;
   - expected score effects by component;
   - principal failure mode;
   - reversal condition.
6. Put any newly discovered but unverified options in `candidate/research_queue.json`. They do not belong in `portfolio.json` until promoted into the locked catalog by a separate authorized process.
7. Stop after the files are internally consistent. Do not ask the user whether to continue.

## Selection rule

The external runner keeps an iteration only when:

- evaluator exit code is zero;
- instrument-integrity score is exactly 100;
- there are zero hard failures;
- outcome score increases by at least the configured minimum delta;
- immutable workspace files retain their original hashes;
- candidate JSON schemas are valid.

Otherwise the runner preserves the attempted workspace as evidence and leaves the accepted candidate unchanged.

## Search strategy

Allocate experiments across materially rival move classes rather than repeatedly tuning one local choice:

- pure cost reduction;
- feature-preserving replacement;
- privacy-first substitution;
- reliability-first consolidation;
- low-maintenance self-hosting;
- reversible cancellation of nonessential services;
- combinations that remove duplicate capability.

A defeated move remains revivable when a relevant catalog fact, inventory requirement, price, migration estimate, or weighting changes.
