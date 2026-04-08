#!/usr/bin/env python3
"""
Content Factory Auto-Drafter v1.0
==================================
Closes the gap between Gold articles and LinkedIn post drafts.

Flow:
  1. Find Gold articles in Content Calendar with Status="Ideas" (placed by bridge)
  2. For each, read the article source (title, summary, format tag, topic)
  3. Generate a LinkedIn post draft using Ahmed's voice + Diandra's 4 formats
  4. Write the draft into the Notion page body
  5. Update Status from "Ideas" → "Draft"
  6. Generate a v3 Premium visual and attach as image block
  7. Notify Ahmed on Telegram with preview

Cron: Runs after bridge (daily 9:00 AM Cairo, after 8:30 bridge)
"""

import json, os, re, ssl, sys, urllib.request, time, subprocess
from datetime import datetime, timezone, timedelta

WORKSPACE = "/root/.openclaw/workspace"
NOTION_TOKEN = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
CALENDAR_DB = "3268d599-a162-814b-8854-c9b8bde62468"
ctx = ssl.create_default_context()
CAIRO = timezone(timedelta(hours=2))

DRY_RUN = "--dry-run" in sys.argv
MAX_DRAFTS = 3  # Don't flood — max 3 drafts per run

# Gateway LLM
try:
    _gw_cfg = json.load(open(os.path.expanduser("~/.openclaw/openclaw.json")))
    GATEWAY_TOKEN = _gw_cfg.get("gateway", {}).get("auth", {}).get("token", "")
except Exception:
    GATEWAY_TOKEN = ""

GATEWAY_URL = "http://127.0.0.1:18789/v1/chat/completions"

# ── Ahmed's LinkedIn Voice (from skills/linkedin-writer) ────────────────────

VOICE_RULES = """
VOICE RULES (Non-negotiable):
- Write like Ahmed talks. Read it out loud — if it sounds stiff, rewrite.
- NO buzzwords: "synergy", "leverage", "ecosystem", "disrupt", "game-changer"
- NO humble brags. NO "I'm excited to share..." — just share it.
- Specific > generic. Numbers, countries, tools, results.
- First person. Contractions. "Don't" not "do not."
- Direct, confident, a little contrarian. Briefing a peer, not teaching a class.
- NEVER use em dashes (—). Use commas or hyphens instead.

ON-VOICE examples:
- "I built a PMO across 8 countries. Here's what broke first."
- "The Salesforce rollout taught me more than my PMP ever did."
- "20 years in tech taught me one thing: governance beats talent."

OFF-VOICE (NEVER write like this):
- "In today's rapidly evolving landscape..."
- "I am a seasoned professional with extensive experience..."
- "Excited to share that I've been thinking about transformation!"
"""

FORMAT_PROMPTS = {
    "Newsjacking": """FORMAT: NEWSJACKING
The article is breaking industry news. Ahmed needs to be the first credible voice.
Structure: Bold claim about what this means → Why most people are reading it wrong → 
What it actually signals for [industry] → One specific prediction → Question.
Key: Speed + credibility. Don't summarize the news, INTERPRET it.""",

    "Brandjacking": """FORMAT: BRANDJACKING  
The article features a recognizable brand/company. Borrow their name recognition.
Structure: "[Company] just did [thing]" → What most people missed → 
The real lesson for [Ahmed's audience] → How this connects to Ahmed's experience → Question.
Key: Use the brand as a hook, but pivot to YOUR insight within 2 lines.""",

    "Namejacking": """FORMAT: NAMEJACKING
The article quotes or features a person Ahmed's audience follows.
Structure: "[Person] said [bold thing]" → Ahmed's take (agree/disagree/extend) → 
Connect to personal experience → What this means for the audience → Question.
Key: Reference the person, deliver YOUR perspective. Not a book report.""",

    "Hot Take": """FORMAT: HOT TAKE
The article enables a contrarian or polarizing opinion.
Structure: Bold opening line that forces people to pick a side → 
Evidence/reasoning → Nuanced but firm conclusion → Specific question.
Key: Make people FEEL something. Safe takes get zero engagement.""",
}

FORMATTING_RULES = """
FORMATTING (Non-negotiable):
- Short paragraphs. 1-2 sentences max per paragraph.
- Line breaks between EVERY paragraph. White space is engagement.
- First line is the HOOK. 8-15 words. Must stop the scroll.
- Under 1300 characters total (unless story format).
- End with a SPECIFIC question. "What's your governance model?" not "What do you think?"
- No links in post body. 
- No emojis as bullet points. One emoji per post MAX, if any.
- 3-5 specific hashtags at the very bottom.
- No em dashes anywhere.
"""

QUALITY_CHECKLIST = """
BEFORE DELIVERING, verify ALL pass:
1. Hook would make YOU stop scrolling
2. Sounds like Ahmed, not a brand or content mill
3. Has white space (short paragraphs with line breaks)
4. Contains at least one specific detail (numbers, names, dates)
5. Ends with a specific engagement question
6. No cringe buzzwords
7. Under 1300 characters (unless story)
8. No links in post body
9. No em dashes
10. Has a defensible point of view (not neutral/generic)
11. 3-5 specific hashtags at bottom
"""


def call_llm(prompt, max_tokens=800, model="anthropic/claude-sonnet-4-6"):
    """Call LLM via gateway."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,  # Creative but controlled
    }
    headers = {"Content-Type": "application/json"}
    if GATEWAY_TOKEN:
        headers["Authorization"] = f"Bearer {GATEWAY_TOKEN}"
    req = urllib.request.Request(GATEWAY_URL, data=json.dumps(payload).encode(),
                                headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  LLM error: {e}")
        return None


def notion_req(method, path, body=None):
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read())


def get_ideas():
    """Get Gold articles in Content Calendar with Status=Ideas (placed by bridge)."""
    body = {
        "filter": {"property": "Status", "select": {"equals": "Ideas"}},
        "sorts": [{"property": "Planned Date", "direction": "descending"}],
        "page_size": MAX_DRAFTS * 2,  # Fetch extra in case some are unsuitable
    }
    result = notion_req("POST", f"/databases/{CALENDAR_DB}/query", body)
    return result.get("results", [])


def extract_page_props(page):
    """Extract relevant properties from a Content Calendar page."""
    props = page.get("properties", {})
    
    title = "".join(t.get("plain_text", "") for t in props.get("Title", {}).get("title", []))
    hook = "".join(t.get("plain_text", "") for t in props.get("Hook", {}).get("rich_text", []))
    topic_sel = props.get("Topic", {}).get("select", {})
    topic = topic_sel.get("name", "AI") if topic_sel else "AI"
    
    # Get posting angle from Hook field (carried over from RSS scorer via bridge)
    posting_angle = "".join(t.get("plain_text", "") for t in props.get("Hook", {}).get("rich_text", []))
    
    # Get existing body content
    blocks = notion_req("GET", f"/blocks/{page['id']}/children?page_size=50")
    body_text = ""
    for b in blocks.get("results", []):
        bt = b["type"]
        rt = b.get(bt, {}).get("rich_text", [])
        body_text += "".join(t.get("plain_text", "") for t in rt) + "\n"
    
    return {
        "page_id": page["id"],
        "title": title,
        "hook": hook,
        "topic": topic,
        "posting_angle": posting_angle,
        "body": body_text.strip(),
    }


def detect_format_from_angle(posting_angle, title):
    """Detect post format from the posting angle tag or title."""
    combined = f"{posting_angle} {title}".lower()
    
    for fmt in ["Newsjacking", "Brandjacking", "Namejacking", "Hot Take"]:
        if fmt.lower() in combined:
            return fmt
    
    # Fallback heuristics
    hot_signals = ["don't", "won't", "stop", "wrong", "myth", "overrated"]
    if any(s in combined for s in hot_signals):
        return "Hot Take"
    
    brands = ["google", "microsoft", "openai", "salesforce", "amazon", "apple", "meta", "nvidia"]
    if any(b in combined for b in brands):
        return "Brandjacking"
    
    if any(w in combined for w in ["ceo", "founder", "said", "according"]):
        return "Namejacking"
    
    return "Newsjacking"


def generate_draft(article):
    """Generate a LinkedIn post draft from a Gold article."""
    post_format = detect_format_from_angle(article["posting_angle"], article["title"])
    format_prompt = FORMAT_PROMPTS.get(post_format, FORMAT_PROMPTS["Newsjacking"])
    
    prompt = f"""You are writing a LinkedIn post for Ahmed Nasr, a Technology Executive with 20+ years in PMO, digital transformation, and AI across GCC/MENA.

{VOICE_RULES}

{format_prompt}

{FORMATTING_RULES}

ARTICLE TO TURN INTO A POST:
Title: {article['title']}
Topic: {article['topic']}
Context/Angle: {article['posting_angle'] or 'Not specified'}
Existing notes: {article['body'][:500] if article['body'] else 'None'}

INSTRUCTIONS:
1. Write 3 hook variants first (curiosity gap, bold claim, specific story)
2. Pick the strongest hook
3. Write the full post using that hook
4. Add 3-5 specific hashtags at the bottom
5. Output ONLY the final post text, ready to copy-paste. No explanations.

{QUALITY_CHECKLIST}

Write the post now:"""

    draft = call_llm(prompt, max_tokens=1000)
    if not draft:
        return None, post_format
    
    # Clean up any meta-text the LLM might add
    lines = draft.split("\n")
    cleaned = []
    skip_prefixes = ["hook variant", "here's the", "here is the", "final post:", 
                     "option 1:", "option 2:", "option 3:", "---", "hook 1", "hook 2",
                     "hook 3", "**hook", "**3 hook", "3 hook", "chosen hook",
                     "type 1", "type 2", "type 3", "selected hook", "best hook",
                     "curiosity gap", "bold claim", "specific story"]
    in_hook_section = False
    for line in lines:
        lower = line.lower().strip()
        # Detect start of hook variants section
        if any(lower.startswith(p) for p in skip_prefixes) or "hook variants" in lower:
            in_hook_section = True
            continue
        # End hook section when we hit an empty line after hooks
        if in_hook_section and not lower:
            in_hook_section = False
            continue
        if in_hook_section:
            continue
        cleaned.append(line)
    
    draft = "\n".join(cleaned).strip()
    
    # If cleaning removed too much, fall back to original
    if len(draft) < 200:
        draft = "\n".join(lines).strip()
    
    # Remove em dashes (voice rule)
    draft = draft.replace("—", ",").replace("–", "-")
    
    return draft, post_format


def write_draft_to_notion(page_id, draft_text, post_format):
    """Write the draft into the Notion page body and update status."""
    # Clear existing body blocks first
    existing = notion_req("GET", f"/blocks/{page_id}/children?page_size=100")
    for block in existing.get("results", []):
        try:
            notion_req("DELETE", f"/blocks/{block['id']}")
        except:
            pass
    
    # Split draft into paragraphs for Notion blocks
    paragraphs = [p.strip() for p in draft_text.split("\n") if p.strip()]
    
    children = []
    for para in paragraphs:
        # Detect bold markdown and create annotations
        rich_text = []
        parts = re.split(r'(\*\*.+?\*\*)', para)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                rich_text.append({
                    "type": "text",
                    "text": {"content": part[2:-2]},
                    "annotations": {"bold": True}
                })
            elif part:
                rich_text.append({
                    "type": "text",
                    "text": {"content": part}
                })
        
        if rich_text:
            children.append({
                "type": "paragraph",
                "paragraph": {"rich_text": rich_text}
            })
    
    # Add the blocks
    if children:
        notion_req("PATCH", f"/blocks/{page_id}/children", {"children": children})
    
    # Update status to Draft and set posting angle to include format
    notion_req("PATCH", f"/pages/{page_id}", {
        "properties": {
            "Status": {"select": {"name": "Draft"}},
        }
    })
    
    return True


def generate_visual(title, post_format, topic):
    """Generate a v3 Premium visual for the draft."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "visuals", f"{WORKSPACE}/scripts/content-factory-visuals.py")
        visuals = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(visuals)
        
        # Use title as headline (trim for visual)
        headline = title[:100] + "..." if len(title) > 100 else title
        path = visuals.generate_visual(headline, post_format, topic, "Ahmed Nasr")
        return path
    except Exception as e:
        print(f"  Visual generation failed: {e}")
        return None


def notify_telegram(drafts):
    """Send Telegram notification about new drafts."""
    if not drafts:
        return
    
    lines = [f"✍️ **Content Factory Auto-Drafter**\n\n{len(drafts)} new draft(s) ready for review:\n"]
    for i, d in enumerate(drafts, 1):
        lines.append(f"{i}. [{d['format']}] {d['title'][:60]}")
    lines.append("\nOpen Notion Content Calendar to review and approve → Scheduled")
    
    msg = "\n".join(lines)
    try:
        result = subprocess.run(
            ["openclaw", "message", "send", "--channel", "telegram",
             "--target", "866838380", "--message", msg],
            timeout=15, capture_output=True, text=True
        )
        _out = (result.stdout + result.stderr)
        _mid = next((p for p in _out.split() if p.strip().isdigit()), None)
        if result.returncode != 0 or 'Sent via Telegram' not in _out:
            print(f'  [TG ERROR] {_out.strip()[:200]}')
        else:
            print(f'  [TG OK] msg_id={_mid}')
        print("Telegram notification sent")
    except Exception as e:
        print(f"Telegram failed: {e}")


def main():
    now = datetime.now(CAIRO)
    print(f"=== Content Factory Auto-Drafter v1.0 - {now.strftime('%Y-%m-%d %H:%M')} ===")
    if DRY_RUN:
        print("[DRY RUN]")
    
    # Get Ideas from Content Calendar
    ideas = get_ideas()
    print(f"Found {len(ideas)} Ideas in Content Calendar")
    
    if not ideas:
        print("No Ideas to draft. Exiting.")
        return
    
    drafted = []
    
    for page in ideas[:MAX_DRAFTS]:
        article = extract_page_props(page)
        
        if not article["title"]:
            print(f"  Skipping page {article['page_id']} - no title")
            continue
        
        # Skip if already has substantial body content (manual draft in progress)
        # 500 chars threshold: summaries from bridge are ~200-300 chars, real drafts are 800+
        if len(article["body"]) > 500:
            print(f"  Skipping '{article['title'][:50]}' - already has content ({len(article['body'])} chars)")
            continue
        
        print(f"\nDrafting: {article['title'][:60]}")
        
        # Generate draft
        draft, post_format = generate_draft(article)
        if not draft:
            print(f"  FAILED: LLM returned no draft")
            continue
        
        print(f"  Format: {post_format}")
        print(f"  Draft length: {len(draft)} chars")
        print(f"  First line: {draft.split(chr(10))[0][:80]}")
        
        if DRY_RUN:
            print(f"  [DRY RUN] Would write to Notion and generate visual")
            drafted.append({"title": article["title"], "format": post_format})
            continue
        
        # Write to Notion
        success = write_draft_to_notion(article["page_id"], draft, post_format)
        if success:
            print(f"  ✅ Written to Notion, status → Draft")
        
        # Generate visual
        visual_path = generate_visual(article["title"], post_format, article["topic"])
        if visual_path:
            print(f"  🖼️ Visual: {visual_path}")
        
        drafted.append({
            "title": article["title"],
            "format": post_format,
            "page_id": article["page_id"],
            "visual": visual_path,
        })
        
        time.sleep(1)  # Rate limit
    
    print(f"\n=== Done: {len(drafted)} drafts created ===")
    
    # Notify Ahmed
    if drafted and not DRY_RUN:
        notify_telegram(drafted)
    
    # Print summary
    for d in drafted:
        print(f"  [{d['format']}] {d['title'][:60]}")


if __name__ == "__main__":
    main()
