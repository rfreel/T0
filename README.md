# UTP Agent Portability Layer

TypeScript implementation of the Universal Transpilation Protocol (UTP) with strict schemas, deterministic run artifacts, and portable tool-harness adapters.

## 60-second first successful run
```bash
pnpm install
pnpm utp:run --source examples/utp/prompt-stack/inputs/source.txt --source-domain prompt-stack --target-domain prompt-stack --target-env local --out runs
# copy printed run path, then:
pnpm utp:audit --run runs/<utc-iso>
```

## Documentation
- [UTP scope/non-goals](docs/utp/SCOPE.md)
- [Architecture](docs/utp/ARCHITECTURE.md)
- [Usage](docs/utp/USAGE.md)
- [Schemas](docs/utp/SCHEMAS.md)
- [Adding adapters](docs/utp/ADDING_ADAPTERS.md)
- [Failure modes](docs/utp/FAILURE_MODES.md)

## CLI entrypoints
- `pnpm utp:run`
- `pnpm utp:audit`
- `pnpm utp:replay`

## Testing
- `pnpm test`
- `pnpm test:integration`
- `pnpm test:golden`
