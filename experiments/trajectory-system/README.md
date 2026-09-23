# Trajectory System Bootstrap

Home: `rfreel/T0/experiments/trajectory-system`

Purpose: preserve objectives, externalize state, execute only to decision-changing observations, verify independently, and update procedures without self-certification.

## Current state

This namespaced T0 experiment contains all 27 source skill files, five normalized candidate procedures, schemas, a live trajectory record, recovery state, and a deterministic validator. It is isolated from T0's canonical loop and does not alter root behavior.

## Verify

From the T0 repository root:

```bash
python experiments/trajectory-system/tests/verify_repository.py
```

Or from this directory:

```bash
python tests/verify_repository.py
```

## Resume

Read in order:

1. `kernel/KERNEL.yaml`
2. `state/ACTIVE_TRAJECTORY.json`
3. `state/RECOVERY.json`
4. matching procedures under `procedures/`

The current publication boundary is a dedicated branch and draft pull request. Merge, deployment, release, secret changes, and destructive actions remain outside authorization.
