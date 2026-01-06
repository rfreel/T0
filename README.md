# T0: TypeScript Library + CLI Template

A production-grade starter for building TypeScript libraries with a companion CLI. It includes opinionated tooling (pnpm, TypeScript, ESLint, Prettier, Vitest) and GitHub automation (CI, CodeQL, Dependabot) to ensure high quality from the first commit.

## Quickstart

1. Ensure Node.js 20+ is installed (tested on Node 22). Enable Corepack to manage pnpm:
   ```bash
   corepack enable
   corepack prepare pnpm@10.13.1 --activate
   ```
   If you see `pnpm: command not found`, rerun the `corepack prepare` line to install the pinned pnpm.
2. Install dependencies:
   ```bash
   pnpm install
   ```
   The first install will generate `pnpm-lock.yaml`; commit it to keep installs reproducible.
3. Run all checks:
   ```bash
   pnpm ci
   ```
4. Use the CLI:
   ```bash
   pnpm cli --name "Ada"
   ```
   > If Corepack cannot download pnpm (e.g., restricted network), ensure `pnpm@10.13.1` is available in your environment before running the scripts.

## Scripts

- `pnpm format`: Apply Prettier formatting.
- `pnpm format:check`: Verify formatting without writing.
- `pnpm lint`: Run ESLint with TypeScript support.
- `pnpm typecheck`: Run the TypeScript compiler in noEmit mode.
- `pnpm test`: Run Vitest.
- `pnpm build`: Emit compiled JavaScript to `dist/`.
- `pnpm ci`: Run format:check, lint, typecheck, test, and build in sequence.

## Project Structure

- `src/index.ts`: Library entry exporting core functionality.
- `src/cli.ts`: CLI wrapper around the library function.
- `tests/`: Vitest test cases.
- `.github/workflows/`: CI and CodeQL automation.
- `.github/ISSUE_TEMPLATE/`: Issue templates for bugs and feature requests.
- `.github/pull_request_template.md`: Pull request checklist aligned with quality gates.
- `.github/CODEOWNERS`: Ownership placeholders; update with your team.
- `agents.md`: Collaboration contract and quality gates.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`: Governance and support docs.

## Defaults

- Runtime: Node.js >=20 (tested with Node 22)
- Language: TypeScript
- Package manager: pnpm (packageManager pinned to 10.13.1)
- Registry: https://registry.npmjs.org/ (see `.npmrc`; update if your environment requires a mirror)
- Test runner: Vitest
- Linting: ESLint
- Formatting: Prettier
- Type checking: `tsc` (noEmit)
- Project type: Library/CLI hybrid
- License: MIT

Any deviations from these defaults must be documented here and enforced in CI.

## Troubleshooting

- **`pnpm: command not found`**: Run `corepack prepare pnpm@10.13.1 --activate` to install the pinned version (or install pnpm 10.13.1 via your package manager).
- **Registry access issues**: Update `.npmrc` with an allowed registry mirror and rerun `pnpm install`. Regenerate and commit `pnpm-lock.yaml` after a successful install.
- **CI uses pnpm 10.13.1** via `pnpm/action-setup@v4`; ensure local tooling matches to avoid lockfile churn.

## Release and Versioning

Releases are manual by default. Tag versions using semantic versioning (e.g., `v1.2.0`) and publish artifacts as needed. Update changelog and documentation alongside releases.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for workflow and expectations.

## Support

See [SUPPORT.md](SUPPORT.md) for how to get help.

## Security

See [SECURITY.md](SECURITY.md) for reporting and handling vulnerabilities.
