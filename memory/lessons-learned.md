# Lessons Learned

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
