# UTP Architecture

```text
SOURCE_ARTIFACT + domains/env
        |
        v
Phase 1: Deconstructionist
  -> structural_logic_map.json
        |
        v
Phase 2: Ontologist
  -> spec.json
        |
        v
Phase 3: Native Creator
  -> target_artifact.txt + target_artifact.json
        |
        v
Phase 4: Reality Auditor
  -> audit_report.json + patch_instructions.json

All phases append events to run.ndjson and are replayable from run directory.
```

Artifacts are written to `runs/<utc-iso>/` with deterministic ordering and schema-validated payloads.
