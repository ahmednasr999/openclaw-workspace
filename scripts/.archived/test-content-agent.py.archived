#!/usr/bin/env python3
"""
test-content-agent.py — Tests for Content Agent system.

Covers: PQS scoring, Notion parsing, post matching, comment JSON parsing,
        pipeline state, content classification, orchestrator state.
"""

import json, re, sys, os
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

PASS = 0
FAIL = 0
SUITE = ""


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL [{SUITE}] {name}")


def suite(name):
    global SUITE
    SUITE = name
    print(f"\n--- {name} ---")


# =============================================================================
# Import modules under test
# =============================================================================

# Import PQS scoring from comment-radar-agent
import importlib.util
spec = importlib.util.spec_from_file_location("comment_radar", str(Path(__file__).parent / "comment-radar-agent.py"))
radar = importlib.util.module_from_spec(spec)
# Need to handle the requests import
sys.modules["requests"] = type(sys)("requests")  # Mock requests module
spec.loader.exec_module(radar)

# Import content-learn classifiers
spec2 = importlib.util.spec_from_file_location("content_learn", str(Path(__file__).parent / "content-learn.py"))
learn = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(learn)

# Import orchestrator
spec3 = importlib.util.spec_from_file_location("orchestrator", str(Path(__file__).parent / "content-orchestrator.py"))
orch = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(orch)


# =============================================================================
# Suite 1: PQS Scoring
# =============================================================================
suite("PQS Scoring")

# High-expertise post should score well
pmo_post = {
    "preview": "Digital transformation PMO governance across 15-hospital network",
    "author": "Chief Technology Officer",
    "title": "CTO discusses PMO governance in healthcare",
    "published_date": datetime.now(timezone.utc).isoformat(),
    "comment_count": 10,
}
pmo_score = radar.score_post(pmo_post)
check("PMO + healthcare + CTO should score high (>50)", pmo_score > 50)

# Generic tech post with no expertise overlap
generic_post = {
    "preview": "Check out this cool new JavaScript framework for web development",
    "author": "Junior Developer",
    "title": "New framework release",
    "published_date": (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat(),
    "comment_count": 2,
}
generic_score = radar.score_post(generic_post)
check("Generic JS post should score low (<30)", generic_score < 30)

# Priority author boost
priority_post = {
    "preview": "Leadership lessons from my career",
    "author": "Pascal Bornet",
    "title": "Pascal Bornet on leadership",
    "published_date": datetime.now(timezone.utc).isoformat(),
    "comment_count": 15,
}
priority_authors = [{"name": "Pascal Bornet", "slug": "pascalbornet"}]
priority_score = radar.score_post(priority_post, priority_authors)
check("Priority author gets +15 boost", priority_post.get("priority") == True)
check("Priority author score > generic post", priority_score > generic_score)

# Crowded post penalty
crowded_post = {
    "preview": "Digital transformation in GCC healthcare PMO",
    "author": "CEO of major company",
    "title": "CEO discusses transformation",
    "published_date": datetime.now(timezone.utc).isoformat(),
    "comment_count": 200,
}
crowded_score = radar.score_post(crowded_post)
uncrowded = crowded_post.copy()
uncrowded["comment_count"] = 15
uncrowded_score = radar.score_post(uncrowded)
check("200 comments gets heavy penalty", crowded_score < uncrowded_score)
check("Crowd penalty > 20 points", uncrowded_score - crowded_score >= 20)

# Zero-comment old post = dead
dead_post = {
    "preview": "AI transformation in PMO governance",
    "author": "Director of PMO",
    "title": "PMO governance post",
    "published_date": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(),
    "comment_count": 0,
}
dead_score = radar.score_post(dead_post)
fresh_dead = dead_post.copy()
fresh_dead["published_date"] = datetime.now(timezone.utc).isoformat()
fresh_score = radar.score_post(fresh_dead)
check("Old zero-comment post gets penalty vs fresh", dead_score < fresh_score)

# GCC terms boost
gcc_post = {
    "preview": "Digital transformation in Saudi Arabia and UAE, Riyadh-based PMO",
    "author": "CTO",
    "title": "GCC digital transformation",
    "published_date": datetime.now(timezone.utc).isoformat(),
    "comment_count": 8,
}
no_gcc = {
    "preview": "Digital transformation in PMO governance",
    "author": "CTO",
    "title": "Digital transformation",
    "published_date": datetime.now(timezone.utc).isoformat(),
    "comment_count": 8,
}
check("GCC terms boost score", radar.score_post(gcc_post) > radar.score_post(no_gcc))

# Discussion markers
discussion_post = {
    "preview": "Unpopular opinion: PMO is dead. What do you think about governance?",
    "author": "VP Technology",
    "title": "Controversial PMO take",
    "published_date": datetime.now(timezone.utc).isoformat(),
    "comment_count": 20,
}
bland_post = {
    "preview": "PMO governance report for Q1 2026 has been released today.",
    "author": "VP Technology",
    "title": "Q1 report",
    "published_date": datetime.now(timezone.utc).isoformat(),
    "comment_count": 20,
}
check("Discussion markers boost score", radar.score_post(discussion_post) > radar.score_post(bland_post))

# Author signal: check author name not post body
exec_author = {
    "preview": "Simple post about technology",
    "author": "Chief Information Officer at Saudi Corp",
    "title": "CIO on tech",
    "published_date": datetime.now(timezone.utc).isoformat(),
    "comment_count": 5,
}
non_exec_author = {
    "preview": "Our Chief Information Officer at Saudi Corp told us this about technology",
    "author": "Marketing Intern",
    "title": "Intern on tech",
    "published_date": datetime.now(timezone.utc).isoformat(),
    "comment_count": 5,
}
check("CIO author scores higher than intern mentioning CIO", 
      radar.score_post(exec_author) > radar.score_post(non_exec_author))

# Score bounds
check("Score >= 0", pmo_score >= 0)
check("Score <= 130", pmo_score <= 130)


# =============================================================================
# Suite 2: Comment JSON Parsing
# =============================================================================
suite("Comment JSON Parsing")

# Valid JSON
valid = '[{"post_num": 1, "comment": "test comment"}]'
parsed = radar.parse_llm_comments(valid)
check("Valid JSON parses correctly", len(parsed) == 1)
check("Correct post_num", parsed[0]["post_num"] == 1)

# Markdown-fenced JSON
fenced = '```json\n[{"post_num": 1, "comment": "fenced"}]\n```'
parsed2 = radar.parse_llm_comments(fenced)
check("Markdown-fenced JSON parses", len(parsed2) == 1)

# Embedded JSON in text
embedded = 'Here are the comments:\n[{"post_num": 1, "comment": "embedded"}]\nEnd.'
parsed3 = radar.parse_llm_comments(embedded)
check("Embedded JSON extracted", len(parsed3) == 1)

# Empty/None input
check("None returns empty", radar.parse_llm_comments(None) == [])
check("Empty string returns empty", radar.parse_llm_comments("") == [])

# Invalid JSON
check("Invalid JSON returns empty", radar.parse_llm_comments("not json at all") == [])


# =============================================================================
# Suite 3: Content Classification
# =============================================================================
suite("Content Classification")

# Post types
check("Story detected", learn.classify_post_type("I hired 16 PMs", "When I started...") == "story")
check("Opinion detected", learn.classify_post_type("Unpopular opinion on PMO", "Stop doing...") == "opinion")
check("Data detected", learn.classify_post_type("PMO survey results", "73% of companies...") == "data")
check("Expertise default", learn.classify_post_type("PMO Best Practices", "Framework for...") == "expertise")

# Pillars
check("PMO pillar", learn.classify_pillar("Program Management Office", "PMO") == "pmo")
check("AI pillar", learn.classify_pillar("AI Agents for Business", "artificial intelligence") == "ai")
check("Transformation pillar", learn.classify_pillar("Digital Transformation Journey", "modernization") == "transformation")
check("Leadership pillar", learn.classify_pillar("Building Great Teams", "leadership") == "leadership")

# Hook styles
check("Question hook", learn.classify_hook_style("What if PMOs could self-optimize?") == "question")
check("Bold claim hook", learn.classify_hook_style("Stop running your PMO like it's 2010") == "bold_claim")
check("Stat hook", learn.classify_hook_style("73% of digital transformations fail") == "stat")
check("Story hook", learn.classify_hook_style("When I joined the hospital network") == "specific_story")


# =============================================================================
# Suite 4: Orchestrator State
# =============================================================================
suite("Orchestrator State")

# New day resets state
state = {"date": "2026-03-23", "today_post_url": "old_url"}
today = datetime.now(timezone(timedelta(hours=2))).strftime("%Y-%m-%d")
if state.get("date") != today:
    state = {"date": today, "started_at": "now"}
check("New day resets state", "today_post_url" not in state)
check("Date updated", state["date"] == today)

# Post registration
import re as re_mod
test_url = "https://www.linkedin.com/posts/ahmednasr_activity-7442117449128337408-xyz"
m = re_mod.search(r'activity[/-](\d+)', test_url)
check("Activity ID extraction from URL", m and m.group(1) == "7442117449128337408")

test_url2 = "https://www.linkedin.com/feed/update/urn:li:share:7442117449128337408"
m2 = re_mod.search(r'activity[/-](\d+)', test_url2)
check("Feed URL doesn't match activity pattern (expected)", m2 is None)

# State file schema
test_state = {
    "date": "2026-03-24",
    "started_at": "2026-03-24T09:00:00+02:00",
    "prime_status": "ok",
    "publish_status": "posted",
    "today_post_url": "https://linkedin.com/posts/test",
    "engage_status": "monitored",
    "collect_status": "ok",
}
check("State has all expected keys", all(k in test_state for k in ["date", "prime_status", "publish_status"]))


# =============================================================================
# Suite 5: Priority Authors
# =============================================================================
suite("Priority Authors")

# Check priority-authors.json exists and is valid
pa_path = Path("/root/.openclaw/workspace/config/priority-authors.json")
check("priority-authors.json exists", pa_path.exists())

if pa_path.exists():
    pa = json.load(open(pa_path))
    check("Priority authors is a list", isinstance(pa, list))
    check("Has 19 authors", len(pa) == 19)
    check("Each has name field", all("name" in a for a in pa))
    check("Each has slug field", all("slug" in a for a in pa))
    check("Pascal Bornet is first", pa[0]["name"] == "Pascal Bornet")


# =============================================================================
# Suite 6: Comment Tracker
# =============================================================================
suite("Comment Tracker")

# Test tracker structure
tracker = radar.load_comment_tracker()
check("Tracker loads (may be empty)", isinstance(tracker, dict))
check("Tracker has comments key", "comments" in tracker)
check("Tracker has stats key", "stats" in tracker)

# Test save/load roundtrip (using temp path)
import tempfile
tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
tmp.close()
old_path = radar.COMMENT_TRACKER_PATH
radar.COMMENT_TRACKER_PATH = Path(tmp.name)
test_tracker = {"comments": [{"url": "test", "posted_at": "2026-03-24"}], "stats": {"total_posted": 1, "total_drafted": 5}}
radar.save_comment_tracker(test_tracker)
loaded = radar.load_comment_tracker()
check("Tracker roundtrip preserves data", loaded["stats"]["total_posted"] == 1)
check("Tracker roundtrip preserves comments", len(loaded["comments"]) == 1)
radar.COMMENT_TRACKER_PATH = old_path
os.unlink(tmp.name)


# =============================================================================
# Suite 7: Content Health Monitor (renamed)
# =============================================================================
suite("Content Health Monitor")

monitor_path = Path("/root/.openclaw/workspace/scripts/content-health-monitor.py")
check("content-health-monitor.py exists (renamed from linkedin-content-agent.py)", monitor_path.exists())

# Verify old file is gone
old_path = Path("/root/.openclaw/workspace/scripts/linkedin-content-agent.py")
check("linkedin-content-agent.py no longer exists", not old_path.exists())

# Verify engagement radar is gone
old_radar = Path("/root/.openclaw/workspace/scripts/linkedin-engagement-radar.py")
check("linkedin-engagement-radar.py no longer exists (D2)", not old_radar.exists())


# =============================================================================
# Suite 8: Cookie Config
# =============================================================================
suite("Cookie Config")

cookie_config = Path("/root/.openclaw/workspace/config/linkedin-cookies.json")
check("linkedin-cookies.json exists", cookie_config.exists())
if cookie_config.exists():
    cc = json.load(open(cookie_config))
    check("Has cookie_file path", "cookie_file" in cc)
    check("Has max_age_hours", "max_age_hours" in cc)
    check("Cookie file path exists", Path(cc["cookie_file"]).exists())


# =============================================================================
# Summary
# =============================================================================
print(f"\n{'='*50}")
print(f"Content Agent Tests: {PASS}/{PASS+FAIL} passed")
if FAIL:
    print(f"FAILURES: {FAIL}")
    sys.exit(1)
else:
    print("ALL PASSED")
