#!/usr/bin/env python3
"""
outreach-agent.py — Reads outreach queue, tracks networking actions.

Tracks: today's actions, weekly summary, queue health
Prioritizes: outreach for companies with active pipeline applications
Cross-references: data/pipeline-status.json
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

# Import from agent-common.py
import sys
sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
common = import_module("agent-common")

AgentResult = common.AgentResult
agent_main = common.agent_main
load_json = common.load_json
is_dry_run = common.is_dry_run
now_cairo = common.now_cairo
now_iso = common.now_iso
WORKSPACE = common.WORKSPACE
DATA_DIR = common.DATA_DIR

OUTPUT_PATH = DATA_DIR / "outreach-summary.json"
OUTREACH_QUEUE_PATH = WORKSPACE / "coordination" / "outreach-queue.json"
PIPELINE_STATUS_PATH = DATA_DIR / "pipeline-status.json"


def create_empty_outreach_queue():
    """Create an empty outreach queue file if missing."""
    empty_queue = {
        "last_updated": now_iso(),
        "generated_by": "outreach-agent",
        "this_week": {
            "target": 25,
            "sent": 0,
            "accepted": 0,
            "pending": 0
        },
        "today": {
            "target": 5,
            "sent": 0,
            "accepted": 0,
            "pending": 0
        },
        "pending_queue": [],
        "warm_leads": [],
        "follow_ups_due": [],
        "targets": {
            "total": 0,
            "researched": 0,
            "contacted": 0,
            "connected": 0
        }
    }
    
    # Only write if not dry run
    if not is_dry_run():
        OUTREACH_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTREACH_QUEUE_PATH, 'w') as f:
            json.dump(empty_queue, f, indent=2)
    
    return empty_queue


def get_pipeline_companies():
    """Extract company names from pipeline status for cross-reference."""
    pipeline = load_json(PIPELINE_STATUS_PATH)
    if not pipeline:
        return set()
    
    companies = set()
    data = pipeline.get("data", {})
    
    # Try to extract company names from various structures
    for app in data.get("stale_applications", []):
        if app.get("company"):
            companies.add(app["company"].lower())
    
    for app in data.get("interviews_upcoming", []):
        if app.get("company"):
            companies.add(app["company"].lower())
    
    return companies


def calculate_response_rate(queue_data):
    """Calculate response rate from queue data."""
    total_sent = queue_data.get("this_week", {}).get("sent", 0)
    total_accepted = queue_data.get("this_week", {}).get("accepted", 0)
    
    if total_sent == 0:
        return 0.0
    
    return round(total_accepted / total_sent * 100, 1)


def run_outreach_agent(result: AgentResult):
    """Main agent logic."""
    now = now_cairo()
    today = now.strftime("%Y-%m-%d")
    
    # Load or create outreach queue
    if not OUTREACH_QUEUE_PATH.exists():
        print("  Outreach queue not found, creating empty...")
        queue_data = create_empty_outreach_queue()
    else:
        queue_data = load_json(OUTREACH_QUEUE_PATH)
    
    print(f"  Loaded outreach queue")
    
    # Get pipeline companies for cross-reference
    pipeline_companies = get_pipeline_companies()
    print(f"  Found {len(pipeline_companies)} companies in pipeline")
    
    # Parse queue data
    pending_queue = queue_data.get("pending_queue", [])
    warm_leads = queue_data.get("warm_leads", [])
    follow_ups_due = queue_data.get("follow_ups_due", [])
    this_week = queue_data.get("this_week", {})
    today_stats = queue_data.get("today", {})
    targets = queue_data.get("targets", {})
    
    # Prioritize leads from pipeline companies
    prioritized_leads = []
    other_leads = []
    
    for lead in pending_queue:
        company = (lead.get("company") or "").lower()
        if company in pipeline_companies:
            lead["priority_reason"] = "Active application in pipeline"
            prioritized_leads.append(lead)
        else:
            other_leads.append(lead)
    
    # Calculate overdue follow-ups
    overdue_count = 0
    for follow_up in follow_ups_due:
        follow_up_date = follow_up.get("follow_up_date")
        if follow_up_date and follow_up_date < today:
            overdue_count += 1
    
    # Queue health metrics
    queue_depth = len(pending_queue)
    warm_count = len(warm_leads)
    
    # Outreach velocity (sent per day this week)
    week_sent = this_week.get("sent", 0)
    days_in_week = min(now.weekday() + 1, 7)  # Days elapsed this week
    velocity = round(week_sent / max(days_in_week, 1), 1)
    
    # Build summary
    result.set_data({
        "scan_time": now_iso(),
        "today": {
            "date": today,
            "target": today_stats.get("target", 5),
            "sent": today_stats.get("sent", 0),
            "remaining": max(0, today_stats.get("target", 5) - today_stats.get("sent", 0))
        },
        "this_week": {
            "target": this_week.get("target", 25),
            "sent": this_week.get("sent", 0),
            "accepted": this_week.get("accepted", 0),
            "pending": this_week.get("pending", 0),
            "velocity": velocity
        },
        "queue_health": {
            "queue_depth": queue_depth,
            "warm_leads": warm_count,
            "follow_ups_due": len(follow_ups_due),
            "overdue_follow_ups": overdue_count
        },
        "prioritized_leads": prioritized_leads[:5],
        "next_actions": (prioritized_leads + other_leads)[:10],
        "targets": targets,
        "pipeline_cross_ref": {
            "companies_matched": len(pipeline_companies),
            "prioritized_count": len(prioritized_leads)
        }
    })
    
    # KPIs
    response_rate = calculate_response_rate(queue_data)
    result.set_kpi({
        "outreach_velocity": velocity,
        "response_rate": response_rate,
        "overdue_count": overdue_count,
        "queue_depth": queue_depth
    })
    
    # Recommendations
    if overdue_count > 0:
        result.add_recommendation(
            action="send_follow_ups",
            target=f"{overdue_count} overdue follow-ups",
            reason="Follow-up dates have passed",
            urgency="high"
        )
    
    remaining_today = max(0, today_stats.get("target", 5) - today_stats.get("sent", 0))
    if remaining_today > 0:
        result.add_recommendation(
            action="send_outreach",
            target=f"{remaining_today} outreach messages",
            reason=f"Today's target: {today_stats.get('target', 5)}, sent: {today_stats.get('sent', 0)}",
            urgency="medium"
        )
    
    if prioritized_leads:
        result.add_recommendation(
            action="prioritize_pipeline_leads",
            target=f"{len(prioritized_leads)} leads at pipeline companies",
            reason="These leads are at companies where you have active applications",
            urgency="high"
        )
    
    if queue_depth < 10:
        result.add_recommendation(
            action="research_more_leads",
            target="Outreach queue",
            reason=f"Queue depth ({queue_depth}) is low - add more leads",
            urgency="medium"
        )
    
    if response_rate < 20 and week_sent > 5:
        result.add_recommendation(
            action="review_outreach_strategy",
            target="Messaging approach",
            reason=f"Response rate ({response_rate}%) is below target",
            urgency="low"
        )


if __name__ == "__main__":
    agent_main(
        agent_name="outreach-agent",
        run_func=run_outreach_agent,
        output_path=OUTPUT_PATH,
        ttl_hours=6,
        version="1.0.0"
    )
