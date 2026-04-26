# Domain Policies

Use these as starting policies. Tighten them before apply mode.

## JobZoom
- Auto-propose reject: duplicate, expired, outside GCC/relocation target, clearly below seniority target, below ATS threshold after scoring.
- Human review: strategic edge cases, confidential companies, roles close to target but unusual title.
- Never auto-apply to jobs unless Ahmed approved the final CV/application path.

## CMO content queue
- Auto-propose: duplicate topic, stale draft, missing approval, scheduled gap.
- Human review: brand-sensitive posts, executive claims, controversial topics.
- Never auto-post unless the approved autoposter lane already covers the exact row/state.

## Email
- Auto-clear: newsletters, routine job alerts, known low-value notices.
- Escalate: interviews, recruiter replies, deadlines, invoices, legal/contract signals, access/security alerts.
- Never send replies without explicit approval.

## OpenClaw health
- Auto-propose: repeated errors, cron failures, config drift, stale queues.
- Human review: gateway restarts, config changes, model routing changes, external writes.
- Never restart the live gateway casually from an active user-facing run.
