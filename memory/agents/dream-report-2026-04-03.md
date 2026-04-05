# Dream Report - 2026-04-03

## Promoted (1 item)
- [OpenClaw Cron CLI Gotchas] → TOOLS.md (reason: confirmed blocker on 2026-04-03 session; `openclaw cron list` crashes gateway, `cron add` has no working syntax, cron entries live in gateway DB not openclaw.json; exec security config also undocumented; direct impact on all cron-related work)

## Deduplicated (0 items)
- None needed - no duplicate entries found

## Archived (0 files)
- No daily notes older than 14 days found (oldest in-scope: 2026-03-31)

## Flagged Stale (0 items)
- No stale entries found (no `<!-- completed -->` tags, no entries without recent references)

## Skipped (3 items)
- [MEMORY.md promotion: exec security config / cron CLI rules] → MEMORY.md ALREADY EXCEEDS 200-LINE CAP (243 lines). Promotion skipped per safety rail. **ACTION REQUIRED: MEMORY.md needs pruning before next dream run can promote to it.**
- [SOUL.md promotion: "autonomous execution preference" / "go do it yourself"] → only 1 occurrence in Apr 3 notes; threshold is 3+. Skipped.
- [MEMORY.md promotion: 3-tier approval policy state] → MEMORY.md cap exceeded. Documented in TOOLS.md instead (exec security config block).

## Flags

### ⚠️ MEMORY.md Over Cap
MEMORY.md is at **243 lines** (cap: 200). Next dream run cannot safely promote to it.
Recommend pruning these candidates:
- `## Strategic Intelligence Framework (Optional)` - marked optional, infrequently triggered, could move to AGENTS.md or archive
- `## Memory System Protocol` Lessons Learned Log subsection (format template) - already documented in lessons-learned.md itself, redundant here
- Consider merging `## CV Design Rules` summary with a pointer to `memory/ats-best-practices.md` (source of truth already exists)

### Notable Patterns from Last 7 Days
- **Gateway restart risk** confirmed and promoted (2026-04-02 dream run) - no re-occurrence in new sessions ✅
- **Heredoc block** promoted (2026-04-03 earlier) - workarounds now documented ✅
- **OpenClaw cron CLI** is the only new undocumented failure mode from this period - now captured
- **Job pipeline** running well: 1,911 jobs, 41 SUBMIT, 26 REVIEW, skip rate healthy at 95.9%
- **CV output** strong: 5+ CVs committed this week with ATS 84-96%
