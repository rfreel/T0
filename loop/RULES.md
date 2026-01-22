# Rules (hard constraints)

1) Radius: Only the last 50 lines of loop/log.txt may be considered “in context.”
2) One task per loop: Only address the highest-priority prd.json item with passes=false.
3) Error vector: If checks fail, append the failure output into loop/log.txt and store it in loop/last_error.txt.
4) No drive-by refactors: Touch only files required for the chosen PRD item.
