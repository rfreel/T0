# Executable Value Proposals

This branch proposes three ways to turn T0 from a self-referential loop scaffold into a persistent system that produces externally useful artifacts. Choose one first. Do not build shared infrastructure until the first witness works.

## 1. Source-grounded semantic twin

**Outcome**

A local, inspectable knowledge system that converts a technical source into structured claims, concepts, relations, and exact provenance, then answers queries with source pointers.

**First witness**

Ingest one bounded source into SQLite and JSONL. Provide a CLI that can:

```text
source-twin ingest <file>
source-twin search "<question>"
source-twin trace <claim-id>
```

Each answer must return the source file, page or section locator, extracted passage, transformation history, and confidence.

**Acceptance**

- One real PDF or book-derived corpus is ingested end to end.
- At least 25 claims and 25 concept relations are stored.
- Five held-out questions return useful answers with exact provenance.
- Re-running ingestion is deterministic and does not duplicate records.
- The database and exports survive independently of chat.

**Likely stack**

Python, SQLite, PyMuPDF or equivalent parser, JSONL exports, pytest. Embeddings are optional and must not be required for the first witness.

**Estimated first witness**

1-2 focused engineering days; runs comfortably on CPU and the available RTX 2080 Super if local embeddings are later added.

**Long-term value**

Highest. It compounds every future research and source-tracing task while preserving provenance.

## 2. Evidence compiler

**Outcome**

A command-line tool that turns a question, source set, and calculations into a reproducible decision packet rather than a transient chat answer.

**First witness**

```text
evidence-compile build case.yaml
```

The command emits:

```text
output/report.md
output/claims.json
output/sources.json
output/calculations.csv
output/manifest.json
```

The manifest records input hashes, tool version, timestamps, assumptions, unresolved claims, and verification status.

**Acceptance**

- One real decision case compiles end to end.
- Every material claim maps to at least one source or is explicitly marked as inference.
- Calculations are independently re-runnable.
- Changing an input produces a visible diff in the output packet.
- The result is usable without reading the originating chat.

**Likely stack**

Python, YAML, Markdown templates, SQLite or JSON, pandas only where tabular calculations justify it, pytest.

**Estimated first witness**

1 focused engineering day.

**Long-term value**

High. It converts research, estimating, negotiations, and technical analysis into durable, reviewable artifacts.

## 3. Contract-tested capability package

**Outcome**

Turn the existing tested primitives in T0 into a small installable package with versioned behavioral contracts and one independent consumer.

**First witness**

Promote `normalize_identifier` from an isolated experiment into a package with:

```text
pip install -e .
python -m t0_identifiers verify-contract
```

Add a separate example consumer that imports the package and demonstrates a compatible upgrade and a deliberately incompatible upgrade rejected by tests.

**Acceptance**

- Package installs in a clean environment.
- Producer tests and consumer contract tests pass in CI.
- A breaking contract change fails the consumer test before merge.
- Version, contract, rollback point, and immutable commit are recorded.
- No planning report is accepted as progress without runnable behavior.

**Likely stack**

Python packaging, pytest, GitHub Actions.

**Estimated first witness**

Half to one focused engineering day because much of the primitive already exists.

**Long-term value**

Medium-high. It is the fastest route from current repository state to a real reusable capability, but it compounds less broadly than the semantic twin.

## Recommended sequence

1. Execute Proposal 3 first as the cheapest proof that T0 can ship a reusable capability.
2. Build Proposal 1 as the main compounding asset.
3. Add Proposal 2 only when a real decision case is ready to compile.

The first implementation branch should contain runnable code, tests, and one externalized artifact. No additional loop, governance, or planning files are required.