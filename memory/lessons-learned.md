# Lessons Learned

- 2026-02-26: **Never ask Ahmed for information he already shared — ever.** He has a powerful memory system. Search memory, knowledge bank, and session history BEFORE asking. If it was shared, find it. Only ask if genuinely not found after exhausting all sources.

- 2026-02-26: **Never guess — always verify with evidence before making any claim.** Got corrected 3+ times in one session for presenting guesses as facts (OAuth token type, subscription usage, API costs). Rule: if I can't verify it, I say "I don't know, let me check" — never fabricate a confident answer. Ahmed's standard: always sure, always evident.

- 2026-02-26: **Never ask Ahmed to re-share content without exhausting all checks first.** `memory_search` alone is insufficient — it can miss content in specific files. Correct sequence: (1) check all `memory/knowledge/*.md` files directly, (2) run memory_search with multiple queries, (3) check recent session transcripts. ONLY THEN ask Ahmed to re-share. Asking him to repeat himself when content was already saved = wasted time + broken trust.

- 2026-02-25: **Skip ai-pdf-builder for CVs.** Use pandoc directly: `pandoc input.md -o output.pdf --pdf-engine=pdflatex -V geometry:margin=0.7in -V fontsize=10pt -V linestretch=1.1`. The ai-pdf-builder chokes on markdown tables and adds unnecessary formatting. Pandoc is 5 seconds, ai-pdf-builder is 3 retries and wasted time.

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

## 2026-02-25

### What I Missed
1. Spent hours trying to authenticate ahmednasr999@gmail.com with OAuth without first asking "why does nasr.ai.assistant work?"
2. Jumped into trying tools before analyzing root cause
3. Kept suggesting "paste transcript" instead of solving the real problem

### Why
- Didn't connect the dots: same account = ownership conflict
- Reactive instead of strategic thinking
- Gave up too easily on fixing OAuth

### Fix
- When OAuth blocks project owner account → use DIFFERENT account to own the project
- Always ask "what's fundamentally different?" before trying solutions
- Save patterns to memory (created oauth-patterns.md)

### What We Gained
- Full Gmail access to ahmednasr999@gmail.com
- nasr.ai.assistant@gmail.com working
- Tavily search (autonomous web search)
- Job radar running daily
- Both Gmail accounts accessible

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

---

**Links:** [[../MEMORY.md]] | [[active-tasks.md]] | [[../AGENTS.md]]

- 2026-03-05: **TOOL ACCESS SILENTLY DOWNGRADED.** `tools.profile` in `openclaw.json` was set to `"messaging"`, stripping exec/read/write/edit/process from all sessions. Likely caused by OpenClaw 2026.3.2 update or onboarding wizard re-run (18:12 UTC today). Result: NASR lost shell access, calendar crons failed, could not self-diagnose. Fix: changed to `"full"`, added `tools.profile` to DRY RUN protected list in AGENTS.md. Rule: after any OpenClaw update, verify `tools.profile` is `"full"` before declaring update successful.

- 2026-02-26: **CV DELIVERY DELAY — 12 min gap between CV ready and PDF sent.** Sub-agent finished at 09:55 UTC. PDF not generated until Ahmed asked at 10:07 UTC. Root cause: I read the sub-agent output but waited for user to trigger PDF generation instead of doing it automatically. Fix: When a CV sub-agent completes, IMMEDIATELY generate PDF and send to Telegram. No waiting. No confirmation needed. Auto-deliver = done.
