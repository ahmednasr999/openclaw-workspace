#!/bin/bash
# SAYYAD Source Pipeline — Phase A
# Runs all sources → merge/dedup → JD fetch → wake HR agent
# Cron: 03:00, 04:00, 08:00, 12:00 Cairo daily
#
# Option B: LinkedIn runs fire-and-forget (takes ~15 min).
# Each run picks up the previous run's linkedin.json during merge.
# Google + Indeed are fast (~2-3 min) and waited on.
#
# This script does ALL plumbing (no LLM). HR Agent does ALL thinking.

set -euo pipefail
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="/var/log/sayyad"
mkdir -p "$LOG_DIR"
DATE=$(date +%Y-%m-%d)
LOG="$LOG_DIR/$DATE-source.log"

log() { echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"; }

log "=== SAYYAD Source Pipeline started ==="

# Clear stale bytecode cache to prevent signature mismatch crashes
find "$SCRIPTS_DIR/__pycache__" -name "*.pyc" -delete 2>/dev/null || true

# Phase A1: Run sources
log "Phase A1: Sourcing"

# LinkedIn: fire-and-forget (takes ~15 min, don't block merge)
python3 "$SCRIPTS_DIR/jobs-source-linkedin-jobspy.py" >> "$LOG" 2>&1 &
PID_LI=$!
log "  LinkedIn: started (PID $PID_LI, fire-and-forget)"

# Google + Indeed: fast, wait for them
python3 "$SCRIPTS_DIR/jobs-source-indeed.py" >> "$LOG" 2>&1 &
PID_IN=$!
python3 "$SCRIPTS_DIR/jobs-source-google.py" >> "$LOG" 2>&1 &
PID_GO=$!

# Wait for Google + Indeed only
wait $PID_IN && log "  Indeed: done ✅" || log "  Indeed: FAILED ❌"
wait $PID_GO && log "  Google/Exa: done ✅" || log "  Google/Exa: FAILED ❌"

# Phase A2: Merge (dedup within SQLite)
# This picks up the PREVIOUS run's linkedin.json (from 1-2 cycles ago)
# while Google/Indeed results are fresh from this run.
log "Phase A2: Merge & dedup"
python3 "$SCRIPTS_DIR/jobs-merge.py" >> "$LOG" 2>&1 || log "  Merge: FAILED ❌"

# Phase A3: Fetch missing JDs (fire-and-forget — takes too long for pipeline timeout)
log "Phase A3: JD enrichment (background)"
python3 "$SCRIPTS_DIR/jobs-enrich-jd.py" >> "$LOG" 2>&1 &
log "  JD enrich: started (background)"

# Phase A3.5: Check if the previous run's JD enrich is still running
PREV_PID=$(pgrep -f "jobs-enrich-jd.py" 2>/dev/null | grep -v $$ | head -1)
if [ -n "$PREV_PID" ]; then
  log "  Previous JD enrich still running (PID $PREV_PID) — OK, next run will pick it up"
fi

# Phase A4: Build source report from source_runs table
log "Phase A4: Source report"
REPORT=$(python3 -c "
import sqlite3, json
db = sqlite3.connect('$SCRIPTS_DIR/../data/nasr-pipeline.db')
db.row_factory = sqlite3.Row

# Today's source runs
runs = db.execute('''
    SELECT source, raw_count, unique_count, db_registered, countries_json, titles_json, errors
    FROM source_runs WHERE run_date = date('now') ORDER BY created_at DESC
''').fetchall()

# Today's fresh unscored jobs
fresh = db.execute('''
    SELECT COUNT(*) FROM jobs WHERE verdict IS NULL
    AND date(created_at) = date('now')
''').fetchone()[0]

# Total unscored
total_unscored = db.execute('SELECT COUNT(*) FROM jobs WHERE verdict IS NULL').fetchone()[0]

# JD coverage for today's fresh
jd_ready = db.execute('''
    SELECT COUNT(*) FROM jobs WHERE verdict IS NULL
    AND date(created_at) = date('now') AND jd_text IS NOT NULL
''').fetchone()[0]

name_map = {
    'linkedin_jobspy': 'LinkedIn',
    'linkedin':       'LinkedIn',
    'google':          'Google Jobs',
    'indeed':          'Indeed',
    'manual':          'Manual',
}

lines = ['📊 SAYYAD Source Report — $(date \"+%d %b %Y\")', '━' * 36]
total_raw = 0
total_unique = 0
all_countries = {}
all_titles = {}

for r in runs:
    src = name_map.get(r['source'], r['source'].replace('_', ' ').title())
    lines.append(f\"{src}: {r['unique_count']} jobs ({r['raw_count']} raw, {r['errors']} errors)\")
    total_raw += r['raw_count']
    total_unique += r['unique_count']
    if r['countries_json']:
        for k, v in json.loads(r['countries_json']).items():
            all_countries[k] = all_countries.get(k, 0) + v
    if r['titles_json']:
        for k, v in json.loads(r['titles_json']).items():
            all_titles[k] = all_titles.get(k, 0) + v

lines.append('━' * 36)
lines.append(f'Total new today: {fresh} (after dedup)')
lines.append(f'Total unscored in DB: {total_unscored}')

if all_countries:
    top_c = sorted(all_countries.items(), key=lambda x: -x[1])[:6]
    lines.append(f\"Countries: {', '.join(f'{k} {v}' for k, v in top_c)}\")

if all_titles:
    top_t = sorted(all_titles.items(), key=lambda x: -x[1])[:5]
    lines.append(f\"Top titles: {', '.join(f'{k} ({v})' for k, v in top_t)}\")

lines.append(f'JDs ready: {jd_ready}/{fresh} ({round(100*jd_ready/max(1,fresh))}%)')
lines.append('━' * 36)
lines.append('Ready for scoring ✅')
print('\n'.join(lines))
db.close()
" 2>&1)

log "$REPORT"

# Save report for HR agent to read
echo "$REPORT" > "$LOG_DIR/$DATE-source-report.txt"

log "=== SAYYAD Source Pipeline complete. Waking HR Agent ==="
