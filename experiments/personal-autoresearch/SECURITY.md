# Security model

## Enforced by this repository

- Locked evaluator, objective, constraints, catalog, and selected inventory are hashed before a run.
- Each model iteration receives a new workspace and process.
- Only three declared candidate files can be promoted.
- Changes to locked workspace files, unexpected files, symbolic links, invalid schemas, failed hard gates, and non-improving scores are rejected.
- Rejected workspaces and logs remain available for inspection.
- Accepted changes are atomic Git commits on a non-default branch.

## Not enforced by this repository

- `workspace-write` does not prevent the agent from reading other host files.
- The runner does not provide a network egress firewall.
- A malicious or compromised agent can attempt external side effects before the post-run verifier observes them.
- Hash verification detects attempted locked-file changes after execution; it does not undo effects outside the workspace.

## Required execution profiles

### Synthetic or public inputs

A normal workstation is sufficient. Do not provide credentials to the agent process.

### Pseudonymous personal inputs

Use a disposable container, VM, or OS account containing only this repository and an opaque inventory. Keep the ID-to-real-world crosswalk outside that environment. Prefer local inference.

### Authenticated or consequential work

Do not expose live credentials to this optimization loop. Export a read-only, minimized dataset into an isolated environment. After research converges, move approved proposals into a separate actuation workflow with named authorization, previews, rate limits, receipts, rollback, and human acceptance.
