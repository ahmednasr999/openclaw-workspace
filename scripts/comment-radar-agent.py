#!/usr/bin/env python3
"""
LinkedIn Comment Radar v2 - Discover posts + draft comments in Ahmed's voice.
Outputs data/comment-radar.json for the briefing runner.

Flow: Tavily search -> fetch LinkedIn HTML -> extract content -> LLM drafts comments
"""
import json, re, ssl, sys, os, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
OUTPUT = DATA_DIR / "comment-radar.json"
CONFIG_DIR = WORKSPACE / "config"

# Gateway for LLM
GATEWAY_URL = "http://127.0.0.1:18789/v1/chat/completions"
MODEL = "minimax-portal/MiniMax-M2.7"

# Tavily API
TAVILY_KEY = os.environ.get("TAVILY_API_KEY")
if not TAVILY_KEY:
    tavily_conf = CONFIG_DIR / "tavily.json"
    if tavily_conf.exists():
        try:
            TAVILY_KEY = json.load(open(tavily_conf)).get("api_key")
        except:
            pass

# Topics for Ahmed
TOPICS = [
    "Digital Transformation",
    "PMO",
    "Program Management",
    "AI in business",
    "Leadership",
    "Healthcare IT",
    "Fintech",
]

GCC_TERMS = "Saudi OR UAE OR Dubai OR Riyadh OR Qatar OR Bahrain OR Kuwait OR Oman OR GCC OR MENA"

# Priority authors - posts from these people get boosted
PRIORITY_AUTHORS_FILE = CONFIG_DIR / "priority-authors.json"

# ==============================================================================
# LLM COMMENT DRAFTING — Anthropic XML-structured prompt
# ==============================================================================
COMMENT_SYSTEM = """You are Ahmed Nasr - PMO & Regional Engagement Lead with 20+ years in tech leadership across GCC. You comment on LinkedIn as a peer, not a fan."""

COMMENT_TASK = """Draft ONE LinkedIn comment per post. Each comment must be 2-4 lines. One shot, make it count."""

COMMENT_CONTEXT = """
Ahmed's background (use sparingly, only when relevant):
- 20+ years tech leadership across GCC (UAE, Saudi, Qatar, Bahrain)
- PMO excellence: governed $50M+ transformation programs across 15-hospital networks
- Digital transformation: led enterprise-wide rollouts in healthcare, education, fintech
- AI automation: building AI agent systems for operational efficiency
- Sectors: healthcare IT, fintech, education, government, hospitality

Your audience: The post author and their network - senior leaders, C-suite, directors, transformation leads in GCC/MENA.
"""

COMMENT_CONSTRAINTS = """
STRUCTURE (every comment must follow this):
1. OPEN WITH INSIGHT - a specific observation, data point, or contrarian angle about the post's topic. Never praise ("Great post", "Well said", "Totally agree", "Important topic", "Strong point").
2. ADD VALUE THE POST DIDN'T COVER - extend it, challenge it, or add a dimension the author missed. The reader should learn something new from YOUR comment. Reference your experience where natural - a project, a number, a region. Not bragging, just credibility.
3. END WITH A HOOK - a question back to the author OR a provocation that invites reply. This turns a comment into a thread.

RULES:
- 2-4 lines max. LinkedIn truncates long comments.
- Match the author's register - casual post = casual comment, formal post = formal comment. Peer tone always.
- NEVER use em dashes. Use commas or hyphens instead.
- NEVER: generic agreement, self-promotion, hashtag spam, emoji overload, restating the post in different words.
- NEVER: "Great insights!", "Thanks for sharing!", "Very relevant topic.", "Excellent breakdown", "At my company we..."
"""

COMMENT_OUTPUT = """
Return ONLY a valid JSON array with this exact structure - no markdown fences, no extra text:
[
  {"post_num": 1, "comment": "exact draft comment text here"},
  {"post_num": 2, "comment": "exact draft comment text here"}
]
"""

# MiniMax for regular comments (free), Sonnet for priority authors only
LLM_MODEL_DEFAULT = "minimax-portal/MiniMax-M2.7"
LLM_MODEL_PREMIUM = "anthropic/claude-sonnet-4-6"
LLM_TEMP = 0.7
COMMENT_TRACKER_PATH = DATA_DIR / "comment-tracker.json"


def load_gateway_token():
    """Load gateway auth token."""
    try:
        cfg = json.load(open("/root/.openclaw/openclaw.json"))
        return cfg.get("gateway", {}).get("auth", {}).get("token", "")
    except:
        return ""


def llm_call(prompt, max_tokens=1500, model=None):
    """Call LLM via gateway."""
    import requests

    gw_token = load_gateway_token()
    headers = {"Content-Type": "application/json"}
    if gw_token:
        headers["Authorization"] = f"Bearer {gw_token}"

    use_model = model or LLM_MODEL_DEFAULT
    try:
        resp = requests.post(GATEWAY_URL, json={
            "model": use_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": LLM_TEMP,
        }, headers=headers, timeout=120)
        if resp.status_code != 200:
            print(f"  LLM error: {resp.status_code}")
            return ""
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  LLM exception: {e}")
        return ""


def tavily_search(query, n=10):
    """Search using Tavily API."""
    if not TAVILY_KEY:
        print("  No Tavily API key!")
        return []

    payload = json.dumps({
        "api_key": TAVILY_KEY,
        "query": query,
        "max_results": n,
        "search_depth": "basic",
        "include_domains": ["linkedin.com"],
    }).encode()

    ctx = ssl.create_default_context()
    req = Request("https://api.tavily.com/search", data=payload,
                  headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=30, context=ctx) as r:
            data = json.loads(r.read().decode("utf-8", errors="ignore"))
        return data.get("results", [])
    except Exception as e:
        print(f"  Tavily error: {e}")
        return []


def fetch_post_content(url):
    """Fetch LinkedIn post HTML and extract author + content."""
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })
        ctx = ssl.create_default_context()
        with urlopen(req, timeout=15, context=ctx) as r:
            html = r.read(200_000).decode("utf-8", errors="ignore")

        author = "Unknown"
        content = ""

        # Method 1: Extract from URL slug (most reliable)
        # URL format: linkedin.com/posts/username_title-activity-123
        url_match = re.search(r'linkedin\.com/posts/([a-zA-Z0-9_-]+?)_', url)
        if url_match:
            slug = url_match.group(1)
            # Convert slug to name: "john-doe" → "John Doe", "company-name" → "Company Name"
            author_from_url = slug.replace("-", " ").replace("_", " ").title()
            if len(author_from_url) > 2:
                author = author_from_url

        # Method 2: og:title patterns (override URL if found)
        m = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        if m:
            title = m.group(1)
            # Pattern: "Author Name on LinkedIn: post content"
            am = re.match(r"^(.+?)\s+on\s+LinkedIn\s*:", title)
            if am and len(am.group(1).strip()) > 2:
                author = am.group(1).strip()
            else:
                # Pattern: "Title | Author posted on"
                am = re.match(r"^(.+?)\s*(?:\|)\s*(.+?)(?:\s+posted)", title)
                if am:
                    author = am.group(2).strip()
                else:
                    # Pattern: "Author's Post"
                    am2 = re.match(r"^(.+?)(?:'s Post|\s+posted on)", title)
                    if am2 and len(am2.group(1).strip()) > 2:
                        author = am2.group(1).strip()
        
        # Method 3: twitter:title meta (sometimes has cleaner author)
        tm = re.search(r'<meta name="twitter:title" content="([^"]+)"', html)
        if tm and author == "Unknown":
            tt = tm.group(1)
            tam = re.match(r"^(.+?)\s+on\s+LinkedIn", tt)
            if tam:
                author = tam.group(1).strip()

        # Extract content from meta description or og:description
        for pattern in [
            r'<meta name="description" content="([^"]*)"',
            r'<meta property="og:description" content="([^"]*)"',
        ]:
            m = re.search(pattern, html)
            if m and len(m.group(1)) > 20:
                content = m.group(1)[:500]
                break

        # Try to extract comment count from HTML (LinkedIn sometimes includes it)
        comment_count = 0
        cm = re.search(r'(\d+)\s*comment', html, re.IGNORECASE)
        if cm:
            try:
                comment_count = int(cm.group(1))
            except (ValueError, TypeError):
                pass

        return author, content, comment_count

    except Exception as e:
        return "Unknown", "", 0


def fetch_full_post_camofox(url):
    """Fetch full LinkedIn post content via Camofox (logged-in, sees complete post body).
    Returns post text up to 1500 chars, or empty string on failure."""
    import subprocess
    try:
        # Create tab
        result = subprocess.run(
            ["camofox-browser", "open", url],
            capture_output=True, text=True, timeout=30
        )
        tab_id = ""
        try:
            data = json.loads(result.stdout)
            tab_id = data.get("tabId", "")
        except:
            if "tabId:" in result.stdout:
                tab_id = result.stdout.strip().split("tabId:")[-1].strip()
        
        if not tab_id:
            return ""
        
        time.sleep(4)  # Wait for full render
        
        # Get snapshot
        result = subprocess.run(
            ["camofox-browser", "snapshot", tab_id],
            capture_output=True, text=True, timeout=30
        )
        content = result.stdout
        
        # Close tab
        subprocess.run(["camofox-browser", "close", tab_id], capture_output=True, timeout=10)
        
        if not content or len(content) < 100:
            return ""
        
        # Extract post body from snapshot (look for main content area)
        # Remove navigation, sidebar, footer noise
        lines = content.split("\n")
        body_lines = []
        capture = False
        for line in lines:
            stripped = line.strip()
            # Skip empty lines and navigation elements
            if not stripped:
                continue
            # Skip common LinkedIn chrome
            if any(skip in stripped.lower() for skip in [
                "linkedin", "sign in", "join now", "skip to main", "messaging",
                "notifications", "home", "my network", "jobs", "more actions",
                "report this", "copy link", "repost", "send", "like button"
            ]):
                continue
            # Capture substantive text lines (>20 chars, not buttons/labels)
            if len(stripped) > 20:
                body_lines.append(stripped)
        
        text = "\n".join(body_lines[:30])  # Cap at ~30 substantive lines
        return text[:1500] if text else ""
        
    except Exception as e:
        print(f"    Camofox error: {e}")
        return ""


def extract_linkedin_posts(results):
    """Filter for LinkedIn post URLs only."""
    posts = []
    seen_urls = set()

    for r in results:
        url = r.get("url", "")
        if "linkedin.com/posts/" not in url and "linkedin.com/feed/update/" not in url:
            continue

        clean_url = url.split("?")[0]
        if clean_url in seen_urls:
            continue
        seen_urls.add(clean_url)

        title = r.get("title", "")
        snippet = r.get("content", r.get("snippet", ""))

        # Extract author: try URL slug first, then title patterns
        author = "Unknown"
        url_m = re.search(r'linkedin\.com/posts/([a-zA-Z0-9_-]+?)_', clean_url)
        if url_m:
            slug = url_m.group(1)
            author = slug.replace("-", " ").replace("_", " ").title()
        # Override with title if it has a cleaner name
        m = re.match(r"^(.+?)(?:\s+on LinkedIn|\s+posted on|\s*\|)", title)
        if m and len(m.group(1).strip()) > 2 and len(m.group(1).strip()) < 50:
            author = m.group(1).strip()

        posts.append({
            "url": clean_url,
            "author": author,
            "title": title[:200],
            "preview": snippet[:300] if snippet else title,
            "published_date": r.get("published_date", ""),
            "source": "tavily",
        })

    return posts


def load_priority_authors():
    """Load optional priority authors list."""
    if PRIORITY_AUTHORS_FILE.exists():
        try:
            return json.load(open(PRIORITY_AUTHORS_FILE))
        except:
            pass
    return []


def score_post(post, priority_authors=None):
    """Score a post for comment opportunity (PQS 0-130).
    
    Dimensions:
    - Expertise overlap (0-30): Would Ahmed's comment add unique value?
    - Author signal (0-25): Is this person worth engaging with?
    - GCC relevance (0-20): Regional alignment
    - Discussion quality (0-20): Does the post invite dialogue?
    - Recency (0-15): Early comments get 3-5x more visibility
    - Crowd penalty (-30 to +5): Avoid invisible comments
    """
    score = 0
    preview = (post.get("full_content", "") or post.get("preview", "") + " " + post.get("title", "")).lower()
    author = post.get("author", "").lower()

    # Expertise overlap (30 points) - Ahmed's specific value-add areas
    # High overlap = Ahmed can write a comment that adds genuine insight
    expertise_high = ["pmo", "program management", "project management office",
                      "digital transformation", "healthcare it", "hospital",
                      "fintech", "payment", "banking technology",
                      "governance", "portfolio management", "change management",
                      "enterprise architecture", "pmp", "prince2", "safe"]
    expertise_med = ["ai agent", "ai automation", "leadership", "c-suite",
                     "executive", "strategy", "operational excellence",
                     "agile transformation", "devops", "cloud migration"]
    expertise_low = ["artificial intelligence", "machine learning", "startup",
                     "technology", "innovation", "digital"]

    high_hits = sum(1 for t in expertise_high if t in preview)
    med_hits = sum(1 for t in expertise_med if t in preview)
    low_hits = sum(1 for t in expertise_low if t in preview)

    if high_hits >= 2:
        score += 30
    elif high_hits == 1:
        score += 22
    elif med_hits >= 2:
        score += 18
    elif med_hits == 1:
        score += 12
    elif low_hits >= 1:
        score += 5
    # No expertise overlap = 0 points (harsh but correct)

    # Author signal (25 points) - check AUTHOR name, not post body
    exec_titles = ["chief", "ceo", "coo", "cto", "cio", "vp", "vice president",
                    "director", "head of", "founder", "managing", "partner", "president"]
    mid_titles = ["manager", "lead", "principal", "senior"]
    # Check author name/title specifically (not preview body)
    author_context = author + " " + post.get("title", "").lower()[:100]
    if any(w in author_context for w in exec_titles):
        score += 25
    elif any(w in author_context for w in mid_titles):
        score += 15
    else:
        score += 5

    # Priority author boost (+15)
    if priority_authors:
        for pa in priority_authors:
            pa_name = pa.get("name", "").lower() if isinstance(pa, dict) else str(pa).lower()
            if pa_name and pa_name in author:
                score += 15
                post["priority"] = True
                break

    # GCC relevance (20 points)
    gcc_terms = ["saudi", "uae", "dubai", "riyadh", "qatar", "bahrain", "kuwait",
                 "oman", "gcc", "mena", "abu dhabi", "jeddah", "doha", "muscat"]
    gcc_hits = sum(1 for t in gcc_terms if t in preview)
    score += min(gcc_hits * 6, 20)

    # Discussion quality (20 points) - does the post invite substantive dialogue?
    strong_discussion = ["what do you think", "thoughts?", "unpopular opinion",
                         "controversial", "disagree", "debate", "wrong about",
                         "hot take", "challenge"]
    mild_discussion = ["agree", "lesson", "mistake", "learned", "surprised",
                       "question", "curious"]
    if any(m in preview for m in strong_discussion):
        score += 20
    elif any(m in preview for m in mild_discussion):
        score += 10
    else:
        score += 3

    # Recency bonus (15 points) - early comments get 3-5x more visibility
    pub_date = post.get("published_date", "")
    if pub_date:
        try:
            pub_dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600
            if age_hours < 24:
                score += 15
            elif age_hours < 48:
                score += 10
            elif age_hours < 72:
                score += 5
        except (ValueError, TypeError):
            pass

    # Crowd penalty - steeper than any bonus to prevent wasted comments
    comment_count = post.get("comment_count", 0)
    if comment_count > 150:
        score -= 30  # Your comment is invisible in 150+ thread
    elif comment_count > 50:
        score -= 15  # Crowded, low visibility
    elif comment_count > 30:
        score -= 5   # Getting crowded
    elif 5 <= comment_count <= 30:
        score += 5   # Sweet spot - active but visible
    # 0 comments: no bonus/penalty (could be new OR dead)

    # Zero-comment + old = dead post penalty
    if comment_count == 0 and pub_date:
        try:
            pub_dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600
            if age_hours > 12:
                score -= 10  # Zero comments after 12h = dead post
        except (ValueError, TypeError):
            pass

    return max(0, min(score, 130))


def parse_llm_comments(response):
    """Parse LLM response into comment list. Returns list of {post_num, comment}."""
    if not response:
        return []
    try:
        response = response.strip()
        if response.startswith("```"):
            response = re.sub(r"```\w*\n?", "", response).strip()
        return json.loads(response)
    except json.JSONDecodeError:
        m = re.search(r'\[.*\]', response, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except:
                pass
        print("  Failed to parse LLM comments")
        return []


def draft_comments(posts):
    """Use LLM to draft comments. MiniMax for regular, Sonnet for priority authors."""
    if not posts:
        return posts

    # Split into priority and regular
    priority_posts = [(i, p) for i, p in enumerate(posts) if p.get("priority")]
    regular_posts = [(i, p) for i, p in enumerate(posts) if not p.get("priority")]

    def build_prompt(post_list):
        post_descriptions = []
        for seq, (orig_idx, p) in enumerate(post_list, 1):
            content = p.get("full_content", "") or p.get("preview", "")
            post_descriptions.append(
                f"POST #{seq}:\n"
                f"Author: {p.get('author', 'Unknown')}\n"
                f"Content: {content[:400]}\n"
            )
        posts_section = "\n".join(post_descriptions)
        return f"""<task>{COMMENT_TASK.strip()}</task>

<context>{COMMENT_CONTEXT.strip()}</context>

<constraints>{COMMENT_CONSTRAINTS.strip()}</constraints>

<output_format>{COMMENT_OUTPUT.strip()}</output_format>

--- LINKEDIN POSTS ---
{posts_section}"""

    # Draft priority posts with Sonnet 4.6
    if priority_posts:
        print(f"  Drafting {len(priority_posts)} priority comments (Sonnet 4.6)...")
        prompt = build_prompt(priority_posts)
        response = llm_call(prompt, max_tokens=2000, model=LLM_MODEL_PREMIUM)
        comments = parse_llm_comments(response)
        for c in comments:
            seq = c.get("post_num", 0) - 1
            if 0 <= seq < len(priority_posts):
                orig_idx = priority_posts[seq][0]
                comment = c.get("comment", "").replace("\u2014", " - ").replace("\u2013", "-")
                posts[orig_idx]["draft_comment"] = comment
                posts[orig_idx]["model_used"] = "sonnet"

    # Draft regular posts with MiniMax (free)
    if regular_posts:
        print(f"  Drafting {len(regular_posts)} regular comments (MiniMax)...")
        prompt = build_prompt(regular_posts)
        response = llm_call(prompt, max_tokens=2000, model=LLM_MODEL_DEFAULT)
        comments = parse_llm_comments(response)
        for c in comments:
            seq = c.get("post_num", 0) - 1
            if 0 <= seq < len(regular_posts):
                orig_idx = regular_posts[seq][0]
                comment = c.get("comment", "").replace("\u2014", " - ").replace("\u2013", "-")
                posts[orig_idx]["draft_comment"] = comment
                posts[orig_idx]["model_used"] = "minimax"

    drafted = sum(1 for p in posts if p.get("draft_comment"))
    print(f"  Drafted {drafted}/{len(posts)} comments")

    return posts


def load_comment_tracker():
    """Load comment tracker for dedup and feedback."""
    if COMMENT_TRACKER_PATH.exists():
        try:
            return json.load(open(COMMENT_TRACKER_PATH))
        except:
            pass
    return {"comments": [], "stats": {"total_posted": 0, "total_drafted": 0}}


def save_comment_tracker(tracker):
    """Save comment tracker."""
    COMMENT_TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    json.dump(tracker, open(COMMENT_TRACKER_PATH, "w"), indent=2)


def run_radar():
    """Main radar execution."""
    print("=== LinkedIn Comment Radar v2 ===")
    print(f"Time: {datetime.now(timezone(timedelta(hours=2))).strftime('%Y-%m-%d %H:%M')}")

    priority_authors = load_priority_authors()
    if priority_authors:
        print(f"Priority authors: {len(priority_authors)}")

    all_posts = []

    # Tavily searches - topic clusters
    queries = [
        f'site:linkedin.com/posts ("digital transformation" OR "PMO" OR "program management") ({GCC_TERMS})',
        f'site:linkedin.com/posts ("AI" OR "artificial intelligence") (business OR enterprise OR strategy) ({GCC_TERMS})',
        f'site:linkedin.com/posts ("leadership" OR "healthcare" OR "fintech") ({GCC_TERMS})',
    ]

    for i, query in enumerate(queries, 1):
        print(f"  Search {i}/{len(queries)}...")
        results = tavily_search(query, n=10)
        posts = extract_linkedin_posts(results)
        print(f"    Found {len(posts)} LinkedIn posts")
        all_posts.extend(posts)
        time.sleep(1)

    if not all_posts:
        print("  No posts found. Check Tavily API key.")
        output = {
            "generated": datetime.now(timezone.utc).isoformat(),
            "version": 2,
            "posts_found": 0,
            "top_posts": [],
            "status": "no_results",
        }
        json.dump(output, open(OUTPUT, "w"), indent=2)
        return

    # Load already-commented URLs from tracker
    commented_urls = set()
    tracker = load_comment_tracker()
    for entry in tracker.get("comments", []):
        url = entry.get("url", "")
        if url:
            commented_urls.add(url.split("?")[0])
    
    # Deduplicate + skip already-commented
    seen = set()
    unique = []
    skipped_commented = 0
    for p in all_posts:
        clean = p["url"].split("?")[0]
        if clean in seen:
            continue
        seen.add(clean)
        if clean in commented_urls:
            skipped_commented += 1
            continue
        unique.append(p)

    if skipped_commented:
        print(f"\n  Skipped {skipped_commented} already-commented posts")
    print(f"  Unique posts: {len(unique)}")

    # Fast pre-screen: enrich top candidates with logged-out HTML (author names + comment counts)
    print("  Pre-screening posts from LinkedIn HTML...")
    for p in unique[:15]:
        author, content, comment_count = fetch_post_content(p["url"])
        if author != "Unknown":
            p["author"] = author
        if content:
            p["full_content"] = content
        if comment_count:
            p["comment_count"] = comment_count
        time.sleep(0.5)

    # Score and rank
    for post in unique:
        post["pqs"] = score_post(post, priority_authors)

    unique.sort(key=lambda x: (-x.get("priority", False), -x["pqs"]))
    
    # Content-level dedup: don't show 3 posts about the same story
    # Compare preview text — if >50% word overlap, skip the lower-scored one
    def word_set(text):
        return set(re.findall(r'\w{4,}', text.lower()))
    
    top = []
    for post in unique:
        if len(top) >= 5:
            break
        post_words = word_set(post.get("preview", "") + " " + post.get("title", ""))
        is_duplicate = False
        for existing in top:
            existing_words = word_set(existing.get("preview", "") + " " + existing.get("title", ""))
            if not post_words or not existing_words:
                continue
            overlap = len(post_words & existing_words) / max(1, min(len(post_words), len(existing_words)))
            if overlap > 0.5:
                is_duplicate = True
                break
        if not is_duplicate:
            top.append(post)
    
    if len(top) < 5:
        # Fill remaining with next best non-duplicate posts
        for post in unique:
            if len(top) >= 5:
                break
            if post not in top:
                top.append(post)

    print(f"\n  Top 5 posts:")
    for i, p in enumerate(top, 1):
        pri = " [PRIORITY]" if p.get("priority") else ""
        print(f"  #{i} PQS:{p['pqs']} | {p['author'][:25]} | {p['title'][:50]}{pri}")

    # Deep-fetch full post content via Camofox for top-5 (logged-in, sees full post)
    print("\n  Deep-fetching full content via Camofox...")
    for p in top:
        full = fetch_full_post_camofox(p["url"])
        if full and len(full) > len(p.get("full_content", "")):
            p["full_content"] = full
            print(f"    {p['author'][:20]}: {len(full)} chars (upgraded)")
        else:
            print(f"    {p['author'][:20]}: kept pre-screen content ({len(p.get('full_content', ''))} chars)")
        time.sleep(2)  # Rate limit for LinkedIn

    # Draft comments via LLM
    print("\n  Drafting comments...")
    top = draft_comments(top)

    drafted = sum(1 for p in top if p.get("draft_comment"))
    print(f"  Drafted {drafted}/{len(top)} comments")

    # Clean output (remove full_content to save space)
    for p in top:
        p.pop("full_content", None)
        p.pop("source", None)

    output = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "version": 2,
        "posts_found": len(unique),
        "top_posts": top,
        "comments_drafted": drafted,
        "status": "ok",
    }

    json.dump(output, open(OUTPUT, "w"), indent=2)

    # Update comment tracker with drafted comments
    tracker = load_comment_tracker()
    tracker["stats"]["total_drafted"] = tracker["stats"].get("total_drafted", 0) + drafted
    tracker["last_radar_run"] = datetime.now(timezone.utc).isoformat()
    save_comment_tracker(tracker)

    print(f"\n=== Done: {len(top)} posts + {drafted} draft comments saved ===")


if __name__ == "__main__":
    run_radar()
