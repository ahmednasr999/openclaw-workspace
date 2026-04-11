#!/usr/bin/env python3
import re
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path('/root/.openclaw/workspace/data/nasr-pipeline.db')
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

apps = list(cur.execute("""
SELECT source, verdict, score_notes, coalesce(application_date, applied_date) as app_date,
       callback_received, interview_stage
FROM jobs
WHERE date(coalesce(application_date, applied_date)) >= date('now','-7 days')
  AND coalesce(application_date, applied_date) IS NOT NULL
"""))

app_count = len(apps)
callbacks = [r for r in apps if (r['callback_received'] or 0) == 1 or (r['interview_stage'] not in (None, '', 'none'))]
callback_count = len(callbacks)
callback_rate = round(100.0 * callback_count / app_count, 1) if app_count else 0.0

source_stats = {}
verdict_stats = {}
dim_stats = {k: {'apps': 0, 'callbacks': 0} for k in ['role','seniority','geo','strategic','evidence']}
for r in apps:
    source = r['source'] or 'unknown'
    verdict = r['verdict'] or 'unknown'
    source_stats.setdefault(source, {'apps': 0, 'callbacks': 0})
    verdict_stats.setdefault(verdict, {'apps': 0, 'callbacks': 0})
    source_stats[source]['apps'] += 1
    verdict_stats[verdict]['apps'] += 1
    got_callback = r in callbacks
    if got_callback:
        source_stats[source]['callbacks'] += 1
        verdict_stats[verdict]['callbacks'] += 1

    notes = r['score_notes'] or ''
    for key in dim_stats:
        m = re.search(rf"{key}=([0-2])", notes)
        if m:
            dim_stats[key]['apps'] += int(m.group(1))
            if got_callback:
                dim_stats[key]['callbacks'] += int(m.group(1))

lines = []
lines.append(f"📊 SAYYAD Weekly Conversion Report — {datetime.now().strftime('%d %b %Y')}")
lines.append("━━━━━━━━━━━━━━━━━━━━")
lines.append(f"- Applications sent (7d): {app_count}")
lines.append(f"- Callback/interview count: {callback_count}")
lines.append(f"- Callback rate: {callback_rate}%")
lines.append("")
lines.append("Callbacks by source")
if source_stats:
    for source, s in sorted(source_stats.items(), key=lambda x: (-x[1]['callbacks'], -x[1]['apps'])):
        rate = round(100.0 * s['callbacks'] / s['apps'], 1) if s['apps'] else 0.0
        lines.append(f"- {source}: {s['callbacks']}/{s['apps']} ({rate}%)")
else:
    lines.append("- No applications in the last 7 days")
lines.append("")
lines.append("Callbacks by verdict at application time")
for verdict, s in sorted(verdict_stats.items(), key=lambda x: (-x[1]['callbacks'], -x[1]['apps'])):
    rate = round(100.0 * s['callbacks'] / s['apps'], 1) if s['apps'] else 0.0
    lines.append(f"- {verdict}: {s['callbacks']}/{s['apps']} ({rate}%)")
lines.append("")
lines.append("Scoring dimensions that predicted callbacks best")
ranked = []
for key, s in dim_stats.items():
    avg_app = round(s['apps'] / app_count, 2) if app_count else 0.0
    avg_cb = round(s['callbacks'] / callback_count, 2) if callback_count else 0.0
    lift = round(avg_cb - avg_app, 2)
    ranked.append((lift, key, avg_app, avg_cb))
for lift, key, avg_app, avg_cb in sorted(ranked, reverse=True):
    lines.append(f"- {key}: avg app score {avg_app}, avg callback score {avg_cb}, lift {lift:+.2f}")

print('\n'.join(lines))
conn.close()
