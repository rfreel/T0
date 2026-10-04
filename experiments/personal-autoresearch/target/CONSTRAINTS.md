# Constraints

## Hard outcome constraints

- Exactly one option must be selected for every inventory service.
- Every selected option must exist in the locked verified catalog and belong to that service.
- Weighted required-feature coverage for each service must meet or exceed its inventory threshold.
- Services marked `allow_cancel=false` may not select an option whose mode is `cancel`.
- Total monthly recurring cost may not exceed the current portfolio cost.
- All numeric fields must be finite and nonnegative where the schema requires.

## Authority constraints

- The loop produces plans and code artifacts only.
- It may not cancel, purchase, subscribe, submit, message, scrape authenticated accounts, or alter external systems.
- Private inventory data must remain uncommitted.
- Unverified options must remain in `research_queue.json` and receive zero outcome credit.

## Experiment constraints

- One fresh model process per iteration.
- One isolated workspace per iteration.
- Only declared mutable files can be accepted back into the target.
- Every rejected run is retained as an inspectable snapshot.
- No acceptance based on prose, predicted benefit, or self-reported testing.
