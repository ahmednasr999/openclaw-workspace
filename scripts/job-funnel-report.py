#!/usr/bin/env python3
"""
job-funnel-report.py - Weekly pipeline funnel analysis.

Tracks: discovered -> scored -> applied -> responded -> interviewed
Breaks down by: source method, title group, country, ATS score band.
Identifies: stale applications (14+ days, no response).

Run: python3 scripts/job-funnel-report.py
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path("/root/.openclaw/workspace/data/nasr-pipeline.db")
REPORT_DIR = Path("/root/.openclaw/workspace/data/funnel-reports")


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def generate_report():
    conn = get_db()
    date_str = datetime.now().strftime("%Y-%m-%d")
    stale_cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

    report = {"date": date_str, "sections": {}}

    # 1. Overall funnel
    rows = conn.execute("SELECT status, COUNT(*) as cnt FROM jobs GROUP BY status ORDER BY cnt DESC").fetchall()
    funnel = {r["status"]: r["cnt"] for r in rows}
    report["sections"]["funnel"] = funnel

    applied = funnel.get("applied", 0)
    responded = funnel.get("response", 0)
    report["sections"]["response_rate"] = f"{responded}/{applied} ({responded/applied*100:.1f}%)" if applied > 0 else "N/A"

    # 2. By source method
    rows = conn.execute("""
        SELECT source_method, status, COUNT(*) as cnt 
        FROM jobs WHERE source_method IS NOT NULL AND source_method != ''
        GROUP BY source_method, status
    """).fetchall()
    by_source = {}
    for r in rows:
        by_source.setdefault(r["source_method"], {})[r["status"]] = r["cnt"]
    report["sections"]["by_source"] = by_source

    # 3. By country
    rows = conn.execute("""
        SELECT country, status, COUNT(*) as cnt
        FROM jobs WHERE country IS NOT NULL AND country != ''
        GROUP BY country, status
    """).fetchall()
    by_country = {}
    for r in rows:
        by_country.setdefault(r["country"], {})[r["status"]] = r["cnt"]
    report["sections"]["by_country"] = by_country

    # 4. ATS score bands for applied jobs
    rows = conn.execute("""
        SELECT 
            CASE 
                WHEN ats_score >= 80 THEN '80-100'
                WHEN ats_score >= 60 THEN '60-79'
                WHEN ats_score >= 40 THEN '40-59'
                ELSE '0-39'
            END as band,
            status, COUNT(*) as cnt
        FROM jobs WHERE ats_score IS NOT NULL
        GROUP BY band, status
    """).fetchall()
    by_ats = {}
    for r in rows:
        by_ats.setdefault(r["band"], {})[r["status"]] = r["cnt"]
    report["sections"]["by_ats_band"] = by_ats

    # 5. Stale applications (14+ days, no response)
    stale = conn.execute("""
        SELECT title, company, location, applied_date, job_url
        FROM jobs 
        WHERE status = 'applied' AND applied_date IS NOT NULL AND applied_date < ?
        ORDER BY applied_date ASC
    """, (stale_cutoff,)).fetchall()
    report["sections"]["stale_applications"] = {
        "count": len(stale),
        "cutoff_days": 14,
        "jobs": [dict(r) for r in stale[:20]],  # top 20
    }

    # 6. Time-to-apply (days from discovery to application)
    rows = conn.execute("""
        SELECT 
            julianday(applied_date) - julianday(created_at) as days_to_apply
        FROM jobs 
        WHERE status IN ('applied', 'cv_built', 'response') 
        AND applied_date IS NOT NULL AND created_at IS NOT NULL
    """).fetchall()
    days = [r["days_to_apply"] for r in rows if r["days_to_apply"] is not None and r["days_to_apply"] >= 0]
    if days:
        report["sections"]["time_to_apply"] = {
            "avg_days": round(sum(days) / len(days), 1),
            "median_days": round(sorted(days)[len(days)//2], 1),
            "min_days": round(min(days), 1),
            "max_days": round(max(days), 1),
            "sample_size": len(days),
        }
    else:
        report["sections"]["time_to_apply"] = {"note": "No data"}

    # 7. Weekly discovery trend (last 4 weeks)
    weeks = []
    for i in range(4):
        week_end = datetime.now() - timedelta(weeks=i)
        week_start = week_end - timedelta(weeks=1)
        row = conn.execute("""
            SELECT COUNT(*) as cnt FROM jobs 
            WHERE created_at >= ? AND created_at < ?
        """, (week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d"))).fetchone()
        weeks.append({"week": f"W-{i}", "discovered": row["cnt"]})
    report["sections"]["weekly_trend"] = weeks

    conn.close()

    # Save report
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORT_DIR / f"funnel-{date_str}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Print summary
    print(f"Job Pipeline Funnel Report - {date_str}")
    print(f"{'='*50}")
    print(f"\nOverall Funnel:")
    for status, count in sorted(funnel.items(), key=lambda x: -x[1]):
        print(f"  {status}: {count}")
    print(f"\nResponse Rate: {report['sections']['response_rate']}")
    
    if report["sections"].get("time_to_apply", {}).get("avg_days"):
        tta = report["sections"]["time_to_apply"]
        print(f"\nTime to Apply: avg {tta['avg_days']}d, median {tta['median_days']}d (n={tta['sample_size']})")

    stale_count = report["sections"]["stale_applications"]["count"]
    if stale_count:
        print(f"\nStale Applications (14+ days, no response): {stale_count}")
        for j in report["sections"]["stale_applications"]["jobs"][:5]:
            print(f"  - {j['title']} @ {j['company']} (applied {j['applied_date']})")

    print(f"\nWeekly Discovery Trend:")
    for w in report["sections"]["weekly_trend"]:
        bar = "#" * (w["discovered"] // 5)
        print(f"  {w['week']}: {w['discovered']:3d} {bar}")

    print(f"\nReport saved: {report_file}")
    return report


if __name__ == "__main__":
    generate_report()
