---
name: content-agent
description: Autonomous LinkedIn content engine. Weekly batch creation, daily posting, engagement orchestration, performance learning loop. Runs on cron or on-demand. Handles the full lifecycle from ideation to post-mortem analysis.
metadata: {"openclaw":{"emoji":"🎯"}}
---

# Content Agent

Autonomous content engine for Ahmed Nasr's LinkedIn presence. Creates, publishes, engages, and learns.

## Architecture

Five layers, each with its own instruction file. Load ONLY the layer needed for the current task.

```
CREATE  →  REVIEW  →  PUBLISH  →  ENGAGE  →  LEARN
(Friday)   (human)    (daily)    (daily)    (weekly)
```

## Layer Triggers

| Task | Layer | Load File | Model |
|------|-------|-----------|-------|
| Weekly batch creation | CREATE | `instructions/create.md` | Sonnet 4.6 |
| Quality gate check | REVIEW | `eval/checklist.md` | Sonnet 4.6 |
| Daily auto-post | PUBLISH | `instructions/publish.md` | MiniMax-M2.7 |
| Comment radar + replies | ENGAGE | `instructions/engage.md` | MiniMax-M2.7 |
| Weekly performance review | LEARN | `instructions/learn.md` | Sonnet 4.6 |
| Image generation | CREATE | `instructions/image-genres.md` | MiniMax-M2.7 |

## Workflow

### 1. CREATE (Friday 10 AM Cairo)

Read `instructions/create.md`. Steps:

1. Read `references/content-performance.json` — what's working, what's not
2. Read `references/content-mix.md` — check current mix ratios vs. targets
3. Read `references/experiments.md` — this week's active experiment
4. Pull next week's topics from Notion Content Calendar (Status=Ideas or Scheduled)
5. For each post:
   a. Select post type based on mix ratio needs
   b. Write 3 hook variants (curiosity gap, bold claim, specific story)
   c. Draft full post using `instructions/voice-and-format.md` rules
   d. Generate image using `instructions/image-genres.md` genre matching
   e. Run quality gate from `eval/checklist.md`
   f. If fail → revise (max 2 attempts) → if still fail, flag for human
6. Save all drafts to Notion with Status=Drafted
7. Tag each post with: type, pillar, hook_style, experiment_variable (if any)
8. Report summary to Ahmed via Telegram

### 2. REVIEW (Human-in-the-loop)

Ahmed reviews in Notion Content Calendar. Three actions:
- **Approve** → Status=Scheduled (auto-posts on planned date)
- **Edit** → Ahmed edits directly, sets Status=Scheduled
- **Reject** → Status=Ideas with comment, agent creates replacement in next batch

### 3. PUBLISH (Daily 9:30 AM Cairo, Sun-Thu)

Read `instructions/publish.md`. Steps:

1. LinkedIn Preflight at 9:00 AM (existing `linkedin-preflight.py`)
2. Post via Composio `LINKEDIN_CREATE_LINKED_IN_POST` at 9:30 AM
3. Send Telegram alert: "Post live. 60-min engagement window open."
4. At 10:30 AM, send: "Engagement window closing."

### 4. ENGAGE (Daily)

Read `instructions/engage.md`. Steps:

1. **Pre-post priming** (9:00 AM): Run Comment Radar for 5 high-PQS posts. Leave substantive comments on 3-5 before our post goes live.
2. **Post-publish** (9:30-10:30 AM): Monitor and draft replies to comments on our post. Present to Ahmed for approval.
3. **Daily radar** (on-demand): When Ahmed asks, find fresh posts for engagement.

### 5. LEARN (Sunday 8 PM Cairo)

Read `instructions/learn.md`. Steps:

1. Fetch past week's post performance (reactions, comments, reposts, impressions if available)
2. Update `references/content-performance.json` with per-post metrics
3. Analyze: which hook type won? which post type? which pillar? which time?
4. Update content mix recommendations
5. Evaluate this week's experiment — winner or loser?
6. Propose next week's experiment
7. Check repurposing candidates (>5% engagement → flag for repurpose)
8. Report weekly digest to Ahmed via Telegram

## Dependencies

- Notion Content Calendar (DB ID: `3268d599-a162-814b-8854-c9b8bde62468`)
- Composio LinkedIn connection (Person URN: `urn:li:person:mm8EyA56mj`)
- LinkedIn Comment Radar skill (`skills/linkedin-comment-radar/`)
- LinkedIn Writer skill (`skills/linkedin-writer/`) — voice rules are canonical
- Brand design system (`instructions/image-genres.md`)
- Telegram alerts (chat ID: 866838380)
