#!/usr/bin/env python3
"""
Sync Notion Job Pipeline DB → Ontology Graph (JobApplication + Organization entities)
Runs on: cron daily OR called from morning-briefing-orchestrator.py

Usage: python3 scripts/ontology-pipeline-sync.py
"""

import json
import urllib.request
import ssl
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path("/root/.openclaw/workspace")
GRAPH_FILE = WORKSPACE / "memory/ontology/graph.jsonl"
NOTION_CONFIG = WORKSPACE / "config/notion.json"
PIPELINE_DB_ID = "3268d599-a162-81b4-b768-f162adfa4971"

ctx = ssl.create_default_context()

def load_token():
    return json.loads(NOTION_CONFIG.read_text())["token"]

def notion_query(db_id, body=None):
    token = load_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    results = []
    cursor = None
    while True:
        payload = dict(body or {})
        payload["page_size"] = 100
        if cursor:
            payload["start_cursor"] = cursor
        req = urllib.request.Request(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            data=json.dumps(payload).encode(), method="POST", headers=headers
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=20, context=ctx).read())
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return results

def prop_text(props, name):
    p = props.get(name, {})
    t = p.get("type")
    if t == "title":
        return "".join(i.get("plain_text", "") for i in p.get("title", [])) or None
    if t == "rich_text":
        return "".join(i.get("plain_text", "") for i in p.get("rich_text", [])) or None
    if t == "select":
        s = p.get("select")
        return s.get("name") if s else None
    if t == "url":
        return p.get("url")
    if t == "date":
        d = p.get("date")
        return d.get("start") if d else None
    if t == "number":
        return p.get("number")
    if t == "checkbox":
        return p.get("checkbox")
    return None

def load_existing_notion_ids(entity_type):
    """Return set of Notion page IDs already in graph for given type."""
    ids = set()
    if not GRAPH_FILE.exists():
        return ids
    with open(GRAPH_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("op") in ("create", "update"):
                e = entry["entity"]
                if e.get("type") == entity_type:
                    nid = e.get("properties", {}).get("notion_id")
                    if nid:
                        ids.add(nid)
    return ids

# Stage → status mapping
STAGE_STATUS = {
    "Discovered": "research",
    "CV Built": "cv_built",
    "SUBMIT": "ready_to_apply",
    "Applied": "applied",
    "Screening": "applied",
    "Interview": "interview",
    "Offer": "offer",
    "Rejected": "rejected",
    "Withdrawn": "withdrawn",
    "Skipped": "withdrawn",
}

def sync():
    now = datetime.now(timezone.utc).isoformat()
    
    existing_job_ids = load_existing_notion_ids("JobApplication")
    existing_org_ids = load_existing_notion_ids("Organization")

    pages = notion_query(PIPELINE_DB_ID)
    entries = []
    new_jobs = 0
    updated_jobs = 0
    new_orgs = 0

    # Track orgs we've already added this run
    orgs_this_run = {}

    for page in pages:
        props = page["properties"]
        page_id = page["id"].replace("-", "")

        company = prop_text(props, "Company")
        role = prop_text(props, "Role")
        stage = prop_text(props, "Stage") or "Discovered"
        status = STAGE_STATUS.get(stage, "applied")
        ats_score = prop_text(props, "ATS Score")
        applied_date = prop_text(props, "Applied Date")
        follow_up_date = prop_text(props, "Follow-up Due")
        cv_link = prop_text(props, "CV Link")
        location = prop_text(props, "Location")
        url = prop_text(props, "URL")
        verdict = prop_text(props, "Verdict")
        notes = prop_text(props, "Notes")
        salary = prop_text(props, "Salary")

        # Org entity
        if company:
            org_key = company.lower().strip()
            if org_key not in orgs_this_run and page_id not in existing_org_ids:
                org_id = f"org_notion_{page_id[:12]}"
                orgs_this_run[org_key] = org_id
                entries.append({"op": "create", "entity": {
                    "id": org_id,
                    "type": "Organization",
                    "properties": {k: v for k, v in {
                        "notion_id": page_id,
                        "name": company,
                        "location": location,
                    }.items() if v is not None},
                    "created": now, "updated": now
                }})
                new_orgs += 1

        # JobApplication entity
        job_id = f"job_notion_{page_id[:12]}"
        props_dict = {k: v for k, v in {
            "notion_id": page_id,
            "title": role,
            "company": company,
            "status": status,
            "stage": stage,
            "location": location,
            "date_applied": applied_date,
            "follow_up_date": follow_up_date,
            "fit_score": f"{ats_score}/100" if ats_score else None,
            "cv_link": cv_link,
            "job_url": url,
            "verdict": verdict,
            "notes": notes,
            "salary": salary,
        }.items() if v is not None}

        if page_id in existing_job_ids:
            # Update status/stage only
            entries.append({"op": "update", "entity": {
                "id": job_id,
                "type": "JobApplication",
                "properties": {"status": status, "stage": stage, "follow_up_date": follow_up_date},
                "updated": now
            }})
            updated_jobs += 1
        else:
            entries.append({"op": "create", "entity": {
                "id": job_id,
                "type": "JobApplication",
                "properties": props_dict,
                "created": now, "updated": now
            }})
            new_jobs += 1

    with open(GRAPH_FILE, "a") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    print(f"✅ Pipeline sync: {new_jobs} new jobs | {updated_jobs} updated | {new_orgs} new orgs | {len(pages)} total in Notion")
    return {"new_jobs": new_jobs, "updated": updated_jobs, "new_orgs": new_orgs, "total": len(pages)}

if __name__ == "__main__":
    sync()
