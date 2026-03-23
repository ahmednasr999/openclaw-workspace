#!/usr/bin/env python3
"""
LinkedIn Reaction Tracker
Tracks reaction snapshots for published LinkedIn posts at defined intervals.

CLI Commands:
  --register <activity_urn> <title> [--url <post_url>]  Add post to tracking
  --check <activity_urn>                                 Record a snapshot (reads reactions JSON from stdin)
  --report                                               Print performance summary across all tracked posts
  --due                                                  List posts due for a reaction check

Intervals tracked: 1hr, 24hr, 48hr, 7d (168hr)

Usage in cron (agent workflow):
  1. Run --due to get list of URNs needing checks
  2. For each, call LINKEDIN_LIST_REACTIONS via Composio, pipe JSON to --check
  3. Example: echo '<reactions_json>' | python3 scripts/linkedin-reaction-tracker.py --check urn:li:activity:XXX
"""

import json
import sys
import os
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────────

WORKSPACE = Path(__file__).parent.parent
DATA_DIR = WORKSPACE / "data"
POSTS_FILE = DATA_DIR / "linkedin-posts.json"
ENGAGEMENT_DIR = DATA_DIR / "linkedin-engagement"

# Intervals in hours at which we check reactions
CHECK_INTERVALS_HOURS = [1, 24, 48, 168]  # 1hr, 24hr, 48hr, 7d


# ─── Helpers ─────────────────────────────────────────────────────────────────

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(ts: str) -> datetime:
    """Parse ISO 8601 string → aware datetime (UTC)."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def activity_id_from_urn(urn: str) -> str:
    """Extract numeric ID from 'urn:li:activity:1234567890'."""
    return urn.split(":")[-1]


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ENGAGEMENT_DIR.mkdir(parents=True, exist_ok=True)


def load_posts() -> dict:
    if POSTS_FILE.exists():
        with open(POSTS_FILE) as f:
            return json.load(f)
    return {"posts": []}


def save_posts(data: dict):
    with open(POSTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_engagement(activity_id: str) -> dict:
    path = ENGAGEMENT_DIR / f"{activity_id}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"activity_id": activity_id, "snapshots": []}


def save_engagement(activity_id: str, data: dict):
    path = ENGAGEMENT_DIR / f"{activity_id}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def get_post_by_urn(posts_data: dict, urn: str) -> dict | None:
    for p in posts_data.get("posts", []):
        if p.get("activity_urn") == urn:
            return p
    return None


# ─── Commands ────────────────────────────────────────────────────────────────

def cmd_register(urn: str, title: str, url: str = ""):
    """Register a new post for tracking."""
    ensure_dirs()
    posts_data = load_posts()

    existing = get_post_by_urn(posts_data, urn)
    if existing:
        print(f"[WARN] Post already registered: {urn}")
        print(json.dumps(existing, indent=2))
        return

    entry = {
        "activity_urn": urn,
        "activity_id": activity_id_from_urn(urn),
        "title": title,
        "post_url": url,
        "published_at": now_utc(),
        "registered_at": now_utc(),
    }
    posts_data["posts"].append(entry)
    save_posts(posts_data)

    print(f"[OK] Registered: {title}")
    print(f"     URN: {urn}")
    print(f"     Activity ID: {entry['activity_id']}")
    print(f"     Published at: {entry['published_at']}")
    print(f"     Next check due in: 1 hour")


def cmd_check(urn: str):
    """
    Record a reaction snapshot for a post.
    Reads Composio LINKEDIN_LIST_REACTIONS JSON from stdin.

    Expected stdin format (Composio tool output):
      {
        "elements": [
          {
            "reactionType": "LIKE",
            "actor": "urn:li:person:xxx",
            "created": {"time": 1234567890000}
          },
          ...
        ]
      }
    OR the agent may pass a summarized form:
      {
        "reaction_count": 42,
        "reaction_types": {"LIKE": 30, "CELEBRATE": 10, "INSIGHTFUL": 2}
      }
    """
    ensure_dirs()
    posts_data = load_posts()
    post = get_post_by_urn(posts_data, urn)

    if not post:
        print(f"[ERROR] Post not registered: {urn}")
        print("Run: python3 scripts/linkedin-reaction-tracker.py --register <urn> '<title>'")
        sys.exit(1)

    # Read reactions from stdin
    stdin_data = sys.stdin.read().strip()
    if not stdin_data:
        print("[ERROR] No reaction data on stdin. Pipe Composio LINKEDIN_LIST_REACTIONS output.")
        sys.exit(1)

    try:
        reactions_raw = json.loads(stdin_data)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON on stdin: {e}")
        sys.exit(1)

    # Parse reaction data - handle both formats
    reaction_types = {
        "LIKE": 0, "CELEBRATE": 0, "SUPPORT": 0,
        "LOVE": 0, "INSIGHTFUL": 0, "FUNNY": 0
    }
    reactions_list = []

    if "elements" in reactions_raw:
        # Full Composio format
        elements = reactions_raw.get("elements", [])
        for elem in elements:
            rtype = elem.get("reactionType", "LIKE").upper()
            if rtype in reaction_types:
                reaction_types[rtype] += 1
            else:
                reaction_types[rtype] = reaction_types.get(rtype, 0) + 1

            actor = elem.get("actor", "")
            created_time = elem.get("created", {}).get("time", 0)
            if created_time:
                ts = datetime.fromtimestamp(created_time / 1000, tz=timezone.utc).isoformat()
            else:
                ts = now_utc()

            reactions_list.append({
                "actor": actor,
                "type": rtype,
                "time": ts
            })
        reaction_count = len(elements)

    elif "reaction_count" in reactions_raw:
        # Summarized format
        reaction_count = reactions_raw.get("reaction_count", 0)
        reaction_types.update(reactions_raw.get("reaction_types", {}))

    elif "paging" in reactions_raw and "elements" in reactions_raw:
        # LinkedIn API paged format
        elements = reactions_raw.get("elements", [])
        for elem in elements:
            rtype = elem.get("reactionType", "LIKE").upper()
            reaction_types[rtype] = reaction_types.get(rtype, 0) + 1
        reaction_count = reactions_raw.get("paging", {}).get("total", len(elements))

    else:
        # Try to handle unknown format gracefully
        print(f"[WARN] Unrecognized reaction format, storing raw count 0")
        reaction_count = 0

    snapshot = {
        "checked_at": now_utc(),
        "reaction_count": reaction_count,
        "reaction_types": {k: v for k, v in reaction_types.items() if v > 0},
        "reactions": reactions_list[:50],  # cap at 50 to avoid huge files
    }

    activity_id = post["activity_id"]
    engagement = load_engagement(activity_id)
    engagement["activity_urn"] = urn
    engagement["title"] = post.get("title", "")
    engagement["snapshots"].append(snapshot)
    save_engagement(activity_id, engagement)

    elapsed = _elapsed_hours(post["published_at"])
    print(f"[OK] Snapshot recorded for: {post.get('title', urn)}")
    print(f"     Reactions: {reaction_count} total")
    print(f"     Types: {snapshot['reaction_types']}")
    print(f"     Hours since publish: {elapsed:.1f}h")
    print(f"     Snapshot #{len(engagement['snapshots'])}")


def cmd_due():
    """
    List posts that need a reaction check.
    Prints one line per post: <activity_urn> <interval_label> <title>
    """
    ensure_dirs()
    posts_data = load_posts()
    posts = posts_data.get("posts", [])

    if not posts:
        print("[INFO] No posts registered yet.")
        print("Run: python3 scripts/linkedin-reaction-tracker.py --register <urn> '<title>'")
        return

    due_items = []
    now = datetime.now(timezone.utc)

    for post in posts:
        urn = post["activity_urn"]
        activity_id = post["activity_id"]
        title = post.get("title", urn)
        published_at = parse_utc(post["published_at"])
        elapsed_hours = (now - published_at).total_seconds() / 3600

        # Load existing snapshots to know which intervals were already checked
        engagement = load_engagement(activity_id)
        checked_at_hours = []
        for snap in engagement.get("snapshots", []):
            snap_time = parse_utc(snap["checked_at"])
            hours_after_publish = (snap_time - published_at).total_seconds() / 3600
            checked_at_hours.append(hours_after_publish)

        # Determine which intervals are due but not yet checked
        # An interval is "checked" if ANY snapshot exists taken after that interval elapsed.
        # E.g., if 1hr interval, any snapshot taken >= 1hr after publish counts.
        # We report only the earliest un-checked interval.
        for interval in CHECK_INTERVALS_HOURS:
            if elapsed_hours < interval:
                break  # Not yet due for this interval (sorted ascending)

            next_interval = CHECK_INTERVALS_HOURS[CHECK_INTERVALS_HOURS.index(interval) + 1] \
                if interval != CHECK_INTERVALS_HOURS[-1] else float("inf")

            # Already checked if we have a snapshot taken after this interval but before the next
            already_checked = any(
                interval - 0.5 <= c < next_interval
                for c in checked_at_hours
            )

            if not already_checked:
                label = _interval_label(interval)
                due_items.append((urn, label, title, elapsed_hours))
                break  # Report only the earliest outstanding interval per post

    if not due_items:
        print("[INFO] No posts due for reaction checks right now.")
        _print_next_due(posts)
        return

    print(f"[DUE] {len(due_items)} post(s) need reaction checks:\n")
    for urn, label, title, elapsed in due_items:
        print(f"  URN:      {urn}")
        print(f"  Interval: {label}")
        print(f"  Title:    {title}")
        print(f"  Elapsed:  {elapsed:.1f}h since publish")
        print()

    print("─" * 60)
    print("To check each post, run LINKEDIN_LIST_REACTIONS via Composio,")
    print("then pipe the output to:")
    print("  echo '<json>' | python3 scripts/linkedin-reaction-tracker.py --check <urn>")


def cmd_report():
    """Generate a performance summary across all tracked posts."""
    ensure_dirs()
    posts_data = load_posts()
    posts = posts_data.get("posts", [])

    if not posts:
        print("[INFO] No posts tracked yet.")
        return

    print("=" * 60)
    print("LinkedIn Reaction Tracker — Performance Report")
    print(f"Generated: {now_utc()}")
    print("=" * 60)
    print()

    total_reactions = 0
    tracked_count = 0
    reaction_totals = {}

    rows = []

    for post in posts:
        urn = post["activity_urn"]
        activity_id = post["activity_id"]
        title = post.get("title", urn)
        published_at = post.get("published_at", "")

        engagement = load_engagement(activity_id)
        snapshots = engagement.get("snapshots", [])

        if not snapshots:
            rows.append({
                "title": title,
                "published_at": published_at,
                "snapshots": 0,
                "latest_reactions": 0,
                "reaction_types": {},
                "urn": urn,
            })
            continue

        # Latest snapshot
        latest = snapshots[-1]
        latest_count = latest.get("reaction_count", 0)
        latest_types = latest.get("reaction_types", {})

        rows.append({
            "title": title,
            "published_at": published_at,
            "snapshots": len(snapshots),
            "latest_reactions": latest_count,
            "reaction_types": latest_types,
            "urn": urn,
        })

        total_reactions += latest_count
        tracked_count += 1
        for rtype, count in latest_types.items():
            reaction_totals[rtype] = reaction_totals.get(rtype, 0) + count

    # Sort by reactions descending
    rows.sort(key=lambda x: x["latest_reactions"], reverse=True)

    print(f"Posts Tracked: {len(posts)}")
    print(f"Posts with Data: {tracked_count}")
    print(f"Total Reactions (latest snapshot): {total_reactions}")
    if tracked_count > 0:
        print(f"Average Reactions/Post: {total_reactions / tracked_count:.1f}")
    print()

    if reaction_totals:
        print("Reaction Breakdown (across all posts):")
        for rtype, count in sorted(reaction_totals.items(), key=lambda x: -x[1]):
            pct = (count / total_reactions * 100) if total_reactions > 0 else 0
            print(f"  {rtype:<12} {count:>4}  ({pct:.0f}%)")
        print()

    print("─" * 60)
    print("Posts by Performance:\n")

    for i, row in enumerate(rows, 1):
        pub = row["published_at"][:10] if row["published_at"] else "unknown"
        types_str = ", ".join(f"{k}:{v}" for k, v in row["reaction_types"].items()) if row["reaction_types"] else "no data"
        print(f"  {i:>2}. [{pub}] {row['title']}")
        print(f"       Reactions: {row['latest_reactions']}  |  Snapshots: {row['snapshots']}")
        if row["reaction_types"]:
            print(f"       Types: {types_str}")
        print()

    print("─" * 60)
    print("Use this report in the weekly LEARN review.")
    print("Feed into: skills/content-agent/instructions/learn.md Step 2")


# ─── Utilities ───────────────────────────────────────────────────────────────

def _elapsed_hours(published_at: str) -> float:
    published = parse_utc(published_at)
    now = datetime.now(timezone.utc)
    return (now - published).total_seconds() / 3600


def _interval_label(hours: int) -> str:
    labels = {1: "1hr", 24: "24hr", 48: "48hr", 168: "7d"}
    return labels.get(hours, f"{hours}hr")


def _print_next_due(posts: list):
    """Show when the next check is due across all posts."""
    now = datetime.now(timezone.utc)
    next_items = []

    for post in posts:
        urn = post["activity_urn"]
        activity_id = post["activity_id"]
        published_at = parse_utc(post["published_at"])
        elapsed_hours = (now - published_at).total_seconds() / 3600

        engagement = load_engagement(activity_id)
        checked_at_hours = []
        for snap in engagement.get("snapshots", []):
            snap_time = parse_utc(snap["checked_at"])
            hours_after_publish = (snap_time - published_at).total_seconds() / 3600
            checked_at_hours.append(hours_after_publish)

        for interval in CHECK_INTERVALS_HOURS:
            already_checked = any(abs(c - interval) <= max(0.5, interval * 0.1) for c in checked_at_hours)
            if already_checked:
                continue
            hours_until = interval - elapsed_hours
            if hours_until > 0:
                due_at = now + timedelta(hours=hours_until)
                next_items.append((due_at, interval, post.get("title", urn), urn))
                break

    if next_items:
        next_items.sort()
        due_at, interval, title, urn = next_items[0]
        label = _interval_label(interval)
        print(f"\nNext check due: {label} for '{title}'")
        print(f"  At: {due_at.strftime('%Y-%m-%d %H:%M UTC')}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="LinkedIn Reaction Tracker — track engagement snapshots for LinkedIn posts"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--register", nargs="+", metavar=("URN", "TITLE"),
                       help="Register a post: --register <urn> <title> [url]")
    group.add_argument("--check", metavar="URN",
                       help="Record a snapshot: pipe Composio reactions JSON to stdin")
    group.add_argument("--report", action="store_true",
                       help="Print performance summary")
    group.add_argument("--due", action="store_true",
                       help="List posts due for reaction check")

    args = parser.parse_args()

    if args.register:
        parts = args.register
        if len(parts) < 2:
            print("[ERROR] --register requires at least: <activity_urn> <title>")
            sys.exit(1)
        urn = parts[0]
        # Support quoted multi-word title: remaining args joined
        if len(parts) == 2:
            title = parts[1]
            url = ""
        elif len(parts) >= 3:
            # Check if last arg looks like a URL
            if parts[-1].startswith("http"):
                title = " ".join(parts[1:-1])
                url = parts[-1]
            else:
                title = " ".join(parts[1:])
                url = ""
        cmd_register(urn, title, url)

    elif args.check:
        cmd_check(args.check)

    elif args.report:
        cmd_report()

    elif args.due:
        cmd_due()


if __name__ == "__main__":
    main()
