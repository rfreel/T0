# INPUT₅β — Operational Compounding Externalization

This experiment closes the previously blocked external-consequence condition by publishing a tested primitive to GitHub through a reversible draft pull request.

## Primitive

`normalize_identifier(raw)` performs:

1. Unicode NFKC compatibility normalization.
2. Leading and trailing whitespace removal.
3. Unicode-aware case folding.
4. Rejection of control and format characters.

The primitive is shared by user, order, and invoice identifier parsers.

## Independent consequence metric

The artifact passes six repository tests, including three adversarial Unicode/security cases:

```text
6 passed in 0.03s
```

GitHub-side consequence is measured by:

- branch and commit existence outside the local runtime;
- draft pull request creation;
- repository checks, when configured;
- unchanged default branch until human review and merge.

## Authority and rollback boundary

- Target: `rfreel/T0`.
- Publication authority: the user's explicit `@GitHub INPUT₅β` instruction.
- Write surface: new branch and draft PR only.
- Default branch is not modified.
- No merge, release, deployment, secret change, or destructive action is authorized.
- Rollback: close the draft PR and delete the branch.

## Local verification

```bash
cd experiments/input5-beta
python -m pytest -q
```
