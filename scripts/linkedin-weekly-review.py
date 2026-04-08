#!/usr/bin/env python3
"""
LinkedIn Weekly Review — Friday draft session.

Pulls candidates from Notion (Status: Idea/Drafted), scores them with the same rubric
as the auto-poster, sends review to Telegram (topic 7), and moves approved posts
to Scheduled with next week's dates.

Usage:
  python3 scripts/linkedin-weekly-review.py          # Live
  python3 scripts/linkedin-weekly-review.py --dry-run  # Preview only
"""

import json, os, re, ssl, sys, urllib.request
from datetime import date, timedelta, datetime

WORKSPACE = "/root/.openclaw/workspace"
NOTION_DB_ID = "3268d599-a162-814b-8854-c9b8bde62468"
RESEARCH_LOG = os.path.join(WORKSPACE, "data", "linkedin-research-log.json")
BATCH_FILE = os.path.join(WORKSPACE, "data", "linkedin-weekly-batch.json")

DRY_RUN = "--dry-run" in sys.argv

# ── Notion helpers ──

def _notion_token():
    return json.load(open(os.path.join(WORKSPACE, "config", "notion.json"), "r"))["token"]

def notion(method, path, body=None):
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {_notion_token()}")
    req.add_header("Notion-Version", "2022-06-28")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=30) as r:
        return json.loads(r.read())

def query_status(status, limit=20):
    return notion("POST", f"/databases/{NOTION_DB_ID}/query", {
        "filter": {"property": "Status", "select": {"equals": status}},
        "page_size": limit,
    }).get("results", [])

def page_prop(page, name):
    prop = page.get("properties", {}).get(name, {})
    t = prop.get("type", "")
    if t == "title":
        return prop.get("title", [{}])[0].get("plain_text", "")
    if t == "select":
        return (prop.get("select") or {}).get("name", "")
    if t == "date":
        return ((prop.get("date") or {}).get("start") or "")
    if t == "rich_text":
        return prop.get("rich_text", [{}])[0].get("plain_text", "")
    return ""

def page_id(page):
    return page["id"].replace("-", "")

def fetch_page_text(pid):
    blocks = notion("GET", f"/blocks/{pid}/children").get("results", [])
    lines = []
    for b in blocks:
        bt = b.get(b.get("type", ""), {})
        for rt in bt.get("rich_text", []):
            txt = rt.get("plain_text", "").strip()
            if txt:
                lines.append(txt)
    return "\n".join(lines)

def update_notion_status(pid, status):
    notion("PATCH", f"/pages/{pid}", {"properties": {"Status": {"select": {"name": status}}}})

def update_notion_date(pid, d):
    notion("PATCH", f"/pages/{pid}", {"properties": {"Planned Date": {"date": {"start": d}}}})

# ── Scoring (same rubric as auto-poster) ──

QUESTIONS_WEIGHTED = [
    ("SCROLL_STOPPER",     "Is the first line a SCROLL-STOPPER that creates a curiosity gap?", 1, True),
    ("CTA",                "Does the post END WITH A QUESTION or CTA for engagement?", 1, True),
    ("METRIC",             "Does the post include a specific METRIC or DATA POINT?", 2, False),
    ("NOT_PRESS_RELEASE",  "Does it avoid sounding like a press release or changelog?", 2, False),
    ("CONTEXT_RICH",       "Is it CONTEXT-RICH — does it explain WHY, not just WHAT?", 2, False),
    ("RESULT_TRANSFORMATION", "Does the hook describe a RESULT or TRANSFORMATION?", 1, False),
    ("SPECIFIC_PERSON",    "Does the post feature a SPECIFIC PERSON or STORY?", 1, False),
    ("HOOK_LENGTH",        "Is the hook under 300 characters?", 1, False),
    ("ACHIEVE_FRAME",      "Is the framing about WHAT YOU CAN ACHIEVE?", 1, False),
    ("URGENCY",            "Does it create a SENSE OF URGENCY or exclusivity?", 1, False),
]
MAX_SCORE = sum(w for _, _, w, _ in QUESTIONS_WEIGHTED)
MIN_SCORE = 8

def get_anthropic_key():
    try:
        cfg = json.load(open(os.path.expanduser("~/.openclaw/openclaw.json")))
        p = cfg.get("models", {}).get("providers", {}).get("anthropic", {})
        return p.get("apiKey", ""), p.get("baseUrl", "https://api.anthropic.com")
    except Exception:
        return "", "https://api.anthropic.com"

def score_post(text):
    api_key, base = get_anthropic_key()
    if not api_key:
        return {"total": 0, "results": [], "error": "No Anthropic key"}
    qs = "\n".join(f"{i+1}. {q}" for i, (k, q, _, _) in enumerate(QUESTIONS_WEIGHTED))
    prompt = f"""Evaluate this LinkedIn post against 10 criteria.
For each, answer ONLY YES or NO on a separate line: Q1: YES, Q2: NO, etc.

{qs}

Post:
---
{text[:3000]}
---"""
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    try:
        req = urllib.request.Request(f"{base}/v1/messages", data=json.dumps({
            "model": "claude-haiku-4-5",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 256,
        }), headers=headers, method="POST")
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=20) as r:
            resp = json.loads(r.read())["content"][0]["text"]
    except Exception as e:
        return {"total": 0, "results": [], "error": str(e)}
    results = []
    total = 0
    for i, (key, _, weight, mandatory) in enumerate(QUESTIONS_WEIGHTED):
        pat = rf'Q?{i+1}[.:)\s]+\s*(YES|NO)'
        m = re.search(pat, resp, re.IGNORECASE)
        passed = m and m.group(1).upper() == "YES"
        if passed:
            total += weight
        results.append({"key": key, "passed": passed, "weight": weight, "mandatory": mandatory})
    return {"total": total, "max": MAX_SCORE, "results": results, "passed": total >= MIN_SCORE}

# ── Main ──

def main():
    print("=== LinkedIn Weekly Review ===")
    print(f"Date: {date.today().isoformat()}")
    print(f"Dry run: {DRY_RUN}")

    # 1. Collect candidates from Notion
    drafts = query_status("Drafted", limit=10)
    ideas = query_status("Idea", limit=10)
    candidates = drafts + ideas
    print(f"Candidates: {len(drafts)} drafted + {len(ideas)} ideas = {len(candidates)} total")

    if not candidates:
        print("No draft or idea posts found. Nothing to review.")
        return

    # 2. Score each
    scored = []
    for pg in candidates[:8]:
        pid = page_id(pg)
        title = page_prop(pg, "Title") or page_prop(pg, "Hook") or "Untitled"
        hook = page_prop(pg, "Hook")
        topic = page_prop(pg, "Topic")
        # Full text from hook + page blocks
        blocks_text = fetch_page_text(pid)
        content = f"{hook}\n\n{blocks_text}" if hook else blocks_text
        if len(content.strip()) < 50:
            continue
        sc = score_post(content)
        scored.append({"pid": pid, "title": title, "hook": hook[:250], "topic": topic, "content": content, "score": sc})
        s = sc
        mark = "✅" if s.get("passed") else "⚠️"
        print(f"  {mark} {s.get('total',0)}/{s.get('max',MAX_SCORE)}  {title[:50]}")

    scored.sort(key=lambda x: x["score"].get("total", 0), reverse=True)
    selected = scored[:5]

    # 3. Build review message
    lines = [f"📝 Weekly Content Review — {date.today().strftime('%b %d')}"]
    lines.append(f"Top {len(selected)} of {len(candidates)} candidates\n")

    for i, p in enumerate(selected, 1):
        s = p["score"]
        tag = "✅ PASS" if s.get("passed") else "⚠️ BELOW MIN"
        hook_preview = p["hook"][:120] + "..." if len(p["hook"]) > 120 else p["hook"]
        lines.append(f"{i}. [{p['topic'] or 'General'}] {p['title']}")
        lines.append(f"   Score: {s.get('total',0)}/{MAX_SCORE} — {tag}")
        lines.append(f"   Hook: {hook_preview}")
        failed = [r["key"] for r in s.get("results", []) if not r.get("passed")]
        if failed:
            lines.append(f"   Needs work: {', '.join(failed[:3])}")
        lines.append("")

    lines.append("Reply: approve 1,2,3,4,5 | skip 3 | edit 2: new text")

    review_text = "\n".join(lines)

    # 4. Save batch for approval processing
    next_monday = date.today() + timedelta(days=(7 - date.today().weekday()))
    batch = []
    for i, p in enumerate(selected):
        day = next_monday + timedelta(days=i)
        batch.append({"n": i+1, "pid": p["pid"], "title": p["title"], "date": day.isoformat(), "score": p["score"].get("total",0)})

    os.makedirs(os.path.dirname(BATCH_FILE), exist_ok=True)
    with open(BATCH_FILE, "w") as f:
        json.dump(batch, f, indent=2)

    if DRY_RUN:
        print(f"\n[DRY RUN] Would send to Telegram topic 7:")
        print("---")
        print(review_text)
        print("---")
    else:
        # Write review to a file the agent can pick up
        review_path = os.path.join(WORKSPACE, "data", f"linkedin-review-{date.today().isoformat()}.md")
        with open(review_path, "w") as f:
            f.write(review_text)
        print(f"\n✅ Review ready: {review_path}")
        print(f"✅ Batch: {BATCH_FILE}")
        print(f"\nTELEGRAM_MSG|7|{review_text}")

if __name__ == "__main__":
    main()
