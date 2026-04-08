# Pre-Flight Checks - All Agents

Every agent MUST self-verify before reporting task completion.

## Writer Agent Pre-Flight

Before delivering any LinkedIn post:
- [ ] Image exists and is accessible? (If no, retry upload 3x before going image-less)
- [ ] Bold text converted to Unicode? (No markdown ** in output)
- [ ] Word count 150-300?
- [ ] CTA or question at end?
- [ ] No em dashes?
- [ ] No links in body? (Links go in first comment)
- [ ] Does this sound like Ahmed specifically?

Before delivering any comment:
- [ ] Is this for review only? (NEVER auto-post comments)
- [ ] Does it add value beyond "great point"?
- [ ] Under 100 words?

## CV Agent Pre-Flight

Before delivering any CV:
- [ ] Single column layout?
- [ ] No tables, multi-column, or text boxes?
- [ ] No images, icons, or special bullets?
- [ ] Top 5 JD keywords in Summary?
- [ ] Top 5 JD keywords in most recent role?
- [ ] All data from master CV only?
- [ ] ATS score calculated and reported?
- [ ] Both HTML and PDF generated?
- [ ] Filename correct: `Ahmed Nasr - {Title} - {Company}.pdf`?

## Max / Chief of Staff Pre-Flight

Before delivering any briefing:
- [ ] Is there a clear recommendation? (Not just information)
- [ ] Are 3+ options provided with trade-offs?
- [ ] Is it actionable immediately?
- [ ] Executive summary under 3 sentences?
- [ ] Bad news surfaced early, not buried?

## Research Agent Pre-Flight

Before delivering research:
- [ ] Every claim sourced?
- [ ] Facts separated from inferences?
- [ ] Information age flagged?
- [ ] Organized for quick scanning?

## Scheduler Agent Pre-Flight

Before marking cron complete:
- [ ] Expected output created?
- [ ] Output non-empty and valid?
- [ ] Any errors in log?
- [ ] Consistent with previous runs?

---

## How to Use

1. Run through checklist BEFORE saying "done"
2. If ANY checkbox fails, fix it first
3. If unable to fix, escalate with specifics
4. NEVER deliver with known failures
