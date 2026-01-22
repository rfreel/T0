# AGENTS

This repo is run as a Ralph loop: one small goal per iteration; state persists in files.

## The loop
1) Pick exactly ONE item in prd.json where passes=false.
2) Make the smallest change that satisfies its acceptance criteria.
3) Update prd.json (passes=true + notes).
4) Append ONE line to progress.txt (what changed + what you learned).
5) Merge.

## Rules
- One PRD item per PR.
- No drive-by refactors.
- If you cannot explain the PR in one sentence, split it.

## Commit messages
docs|chore|feat|fix: [PRD-ID] short description

