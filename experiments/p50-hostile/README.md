# P50 hostile synthetic benchmark v2

## Claim tested

> Automated search can discover the smallest environment change that unlocks a latent fixed capability.

## Antithesis construction

The benchmark does not assume that more scaffolding helps. It includes:

- tasks that need one primitive;
- tasks that need a specific interaction;
- redundant unlocking routes;
- holistic tasks harmed by decomposition;
- regime-shift tasks harmed by stale state, retrieval, and larger context;
- verifier traps where measured success diverges from world-state success;
- intrinsic ceilings that scaffolding cannot repair;
- null tasks with no environment-dependent capability;
- a fixed attention/control budget that dilutes useful components when too many are active;
- signed, task-dependent component effects and coordination costs.

The same frozen tasks from v1 are retained. V2 changes only the environment transport law after v1 failed a benchmark-quality gate because the full scaffold dominated.

## Search conditions

- 12 environment primitives.
- 794 candidate configurations: every subset of cardinality 0–4 plus the full 12-component scaffold.
- 120 development tasks.
- 120 sealed IID tasks.
- 120 sealed distribution-shift tasks.
- 80 adversarial null tasks.
- Conditional routing sees only nine observable geometry variables, never hidden family labels.
- `family_oracle` is reported only as an unattainable ceiling.

## Result

```json
{
  "original_P50_global_unlock": "NOT_SUPPORTED",
  "conditional_P50": "SUPPORTED",
  "global_gain_sealed_iid": 0.04867929220199585,
  "global_gain_sealed_shift": 0.05719351768493652,
  "conditional_gain_over_global_iid": 0.09428136050701141,
  "conditional_gain_over_global_shift": 0.08056798577308655,
  "full_minus_global_iid": -0.13435772061347961,
  "null_best_gain": 0.0013227462768554688
}
```

The best sparse global policy selected only `transport_modeling`. Conditional routing selected approximately two primitives per task and nearly reached the hidden-family oracle on both sealed splits.

## Revised prediction

> Automated search can discover the smallest **task-conditional** environment mutation that unlocks latent capability. A single global scaffold is generally the wrong object.

## Run

```bash
python experiments/p50-hostile/evaluate_v2.py
```

Dependencies: Python, NumPy, pandas, scikit-learn.
