# Chief of Staff Skill
# Agent Coordination and Orchestration

## Purpose
Chief of Staff (Max) coordinates all specialist agents, maintains the big picture, generates daily briefs, and handles crisis escalation.

## Usage
```
openclaw agent run chief-of-staff --message "Generate morning brief"
openclaw agent run chief-of-staff --message "Review pipeline and flag issues"
openclaw agent run chief-of-staff --message "Weekly synthesis and strategy report"
```

## Files Managed

### Coordination Files
- `coordination/dashboard.json` - Key metrics and status
- `coordination/pipeline.json` - Job application pipeline
- `coordination/content-calendar.json` - LinkedIn content
- `coordination/outreach-queue.json` - Lead outreach queue

### Memory Files
- `memory/agents/daily-[date].md` - Daily agent outputs
- `memory/agents/weekly-brief.md` - Weekly synthesis

## Commands

### Daily Brief
```bash
openclaw agent run chief-of-staff --message "
1. Read yesterday's agent outputs from memory/agents/
2. Update coordination/dashboard.json with:
   - Pipeline metrics
   - Content performance
   - Outreach progress
3. Identify stuck items or bottlenecks
4. Generate morning brief for human review
5. Flag urgent items (interviews, deadlines)
"
```

### Weekly Review
```bash
openclaw agent run chief-of-staff --message "
1. Synthesize all agent outputs from this week
2. Update coordination/pipeline.json with weekly stats
3. Calculate conversion rates and trends
4. Generate strategy report:
   - What's working
   - What's not
   - Next week's priorities
5. Update dashboard with weekly summary
"
```

### Pipeline Check
```bash
openclaw agent run chief-of-staff --message "
1. Review coordination/pipeline.json
2. Identify applications needing follow-up
3. Flag expired opportunities
4. Update metrics in dashboard.json
5. Report: Active: X, Interview: Y, This Week: Applied Z
"
```

### Content Review
```bash
openclaw agent run chief-of-staff --message "
1. Read coordination/content-calendar.json
2. Review drafts needing approval
3. Check scheduled posts for tomorrow
4. Update engagement metrics from LinkedIn
5. Report: Published: X, Scheduled: Y, Drafts: Z
"
```

### Outreach Audit
```bash
openclaw agent run chief-of-staff --message "
1. Read coordination/outreach-queue.json
2. Check follow-ups due today
3. Review pending queue for priority items
4. Update targets in dashboard.json
5. Report: Sent: X, Accepted: Y, Pending: Z
"
```

## Coordination Protocol

### With Content Agent
- Content Agent → writes to `coordination/content-calendar.json`
- Chief of Staff → reviews, approves/requests revisions
- Human → final approval before publishing

### With Outreach Agent
- Outreach Agent → writes to `coordination/outreach-queue.json`
- Chief of Staff → ensures follow-ups happen
- Human → reviews discovery call outcomes

### With Research Agent
- Research Agent → writes findings to `memory/agents/research/`
- Chief of Staff → synthesizes for human review
- Human → uses insights for applications/LinkedIn

### With Scheduler Agent
- Scheduler Agent → maintains cron jobs
- Chief of Staff → monitors for failures
- Human → receives alerts for critical issues

## Integration

### Cron Jobs
```json
{
  "name": "Chief of Staff - Daily Brief",
  "schedule": "0 8 * * *",
  "message": "Generate morning brief from yesterday's agent outputs",
  "agent": "chief-of-staff"
}
```

### Subagents
- Content Agent
- Outreach Agent  
- Research Agent
- Scheduler Agent

## Metrics Tracked

| Metric | Source | Frequency |
|--------|--------|------------|
| Pipeline velocity | pipeline.json | Daily |
| Content engagement | content-calendar.json | Daily |
| Outreach completion | outreach-queue.json | Daily |
| Agent health | dashboard.json | Daily |

## Notes
- Chief of Staff is the "single source of truth"
- All agents write to coordination files
- Human reviews outputs before critical actions
- Crisis items get immediate notification
