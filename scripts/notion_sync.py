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

        # Jobs section with scanner health
        blocks.append(nc.heading_block("💼 Job Scanner", 2))

        # Scanner health summary
        scanner_meta = briefing_data.get("scanner_meta")
        if scanner_meta:
            searches = scanner_meta.get("total_searches", "?")
            countries = len(scanner_meta.get("countries", []))
            total = scanner_meta.get("total_found", 0)
            src_status = scanner_meta.get("source_status", {})
            src_line = " | ".join(f"{k}: {v}" for k, v in src_status.items())
            cookie_age = scanner_meta.get("cookie_age_days", "?")
            runtime = scanner_meta.get("runtime_seconds", "?")

            blocks.append(nc.callout_block(
                f"Searches: {searches} | Countries: {countries} | Found: {total} | Runtime: {runtime}s\n{src_line} | Cookie: {cookie_age}d old",
                "🔍"
            ))
            if scanner_meta.get("degraded"):
                blocks.append(nc.callout_block("⚠️ DEGRADED: Low results, possible rate limit or cookie expiry", "⚠️"))
            if scanner_meta.get("validation_warnings"):
                for w in scanner_meta["validation_warnings"]:
                    blocks.append(nc.bullet_block(f"⚠️ {w}"))
        else:
            scanner_note = jobs_section.get("scanner_note", "No scanner data")
            blocks.append(nc.paragraph_block(str(scanner_note)[:2000]))

        # Priority picks with JD summary
        if qualified:
            blocks.append(nc.heading_block("🟢 Priority Picks", 3))
            for j in qualified[:15]:
                title = j.get("title", "Unknown")
                company = j.get("company", "Unknown")
                ats = j.get("ats_score", "N/A")
                location = j.get("location", "")
                url = j.get("link", j.get("url", ""))
                jd_snippet = j.get("jd_snippet", j.get("description", ""))

                line = f"{title} @ {company} — {location} (ATS: {ats}%)"
                blocks.append(nc.bullet_block(line[:200]))
                if jd_snippet:
                    blocks.append(nc.paragraph_block(f"  \"{jd_snippet[:300]}\""))
                if url:
                    blocks.append(nc.paragraph_block(f"  → {url}"))

        # Borderline (Notion only, not in Telegram)
        if borderline:
            blocks.append(nc.heading_block("🟡 Borderline (75-81%)", 3))
            for j in borderline[:10]:
                title = j.get("title", "Unknown")
                company = j.get("company", "Unknown")
                ats = j.get("ats_score", "N/A")
                location = j.get("location", "")
                url = j.get("link", j.get("url", ""))
                blocks.append(nc.bullet_block(f"{title} @ {company} — {location} (ATS: {ats}%) → {url}"[:200]))

        blocks.append(nc.divider_block())

        # Pipeline
        blocks.append(nc.heading_block("📊 Pipeline", 2))
        p_applied = pipeline.get("applied", 0)
        p_interview = pipeline.get("interviews", 0)
        p_closed = pipeline.get("closed", 0)
        p_stale = pipeline.get("stale", 0)
        p_total = pipeline.get("total_applications", 0)

        # Summary callout
        blocks.append(nc.callout_block(
            f"Total: {p_total} | Applied: {p_applied} | Interview: {p_interview} | Closed: {p_closed} | Stale (14d+): {p_stale}",
            "📊"
        ))

        # Interview alert (prominent)
        if p_interview > 0:
            blocks.append(nc.callout_block(f"🎯 {p_interview} active interview(s) in pipeline!", "🎯"))

        # Overdue follow-ups (the actionable part)
        p_overdue = pipeline.get("overdue", [])
        if p_overdue:
            blocks.append(nc.heading_block("⏰ Follow-ups Overdue", 3))
            blocks.append(nc.paragraph_block(f"{len(p_overdue)} applications with no response after 14+ days:"))
            for o in p_overdue[:20]:
                days = o.get("days", 0)
                urgency = "🔴" if days >= 21 else "🟡"
                blocks.append(nc.bullet_block(
                    f"{urgency} {o['company']} — {o['role']} — applied {o['applied']} ({days}d ago)"[:200]
                ))
            if len(p_overdue) > 20:
                blocks.append(nc.paragraph_block(f"... and {len(p_overdue) - 20} more"))

            # Recommendation
            top3 = p_overdue[:3]
            if top3:
                names = ", ".join(o["company"] for o in top3)
                blocks.append(nc.callout_block(
                    f"Recommended action: Send follow-up messages to {names} (oldest, highest urgency)",
                    "💡"
                ))
        else:
            blocks.append(nc.paragraph_block("No overdue follow-ups. All applications within 14-day window."))

        blocks.append(nc.divider_block())

        # Calendar
        blocks.append(nc.heading_block("📅 Calendar", 2))
        cal_err = briefing_data.get("cal_error")
        if cal_err:
            blocks.append(nc.callout_block(f"⚠️ Calendar offline: {cal_err}", "⚠️"))
        elif cal_events:
            blocks.append(nc.heading_block("Today", 3))
            for ev in cal_events[:8]:
                if isinstance(ev, dict):
                    t = ev.get("time", "")
                    title = ev.get("title", "")
                    notes = ev.get("notes", "")
                    line = f"{t}: {title}" if t else title
                    blocks.append(nc.bullet_block(line[:200]))
                    if notes:
                        blocks.append(nc.paragraph_block(f"  {notes[:300]}"))
                else:
                    blocks.append(nc.bullet_block(str(ev)[:200]))

            # Upcoming 3 days
            cal_upcoming = briefing_data.get("calendar", {}).get("upcoming", [])
            if cal_upcoming:
                blocks.append(nc.heading_block("Next 3 Days", 3))
                for item in cal_upcoming[:8]:
                    blocks.append(nc.bullet_block(str(item)[:200]))
        else:
            blocks.append(nc.paragraph_block("Clear day, no events scheduled. ✅"))
        blocks.append(nc.divider_block())

        # LinkedIn
        blocks.append(nc.heading_block("📱 LinkedIn", 2))

        GITHUB_RAW_BASE = "https://raw.githubusercontent.com/ahmednasr999/openclaw-workspace/master"
        GITHUB_BLOB_BASE = "https://github.com/ahmednasr999/openclaw-workspace/blob/master"

        # Today's post
        if todays_post and todays_post.get("title"):
            post_title = todays_post.get("title", "")
            post_status = todays_post.get("status", "drafted")
            post_content = todays_post.get("content", "")
            blocks.append(nc.heading_block(f"Today's Post: {post_title}", 3))
            blocks.append(nc.callout_block(f"Status: {post_status}", "📝"))

            # Embed post image if exists
            import glob as _glob
            date_str_local = date_str  # from outer scope
            image_patterns = [
                f"/root/.openclaw/workspace/linkedin/posts/{date_str_local}*.png",
                f"/root/.openclaw/workspace/linkedin/posts/{date_str_local}*.jpg",
            ]
            for pat in image_patterns:
                for img_path in _glob.glob(pat):
                    rel_path = img_path.replace("/root/.openclaw/workspace/", "")
                    img_url = f"{GITHUB_RAW_BASE}/{rel_path}"
                    blocks.append(nc.image_block(img_url, f"Post image: {os.path.basename(img_path)}"))

            # Post content
            if post_content:
                for chunk_start in range(0, min(len(post_content), 4000), 2000):
                    blocks.append(nc.paragraph_block(post_content[chunk_start:chunk_start+2000]))

            # GitHub link to post file
            post_file = todays_post.get("file", "")
            if not post_file:
                # Try to find it
                for f in sorted(os.listdir("/root/.openclaw/workspace/linkedin/posts/"), reverse=True):
                    if date_str_local in f and f.endswith(".md"):
                        post_file = f"linkedin/posts/{f}"
                        break
            if post_file:
                github_url = f"{GITHUB_BLOB_BASE}/{post_file}"
                blocks.append(nc.bookmark_block(github_url, f"View on GitHub: {post_file}"))
        else:
            blocks.append(nc.paragraph_block("No post scheduled today."))

        # Engagement targets
        if comments:
            blocks.append(nc.heading_block("💬 Engagement Targets", 3))
            blocks.append(nc.paragraph_block(f"{len(comments)} posts identified for strategic commenting:"))
            for c in comments[:8]:
                author = c.get("author", "Unknown")
                topic = c.get("topic", c.get("snippet", ""))[:150]
                url = c.get("url", "")
                ready_comment = c.get("ready_comment", "")
                blocks.append(nc.bullet_block(f"{author}: {topic}"[:200]))
                if url:
                    blocks.append(nc.paragraph_block(f"  → {url}"))
                if ready_comment:
                    blocks.append(nc.paragraph_block(f"  Draft: \"{ready_comment[:300]}\""))
        blocks.append(nc.divider_block())

        # System health
        blocks.append(nc.heading_block("⚙️ System Health", 2))

        # Went right
        went_right_list = briefing_data.get("went_right", [])
        if went_right_list:
            blocks.append(nc.heading_block("✅ Completed", 3))
            for item in went_right_list[:10]:
                blocks.append(nc.bullet_block(f"✅ {item}"[:200]))

        # Errors
        if errors_list:
            blocks.append(nc.heading_block("❌ Errors", 3))
            for e in errors_list:
                issue = e.get("issue", str(e))
                fix = e.get("fix", "")
                line = f"❌ {issue}"
                if fix:
                    line += f" — Fix: {fix}"
                blocks.append(nc.bullet_block(line[:200]))
        else:
            blocks.append(nc.callout_block("All systems operational. No errors detected.", "✅"))
        blocks.append(nc.divider_block())

        # Action items callout (summary)
        action_items = []
        if qualified:
            action_items.append(f"Review {len(qualified)} new priority picks")
        p_overdue = pipeline.get("overdue", [])
        if p_overdue:
            action_items.append(f"Follow up on {len(p_overdue)} stale applications")
        if comments:
            action_items.append(f"Post {len(comments)} engagement comments")
        if todays_post and todays_post.get("title"):
            action_items.append("Review and publish today's LinkedIn post")
        if action_items:
            blocks.append(nc.heading_block("⚡ Today's Action Items", 2))
            for ai in action_items:
                blocks.append(nc.bullet_block(f"☐ {ai}"))
            blocks.append(nc.divider_block())

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
    jobs_list: list of dicts with keys: title, company, location, url, ats_score, site, applied_date
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
                discovered_date=job.get("date_posted", datetime.now().strftime("%Y-%m-%d")),
                applied_date=job.get("applied_date")  # Pass through if available
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


def read_pipeline_from_notion():
    """
    Two-way sync: Read pipeline from Notion and detect changes vs local pipeline.md.
    Returns dict with: jobs (list), changes (list of dicts with company, field, old, new).
    """
    nc = _get_client()
    if not nc:
        return {"jobs": [], "changes": []}

    # Stage mapping: Notion emoji stages -> pipeline.md stages
    notion_to_local = {
        "🔍 Discovered": "🔍 Discovered",
        "📋 Scored": "📋 Scored",
        "📄 CV Ready": "📄 CV Ready",
        "✅ Applied": "✅ Applied",
        "📞 Interview": "📞 Interview",
        "🤝 Offer": "🤝 Offer",
        "❌ Rejected": "❌ Rejected",
        "⏸️ Stale": "⏸️ Stale",
        "❌ Closed": "❌ Closed",
    }

    workspace = "/root/.openclaw/workspace"

    try:
        # Read all Notion pipeline entries
        results = nc._query_database("job_pipeline")
        notion_jobs = {}

        def _title(props, key):
            t = props.get(key, {}).get("title", [])
            return t[0].get("plain_text", "") if t else ""

        def _text(props, key):
            t = props.get(key, {}).get("rich_text", [])
            return t[0].get("plain_text", "") if t else ""

        def _select(props, key):
            s = props.get(key, {}).get("select")
            return s.get("name", "") if s else ""

        for r in results:
            props = r.get("properties", {})
            company = _title(props, "Company")
            role = _text(props, "Role")
            stage_name = _select(props, "Stage")
            ats = props.get("ATS Score", {}).get("number")
            location = _text(props, "Location")
            applied = props.get("Applied Date", {}).get("date")
            applied_str = applied.get("start", "") if applied else ""
            url = props.get("URL", {}).get("url", "") or ""
            notes = _text(props, "Notes")

            if company:
                notion_jobs[company.lower()] = {
                    "company": company,
                    "role": role,
                    "stage": stage_name,
                    "ats": ats,
                    "location": location,
                    "applied": applied_str,
                    "url": url,
                    "notes": notes,
                    "page_id": r["id"],
                }

        # Read local pipeline.md for comparison
        local_jobs = {}
        pipeline_path = os.path.join(workspace, "jobs-bank", "pipeline.md")
        if os.path.exists(pipeline_path):
            with open(pipeline_path) as f:
                for line in f:
                    if "|" not in line or line.strip().startswith("#") or line.strip().startswith("|---"):
                        continue
                    cols = [c.strip() for c in line.split("|")]
                    if len(cols) < 11:
                        continue
                    company = cols[3].replace("~~", "").strip()
                    stage = cols[7].strip()
                    applied = cols[9].replace("~~", "").strip()
                    if company:
                        local_jobs[company.lower()] = {
                            "company": company,
                            "stage": stage,
                            "applied": applied,
                        }

        # Detect changes (Notion is source of truth for stage changes)
        changes = []
        for key, notion_data in notion_jobs.items():
            if key in local_jobs:
                local_data = local_jobs[key]
                # Check stage change
                if notion_data["stage"] and local_data["stage"]:
                    # Normalize for comparison
                    n_stage = notion_data["stage"]
                    l_stage = local_data["stage"]
                    if n_stage != l_stage:
                        changes.append({
                            "company": notion_data["company"],
                            "role": notion_data["role"],
                            "field": "stage",
                            "old": l_stage,
                            "new": n_stage,
                            "page_id": notion_data["page_id"],
                        })

        return {"jobs": list(notion_jobs.values()), "changes": changes}

    except Exception as e:
        print(f"[notion_sync] ERROR reading pipeline from Notion: {e}")
        return {"jobs": [], "changes": []}


def apply_notion_changes_to_pipeline(changes):
    """
    Apply stage changes detected from Notion back to local pipeline.md.
    Returns count of changes applied.
    """
    if not changes:
        return 0

    workspace = "/root/.openclaw/workspace"
    pipeline_path = os.path.join(workspace, "jobs-bank", "pipeline.md")

    if not os.path.exists(pipeline_path):
        print("[notion_sync] pipeline.md not found")
        return 0

    with open(pipeline_path) as f:
        lines = f.readlines()

    applied = 0
    for change in changes:
        company = change["company"]
        new_stage = change["new"]

        for i, line in enumerate(lines):
            if "|" not in line:
                continue
            # Match company name (with or without strikethrough)
            clean_line = line.replace("~~", "")
            if company.lower() in clean_line.lower():
                cols = line.split("|")
                if len(cols) > 7:
                    old_stage = cols[7].strip()
                    cols[7] = f" {new_stage} "
                    lines[i] = "|".join(cols)
                    print(f"[notion_sync] Pipeline updated: {company} | {old_stage} -> {new_stage}")
                    applied += 1
                break

    if applied:
        with open(pipeline_path, "w") as f:
            f.writelines(lines)
        print(f"[notion_sync] {applied} changes written to pipeline.md")

    return applied




def sync_email_digest(emails, date_str=None):
    """
    Push flagged/important emails to Notion System Log as email events.
    emails: list of dicts with keys: from, subject, snippet, date, flagged, category
    """
    nc = _get_client()
    if not nc:
        return 0
    
    if not date_str:
        date_str = datetime.now(timezone(timedelta(hours=2))).strftime("%Y-%m-%d")
    
    synced = 0
    for email in emails:
        try:
            subject = email.get("subject", "No subject")[:100]
            sender = email.get("from", "Unknown")[:100]
            snippet = email.get("snippet", "")[:500]
            category = email.get("category", "Email")
            
            severity = "Info"
            if email.get("flagged") or email.get("important"):
                severity = "Warning"
            if "interview" in subject.lower() or "offer" in subject.lower():
                severity = "Critical"
            
            nc.log_event(
                f"Email: {subject}",
                severity=severity,
                component="Email",
                details=f"From: {sender}\n{snippet}",
            )
            synced += 1
        except Exception as e:
            print(f"[notion_sync] ERROR syncing email: {e}")
    
    print(f"[notion_sync] {synced}/{len(emails)} emails synced to System Log")
    return synced


def sync_scanner_run(meta_data, date_str=None):
    """
    Push scanner run metadata to Scanner History database.
    """
    nc = _get_client()
    if not nc:
        return None
    
    if not date_str:
        date_str = datetime.now(timezone(timedelta(hours=2))).strftime("%Y-%m-%d")
    
    nc.databases["scanner_history"] = "3268d599-a162-8123-a867-d7231817f03d"
    
    searches = meta_data.get("total_searches", 0)
    found = meta_data.get("total_found", 0)
    picks = meta_data.get("priority_picks", 0)
    leads = meta_data.get("exec_leads", 0)
    filtered = meta_data.get("filtered_out", 0)
    runtime = meta_data.get("runtime_seconds", 0)
    cookie_age = meta_data.get("cookie_age_days")
    
    status = "✅ Healthy"
    if found == 0:
        status = "❌ Failed"
    elif meta_data.get("degraded"):
        status = "⚠️ Degraded"
    
    warnings = "; ".join(meta_data.get("validation_warnings", []))[:200]
    sources = " ".join(f"{k}:{v}" for k, v in meta_data.get("source_status", {}).items())[:200]
    
    props = {
        "Date": {"title": [{"text": {"content": date_str}}]},
        "Searches": {"number": searches},
        "Jobs Found": {"number": found},
        "Priority Picks": {"number": picks},
        "Exec Leads": {"number": leads},
        "Filtered Out": {"number": filtered},
        "Runtime (sec)": {"number": runtime},
        "Status": {"select": {"name": status}},
    }
    if cookie_age is not None:
        props["Cookie Age"] = {"number": cookie_age}
    if warnings:
        props["Warnings"] = {"rich_text": [{"text": {"content": warnings}}]}
    if sources:
        props["Sources"] = {"rich_text": [{"text": {"content": sources}}]}
    
    try:
        page = nc._create_page("scanner_history", props)
        print(f"[notion_sync] Scanner run synced: {date_str}")
        return page
    except Exception as e:
        print(f"[notion_sync] ERROR syncing scanner run: {e}")
        return None


def sync_active_tasks(tasks_data):
    """
    Two-way sync for active tasks.
    Reads Notion tasks, compares with local, syncs changes.
    tasks_data: list of dicts with: text, done, priority, category
    """
    nc = _get_client()
    if not nc:
        return {"synced": 0, "changes": []}
    
    nc.databases["active_tasks"] = "3268d599-a162-8152-9036-e4e4a85d444d"
    
    # Read Notion tasks
    results = nc._query_database("active_tasks")
    notion_tasks = {}
    for r in results:
        props = r.get("properties", {})
        t = props.get("Task", {}).get("title", [])
        text = t[0].get("plain_text", "") if t else ""
        done = props.get("Done", {}).get("checkbox", False)
        if text:
            notion_tasks[text.lower()[:50]] = {"done": done, "page_id": r["id"], "text": text}
    
    changes = []
    for nt_key, nt_data in notion_tasks.items():
        # If task was marked done in Notion, flag it
        if nt_data["done"]:
            changes.append({"task": nt_data["text"], "action": "completed_in_notion"})
    
    return {"synced": len(notion_tasks), "changes": changes}


def sync_cron_status():
    """
    Update Cron Dashboard with latest status from OpenClaw.
    """
    nc = _get_client()
    if not nc:
        return 0
    
    nc.databases["cron_dashboard"] = "3268d599-a162-8188-b531-e25071653203"
    
    import json
    try:
        with open("/root/.openclaw/cron/jobs.json") as f:
            data = json.load(f)
        jobs = data.get("jobs", [])
    except:
        return 0
    
    # Get existing dashboard entries
    results = nc._query_database("cron_dashboard")
    existing = {}
    for r in results:
        props = r.get("properties", {})
        cron_id_t = props.get("Cron ID", {}).get("rich_text", [])
        cron_id = cron_id_t[0].get("plain_text", "") if cron_id_t else ""
        if cron_id:
            existing[cron_id] = r["id"]
    
    updated = 0
    for job in jobs:
        jid = job.get("id", "")
        if jid not in existing:
            continue
        
        state = job.get("state", {})
        last_status = state.get("lastStatus", "")
        enabled = job.get("enabled", False)
        
        status_name = "✅ OK"
        if not enabled:
            status_name = "⏸️ Disabled"
        elif last_status == "error" or state.get("consecutiveErrors", 0) > 0:
            status_name = "❌ Failed"
        
        last_run_ms = state.get("lastRunAtMs", 0)
        props = {"Last Status": {"select": {"name": status_name}}}
        if last_run_ms:
            from datetime import datetime as dt2, timezone as tz2
            last_date = dt2.fromtimestamp(last_run_ms / 1000, tz=tz2.utc).strftime("%Y-%m-%d")
            props["Last Run"] = {"date": {"start": last_date}}
        
        try:
            nc._update_page(existing[jid], props)
            updated += 1
        except:
            pass
    
    print(f"[notion_sync] Cron dashboard: {updated} crons updated")
    return updated


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


def audit_learnings_staleness():
    """
    SIE nightly audit: Flag any learning older than 48h still at "Logged" as "Unacted".
    Returns list of flagged entries for alerting.
    """
    nc = _get_client()
    if not nc:
        return []
    
    nc.databases["learnings"] = "3268d599-a162-810f-9f1b-ffdc280ae96d"
    
    results = nc._query_database("learnings")
    
    flagged = []
    now = datetime.now(timezone(timedelta(hours=2)))
    cutoff = now - timedelta(hours=48)
    
    for r in results:
        props = r.get("properties", {})
        status = props.get("Status", {}).get("select", {})
        status_name = status.get("name", "") if status else ""
        
        if status_name != "Logged":
            continue
        
        # Check date
        date_prop = props.get("Date", {}).get("date")
        if not date_prop or not date_prop.get("start"):
            # No date = old entry, flag it
            pass
        else:
            entry_date = datetime.fromisoformat(date_prop["start"].replace("Z", "+00:00"))
            if hasattr(entry_date, 'tzinfo') and entry_date.tzinfo is None:
                entry_date = entry_date.replace(tzinfo=timezone(timedelta(hours=2)))
            if entry_date > cutoff:
                continue  # Too recent, skip
        
        title_arr = props.get("Title", {}).get("title", [])
        title = title_arr[0].get("plain_text", "") if title_arr else "Untitled"
        
        # Flag as Unacted
        try:
            nc._update_page(r["id"], {"Status": {"select": {"name": "Unacted"}}})
            flagged.append(title[:80])
            import time
            time.sleep(0.35)
        except Exception as e:
            print(f"[audit_learnings] ERROR flagging {title[:30]}: {e}")
    
    print(f"[audit_learnings] {len(flagged)} entries flagged as Unacted")
    return flagged


def detect_repeated_learnings():
    """
    Find learnings that appear multiple times (similar titles).
    Updates Times Repeated field.
    """
    nc = _get_client()
    if not nc:
        return []
    
    nc.databases["learnings"] = "3268d599-a162-810f-9f1b-ffdc280ae96d"
    
    results = nc._query_database("learnings")
    
    # Group by normalized title
    title_groups = {}
    for r in results:
        props = r.get("properties", {})
        title_arr = props.get("Title", {}).get("title", [])
        title = title_arr[0].get("plain_text", "").lower().strip() if title_arr else ""
        if not title:
            continue
        
        # Normalize: remove dates, numbers, common prefixes
        import re
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}', '', title)
        normalized = re.sub(r'[^\w\s]', '', normalized).strip()
        # Use first 30 chars as grouping key
        key = normalized[:30]
        
        if key not in title_groups:
            title_groups[key] = []
        title_groups[key].append(r["id"])
    
    repeated = []
    for key, page_ids in title_groups.items():
        if len(page_ids) > 1:
            repeated.append({"key": key, "count": len(page_ids)})
            for pid in page_ids:
                try:
                    nc._update_page(pid, {"Times Repeated": {"number": len(page_ids)}})
                    import time
                    time.sleep(0.35)
                except:
                    pass
    
    print(f"[detect_repeated] Found {len(repeated)} repeated learning patterns")
    return repeated


def two_way_sync_active_tasks():
    """
    Two-way sync between Notion Active Tasks and memory/active-tasks.md.
    1. Read Notion tasks (check for Done ticks, new tasks added by Ahmed)
    2. Read local active-tasks.md
    3. Apply Notion changes to local file
    4. Push local-only items to Notion
    Returns dict with changes for briefing display.
    """
    nc = _get_client()
    if not nc:
        return {"changes": [], "overdue": [], "due_today": []}
    
    nc.databases["active_tasks"] = "3268d599-a162-8152-9036-e4e4a85d444d"
    
    results = nc._query_database("active_tasks")
    
    changes = []
    overdue = []
    due_today = []
    today_str = datetime.now(timezone(timedelta(hours=2))).strftime("%Y-%m-%d")
    
    for r in results:
        props = r.get("properties", {})
        
        # Get task text
        t = props.get("Task", {}).get("title", [])
        text = t[0].get("plain_text", "") if t else ""
        if not text:
            continue
        
        # Check Done status
        done = props.get("Done", {}).get("checkbox", False)
        if done:
            changes.append({"task": text, "action": "completed"})
        
        # Check due date
        due = props.get("Due Date", {}).get("date")
        if due and due.get("start"):
            due_date = due["start"]
            if due_date < today_str and not done:
                overdue.append(text)
            elif due_date == today_str and not done:
                due_today.append(text)
    
    # Update active-tasks.md with completed items
    if changes:
        try:
            with open("/root/.openclaw/workspace/memory/active-tasks.md") as f:
                content = f.read()
            
            for change in changes:
                if change["action"] == "completed":
                    # Mark as done in local file
                    task_text = change["task"]
                    content = content.replace(f"- [ ] {task_text}", f"- [x] {task_text}")
            
            with open("/root/.openclaw/workspace/memory/active-tasks.md", "w") as f:
                f.write(content)
            
            print(f"[active_tasks] Applied {len(changes)} changes from Notion")
        except Exception as e:
            print(f"[active_tasks] ERROR updating local file: {e}")
    
    result = {
        "changes": changes,
        "overdue": overdue,
        "due_today": due_today,
        "total_open": sum(1 for r in results if not r.get("properties", {}).get("Done", {}).get("checkbox", False)),
    }
    
    print(f"[active_tasks] Open: {result['total_open']}, Overdue: {len(overdue)}, Due today: {len(due_today)}, Completed in Notion: {len(changes)}")
    return result


def sync_session_log(date_str=None, title=None, topics=None, decisions=0, 
                     duration=None, focus=None, outcome=None, artifacts=None, content=None):
    """
    Auto-sync a session log to Notion. Called during session flush.
    Creates or updates the session log page for the given date.
    """
    nc = _get_client()
    if not nc:
        return None
    
    nc.databases["session_logs"] = "3268d599-a162-8117-afef-e4910ec15e55"
    
    if not date_str:
        date_str = datetime.now(timezone(timedelta(hours=2))).strftime("%Y-%m-%d")
    
    if not title:
        title = f"Session {date_str}"
    
    # Check if page exists for this date
    results = nc._query_database("session_logs")
    existing_id = None
    for r in results:
        d = r.get("properties", {}).get("Date", {}).get("date")
        if d and d.get("start") == date_str:
            existing_id = r["id"]
            break
    
    # Build properties
    props = {
        "Title": {"title": [{"text": {"content": title[:100]}}]},
        "Date": {"date": {"start": date_str}},
        "Decisions Made": {"number": decisions},
    }
    if topics:
        props["Topics"] = {"multi_select": [{"name": t} for t in topics[:5]]}
    if focus:
        props["Primary Focus"] = {"select": {"name": focus}}
    if duration:
        props["Duration (min)"] = {"number": duration}
    if outcome:
        props["Key Outcome"] = {"rich_text": [{"text": {"content": outcome[:200]}}]}
    if artifacts:
        props["Artifacts"] = {"rich_text": [{"text": {"content": artifacts[:200]}}]}
    
    # Build body blocks from content
    blocks = []
    if content:
        import re
        sections = re.split(r'^##\s+', content, flags=re.MULTILINE)
        for section in sections[:15]:
            lines = section.strip().split("\\n")
            if not lines:
                continue
            heading = lines[0].strip()
            if heading and not heading.startswith("---") and len(heading) > 2:
                blocks.append(nc.heading_block(heading[:100], 2))
            for line in lines[1:25]:
                line = line.strip()
                if line.startswith("- "):
                    blocks.append(nc.bullet_block(line[2:][:200]))
                elif line and not line.startswith("#") and not line.startswith("---") and len(line) > 3:
                    blocks.append(nc.paragraph_block(line[:2000]))
    
    try:
        if existing_id:
            nc._update_page(existing_id, props)
            print(f"[session_log] Updated session log for {date_str}")
            return existing_id
        else:
            page = nc._create_page("session_logs", props, children=blocks[:80])
            print(f"[session_log] Created session log for {date_str}")
            return page.get("id")
    except Exception as e:
        print(f"[session_log] ERROR: {e}")
        return None


def get_scanner_trends():
    """
    Analyze scanner history for trends and degradation.
    Returns trend data for briefing display + updates Notion with trends.
    """
    nc = _get_client()
    if not nc:
        return {"trend": "unknown", "avg_7d": 0, "today": 0, "alert": None}
    
    nc.databases["scanner_history"] = "3268d599-a162-8123-a867-d7231817f03d"
    
    results = nc._query_database("scanner_history")
    
    # Parse all runs with dates and job counts
    runs = []
    for r in results:
        props = r.get("properties", {})
        t = props.get("Date", {}).get("title", [])
        date_str = t[0].get("plain_text", "") if t else ""
        found = props.get("Jobs Found", {}).get("number", 0) or 0
        picks = props.get("Priority Picks", {}).get("number", 0) or 0
        status = props.get("Status", {}).get("select", {})
        status_name = status.get("name", "") if status else ""
        
        if date_str:
            runs.append({
                "date": date_str,
                "found": found,
                "picks": picks,
                "status": status_name,
                "page_id": r["id"],
            })
    
    runs.sort(key=lambda x: x["date"])
    
    if len(runs) < 2:
        return {"trend": "insufficient_data", "avg_7d": 0, "today": 0, "alert": None}
    
    # Calculate 7-day average
    recent_7 = runs[-7:] if len(runs) >= 7 else runs
    avg_found = sum(r["found"] for r in recent_7) / len(recent_7)
    avg_picks = sum(r["picks"] for r in recent_7) / len(recent_7)
    
    # Today vs average
    today = runs[-1]
    today_found = today["found"]
    
    # Trend detection
    trend = "➡️ Stable"
    if len(runs) >= 3:
        last_3 = [r["found"] for r in runs[-3:]]
        if all(last_3[i] < last_3[i-1] for i in range(1, len(last_3))):
            trend = "📉 Down"
        elif all(last_3[i] > last_3[i-1] for i in range(1, len(last_3))):
            trend = "📈 Up"
    
    # Degradation alert
    alert = None
    consecutive_low = 0
    for r in reversed(runs):
        if r["found"] < 10:
            consecutive_low += 1
        else:
            break
    
    if consecutive_low >= 3:
        alert = f"🔴 SCANNER DEGRADED: {consecutive_low} consecutive runs with < 10 jobs. Check cookie freshness!"
    elif consecutive_low >= 2:
        alert = f"🟡 Scanner warning: {consecutive_low} low-result runs in a row"
    
    # Cookie health check
    import os
    cookie_alert = None
    cookie_path = "/root/.openclaw/cookies/linkedin.txt"
    if os.path.exists(cookie_path):
        cookie_age = (datetime.now().timestamp() - os.path.getmtime(cookie_path)) / 86400
        if cookie_age > 7:
            cookie_alert = f"🟡 LinkedIn cookie is {int(cookie_age)} days old. Refresh recommended."
    
    # Update Notion with trend and 7-day avg
    import time as t_mod
    for r in runs[-3:]:
        try:
            nc._update_page(r["page_id"], {
                "7-Day Avg": {"number": round(avg_found, 1)},
                "Trend": {"select": {"name": trend}},
            })
            t_mod.sleep(0.35)
        except:
            pass
    
    result = {
        "trend": trend,
        "trend_direction": "down" if "Down" in trend else "up" if "Up" in trend else "stable",
        "avg_7d_found": round(avg_found, 1),
        "avg_7d_picks": round(avg_picks, 1),
        "today_found": today_found,
        "today_picks": today["picks"],
        "total_runs": len(runs),
        "alert": alert,
        "cookie_alert": cookie_alert,
        "consecutive_low": consecutive_low,
    }
    
    print(f"[scanner_trends] Trend: {trend}, 7d avg: {avg_found:.0f} jobs, Today: {today_found}, Alert: {alert or 'None'}")
    return result


def sync_cron_dashboard_full():
    """
    Full cron dashboard sync: status, errors, duration, cost tier.
    Called by heartbeat to keep dashboard live.
    Returns health summary for briefing.
    """
    nc = _get_client()
    if not nc:
        return {"ok": 0, "failed": 0, "disabled": 0, "failures": []}
    
    nc.databases["cron_dashboard"] = "3268d599-a162-8188-b531-e25071653203"
    
    import json as json_mod
    import time as t_mod
    
    try:
        with open("/root/.openclaw/cron/jobs.json") as f:
            data = json_mod.load(f)
        jobs = data.get("jobs", [])
    except:
        return {"ok": 0, "failed": 0, "disabled": 0, "failures": []}
    
    # Get existing dashboard entries by cron ID
    results = nc._query_database("cron_dashboard")
    existing = {}
    for r in results:
        props = r.get("properties", {})
        cron_id_t = props.get("Cron ID", {}).get("rich_text", [])
        cron_id = cron_id_t[0].get("plain_text", "") if cron_id_t else ""
        if cron_id:
            existing[cron_id] = r["id"]
    
    # Cost tier mapping
    def get_cost_tier(model_str):
        if not model_str:
            return "🟢 Free (MiniMax)"
        m = model_str.lower()
        if "opus" in m:
            return "💰 Premium (Opus)"
        elif "sonnet" in m:
            return "🔵 Standard (Sonnet)"
        elif "gpt" in m or "codex" in m:
            return "🟡 Codex (GPT)"
        elif "haiku" in m:
            return "⚪ Light (Haiku)"
        return "🟢 Free (MiniMax)"
    
    ok_count = 0
    failed_count = 0
    disabled_count = 0
    failures = []
    
    for job in jobs:
        jid = job.get("id", "")
        name = job.get("name", "Unknown")[:100]
        enabled = job.get("enabled", False)
        state = job.get("state", {})
        last_status = state.get("lastStatus", "")
        consecutive_errors = state.get("consecutiveErrors", 0)
        last_error = state.get("lastError", "")
        last_duration_ms = state.get("lastDurationMs", 0)
        last_run_ms = state.get("lastRunAtMs", 0)
        payload = job.get("payload", {})
        model = payload.get("model", "")
        
        # Status
        if not enabled:
            status_name = "⏸️ Disabled"
            disabled_count += 1
        elif consecutive_errors > 0 or last_status == "error":
            status_name = "❌ Failed"
            failed_count += 1
            failures.append({
                "name": name,
                "error": last_error[:100] if last_error else "Unknown",
                "consecutive": consecutive_errors,
            })
        else:
            status_name = "✅ OK"
            ok_count += 1
        
        # Build update
        props = {
            "Last Status": {"select": {"name": status_name}},
            "Enabled": {"checkbox": enabled},
            "Consecutive Errors": {"number": consecutive_errors},
            "Cost Tier": {"select": {"name": get_cost_tier(model)}},
        }
        
        if last_duration_ms:
            props["Last Duration (sec)"] = {"number": round(last_duration_ms / 1000, 1)}
        
        if last_error:
            props["Last Error"] = {"rich_text": [{"text": {"content": last_error[:2000]}}]}
        
        if last_run_ms:
            dt = datetime.fromtimestamp(last_run_ms / 1000, tz=timezone(timedelta(hours=0)))
            props["Last Run"] = {"date": {"start": dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")}}
        
        page_id = existing.get(jid)
        if page_id:
            try:
                nc._update_page(page_id, props)
                t_mod.sleep(0.35)
            except Exception as e:
                print(f"[cron_dashboard] ERROR updating {name[:20]}: {e}")
        else:
            # New cron not in dashboard yet, create it
            schedule = job.get("schedule", {})
            cron_expr = schedule.get("expr", "")
            tz = schedule.get("tz", "UTC")
            timeout = payload.get("timeoutSeconds", 30)
            
            # Category
            category = "Other"
            nl = name.lower()
            if "briefing" in nl or "morning" in nl: category = "Briefing"
            elif "scanner" in nl or "job" in nl or "radar" in nl: category = "Scanner"
            elif "linkedin" in nl or "content" in nl or "engagement" in nl: category = "LinkedIn"
            elif "email" in nl: category = "Email"
            elif "heartbeat" in nl or "system" in nl or "audit" in nl or "sie" in nl: category = "System"
            
            # Model name
            model_name = None
            if model:
                if "minimax" in model.lower(): model_name = "minimax-m2.5"
                elif "opus" in model.lower(): model_name = "opus46"
                elif "sonnet" in model.lower(): model_name = "sonnet46"
                elif "gpt" in model.lower(): model_name = "gpt54"
                elif "haiku" in model.lower(): model_name = "haiku"
            
            create_props = {
                "Name": {"title": [{"text": {"content": name}}]},
                "Schedule": {"rich_text": [{"text": {"content": f"{cron_expr} ({tz})"[:200]}}]},
                "Cron ID": {"rich_text": [{"text": {"content": jid}}]},
                "Timeout": {"number": timeout},
                "Category": {"select": {"name": category}},
            }
            create_props.update(props)
            if model_name:
                create_props["Model"] = {"select": {"name": model_name}}
            
            try:
                nc._create_page("cron_dashboard", create_props)
                t_mod.sleep(0.35)
            except Exception as e:
                print(f"[cron_dashboard] ERROR creating {name[:20]}: {e}")
    
    summary = {
        "total": ok_count + failed_count + disabled_count,
        "ok": ok_count,
        "failed": failed_count,
        "disabled": disabled_count,
        "failures": failures,
    }
    
    print(f"[cron_dashboard] Total: {summary['total']}, OK: {ok_count}, Failed: {failed_count}, Disabled: {disabled_count}")
    return summary


def sync_email_to_notion(subject, sender, date_str, category, company="", role="",
                         priority="🟡 Normal", snippet="", gmail_link="", thread_id="",
                         action_required=False, response_due=None, pipeline_stage=None):
    """
    Sync a single email to Notion Email Intelligence DB.
    Called by email cron when it finds important emails.
    """
    nc = _get_client()
    if not nc:
        return None
    
    nc.databases["email_intelligence"] = "3278d599-a162-8123-923c-f04999d7292d"
    
    # Check for duplicates by thread ID
    if thread_id:
        results = nc._query_database("email_intelligence")
        for r in results:
            tid = r.get("properties", {}).get("Thread ID", {}).get("rich_text", [])
            if tid and tid[0].get("plain_text", "") == thread_id:
                print(f"[email] Duplicate thread {thread_id}, skipping")
                return r["id"]
    
    props = {
        "Subject": {"title": [{"text": {"content": subject[:100]}}]},
        "From": {"rich_text": [{"text": {"content": sender[:200]}}]},
        "Date": {"date": {"start": date_str}},
        "Category": {"select": {"name": category}},
        "Priority": {"select": {"name": priority}},
        "Status": {"select": {"name": "📬 Unread"}},
        "Action Required": {"checkbox": action_required},
        "Auto-Synced": {"checkbox": True},
    }
    
    if company:
        props["Company"] = {"rich_text": [{"text": {"content": company[:200]}}]}
    if role:
        props["Role"] = {"rich_text": [{"text": {"content": role[:200]}}]}
    if snippet:
        props["Snippet"] = {"rich_text": [{"text": {"content": snippet[:2000]}}]}
    if gmail_link:
        props["Gmail Link"] = {"url": gmail_link}
    if thread_id:
        props["Thread ID"] = {"rich_text": [{"text": {"content": thread_id}}]}
    if response_due:
        props["Response Due"] = {"date": {"start": response_due}}
    if pipeline_stage:
        props["Pipeline Stage"] = {"select": {"name": pipeline_stage}}
    
    try:
        page = nc._create_page("email_intelligence", props)
        print(f"[email] Synced: {subject[:50]}")
        return page.get("id")
    except Exception as e:
        print(f"[email] ERROR: {e}")
        return None


def get_email_summary():
    """
    Get email intelligence summary for morning briefing.
    Returns counts by category and action items.
    """
    nc = _get_client()
    if not nc:
        return {"total": 0, "unread": 0, "action_needed": 0, "urgent": []}
    
    nc.databases["email_intelligence"] = "3278d599-a162-8123-923c-f04999d7292d"
    
    results = nc._query_database("email_intelligence")
    
    unread = 0
    action_needed = 0
    urgent = []
    by_category = {}
    
    for r in results:
        props = r.get("properties", {})
        
        status = props.get("Status", {}).get("select", {})
        status_name = status.get("name", "") if status else ""
        
        cat = props.get("Category", {}).get("select", {})
        cat_name = cat.get("name", "") if cat else ""
        
        priority = props.get("Priority", {}).get("select", {})
        priority_name = priority.get("name", "") if priority else ""
        
        action = props.get("Action Required", {}).get("checkbox", False)
        
        subject_t = props.get("Subject", {}).get("title", [])
        subject = subject_t[0].get("plain_text", "") if subject_t else ""
        
        if "Unread" in status_name:
            unread += 1
        if action:
            action_needed += 1
        if "Urgent" in priority_name:
            urgent.append(subject[:50])
        
        by_category[cat_name] = by_category.get(cat_name, 0) + 1
    
    return {
        "total": len(results),
        "unread": unread,
        "action_needed": action_needed,
        "urgent": urgent,
        "by_category": by_category,
    }
