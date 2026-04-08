# intel/ — Shared Intelligence Layer

**One write, many reads.** This directory is the coordination backbone between agents.

## Files

| File | Writer | Readers | Purpose |
|------|--------|---------|---------|
| `DAILY-INTEL.md` | Intel Sweep cron (05:45 Cairo) | CEO, HR, CMO agents | Daily research digest |
| `intel-YYYY-MM-DD.md` | Same cron | Archive only | Dated history |

## How Agents Use It

**CEO Agent** — reads Section 1 (Hot Topics) in morning briefing for context
**HR Agent** — reads Section 2 (Job Market) + Section 4 (Company Intel) before pipeline work
**CMO Agent** — reads Section 1 + Section 3 (LinkedIn Opportunities) before drafting content

## DAILY-INTEL.md Sections

1. **Hot Topics** — AI/Tech/PMO signals, fresh angles for content
2. **Job Market Signals** — executive hiring trends in GCC
3. **LinkedIn Engagement Opportunities** — fresh posts + suggested comment angles
4. **Company Intel** — news on Cigna, G42, Involved Solutions, other active targets
