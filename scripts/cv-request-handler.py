#!/usr/bin/env python3
"""
CV Request Handler - Polls Notion Pipeline for "Request CV" checkbox.
When found, triggers CV build on Opus 4.6, updates Notion + sends Telegram.

Usage:
  python3 cv-request-handler.py          # One-shot poll
  python3 cv-request-handler.py --watch  # Continuous polling (for cron)
"""

import sys, os, json, re, time, subprocess, urllib.request
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from application_lock import ApplicationLockService

WORKSPACE = "/root/.openclaw/workspace"
CAIRO = timezone(timedelta(hours=2))


def get_notion_token():
    with open(os.path.join(WORKSPACE, "config/notion.json")) as f:
        return json.load(f)["token"]


def notion_request(method, endpoint, body=None):
    token = get_notion_token()
    url = f"https://api.notion.com/v1/{endpoint}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def find_cv_requests():
    """Find all Pipeline entries with Request CV = True."""
    db_id = "3268d599-a162-81b4-b768-f162adfa4971"
    result = notion_request("POST", f"databases/{db_id}/query", {
        "filter": {
            "property": "Request CV",
            "checkbox": {"equals": True}
        }
    })
    
    requests = []
    for page in result.get("results", []):
        props = page.get("properties", {})
        
        # Safe extraction
        company_t = props.get("Company", {}).get("title", [])
        company = company_t[0].get("plain_text", "") if company_t else ""
        
        role_t = props.get("Role", {}).get("rich_text", [])
        role = role_t[0].get("plain_text", "") if role_t else ""
        
        url = props.get("URL", {}).get("url", "") or ""
        
        ats = props.get("ATS Score", {}).get("number")
        
        location_t = props.get("Location", {}).get("rich_text", [])
        location = location_t[0].get("plain_text", "") if location_t else ""
        
        requests.append({
            "page_id": page["id"],
            "company": company,
            "role": role,
            "url": url,
            "ats_score": ats,
            "location": location,
        })
    
    return requests


def update_notion_after_cv(page_id, cv_url, ats_score=None):
    """Update Pipeline row after CV is built."""
    today = datetime.now(CAIRO).strftime("%Y-%m-%d")
    props = {
        "Request CV": {"checkbox": False},  # Untick
        "CV Link": {"url": cv_url},
        "CV Date": {"date": {"start": today}},
        "CV Model": {"select": {"name": "opus46"}},
        "Stage": {"select": {"name": "\ud83d\udcc4 CV Ready"}},
    }
    notion_request("PATCH", f"pages/{page_id.replace('-','')}", {"properties": props})


def send_telegram(message, file_path=None):
    """Send notification via OpenClaw message tool (called externally)."""
    # Write to a trigger file that OpenClaw can pick up
    trigger = {
        "message": message,
        "file": file_path,
        "timestamp": datetime.now(CAIRO).isoformat(),
    }
    trigger_path = os.path.join(WORKSPACE, "jobs-bank/handoff/cv-ready.trigger")
    os.makedirs(os.path.dirname(trigger_path), exist_ok=True)
    with open(trigger_path, "w") as f:
        json.dump(trigger, f, indent=2)
    print(f"[cv-handler] Trigger written: {trigger_path}")


def process_cv_request(req):
    """Process a single CV request."""
    company = req["company"]
    role = req["role"]
    url = req["url"]
    page_id = req["page_id"]
    
    print(f"[cv-handler] Processing: {role} @ {company}")
    
    # Check if job is already being processed (lock check)
    lock_service = ApplicationLockService()
    if lock_service.is_locked(company, role):
        print(f"[cv-handler] ⚠️  DUPLICATE: {company} | {role} is already being processed")
        msg = f"⚠️ CV Build Skipped\n{role} @ {company}\nJob is already being processed (in-flight)"
        send_telegram(msg)
        return None
    
    # Check if job already exists in pipeline_db
    try:
        import sqlite3
        db_path = os.path.join(WORKSPACE, "data/nasr-pipeline.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, status FROM jobs 
            WHERE LOWER(company) = LOWER(?) AND LOWER(title) = LOWER(?)
        """, (company, role))
        existing = cursor.fetchone()
        conn.close()
        
        if existing:
            job_id, status = existing
            print(f"[cv-handler] ⚠️  DUPLICATE: {company} | {role} already in database (status: {status})")
            msg = f"⚠️ CV Build Skipped\n{role} @ {company}\nJob already registered in pipeline (status: {status})"
            send_telegram(msg)
            return None
    except Exception as e:
        print(f"[cv-handler] Failed to check pipeline_db: {e}")
    
    # Check if we have a dossier
    dossier_slug = f"{company.lower().replace(' ','-')}-{role.lower().replace(' ','-')}"
    dossier_path = os.path.join(WORKSPACE, f"jobs-bank/dossiers/{dossier_slug}.md")
    
    # Build the CV request brief
    brief = f"""BUILD TAILORED CV for:
Company: {company}
Role: {role}
Location: {req.get('location', 'GCC')}
Job URL: {url}
ATS Score: {req.get('ats_score', 'Unknown')}

INSTRUCTIONS:
1. Fetch the full JD from the URL above
2. Load master CV from memory/master-cv-data.md
3. Tailor CV to this specific role (NOT a template)
4. Generate PDF using WeasyPrint
5. Save PDF to: {WORKSPACE}/jobs-bank/cvs/{company.replace(' ','_')}_{role.replace(' ','_')}.pdf
6. Save to GitHub-ready path for linking

Quality over speed. Full ATS keyword optimization.
Every CV must be individually crafted for this specific JD.

COMPLETION RULES:
- You are NOT done until the PDF exists and is verified
- Do not summarize what you "would do." Do the work now
- When genuinely complete, end with: TASK_COMPLETE
- Include the PDF file path in your final output

DO NOT update MEMORY.md, GOALS.md, or active-tasks.md.
"""
    
    # Write brief for OpenClaw to pick up
    brief_path = os.path.join(WORKSPACE, f"jobs-bank/handoff/cv-request-{dossier_slug}.md")
    os.makedirs(os.path.dirname(brief_path), exist_ok=True)
    with open(brief_path, "w") as f:
        f.write(brief)
    
    # Create trigger for NASR to spawn sub-agent
    trigger = {
        "type": "CV_BUILD_REQUEST",
        "company": company,
        "role": role,
        "url": url,
        "page_id": page_id,
        "brief_path": brief_path,
        "status": "NASR_REVIEW_NEEDED",
        "requested_at": datetime.now(CAIRO).isoformat(),
    }
    trigger_path = os.path.join(WORKSPACE, f"jobs-bank/handoff/cv-build-{dossier_slug}.trigger")
    with open(trigger_path, "w") as f:
        json.dump(trigger, f, indent=2)
    
    print(f"[cv-handler] Trigger created: {trigger_path}")
    print(f"[cv-handler] Brief written: {brief_path}")
    
    return trigger_path


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true", help="Continuous polling")
    args = parser.parse_args()
    
    print(f"[cv-handler] Checking for CV requests...")
    requests = find_cv_requests()
    
    if not requests:
        print("[cv-handler] No CV requests found")
        return
    
    print(f"[cv-handler] Found {len(requests)} CV request(s)")
    
    for req in requests:
        trigger = process_cv_request(req)
        print(f"[cv-handler] {req['company']} - {req['role']}: trigger created")
        
        # Send Telegram notification
        msg = f"📝 CV Build Requested\n{req['role']} @ {req['company']}\nTriggered from Notion. Spawning Opus 4.6..."
        send_telegram(msg)


if __name__ == "__main__":
    main()
