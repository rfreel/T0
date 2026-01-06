# Collaboration Contract for Codex and Humans

## Purpose

Provide clear guidance for AI and human contributors to collaborate safely and ship high-quality software. This repository is a production-grade template; every change must respect the standards below.

## Allowed Actions

- Edit code, configuration, and documentation in this repository.
- Run local checks (format, lint, typecheck, test, build).
- Open and review pull requests.

## Forbidden Actions

- Exfiltrating secrets or credentials.
- Performing destructive operations (e.g., deleting data, modifying external systems).
- Making network calls unless explicitly required for repository tooling (e.g., dependency installs).

## Workflow

1. Start from an issue or well-defined task.
2. Create a branch from `main` for your work.
3. Implement changes with frequent commits.
4. Run self-checks: format → lint → typecheck → test → build.
5. Update documentation for any behavioral or tooling changes.
6. Open a pull request referencing the issue; ensure CI passes.

## Quality Gates

- `pnpm format:check`, `pnpm lint`, `pnpm typecheck`, `pnpm test`, and `pnpm build` must all pass.
- Documentation updates accompany functional or tooling changes.
- Add or update tests for new behavior.
- Follow commit conventions and ensure changelog/release notes are updated when relevant.
- Commit `pnpm-lock.yaml` changes alongside dependency updates.

## Coding Standards

- Prefer small, composable modules and pure functions where possible.
- Use explicit typing; avoid `any` unless unavoidable and documented.
- Handle errors with informative messages; avoid silent failures.
- Logging: keep concise and actionable; do not log secrets.
- Comments: explain reasoning, not obvious code; keep TODOs actionable with issue links.
- Naming: descriptive and consistent; functions use verbs, constants use nouns.

## Review Policy

- Request human review for public API changes, dependency upgrades, security-sensitive code, or architectural shifts.
- High-risk areas (security, build tooling, release automation) always require review.

## Commit Message Convention

- Format: `type(scope): summary` (e.g., `feat(cli): add run command`).
- Types: feat, fix, chore, docs, test, refactor, ci, build.

## Definition of Done

- All quality gates pass locally and in CI.
- Documentation updated (README, agents.md, or relevant docs).
- Tests cover new or changed behavior.
- No unresolved TODOs without linked issues.
- PR description includes what changed, why, and how to verify.

## Using Codex Here

- Target Node.js >=20 (template tested on Node 22).
- Use `pnpm@10.13.1` (pinned via `packageManager`). If Corepack cannot fetch it, ensure the version is available locally before running commands.
- If `pnpm` is missing, run `corepack prepare pnpm@10.13.1 --activate` to install the shimmed binary.
- To run checks: `pnpm format`, `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`.
- To update dependencies: `pnpm update` (ensure CI stays green).
- To create releases: follow the README defaults section and document any deviations.
- Update the registry in `.npmrc` only if required by your environment and regenerate `pnpm-lock.yaml` afterward.
- To run checks: `pnpm format`, `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`.
- To update dependencies: `pnpm update` (ensure CI stays green).
- To create releases: follow the README defaults section and document any deviations.
