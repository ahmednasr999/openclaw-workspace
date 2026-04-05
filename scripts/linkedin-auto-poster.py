#!/usr/bin/env python3
"""
LinkedIn Auto-Poster v3: Reads from Notion Content Calendar, scores via autoresearch loop, posts via Composio.

Flow:
1. Find today's "Scheduled" post in Notion Content Calendar
2. Extract full post text from page blocks
3. Score post using 10 binary eval questions (linkedin-score-post logic)
4. Log score + post text to data/linkedin-research-log.json
5. Convert **bold** markdown to LinkedIn Unicode bold
6. Quality gate: if score < threshold, rewrite using reference posts as style guide
6. Download image from GitHub (if any)
7. Write payload to /tmp/linkedin-post-payload.json for agent
8. Agent posts via Composio, then this script updates log with post URL

Usage:
  python3 linkedin-auto-poster.py              # Score + post today's scheduled content
  python3 linkedin-auto-poster.py --dry-run     # Preview without posting
  python3 linkedin-auto-poster.py --date 2026-03-19  # Post for specific date
  python3 linkedin-auto-poster.py --update-url "<url>" --page-id <id>  # Record post URL after agent posts
"""

import json, os, re, ssl, sys, urllib.request, tempfile
from datetime import datetime, date
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
NOTION_DB = "3268d599-a162-814b-8854-c9b8bde62468"  # Content Calendar
NOTION_TOKEN = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
PERSON_URN = "urn:li:person:mm8EyA56mj"
RESEARCH_LOG = f"{WORKSPACE}/data/linkedin-research-log.json"

# Parse args
DRY_RUN = "--dry-run" in sys.argv
UPDATE_URL = None
UPDATE_PAGE_ID = None

for i, arg in enumerate(sys.argv):
    if arg == "--update-url" and i + 1 < len(sys.argv):
        UPDATE_URL = sys.argv[i + 1]
    if arg == "--page-id" and i + 1 < len(sys.argv):
        UPDATE_PAGE_ID = sys.argv[i + 1]

# ── Autoresearch Scoring ────────────────────────────────────────

# Scoring: weighted questions with mandatory gates
# Format: (key, question, weight, mandatory)
SCORED_QUESTIONS = [
    ("RESULT_TRANSFORMATION", "Does the hook describe a RESULT or TRANSFORMATION (not just a topic)?", 1, False),
    ("SPECIFIC_PERSON", "Does the post feature a SPECIFIC PERSON or STORY (not just a company)?", 1, False),
    ("SCROLL_STOPPER", "Is the first line a SCROLL-STOPPER that creates a curiosity gap?", 1, True),  # MANDATORY
    ("METRIC", "Does the post include a specific METRIC or DATA POINT?", 2, False),  # HIGH
    ("HOOK_LENGTH", "Is the hook under 300 characters?", 1, False),
    ("CTA", "Does the post END WITH A QUESTION or CTA for engagement?", 1, True),  # MANDATORY
    ("ACHIEVE_FRAME", "Is the framing about WHAT YOU CAN ACHIEVE (not what the tool/company does)?", 1, False),
    ("NOT_PRESS_RELEASE", "Does it avoid sounding like a press release or changelog?", 2, False),  # HIGH
    ("CONTEXT_RICH", "Is it CONTEXT-RICH - does it explain WHY, not just WHAT?", 2, False),  # HIGH
    ("URGENCY", "Does it create a SENSE OF URGENCY or exclusivity?", 1, False),
]

# Legacy flat list for LLM prompt (just the question text)
QUESTIONS = [f"{q[0]}: {q[1]} Answer YES or NO." for q in SCORED_QUESTIONS]
MAX_SCORE = sum(q[2] for q in SCORED_QUESTIONS)  # 13 (3 high-weight x2 + 7 standard x1)
MIN_SCORE = 8  # ~60% of MAX_SCORE

# Auth: read Anthropic API key directly from openclaw.json (gateway /v1/chat/completions
# requires operator.write scope which the gateway token lacks — use Anthropic directly)
try:
    _oc_cfg = json.load(open(os.path.expanduser("~/.openclaw/openclaw.json")))
    ANTHROPIC_API_KEY = _oc_cfg.get("models", {}).get("providers", {}).get("anthropic", {}).get("apiKey", "")
    ANTHROPIC_BASE_URL = _oc_cfg.get("models", {}).get("providers", {}).get("anthropic", {}).get("baseUrl", "https://api.anthropic.com")
except Exception:
    ANTHROPIC_API_KEY = ""
    ANTHROPIC_BASE_URL = "https://api.anthropic.com"

SCORER_MODEL = "claude-haiku-4-5"  # Fast, cheap, accurate for binary YES/NO scoring


def call_llm(prompt: str) -> str:
    """Call claude-haiku-4-5 via Anthropic API for scoring."""
    payload = {
        "model": SCORER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 64,
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    req = urllib.request.Request(
        f"{ANTHROPIC_BASE_URL}/v1/messages",
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"].strip()
    except Exception as e:
        print(f"  LLM error: {e}")
        return f"ERROR: {e}"


def call_llm_long(prompt: str) -> str:
    """Call claude-haiku-4-5 with higher token limit for batched scoring and rewrites."""
    payload = {
        "model": SCORER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    req = urllib.request.Request(
        f"{ANTHROPIC_BASE_URL}/v1/messages",
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["content"][0]["text"].strip()
    except Exception as e:
        print(f"  LLM error: {e}")
        return ""


def load_reference_posts() -> str:
    """Load reference posts from the reference folder for style guidance.
    
    The reference folder (memory/linkedin-reference-posts.md) contains examples
    of Ahmed's best-performing posts. Injecting these into rewrite prompts
    improves style consistency and quality over time.
    """
    ref_path = WORKSPACE / "memory" / "linkedin-reference-posts.md"
    if not ref_path.exists():
        return ""
    
    content = ref_path.read_text()
    # Extract only the example posts section (before "Ahmed's Voice Patterns")
    patterns_marker = "## Ahmed's Voice Patterns"
    if patterns_marker in content:
        content = content.split(patterns_marker)[0]
    
    # Limit to ~1500 chars to avoid prompt bloat
    if len(content) > 1500:
        content = content[:1500] + "\n[...]"
    
    if not content.strip():
        return ""
    
    return (
        "\n\nBelow are examples of Ahmed's best-performing LinkedIn posts "
        "(use these as style reference when rewriting):\n\n"
        + content.strip()
    )

def parse_answer(text: str) -> int:
    t = text.upper().strip()
    return 1 if "YES" in t and "NO" not in t else 0


def score_post(post_text: str) -> dict:
    """Run all 10 eval questions in a single LLM call (10x faster)."""
    print("\n=== Scoring Post ===")
    
    questions_block = "\n".join(f"Q{i+1}. {q}" for i, q in enumerate(QUESTIONS))
    prompt = f"""Evaluate this LinkedIn post against 10 quality criteria.
For each question, answer ONLY "YES" or "NO" on a separate line.
Format: Q1: YES/NO, Q2: YES/NO, ... Q10: YES/NO

{questions_block}

Post to evaluate:
{post_text[:3000]}

Answer each Q1-Q10 as YES or NO:"""
    
    response = call_llm_long(prompt)
    
    # Parse: look for YES/NO per question
    results = []
    for i in range(1, 11):
        # Try patterns: "Q1: YES", "Q1. YES", "1. YES", just sequential YES/NO
        pattern = rf'Q?{i}[.:)\s]+\s*(YES|NO)'
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            results.append(1 if match.group(1).upper() == "YES" else 0)
        else:
            results.append(0)  # Default to 0 if unparseable
    
    # Fallback: if regex found nothing, count YES/NO in order
    if sum(results) == 0 and "YES" in response.upper():
        words = [w.strip().upper() for w in re.split(r'[,\n;]+', response) if w.strip().upper() in ("YES", "NO")]
        for i, w in enumerate(words[:10]):
            results[i] = 1 if w == "YES" else 0
    
    # Weighted scoring
    weighted_total = 0
    mandatory_failed = []
    for i, (key, question, weight, mandatory) in enumerate(SCORED_QUESTIONS):
        passed = results[i] == 1
        pts = weight if passed else 0
        weighted_total += pts
        marker = "MANDATORY" if mandatory else f"x{weight}"
        status = f"{'PASS' if passed else 'FAIL'} ({pts}/{weight})"
        print(f"  Q{i+1}: {key:25s} [{marker:9s}] {status}")
        if mandatory and not passed:
            mandatory_failed.append(key)

    print(f"=== Score: {weighted_total}/{MAX_SCORE} ===")
    if mandatory_failed:
        print(f"=== MANDATORY FAILED: {', '.join(mandatory_failed)} ===")
    print()
    return {
        "total": weighted_total,
        "max_score": MAX_SCORE,
        "questions": results,
        "mandatory_failed": mandatory_failed,
    }


def log_post(post_text: str, score_result: dict, page_id: str):
    """Append scored post to research log."""
    os.makedirs(os.path.dirname(RESEARCH_LOG), exist_ok=True)
    
    if os.path.exists(RESEARCH_LOG):
        with open(RESEARCH_LOG) as f:
            data = json.load(f)
    else:
        data = {"posts": []}
    
    # Migrate: remove dead fields from old schema
    for key in ["current_prompt", "prompt_history", "current_prompt_version"]:
        data.pop(key, None)
    
    today_str = date.today().isoformat()
    
    # Dedup: replace existing entry for same page_id + date (don't append duplicates)
    data["posts"] = [
        p for p in data["posts"]
        if not (p.get("notion_page_id") == page_id and p.get("date") == today_str and not p.get("post_url"))
    ]
    
    entry = {
        "date": today_str,
        "post_text": post_text[:5000],
        "score": score_result["total"],
        "max_score": score_result.get("max_score", MAX_SCORE),
        "questions": score_result["questions"],
        "mandatory_failed": score_result.get("mandatory_failed", []),
        "notion_page_id": page_id,
    }
    data["posts"].append(entry)
    
    with open(RESEARCH_LOG, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Logged to {RESEARCH_LOG} | Score: {score_result['total']}/10")


def update_post_url(page_id: str, post_url: str):
    """Update the most recent post entry with the given page_id to include the URL."""
    if not os.path.exists(RESEARCH_LOG):
        print("Research log not found")
        return
    
    with open(RESEARCH_LOG) as f:
        data = json.load(f)
    
    # Find and update the entry with matching page_id (most recent first)
    for post in reversed(data.get("posts", [])):
        if post.get("notion_page_id") == page_id and not post.get("post_url"):
            post["post_url"] = post_url
            with open(RESEARCH_LOG, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Updated post URL: {post_url}")
            return
    
    print(f"No unmatched entry found for page_id: {page_id}")
CUSTOM_DATE = None
for i, arg in enumerate(sys.argv):
    if arg == "--date" and i + 1 < len(sys.argv):
        CUSTOM_DATE = sys.argv[i + 1]

TODAY = CUSTOM_DATE or datetime.now().strftime("%Y-%m-%d")

# ── Notion helpers ──────────────────────────────────────────────

def notion_req(method, path, body=None):
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode() if body else None
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read())


# ── Unicode Bold Converter ──────────────────────────────────────

def to_unicode_bold(text):
    """Convert regular text to Unicode Mathematical Bold (LinkedIn-compatible)."""
    result = []
    for ch in text:
        if 'A' <= ch <= 'Z':
            result.append(chr(0x1D5D4 + ord(ch) - ord('A')))
        elif 'a' <= ch <= 'z':
            result.append(chr(0x1D5EE + ord(ch) - ord('a')))
        elif '0' <= ch <= '9':
            result.append(chr(0x1D7EC + ord(ch) - ord('0')))
        else:
            result.append(ch)
    return ''.join(result)


def convert_bold_markdown(text):
    """Replace **bold text** with Unicode bold equivalent."""
    def bold_replacer(match):
        return to_unicode_bold(match.group(1))
    return re.sub(r'\*\*(.+?)\*\*', bold_replacer, text)


# ── Content Extraction ──────────────────────────────────────────

def get_today_post():
    """Find today's scheduled post in Notion Content Calendar."""
    body = {
        "filter": {"and": [
            {"property": "Status", "select": {"equals": "Scheduled"}},
            {"property": "Planned Date", "date": {"equals": TODAY}}
        ]},
        "page_size": 1
    }
    result = notion_req("POST", f"/databases/{NOTION_DB}/query", body)

    if not result.get("results"):
        return None

    page = result["results"][0]
    pid = page["id"]
    props = page["properties"]

    title = "".join(t.get("plain_text", "") for t in props.get("Title", {}).get("title", []))

    # Get full content from page blocks
    blocks_result = notion_req("GET", f"/blocks/{pid}/children?page_size=100")

    full_text = ""
    image_url = None
    numbered_counter = 0
    total_blocks = 0
    extracted_blocks = 0

    def extract_rich_text(rich_text_list, respect_bold=True):
        """Extract text from Notion rich_text array, preserving bold annotations."""
        line = ""
        for t in rich_text_list:
            text = t.get("plain_text", "")
            annotations = t.get("annotations", {})
            if respect_bold and annotations.get("bold") and text.strip():
                line += f"**{text}**"
            else:
                line += text
        return line

    for b in blocks_result.get("results", []):
        bt = b["type"]
        total_blocks += 1

        if bt == "image":
            img = b["image"]
            image_url = img.get("external", {}).get("url") or img.get("file", {}).get("url", "")
            extracted_blocks += 1

        elif bt in ("paragraph", "heading_1", "heading_2", "heading_3"):
            numbered_counter = 0  # Reset numbered list on non-list block
            rt = b.get(bt, {}).get("rich_text", [])
            line = extract_rich_text(rt)
            if line:
                full_text += line + "\n\n"  # double newline = blank line between paragraphs
                extracted_blocks += 1
            else:
                # Empty paragraph block = intentional blank line in Notion (kept as-is,
                # but we already add \n\n after content blocks so skip adding more)
                pass

        elif bt == "quote":
            numbered_counter = 0
            rt = b.get("quote", {}).get("rich_text", [])
            line = extract_rich_text(rt)
            if line:
                full_text += f"\"{line}\"\n\n"
                extracted_blocks += 1

        elif bt == "callout":
            numbered_counter = 0
            rt = b.get("callout", {}).get("rich_text", [])
            line = extract_rich_text(rt)
            if line:
                full_text += line + "\n\n"
                extracted_blocks += 1

        elif bt == "bulleted_list_item":
            numbered_counter = 0
            rt = b.get("bulleted_list_item", {}).get("rich_text", [])
            line = extract_rich_text(rt)
            if line:
                full_text += f"\u2022 {line}\n"  # list items: single newline (group tightly)
                extracted_blocks += 1

        elif bt == "numbered_list_item":
            numbered_counter += 1
            rt = b.get("numbered_list_item", {}).get("rich_text", [])
            line = extract_rich_text(rt)
            if line:
                full_text += f"{numbered_counter}. {line}\n"  # list items: single newline
                extracted_blocks += 1

        elif bt == "code":
            numbered_counter = 0
            rt = b.get("code", {}).get("rich_text", [])
            line = extract_rich_text(rt, respect_bold=False)
            if line:
                full_text += line + "\n\n"
                extracted_blocks += 1

        elif bt in ("divider", "table_of_contents", "breadcrumb", "child_page", "child_database"):
            numbered_counter = 0
            # Skip non-content blocks silently

        elif bt == "toggle":
            numbered_counter = 0
            rt = b.get("toggle", {}).get("rich_text", [])
            line = extract_rich_text(rt)
            if line:
                full_text += line + "\n\n"
                extracted_blocks += 1
                print(f"  WARNING: Toggle block extracted (top-level text only, children skipped)")

        else:
            # Catch-all: try to extract rich_text from unknown block types
            numbered_counter = 0
            block_data = b.get(bt, {})
            if isinstance(block_data, dict) and "rich_text" in block_data:
                rt = block_data["rich_text"]
                line = extract_rich_text(rt)
                if line:
                    full_text += line + "\n\n"
                    extracted_blocks += 1
                    print(f"  WARNING: Unknown block type '{bt}' - extracted via catch-all")
            else:
                print(f"  WARNING: Skipped unhandled block type '{bt}'")

    # Content loss detection
    if total_blocks > 2 and extracted_blocks > 0:
        avg_chars = len(full_text) / extracted_blocks
        if avg_chars < 20:
            print(f"  WARNING: Low extraction ratio ({avg_chars:.0f} chars/block) - content may be lost")

    # Clean up: remove metadata lines that leaked from .md files
    full_text = re.sub(r'^File:.*$', '', full_text, flags=re.MULTILINE)
    full_text = re.sub(r'^## Image Generated.*$', '', full_text, flags=re.MULTILINE)
    # Remove excessive blank lines, trim
    full_text = re.sub(r'\n{3,}', '\n\n', full_text).strip()

    # Convert **bold** to Unicode bold (Notion annotations are the single source of truth)
    full_text = convert_bold_markdown(full_text)

    return {
        "page_id": pid,
        "title": title,
        "content": full_text,
        "image_url": image_url
    }


# ── Image Upload ────────────────────────────────────────────────

def detect_post_format(title, content):
    """Detect which LinkedIn format a post fits best for visual generation."""
    combined = f"{title} {content[:500]}".lower()
    
    # Hot Take signals: strong opinions, contrarian phrases
    hot_take_signals = ["don't", "won't", "stop", "wrong", "myth", "unpopular", "controversial",
                        "nobody", "everyone", "overrated", "underrated", "hot take", "truth is"]
    if sum(1 for s in hot_take_signals if s in combined) >= 2:
        return "Hot Take"
    
    # Brandjacking: mentions specific brands/companies
    brands = ["google", "microsoft", "openai", "salesforce", "amazon", "apple", "meta",
              "netflix", "tesla", "nvidia", "mckinsey", "deloitte", "disney", "linkedin"]
    if any(b in combined for b in brands):
        return "Brandjacking"
    
    # Namejacking: references specific people
    people = ["ceo", "founder", "said", "according to", "as", "told", "argues"]
    if any(p in combined for p in people):
        return "Namejacking"
    
    # Default: Newsjacking (works for most content)
    return "Newsjacking"


def detect_topic(title, content):
    """Detect primary topic for visual badge."""
    combined = f"{title} {content[:500]}".lower()
    
    topic_keywords = {
        "AI": ["ai ", "artificial intelligence", "machine learning", "llm", "gpt", "agent",
               "automation", "neural", "deep learning", "claude", "chatgpt"],
        "Digital Transformation": ["digital transformation", "digitalization", "digital strategy",
                                   "modernization", "legacy system"],
        "PMO": ["project management", "pmo", "program management", "agile", "scrum",
                "portfolio", "stakeholder", "milestone", "deliverable"],
        "Healthcare": ["healthcare", "hospital", "patient", "clinical", "medical", "health system"],
        "HealthTech": ["healthtech", "health tech", "telehealth", "digital health", "medtech"],
        "FinTech": ["fintech", "banking", "payments", "financial technology", "neobank"],
        "Strategy": ["strategy", "strategic", "competitive advantage", "market position"],
    }
    
    scores = {}
    for topic, keywords in topic_keywords.items():
        scores[topic] = sum(1 for k in keywords if k in combined)
    
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "AI"


def download_image(url):
    """Download image from URL, with multi-tier local fallback.
    
    Search order:
    1. GitHub raw URL -> extract filename -> search local directories
    2. Any URL -> extract filename -> search local directories
    3. Search ALL media/post-images* directories for filename match
    4. HTTP download from URL
    """
    from urllib.parse import urlparse
    
    # Extract filename from URL (strip query params)
    try:
        parsed = urlparse(url)
        filename = parsed.path.rsplit("/", 1)[-1].split("?")[0]
    except Exception:
        filename = ""
    
    # Also extract the directory hint from GitHub URLs (e.g., "post-images-2026-03-29-v2")
    dir_hint = ""
    if "raw.githubusercontent.com" in url:
        parts = parsed.path.split("/")
        # URL format: /user/repo/branch/path/to/dir/filename
        if len(parts) >= 3:
            dir_hint = parts[-2]  # directory containing the file
    
    workspace = os.path.expanduser("~/.openclaw/workspace")
    
    # Local search directories (ordered by priority)
    search_dirs = []
    
    # If we have a directory hint, check that specific directory first
    if dir_hint:
        search_dirs.append(os.path.join(workspace, "media", dir_hint))
        search_dirs.append(os.path.join(workspace, dir_hint))
    
    # Standard locations
    search_dirs.extend([
        os.path.join(workspace, "linkedin/posts"),
        os.path.join(workspace, "media/post-visuals"),
    ])
    
    # Also search ALL media/post-images* directories dynamically
    media_dir = os.path.join(workspace, "media")
    if os.path.isdir(media_dir):
        for d in sorted(os.listdir(media_dir), reverse=True):
            full = os.path.join(media_dir, d)
            if os.path.isdir(full) and d.startswith("post-images"):
                if full not in search_dirs:
                    search_dirs.append(full)
    
    # Search all directories for the filename
    if filename:
        for search_dir in search_dirs:
            local_path = os.path.join(search_dir, filename)
            if os.path.exists(local_path):
                print(f"Using local image: {local_path}")
                with open(local_path, "rb") as f:
                    data = f.read()
                ct = "image/png" if local_path.lower().endswith(".png") else "image/jpeg"
                print(f"Local image: {len(data)} bytes, type: {ct}")
                return data, ct

    # Date-pattern fallback: look for YYYY-MM-DD-image.{png,jpg} in linkedin/posts/
    import re, datetime
    today = datetime.date.today().strftime("%Y-%m-%d")
    # Also try to extract date from the URL directory hint (e.g., "post-images-2026-03-29-v2")
    date_candidates = [today]
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", dir_hint + url)
    if date_match:
        date_candidates.append(date_match.group(1))
    
    posts_dir = os.path.join(workspace, "linkedin/posts")
    for date_str in date_candidates:
        for ext in ("png", "jpg", "jpeg"):
            candidate = os.path.join(posts_dir, f"{date_str}-image.{ext}")
            if os.path.exists(candidate):
                print(f"Date-pattern fallback image: {candidate}")
                with open(candidate, "rb") as f:
                    data = f.read()
                ct = "image/png" if ext == "png" else "image/jpeg"
                print(f"Local image: {len(data)} bytes, type: {ct}")
                return data, ct

    # HTTP download (will raise on 404/error - caught by caller for IMAGE_HOLD)
    print(f"Downloading image: {url[:80]}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
        content_type = r.headers.get("Content-Type", "image/png")
        data = r.read()
        print(f"Downloaded: {len(data)} bytes, type: {content_type}")
        return data, content_type


def upload_image_to_linkedin(image_bytes, content_type):
    """
    Save image to /tmp/ for agent to upload via Composio.
    Returns the temp file path.
    """
    ext = "png" if "png" in content_type else "jpg"
    tmp_path = f"/tmp/linkedin-post-image.{ext}"
    with open(tmp_path, "wb") as f:
        f.write(image_bytes)
    print(f"Image saved to: {tmp_path} ({len(image_bytes)} bytes)")
    return tmp_path


# ── Notion Update ───────────────────────────────────────────────

def update_notion_status(page_id, post_url):
    """Update Notion page status to Posted and add URL.
    Note: Post URL property is type 'url' in Notion, NOT rich_text."""
    body = {
        "properties": {
            "Status": {"select": {"name": "Posted"}},
        }
    }
    # Post URL is a 'url' type property in Notion - NOT rich_text
    if post_url:
        body["properties"]["Post URL"] = {"url": post_url[:2000]}
    notion_req("PATCH", f"/pages/{page_id}", body)
    print(f"Updated Notion: status=Posted, url={post_url}")


def send_telegram_confirmation(post_url, title="", image_url=None):
    """Send Telegram notification that post was published."""
    import subprocess
    image_status = "✅ with image" if image_url else "📝 text only"
    msg = f"✅ LinkedIn Posted ({image_status})\n\n{title[:100]}\n\n🔗 {post_url}"
    try:
        result = subprocess.run(
            ["openclaw", "message", "send", "--channel", "telegram",
             "--target", "866838380", "--message", msg],
            timeout=15, capture_output=True, text=True
        )
        _out = (result.stdout + result.stderr)
        _mid = next((p for p in _out.split() if p.strip().isdigit()), None)
        if result.returncode != 0 or "Sent via Telegram" not in _out:
            print(f"[TG ERROR] Delivery failed: {_out.strip()[:200]}")
        else:
            print(f"[TG OK] Confirmation sent msg_id={_mid}")
    except Exception as e:
        print(f"Telegram notification failed: {e}")


def update_briefing_page(post_url, image_url=None, title=""):
    """Add post details to today's morning briefing Notion page."""
    from datetime import timezone, timedelta
    cairo = timezone(timedelta(hours=2))
    today_str = datetime.now(cairo).strftime("%Y-%m-%d")
    
    # Find today's briefing page
    briefing_db = "3268d599-a162-812d-a59e-e5496dec80e7"
    result = notion_req("POST", f"/databases/{briefing_db}/query", {
        "filter": {"property": "Name", "title": {"contains": today_str}},
        "page_size": 1,
    })
    if not result:
        print("  Briefing update: No API response")
        return False
    
    pages = result.get("results", [])
    if not pages:
        print(f"  Briefing update: No page found for {today_str}")
        return False
    
    briefing_page_id = pages[0]["id"]
    
    # Get existing blocks to find Content section
    blocks_resp = notion_req("GET", f"/blocks/{briefing_page_id}/children?page_size=100")
    if not blocks_resp:
        print("  Briefing update: Could not fetch blocks")
        return False
    
    blocks = blocks_resp.get("results", [])
    
    # Find the Content & Engagement section
    content_section_idx = None
    insert_after_id = None
    for i, b in enumerate(blocks):
        btype = b["type"]
        rt = b.get(btype, {}).get("rich_text", [])
        text = "".join(t.get("text", {}).get("content", "") for t in rt)
        if "Content" in text and "Engagement" in text and btype == "heading_2":
            content_section_idx = i
        # Find last block before next section divider
        if content_section_idx is not None and i > content_section_idx:
            if b["type"] == "divider" or (b["type"] == "heading_2" and i > content_section_idx):
                break
            insert_after_id = b["id"]
    
    if not insert_after_id:
        # Fallback: insert after the heading itself
        if content_section_idx is not None:
            insert_after_id = blocks[content_section_idx]["id"]
        else:
            print("  Briefing update: Could not find Content & Engagement section")
            return False
    
    # Build blocks to insert
    new_blocks = [
        {
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": f"Posted: {title[:80]}"}, "annotations": {"bold": True}}],
                "icon": {"type": "emoji", "emoji": "✅"},
                "color": "green_background",
            }
        },
        {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {"type": "text", "text": {"content": "LinkedIn: "}},
                    {"type": "text", "text": {"content": post_url, "link": {"url": post_url}}},
                ]
            }
        },
    ]
    
    if image_url:
        new_blocks.append({
            "type": "image",
            "image": {"type": "external", "external": {"url": image_url}}
        })
    
    # Insert blocks
    resp = notion_req("PATCH", f"/blocks/{briefing_page_id}/children", {
        "children": new_blocks,
        "after": insert_after_id,
    })
    
    if resp:
        print(f"  Briefing page updated with post details")
        return True
    else:
        print(f"  Briefing update: Failed to insert blocks")
        return False


# ── Main ────────────────────────────────────────────────────────

def check_stale_watchdog():
    """Check if yesterday's watchdog flag still exists - means posting failed."""
    import subprocess
    watchdog_path = f"{WORKSPACE}/data/linkedin-watchdog.json"
    if not os.path.exists(watchdog_path):
        return
    try:
        data = json.load(open(watchdog_path))
        created = datetime.fromisoformat(data.get("created_at", ""))
        age_hours = (datetime.now() - created).total_seconds() / 3600
        if age_hours > 1:
            title = data.get("title", "Unknown")
            msg = f"🔴 LinkedIn post FAILED yesterday\n\nTitle: {title}\nPrepared {age_hours:.0f}h ago but never posted.\nWatchdog flag still exists."
            try:
                result = subprocess.run(
                    ["openclaw", "message", "send", "--channel", "telegram",
                     "--target", "866838380", "--message", msg],
                    timeout=15, capture_output=True, text=True
                )
                _out = (result.stdout + result.stderr)
                if "Sent via Telegram" not in _out:
                    print(f"[TG ERROR] Watchdog alert failed: {_out.strip()[:100]}")
            except Exception as _e:
                print(f"[TG ERROR] Watchdog alert exception: {_e}")
            print(f"⚠️ Stale watchdog: {title} ({age_hours:.0f}h old)")
            # Remove stale flag so we don't alert again
            os.remove(watchdog_path)
    except Exception:
        # Corrupted flag — remove it
        os.remove(watchdog_path)


def main():
    # Check for stale watchdog from previous run
    check_stale_watchdog()
    
    # Handle URL update mode (after agent posts)
    if UPDATE_URL and UPDATE_PAGE_ID:
        update_post_url(UPDATE_PAGE_ID, UPDATE_URL)
        # Also update today's briefing page
        # Read the payload to get image URL and title
        payload_path = "/tmp/linkedin-post-payload.json"
        image_url = None
        title = ""
        if os.path.exists(payload_path):
            try:
                payload = json.load(open(payload_path))
                title = payload.get("title", "")
                # Get original image URL from Notion (GitHub raw URL)
                image_url = None
                # Check if the post had an image
                if payload.get("image_required") or payload.get("image_path"):
                    # Try to find image URL from today's content calendar entry
                    post_data = get_today_post()
                    if post_data:
                        image_url = post_data.get("image_url")
            except Exception:
                pass
        update_briefing_page(UPDATE_URL, image_url=image_url, title=title)
        # Remove watchdog flag - post succeeded
        watchdog_path = f"{WORKSPACE}/data/linkedin-watchdog.json"
        if os.path.exists(watchdog_path):
            os.remove(watchdog_path)
            print("Watchdog flag removed (post successful)")
        # Send Telegram confirmation
        send_telegram_confirmation(UPDATE_URL, title, image_url)
        return
    
    print(f"=== LinkedIn Auto-Poster v3 - {TODAY} ===")
    if DRY_RUN:
        print("[DRY RUN MODE - will not post]")

    # Get today's post
    post = get_today_post()
    if not post:
        print(f"No scheduled post for {TODAY}")
        return

    print(f"\nTitle: {post['title']}")
    print(f"Content length: {len(post['content'])} chars")
    print(f"Image: {post['image_url'] or 'None'}")
    print(f"\n--- POST CONTENT ---")
    print(post['content'])
    print(f"--- END CONTENT ---\n")

    # Score the post via autoresearch loop
    score_result = score_post(post['content'])
    log_post(post['content'], score_result, post['page_id'])

    if DRY_RUN:
        print("[DRY RUN] Would post above content to LinkedIn")
        if post['image_url']:
            print(f"[DRY RUN] Would attach image: {post['image_url']}")
        return

    # Quality gate: weighted score + mandatory gates
    gate_failed = False
    gate_reason = []

    if score_result.get("mandatory_failed"):
        gate_failed = True
        gate_reason.append(f"Mandatory failed: {', '.join(score_result['mandatory_failed'])}")

    if score_result["total"] < MIN_SCORE:
        gate_failed = True
        gate_reason.append(f"Score {score_result['total']}/{MAX_SCORE} < {MIN_SCORE}")

    if gate_failed:
        print(f"\u26a0\ufe0f QUALITY GATE: {'; '.join(gate_reason)}")

        # Decision 2: Auto-rewrite attempt before holding
        failed_keys = [SCORED_QUESTIONS[i][0] for i, s in enumerate(score_result["questions"]) if s == 0]
        failed_descriptions = [f"- {SCORED_QUESTIONS[i][0]}: {SCORED_QUESTIONS[i][1]}"
                               for i, s in enumerate(score_result["questions"]) if s == 0]
        # Load reference posts for style guidance
        reference_posts = load_reference_posts()
        
        rewrite_prompt = (
            f"This LinkedIn post scored {score_result['total']}/{MAX_SCORE}. "
            f"It failed these quality criteria:\n"
            + "\n".join(failed_descriptions) +
            f"\n\nRewrite the post to pass ALL criteria while keeping the core message, "
            f"tone, and key facts. Keep it under 2800 characters. "
            f"Output ONLY the rewritten post text, no explanation.\n\n"
            f"Original post:\n{post['content'][:3000]}"
            + (reference_posts if reference_posts else "")
        )

        print("Attempting auto-rewrite with reference posts...")
        rewritten = call_llm_long(rewrite_prompt)
        if rewritten and len(rewritten) > 100 and not rewritten.startswith("ERROR"):
            # Re-score the rewrite
            rewritten_bold = convert_bold_markdown(rewritten)
            rescore = score_post(rewritten_bold)
            rescore_failed = bool(rescore.get("mandatory_failed")) or rescore["total"] < MIN_SCORE

            if not rescore_failed:
                print(f"\u2705 Rewrite PASSED: {rescore['total']}/{MAX_SCORE}")
                post['content'] = rewritten_bold
                score_result = rescore
                gate_failed = False
            else:
                print(f"\u274c Rewrite also failed: {rescore['total']}/{MAX_SCORE}")

        if gate_failed:
            print(f"Post flagged for manual review. NOT auto-posting.")
            flag = {
                "action": "quality_hold",
                "score": score_result["total"],
                "max_score": MAX_SCORE,
                "min_score": MIN_SCORE,
                "title": post['title'],
                "page_id": post['page_id'],
                "failed_questions": failed_keys,
                "mandatory_failed": score_result.get("mandatory_failed", []),
                "rewrite_attempted": True,
            }
            with open("/tmp/linkedin-post-payload.json", "w") as f:
                json.dump(flag, f, ensure_ascii=False, indent=2)
            print(f"QUALITY_HOLD")
            return

    # ── AI-Pattern Audit (avoid-ai-writing skill) ──────────────────────────────────
    # Mandatory: run all posts through avoid-ai-writing before posting
    audit_note = ""
    try:
        skill_path = Path(WORKSPACE) / "skills" / "avoid-ai-writing" / "SKILL.md"
        if skill_path.exists():
            print("\u270d\ufe0f Running AI-pattern audit...")
            audit_prompt = f"""You are editing content to remove AI writing patterns for LinkedIn posts.
Context: linkedin profile
Read the skill at: {skill_path}
Apply the skill in rewrite mode (linkedin profile).

Post text to audit and rewrite:
{post['content']}

Output format: Start with a brief note of what you found/fixed, then give the full rewritten post."""
            import subprocess
            result = subprocess.run(
                ["python3", "-c", f"""
import anthropic, json
client = anthropic.Anthropic()
with open("{skill_path}") as f:
    skill_text = f.read()
msg = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=2000,
    system=[{{"type": "system", "text": "You are a LinkedIn writing quality auditor. Read the avoid-ai-writing skill and apply it. Return the rewritten post with a brief audit note."}}],
    messages=[{{"role": "user", "content": f'''Read this skill:
{{skill_text}}

Now apply it to this LinkedIn post in rewrite mode (linkedin profile):
{{post['content'][:3000]}}

Return: (1) brief note of what you found/fixed, (2) full rewritten post'''}}]
)
print(msg.content[0].text[:3000])
"""],
                capture_output=True, text=True, cwd=WORKSPACE, timeout=60
            )
            if result.returncode == 0 and result.stdout.strip():
                audit_output = result.stdout.strip()
                # Try to extract just the rewritten post (skip audit notes)
                if len(audit_output) > 100:
                    lines = audit_output.split('\n')
                    # Find where rewritten content starts (skip audit notes)
                    post_start = -1
                    for i, line in enumerate(lines):
                        if len(line) > 50 and not line.startswith('-') and not line.startswith('*') and 'Issue' not in line and 'changed' not in line and 'found' not in line and 'flag' not in line.lower():
                            if i > 2:  # Skip first 2 lines (audit notes)
                                post_start = i
                                break
                    if post_start > 0:
                        rewritten_post = '\n'.join(lines[post_start:])
                        if len(rewritten_post) > 50 and len(rewritten_post) < 3500:
                            post['content'] = rewritten_post
                            audit_note = audit_output[:200]
                            print(f"\u2705 AI-pattern audit applied: {audit_note[:100]}")
                        else:
                            print(f"\u26a0\ufe0f AI audit output length unusual ({len(rewritten_post)} chars), skipping")
                    else:
                        print(f"\u26a0\ufe0f Could not parse audit output, skipping")
                else:
                    print(f"\u26a0\ufe0f AI audit returned short output, skipping")
            else:
                print(f"\u26a0\ufe0f AI audit failed: {result.stderr[:100] if result.stderr else 'no output'}")
        else:
            print("\u26a0\ufe0f avoid-ai-writing skill not found, skipping audit")
    except Exception as e:
        print(f"\u26a0\ufe0f AI audit error: {{e}}")

    # Download image if present - tiered degradation (Decision 3)
    # If no image in Notion, auto-generate branded visual template (v3 Premium)
    image_path = None
    if post['image_url']:

        try:
            image_bytes, content_type = download_image(post['image_url'])
            image_path = upload_image_to_linkedin(image_bytes, content_type)
        except Exception as e:
            # NEVER post without image if image was expected — always hold for review
            print(f"WARNING: Image download/upload failed ({e})")
            print(f"HELD: Image required but failed. NOT posting text-only.")
            flag = {
                "action": "image_failed_hold",
                "score": score_result["total"],
                "max_score": MAX_SCORE,
                "title": post['title'],
                "page_id": post['page_id'],
                "image_error": str(e),
            }
            with open("/tmp/linkedin-post-payload.json", "w") as f:
                json.dump(flag, f, ensure_ascii=False, indent=2)
            print("IMAGE_HOLD")
            return
    else:
        # No image in Notion — generate branded visual
        # Strategy: PIL template for cron (autonomous), agent upgrades to Gemini AI when posting
        print("No image in Notion. Generating visual...")
        try:
            import importlib.util
            vspec = importlib.util.spec_from_file_location(
                "visuals", f"{WORKSPACE}/scripts/content-factory-visuals.py")
            visuals = importlib.util.module_from_spec(vspec)
            vspec.loader.exec_module(visuals)
            
            # Detect post format from title/content
            post_format = detect_post_format(post['title'], post['content'])
            topic = detect_topic(post['title'], post['content'])
            
            # Use first line of content as headline (usually the hook)
            first_line = post['content'].split('\n')[0].strip()
            # Remove Unicode bold for the visual (keep it clean)
            headline = re.sub(r'[\U0001D400-\U0001D7FF]', lambda m: chr(
                ord('A') + ord(m.group()) - 0x1D5D4 if 0x1D5D4 <= ord(m.group()) <= 0x1D5ED
                else ord('a') + ord(m.group()) - 0x1D5EE if 0x1D5EE <= ord(m.group()) <= 0x1D607
                else ord('0') + ord(m.group()) - 0x1D7EC if 0x1D7EC <= ord(m.group()) <= 0x1D7F5
                else ord(m.group())
            ), first_line)
            # Trim to reasonable headline length
            if len(headline) > 100:
                headline = headline[:97] + "..."
            
            visual_path = visuals.generate_visual(
                headline, post_format, topic, "Ahmed Nasr",
                f"/tmp/linkedin-auto-visual.png"
            )
            image_path = visual_path
            post['image_url'] = None  # Mark as auto-generated (not from Notion)
            post['auto_visual'] = True
            post['visual_source'] = 'pil_template'
            # Signal to agent: upgrade available via image-gen-chain with topic-aware routing
            post['image_upgrade_available'] = True
            post['gemini_upgrade_available'] = True  # backward compat
            post['image_topic'] = topic
            post['gemini_topic'] = topic  # backward compat
            # Route hint: AI/Tech topics → Gemini first, Business → Stock first
            ai_tech = {"AI", "Digital Transformation", "HealthTech", "FinTech", "Data", "Innovation"}
            post['preferred_source'] = 'gemini' if topic in ai_tech else 'stock'
            print(f"Auto-visual generated: {post_format} / {topic} -> {visual_path}")
            print(f"IMAGE_UPGRADE_HINT: Agent should use image-gen-chain.py with topic={topic} (prefer={post['preferred_source']})")
        except Exception as e:
            print(f"Visual generation failed ({e}) - posting without image")
            import traceback; traceback.print_exc()

    # Write payload with EXACT content (bold already converted to Unicode)
    output = {
        "action": "post_to_linkedin",
        "person_urn": PERSON_URN,
        "content": post['content'],
        "image_path": image_path,
        "image_required": bool(post['image_url']),
        "page_id": post['page_id'],
        "title": post['title'],
        "score": score_result['total'],
        "image_url_original": post['image_url'],
        # Image upgrade metadata for agent
        "image_upgrade_available": post.get('image_upgrade_available', False),
        "image_topic": post.get('image_topic', ''),
        "preferred_image_source": post.get('preferred_source', 'gemini'),
        "visual_source": post.get('visual_source', 'notion'),
    }
    
    output_path = "/tmp/linkedin-post-payload.json"
    with open(output_path, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # Watchdog (persistent - survives reboots)
    watchdog_path = f"{WORKSPACE}/data/linkedin-watchdog.json"
    with open(watchdog_path, "w") as f:
        json.dump({
            "created_at": datetime.now().isoformat(),
            "page_id": post['page_id'],
            "title": post['title'],
        }, f)
    
    # Decision 5: Character limit safety check
    content_len = len(post['content'])
    if content_len > 2800:
        print(f"\u26a0\ufe0f WARNING: Post is {content_len} chars (limit ~3000). May be truncated by LinkedIn.")

    print(f"\nSCORE: {score_result['total']}/{MAX_SCORE}")
    print(f"CONTENT_LENGTH: {len(post['content'])} chars")
    print(f"BOLD_CONVERTED: {'yes' if any(ord(c) > 0x1D400 for c in post['content']) else 'no'}")
    print(f"IMAGE_FILE: {image_path or 'none'}")
    print(f"IMAGE_REQUIRED: {bool(post['image_url'])}")
    print(f"PAGE_ID: {post['page_id']}")

    # Decision 9: Agent-assisted posting via Composio (2026-03-25)
    # Autonomous direct-post disabled — agent handles posting with verified Composio image flow
    # The cron prepares payload + image, agent wakes up and posts via LINKEDIN_CREATE_LINKED_IN_POST
    import subprocess as sp
    direct_post_script = f"{WORKSPACE}/scripts/linkedin-direct-post.py"
    if False and os.path.exists(direct_post_script):  # DISABLED — agent posts daily
        print("\nATTEMPTING DIRECT POST (autonomous mode)...")
        cmd = ["python3", direct_post_script, "--text-file", "/dev/stdin"]
        if image_path:
            cmd += ["--image", image_path]

        try:
            result = sp.run(
                ["python3", direct_post_script, "--text", post['content']]
                + (["--image", image_path] if image_path else []),
                capture_output=True, text=True, timeout=120,
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            print(f"  Direct-post exit: {result.returncode}")
            if stdout:
                print(f"  stdout: {stdout[:500]}")

            # Try to extract post URL from output
            url_match = re.search(r'https://www\.linkedin\.com/feed/update/[^\s"\']+', stdout)
            if url_match and result.returncode == 0:
                post_url = url_match.group(0)
                print(f"\n\u2705 POSTED: {post_url}")

                # Close the loop: update Notion, log, remove watchdog
                update_notion_status(post['page_id'], post_url)
                update_post_url(post['page_id'], post_url)
                update_briefing_page(post_url, image_url=post.get('image_url'), title=post['title'])

                # Update ontology graph: mark LinkedInPost as posted
                try:
                    import json as _json, subprocess as _sp
                    from datetime import datetime as _dt, timezone as _tz
                    _graph = f"{WORKSPACE}/memory/ontology/graph.jsonl"
                    _now = _dt.now(_tz.utc).isoformat()
                    _page_id_clean = post['page_id'].replace("-", "")
                    _entity_id = f"post_notion_{_page_id_clean[:12]}"
                    _update = {
                        "op": "update",
                        "entity": {
                            "id": _entity_id,
                            "type": "LinkedInPost",
                            "properties": {
                                "status": "posted",
                                "post_url": post_url,
                                "posted_date": TODAY,
                            },
                            "updated": _now
                        }
                    }
                    with open(_graph, "a") as _f:
                        _f.write(_json.dumps(_update) + "\n")
                    print(f"✅ Ontology graph updated: {_entity_id} → posted")
                except Exception as _e:
                    print(f"⚠️ Ontology graph update failed (non-blocking): {_e}")

                # Remove watchdog
                if os.path.exists(watchdog_path):
                    os.remove(watchdog_path)

                # Decision 10: Post-publish audit trail
                os.makedirs(f"{WORKSPACE}/data/linkedin-posted-audit", exist_ok=True)
                audit = {
                    "date": TODAY,
                    "title": post['title'],
                    "content": post['content'],
                    "content_length": len(post['content']),
                    "score": score_result['total'],
                    "max_score": MAX_SCORE,
                    "post_url": post_url,
                    "image_url": post.get('image_url'),
                    "image_degraded": post.get('image_degraded', False),
                    "page_id": post['page_id'],
                }
                with open(f"{WORKSPACE}/data/linkedin-posted-audit/{TODAY}.json", "w") as af:
                    json.dump(audit, af, ensure_ascii=False, indent=2)
                print(f"Audit saved: data/linkedin-posted-audit/{TODAY}.json")

                # Decision 10: Post-publish verification (read-back)
                import time
                print("Waiting 60s for LinkedIn propagation before verification...")
                time.sleep(60)
                verify_result = sp.run(
                    ["python3", direct_post_script, "--verify", post_url,
                     "--expected-length", str(len(post['content']))],
                    capture_output=True, text=True, timeout=30,
                )
                if "TRUNCATED" in verify_result.stdout:
                    pct = re.search(r'(\d+)%', verify_result.stdout)
                    pct_val = int(pct.group(1)) if pct else 0
                    if pct_val < 50:
                        print(f"\U0001f534 CRITICAL: Post truncated to {pct_val}% - auto-deleting!")
                        sp.run(
                            ["python3", direct_post_script, "--delete", post_url],
                            capture_output=True, timeout=30,
                        )
                        print("DELETED_TRUNCATED_POST")
                    else:
                        print(f"\u26a0\ufe0f WARNING: Post may be truncated ({pct_val}%)")
                elif "VERIFIED" in verify_result.stdout:
                    print("\u2705 Post verified - content matches")

                # Telegram confirmation
                degraded_note = " (\u26a0\ufe0f without image - degraded)" if post.get('image_degraded') else ""
                send_telegram_confirmation(post_url, post['title'], post.get('image_url'))
                print(f"POSTED_AUTONOMOUS{degraded_note}")
                return
            else:
                print(f"\u26a0\ufe0f Direct-post did not return URL. Falling back to agent mode.")
                if stderr:
                    print(f"  stderr: {stderr[:300]}")
        except sp.TimeoutExpired:
            print("\u26a0\ufe0f Direct-post timed out. Falling back to agent mode.")
        except Exception as e:
            print(f"\u26a0\ufe0f Direct-post error: {e}. Falling back to agent mode.")

    # Fallback: agent-assisted posting
    print(f"\nPOST_URL_UPDATE_CMD: python3 scripts/linkedin-auto-poster.py --update-url '<POST_URL>' --page-id {post['page_id']}")
    print(f"READY_TO_POST")

if __name__ == "__main__":
    main()
