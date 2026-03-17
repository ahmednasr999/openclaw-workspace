#!/usr/bin/env python3
"""
Notion Sync Module
==================
Hooks into existing crons/scripts to push data to Notion automatically.
Import and call the relevant function at the end of each pipeline step.

Usage:
    from notion_sync import sync_briefing, sync_new_jobs, sync_content_status, sync_system_event
"""

import json, os, sys, re, glob, traceback
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def _get_client():
    """Lazy-load NotionClient to avoid import errors if Notion not configured."""
    try:
        from notion_client import NotionClient
        return NotionClient()
    except Exception as e:
        print(f"[notion_sync] ERROR: Could not init NotionClient: {e}")
        return None


def sync_briefing(briefing_json_path=None, briefing_data=None, date_str=None):
    """
    Push a morning briefing to Notion Daily Briefings database.
    Accepts either a path to the briefing JSON or the data dict directly.
    Returns the Notion page URL or None on failure.
    """
    nc = _get_client()
    if not nc:
        return None

    try:
        if briefing_json_path and not briefing_data:
            with open(briefing_json_path) as f:
                briefing_data = json.load(f)

        if not briefing_data:
            print("[notion_sync] No briefing data provided")
            return None

        cairo = timezone(timedelta(hours=2))
        now = datetime.now(cairo)
        if not date_str:
            date_str = now.strftime("%Y-%m-%d")

        # Extract fields from briefing JSON
        jobs_section = briefing_data.get("jobs", {})
        pipeline = briefing_data.get("pipeline", {})
        calendar_section = briefing_data.get("calendar", {})
        linkedin = briefing_data.get("linkedin", {})
        syslog = briefing_data.get("system", {})
        todays_post = briefing_data.get("todays_post", {})
        comments = briefing_data.get("comments", [])
        went_right = briefing_data.get("went_right", [])
        errors_list = briefing_data.get("errors", [])

        # Count metrics
        qualified = jobs_section.get("qualified", [])
        borderline = jobs_section.get("borderline", [])
        jobs_found = len(qualified) + len(borderline)
        priority_picks = len(qualified)

        total_apps = pipeline.get("total_applications", 0)
        if isinstance(total_apps, str):
            m = re.search(r'\d+', total_apps)
            total_apps = int(m.group()) if m else 0

        cal_events = calendar_section.get("events_today", [])
        cal_count = len(cal_events) if isinstance(cal_events, list) else 0

        system_health = "✅ All Clear" if not errors_list else f"⚠️ {len(errors_list)} issues"

        # Create briefing row
        briefing_page = nc.add_briefing(
            date=date_str,
            jobs_found=jobs_found,
            priority_picks=priority_picks,
            emails_flagged=0,
            calendar_events=cal_count,
            linkedin_impressions=0,
            system_health=system_health,
            model_used="MiniMax M2.5 (orchestrator)",
            generation_time=0,
            status="Delivered"
        )

        # Build rich content blocks
        blocks = []

        # Summary callout
        summary_parts = []
        if went_right:
            summary_parts = went_right[:5]
        summary_text = " | ".join(summary_parts) if summary_parts else f"Briefing for {date_str}"
        blocks.append(nc.callout_block(summary_text[:2000], "📊"))
        blocks.append(nc.divider_block())

        # Jobs section
        blocks.append(nc.heading_block("💼 Job Scanner", 2))
        scanner_note = jobs_section.get("scanner_note", "No scanner data")
        blocks.append(nc.paragraph_block(str(scanner_note)[:2000]))
        if qualified:
            blocks.append(nc.heading_block("Priority Picks", 3))
            for j in qualified[:10]:
                title = j.get("title", "Unknown")
                company = j.get("company", "Unknown")
                ats = j.get("ats_score", "N/A")
                blocks.append(nc.bullet_block(f"{title} @ {company} (ATS: {ats})"))
        if borderline:
            blocks.append(nc.heading_block("Borderline", 3))
            for j in borderline[:10]:
                title = j.get("title", "Unknown")
                company = j.get("company", "Unknown")
                ats = j.get("ats_score", "N/A")
                blocks.append(nc.bullet_block(f"{title} @ {company} (ATS: {ats})"))
        blocks.append(nc.divider_block())

        # Pipeline
        blocks.append(nc.heading_block("📈 Pipeline", 2))
        for k, v in pipeline.items():
            blocks.append(nc.bullet_block(f"{k}: {v}"))
        blocks.append(nc.divider_block())

        # Calendar
        if cal_events:
            blocks.append(nc.heading_block("📅 Calendar", 2))
            for ev in cal_events[:5]:
                if isinstance(ev, dict):
                    blocks.append(nc.bullet_block(f"{ev.get('time','')}: {ev.get('title','')}"[:200]))
                else:
                    blocks.append(nc.bullet_block(str(ev)[:200]))
            blocks.append(nc.divider_block())

        # LinkedIn
        if todays_post:
            blocks.append(nc.heading_block("📱 Today's LinkedIn Post", 2))
            post_title = todays_post.get("title", "")
            blocks.append(nc.paragraph_block(post_title[:2000]))
            blocks.append(nc.divider_block())

        # Comments
        if comments:
            blocks.append(nc.heading_block("💬 Engagement Targets", 2))
            for c in comments[:5]:
                author = c.get("author", "Unknown")
                topic = c.get("topic", c.get("snippet", ""))[:100]
                blocks.append(nc.bullet_block(f"{author}: {topic}"))
            blocks.append(nc.divider_block())

        # System health
        blocks.append(nc.heading_block("⚙️ System", 2))
        if errors_list:
            for e in errors_list:
                issue = e.get("issue", str(e))
                blocks.append(nc.bullet_block(f"❌ {issue}"[:200]))
        else:
            blocks.append(nc.bullet_block("All systems operational"))
        blocks.append(nc.divider_block())

        # Action items callout
        action_items = []
        if qualified:
            action_items.append(f"Review {len(qualified)} new priority picks")
        if comments:
            action_items.append(f"Post {len(comments)} engagement comments")
        if todays_post:
            action_items.append("Review and publish today's LinkedIn post")
        if action_items:
            blocks.append(nc.callout_block("Action: " + " | ".join(action_items), "⚡"))

        # Append blocks in batches (API limit: 100 blocks per call)
        for i in range(0, len(blocks), 90):
            batch = blocks[i:i+90]
            nc._append_blocks(briefing_page["id"], batch)

        print(f"[notion_sync] Briefing synced: {briefing_page.get('url', '')}")
        return briefing_page.get("url")

    except Exception as e:
        print(f"[notion_sync] ERROR syncing briefing: {e}")
        traceback.print_exc()
        return None


def sync_new_jobs(jobs_list):
    """
    Push newly discovered jobs to Notion Job Pipeline.
    jobs_list: list of dicts with keys: title, company, location, url, ats_score, site
    Returns count of jobs added.
    """
    nc = _get_client()
    if not nc:
        return 0

    added = 0
    for job in jobs_list:
        try:
            nc.add_job(
                company=job.get("company", "Unknown")[:100],
                role=job.get("title", "Unknown")[:100],
                stage="🔍 Discovered",
                ats_score=job.get("ats_score"),
                location=job.get("location", "")[:200],
                source=job.get("site", "LinkedIn").capitalize()[:50],
                url=job.get("url", ""),
                discovered_date=job.get("date_posted", datetime.now().strftime("%Y-%m-%d"))
            )
            added += 1
        except Exception as e:
            print(f"[notion_sync] ERROR adding job {job.get('title','?')}: {e}")

    print(f"[notion_sync] {added}/{len(jobs_list)} new jobs synced to Notion")
    return added


def sync_content_status(post_title, new_status, date_str=None):
    """
    Update a content calendar item's status (e.g., 'Drafted' -> 'Posted').
    """
    nc = _get_client()
    if not nc:
        return False

    try:
        # Query content calendar for matching title
        results = nc._query_database("content_calendar")
        for row in results:
            props = row.get("properties", {})
            title_prop = props.get("Title", {}).get("title", [])
            if title_prop and post_title.lower() in title_prop[0].get("text", {}).get("content", "").lower():
                nc._update_page(row["id"], {
                    "Status": {"select": {"name": new_status}}
                })
                print(f"[notion_sync] Content '{post_title}' -> {new_status}")
                return True
        print(f"[notion_sync] Content not found: {post_title}")
        return False
    except Exception as e:
        print(f"[notion_sync] ERROR updating content status: {e}")
        return False


def sync_system_event(event, severity="Info", component="Gateway", details="", auto_fixed=False):
    """Log a system event to Notion System Log."""
    nc = _get_client()
    if not nc:
        return None
    try:
        return nc.log_event(event, severity=severity, component=component,
                           details=details, auto_fixed=auto_fixed)
    except Exception as e:
        print(f"[notion_sync] ERROR logging event: {e}")
        return None


def sync_dossier(title, company, ats_score=None, verdict=None, location="",
                 top_matches="", top_gaps=""):
    """Push a job dossier analysis to Notion."""
    nc = _get_client()
    if not nc:
        return None
    try:
        return nc.add_dossier(title, company, ats_score=ats_score, verdict=verdict,
                             location=location, top_matches=top_matches, top_gaps=top_gaps)
    except Exception as e:
        print(f"[notion_sync] ERROR adding dossier: {e}")
        return None


def backfill_briefings(days=14):
    """
    Create Notion briefing entries from historical briefing JSONs.
    Looks for /tmp/briefing-*.json and jobs-bank/scraped/scanner-*.json files.
    """
    nc = _get_client()
    if not nc:
        return 0

    workspace = "/root/.openclaw/workspace"
    created = 0
    cairo = timezone(timedelta(hours=2))

    # Check what dates already exist in Notion
    existing = set()
    try:
        results = nc._query_database("daily_briefings")
        for row in results:
            props = row.get("properties", {})
            date_prop = props.get("Date", {}).get("date", {})
            if date_prop and date_prop.get("start"):
                existing.add(date_prop["start"])
    except:
        pass

    # Look for briefing JSONs
    json_files = sorted(glob.glob(f"/tmp/briefing-*.json") + 
                       glob.glob(f"{workspace}/jobs-bank/scraped/briefing-*.json"))

    for jf in json_files:
        try:
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(jf))
            if not date_match:
                continue
            date_str = date_match.group(1)
            if date_str in existing:
                continue

            with open(jf) as f:
                data = json.load(f)

            url = sync_briefing(briefing_data=data, date_str=date_str)
            if url:
                created += 1
                existing.add(date_str)
        except Exception as e:
            print(f"[notion_sync] Backfill error for {jf}: {e}")

    # Also create skeleton entries for recent dates with no JSON
    now = datetime.now(cairo)
    for days_ago in range(1, days + 1):
        d = now - timedelta(days=days_ago)
        date_str = d.strftime("%Y-%m-%d")
        day_name = d.strftime("%A")

        if date_str in existing:
            continue

        # Check memory log for this date
        mem_file = f"{workspace}/memory/{date_str}.md"
        mem_content = ""
        if os.path.exists(mem_file):
            with open(mem_file) as f:
                mem_content = f.read()[:3000]

        if not mem_content:
            continue  # No data for this day, skip

        try:
            briefing = nc.add_briefing(
                date=date_str,
                jobs_found=0,
                priority_picks=0,
                emails_flagged=0,
                calendar_events=0,
                linkedin_impressions=0,
                system_health="Historical",
                model_used="Backfill",
                status="Historical"
            )

            # Add memory content as blocks
            blocks = [
                nc.callout_block(f"Historical entry from memory log ({day_name})", "📁"),
                nc.divider_block(),
            ]

            # Parse memory sections
            sections = re.split(r'^##\s+', mem_content, flags=re.MULTILINE)
            for section in sections[:10]:
                lines = section.strip().split('\n')
                if not lines:
                    continue
                heading = lines[0].strip()
                if heading:
                    blocks.append(nc.heading_block(heading[:100], 2))
                for line in lines[1:15]:
                    line = line.strip()
                    if line.startswith('- '):
                        blocks.append(nc.bullet_block(line[2:][:200]))
                    elif line and not line.startswith('#') and not line.startswith('---'):
                        blocks.append(nc.paragraph_block(line[:2000]))

            nc._append_blocks(briefing["id"], blocks[:90])
            created += 1
            existing.add(date_str)
            print(f"[notion_sync] Backfilled {date_str} from memory log")

        except Exception as e:
            print(f"[notion_sync] Backfill error for {date_str}: {e}")

    print(f"[notion_sync] Backfill complete: {created} briefings created")
    return created


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Notion Sync Module")
    parser.add_argument("--backfill", type=int, default=0, help="Backfill N days of briefings")
    parser.add_argument("--test", action="store_true", help="Run sync test")
    args = parser.parse_args()

    if args.backfill:
        count = backfill_briefings(args.backfill)
        print(f"Backfilled {count} briefings")
    elif args.test:
        nc = _get_client()
        if nc:
            print("✅ Notion client connected")
            sync_system_event("Notion sync module test", component="Briefing", details="Manual test run")
            print("✅ Test event logged")
        else:
            print("❌ Notion client failed")
