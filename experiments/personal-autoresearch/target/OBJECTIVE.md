# Objective — Service Replacement Portfolio

Choose one verified option for every recurring service in the inventory to maximize the deterministic outcome score while satisfying every hard constraint.

The score rewards:

- lower recurring cost relative to the current portfolio;
- retention of required capabilities;
- privacy;
- reliability;
- low migration effort;
- low ongoing maintenance burden.

The score does not reward unverified claims or options absent from `catalog.json`.

The output at each accepted turn is:

1. a complete, schema-valid `candidate/portfolio.json`;
2. a concise experiment record in `candidate/RESEARCH_NOTES.md`;
3. optional unverified discoveries in `candidate/research_queue.json`.
