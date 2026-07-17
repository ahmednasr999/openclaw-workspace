#!/usr/bin/env python3
"""Global Fintech Executive Radar.

Builds an evidence-labelled internal brief from live news search. Discovery is
allowed from reporting sources, but a story is never labelled verified unless
the result itself is a regulator/company/investor source or a separate primary
source is found.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import ssl
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "fintech-radar.json"
OUT_DIR = ROOT / "intel" / "fintech-radar"
STATE_PATH = ROOT / "data" / "fintech-radar-state.json"
SEARXNG = "http://127.0.0.1:8090/search"
CAIRO = dt.timezone(dt.timedelta(hours=3))
CTX = ssl.create_default_context()

FINTECH_TERMS = re.compile(
    r"\b(fintech|payments?|banking|bank|neobank|digital bank|wallet|lending|credit|"
    r"insurtech|wealthtech|regtech|open banking|embedded finance|financial infrastructure|"
    r"fraud|digital identity|stablecoin|tokeni[sz]ation|remittance|money movement|card issuing|"
    r"merchant acquiring|buy now pay later|bnpl)\b",
    re.I,
)

CATEGORY_TERMS = {
    "Capital": re.compile(r"\b(rais(?:e|es|ed|ing)|funding|investment|series [a-f]|seed|venture debt|debt facility|acqui(?:re|res|red|sition)|merger|ipo|capital|valuation)\b", re.I),
    "Regulation": re.compile(r"\b(regulat|license|licence|enforcement|central bank|authority|law|rule|compliance|policy)\b", re.I),
    "Payments": re.compile(r"\b(payment|wallet|merchant|acquiring|card|remittance|money movement|checkout|bnpl)\b", re.I),
    "Digital Banking": re.compile(r"\b(digital bank|neobank|banking|bank|open banking)\b", re.I),
    "Infrastructure": re.compile(r"\b(infrastructure|fraud|identity|stablecoin|tokeni[sz]ation|api|core banking|regtech)\b", re.I),
    "Leadership": re.compile(r"\b(appoint|ceo|chief executive|leadership|layoffs?|hiring|joins|steps down)\b", re.I),
}


@dataclass
class Story:
    title: str
    url: str
    snippet: str
    source: str
    category: str
    published: str = ""
    amount: str = ""
    stage: str = ""
    companies: str = ""
    geography: str = "Global"
    gcc_relevance: str = "Low"
    evidence_grade: str = "DISCOVERY"
    primary_url: str = ""
    score: int = 0
    action: str = "Monitor"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def clean(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def domain_matches(host: str, domains: list[str]) -> bool:
    return any(host == item or host.endswith("." + item) for item in domains)


def searx(query: str, limit: int = 10, category: str = "news") -> list[dict]:
    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "language": "en",
        "safesearch": "0",
        "categories": category,
        "time_range": "week",
    })
    req = urllib.request.Request(f"{SEARXNG}?{params}", headers={"User-Agent": "FintechRadar/0.1"})
    with urllib.request.urlopen(req, timeout=20) as response:
        payload = json.loads(response.read())
    return payload.get("results", [])[:limit]


def google_news(query: str, limit: int = 30) -> list[dict]:
    params = urllib.parse.urlencode({
        "q": f"{query} when:3d",
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    })
    req = urllib.request.Request(
        f"https://news.google.com/rss/search?{params}",
        headers={"User-Agent": "FintechRadar/0.1"},
    )
    with urllib.request.urlopen(req, context=CTX, timeout=25) as response:
        root = ET.fromstring(response.read())
    results = []
    for item in root.findall(".//item")[:limit]:
        source = item.find("source")
        source_name = clean(source.text if source is not None else "")
        source_url = source.get("url", "") if source is not None else ""
        raw_title = clean(item.findtext("title") or "")
        suffix = f" - {source_name}" if source_name else ""
        title = raw_title[:-len(suffix)].strip() if suffix and raw_title.endswith(suffix) else raw_title
        results.append({
            "title": title,
            "url": clean(item.findtext("link") or ""),
            "content": clean(item.findtext("description") or ""),
            "publishedDate": clean(item.findtext("pubDate") or ""),
            "source": source_name,
            "source_url": source_url,
        })
    return results


def normalized_title(title: str) -> str:
    text = re.sub(r"\b(update|exclusive|breaking|new)\b", "", title.lower())
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def story_key(title: str, url: str) -> str:
    title_key = " ".join(normalized_title(title).split()[:12])
    return hashlib.sha256(f"{title_key}|{domain(url)}".encode()).hexdigest()[:20]


def extract_amount(text: str) -> str:
    patterns = [
        r"(?:US\$|USD\s*|\$)\s?\d+(?:\.\d+)?\s?(?:billion|million|bn|m|b)\b",
        r"(?:€|EUR\s*)\d+(?:\.\d+)?\s?(?:billion|million|bn|m|b)\b",
        r"(?:£|GBP\s*)\d+(?:\.\d+)?\s?(?:billion|million|bn|m|b)\b",
        r"(?:AED|SAR|QAR|KWD|BHD|OMR)\s*\d+(?:\.\d+)?\s?(?:billion|million|bn|m|b)?\b",
    ]
    matches = []
    for pattern in patterns:
        matches.extend(re.finditer(pattern, text, re.I))
    if matches:
        staged = []
        for match in matches:
            tail = text[match.end():match.end() + 45]
            stage_match = re.search(r"\b(series\s+[a-f]|seed|round|funding|financing|debt facility)\b", tail, re.I)
            if stage_match:
                staged.append((stage_match.start(), match))
        if staged:
            staged.sort(key=lambda item: item[0])
            return clean(staged[0][1].group(0))
        for match in matches:
            window = text[max(0, match.start() - 35):match.end() + 20]
            if re.search(r"\b(rais|secur|clos|funding|financing)\w*\b", window, re.I):
                return clean(match.group(0))
        return clean(matches[0].group(0))
    return ""


def extract_stage(text: str) -> str:
    match = re.search(
        r"\b(pre[- ]seed|seed|series\s+[a-f]|growth round|venture debt|debt facility|private equity|ipo|acquisition|merger)\b",
        text,
        re.I,
    )
    return clean(match.group(0)).title() if match else ""


def infer_company(title: str) -> str:
    title = clean(title)
    patterns = [
        r"^(.+?)\s+(?:raises|raised|secures|secured|lands|closes|acquires|acquired|launches|partners|appoints|targets|hits|banks|pledges)\b",
        r"^(.+?)\s+(?:wins|gets)\s+",
    ]
    for pattern in patterns:
        match = re.search(pattern, title, re.I)
        if match:
            company = clean(match.group(1))
            company = re.sub(
                r"^(?:paris-based|london-based|uk|us|u\.s\.|sydney|australian|african|european|global)\s+",
                "",
                company,
                flags=re.I,
            )
            company = re.sub(r"^(?:mortgage\s+)?fintech\s+", "", company, flags=re.I)
            return company[:80]
    return title.split(":", 1)[0][:80]


def classify_geography(text: str, gcc_terms: list[str]) -> tuple[str, str]:
    lower = text.lower()
    matched = [term for term in gcc_terms if re.search(rf"\b{re.escape(term)}\b", lower)]
    if matched:
        return matched[0].title(), "High"
    regions = [
        ("United States", ["united states", "u.s.", " usa ", "new york", "san francisco"]),
        ("United Kingdom", ["united kingdom", " u.k.", "london"]),
        ("Europe", ["europe", "european union", "eu "]),
        ("Africa", ["africa", "nigeria", "kenya", "south africa", "egypt"]),
        ("Asia", ["singapore", "india", "china", "hong kong", "indonesia", "japan"]),
        ("Latin America", ["latin america", "brazil", "mexico", "colombia"]),
    ]
    for label, terms in regions:
        if any(term in lower for term in terms):
            relevance = "Medium" if label in {"Africa", "Asia", "Europe"} else "Low"
            return label, relevance
    return "Global", "Low"


def is_probable_company_primary(host: str, company: str, cfg: dict) -> bool:
    if domain_matches(host, cfg["primary_domains"]):
        return True
    if domain_matches(host, cfg["trusted_reporting_domains"]):
        return False
    stop = {"fintech", "global", "markets", "funding", "round", "week", "million", "billion", "company", "digital", "banking"}
    company_tokens = [t for t in re.findall(r"[a-z0-9]+", company.lower()) if len(t) >= 4 and t not in stop]
    host_flat = host.replace("-", "").replace(".", "")
    return bool(company_tokens and any(token in host_flat for token in company_tokens[:2]))


def is_relevant(title: str, snippet: str, category: str) -> bool:
    text = f"{title} {snippet}"
    return bool(FINTECH_TERMS.search(text) and CATEGORY_TERMS[category].search(text))


def resolve_direct_result(story: Story) -> None:
    """Replace a Google News wrapper with a matching direct search result."""
    try:
        results = searx(f'"{story.title}"', limit=6, category="general")
    except Exception:
        return
    source_host = story.source
    title_words = set(normalized_title(story.title).split())
    best = None
    best_score = 0.0
    for result in results:
        candidate_url = result.get("url") or ""
        candidate_title = clean(result.get("title") or "")
        if not candidate_url or not candidate_title:
            continue
        candidate_words = set(normalized_title(candidate_title).split())
        overlap = len(title_words & candidate_words) / max(1, len(title_words | candidate_words))
        if source_host and domain(candidate_url) == source_host:
            overlap += 0.35
        if overlap > best_score:
            best_score = overlap
            best = result
    if best and best_score >= 0.55:
        story.url = best.get("url") or story.url
        direct_snippet = clean(best.get("content") or best.get("snippet") or "")
        if direct_snippet:
            story.snippet = direct_snippet[:420]


def find_primary(story: Story, cfg: dict) -> str:
    company = story.companies
    query = f'"{company}" {story.stage or story.category} press release'
    try:
        results = searx(query, limit=6, category="general")
    except Exception:
        return ""
    for result in results:
        url = result.get("url") or ""
        host = domain(url)
        if not url or domain_matches(host, cfg["blocked_domains"]):
            continue
        if is_probable_company_primary(host, company, cfg):
            return url
    return ""


def score_story(story: Story) -> int:
    text = f"{story.title} {story.snippet}".lower()
    score = 20
    if story.category == "Capital": score += 18
    if story.amount: score += 12
    if story.stage: score += 8
    if story.evidence_grade == "PRIMARY": score += 20
    elif story.evidence_grade == "CORROBORATED": score += 14
    elif story.evidence_grade == "TRUSTED_REPORTING": score += 8
    if story.gcc_relevance == "High": score += 12
    if re.search(r"\b(regulat|license|central bank|enforcement|acquisition|merger|ipo)\b", text): score += 10
    if re.search(r"\b(partnership|launch|appoints|expands)\b", text): score += 4
    if re.search(r"\b(opinion|podcast|webinar|sponsored)\b", text): score -= 16
    return max(0, min(score, 100))


def build_story(result: dict, category: str, cfg: dict) -> Story | None:
    title = clean(result.get("title") or "")
    url = result.get("url") or ""
    snippet = clean(result.get("content") or result.get("snippet") or "")
    if not title or not url:
        return None
    source_url = result.get("source_url") or ""
    host = domain(source_url) or domain(url)
    if domain_matches(host, cfg["blocked_domains"]):
        return None
    if not is_relevant(title, snippet, category):
        return None
    text = f"{title} {snippet}"
    company = infer_company(title)
    geography, gcc = classify_geography(text, cfg["gcc_terms"])
    story = Story(
        title=title,
        url=url,
        snippet=snippet[:420],
        source=host,
        category=category,
        published=clean(result.get("publishedDate") or result.get("published_date") or ""),
        amount=extract_amount(text),
        stage=extract_stage(text),
        companies=company,
        geography=geography,
        gcc_relevance=gcc,
    )
    if is_probable_company_primary(host, company, cfg):
        story.evidence_grade = "PRIMARY"
        story.primary_url = url
    elif domain_matches(host, cfg["trusted_reporting_domains"]):
        story.evidence_grade = "TRUSTED_REPORTING"
    story.action = "Review now" if category in {"Capital", "Regulation"} else "Monitor"
    return story


def enrich_primary(stories: list[Story], cfg: dict, limit: int = 12) -> None:
    for story in stories[:limit]:
        if story.evidence_grade == "PRIMARY":
            continue
        primary = find_primary(story, cfg)
        if primary:
            story.primary_url = primary
            story.evidence_grade = "CORROBORATED"


def dedupe(stories: list[Story]) -> list[Story]:
    kept: dict[str, Story] = {}
    for story in stories:
        if story.category == "Capital" and story.amount:
            company_key = " ".join(normalized_title(story.companies).split()[:4])
            key = f"capital|{company_key}|{story.amount.lower()}|{story.stage.lower()}"
        else:
            key = normalized_title(story.title)
            key = " ".join(key.split()[:10])
        current = kept.get(key)
        if current is None or story.score > current.score:
            kept[key] = story
    return list(kept.values())


def select_diverse(stories: list[Story], maximum: int) -> list[Story]:
    quotas = {
        "Capital": 8,
        "Regulation": 3,
        "Payments": 2,
        "Digital Banking": 2,
        "Infrastructure": 2,
        "Leadership": 1,
    }
    selected: list[Story] = []
    used: set[int] = set()
    for category, quota in quotas.items():
        for story in [s for s in stories if s.category == category][:quota]:
            selected.append(story)
            used.add(id(story))
    for story in stories:
        if len(selected) >= maximum:
            break
        if id(story) not in used:
            selected.append(story)
    selected.sort(key=lambda s: (-s.score, s.title.lower()))
    return selected[:maximum]


def select_content_candidate(stories: list[Story]) -> Story | None:
    capital = [story for story in stories if story.category == "Capital"]
    if not capital:
        return None
    return max(
        capital,
        key=lambda story: (
            "debt facility" in f"{story.title} {story.snippet}".lower(),
            story.evidence_grade in {"PRIMARY", "CORROBORATED", "TRUSTED_REPORTING"},
            story.score,
        ),
    )


def content_package(story: Story | None, generated: dt.datetime, cfg: dict) -> dict:
    content_cfg = cfg.get("content_output", {})
    date_key = generated.strftime("%Y-%m-%d")
    filename = f"fintech-radar-linkedin-{date_key}.png"
    output_path = ROOT / content_cfg.get("visual_output_dir", "output/fintech-radar") / filename
    media_path = Path(content_cfg.get("telegram_media_dir", "/root/.openclaw/media/fintech-radar")) / filename
    manifest_path = output_path.with_suffix(".manifest.json")
    ready = output_path.is_file() and media_path.is_file() and manifest_path.is_file()
    if not story:
        return {"status": "BLOCKED_NO_CANDIDATE", "image_ready": False}

    financing_text = f"{story.title} {story.snippet}".lower()
    if "debt facility" in financing_text and story.amount:
        post_text = (
            "A fintech funding headline can be technically accurate and still create the wrong impression.\n\n"
            "Aria announced €7 million in equity alongside a €240 million debt facility. "
            "That is not a €247 million equity round.\n\n"
            "Equity funds the company and changes ownership. A debt facility provides lending capacity, "
            "with repayment obligations, conditions and deployment limits.\n\n"
            "Before judging a funding announcement, executives should ask:\n"
            "1. How much is equity?\n2. How much is debt?\n3. Who supplied each component?\n"
            "4. What can the capital fund?\n5. What obligations come with it?\n\n"
            "The headline gets attention. The capital structure tells the real story.\n\n"
            "Do you examine the composition of a funding round before judging its significance?"
        )
        visual_topic = "€247M RAISED?"
        visual_prompt = (
            "Use case: infographic-diagram\nAsset type: LinkedIn portrait post, 1080x1350 PNG\n"
            "Primary request: Premium hand-drawn executive sketchnote explaining that €7M equity plus a €240M debt facility are different forms of capital.\n"
            "Scene/backdrop: warm off-white textured paper.\nStyle/medium: black ink hand-drawn sketchnote with restrained orange accents, practical and executive.\n"
            "Composition: large headline at top, two clearly separated hand-drawn containers in the center, compact five-question checklist below, signature footer.\n"
            "Text (verbatim): \"€247M RAISED?\"; \"€7M EQUITY\"; \"Ownership + growth\"; \"€240M DEBT FACILITY\"; "
            "\"Lending capacity + repayment\"; \"SAME HEADLINE. VERY DIFFERENT CAPITAL.\"; \"Ahmed Nasr\".\n"
            "Constraints: highly legible mobile typography, no logos, no portraits, no photorealism, no dark tech-card style, no invented financial claims."
        )
    else:
        post_text = (
            f"{story.title}\n\nThe announcement matters less as a headline than as a signal. "
            "Executives should examine the capital type, strategic use, investor conviction and operating implications before drawing conclusions.\n\n"
            "What signal do you take from this development?"
        )
        visual_topic = story.title
        visual_prompt = (
            "Use case: infographic-diagram\nAsset type: LinkedIn portrait post, 1080x1350 PNG\n"
            f"Primary request: Premium hand-drawn executive sketchnote about: {story.title}.\n"
            "Scene/backdrop: warm off-white textured paper.\nStyle/medium: black ink with restrained orange accents.\n"
            "Constraints: legible, evidence-led, no logos, no portrait, no photorealism, no invented claims."
        )
    return {
        "status": "READY" if ready else "BLOCKED_IMAGE_MISSING",
        "topic": visual_topic,
        "source_story": story.title,
        "evidence_status": story.evidence_grade,
        "post_text": post_text,
        "visual_prompt": visual_prompt,
        "image_ready": ready,
        "output_path": str(output_path),
        "telegram_media_path": str(media_path),
        "manifest_path": str(manifest_path),
        "style_reference": str(ROOT / content_cfg.get("style_reference", "media/inbound/234fe40d-96c3-4b4a-bf6f-dc1f75f91bbf.jpg")),
    }


def render(stories: list[Story], cfg: dict, generated: dt.datetime) -> str:
    capital = [s for s in stories if s.category == "Capital"]
    verified = [s for s in stories if s.evidence_grade in {"PRIMARY", "CORROBORATED"}]
    gcc = [s for s in stories if s.gcc_relevance == "High"]
    content_candidate = select_content_candidate(stories)
    package = content_package(content_candidate, generated, cfg)
    content_cfg = cfg.get("content_output", {})
    top = []
    for story in [s for s in stories if s.category == "Capital"][:4]:
        top.append(story)
    for category in ["Regulation", "Payments", "Digital Banking", "Infrastructure", "Leadership"]:
        candidate = next((s for s in stories if s.category == category), None)
        if candidate and candidate not in top:
            top.append(candidate)
    for story in stories:
        if len(top) >= cfg["top_items"]:
            break
        if story not in top:
            top.append(story)
    lines = [
        "# Global Fintech Executive Radar",
        "",
        f"*Generated: {generated.strftime('%Y-%m-%d %H:%M Cairo')}*",
        f"*Coverage: worldwide fintech, capital, regulation, payments, digital banking, infrastructure, and leadership*",
        "",
        "## Executive Decision Card",
        "",
        f"- High-priority developments: **{sum(s.score >= 65 for s in stories)}**",
        f"- Capital events: **{len(capital)}**",
        f"- Primary-source verified/corroborated: **{len(verified)}**",
        f"- Direct GCC relevance: **{len(gcc)}**",
        "- Rule: discovery-only items are leads, not confirmed facts.",
        "",
        "## Top Developments",
        "",
    ]
    if not top:
        lines.append("_No qualifying developments found in this run._")
    for index, story in enumerate(top, 1):
        evidence = story.evidence_grade.replace("_", " ").title()
        details = " · ".join(filter(None, [story.category, story.amount, story.stage, story.geography, evidence]))
        lines.extend([
            f"### {index}. [{story.title}]({story.url})",
            "",
            f"**{details}**",
            "",
            story.snippet or "No usable summary was returned by the discovery source.",
            "",
            f"- Company/entity: {story.companies}",
            f"- GCC relevance: {story.gcc_relevance}",
            f"- Recommended action: {story.action}",
        ])
        if story.primary_url and story.primary_url != story.url:
            lines.append(f"- Primary evidence: {story.primary_url}")
        lines.append("")
    lines.extend(["## Funding and M&A Ledger", "", "| Company | Amount | Stage/event | Geography | Evidence |", "|---|---:|---|---|---|"])
    for story in capital[:12]:
        lines.append(f"| {story.companies} | {story.amount or 'Not disclosed'} | {story.stage or 'Capital event'} | {story.geography} | {story.evidence_grade.replace('_', ' ').title()} |")
    if not capital:
        lines.append("| None found | - | - | - | - |")
    lines.extend([
        "",
        "## LinkedIn Content Opportunity",
        "",
    ])
    if content_candidate:
        lines.extend([
            f"- Recommended topic: **{content_candidate.title}**",
            f"- Evidence status: **{content_candidate.evidence_grade.replace('_', ' ').title()}**",
            f"- Content status: **{package['status']}**",
            "",
            "### Ready-to-review post text",
            "",
            package["post_text"],
            "",
            "### Visual artifact",
            "",
            f"- Image specification: **{content_cfg.get('image_format', 'PNG')}, {content_cfg.get('image_dimensions', '1080x1350')}**",
            f"- Workspace image: `{package['output_path']}`",
            f"- Telegram-safe image: `{package['telegram_media_path']}`",
            f"- Artifact state: **{'READY' if package['image_ready'] else 'MISSING - DELIVERY BLOCKED'}**",
            "- A prompt or concept never satisfies the image requirement.",
            "- Publishing: **manual approval required**",
        ])
    else:
        lines.append("_Blocked: no evidence-backed content candidate was found._")
    lines.extend([
        "",
        "## Evidence Notes",
        "",
        "- **Primary:** regulator, company, or investor source.",
        "- **Corroborated:** discovery report plus a separate probable primary source.",
        "- **Trusted reporting:** reputable reporting, but no primary source found during this bounded run.",
        "- **Discovery:** useful lead requiring verification before decisions, alerts, or publication.",
        "",
        "## Product Status",
        "",
        "Internal MVP. No public publishing and no automated external delivery.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-primary-enrichment", action="store_true")
    args = parser.parse_args()
    cfg = load_config()
    prompt_path = ROOT / cfg.get("daily_prompt", "prompts/fintech-radar-daily.md")
    if not prompt_path.is_file():
        raise FileNotFoundError(f"Fintech Radar prompt contract missing: {prompt_path}")
    prompt_sha256 = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
    collected: list[Story] = []
    failures: list[str] = []
    now = dt.datetime.now(CAIRO)
    for item in cfg["queries"]:
        query = f'{item["query"]} after:{(now.date() - dt.timedelta(days=cfg["lookback_days"])).isoformat()}'
        try:
            results = google_news(item["query"], limit=35)
        except Exception as exc:
            failures.append(f'{item["category"]}: {exc}')
            continue
        for result in results:
            story = build_story(result, item["category"], cfg)
            if story:
                collected.append(story)
    for story in collected:
        story.score = score_story(story)
    collected = dedupe(collected)
    collected.sort(key=lambda s: (-s.score, s.title.lower()))
    for story in collected[:30]:
        resolve_direct_result(story)
        story.amount = story.amount or extract_amount(f"{story.title} {story.snippet}")
        story.stage = story.stage or extract_stage(f"{story.title} {story.snippet}")
    if not args.no_primary_enrichment:
        enrich_primary(collected, cfg)
        for story in collected:
            story.score = score_story(story)
        collected.sort(key=lambda s: (-s.score, s.title.lower()))
    stories = select_diverse(collected, cfg["max_items"])
    package = content_package(select_content_candidate(stories), now, cfg)
    payload = {
        "generated_at": now.isoformat(),
        "prompt_contract": {"path": str(prompt_path), "sha256": prompt_sha256},
        "failures": failures,
        "stories": [asdict(story) for story in stories],
        "content_package": package,
    }
    report = render(stories, cfg, now)
    if args.dry_run:
        print(report)
        print(json.dumps({"stories": len(stories), "failures": failures}, indent=2))
        return 0 if stories else 2
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    date_path = OUT_DIR / f"fintech-radar-{now.strftime('%Y-%m-%d')}.md"
    json_path = OUT_DIR / f"fintech-radar-{now.strftime('%Y-%m-%d')}.json"
    content_job_path = OUT_DIR / f"content-job-{now.strftime('%Y-%m-%d')}.json"
    latest_path = OUT_DIR / "FINTECH-RADAR-LATEST.md"
    date_path.write_text(report)
    latest_path.write_text(report)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    content_job_path.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n")
    STATE_PATH.write_text(json.dumps({"last_run": now.isoformat(), "story_count": len(stories), "prompt_sha256": prompt_sha256, "failures": failures}, indent=2) + "\n")
    print(json.dumps({"report": str(date_path), "latest": str(latest_path), "stories": len(stories), "content_status": package["status"], "content_job": str(content_job_path), "failures": failures}, indent=2))
    return 0 if stories else 2


if __name__ == "__main__":
    raise SystemExit(main())
