#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

root = Path.cwd()
portfolio_path = root / "candidate/portfolio.json"
portfolio = json.loads(portfolio_path.read_text(encoding="utf-8"))
replacement = {
    "notes": "notes_local_sync",
    "cloud_storage": "cloud_bundle",
    "automation": "automation_managed_lowcost",
}
for decision in portfolio["decisions"]:
    decision["option_id"] = replacement[decision["service_id"]]
portfolio_path.write_text(json.dumps(portfolio, indent=2) + "\n", encoding="utf-8")
(root / "candidate/RESEARCH_NOTES.md").write_text(
    "# Feature-preserving managed replacements\n\n"
    "Hypothesis: lower-cost managed alternatives improve cost and privacy without "
    "crossing per-service feature thresholds.\n\n"
    "Changed all three current selections to verified lower-cost managed options.\n\n"
    "Principal failure mode: migration penalties could exceed recurring savings.\n\n"
    "Reversal condition: revert any service whose measured feature coverage or "
    "reliability falls below its locked threshold.\n",
    encoding="utf-8",
)
