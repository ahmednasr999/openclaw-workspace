#!/usr/bin/env python3
"""
notion_client_shared.py - Shared Notion API client with retry/backoff.

All Notion operations should go through notion_req() for reliability.
Handles 429 rate limits, 502/503 server errors, and connection timeouts.
Falls back to local JSON if all retries fail.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds
FALLBACK_DIR = Path("/tmp/notion-fallback")


class NotionClient:
    """Lightweight Notion client wrapper. Just holds the token."""
    def __init__(self, token=None):
        if token:
            self.token = token
        else:
            # Auto-load from config
            cfg_path = os.path.expanduser("~/.openclaw/workspace/config/notion.json")
            if os.path.exists(cfg_path):
                with open(cfg_path) as f:
                    self.token = json.load(f)["token"]
            else:
                raise RuntimeError(f"No Notion token provided and {cfg_path} not found")


def get_client(token=None):
    """Get a NotionClient instance. Auto-loads token from config if not provided."""
    return NotionClient(token)


def notion_req(client, method, endpoint, body=None, retries=MAX_RETRIES):
    """Make a Notion API request with exponential backoff retry.
    
    Args:
        client: NotionClient instance (from notion_client.py)
        method: 'get', 'post', 'patch', 'delete'
        endpoint: Notion API endpoint path
        body: Request body dict (for post/patch)
        retries: Max retry count
    
    Returns:
        (response_data, error_string)
        On total failure: saves to local JSON fallback and returns (None, error)
    """
    import requests

    last_error = ""
    for attempt in range(retries):
        try:
            headers = {
                "Authorization": f"Bearer {client.token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            }

            url = f"https://api.notion.com/v1/{endpoint.lstrip('/')}"
            func = getattr(requests, method.lower())

            if body:
                resp = func(url, headers=headers, json=body, timeout=30)
            else:
                resp = func(url, headers=headers, timeout=30)

            if resp.status_code == 200:
                return resp.json(), ""

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", BACKOFF_BASE ** (attempt + 1)))
                print(f"  [notion] 429 rate limit, retrying in {retry_after}s (attempt {attempt+1}/{retries})")
                time.sleep(retry_after)
                continue

            if resp.status_code in (502, 503):
                wait = BACKOFF_BASE ** (attempt + 1)
                print(f"  [notion] {resp.status_code} server error, retrying in {wait}s (attempt {attempt+1}/{retries})")
                time.sleep(wait)
                continue

            last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            break  # Non-retryable error

        except requests.exceptions.Timeout:
            wait = BACKOFF_BASE ** (attempt + 1)
            print(f"  [notion] Timeout, retrying in {wait}s (attempt {attempt+1}/{retries})")
            time.sleep(wait)
            last_error = "Timeout"
        except Exception as e:
            last_error = str(e)
            break

    # All retries failed - save fallback
    if body:
        FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
        fallback_file = FALLBACK_DIR / f"{endpoint.replace('/', '-')}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(fallback_file, "w") as f:
            json.dump({"endpoint": endpoint, "method": method, "body": body, "error": last_error}, f, indent=2, default=str)
        print(f"  [notion] Fallback saved: {fallback_file}")

    return None, last_error


def notion_create_page(client, database_id, properties, children=None):
    """Create a Notion page with retry."""
    body = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }
    if children:
        body["children"] = children
    return notion_req(client, "post", "pages", body)


def notion_update_page(client, page_id, properties):
    """Update a Notion page with retry."""
    return notion_req(client, "patch", f"pages/{page_id}", {"properties": properties})


def notion_query_db(client, database_id, filter_obj=None, sorts=None, page_size=100):
    """Query a Notion database with retry."""
    body = {"page_size": page_size}
    if filter_obj:
        body["filter"] = filter_obj
    if sorts:
        body["sorts"] = sorts
    return notion_req(client, "post", f"databases/{database_id}/query", body)
