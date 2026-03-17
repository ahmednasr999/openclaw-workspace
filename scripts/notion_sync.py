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
