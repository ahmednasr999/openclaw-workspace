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

## Script
```bash
python3 scripts/weekly-team-retro.py
```

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
