# Weekly Team Retro (Cron)

Generates a structured performance review of all pipeline agents.

## Schedule
- **Frequency:** Weekly, Sundays at 10:00 AM Cairo
- **Cron:** `0 10 * * 0`

## What It Does
1. Pulls run history from `data/run-history.jsonl` (last 7 days)
2. Pulls heartbeat status from `data/heartbeat.json`
3. Pulls agent feedback from `data/agent-feedback/`
4. Pulls lessons learned from `memory/lessons-learned.md`
5. Generates structured markdown report with:
   - Summary stats (runs, success rate)
   - Per-agent breakdown (runs, success rate, avg duration, avg records)
   - Top performers (most reliable, fastest, most productive)
   - Failure patterns
   - Lessons learned
   - Growth areas
   - Recommendations

## Output
- File: `memory/retros/YYYY-MM-DD-weekly-retro.md`
- Also sent as digest to Telegram (optional)

## Steps

### Step 1: Run Script
```bash
python3 scripts/weekly-team-retro.py
```

### Step 2: Review Output
The script generates `memory/retros/YYYY-MM-DD-weekly-retro.md` containing:
- Summary stats (runs, success rate)
- Per-agent breakdown (runs, success rate, avg duration, avg records)
- Top performers (most reliable, fastest, most productive)
- Failure patterns
- Lessons learned
- Growth areas
- Recommendations

Review the output for any urgent action items or patterns needing human attention.

### Step 3: Send Digest
Send a summary digest to Telegram with:
- Key metrics (total runs, overall success rate)
- Top 2-3 findings or recommendations
- Any agents with critical failure rates needing attention

## Manual Run
```bash
# Preview without saving
python3 scripts/weekly-team-retro.py --dry-run

# Different time window
python3 scripts/weekly-team-retro.py --days 14

# Custom output path
python3 scripts/weekly-team-retro.py --output /tmp/retro.md
```

## Dependencies
- `data/run-history.jsonl` (populated by pipeline runs)
- `data/heartbeat.json` (populated by heartbeat tracker)
- `memory/lessons-learned.md` (populated by auto-lessons or manual)

## Error Handling
- If run-history.jsonl missing: report "No run history - skipping retro"
- If script fails: report error, save partial output if available
- If no data for the week: generate "quiet week" stub report

## Quality Gates
- Report covers full 7-day window
- Per-agent breakdown included for all active agents
- File saved to memory/retros/ with correct date
- Recommendations section always present (even if "no changes needed")
