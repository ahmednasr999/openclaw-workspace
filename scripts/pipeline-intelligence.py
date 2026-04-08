#!/usr/bin/env python3
"""
pipeline-intelligence.py - Single intelligence engine for the job pipeline.

Reads from pipeline_db (single source of truth) and produces:
- Health metrics (response rate, velocity, stale count, weekly trend)
- Top prospects (ranked by recency + stage + ATS score)
- Recommendations (which sources convert, which titles get responses)
- Alerts (stale follow-ups, stage transitions, recruiter gaps)

Output: data/pipeline-intelligence.json + human-readable Telegram summary

All consumers read from this output instead of querying separately.

Usage:
    python3 pipeline-intelligence.py                # Full report
    python3 pipeline-intelligence.py --telegram     # Just Telegram summary
    python3 pipeline-intelligence.py --json         # Just JSON output
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
OUTPUT_PATH = DATA_DIR / "pipeline-intelligence.json"
CAIRO = timezone(timedelta(hours=2))

sys.path.insert(0, str(WORKSPACE / "scripts"))
try:
    import pipeline_db as pdb
except ImportError:
    print("ERROR: pipeline_db not importable")
    sys.exit(1)


def now_cairo():
    return datetime.now(CAIRO)


def generate_report():
    """Generate the full intelligence report."""
    now = now_cairo()
    report = {
        "generated_at": now.isoformat(),
        "health": {},
        "funnel": {},
        "prospects": [],
        "transitions": [],
        "alerts": [],
        "recommendations": [],
        "velocity": {},
    }

    # ── Funnel ───────────────────────────────────────────────────────────
    funnel = pdb.get_funnel()
    total = funnel.pop("_total", 0)
    report["funnel"] = {
        "total": total,
        "by_status": funnel,
    }

    applied = funnel.get("applied", 0)
    responded = funnel.get("response", 0)
    interviewed = funnel.get("interview", 0)
    offered = funnel.get("offer", 0)

    response_rate = (responded / applied * 100) if applied > 0 else 0
    interview_rate = (interviewed / max(responded, 1) * 100) if responded > 0 else 0

    report["health"] = {
        "total_tracked": total,
        "active_applications": applied + responded + interviewed + offered,
        "response_rate_pct": round(response_rate, 1),
        "interview_rate_pct": round(interview_rate, 1),
        "benchmark_response_rate": 5.0,  # Industry benchmark
        "below_benchmark": response_rate < 5.0,
    }

    # ── Stale applications ───────────────────────────────────────────────
    stale = pdb.get_stale(days=14)
    report["health"]["stale_count"] = len(stale)
    report["alerts"].extend([
        {
            "type": "stale",
            "company": s.get("company", "?"),
            "title": s.get("title", "?"),
            "days": (now.replace(tzinfo=None) - datetime.fromisoformat(
                s.get("applied_date", now.isoformat())[:19]
            )).days if s.get("applied_date") else 0,
            "action": "Follow up or withdraw",
        }
        for s in stale[:10]
    ])

    # ── Recent transitions ───────────────────────────────────────────────
    transitions = pdb.get_recent_transitions(days=7)
    report["transitions"] = [
        {
            "company": t.get("company", "?"),
            "title": t.get("title", "?"),
            "from": t.get("from_status", "?"),
            "to": t.get("to_status", "?"),
            "date": t.get("changed_at", "?"),
        }
        for t in transitions[:20]
    ]

    # Alert on high-value transitions
    for t in transitions:
        if t.get("to_status") in ("interview", "offer"):
            report["alerts"].append({
                "type": "transition",
                "company": t.get("company", "?"),
                "title": t.get("title", "?"),
                "to": t.get("to_status"),
                "date": t.get("changed_at", "?"),
                "action": f"Prepare for {t.get('to_status')}",
            })

    # ── Top prospects ────────────────────────────────────────────────────
    try:
        conn = pdb._get_conn()
        rows = conn.execute("""
            SELECT * FROM jobs
            WHERE status IN ('applied', 'response', 'interview', 'offer', 'cv_built')
            ORDER BY
                CASE status
                    WHEN 'offer' THEN 1
                    WHEN 'interview' THEN 2
                    WHEN 'response' THEN 3
                    WHEN 'applied' THEN 4
                    WHEN 'cv_built' THEN 5
                    ELSE 6
                END,
                COALESCE(ats_score, 0) DESC,
                updated_at DESC
            LIMIT 10
        """).fetchall()
        conn.close()
        report["prospects"] = [
            {
                "company": r["company"],
                "title": r["title"],
                "status": r["status"],
                "ats_score": r["ats_score"],
                "applied_date": r["applied_date"],
                "location": r["location"],
            }
            for r in rows
        ]
    except Exception:
        pass

    # ── Source analysis ───────────────────────────────────────────────────
    try:
        conn = pdb._get_conn()
        source_rows = conn.execute("""
            SELECT source, status, COUNT(*) as cnt FROM jobs
            WHERE source IS NOT NULL
            GROUP BY source, status
        """).fetchall()
        conn.close()

        source_stats = defaultdict(lambda: defaultdict(int))
        for r in source_rows:
            source_stats[r["source"]][r["status"]] = r["cnt"]

        best_source = None
        best_rate = 0
        for src, stats in source_stats.items():
            src_applied = stats.get("applied", 0)
            src_response = stats.get("response", 0) + stats.get("interview", 0)
            if src_applied >= 5:
                rate = src_response / src_applied * 100
                if rate > best_rate:
                    best_rate = rate
                    best_source = src

        if best_source:
            report["recommendations"].append(
                f"Best source: {best_source} ({best_rate:.0f}% response rate). Consider increasing volume."
            )
    except Exception:
        pass

    # ── Velocity ─────────────────────────────────────────────────────────
    report["velocity"] = pdb.get_stage_velocity()

    # ── Weekly trend ─────────────────────────────────────────────────────
    try:
        recent = pdb.get_recent(days=7)
        report["health"]["discovered_this_week"] = len(recent)
    except Exception:
        report["health"]["discovered_this_week"] = 0

    # ── Recruiter gaps ───────────────────────────────────────────────────
    try:
        conn = pdb._get_conn()
        no_recruiter = conn.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status IN ('applied', 'response', 'interview')
            AND job_id NOT IN (SELECT DISTINCT job_id FROM job_recruiters)
            AND recruiter_name IS NULL AND recruiter_email IS NULL
        """).fetchone()[0]
        conn.close()
        if no_recruiter > 5:
            report["alerts"].append({
                "type": "recruiter_gap",
                "count": no_recruiter,
                "action": f"{no_recruiter} active applications have no recruiter contact. Run outreach-agent.",
            })
    except Exception:
        pass

    # General recommendations
    if response_rate < 5.0 and applied > 20:
        report["recommendations"].append(
            f"Response rate {response_rate:.1f}% is below 5% benchmark. "
            "Consider: (1) tailoring CVs more aggressively, (2) adding cover letters, "
            "(3) direct recruiter outreach for top-scored roles."
        )
    if len(stale) > 5:
        report["recommendations"].append(
            f"{len(stale)} stale applications (14+ days, no response). "
            "Consider sending follow-up emails or marking withdrawn."
        )

    return report


def format_telegram(report):
    """Format report as compact Telegram message."""
    h = report["health"]
    lines = []
    lines.append(f"Pipeline: {h['active_applications']} active | {h['response_rate_pct']}% response rate")

    # Top 3 prospects
    if report["prospects"]:
        top3 = report["prospects"][:3]
        prospects_str = ", ".join(f"{p['company']}({p['status'][:3]})" for p in top3)
        lines.append(f"Top: {prospects_str}")

    # Alerts
    interviews = [a for a in report["alerts"] if a.get("to") == "interview"]
    if interviews:
        lines.append(f"New interviews: {', '.join(a['company'] for a in interviews)}")

    stale_count = h.get("stale_count", 0)
    if stale_count > 0:
        lines.append(f"Stale: {stale_count} need follow-up")

    # Recommendations (first one only)
    if report["recommendations"]:
        lines.append(f"Tip: {report['recommendations'][0][:100]}")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline Intelligence Engine")
    parser.add_argument("--telegram", action="store_true", help="Output Telegram summary only")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    report = generate_report()

    # Save JSON
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=2, default=str)

    if args.telegram:
        print(format_telegram(report))
    elif args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        # Both
        print(f"\nIntelligence report saved: {OUTPUT_PATH}")
        print(f"\nTelegram summary:")
        print(format_telegram(report))
        print(f"\nAlerts: {len(report['alerts'])}")
        for a in report["alerts"][:5]:
            print(f"  [{a['type']}] {a.get('company', '')} - {a.get('action', '')}")
        print(f"\nRecommendations: {len(report['recommendations'])}")
        for r in report["recommendations"]:
            print(f"  - {r[:120]}")


if __name__ == "__main__":
    main()
