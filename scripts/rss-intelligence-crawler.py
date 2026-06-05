#!/usr/bin/env python3
"""
RSS Content Intelligence Crawler.

Fetches curated RSS/Atom feeds, deduplicates articles, saves them to the RSS
Notion database, creates a ranked content brief, optionally seeds the Notion
Content Calendar with the strongest ideas, and sends a compact Telegram summary.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from dateutil import parser as dateparser

# Config
BASE = Path(__file__).resolve().parent
WORKSPACE = BASE.parent
CFG = json.load(open(WORKSPACE / "config" / "rss-intelligence.json"))
NOTION_CFG_PATH = WORKSPACE / "config" / "notion.json"
NOTION_CFG = json.load(open(NOTION_CFG_PATH)) if NOTION_CFG_PATH.exists() else {}
TOKEN = NOTION_CFG.get("token") or CFG["notion_token"]
DB = CFG["database_id"]
CONTENT_CALENDAR_DB = "3268d599-a162-814b-8854-c9b8bde62468"
FEEDS = CFG["feeds"]
STATE_FILE = Path(CFG.get("state_file", WORKSPACE / "data" / "rss-intelligence-state.json"))
DATA_DIR = WORKSPACE / "data"
TELEGRAM_BOT = "<redacted>"
TELEGRAM_CHAT = "866838380"

STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

state = json.load(open(STATE_FILE)) if STATE_FILE.exists() else {"seen_urls": []}
seen = set(state.get("seen_urls", []))
content_idea_urls = set(state.get("content_idea_urls", []))
ctx = ssl.create_default_context()

CATEGORY_TOPIC_MAP = {
    "AI": "AI",
    "Digital Transformation": "Digital Transformation",
    "FinTech": "FinTech",
    "HealthTech": "HealthTech",
    "Healthcare": "Healthcare",
    "Operation Excellence": "Operation Excellence",
    "PMO": "PMO",
    "Strategy": "Strategy",
}

CATEGORY_BASE_SCORE = {
    "AI": 16,
    "Digital Transformation": 17,
    "Healthcare": 18,
    "HealthTech": 16,
    "PMO": 16,
    "Strategy": 15,
    "Operation Excellence": 14,
    "FinTech": 12,
}

EXECUTIVE_KEYWORDS = {
    "board": 10,
    "ceo": 8,
    "chief": 8,
    "strategy": 8,
    "operating model": 9,
    "governance": 9,
    "execution": 10,
    "transformation": 9,
    "portfolio": 7,
    "program": 7,
    "pmo": 9,
    "healthcare": 9,
    "hospital": 8,
    "clinical": 7,
    "patient": 6,
    "ai agent": 10,
    "agentic": 10,
    "automation": 8,
    "workflow": 6,
    "risk": 7,
    "compliance": 7,
    "cost": 6,
    "productivity": 6,
    "roi": 6,
    "resilience": 6,
    "sovereignty": 6,
}

WEAK_SIGNALS = {
    "conference": -8,
    "webinar": -8,
    "podcast": -5,
    "sponsored": -12,
    "roundup": -6,
    "funding": -4,
    "launches": -4,
    "announces": -3,
}

ANGLE_PATTERNS = [
    (re.compile(r"\b(ai|agentic|automation|llm|genai)\b", re.I), "AI execution gap"),
    (re.compile(r"\b(healthcare|hospital|clinical|patient)\b", re.I), "healthcare operating model"),
    (re.compile(r"\b(pmo|portfolio|program|project)\b", re.I), "PMO governance"),
    (re.compile(r"\b(strategy|board|ceo|leadership)\b", re.I), "executive decision quality"),
    (re.compile(r"\b(risk|compliance|regulat|resilien|security)\b", re.I), "risk and governance"),
    (re.compile(r"\b(fintech|payments|banking|stablecoin)\b", re.I), "fintech transformation"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RSS content intelligence.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and score only. Do not write Notion, state, or Telegram.")
    parser.add_argument("--no-calendar", action="store_true", help="Do not create Content Calendar idea entries.")
    parser.add_argument("--no-telegram", action="store_true", help="Do not send Telegram summary after a live run.")
    parser.add_argument("--max-calendar-ideas", type=int, default=3, help="Max top ideas to create in Content Calendar.")
    parser.add_argument("--brief-top", type=int, default=8, help="Number of ranked items to keep in the content brief.")
    parser.add_argument("--rescore-recent", type=int, default=0, help="Also score this many recent RSS Notion entries for backfill.")
    return parser.parse_args()


# HTTP
def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 RSS-Intelligence/2.1"})
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        return r.read()


# XML helpers
def clean_xml(raw_bytes: bytes) -> ET.Element:
    text = raw_bytes.decode("utf-8", errors="replace")
    if "<atom:" in text and "xmlns:atom" not in text:
        text = text.replace(
            'xmlns="http://www.w3.org/2005/Atom"',
            'xmlns="http://www.w3.org/2005/Atom" xmlns:atom="http://www.w3.org/2005/Atom"',
        )
    try:
        return ET.fromstring(text.encode())
    except ET.ParseError:
        cleaned = re.sub(r'xmlns:[a-zA-Z0-9]+="[^"]+"', "", text)
        return ET.fromstring(cleaned.encode())


def tag_without_namespace(tag: str) -> str:
    return tag.lower().split("}")[-1]


def find_all(element: ET.Element, tag_name: str) -> list[ET.Element]:
    tag_lower = tag_name.lower()
    return [el for el in element.iter() if tag_lower == tag_without_namespace(el.tag)]


def find_first(element: ET.Element, tag_name: str) -> ET.Element | None:
    results = find_all(element, tag_name)
    return results[0] if results else None


def text_of(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return re.sub(r"\s+", " ", element.text).strip()


def extract_description(item: ET.Element) -> str:
    fields = ["description", "summary", "content", "encoded"]
    for field in fields:
        for el in find_all(item, field):
            raw = text_of(el)
            if not raw:
                continue
            desc = re.sub(r"<[^>]+>", "", raw)
            desc = html.unescape(re.sub(r"\s+", " ", desc)).strip()
            if desc:
                return desc[:900]
    return ""


def extract_pub_date(item: ET.Element) -> str:
    for field in ["pubdate", "published", "updated", "date"]:
        for el in find_all(item, field):
            if el.text:
                try:
                    return dateparser.parse(el.text).strftime("%Y-%m-%d")
                except Exception:
                    pass
    return ""


def extract_link(item: ET.Element) -> str:
    for link_el in find_all(item, "link"):
        href = link_el.get("href", "")
        if href.startswith("http"):
            return href
        if link_el.text and link_el.text.strip().startswith("http"):
            return link_el.text.strip()
    guid = find_first(item, "guid")
    guid_text = text_of(guid)
    return guid_text if guid_text.startswith("http") else ""


# Feed parser
def parse_feed(url: str, category: str) -> tuple[list[dict], str]:
    raw = fetch(url)
    root = clean_xml(raw)
    source_name = urlparse(url).netloc
    atom_ns = "http://www.w3.org/2005/Atom"
    items = root.findall(".//item") or root.findall(f".//{{{atom_ns}}}entry")
    results = []
    for item in items:
        title = html.unescape(text_of(find_first(item, "title")))
        link = extract_link(item)
        if not title or not link or link in seen:
            continue
        description = extract_description(item)
        pub_date = extract_pub_date(item)
        results.append({
            "title": title,
            "link": link,
            "description": description,
            "published": pub_date,
            "category": category,
            "source": source_name,
            "item": item,
        })
    return results, source_name


# Notion
def notion_req(path: str, method: str = "GET", body: dict | None = None) -> dict:
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read())


def add_rss_article(article: dict) -> tuple[bool, str]:
    body = {
        "parent": {"database_id": DB},
        "properties": {
            "Name": {"title": [{"text": {"content": article["title"][:200]}}]},
            "Category": {"multi_select": [{"name": article["category"]}]},
            "Source": {"rich_text": [{"text": {"content": article["source"]}}]},
            "URL": {"url": article["link"]},
            "Status": {"select": {"name": "New"}},
        },
    }
    if article.get("published"):
        body["properties"]["Published"] = {"date": {"start": article["published"]}}
    if article.get("description"):
        body["properties"]["Summary"] = {"rich_text": [{"text": {"content": article["description"][:500]}}]}
    try:
        notion_req("/pages", method="POST", body=body)
        return True, article["title"][:60]
    except Exception as e:
        return False, str(e)[:140]


def rich_text_plain(prop: dict) -> str:
    return "".join(part.get("plain_text", "") for part in prop.get("rich_text", []))


def title_plain(prop: dict) -> str:
    return "".join(part.get("plain_text", "") for part in prop.get("title", []))


def parse_rss_page(page: dict) -> dict | None:
    props = page.get("properties", {})
    title = title_plain(props.get("Name", {}))
    url = props.get("URL", {}).get("url") or ""
    if not title or not url:
        return None
    categories = [item.get("name", "") for item in props.get("Category", {}).get("multi_select", [])]
    category = categories[0] if categories else "General"
    return {
        "title": title,
        "link": url,
        "description": rich_text_plain(props.get("Summary", {})),
        "published": (props.get("Published", {}).get("date") or {}).get("start", ""),
        "category": category,
        "source": rich_text_plain(props.get("Source", {})) or urlparse(url).netloc,
        "item": None,
    }


def query_recent_rss_articles(limit: int) -> list[dict]:
    if limit <= 0:
        return []
    body = {
        "sorts": [{"timestamp": "created_time", "direction": "descending"}],
        "page_size": min(max(limit, 1), 100),
    }
    pages = notion_req(f"/databases/{DB}/query", method="POST", body=body).get("results", [])
    articles = []
    for page in pages:
        parsed = parse_rss_page(page)
        if parsed:
            articles.append(parsed)
    return articles


def add_content_calendar_idea(candidate: dict) -> tuple[bool, str]:
    if candidate["link"] in content_idea_urls:
        return False, "duplicate"
    title = f"RSS angle: {candidate['angle']}"
    draft = (
        f"Source: {candidate['title']}\n"
        f"URL: {candidate['link']}\n\n"
        f"Why it matters: {candidate['why']}\n\n"
        f"Suggested take: {candidate['take']}\n\n"
        f"Possible post spine:\n"
        f"1. The signal: {candidate['signal']}\n"
        f"2. The executive risk: {candidate['risk']}\n"
        f"3. The operating rule: {candidate['rule']}\n"
        f"4. CTA: {candidate['cta']}"
    )
    body = {
        "parent": {"database_id": CONTENT_CALENDAR_DB},
        "properties": {
            "Title": {"title": [{"text": {"content": title[:200]}}]},
            "Status": {"select": {"name": "Idea"}},
            "Topic": {"select": {"name": CATEGORY_TOPIC_MAP.get(candidate["category"], "General")}},
            "Owner": {"select": {"name": "CMO"}},
            "Hook": {"rich_text": [{"text": {"content": candidate["hook"][:1900]}}]},
            "Draft": {"rich_text": [{"text": {"content": draft[:1900]}}]},
            "Image Intent": {"rich_text": [{"text": {"content": candidate["image_intent"][:1900]}}]},
        },
    }
    try:
        page = notion_req("/pages", method="POST", body=body)
        content_idea_urls.add(candidate["link"])
        return True, page.get("id", "created")
    except Exception as e:
        return False, str(e)[:140]


# Content intelligence
def score_article(article: dict) -> tuple[int, list[str]]:
    text = f"{article['title']} {article.get('description', '')}".lower()
    score = CATEGORY_BASE_SCORE.get(article["category"], 10)
    reasons = [f"{article['category']} source"]
    for key, points in EXECUTIVE_KEYWORDS.items():
        if key in text:
            score += points
            reasons.append(key)
    for key, points in WEAK_SIGNALS.items():
        if key in text:
            score += points
            reasons.append(f"weak: {key}")
    if re.search(r"\b(\d+%|\$\d+|\d+x|\d+\s*(million|billion|m|bn))\b", text):
        score += 6
        reasons.append("specific data")
    if len(article.get("description", "")) > 120:
        score += 4
        reasons.append("context available")
    return max(score, 0), reasons[:8]


def detect_angle(article: dict) -> str:
    text = f"{article['title']} {article.get('description', '')}"
    for pattern, angle in ANGLE_PATTERNS:
        if pattern.search(text):
            return angle
    return CATEGORY_TOPIC_MAP.get(article["category"], "executive operating insight")


def build_candidate(article: dict) -> dict:
    score, reasons = score_article(article)
    angle = detect_angle(article)
    title = article["title"].strip()
    desc = article.get("description", "").strip()
    signal = desc[:180] if desc else title
    if len(signal) == 180:
        signal = signal.rsplit(" ", 1)[0] + "..."

    if angle == "AI execution gap":
        take = "AI value is being won in workflow redesign and governance, not tool adoption."
        risk = "leaders treat AI as a technology rollout instead of an operating-model change"
        rule = "start with the decision, control point, and accountability path before buying the tool"
        hook = "AI does not fail because the model is weak. It fails because the operating model around it is vague."
        cta = "Where is your AI program still a demo instead of an operating rhythm?"
        image_intent = "Dark executive AI execution card showing workflow nodes, governance checkpoints, and boardroom decision path."
    elif angle == "healthcare operating model":
        take = "Healthcare transformation only works when clinical workflow, governance, and technology move together."
        risk = "digital projects create data and alerts that clinicians cannot absorb"
        rule = "design around the clinical decision and the handoff, then automate around that path"
        hook = "Healthcare does not need more digital noise. It needs cleaner operating decisions at the point of care."
        cta = "Which healthcare workflow would you redesign before adding another platform?"
        image_intent = "Premium healthcare operations card with hospital command center, patient-flow signals, and executive governance overlay."
    elif angle == "PMO governance":
        take = "The modern PMO is shifting from reporting office to execution control tower."
        risk = "portfolios look green while dependencies, benefits, and decisions are stuck"
        rule = "measure decision latency and dependency burn-down, not only milestone status"
        hook = "A PMO that only reports status is already late. The real value is controlling execution risk before it becomes visible."
        cta = "What is the one PMO metric your leadership team should stop ignoring?"
        image_intent = "Executive PMO control-tower card with portfolio signals, risk map, and gold/blue governance accents."
    elif angle == "risk and governance":
        take = "Execution speed now depends on governance that is embedded, not bolted on."
        risk = "teams move fast locally while enterprise risk accumulates silently"
        rule = "put control evidence inside the workflow, not in a separate reporting ritual"
        hook = "Governance fails when it arrives after the work is already done."
        cta = "Where should governance be embedded directly into the workflow?"
        image_intent = "Dark governance card with control checkpoints, audit trail lines, and executive risk dashboard atmosphere."
    elif angle == "executive decision quality":
        take = "Executive leverage comes from better decision systems, not more information."
        risk = "leaders mistake more dashboards for better judgment"
        rule = "separate signal, implication, decision, and owner in every executive review"
        hook = "The bottleneck in transformation is rarely information. It is decision quality."
        cta = "What decision in your organization needs a clearer operating rhythm?"
        image_intent = "Boardroom decision-system card with signal-to-decision flow, crisp typography, and strategic control metaphor."
    else:
        take = "Market signals matter only when converted into operating choices."
        risk = "teams collect trends without changing priorities, governance, or execution habits"
        rule = "turn every trend into a decision, a risk, or a content-backed point of view"
        hook = "Trends are cheap. The advantage is turning the signal into an operating decision."
        cta = "Which trend deserves a real management decision this quarter?"
        image_intent = "Executive signal-to-action card with market signal stream, decision node, and Ahmed-branded footer."

    why = f"Useful for Ahmed's content because it connects {article['category']} signal to {angle}."
    return {
        "title": title,
        "link": article["link"],
        "category": article["category"],
        "source": article["source"],
        "published": article.get("published", ""),
        "description": desc,
        "score": score,
        "reasons": reasons,
        "angle": angle,
        "signal": signal,
        "why": why,
        "take": take,
        "risk": risk,
        "rule": rule,
        "hook": hook,
        "cta": cta,
        "image_intent": image_intent,
    }


def select_diverse_candidates(candidates: list[dict], limit: int) -> list[dict]:
    selected = []
    category_counts: dict[str, int] = {}
    angle_counts: dict[str, int] = {}
    for candidate in candidates:
        if len(selected) >= limit:
            break
        if category_counts.get(candidate["category"], 0) >= 3:
            continue
        if angle_counts.get(candidate["angle"], 0) >= 2:
            continue
        selected.append(candidate)
        category_counts[candidate["category"]] = category_counts.get(candidate["category"], 0) + 1
        angle_counts[candidate["angle"]] = angle_counts.get(candidate["angle"], 0) + 1
    for candidate in candidates:
        if len(selected) >= limit:
            break
        if candidate not in selected:
            selected.append(candidate)
    return selected


def build_content_brief(candidates: list[dict], errors: list[str], created: list[dict], articles_considered: int) -> str:
    now = datetime.now().astimezone()
    lines = [
        f"# RSS Content Intelligence - {now.strftime('%Y-%m-%d')}",
        "",
        f"Articles considered: {articles_considered}",
        f"Ranked candidates shown: {len(candidates)}",
        f"Content Calendar ideas created: {len(created)}",
    ]
    if errors:
        lines.append(f"Feed/write errors: {len(errors)}")
    lines.extend(["", "## Top Content Angles", ""])
    for i, c in enumerate(candidates, 1):
        lines.extend([
            f"### {i}. {c['angle']} - {c['score']}",
            f"Source: {c['title']}",
            f"Category: {c['category']} | {c['source']}",
            f"URL: {c['link']}",
            "",
            f"Why it matters: {c['why']}",
            f"Suggested hook: {c['hook']}",
            f"Take: {c['take']}",
            f"Risk: {c['risk']}",
            f"Rule: {c['rule']}",
            f"CTA: {c['cta']}",
            "",
        ])
    if errors:
        lines.extend(["## Errors", ""])
        lines.extend(f"- {e}" for e in errors)
    return "\n".join(lines).strip() + "\n"


# Telegram
def telegram_msg(text: str) -> dict:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT}/sendMessage"
    data = json.dumps({"chat_id": TELEGRAM_CHAT, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        return json.loads(r.read())


def build_telegram_summary(new_count: int, candidates: list[dict], created: list[dict], errors: list[str]) -> str:
    lines = [f"<b>RSS Content Intel</b> - {new_count} new article{'s' if new_count != 1 else ''}"]
    if created:
        lines.append(f"Created {len(created)} Content Calendar idea{'s' if len(created) != 1 else ''} for review.")
    lines.append("")
    lines.append("<b>Top content picks</b>")
    if not candidates:
        lines.append("No strong content candidates this run.")
    for i, c in enumerate(candidates[:3], 1):
        lines.append(f"{i}. <b>{html.escape(c['angle'])}</b> ({c['score']})")
        lines.append(f"   {html.escape(c['title'][:90])}")
        lines.append(f"   Hook: {html.escape(c['hook'][:150])}")
    if errors:
        lines.append("")
        lines.append(f"Errors: {len(errors)}. See content brief for details.")
    lines.append("")
    lines.append("Decision: use the top ideas for LinkedIn drafts, not as raw links.")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] RSS Content Intelligence Crawler", flush=True)
    print(f"Feeds: {len(FEEDS)} | Seen URLs: {len(seen)} | Dry run: {args.dry_run}", flush=True)

    new_count = 0
    new_articles: list[dict] = []
    errors: list[str] = []

    for category, url in FEEDS.items():
        try:
            articles, source_name = parse_feed(url, category)
            print(f"  {category}: {len(articles)} new", flush=True)
            for article in articles:
                if args.dry_run:
                    ok, result = True, article["title"][:60]
                else:
                    ok, result = add_rss_article(article)
                if ok:
                    if not args.dry_run:
                        seen.add(article["link"])
                    new_count += 1
                    new_articles.append(article)
                    print(f"    + {article['title'][:65]}", flush=True)
                else:
                    errors.append(f"{category}/{article['title'][:40]}: {result}")
        except Exception as e:
            print(f"  FAIL {category}: {e}", flush=True)
            errors.append(f"{category}: {e}")

    scoring_articles = list(new_articles)
    if args.rescore_recent:
        try:
            recent_articles = query_recent_rss_articles(args.rescore_recent)
            known_links = {article["link"] for article in scoring_articles}
            added_recent = 0
            for article in recent_articles:
                if article["link"] in known_links:
                    continue
                scoring_articles.append(article)
                known_links.add(article["link"])
                added_recent += 1
            print(f"  Recent backfill: {added_recent} added for scoring", flush=True)
        except Exception as e:
            errors.append(f"recent backfill: {e}")

    candidates = [build_candidate(article) for article in scoring_articles]
    candidates.sort(key=lambda c: c["score"], reverse=True)
    top_candidates = select_diverse_candidates(candidates, max(args.brief_top, 1))

    created: list[dict] = []
    if not args.dry_run and not args.no_calendar:
        calendar_candidates = []
        used_angles = set()
        for candidate in top_candidates + candidates:
            if len(calendar_candidates) >= max(args.max_calendar_ideas, 0):
                break
            if candidate["score"] < 28:
                continue
            if candidate["angle"] in used_angles:
                continue
            calendar_candidates.append(candidate)
            used_angles.add(candidate["angle"])
        for candidate in candidates:
            if len(calendar_candidates) >= max(args.max_calendar_ideas, 0):
                break
            if candidate["score"] >= 35 and candidate not in calendar_candidates:
                calendar_candidates.append(candidate)
        for candidate in calendar_candidates:
            ok, result = add_content_calendar_idea(candidate)
            if ok:
                created.append({"title": candidate["title"], "page_id": result, "score": candidate["score"]})
                print(f"  Content idea: {candidate['angle']} ({candidate['score']})", flush=True)
            elif result != "duplicate":
                errors.append(f"content calendar/{candidate['title'][:40]}: {result}")

    brief = build_content_brief(top_candidates, errors, created, len(scoring_articles))
    latest_brief = DATA_DIR / "rss-content-brief-latest.md"
    dated_brief = DATA_DIR / f"rss-content-brief-{datetime.now().strftime('%Y-%m-%d')}.md"
    latest_json = DATA_DIR / "rss-content-candidates-latest.json"

    if not args.dry_run:
        latest_brief.write_text(brief)
        dated_brief.write_text(brief)
        latest_json.write_text(json.dumps({
            "generated_at": datetime.now().astimezone().isoformat(),
            "new_articles": new_count,
            "scored_articles": len(scoring_articles),
            "created_content_ideas": created,
            "candidates": top_candidates,
            "errors": errors,
        }, indent=2, ensure_ascii=False))
        state["seen_urls"] = list(seen)[-50000:]
        state["content_idea_urls"] = list(content_idea_urls)[-50000:]
        state["last_run"] = datetime.now().astimezone().isoformat()
        state["last_content_brief"] = str(latest_brief)
        state["last_new_count"] = new_count
        state["last_content_ideas_created"] = len(created)
        state["last_errors"] = errors[-20:]
        json.dump(state, open(STATE_FILE, "w"), indent=2)
    else:
        print("\n--- Content brief preview ---")
        print(brief[:5000])

    if new_count > 0 and not args.dry_run and not args.no_telegram:
        try:
            telegram_msg(build_telegram_summary(new_count, top_candidates, created, errors))
            print(f"\nTelegram: sent ({new_count} articles, {len(created)} ideas)", flush=True)
        except Exception as e:
            print(f"\nTelegram FAIL: {e}", flush=True)
    elif new_count > 0 and args.no_telegram:
        print(f"\nTelegram: skipped by --no-telegram ({new_count} articles, {len(created)} ideas)", flush=True)
    elif new_count == 0:
        print("\nNo new articles.", flush=True)

    print(f"\nDone. {new_count} new added. {len(seen)} total in state. Top content candidates: {len(top_candidates)}.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
