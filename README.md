# UTP Callable-Agent Scaffold (TypeScript)

This repository now implements a **Universal Transpilation Protocol (UTP)** as a series of callable agents.

## Pipeline
- `Structural_Analyst`
- `Abstract_Specifier`
- `Domain_Specialist`
- `Variance_Detector`

Each phase is implemented as a callable agent module in `src/utp/` and orchestrated by `UtpOrchestrator`.

## Run
```bash
pnpm install
pnpm dev
```

The entrypoint prints exactly five ordered sections:
1. `STRUCTURAL_LOGIC_MAP`
2. `MEDIUM_AGNOSTIC_SPEC`
3. `TARGET_ARTIFACT`
4. `AUDIT_REPORT`
5. `PATCH_INSTRUCTIONS`
