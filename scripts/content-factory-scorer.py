#!/usr/bin/env python3
"""
Content Factory Scorer v1.0
============================
Phase 1 of Content Factory: Quality Scoring + Topic Weighting + Format Tagging

Runs AFTER rss-intelligence-crawler.py, processes articles with Status="New".

Scoring layers (from video insights):
  Layer 1: Source Quality (is the source reputable?)
  Layer 2: Topic Relevance + Weight (Core 60% / Supporting 30% / Occasional 10%)
  Layer 3: Content Potential — which LinkedIn post format does this enable?
           (Brandjacking / Newsjacking / Namejacking / Hot Take — from Diandra Escobar)

Binary eval criteria (from AI Andy / Karpathy Autoresearch):
  10 yes/no questions scored for each article

Output: Updates RSS Intelligence DB with Quality Score, Topic Weight, Post Format,
        Hook Score, Priority, Posting Angle, and Executive Summary.

Cron: 30 7 * * * (runs at 7:30 AM Cairo, after crawler at 7:00 AM)
"""
import json, os, ssl, sys, urllib.request, re, time
from datetime import datetime, timezone, timedelta

WORKSPACE = "/root/.openclaw/workspace"
NOTION_TOKEN = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
RSS_DB = "32e8d599-a162-8180-9e3a-fbfc17a84e49"
TELEGRAM_BOT = "8213291111:AAHCk2J4XIRQaTsBkACl_Xpla7LFvVx1304"
TELEGRAM_CHAT = "866838380"
CAIRO = timezone(timedelta(hours=2))

LOG_FILE = f"{WORKSPACE}/logs/content-factory-scorer.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

ctx = ssl.create_default_context()

# ── Topic Weighting (from Content Factory design) ────────────────────────────
TOPIC_WEIGHTS = {
    # Core (60%) — Ahmed's primary positioning
    "AI": {"tier": "Core (60%)", "weight": 0.6, "pillar": "AI & Automation"},
    "Digital Transformation": {"tier": "Core (60%)", "weight": 0.6, "pillar": "Digital Transformation"},
    "PMO": {"tier": "Core (60%)", "weight": 0.6, "pillar": "PMO & Program Management"},
    "Operation Excellence": {"tier": "Core (60%)", "weight": 0.6, "pillar": "PMO & Program Management"},
    # Supporting (30%) — industry credibility
    "Healthcare": {"tier": "Supporting (30%)", "weight": 0.3, "pillar": "FinTech & HealthTech"},
    "HealthTech": {"tier": "Supporting (30%)", "weight": 0.3, "pillar": "FinTech & HealthTech"},
    "FinTech": {"tier": "Supporting (30%)", "weight": 0.3, "pillar": "FinTech & HealthTech"},
    # Occasional (10%) — thought leadership variety
    "Strategy": {"tier": "Occasional (10%)", "weight": 0.1, "pillar": "Leadership & Strategy"},
}

# ── Source Quality Scores ────────────────────────────────────────────────────
SOURCE_QUALITY = {
    # Tier 1: Premium (0.9-0.95) — HBR, MIT, Reuters, etc.
    "sloanreview.mit.edu": 0.95,
    "hbr.org": 0.95,
    "reuters.com": 0.9,
    "bloomberg.com": 0.9,
    "mckinsey.com": 0.9,
    "deloitte.com": 0.9,
    "forbes.com": 0.85,
    "venturebeat.com": 0.9,
    "wired.com": 0.85,
    "techcrunch.com": 0.85,
    "bbc.com": 0.85,
    "ft.com": 0.9,
    "wsj.com": 0.9,
    "economist.com": 0.9,
    # Tier 2: Strong (0.75-0.85) — industry publications
    "fs.blog": 0.85,
    "healthcareittoday.com": 0.75,
    "mobihealthnews.com": 0.75,
    "connectingthedotsinfin.tech": 0.75,
    "pmo.zalando.com": 0.75,
    "leanblog.org": 0.8,
    "indiatoday.in": 0.7,
    "cbc.ca": 0.8,
    "fedscoop.com": 0.75,
    "fiercehealthcare.com": 0.8,
    "beckershospitalreview.com": 0.75,
    "projectmanager.com": 0.7,
    "pmi.org": 0.85,
    # Social platforms — scored by platform, boosted by author below
    "linkedin.com": 0.7,
    "twitter.com": 0.65,
    "x.com": 0.65,
    "medium.com": 0.6,
    "substack.com": 0.7,
}

# ── Authority Boost: Known thought leaders ───────────────────────────────────
# If source or title references these names/handles, boost quality +2
AUTHORITY_FIGURES = [
    # Tech/AI leadership
    "josh bersin", "bersin", "daniel miessler", "miessler",
    "satya nadella", "nadella", "sam altman", "altman",
    "jensen huang", "marc benioff", "benioff",
    "marc andreessen", "andreessen", "ben horowitz",
    # Consulting/Strategy
    "mckinsey", "deloitte", "gartner", "forrester", "bain",
    "peter drucker", "clayton christensen", "michael porter",
    "simon sinek", "adam grant",
    # PMO/Agile
    "martin fowler", "kent beck", "mike cohn",
    # Healthcare
    "eric topol", "atul gawande",
    # FinTech
    "cathie wood",
    # Content/LinkedIn influencers in Ahmed's space
    "lenny rachitsky", "shreyas doshi", "julie zhuo",
]

# ── Top-tier source domains (get source quality boost) ───────────────────────
PREMIUM_DOMAINS = [
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com", "economist.com",
    "hbr.org", "sloanreview.mit.edu", "mckinsey.com", "deloitte.com",
    "forbes.com", "bbc.com", "wired.com", "nature.com",
]

# ── Binary Eval Criteria (inspired by AI Andy / Karpathy Autoresearch) ───────
# 10 yes/no questions for LinkedIn content potential
EVAL_CRITERIA = [
    "Does the title describe a result, transformation, or trend (not just a feature)?",
    "Does the article reference a specific company, person, or brand Ahmed's audience would recognize?",
    "Could Ahmed frame this as 'what you should do about it' (not just 'what happened')?",
    "Is there a contrarian or surprising angle that challenges conventional wisdom?",
    "Does this touch a pain point Ahmed's target audience (senior tech leaders) actually feels?",
    "Is the topic timely enough to post about within the next 7 days?",
    "Could this be framed around a person or story (not just abstract concepts)?",
    "Does this avoid sounding like a press release or corporate announcement?",
    "Would a busy executive stop scrolling to read a post about this?",
    "Can Ahmed add genuine personal expertise or experience to this topic?",
]

# ── Logging ──────────────────────────────────────────────────────────────────
def log(msg):
    ts = datetime.now(CAIRO).strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ── HTTP helpers ─────────────────────────────────────────────────────────────
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

def fetch_url_text(url, max_chars=3000):
    """Fetch article text for scoring (lightweight, no JS)."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 ContentFactory/1.0"
        })
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
        # Strip HTML tags, get plain text
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]
    except Exception as e:
        return ""

def telegram_msg(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT}/sendMessage"
    data = json.dumps({"chat_id": TELEGRAM_CHAT, "text": text, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            return json.loads(r.read())
    except:
        pass

# ── Scoring Engine ───────────────────────────────────────────────────────────

def score_source_quality(source_domain):
    """Layer 1: Source reputation score (0-1)."""
    source_lower = source_domain.lower()
    for domain, score in SOURCE_QUALITY.items():
        if domain in source_lower:
            return score
    # Boost for premium domains even if not exact match
    for pd in PREMIUM_DOMAINS:
        if pd in source_lower:
            return 0.85
    return 0.5  # Unknown source gets neutral

def get_authority_boost(title, source, summary=""):
    """Detect thought leader references. Returns boost points (0-2)."""
    combined = f"{title} {source} {summary}".lower()
    for name in AUTHORITY_FIGURES:
        if name in combined:
            return 2  # Thought leader = +2 quality points
    return 0

def get_engagement_signals(title, summary=""):
    """Detect high-engagement indicators from title/text. Returns boost (0-1)."""
    combined = f"{title} {summary}".lower()
    signals = 0
    # Viral indicators
    if any(w in combined for w in ["comments", "reactions", "viral", "trending", "million views"]):
        signals += 1
    # Strong numbers (dollar amounts, percentages, large figures)
    import re
    if re.search(r'\$\d+[bmk]|\d+%|\d{3,}', combined, re.IGNORECASE):
        signals += 0.5
    # Controversy/debate (high engagement driver)
    if any(w in combined for w in ["controversy", "backlash", "debate", "fired", "dropped", "collapses"]):
        signals += 0.5
    return min(signals, 1)  # Cap at 1

def get_topic_weight(categories):
    """Layer 2: Topic weight based on Ahmed's positioning strategy."""
    best_weight = 0.1
    best_tier = "Occasional (10%)"
    best_pillar = "Leadership & Strategy"
    for cat in categories:
        if cat in TOPIC_WEIGHTS:
            tw = TOPIC_WEIGHTS[cat]
            if tw["weight"] > best_weight:
                best_weight = tw["weight"]
                best_tier = tw["tier"]
                best_pillar = tw["pillar"]
    return best_weight, best_tier, best_pillar

def score_content_potential(title, summary, article_text, categories):
    """Layer 3: LinkedIn post format detection + binary eval scoring.
    
    Returns: (quality_score 0-10, formats list, hook_score 0-10, posting_angle str, exec_summary str)
    """
    # Combine available text
    context = f"Title: {title}\nSummary: {summary}\nCategories: {', '.join(categories)}"
    if article_text:
        context += f"\nArticle excerpt: {article_text[:1500]}"
    
    # ── Format Detection (Diandra's 4 types) ──
    formats = []
    title_lower = title.lower()
    summary_lower = (summary or "").lower()
    text_lower = (article_text or "").lower()
    combined = f"{title_lower} {summary_lower} {text_lower}"
    
    # Brandjacking: mentions well-known brands/companies
    brand_signals = ["google", "amazon", "apple", "microsoft", "tesla", "openai", "meta",
                     "nvidia", "netflix", "uber", "airbnb", "stripe", "coinbase", "jpmorgan",
                     "mckinsey", "deloitte", "accenture", "ibm", "salesforce", "oracle",
                     "epic", "cerner", "philips", "siemens", "ge health"]
    if any(brand in combined for brand in brand_signals):
        formats.append("Brandjacking")
    
    # Newsjacking: breaking news, announcements, launches, reports
    news_signals = ["announced", "launches", "released", "report shows", "study finds",
                    "breaking", "just released", "new report", "survey reveals", "data shows",
                    "according to", "latest", "2026", "2025", "this week", "today"]
    if sum(1 for s in news_signals if s in combined) >= 2:
        formats.append("Newsjacking")
    
    # Namejacking: references specific people
    name_signals = ["ceo", "cto", "cio", "founder", "says", "argues", "believes",
                    "according to", "expert", "leader", "executive", "professor"]
    if sum(1 for s in name_signals if s in combined) >= 2:
        formats.append("Namejacking")
    
    # Hot Take: contrarian, debate, controversial
    hottake_signals = ["wrong", "myth", "actually", "unpopular", "controversial", "debate",
                       "overrated", "underrated", "stop", "why most", "the truth about",
                       "nobody talks about", "hot take", "contrary", "rethink", "challenge"]
    if any(s in combined for s in hottake_signals):
        formats.append("Hot Take")
    
    if not formats:
        formats.append("Newsjacking")  # Default: most articles are news-based
    
    # ── Binary Eval Scoring (AI Andy inspired) ──
    eval_score = 0
    
    # Q1: Title describes result/transformation/trend?
    result_words = ["transform", "disrupts", "revolution", "growth", "impact", "change",
                    "future", "trend", "shift", "rise", "decline", "crisis", "opportunity"]
    if any(w in title_lower for w in result_words):
        eval_score += 1
    
    # Q2: References recognizable company/person/brand?
    if "Brandjacking" in formats or "Namejacking" in formats:
        eval_score += 1
    
    # Q3: "What you should do" framing possible?
    actionable_words = ["how to", "guide", "strategy", "framework", "steps", "tips",
                        "approach", "solution", "implement", "adopt", "leverage"]
    if any(w in combined for w in actionable_words):
        eval_score += 1
    
    # Q4: Contrarian/surprising angle?
    if "Hot Take" in formats:
        eval_score += 1
    
    # Q5: Touches senior leader pain point?
    pain_words = ["budget", "roi", "cost", "efficiency", "scale", "talent", "risk",
                  "compliance", "deadline", "stakeholder", "board", "governance",
                  "transformation", "migration", "integration"]
    if any(w in combined for w in pain_words):
        eval_score += 1
    
    # Q6: Timely (within 7 days)?
    time_words = ["2026", "this week", "today", "just", "new", "latest", "recently", "march"]
    if any(w in combined for w in time_words):
        eval_score += 1
    
    # Q7: Person/story framing possible?
    if "Namejacking" in formats or "Brandjacking" in formats:
        eval_score += 1
    
    # Q8: Not a press release?
    press_words = ["pleased to announce", "is excited to", "partnership with",
                   "proud to", "we are thrilled"]
    if not any(w in combined for w in press_words):
        eval_score += 1
    
    # Q9: Would executive stop scrolling?
    scroll_stop = len(formats) >= 2 or eval_score >= 5
    if scroll_stop:
        eval_score += 1
    
    # Q10: Ahmed can add personal expertise?
    ahmed_topics = ["program management", "pmo", "digital transformation", "healthcare",
                    "ai", "automation", "project", "agile", "waterfall", "governance",
                    "stakeholder", "budget", "executive", "leadership", "fintech"]
    if any(t in combined for t in ahmed_topics):
        eval_score += 1
    
    # ── Authority + Engagement Boosts ──
    authority = get_authority_boost(title, "", summary)  # +0 or +2
    engagement = get_engagement_signals(title, summary)  # 0 to 1
    
    # ── Composite Scores ──
    quality_score = min(10, eval_score + authority + round(engagement))  # 0-10 scale, capped
    hook_score = min(10, eval_score + authority + len(formats))  # Formats boost hook potential
    
    # ── Posting Angle ──
    if "Newsjacking" in formats:
        angle = f"Breaking: {title[:60]}... Here's what this means for [your industry]"
    elif "Brandjacking" in formats:
        brand = next((b for b in brand_signals if b in combined), "this company")
        angle = f"What {brand.title()}'s move teaches us about [transformation/AI/leadership]"
    elif "Hot Take" in formats:
        angle = f"Unpopular opinion: {title[:50]}... and why most leaders get this wrong"
    elif "Namejacking" in formats:
        angle = f"[Leader name] just said something about {categories[0] if categories else 'tech'} that every exec should hear"
    else:
        angle = f"3 things senior leaders should know about: {title[:60]}"
    
    # ── Executive Summary ──
    exec_summary = f"{'|'.join(formats)} opportunity. Eval: {eval_score}/10. "
    if summary:
        exec_summary += summary[:200]
    
    return quality_score, formats, hook_score, angle, exec_summary

def recency_multiplier(published_date_str):
    """Penalize old content. Articles >30 days old get heavily discounted."""
    if not published_date_str:
        return 0.5  # Unknown date = assume stale
    try:
        pub = datetime.fromisoformat(published_date_str.replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - pub).days
        if age_days <= 3:
            return 1.0   # Fresh - full score
        elif age_days <= 7:
            return 0.9   # This week - slight discount
        elif age_days <= 14:
            return 0.7   # Last 2 weeks
        elif age_days <= 30:
            return 0.5   # Last month
        else:
            return 0.2   # Stale - heavy penalty
    except:
        return 0.5

def calculate_priority(quality_score, topic_weight, source_quality, recency=1.0):
    """Weighted priority: Quality (40%) + Topic Weight (25%) + Source (15%) + Recency (20%)."""
    composite = (quality_score / 10 * 0.4) + (topic_weight * 0.25) + (source_quality * 0.15) + (recency * 0.2)
    if composite >= 0.55:
        return "High"
    elif composite >= 0.3:
        return "Medium"
    else:
        return "Low"

# ── Main Pipeline ────────────────────────────────────────────────────────────

def get_unscored_articles():
    """Get articles with Status=New (not yet scored)."""
    pages = notion_req("POST", f"/databases/{RSS_DB}/query", {
        "filter": {
            "property": "Status",
            "select": {"equals": "New"}
        },
        "page_size": 50
    })
    return pages.get("results", [])

def update_article_scores(page_id, quality_score, hook_score, formats, topic_tier,
                          pillar, priority, posting_angle, exec_summary, format_score):
    """Update article with all scoring data."""
    props = {
        "Quality Score": {"number": quality_score},
        "Hook Score": {"number": hook_score},
        "Format Score": {"number": format_score},
        "Post Format": {"multi_select": [{"name": f} for f in formats]},
        "Topic Weight": {"select": {"name": topic_tier}},
        "Content Pillar": {"multi_select": [{"name": pillar}]},
        "Priority": {"select": {"name": priority}},
        "Posting Angle": {"rich_text": [{"text": {"content": posting_angle[:500]}}]},
        "Executive Summary": {"rich_text": [{"text": {"content": exec_summary[:500]}}]},
        "Status": {"select": {"name": "Read"}},  # Mark as processed
    }
    return notion_req("PATCH", f"/pages/{page_id}", {"properties": props})

def main():
    now = datetime.now(CAIRO)
    log(f"=== Content Factory Scorer v1.0 === {now.strftime('%Y-%m-%d %H:%M')} Cairo")
    
    articles = get_unscored_articles()
    log(f"Found {len(articles)} unscored articles")
    
    if not articles:
        log("Nothing to score. Done.")
        return
    
    scored = 0
    gold = []  # High priority items
    errors = 0
    
    for page in articles:
        props = page.get("properties", {})
        page_id = page["id"]
        
        # Extract data
        title = "".join([t.get("plain_text", "") for t in props.get("Name", {}).get("title", [])])
        url = props.get("URL", {}).get("url", "")
        source = "".join([t.get("plain_text", "") for t in props.get("Source", {}).get("rich_text", [])])
        summary = "".join([t.get("plain_text", "") for t in props.get("Summary", {}).get("rich_text", [])])
        categories = [c.get("name", "") for c in props.get("Category", {}).get("multi_select", [])]
        
        if not title:
            continue
        
        log(f"  Scoring: {title[:65]}")
        
        # Fetch article text for deeper scoring (with rate limiting)
        article_text = ""
        if url:
            article_text = fetch_url_text(url)
            time.sleep(0.5)
        
        # Layer 1: Source quality
        source_quality = score_source_quality(source)
        
        # Layer 2: Topic weight
        topic_weight, topic_tier, pillar = get_topic_weight(categories)
        
        # Layer 3: Content potential + format detection
        quality_score, formats, hook_score, posting_angle, exec_summary = \
            score_content_potential(title, summary, article_text, categories)
        
        # Layer 4: Recency decay
        published = props.get("Published", {}).get("date", {})
        pub_date = published.get("start", "") if published else ""
        recency = recency_multiplier(pub_date)
        
        # Composite format score (quality * topic weight * source * recency)
        format_score = round(quality_score * (1 + topic_weight) * source_quality * recency, 1)
        
        # Priority
        priority = calculate_priority(quality_score, topic_weight, source_quality, recency)
        
        try:
            update_article_scores(
                page_id, quality_score, hook_score, formats, topic_tier,
                pillar, priority, posting_angle, exec_summary, format_score
            )
            scored += 1
            
            if priority == "High":
                gold.append({
                    "title": title[:80],
                    "formats": formats,
                    "score": quality_score,
                    "format_score": format_score,
                    "angle": posting_angle[:120],
                    "categories": categories,
                })
            
            time.sleep(0.5)  # Notion rate limit
            
        except Exception as e:
            log(f"    ERROR: {e}")
            errors += 1
    
    # ── Summary ──
    log(f"\n=== Done ===")
    log(f"  Scored: {scored}")
    log(f"  Gold (High Priority): {len(gold)}")
    log(f"  Errors: {errors}")
    
    # ── Telegram Summary ──
    if scored > 0:
        lines = [f"<b>Content Factory Scorer</b> - {scored} articles scored\n"]
        
        if gold:
            lines.append(f"<b>🥇 Gold Items ({len(gold)}):</b>")
            for g in gold[:5]:
                fmt_str = ", ".join(g["formats"])
                lines.append(
                    f"\n• <b>{g['title'][:60]}</b>"
                    f"\n  Score: {g['score']}/10 | Format: {fmt_str} | Composite: {g['format_score']}"
                    f"\n  Angle: {g['angle'][:100]}"
                )
        else:
            lines.append("\nNo gold items this batch. All Medium/Low priority.")
        
        lines.append(f"\n\n📊 {scored} scored | {len(gold)} gold | {errors} errors")
        
        telegram_msg("\n".join(lines))
    
    # ── Save scoring stats for autoresearch loop (Phase 4) ──
    stats_file = f"{WORKSPACE}/data/content-factory-scoring-stats.json"
    stats = {"last_run": now.isoformat(), "scored": scored, "gold_count": len(gold), "gold_items": gold}
    json.dump(stats, open(stats_file, "w"), indent=2)
    log(f"Stats saved to {stats_file}")

if __name__ == "__main__":
    main()
