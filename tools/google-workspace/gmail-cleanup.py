#!/usr/bin/env python3
"""Gmail Cleanup Tool - Scan, categorize, and clean with approval.

Usage:
  gmail-cleanup.py scan [--days 30] [--max 500]    Scan and produce cleanup plan
  gmail-cleanup.py execute <plan-file>              Execute approved plan
  gmail-cleanup.py stats                            Show inbox stats

Output: JSON plan file for review before any action is taken.
"""

import argparse
import json
import os
import sys
import time
import re
from pathlib import Path
from datetime import datetime, timedelta

# Import gw.py functions
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from gw import get_access_token, api_call
GMAIL_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"

# ─── Protected Patterns (NEVER touch these) ───

PROTECTED_KEYWORDS = [
    "interview", "offer", "shortlist", "shortlisted", "selected",
    "congratulations", "accepted", "next round", "assessment",
    "technical test", "case study", "salary", "compensation",
    "contract", "onboarding", "background check", "reference check",
    "we'd like to", "we would like to invite", "pleased to inform",
    "moving forward", "next steps", "follow up", "follow-up",
]

PROTECTED_DOMAINS = []  # Populated at runtime from pipeline.md

PROTECTED_SENDERS = [
    "toplead", "topmed", "sgh", "saudi german",
    "eslsca", "paris eslsca",
]

# ─── Category Rules ───

NEWSLETTER_PATTERNS = [
    "noreply", "no-reply", "newsletter", "digest", "weekly update",
    "daily brief", "unsubscribe", "email preferences", "marketing",
    "notifications@", "info@", "hello@", "team@", "news@",
]

PROMOTION_PATTERNS = [
    "sale", "discount", "% off", "limited time", "deal", "offer expires",
    "free trial", "upgrade now", "premium", "subscribe now",
    "black friday", "cyber monday", "flash sale", "coupon",
    "order confirmation", "shipping", "delivery", "tracking",
]

SOCIAL_PATTERNS = [
    "linkedin.com", "facebook.com", "twitter.com", "x.com",
    "instagram.com", "youtube.com", "tiktok.com", "reddit.com",
    "notifications-noreply@linkedin.com", "invitations@linkedin.com",
]

JOB_ALERT_PATTERNS = [
    "jobalerts-noreply@linkedin.com", "jobs-listings@linkedin.com",
    "bayt.com", "indeed.com", "glassdoor.com", "naukrigulf.com",
    "job alert", "new jobs for you", "jobs matching",
    "careers@", "talent@", "recruiting@", "hr@",
]


def load_pipeline_domains():
    """Load company domains from pipeline.md to protect."""
    pipeline_path = Path("/root/.openclaw/workspace/jobs-bank/pipeline.md")
    if not pipeline_path.exists():
        return []
    
    domains = []
    content = pipeline_path.read_text()
    # Extract company names from pipeline table rows
    for line in content.split("\n"):
        if "|" in line and not line.startswith("|-"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) > 2 and parts[1] and parts[1] != "Company":
                company = parts[1].lower().strip()
                if company:
                    domains.append(company)
    return domains


def is_protected(email_data):
    """Check if an email should NEVER be touched."""
    subject = (email_data.get("subject", "") or "").lower()
    sender = (email_data.get("from", "") or "").lower()
    snippet = (email_data.get("snippet", "") or "").lower()
    
    combined = f"{subject} {sender} {snippet}"
    
    # Check protected keywords
    for kw in PROTECTED_KEYWORDS:
        if kw in combined:
            return True, f"Protected keyword: '{kw}'"
    
    # Check pipeline companies
    for domain in PROTECTED_DOMAINS:
        if domain in sender or domain in subject:
            return True, f"Pipeline company: '{domain}'"
    
    # Check protected senders
    for ps in PROTECTED_SENDERS:
        if ps in sender or ps in subject:
            return True, f"Protected sender: '{ps}'"
    
    return False, ""


def categorize(email_data):
    """Categorize an email for cleanup action."""
    subject = (email_data.get("subject", "") or "").lower()
    sender = (email_data.get("from", "") or "").lower()
    snippet = (email_data.get("snippet", "") or "").lower()
    
    combined = f"{subject} {sender} {snippet}"
    
    # Check protection first
    protected, reason = is_protected(email_data)
    if protected:
        return "PROTECTED", reason
    
    # Job alerts (label, don't delete)
    for pattern in JOB_ALERT_PATTERNS:
        if pattern in combined:
            return "JOB_ALERT", f"Matched: '{pattern}'"
    
    # Social notifications
    for pattern in SOCIAL_PATTERNS:
        if pattern in combined:
            return "SOCIAL", f"Matched: '{pattern}'"
    
    # Newsletters
    for pattern in NEWSLETTER_PATTERNS:
        if pattern in combined:
            return "NEWSLETTER", f"Matched: '{pattern}'"
    
    # Promotions
    for pattern in PROMOTION_PATTERNS:
        if pattern in combined:
            return "PROMOTION", f"Matched: '{pattern}'"
    
    return "KEEP", "No cleanup pattern matched"


def get_messages(query, max_results):
    """Fetch messages matching a query."""
    messages = []
    page_token = None
    
    while len(messages) < max_results:
        params = {"q": query, "maxResults": min(100, max_results - len(messages))}
        if page_token:
            params["pageToken"] = page_token
        
        import urllib.parse
        param_str = urllib.parse.urlencode(params)
        result = api_call("GET", f"{GMAIL_BASE}/messages?{param_str}")
        
        batch = result.get("messages", [])
        if not batch:
            break
        
        messages.extend(batch)
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    
    return messages[:max_results]


def get_message_metadata(msg_id):
    """Get message metadata (subject, from, date, snippet)."""
    detail = api_call("GET", f"{GMAIL_BASE}/messages/{msg_id}?format=metadata&metadataHeaders=Subject&metadataHeaders=From&metadataHeaders=Date")
    headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
    return {
        "id": msg_id,
        "subject": headers.get("Subject", "(no subject)"),
        "from": headers.get("From", ""),
        "date": headers.get("Date", ""),
        "snippet": detail.get("snippet", ""),
        "labelIds": detail.get("labelIds", []),
    }


def scan(days, max_results):
    """Scan inbox and produce a cleanup plan."""
    global PROTECTED_DOMAINS
    PROTECTED_DOMAINS = load_pipeline_domains()
    
    print(f"Scanning inbox (last {days} days, max {max_results} emails)...", file=sys.stderr)
    print(f"Loaded {len(PROTECTED_DOMAINS)} pipeline companies as protected.", file=sys.stderr)
    
    query = f"in:inbox newer_than:{days}d"
    messages = get_messages(query, max_results)
    print(f"Found {len(messages)} messages.", file=sys.stderr)
    
    plan = {
        "generated": datetime.utcnow().isoformat() + "Z",
        "scan_params": {"days": days, "max_results": max_results},
        "protected_companies": PROTECTED_DOMAINS,
        "summary": {},
        "actions": [],
    }
    
    categories = {}
    
    for i, msg in enumerate(messages):
        if i % 20 == 0 and i > 0:
            print(f"  Processing {i}/{len(messages)}...", file=sys.stderr)
            time.sleep(0.5)  # Rate limit courtesy
        
        try:
            meta = get_message_metadata(msg["id"])
        except Exception as e:
            print(f"  Error reading {msg['id']}: {e}", file=sys.stderr)
            continue
        
        category, reason = categorize(meta)
        
        if category not in categories:
            categories[category] = []
        categories[category].append(meta)
        
        # Determine action
        if category == "PROTECTED":
            action = "SKIP"
        elif category == "KEEP":
            action = "SKIP"
        elif category == "JOB_ALERT":
            action = "LABEL_AND_ARCHIVE"
        elif category == "SOCIAL":
            action = "ARCHIVE"
        elif category == "NEWSLETTER":
            action = "ARCHIVE"
        elif category == "PROMOTION":
            action = "TRASH"
        else:
            action = "SKIP"
        
        if action != "SKIP":
            plan["actions"].append({
                "id": meta["id"],
                "action": action,
                "category": category,
                "reason": reason,
                "subject": meta["subject"][:100],
                "from": meta["from"][:80],
                "date": meta["date"],
            })
    
    # Summary
    plan["summary"] = {
        "total_scanned": len(messages),
        "protected": len(categories.get("PROTECTED", [])),
        "keep": len(categories.get("KEEP", [])),
        "job_alerts_to_label": len(categories.get("JOB_ALERT", [])),
        "social_to_archive": len(categories.get("SOCIAL", [])),
        "newsletters_to_archive": len(categories.get("NEWSLETTER", [])),
        "promotions_to_trash": len(categories.get("PROMOTION", [])),
        "total_actions": len(plan["actions"]),
    }
    
    # Save plan
    plan_path = SCRIPT_DIR / f"cleanup-plan-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"
    with open(plan_path, "w") as f:
        json.dump(plan, f, indent=2)
    
    # Print human-readable summary
    s = plan["summary"]
    print(f"\n{'='*50}")
    print(f"GMAIL CLEANUP PLAN")
    print(f"{'='*50}")
    print(f"Total scanned: {s['total_scanned']}")
    print(f"")
    print(f"  PROTECTED (never touch):     {s['protected']}")
    print(f"  KEEP (no action):            {s['keep']}")
    print(f"  Job alerts (label+archive):  {s['job_alerts_to_label']}")
    print(f"  Social (archive):            {s['social_to_archive']}")
    print(f"  Newsletters (archive):       {s['newsletters_to_archive']}")
    print(f"  Promotions (trash):          {s['promotions_to_trash']}")
    print(f"")
    print(f"  TOTAL ACTIONS: {s['total_actions']}")
    print(f"")
    print(f"Plan saved to: {plan_path}")
    print(f"")
    print(f"To execute: python3 {__file__} execute {plan_path}")
    
    return plan_path


def execute(plan_file):
    """Execute an approved cleanup plan."""
    with open(plan_file) as f:
        plan = json.load(f)
    
    actions = plan["actions"]
    print(f"Executing {len(actions)} actions...", file=sys.stderr)
    
    # Ensure Job Alerts label exists
    labels_result = api_call("GET", f"{GMAIL_BASE}/labels")
    label_map = {l["name"]: l["id"] for l in labels_result.get("labels", [])}
    
    job_alert_label_id = label_map.get("Job Alerts")
    if not job_alert_label_id:
        result = api_call("POST", f"{GMAIL_BASE}/labels", {
            "name": "Job Alerts",
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show"
        })
        job_alert_label_id = result["id"]
        print("Created 'Job Alerts' label.", file=sys.stderr)
    
    stats = {"archived": 0, "trashed": 0, "labeled": 0, "errors": 0}
    
    for i, action in enumerate(actions):
        if i % 20 == 0 and i > 0:
            print(f"  Progress: {i}/{len(actions)}...", file=sys.stderr)
            time.sleep(0.3)
        
        msg_id = action["id"]
        act = action["action"]
        
        try:
            if act == "ARCHIVE":
                # Remove INBOX label
                api_call("POST", f"{GMAIL_BASE}/messages/{msg_id}/modify", {
                    "removeLabelIds": ["INBOX"]
                })
                stats["archived"] += 1
            
            elif act == "LABEL_AND_ARCHIVE":
                api_call("POST", f"{GMAIL_BASE}/messages/{msg_id}/modify", {
                    "addLabelIds": [job_alert_label_id],
                    "removeLabelIds": ["INBOX"]
                })
                stats["labeled"] += 1
                stats["archived"] += 1
            
            elif act == "TRASH":
                api_call("POST", f"{GMAIL_BASE}/messages/{msg_id}/trash", {})
                stats["trashed"] += 1
        
        except Exception as e:
            print(f"  Error on {msg_id}: {e}", file=sys.stderr)
            stats["errors"] += 1
    
    print(f"\n{'='*50}")
    print(f"CLEANUP COMPLETE")
    print(f"{'='*50}")
    print(f"  Archived:  {stats['archived']}")
    print(f"  Labeled:   {stats['labeled']} (Job Alerts)")
    print(f"  Trashed:   {stats['trashed']} (recoverable 30 days)")
    print(f"  Errors:    {stats['errors']}")


def inbox_stats():
    """Show inbox statistics."""
    import urllib.parse
    
    queries = {
        "Total inbox": "in:inbox",
        "Unread": "in:inbox is:unread",
        "Last 24h": "in:inbox newer_than:1d",
        "Last 7d": "in:inbox newer_than:7d",
        "Newsletters": "in:inbox unsubscribe",
        "LinkedIn": "in:inbox from:linkedin.com",
        "Job alerts": "in:inbox from:jobalerts-noreply@linkedin.com",
        "Social": "in:inbox category:social",
        "Promotions": "in:inbox category:promotions",
    }
    
    print(f"{'='*40}")
    print(f"INBOX STATS")
    print(f"{'='*40}")
    
    for label, query in queries.items():
        params = urllib.parse.urlencode({"q": query, "maxResults": 1})
        result = api_call("GET", f"{GMAIL_BASE}/messages?{params}")
        count = result.get("resultSizeEstimate", 0)
        print(f"  {label:20s}: {count}")
    
    print()


def main():
    parser = argparse.ArgumentParser(description="Gmail Cleanup Tool")
    sub = parser.add_subparsers(dest="command")
    
    p = sub.add_parser("scan")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--max", type=int, default=500)
    
    p = sub.add_parser("execute")
    p.add_argument("plan_file")
    
    sub.add_parser("stats")
    
    args = parser.parse_args()
    
    if args.command == "scan":
        scan(args.days, args.max)
    elif args.command == "execute":
        execute(args.plan_file)
    elif args.command == "stats":
        inbox_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
