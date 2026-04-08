# Agent Trace-Sharing Layer — Design Spec

## Problem
Each agent operates in isolation. When HR fails a CV, CEO doesn't know. When CTO fixes a cron bug, CMO doesn't learn. Failures repeat across agents because there's no shared memory of what went wrong.

## Architecture

```
memory/agent-traces/
├── trace-log.jsonl          # Append-only, all agents, all events
├── index.json               # Quick-read summary (last 50 entries, categorized)
├── lessons.md               # Human-readable persistent lessons (curated)
└── readme.md                # How agents use this system
```

## Trace Format (one line per entry in trace-log.jsonl)

```json
{
  "id": "trace-20260403-001",
  "agent": "HR",
  "timestamp": "2026-04-03T06:05:00Z",
  "category": "cv_creation",
  "action": "Generate ATS resume for Senior PM role",
  "outcome": "failed",
  "error": "ATS score 72 — missed keywords: stage-gate, QBR, JCI compliance",
  "root_cause": "Master CV missing keywords; used generic PMO phrasing instead of JD-specific terms",
  "fix": "Added JD keywords to CV context before generation; ATS score improved to 88",
  "lesson": "Always inject top 5 JD keywords into CV generation context, even on tight deadlines",
  "expires": null
}
```

## When to Write a Trace

**Always write (all agents):**
- External action failed (job apply rejected, API error from non-auth cause)
- Logic error (wrong data, hallucinated facts, misread document)
- Skill triggered but didn't work (tool output wrong, format rejected)
- User corrected the agent
- Performance issue (took 3x longer than expected)

**Don't write (noise):**
- Transient network errors (already retried successfully)
- Gateway restarts, timeouts, platform issues
- "I couldn't find X" where X doesn't exist by design
- Rate limit hits (these are operational, not learnable)

## When to Read Traces

**Before starting a task — quick index scan:**

```python
# Pseudocode — what each agent does at task start
traces = read("memory/agent-traces/index.json")
relevant = filter_by_category(traces, task_category, limit=3)
if relevant:
    apply_lessons(relevant)
```

**Reading rules:**
1. Always scan `index.json` at task start
2. Filter by category match (cv_creation, job_apply, content_post, cron, etc.)
3. Load last 3 relevant traces maximum
4. Apply lessons to current approach
5. If a trace's fix solved it → use same fix. If trace is unresolved → avoid that approach

## Categories

| Category | Agents That Care | Example |
|----------|-----------------|---------|
| `cv_creation` | HR, CEO | ATS score failures, format issues |
| `job_apply` | HR | Pipeline breaks, JD parsing failures |
| `content_post` | CMO, CEO | LinkedIn truncation, image issues |
| `cron_automation` | CTO, CEO | Cron failures, script bugs |
| `tool_integration` | ALL | API changes, auth expiry, rate limits |
| `research` | CEO, CMO | Bad data sources, outdated info |
| `communication` | ALL | Telegram delivery failures, notification routing |
| `config_system` | CTO | Gateway issues, permission changes |

## Index.json Structure

```json
{
  "updated_at": "2026-04-03T06:05:00Z",
  "total_traces": 47,
  "by_category": {
    "cv_creation": [{"id": "trace-...", "lesson": "...", "severity": "high"}],
    "job_apply": [...],
    ...
  },
  "recent": [
    {"id": "trace-...", "agent": "HR", "category": "cv_creation", "lesson": "...", "timestamp": "..."},
    ...last 50 entries...
  ]
}
```

## Lessons.md — Persistent Knowledge

Auto-curated from traces that meet criteria:
- Same error appeared 2+ times across agents or sessions
- Agent corrected by user (auto-correction trigger)
- High-impact failure (external communication, data loss, public post error)

This file is the "what we learned" document — human-readable, short, actionable.

```markdown
# Agent Lessons Learned

## CV Creation
- ✅ Always inject top 5 JD keywords before generation (HR, 2026-04-02)
- ✅ ATS scores below 82 need manual review before sending (CEO, 2026-04-01)

## LinkedIn Posting
- ❌ Never post without image review — we truncated content twice (CMO, 2026-03-23)
- ✅ Pull images from Notion blocks, never Google Drive links (CMO, 2026-03-25)

## Telegram Notifications
- ❌ CLI uses `--target` not `--to` — silent failure (CTO, 2026-03-30)
```

## Implementation Plan

1. Create directory structure
2. Add trace-writing hook to agent workflow (write to jsonl after every task)
3. Add index auto-update script (maintains index.json from jsonl)
4. Update AGENTS.md with read/write rules for all agents
5. Seed with existing known failures (post a few lessons from MEMORY.md incidents)

## Cross-Agent Benefits

| Scenario | Without Traces | With Traces |
|----------|---------------|-------------|
| HR applies to job, CV gets 72 ATS | HR tries again same way next time | CTO sees trace, adds keyword injection to pipeline |
| CMO posts LinkedIn with truncated text | Happens again next post | HR reads lesson "never post without length check" |
| CEO uses wrong Telegram CLI param | Fails silently, nobody knows | CMO learns correct param before first notification |
