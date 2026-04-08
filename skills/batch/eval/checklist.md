# Batch Skill Evaluation Checklist

| # | Check | Pass/Fail |
|---|-------|-----------|
| 1 | All items accounted for (completed + failed + skipped = total) | |
| 2 | Failed items have specific error messages (not generic) | |
| 3 | Rate limits were respected (check audit log for burst patterns) | |
| 4 | Checkpoint exists for batches >50 items | |
| 5 | Final report includes duration and per-item breakdown | |
| 6 | No silent failures (every error logged to audit-log.jsonl) | |
