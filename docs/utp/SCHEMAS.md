# UTP Schemas

Schemas are implemented in `src/utp/models.ts` using Zod and exported via `exportSchemas()`.

- `pipelineInput`
- `structuralLogicMap`
- `mediumAgnosticSpec`
- `targetArtifact`
- `auditReport`

All phase outputs are `.strict()` and reject extra fields.
