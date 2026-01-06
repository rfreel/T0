# Contributing Guide

## Workflow

1. Create a branch from `main` for your change.
2. Make small, focused commits following `type(scope): summary`.
3. Keep documentation and tests in sync with code changes.
4. Run local checks before opening a PR:
   ```bash
   pnpm format:check
   pnpm lint
   pnpm typecheck
   pnpm test
   pnpm build
   ```
5. Open a pull request referencing any related issues. Describe what changed, why, and how to verify. Ensure CI is green.

## Pull Request Expectations

- Include tests for new or changed behavior.
- Update README or other docs when behavior, tooling, or workflows change.
- Avoid introducing lint warnings or type errors.
- Keep PRs focused and reasonably sized.

## Coding Standards

- Prefer pure functions and small modules.
- Use explicit types; avoid `any` unless documented.
- Handle errors with context-rich messages; avoid swallowing exceptions.
- Do not log secrets or sensitive data.
- Write comments for intent, not obvious code.

## Commit Messages

Use `type(scope): summary` where `type` is one of `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `ci`, or `build`.

## Release Process

Tags follow semantic versioning. Update changelog and documentation with each release. Include summary of changes and verification steps in release notes.
