#!/usr/bin/env python3
"""
pipeline-agent.py — Reads Notion Job Pipeline DB, tracks application metrics.

Tracks: total applications, by_status, active_count, this_week stats
Detects: stale applications, follow-ups overdue, interviews upcoming
Computes: conversion funnel rates
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

# Import from agent-common.py
import sys
sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
common = import_module("agent-common")

AgentResult = common.AgentResult
agent_main = common.agent_main
retry_with_backoff = common.retry_with_backoff
load_json = common.load_json
is_dry_run = common.is_dry_run
now_cairo = common.now_cairo
now_iso = common.now_iso
WORKSPACE = common.WORKSPACE
DATA_DIR = common.DATA_DIR

# Configuration — use shared Notion client
notion_req = None
notion_query_db = None
try:
    from notion_client_shared import get_client, notion_req, notion_query_db
    _notion_client = get_client()
except Exception:
    _notion_client = None

PIPELINE_DB_ID = "3268d599-a162-81b4-b768-f162adfa4971"
APPLIED_IDS_FILE = WORKSPACE / "jobs-bank" / "applied-job-ids.txt"
OUTPUT_PATH = DATA_DIR / "pipeline-status.json"


@retry_with_backoff(max_retries=3, base_delay=2)
def fetch_notion_db(database_id):
    """Fetch all pages from a Notion database using shared client with retry/backoff."""
    if _notion_client is None or notion_req is None:
        return []

    all_results = []
    start_cursor = None
    has_more = True

    while has_more:
        body = {"page_size": 100}
        if start_cursor:
            body["start_cursor"] = start_cursor

        data, err = notion_req(_notion_client, "post", f"databases/{database_id}/query", body)
        if err:
            raise RuntimeError(f"Notion query failed: {err}")

        all_results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return all_results


def parse_notion_page(page):
    """Extract relevant fields from a Notion page."""
    props = page.get("properties", {})
    
    def get_title(prop):
        title = prop.get("title", [])
        return title[0]["plain_text"] if title else ""
    
    def get_select(prop):
        select = prop.get("select")
        return select["name"] if select else None
    
    def get_date(prop):
        date = prop.get("date")
        return date["start"] if date else None
    
    def get_rich_text(prop):
        text = prop.get("rich_text", [])
        return text[0]["plain_text"] if text else ""
    
    def get_number(prop):
        return prop.get("number")
    
    # Extract fields (adapt to actual Notion schema)
    result = {
        "id": page.get("id"),
        "created_time": page.get("created_time"),
        "last_edited_time": page.get("last_edited_time"),
    }
    
    # Common field names to check
    for key, prop in props.items():
        key_lower = key.lower()
        prop_type = prop.get("type")
        
        if prop_type == "title":
            result["title"] = get_title(prop)
        elif prop_type == "select":
            result[key_lower] = get_select(prop)
        elif prop_type == "date":
            result[key_lower] = get_date(prop)
        elif prop_type == "rich_text":
            result[key_lower] = get_rich_text(prop)
        elif prop_type == "number":
            result[key_lower] = get_number(prop)
        elif prop_type == "url":
            result[key_lower] = prop.get("url")
        elif prop_type == "checkbox":
            result[key_lower] = prop.get("checkbox", False)
    
    return result


def count_applied_ids():
    """Count unique job IDs from applied-job-ids.txt"""
    if not APPLIED_IDS_FILE.exists():
        return 0
    
    count = 0
    with open(APPLIED_IDS_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "|" in line:
                count += 1
    return count


def run_pipeline_agent(result: AgentResult):
    """Main agent logic."""
    now = now_cairo()
    week_start = now - timedelta(days=now.weekday())
    seven_days_ago = now - timedelta(days=7)
    
    print("  Fetching Notion Pipeline DB...")
    pages = fetch_notion_db(PIPELINE_DB_ID)
    print(f"  Found {len(pages)} applications in pipeline")
    
    applications = []
    by_status = {}
    stale_applications = []
    interviews_upcoming = []
    follow_ups_overdue = []
    this_week_applied = 0
    
    # Active statuses (not rejected, not withdrawn, not completed)
    # Based on Notion DB schema: Stage field contains status (may have emoji prefixes)
    # Normalize by checking if key words are IN the status string
    active_keywords = ["applied", "screening", "interview", "offer", "negotiation", "in progress", "pending", "active", "cv sent", "shortlisted", "assessment"]
    inactive_keywords = ["rejected", "withdrawn", "declined", "closed", "no response", "ghosted", "passed", "not interested"]
    # "discovered" jobs are scanner finds, not real applications — separate category
    discovered_keywords = ["discovered"]
    
    def is_discovered(status_str):
        status_lower = status_str.lower()
        return any(kw in status_lower for kw in discovered_keywords)
    
    def is_active_status(status_str):
        status_lower = status_str.lower()
        for kw in active_keywords:
            if kw in status_lower:
                return True
        return False
    
    def is_inactive_status(status_str):
        status_lower = status_str.lower()
        for kw in inactive_keywords:
            if kw in status_lower:
                return True
        return False
    
    for page in pages:
        app = parse_notion_page(page)
        applications.append(app)
        
        # Count by status - Notion uses "Stage" for status, "Company" is title
        status = (app.get("stage") or app.get("status") or "unknown").lower()
        by_status[status] = by_status.get(status, 0) + 1
        
        # Skip discovered jobs from all application metrics
        if is_discovered(status):
            continue
        
        # Parse last edited time
        last_edited = app.get("last_edited_time")
        if last_edited:
            try:
                edit_dt = datetime.fromisoformat(last_edited.replace("Z", "+00:00"))
                days_since_update = (now.replace(tzinfo=None) - edit_dt.replace(tzinfo=None)).days
                app["days_since_update"] = days_since_update
                
                # Stale detection (applied+ jobs with no update in 14+ days)
                if is_active_status(status) and days_since_update > 14:
                    stale_applications.append({
                        "company": app.get("title", "Unknown"),  # Company is the title field
                        "role": app.get("role", "Unknown"),
                        "status": status,
                        "days_stale": days_since_update
                    })
            except Exception:
                pass
        
        # Check for interview-related status
        if "interview" in status:
            interview_date = app.get("follow-up_due") or app.get("applied_date")
            if interview_date:
                try:
                    int_dt = datetime.fromisoformat(interview_date)
                    if int_dt.replace(tzinfo=None) >= now.replace(tzinfo=None):
                        interviews_upcoming.append({
                            "company": app.get("title", "Unknown"),
                            "role": app.get("role", "Unknown"),
                            "date": interview_date
                        })
                except Exception:
                    pass
        
        # Screening/interview jobs going quiet (7+ days with no update)
        if any(kw in status for kw in ["screening", "interview", "assessment", "shortlisted"]):
            if last_edited:
                try:
                    edit_dt2 = datetime.fromisoformat(last_edited.replace("Z", "+00:00"))
                    quiet_days = (now.replace(tzinfo=None) - edit_dt2.replace(tzinfo=None)).days
                    if quiet_days > 7:
                        follow_ups_overdue.append({
                            "company": app.get("title", "Unknown"),
                            "role": app.get("role", "Unknown"),
                            "follow_up_date": last_edited[:10],
                            "days_overdue": quiet_days,
                            "reason": f"In '{status}' with no update for {quiet_days} days"
                        })
                except Exception:
                    pass
        
        # Check follow-up dates (Notion field: Follow-up Due)
        follow_up = app.get("follow-up_due")
        if follow_up:
            try:
                fu_dt = datetime.fromisoformat(follow_up)
                if fu_dt.replace(tzinfo=None) < now.replace(tzinfo=None):
                    follow_ups_overdue.append({
                        "company": app.get("title", "Unknown"),
                        "role": app.get("role", "Unknown"),
                        "follow_up_date": follow_up,
                        "days_overdue": (now.replace(tzinfo=None) - fu_dt.replace(tzinfo=None)).days
                    })
            except Exception:
                pass
        
        # This week applications — only count jobs with applied+ status
        if is_active_status(status):
            applied_date = app.get("applied_date") or app.get("created_time")
            if applied_date:
                try:
                    if "T" not in applied_date:
                        applied_date = applied_date + "T00:00:00"
                    applied_dt = datetime.fromisoformat(applied_date.replace("Z", "+00:00"))
                    if applied_dt.replace(tzinfo=None) >= week_start.replace(tzinfo=None):
                        this_week_applied += 1
                except Exception:
                    pass
    
    # Count active vs total (excluding discovered from application counts)
    active_count = sum(1 for a in applications if is_active_status(a.get("stage") or a.get("status") or ""))
    discovered_count = sum(1 for a in applications if is_discovered((a.get("stage") or a.get("status") or "").lower()))
    total_tracked = len(applications) - discovered_count  # Real applications only
    
    # Conversion funnel - count by keyword matching since statuses have emojis
    def count_by_keyword(keyword):
        return sum(count for status, count in by_status.items() if keyword in status.lower())
    
    applied_count = count_by_keyword("applied")
    screening_count = count_by_keyword("screening")
    interview_count = count_by_keyword("interview")
    offer_count = count_by_keyword("offer") + count_by_keyword("negotiation")
    
    total_for_funnel = applied_count if applied_count > 0 else 1  # Funnel based on applied count
    funnel = {
        "applied": applied_count,
        "screening": screening_count,
        "interview": interview_count,
        "offer": offer_count,
        "rates": {
            "applied_to_screening": round(screening_count / total_for_funnel * 100, 1),
            "screening_to_interview": round(interview_count / max(screening_count, 1) * 100, 1),
            "interview_to_offer": round(offer_count / max(interview_count, 1) * 100, 1)
        }
    }
    
    # Cross-reference with applied-job-ids.txt
    external_applied_count = count_applied_ids()

    # ── DB query path (reads DB if available, supplements Notion data) ───────
    db_funnel = {}
    db_stale = []
    db_total = 0
    if _pdb:
        try:
            db_funnel = _pdb.get_funnel()
            db_stale = _pdb.get_stale(days=7)
            db_total = db_funnel.get("_total", 0)
            # Use DB stale count as authoritative if DB has data
            if db_stale and not stale_applications:
                for s in db_stale[:10]:
                    stale_applications.append({
                        "company": s.get("company"),
                        "title": s.get("title"),
                        "applied_date": s.get("applied_date"),
                        "days_stale": (datetime.now() - datetime.fromisoformat(
                            s["applied_date"] + "T00:00:00"
                        )).days if s.get("applied_date") else 0,
                    })
        except Exception:
            pass  # DB read failed, continue with Notion data
    # ─────────────────────────────────────────────────────────────────────────
    
    # Calculate avg days in pipeline
    total_days = 0
    counted = 0
    for app in applications:
        created = app.get("applied_date") or app.get("created_time")
        status_str = app.get("stage") or app.get("status") or ""
        if created and is_active_status(status_str):
            try:
                if "T" not in created:
                    created = created + "T00:00:00"
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                days = (now.replace(tzinfo=None) - created_dt.replace(tzinfo=None)).days
                total_days += days
                counted += 1
            except Exception:
                pass
    avg_days = round(total_days / max(counted, 1), 1)
    
    # ── DB read: add keywords (already have db_funnel and db_stale from above) ─
    db_keywords = []
    if _pdb:
        try:
            db_keywords = _pdb.analyze_keywords(top_n=10)
        except Exception:
            pass
    # ─────────────────────────────────────────────────────────────────────────

    # Set data
    result.set_data({
        "total_applications": total_tracked,
        "active_count": active_count,
        "external_applied_count": external_applied_count,
        "db_total": db_total,
        "db_funnel": db_funnel,
        "by_status": by_status,
        "this_week": {
            "applied": this_week_applied,
            "start_date": week_start.strftime("%Y-%m-%d")
        },
        "stale_applications": stale_applications[:10],  # Top 10
        "interviews_upcoming": interviews_upcoming,
        "follow_ups_overdue": follow_ups_overdue[:10],  # Top 10
        "conversion_funnel": funnel
    })
    
    # Set KPIs
    result.set_kpi({
        "total_tracked": total_tracked,
        "active_rate": round(active_count / max(total_tracked, 1) * 100, 1),
        "avg_days_in_pipeline": avg_days,
        "follow_ups_overdue": len(follow_ups_overdue),
        "interviews_this_week": len([i for i in interviews_upcoming if _is_this_week(i.get("date"), now, week_start)]),
        "stale_count": len(stale_applications)
    })
    
    # Add recommendations
    if stale_applications:
        result.add_recommendation(
            action="follow_up",
            target=f"{len(stale_applications)} stale applications",
            reason="Applications with no update in 7+ days need attention",
            urgency="medium"
        )
    
    if follow_ups_overdue:
        result.add_recommendation(
            action="send_follow_up",
            target=f"{len(follow_ups_overdue)} overdue follow-ups",
            reason="Follow-up dates have passed",
            urgency="high"
        )
    
    if interviews_upcoming:
        result.add_recommendation(
            action="prepare_interview",
            target=f"{len(interviews_upcoming)} upcoming interviews",
            reason="Interviews scheduled - prepare talking points",
            urgency="high"
        )
    
    if this_week_applied < 5:
        result.add_recommendation(
            action="apply_more",
            target="Job applications",
            reason=f"Only {this_week_applied} applications this week, aim for 10+",
            urgency="medium"
        )


def _is_this_week(date_str, now, week_start):
    """Check if a date is within this week."""
    if not date_str:
        return False
    try:
        dt = datetime.fromisoformat(date_str)
        return week_start.replace(tzinfo=None) <= dt.replace(tzinfo=None) <= now.replace(tzinfo=None) + timedelta(days=7-now.weekday())
    except Exception:
        return False


if __name__ == "__main__":
    agent_main(
        agent_name="pipeline-agent",
        run_func=run_pipeline_agent,
        output_path=OUTPUT_PATH,
        ttl_hours=6,
        version="1.0.0"
    )
