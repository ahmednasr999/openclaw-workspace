#!/usr/bin/env python3
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB = Path('/root/.openclaw/workspace/data/nasr-pipeline.db')
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

alerts = []

# 1) 7d REVIEW burden too high
review7 = cur.execute("SELECT count(*) n FROM jobs WHERE datetime(created_at) >= datetime('now','-7 days') AND verdict='REVIEW'").fetchone()['n']
if review7 > 8:
    alerts.append(f"7d REVIEW burden high: {review7} > 8")

# 2) No SUBMITs for 3 consecutive days
rows = list(cur.execute("""
SELECT date(created_at) d, sum(CASE WHEN verdict='SUBMIT' THEN 1 ELSE 0 END) as submits
FROM jobs
WHERE datetime(created_at) >= datetime('now','-3 days')
GROUP BY date(created_at)
ORDER BY d DESC
LIMIT 3
"""))
if len(rows) == 3 and all((r['submits'] or 0) == 0 for r in rows):
    alerts.append("0 SUBMITs for 3 consecutive days")

# 3) Indeed error rate too high in last 7d
indeed = cur.execute("""
SELECT round(1.0 * sum(errors) / NULLIF(sum(raw_count),0), 4) as err_per_raw,
       sum(errors) as errs, sum(raw_count) as raw_total
FROM source_runs
WHERE run_date >= date('now','-7 days') AND source='indeed'
""").fetchone()
err_per_raw = indeed['err_per_raw'] if indeed and indeed['err_per_raw'] is not None else 0
if err_per_raw > 0.30:
    alerts.append(f"Indeed error rate high: err/raw {err_per_raw:.4f} > 0.30")

if alerts:
    print("🚨 SAYYAD Fail Alert")
    print("━━━━━━━━━━━━━━━━━━━━")
    for a in alerts:
        print(f"- {a}")
    print(f"- review7={review7}")
    print(f"- indeed_err_per_raw={err_per_raw:.4f}")
else:
    print("SAYYAD_FAIL_ALERT_OK")

conn.close()
