#!/usr/bin/env python3
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path('/root/.openclaw/workspace/data/nasr-pipeline.db')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# last 24h verdict mix
v24 = {r['verdict'] or 'NULL': r['n'] for r in cur.execute("""
SELECT verdict, count(*) n
FROM jobs
WHERE datetime(created_at) >= datetime('now','-1 day')
GROUP BY verdict
""")}

# 7d source quality
source_rows = list(cur.execute("""
WITH recent AS (
  SELECT source, verdict, ats_score, fit_score,
         CASE WHEN jd_text IS NOT NULL AND length(jd_text) > 100 THEN 1 ELSE 0 END as has_jd
  FROM jobs
  WHERE datetime(created_at) >= datetime('now','-7 days')
)
SELECT source,
       count(*) as total,
       sum(CASE WHEN verdict IN ('REVIEW','SUBMIT') THEN 1 ELSE 0 END) as relevant,
       sum(CASE WHEN verdict='SUBMIT' THEN 1 ELSE 0 END) as submit,
       round(100.0 * sum(CASE WHEN verdict IN ('REVIEW','SUBMIT') THEN 1 ELSE 0 END) / count(*), 1) as relevance_rate,
       round(avg(CASE WHEN verdict IN ('REVIEW','SUBMIT') THEN ats_score END),1) as avg_ats_rel,
       round(avg(CASE WHEN verdict IN ('REVIEW','SUBMIT') THEN fit_score END),1) as avg_fit_rel,
       sum(has_jd) as jd_ready,
       round(100.0 * sum(has_jd) / count(*), 1) as jd_ready_pct
FROM recent
GROUP BY source
ORDER BY total DESC
"""))

# 7d source run efficiency
run_rows = list(cur.execute("""
SELECT source,
       count(*) as runs,
       sum(raw_count) as raw_total,
       sum(unique_count) as unique_total,
       sum(db_registered) as registered_total,
       sum(errors) as errors_total,
       round(1.0 * sum(db_registered) / NULLIF(sum(raw_count),0), 4) as registered_per_raw,
       round(1.0 * sum(errors) / NULLIF(sum(raw_count),0), 4) as errors_per_raw
FROM source_runs
WHERE run_date >= date('now','-7 days')
GROUP BY source
ORDER BY raw_total DESC
"""))

# 7d review burden snapshot
review7 = cur.execute("SELECT count(*) n FROM jobs WHERE datetime(created_at) >= datetime('now','-7 days') AND verdict='REVIEW'").fetchone()['n']
submit7 = cur.execute("SELECT count(*) n FROM jobs WHERE datetime(created_at) >= datetime('now','-7 days') AND verdict='SUBMIT'").fetchone()['n']
skip7 = cur.execute("SELECT count(*) n FROM jobs WHERE datetime(created_at) >= datetime('now','-7 days') AND verdict='SKIP'").fetchone()['n']

def fmt(v):
    return '-' if v is None else str(v)

lines = []
lines.append(f"📈 SAYYAD Performance Watch — {datetime.now().strftime('%d %b %Y %H:%M Cairo')}")
lines.append("━━━━━━━━━━━━━━━━━━━━")
lines.append("24h verdict mix")
lines.append(f"- SUBMIT: {v24.get('SUBMIT', 0)}")
lines.append(f"- REVIEW: {v24.get('REVIEW', 0)}")
lines.append(f"- SKIP: {v24.get('SKIP', 0)}")
lines.append("")
lines.append("7d pipeline mix")
lines.append(f"- SUBMIT: {submit7}")
lines.append(f"- REVIEW: {review7}")
lines.append(f"- SKIP: {skip7}")
lines.append("")
lines.append("7d source quality")
for r in source_rows:
    lines.append(f"- {r['source']}: total {r['total']}, relevant {r['relevant']}, submit {r['submit']}, relevance {fmt(r['relevance_rate'])}%, avg ATS {fmt(r['avg_ats_rel'])}, avg fit {fmt(r['avg_fit_rel'])}, JD {fmt(r['jd_ready_pct'])}%")
lines.append("")
lines.append("7d source efficiency")
for r in run_rows:
    lines.append(f"- {r['source']}: runs {r['runs']}, raw {fmt(r['raw_total'])}, unique {fmt(r['unique_total'])}, registered {fmt(r['registered_total'])}, errors {fmt(r['errors_total'])}, reg/raw {fmt(r['registered_per_raw'])}, err/raw {fmt(r['errors_per_raw'])}")
lines.append("")
lines.append("Signals")
if source_rows:
    best = max(source_rows, key=lambda x: (x['relevance_rate'] or 0, x['submit'] or 0))
    worst = max(run_rows, key=lambda x: (x['errors_per_raw'] or 0)) if run_rows else None
    lines.append(f"- Best quality source now: {best['source']} ({fmt(best['relevance_rate'])}% relevance)")
    if worst:
        lines.append(f"- Noisiest source now: {worst['source']} (err/raw {fmt(worst['errors_per_raw'])})")
    lines.append(f"- Review burden target: keep 7d REVIEW at or below 5, current {review7}")

print('\n'.join(lines))
conn.close()
