# CRM System

## Overview
Personal CRM for job search, networking, and contact management. Built on SQLite.

## Database
Same DB: `/root/.openclaw/workspace/knowledge-base/kb.db`

## Tables

### contacts
- Track recruiters, hiring managers, colleagues, network
- Auto-discover from Gmail (himalaya)
- Relationship health scoring

### interactions
- Email, meeting, call, LinkedIn, application
- Linked to contacts
- Direction tracking (inbound/outbound)

### job_pipeline
- Full application lifecycle: discovered → applied → screening → interview → offer/rejected/withdrawn
- ATS scores, CV filenames
- Linked to contacts (recruiter/hiring manager)

### follow_ups
- Action items with due dates
- Linked to contacts and jobs
- Status: pending, done, skipped

## Agent Workflows

### When user applies to a job:
1. Create job_pipeline entry (company, role, URL, status)
2. Link to contact if recruiter known
3. Set ATS score from CV creation
4. Create follow-up reminder (1 week)

### When user shares a recruiter email:
1. Auto-create contact (name, email, company, role)
2. Log interaction
3. Link to job pipeline if applicable

### Daily scan (future):
1. Check Gmail for replies from pipeline contacts
2. Update interaction history
3. Flag stale follow-ups
4. Morning briefing with pipeline status

## Quick Queries

```bash
# Pipeline summary
sqlite3 kb.db "SELECT status, COUNT(*) FROM job_pipeline GROUP BY status;"

# All applications
sqlite3 kb.db "SELECT company, role, status, ats_score FROM job_pipeline ORDER BY applied_date DESC;"

# Pending follow-ups
sqlite3 kb.db "SELECT f.action, f.due_date, c.name, j.company FROM follow_ups f LEFT JOIN contacts c ON f.contact_id=c.id LEFT JOIN job_pipeline j ON f.job_id=j.id WHERE f.status='pending' ORDER BY f.due_date;"

# Contact search
sqlite3 kb.db "SELECT name, company, role, last_contact_date FROM contacts WHERE name LIKE '%query%' OR company LIKE '%query%';"
```
