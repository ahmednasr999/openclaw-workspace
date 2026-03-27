# AI Agents Under CTO Management

All production agents CTO oversees, their schedules, last run status, and troubleshooting.

## Agent Registry

| Agent | Purpose | Cron Schedule | Owner | Log File |
|-------|---------|---------------|-------|----------|
| linkedin-engagement-agent | Find best LinkedIn posts for Ahmed to comment on, draft comments | Sun-Thu 01:00 Cairo | CMO | linkedin-engagement.log |
| linkedin-auto-poster | Post Ahmed's content from Notion content calendar | Sun-Thu 09:30 Cairo | CMO | linkedin-auto-poster.log |
| briefing-agent | Compile morning briefing (emails, jobs, calendar, LinkedIn) for CEO | Daily 06:00 Cairo | CEO | briefing-agent.log |
| notion-pipeline-sync | Sync job applications between Notion + ontology graph | Every 2 hours | PMO | notion-pipeline-sync.log |
| jobs-review | Score job opportunities, update "fit" metrics | Part of briefing pipeline | PMO | jobs-review.log (in briefing) |
| cron-dashboard-updater | Update Notion cron health dashboard | Every 1 hour | CTO | cron-dashboard-updater.log |
| application-lock | Prevent duplicate job applications (integrated into pipeline-sync) | Every 2 hours (integrated) | PMO | notion-pipeline-sync.log |
| email-agent | Monitor Gmail for urgent messages | Daily 08:00 Cairo | CEO | email-agent.log |

---

## Detailed Agent Specs

### 1. linkedin-engagement-agent.py

**Purpose:** Daily discovery of high-value LinkedIn posts for Ahmed to comment on

**Script Location:** `/root/.openclaw/workspace/scripts/linkedin-engagement-agent.py`

**Cron Schedule:** `0 1 * * 0-4` (01:00 Cairo, Sunday–Thursday)

**What It Does:**
1. Loads Ahmed's context (sectors, personas, career stage) from MEMORY.md + ontology
2. Searches LinkedIn for fresh posts (via Exa API) matching Ahmed's interests
3. Scores each post: career relevance, comment opportunity, persona fit (0-100)
4. Drafts top 5 comments in Ahmed's voice
5. Sends to Telegram topic 7 (CMO Desk) with approval buttons
6. On approval: posts comment + like on Ahmed-Mac Chrome
7. Logs to ontology: `Person.last_commented`, `Person.last_commented_post`

**Dependencies:**
- Exa API (EXA_API_KEY)
- Ahmed-Mac Chrome (logged in to LinkedIn)
- Telegram bot (TELEGRAM_BOT_TOKEN)
- Notion (optional, for context)

**Failure Modes:**
- **Exa timeout:** Retry next run (AMBER)
- **Ahmed-Mac offline:** Skip posting, send draft to Telegram (AMBER)
- **Telegram send fails:** Retry in next run (AMBER)
- **No posts found:** Log as success (GREEN, empty result)

**Manual Test:**
```bash
python3 /root/.openclaw/workspace/scripts/linkedin-engagement-agent.py --dry-run
# Prints top 5 posts + drafted comments, no Telegram send
```

**Last Run Status:**
Check: `tail -20 ~/.openclaw/logs/linkedin-engagement.log`

---

### 2. linkedin-auto-poster.py

**Purpose:** Automatically post Ahmed's pre-written content from Notion Content Calendar

**Script Location:** `/root/.openclaw/workspace/scripts/linkedin-auto-poster.py`

**Cron Schedule:** `30 9 * * 0-4` (09:30 Cairo, Sunday–Thursday)

**What It Does:**
1. Reads Notion Content Calendar DB (Status=Scheduled, Date=today)
2. Extracts post text, images, formatting
3. Converts markdown bold (`**text**`) to LinkedIn Unicode bold (mathematical alphanumeric symbols)
4. Uploads images to Composio S3 (if image in post)
5. Posts via `LINKEDIN_CREATE_LINKED_IN_POST` (Composio tool)
6. Updates Notion: Status → "Posted", Post URL field populated
7. Logs to ontology: LinkedInPost entity created/updated

**Dependencies:**
- Notion API (NOTION_API_KEY)
- Composio LinkedIn (LINKEDIN_ACCOUNT_URN)
- Images hosted on GitHub raw URL (or Notion blocks)

**Failure Modes:**
- **Notion 500 error:** Retry next run (AMBER)
- **Image 404:** Skip image, post text-only, flag in Notion (AMBER)
- **Composio timeout:** Retry next run (AMBER)
- **No posts scheduled:** Log as success (GREEN, empty result)

**Manual Test:**
```bash
python3 /root/.openclaw/workspace/scripts/linkedin-auto-poster.py --dry-run
# Prints posts that would be posted, no actual posting
```

**Last Run Status:**
Check: `tail -20 ~/.openclaw/logs/linkedin-auto-poster.log`

**Notion Content Calendar DB:**
- ID: `3268d599-a162-814b-8854-c9b8bde62468`
- Properties: Title, Hook, Status (Posted/Drafted/Scheduled), Planned Date, Draft, Post URL, Topic, Day

---

### 3. briefing-agent.py

**Purpose:** Compile morning briefing for CEO (emails, jobs, calendar, LinkedIn trends)

**Script Location:** `/root/.openclaw/workspace/scripts/briefing-agent.py`

**Cron Schedule:** `0 6 * * *` (06:00 Cairo, daily)

**What It Does:**
1. Fetches unread emails (Gmail via himalaya)
2. Fetches open job applications (ontology graph)
3. Scores jobs by urgency/fit (jobs-review.py subprocess)
4. Fetches calendar events (next 12 hours)
5. Checks Ahmed's LinkedIn notifications (Composio or browser)
6. Compiles into formatted briefing
7. Posts to Telegram topic 1 (CEO Desk)
8. Sends summary to CEO email (optional)

**Dependencies:**
- Gmail (himalaya, IMAP access)
- Notion job pipeline (via ontology)
- Google Calendar (optional)
- LinkedIn (optional)

**Failure Modes:**
- **Gmail timeout:** Skip emails section, continue with jobs (AMBER)
- **Jobs query fails:** Skip jobs, continue with other sections (AMBER)
- **Telegram post fails:** Log error, retry in 5 min (AMBER)
- **Empty briefing:** Still post ("No updates"), don't skip (GREEN)

**Manual Test:**
```bash
python3 /root/.openclaw/workspace/scripts/briefing-agent.py --dry-run
# Prints briefing to console, no Telegram send
```

**Last Run Status:**
Check: `tail -20 ~/.openclaw/logs/briefing-agent.log`

**Critical Dependency:**
- If briefing fails, CEO doesn't get morning context
- Severity: RED if fails 2+ days in a row
- Escalate after first failure if it's not recoverable in 10 min

---

### 4. notion-pipeline-sync.py

**Purpose:** Keep job pipeline in sync between Notion and ontology graph (single source of truth)

**Script Location:** `/root/.openclaw/workspace/scripts/notion-pipeline-sync.py`

**Cron Schedule:** `0 * * * *` (every hour, on the hour)

**What It Does:**
1. Reads Notion job pipeline DB
2. Upserts each job to ontology graph (JobApplication entity)
3. Detects new applications → creates entities
4. Detects status changes → updates entities
5. Runs application-lock check (prevent duplicates)
6. Logs sync results to cron dashboard
7. Updates coordination/pipeline.json (export for dashboards)

**Dependencies:**
- Notion API (NOTION_API_KEY)
- Ontology graph (memory/ontology/graph.jsonl)
- Git (for commits, if auto-commit enabled)

**Failure Modes:**
- **Notion 500 error:** Retry next hour (AMBER)
- **Graph write fails:** Partial sync, log error (AMBER)
- **Duplicate detected:** Log warning, application-lock prevents it (GREEN)
- **Empty pipeline:** Still complete sync (GREEN)

**Manual Test:**
```bash
python3 /root/.openclaw/workspace/scripts/notion-pipeline-sync.py --dry-run
# Prints what would be synced, no actual changes
```

**Last Run Status:**
Check: `tail -20 ~/.openclaw/logs/notion-pipeline-sync.log`

**Related: application-lock.py**
- Integrated into pipeline-sync (run together)
- Detects if same job was applied to twice
- Prevents accidental duplicate applications
- Flags suspicious patterns (e.g., same company, different roles)

---

### 5. jobs-review.py

**Purpose:** Score job opportunities by fit, urgency, salary alignment

**Script Location:** `/root/.openclaw/workspace/scripts/jobs-review.py`

**Trigger:** Called by briefing-agent.py (not standalone cron)

**What It Does:**
1. Reads all open JobApplication entities (ontology)
2. Scores each by:
   - ATS fit (resume → JD alignment)
   - Title/level match (VP/C-Suite target)
   - Salary range (vs. Ahmed's expectations)
   - Interview stage (screening/phone/final)
   - Days since applied (urgency)
3. Updates ontology: JobApplication.score field
4. Returns ranked list (highest score first)
5. Feeds into briefing summary

**Dependencies:**
- Ontology graph (read/write)
- ATS guide (memory/ats-best-practices.md)

**Failure Modes:**
- **Ontology query fails:** Log error, use cached scores (AMBER)
- **Scoring error:** Skip affected job, continue (AMBER)
- **No open jobs:** Return empty list, no error (GREEN)

**Manual Test:**
```bash
python3 /root/.openclaw/workspace/scripts/jobs-review.py --dry-run
# Prints scored jobs, no updates
```

---

### 6. cron-dashboard-updater.py

**Purpose:** Monitor all cron jobs, log health, detect failures

**Script Location:** `/root/.openclaw/workspace/scripts/cron-dashboard-updater.py`

**Cron Schedule:** `0 * * * *` (every hour, on the hour)

**What It Does:**
1. Reads all log files in `~/.openclaw/logs/`
2. Checks last run time for each agent
3. Detects failures (error patterns in logs)
4. Updates Notion cron health DB (3268d599-a162-8188-b531-e25071653203)
5. Marks RED/AMBER issues
6. Posts summary to topic 8 (if issues found)

**Dependencies:**
- Notion API (NOTION_API_KEY)
- Log files exist

**Failure Modes:**
- **Notion update fails:** Retry next hour (AMBER)
- **Log parsing error:** Skip affected agent, continue (AMBER)
- **Telegram post fails:** Notification skipped, data still updated (GREEN)

**Manual Test:**
```bash
python3 /root/.openclaw/workspace/scripts/cron-dashboard-updater.py --dry-run
# Prints dashboard summary, no Notion update
```

**Last Run Status:**
Check: `tail -20 ~/.openclaw/logs/cron-dashboard-updater.log`

**Notion Cron Dashboard DB:**
- ID: `3268d599-a162-8188-b531-e25071653203`
- Properties: Agent Name, Last Run, Status (OK/FAILED), Error Message, Severity (RED/AMBER/GREEN)

---

### 7. email-agent.py

**Purpose:** Monitor Gmail for urgent messages, flag critical emails

**Script Location:** `/root/.openclaw/workspace/scripts/email-agent.py`

**Cron Schedule:** `0 8 * * *` (08:00 Cairo, daily)

**What It Does:**
1. Connects to Gmail (himalaya IMAP)
2. Fetches unread emails
3. Marks "urgent" by sender/subject patterns
4. Posts urgent emails to Telegram topic 1 (CEO Desk)
5. Logs activity

**Dependencies:**
- Gmail (himalaya, IMAP access)
- Telegram bot

**Failure Modes:**
- **Gmail timeout:** Skip, don't error (GREEN)
- **Telegram post fails:** Log, retry next run (AMBER)
- **No new emails:** Log as success (GREEN)

**Manual Test:**
```bash
python3 /root/.openclaw/workspace/scripts/email-agent.py --dry-run
# Prints urgent emails found, no Telegram send
```

---

## Agent Health Status

### Quick Health Check (Daily Standup)
```bash
python3 /root/.openclaw/workspace/scripts/cron-dashboard-updater.py --dry-run
```

This outputs:
- Last run time for each agent
- Pass/fail status
- Any RED or AMBER issues

### Detailed Agent Logs
```bash
# LinkedIn engagement
tail -20 ~/.openclaw/logs/linkedin-engagement.log

# LinkedIn poster
tail -20 ~/.openclaw/logs/linkedin-auto-poster.log

# Briefing
tail -20 ~/.openclaw/logs/briefing-agent.log

# Pipeline sync
tail -20 ~/.openclaw/logs/notion-pipeline-sync.log

# Cron dashboard
tail -20 ~/.openclaw/logs/cron-dashboard-updater.log

# Email agent
tail -20 ~/.openclaw/logs/email-agent.log
```

### Search for Errors
```bash
# All errors in last 100 lines of all logs
grep -i "error\|failed\|exception" ~/.openclaw/logs/*.log | tail -20
```

---

## Manual Agent Run (Testing)

**All agents support `--dry-run` flag:**

```bash
# Test without side effects
python3 /root/.openclaw/workspace/scripts/[agent-name].py --dry-run

# Actual run (does posting/updates)
python3 /root/.openclaw/workspace/scripts/[agent-name].py
```

---

## Dependencies Matrix

| Agent | Gmail | Notion | Composio | Ontology | LinkedIn | Telegram | GitHub |
|-------|-------|--------|----------|----------|----------|----------|--------|
| engagement | ❌ | ✅ | ✅ (Exa) | ✅ | ✅ (Chrome) | ✅ | ❌ |
| auto-poster | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| briefing | ✅ | ✅ | ❌ | ✅ | ✅ (opt) | ✅ | ❌ |
| pipeline-sync | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| jobs-review | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| dashboard | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| email | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

---

## Troubleshooting Quick Links

- Agent hangs or timeout? Check gateway (instructions/gateway.md)
- Notion errors? Check credentials, API key renewal
- Telegram not posting? Check bot token, chat ID
- LinkedIn posting failing? Check Composio account, image URLs
- Ontology query fails? Check graph.jsonl syntax, file permissions
