#!/usr/bin/env python3
"""
Notion Client for NASR Command Center
======================================
Lightweight wrapper around Notion REST API.
All scripts import this module to read/write Notion databases.

Usage:
    from notion_client import NotionClient
    nc = NotionClient()
    nc.add_job("Acme Corp", "VP Digital", stage="Discovered", ats_score=88)
    nc.add_briefing(date="2026-03-17", jobs_found=42, priority_picks=5)
    rows = nc.query_pipeline(stage="Applied")
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

# Config paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(SCRIPT_DIR)
CONFIG_DIR = os.path.join(WORKSPACE, "config")
TOKEN_FILE = os.path.join(CONFIG_DIR, "notion.json")
DB_FILE = os.path.join(CONFIG_DIR, "notion-databases.json")


class NotionClient:
    """Direct Notion API client. No SDK, no middleware, no dependencies beyond stdlib."""

    def __init__(self, token: Optional[str] = None):
        if token:
            self.token = token
        else:
            with open(TOKEN_FILE) as f:
                self.token = json.load(f)["token"]
        
        with open(DB_FILE) as f:
            config = json.load(f)
            self.databases = {k: v["id"] for k, v in config["databases"].items()}
            self.root_page_id = config["root_page"]["id"]
        
        self.base_url = "https://api.notion.com/v1"
        self.version = "2022-06-28"

    # ─── Low-level API ───────────────────────────────────────────

    def _request(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        """Make a Notion API request."""
        url = f"{self.base_url}/{path}"
        data = json.dumps(body).encode() if body else None
        
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Notion-Version", self.version)
        req.add_header("Content-Type", "application/json")
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise Exception(f"Notion API {e.code}: {error_body}")

    def _create_page(self, database_key: str, properties: dict) -> dict:
        """Create a page (row) in a database."""
        db_id = self.databases[database_key]
        return self._request("POST", "pages", {
            "parent": {"database_id": db_id},
            "properties": properties
        })

    def _query_database(self, database_key: str, 
                         filter_obj: Optional[dict] = None,
                         sorts: Optional[list] = None,
                         page_size: int = 100) -> List[dict]:
        """Query a database with optional filter and sort."""
        db_id = self.databases[database_key]
        body: Dict[str, Any] = {"page_size": page_size}
        if filter_obj:
            body["filter"] = filter_obj
        if sorts:
            body["sorts"] = sorts
        
        all_results = []
        while True:
            response = self._request("POST", f"databases/{db_id}/query", body)
            all_results.extend(response["results"])
            if not response.get("has_more"):
                break
            body["start_cursor"] = response["next_cursor"]
        
        return all_results

    def _update_page(self, page_id: str, properties: dict) -> dict:
        """Update a page's properties."""
        return self._request("PATCH", f"pages/{page_id}", {
            "properties": properties
        })

    def _archive_page(self, page_id: str) -> dict:
        """Archive (trash) a page."""
        return self._request("PATCH", f"pages/{page_id}", {
            "archived": True
        })

    def _append_blocks(self, page_id: str, blocks: list) -> dict:
        """Append content blocks to a page."""
        return self._request("PATCH", f"blocks/{page_id}/children", {
            "children": blocks
        })

    # ─── Property Helpers ────────────────────────────────────────

    @staticmethod
    def _title(text: str) -> dict:
        return {"title": [{"text": {"content": text}}]}

    @staticmethod
    def _rich_text(text: str) -> dict:
        return {"rich_text": [{"text": {"content": text[:2000]}}]}  # Notion limit

    @staticmethod
    def _number(n: Optional[float]) -> dict:
        return {"number": n}

    @staticmethod
    def _select(name: str) -> dict:
        return {"select": {"name": name}}

    @staticmethod
    def _date(date_str: str, end_str: Optional[str] = None) -> dict:
        d: Dict[str, Any] = {"date": {"start": date_str}}
        if end_str:
            d["date"]["end"] = end_str
        return d

    @staticmethod
    def _url(url: str) -> dict:
        return {"url": url if url else None}

    @staticmethod
    def _checkbox(checked: bool) -> dict:
        return {"checkbox": checked}

    # ─── Daily Briefings ─────────────────────────────────────────

    def add_briefing(self, *,
                     date: str,
                     jobs_found: int = 0,
                     priority_picks: int = 0,
                     emails_flagged: int = 0,
                     calendar_events: int = 0,
                     linkedin_impressions: int = 0,
                     system_health: str = "✅ All Clear",
                     model_used: str = "",
                     generation_time: float = 0,
                     status: str = "Delivered",
                     content_blocks: Optional[list] = None) -> dict:
        """Add a daily briefing entry."""
        props = {
            "Name": self._title(f"Briefing {date}"),
            "Date": self._date(date),
            "Status": self._select(status),
            "Jobs Found": self._number(jobs_found),
            "Priority Picks": self._number(priority_picks),
            "Emails Flagged": self._number(emails_flagged),
            "Calendar Events": self._number(calendar_events),
            "LinkedIn Impressions": self._number(linkedin_impressions),
            "System Health": self._select(system_health),
            "Model Used": self._rich_text(model_used),
            "Generation Time (s)": self._number(generation_time),
        }
        page = self._create_page("daily_briefings", props)
        
        # Add rich content blocks if provided
        if content_blocks:
            self._append_blocks(page["id"], content_blocks)
        
        return page

    def get_last_briefing(self) -> Optional[dict]:
        """Get the most recent briefing."""
        results = self._query_database(
            "daily_briefings",
            sorts=[{"property": "Date", "direction": "descending"}],
            page_size=1
        )
        return results[0] if results else None

    # ─── Job Pipeline ────────────────────────────────────────────

    def add_job(self, company: str, role: str, *,
                stage: str = "🔍 Discovered",
                ats_score: Optional[int] = None,
                location: str = "",
                salary: str = "",
                source: str = "LinkedIn",
                url: str = "",
                verdict: Optional[str] = None,
                notes: str = "",
                discovered_date: Optional[str] = None) -> dict:
        """Add a job to the pipeline."""
        props: Dict[str, Any] = {
            "Company": self._title(company),
            "Role": self._rich_text(role),
            "Stage": self._select(stage),
            "Source": self._select(source),
        }
        if ats_score is not None:
            props["ATS Score"] = self._number(ats_score)
        if location:
            props["Location"] = self._rich_text(location)
        if salary:
            props["Salary"] = self._rich_text(salary)
        if url:
            props["URL"] = self._url(url)
        if verdict:
            props["Verdict"] = self._select(verdict)
        if notes:
            props["Notes"] = self._rich_text(notes)
        if discovered_date:
            props["Discovered Date"] = self._date(discovered_date)
        else:
            props["Discovered Date"] = self._date(datetime.now().strftime("%Y-%m-%d"))
        
        return self._create_page("job_pipeline", props)

    def update_job_stage(self, page_id: str, stage: str, **kwargs) -> dict:
        """Update a job's stage and optional fields."""
        props: Dict[str, Any] = {"Stage": self._select(stage)}
        if "applied_date" in kwargs:
            props["Applied Date"] = self._date(kwargs["applied_date"])
        if "follow_up_due" in kwargs:
            props["Follow-up Due"] = self._date(kwargs["follow_up_due"])
        if "notes" in kwargs:
            props["Notes"] = self._rich_text(kwargs["notes"])
        if "ats_score" in kwargs:
            props["ATS Score"] = self._number(kwargs["ats_score"])
        return self._update_page(page_id, props)

    def query_pipeline(self, stage: Optional[str] = None,
                        source: Optional[str] = None) -> List[dict]:
        """Query job pipeline with optional filters."""
        filters = []
        if stage:
            filters.append({"property": "Stage", "select": {"equals": stage}})
        if source:
            filters.append({"property": "Source", "select": {"equals": source}})
        
        filter_obj = None
        if len(filters) == 1:
            filter_obj = filters[0]
        elif len(filters) > 1:
            filter_obj = {"and": filters}
        
        return self._query_database(
            "job_pipeline",
            filter_obj=filter_obj,
            sorts=[{"property": "Discovered Date", "direction": "descending"}]
        )

    def find_job(self, company: str, role: str = "") -> Optional[dict]:
        """Find a job by company name (and optionally role)."""
        results = self._query_database(
            "job_pipeline",
            filter_obj={"property": "Company", "title": {"contains": company}}
        )
        if role and results:
            results = [r for r in results 
                      if role.lower() in self._extract_text(r, "Role").lower()]
        return results[0] if results else None

    # ─── Job Dossiers ────────────────────────────────────────────

    def add_dossier(self, title: str, company: str, *,
                    ats_score: int,
                    verdict: str,
                    location: str = "",
                    salary_range: str = "",
                    source_url: str = "",
                    top_matches: str = "",
                    top_gaps: str = "",
                    archetype: str = "",
                    priority_keywords: str = "",
                    content_blocks: Optional[list] = None) -> dict:
        """Add a detailed job dossier."""
        props: Dict[str, Any] = {
            "Title": self._title(title),
            "Company": self._rich_text(company),
            "ATS Score": self._number(ats_score),
            "Verdict": self._select(verdict),
            "Date Analyzed": self._date(datetime.now().strftime("%Y-%m-%d")),
        }
        if location:
            props["Location"] = self._rich_text(location)
        if salary_range:
            props["Salary Range"] = self._rich_text(salary_range)
        if source_url:
            props["Source URL"] = self._url(source_url)
        if top_matches:
            props["Top Matches"] = self._rich_text(top_matches)
        if top_gaps:
            props["Top Gaps"] = self._rich_text(top_gaps)
        if archetype:
            props["Summary Archetype"] = self._select(archetype)
        if priority_keywords:
            props["Priority Keywords"] = self._rich_text(priority_keywords)
        
        page = self._create_page("job_dossiers", props)
        if content_blocks:
            self._append_blocks(page["id"], content_blocks)
        return page

    # ─── CV Tracker ──────────────────────────────────────────────

    def add_cv(self, target_role: str, company: str, *,
               model_used: str = "Opus 4.6",
               ats_score: Optional[int] = None,
               filename: str = "",
               key_modifications: str = "",
               status: str = "Generated") -> dict:
        """Track a generated CV."""
        props: Dict[str, Any] = {
            "Target Role": self._title(target_role),
            "Company": self._rich_text(company),
            "Model Used": self._select(model_used),
            "Date Created": self._date(datetime.now().strftime("%Y-%m-%d")),
            "Status": self._select(status),
        }
        if ats_score is not None:
            props["ATS Score"] = self._number(ats_score)
        if filename:
            props["Filename"] = self._rich_text(filename)
        if key_modifications:
            props["Key Modifications"] = self._rich_text(key_modifications)
        return self._create_page("cv_tracker", props)

    # ─── LinkedIn Analytics ──────────────────────────────────────

    def add_linkedin_post(self, title: str, *,
                          published_date: str,
                          topic: str = "Leadership",
                          impressions: int = 0,
                          likes: int = 0,
                          comments: int = 0,
                          reposts: int = 0,
                          engagement_rate: float = 0,
                          post_url: str = "",
                          notes: str = "") -> dict:
        """Log a LinkedIn post with analytics."""
        props: Dict[str, Any] = {
            "Post Title": self._title(title),
            "Published Date": self._date(published_date),
            "Topic": self._select(topic),
            "Impressions": self._number(impressions),
            "Likes": self._number(likes),
            "Comments": self._number(comments),
            "Reposts": self._number(reposts),
            "Engagement Rate": self._number(engagement_rate),
        }
        if post_url:
            props["Post URL"] = self._url(post_url)
        if notes:
            props["Notes"] = self._rich_text(notes)
        return self._create_page("linkedin_analytics", props)

    def update_linkedin_metrics(self, page_id: str, *,
                                 impressions: int = 0,
                                 likes: int = 0,
                                 comments: int = 0,
                                 reposts: int = 0,
                                 engagement_rate: float = 0) -> dict:
        """Update metrics on an existing LinkedIn post."""
        return self._update_page(page_id, {
            "Impressions": self._number(impressions),
            "Likes": self._number(likes),
            "Comments": self._number(comments),
            "Reposts": self._number(reposts),
            "Engagement Rate": self._number(engagement_rate),
        })

    # ─── Content Calendar ────────────────────────────────────────

    def add_content_idea(self, title: str, *,
                          planned_date: Optional[str] = None,
                          topic: str = "Leadership",
                          status: str = "Idea",
                          hook: str = "",
                          day: Optional[str] = None) -> dict:
        """Add a content idea to the calendar."""
        props: Dict[str, Any] = {
            "Title": self._title(title),
            "Status": self._select(status),
            "Topic": self._select(topic),
        }
        if planned_date:
            props["Planned Date"] = self._date(planned_date)
        if hook:
            props["Hook"] = self._rich_text(hook)
        if day:
            props["Day"] = self._select(day)
        return self._create_page("content_calendar", props)

    def update_content_status(self, page_id: str, status: str, **kwargs) -> dict:
        """Update content item status."""
        props: Dict[str, Any] = {"Status": self._select(status)}
        if "post_url" in kwargs:
            props["Post URL"] = self._url(kwargs["post_url"])
        if "draft" in kwargs:
            props["Draft"] = self._rich_text(kwargs["draft"])
        return self._update_page(page_id, props)

    # ─── System Log ──────────────────────────────────────────────

    def log_event(self, event: str, *,
                   severity: str = "Info",
                   component: str = "Gateway",
                   details: str = "",
                   resolution: str = "",
                   auto_fixed: bool = False) -> dict:
        """Log a system event."""
        props: Dict[str, Any] = {
            "Event": self._title(event),
            "Timestamp": self._date(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")),
            "Severity": self._select(severity),
            "Component": self._select(component),
            "Auto-Fixed": self._checkbox(auto_fixed),
        }
        if details:
            props["Details"] = self._rich_text(details)
        if resolution:
            props["Resolution"] = self._rich_text(resolution)
        return self._create_page("system_log", props)

    # ─── Content Block Helpers ───────────────────────────────────

    @staticmethod
    def heading_block(text: str, level: int = 2) -> dict:
        """Create a heading block (level 1, 2, or 3)."""
        key = f"heading_{level}"
        return {
            "object": "block",
            "type": key,
            key: {"rich_text": [{"text": {"content": text}}]}
        }

    @staticmethod
    def paragraph_block(text: str) -> dict:
        """Create a paragraph block."""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": text[:2000]}}]}
        }

    @staticmethod
    def bullet_block(text: str) -> dict:
        """Create a bulleted list item."""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": text[:2000]}}]}
        }

    @staticmethod
    def divider_block() -> dict:
        """Create a divider."""
        return {"object": "block", "type": "divider", "divider": {}}

    @staticmethod
    def callout_block(text: str, emoji: str = "💡") -> dict:
        """Create a callout block."""
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "icon": {"emoji": emoji},
                "rich_text": [{"text": {"content": text[:2000]}}]
            }
        }

    @staticmethod
    def image_block(url: str, caption: str = "") -> dict:
        """Create an external image block."""
        block = {
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {"url": url},
            }
        }
        if caption:
            block["image"]["caption"] = [{"text": {"content": caption[:2000]}}]
        return block

    @staticmethod
    def bookmark_block(url: str, caption: str = "") -> dict:
        """Create a bookmark block (shows URL preview)."""
        block = {
            "object": "block",
            "type": "bookmark",
            "bookmark": {"url": url}
        }
        if caption:
            block["bookmark"]["caption"] = [{"text": {"content": caption[:2000]}}]
        return block

    # ─── Extraction Helpers ──────────────────────────────────────

    @staticmethod
    def _extract_text(page: dict, prop_name: str) -> str:
        """Extract text from a page property."""
        prop = page.get("properties", {}).get(prop_name, {})
        ptype = prop.get("type", "")
        
        if ptype == "title":
            return "".join(t.get("plain_text", "") for t in prop.get("title", []))
        elif ptype == "rich_text":
            return "".join(t.get("plain_text", "") for t in prop.get("rich_text", []))
        elif ptype == "select":
            sel = prop.get("select")
            return sel.get("name", "") if sel else ""
        elif ptype == "number":
            return str(prop.get("number", ""))
        elif ptype == "date":
            d = prop.get("date")
            return d.get("start", "") if d else ""
        elif ptype == "url":
            return prop.get("url", "") or ""
        elif ptype == "checkbox":
            return str(prop.get("checkbox", False))
        return ""

    def extract_row(self, page: dict, fields: List[str]) -> Dict[str, str]:
        """Extract multiple fields from a page into a dict."""
        return {f: self._extract_text(page, f) for f in fields}


# ─── CLI Testing ─────────────────────────────────────────────────

if __name__ == "__main__":
    nc = NotionClient()
    
    if len(sys.argv) < 2:
        print("Usage: python notion_client.py <command>")
        print("Commands: test, ping, stats")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "ping":
        user = nc._request("GET", "users/me")
        print(f"✅ Connected: {user['name']} @ {user['bot']['workspace_name']}")
    
    elif cmd == "test":
        # Quick integration test
        print("Testing Notion client...")
        
        # Test: add and query a system log entry
        entry = nc.log_event(
            "Integration test",
            severity="Info",
            component="Gateway",
            details="notion_client.py self-test",
            auto_fixed=True
        )
        print(f"  ✅ Created system log entry: {entry['id']}")
        
        # Test: query it back
        results = nc._query_database("system_log", page_size=1)
        if results:
            row = nc.extract_row(results[0], ["Event", "Severity", "Component"])
            print(f"  ✅ Read back: {row}")
        
        # Clean up test entry
        nc._archive_page(entry["id"])
        print(f"  ✅ Cleaned up test entry")
        print("\n✅ All tests passed!")
    
    elif cmd == "stats":
        for db_name, db_id in nc.databases.items():
            results = nc._query_database(db_name, page_size=1)
            # Get count by querying with page_size=100
            all_results = nc._query_database(db_name)
            print(f"  {db_name}: {len(all_results)} rows")
