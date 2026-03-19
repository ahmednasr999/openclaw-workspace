# Lessons Learned

## 2026-03-19

### What I Missed
LinkedIn daily post cron posted WITHOUT image when image upload failed, then failed to update Notion because of wrong property type (sent rich_text instead of url type).

### Why
1. **Gave up instead of fixing:** Cron agent hit image upload error and chose "post without image" instead of diagnosing and retrying with a different method
2. **Bug in SKILL.md:** Error handling section literally said "If image upload fails: Post WITHOUT image" - gave agents explicit permission to deliver partial results
3. **Bug in script:** `update_notion_status()` used `rich_text` format for Post URL property, but Notion property type is `url`
4. **No retry logic:** Both failures were single-attempt with no diagnosis or alternative approaches

### Fix
1. Added "Never Give Up" rule to SOUL.md - applies to ALL agents, ALL models, ALL tasks
2. Rewrote linkedin-daily-post/SKILL.md - removed "post without image" fallback, added 3-attempt retry strategies for every failure mode
3. Fixed Post URL property type in both SKILL.md and linkedin-auto-poster.py (url, not rich_text)
4. Added proxy_execute method as primary post creation path (avoids Composio S3 key requirement for images)

### Real Damage
- 4 LinkedIn likes lost (had to delete and re-post)
- Algorithm cold restart on re-posted content
- Engagement damage is permanent - can't recover those impressions

### Rule (Permanent)
**Partial completion = failure.** Never post without image if content has one. Never skip Notion update. Diagnose errors, try 3+ approaches, only report failure after exhausting all options.

---

## 2026-02-17

### What I Missed
1. Didn't check Telegram ID before cron ran → caused failure
2. Let files accumulate → should have synced to GitHub org earlier
3. Built web dashboard reactively → should have offered proactively
4. Didn't connect Renato's tweet to our workflow immediately

### Why
- Assumed "Ahmed" would work
- Focused on single tasks, not system design
- Waiting for instructions instead of anticipating needs

### Fix
1. Always verify target identifiers before configuring crons
2. At session start, ask "What should we sync/push today?"
3. When something works, immediately ask "How does this fit the bigger picture?"
4. End every session with: What did I miss? What will I do differently?

---

## Template (Future)

```
## [Date]

### What I Missed
1. [Specific example]
2. [Specific example]

### Why
- [Root cause 1]
- [Root cause 2]

### Fix
- [What I'll do differently 1]
- [What I'll do differently 2]
```
