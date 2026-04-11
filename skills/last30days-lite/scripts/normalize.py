#!/usr/bin/env python3
"""
normalize.py — Convert raw search results into canonical scored items,
then deterministically cluster and dedupe near-duplicate findings.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


# ---------------------------------------------------------------------------
# Canonical schema
# ---------------------------------------------------------------------------

@dataclass
class Engagement:
    upvotes: int = 0
    comments: int = 0
    shares: int = 0


@dataclass
class RankingProfile:
    name: str
    topic_type: str
    reasons: list[str] = field(default_factory=list)
    relevance_weight: float = 0.45
    recency_weight: float = 0.43
    engagement_weight: float = 0.12
    source_multipliers: dict[str, float] = field(default_factory=dict)
    source_bonuses: dict[str, float] = field(default_factory=dict)
    source_repeat_penalties: dict[str, float] = field(default_factory=dict)


@dataclass
class ResearchItem:
    id: str
    title: str
    url: str
    source: str
    source_sub: str
    published_date: str
    engagement: Engagement
    relevance_signal: float
    recency_score: float
    final_score: float
    entities: list[str]
    snippet: str
    canonical_url: str = ""
    result_type: str = "unknown"
    authority_tier: str = "unknown"
    freshness_confidence: float = 1.0
    source_trust_score: float = 0.5
    claim_confidence_score: float = 0.45
    claim_confidence_label: str = "low"
    cluster_id: str = ""
    cluster_size: int = 1
    cluster_sources: list[str] = field(default_factory=list)
    cluster_member_ids: list[str] = field(default_factory=list)
    cluster_titles: list[str] = field(default_factory=list)
    cluster_reasons: list[str] = field(default_factory=list)
    score_breakdown: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

RECENCY_WINDOW_DAYS = 30

UTILITY_SUBS = {
    "r/tipofmytongue", "r/whatisthisthing", "r/findareddit",
    "r/newtoreddit", "r/subredditstats",
}

TRACKING_QUERY_PARAMS = {
    "fbclid", "gclid", "igshid", "mc_cid", "mc_eid", "mkt_tok",
    "ref", "ref_src", "ref_url", "source", "spm", "trk", "ved", "tl",
}

STOPWORDS = {
    "a", "an", "and", "at", "by", "for", "from", "how", "in", "into",
    "is", "it", "of", "on", "or", "the", "to", "with", "why", "what",
    "who", "when", "where", "after", "before", "over", "under", "vs",
    "via", "new", "latest", "update", "updated", "announces", "launches",
}

STRONG_CODE_HINTS = {
    "github", "repo", "repository", "sdk", "api", "cli", "framework",
    "library", "package", "python", "javascript", "typescript", "swift",
    "ios", "android", "npm", "pip", "open source", "developer", "coding",
    "code",
}

SOFT_CODE_HINTS = {
    "tool", "tooling", "agent", "agents", "assistant", "workflow", "llm",
    "model", "models",
}


# ---------------------------------------------------------------------------
# Ranking profile
# ---------------------------------------------------------------------------


def _match_hint_terms(text: str, hints: set[str]) -> list[str]:
    lowered = f" {_clean_text(text)} "
    matches: list[str] = []
    for hint in sorted(hints):
        pattern = f" {hint.lower()} " if " " not in hint else f" {hint.lower()} "
        if pattern in lowered:
            matches.append(hint)
    return matches


def build_ranking_profile(topic: str, plan: Optional[dict] = None) -> RankingProfile:
    plan = plan or {}
    canonical_topic = str(plan.get("canonical_topic") or topic or "")
    topic_type = str(plan.get("type") or "topic")
    handles = plan.get("handles") or {}
    topic_text = " ".join(part for part in [topic, canonical_topic] if part)
    strong_code_hits = _match_hint_terms(topic_text, STRONG_CODE_HINTS)
    soft_code_hits = _match_hint_terms(topic_text, SOFT_CODE_HINTS)
    github_handle = str(handles.get("github") or "").strip()
    repo_like = bool(re.search(r"\b[\w.-]+/[\w.-]+\b", topic_text))
    explicit_github_focus = any(token in topic_text.lower() for token in {"github", "repo", "repository"})
    code_cues = sorted(set(strong_code_hits + soft_code_hits))

    if repo_like or explicit_github_focus:
        return RankingProfile(
            name="repo-centric",
            topic_type=topic_type,
            reasons=["explicit repo or GitHub-focused topic"],
            source_multipliers={"tavily": 0.98, "reddit": 0.96, "hn": 0.96, "github": 1.18},
            source_bonuses={"tavily": 0.01, "reddit": 0.03, "hn": 0.02, "github": 0.04},
            source_repeat_penalties={"tavily": 0.02, "reddit": 0.01, "hn": 0.01, "github": 0.02},
        )

    if len(strong_code_hits) >= 2 or (len(strong_code_hits) >= 1 and len(soft_code_hits) >= 2) or (topic_type == "product" and github_handle):
        reasons = ["topic reads as code, tooling, or open-source centric"]
        if code_cues:
            reasons.append("code cues: " + ", ".join(code_cues[:4]))
        return RankingProfile(
            name="code-balanced",
            topic_type=topic_type,
            reasons=reasons,
            source_multipliers={"tavily": 1.02, "reddit": 1.00, "hn": 1.03, "github": 1.05},
            source_bonuses={"tavily": 0.02, "reddit": 0.03, "hn": 0.04, "github": 0.01},
            source_repeat_penalties={"tavily": 0.02, "reddit": 0.01, "hn": 0.02, "github": 0.05},
        )

    if topic_type == "person":
        reasons = ["person search should not be dominated by unrelated repositories"]
        if github_handle:
            reasons.append("GitHub handle kept as a useful but secondary signal")
        return RankingProfile(
            name="person-balanced",
            topic_type=topic_type,
            reasons=reasons,
            source_multipliers={"tavily": 1.07, "reddit": 1.07, "hn": 1.10, "github": 0.52},
            source_bonuses={"tavily": 0.03, "reddit": 0.06, "hn": 0.06, "github": -0.02},
            source_repeat_penalties={"tavily": 0.03, "reddit": 0.01, "hn": 0.02, "github": 0.12},
        )

    return RankingProfile(
        name="general-balanced",
        topic_type=topic_type,
        reasons=["general topic, so GitHub is treated as supporting evidence unless explicitly central"],
        source_multipliers={"tavily": 1.06, "reddit": 1.08, "hn": 1.10, "github": 0.58},
        source_bonuses={"tavily": 0.03, "reddit": 0.06, "hn": 0.05, "github": -0.01},
        source_repeat_penalties={"tavily": 0.03, "reddit": 0.01, "hn": 0.02, "github": 0.10},
    )


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _recency_score(published_date: str) -> float:
    if not published_date:
        return 0.45
    try:
        pub = datetime.fromisoformat(published_date).replace(tzinfo=timezone.utc)
    except ValueError:
        return 0.45
    now = datetime.now(timezone.utc)
    days_old = max(0, (now - pub).days)
    return max(0.0, 1.0 - (days_old / RECENCY_WINDOW_DAYS))


def _engagement_signal(eng: Engagement) -> float:
    return eng.upvotes + (eng.comments * 2.0) + (eng.shares * 0.5)


def _engagement_score(eng: Engagement) -> float:
    signal = _engagement_signal(eng)
    if signal <= 0:
        return 0.0
    return min(1.0, math.log1p(signal) / 6.0)


def _domain_adjustment(item: ResearchItem, profile: RankingProfile) -> tuple[float, str]:
    url = (item.canonical_url or item.url or "").lower()
    multiplier = 1.0
    reasons: list[str] = []

    if "github.com" in url and item.source != "github":
        if profile.name in {"person-balanced", "general-balanced"}:
            multiplier *= 0.82
            reasons.append("github-domain-downweight")
        elif profile.name == "code-balanced":
            multiplier *= 0.95
            reasons.append("github-domain-soft-downweight")

    if any(domain in url for domain in {"x.com", "twitter.com"}):
        if profile.name == "repo-centric":
            multiplier *= 0.90
            reasons.append("x-domain-soft-downweight")
        else:
            multiplier *= 0.76
            reasons.append("x-domain-downweight")

    if item.authority_tier == "reference":
        multiplier *= 1.08
        reasons.append("reference-authority")
    elif item.authority_tier == "official":
        multiplier *= 1.05
        reasons.append("official-authority")
    elif item.authority_tier == "community" and profile.name in {"person-balanced", "general-balanced"}:
        multiplier *= 0.93
        reasons.append("community-downweight")
    elif item.authority_tier == "social" and profile.name in {"person-balanced", "general-balanced"}:
        multiplier *= 0.92
        reasons.append("social-authority-downweight")
    elif item.authority_tier == "weak-web":
        multiplier *= 0.86
        reasons.append("weak-web-downweight")

    if item.result_type == "listing":
        multiplier *= 0.78
        reasons.append("listing-downweight")
    elif item.result_type == "profile":
        multiplier *= 0.82
        reasons.append("profile-downweight")
    elif item.result_type == "homepage":
        multiplier *= 0.88
        reasons.append("homepage-downweight")
    elif item.result_type == "article":
        multiplier *= 1.05
        reasons.append("article-upweight")
    elif item.result_type == "social-post":
        if profile.name in {"person-balanced", "general-balanced"}:
            multiplier *= 0.86
            reasons.append("social-post-downweight")
        else:
            multiplier *= 0.94
            reasons.append("social-post-soft-downweight")
    elif item.result_type in {"repo", "issue", "pr"}:
        if profile.name in {"code-balanced", "repo-centric"}:
            multiplier *= 1.05
            reasons.append("code-artifact-upweight")
        elif profile.name in {"person-balanced", "general-balanced"}:
            multiplier *= 0.94
            reasons.append("code-artifact-soft-downweight")

    if item.freshness_confidence < 1.0:
        multiplier *= item.freshness_confidence
        reasons.append(f"freshness-confidence:{item.freshness_confidence:.2f}")

    return multiplier, "+".join(reasons) if reasons else "none"


def score(item: ResearchItem, ranking_profile: Optional[RankingProfile] = None) -> ResearchItem:
    profile = ranking_profile or build_ranking_profile(item.title, {"type": "topic"})
    item.recency_score = _recency_score(item.published_date)

    relevance_component = item.relevance_signal * profile.relevance_weight
    recency_component = item.recency_score * profile.recency_weight
    engagement_component = _engagement_score(item.engagement) * profile.engagement_weight
    raw = relevance_component + recency_component + engagement_component

    source_multiplier = profile.source_multipliers.get(item.source, 1.0)
    source_bonus = profile.source_bonuses.get(item.source, 0.0)
    trust_multiplier = 0.85 + (item.source_trust_score * 0.25)
    domain_multiplier, domain_reason = _domain_adjustment(item, profile)
    final = max(0.0, min(1.0, raw * source_multiplier * trust_multiplier * domain_multiplier + source_bonus))

    item.final_score = final
    item.score_breakdown = {
        "profile": profile.name,
        "profile_reasons": profile.reasons,
        "weights": {
            "relevance": profile.relevance_weight,
            "recency": profile.recency_weight,
            "engagement": profile.engagement_weight,
        },
        "components": {
            "relevance": round(relevance_component, 4),
            "recency": round(recency_component, 4),
            "engagement": round(engagement_component, 4),
            "raw": round(raw, 4),
        },
        "adjustments": {
            "source": item.source,
            "source_multiplier": source_multiplier,
            "source_bonus": source_bonus,
            "source_trust_score": item.source_trust_score,
            "trust_multiplier": round(trust_multiplier, 4),
            "domain_multiplier": domain_multiplier,
            "domain_reason": domain_reason,
            "result_type": item.result_type,
            "authority_tier": item.authority_tier,
            "freshness_confidence": item.freshness_confidence,
            "source_repeat_index": 1,
            "source_repeat_penalty": 0.0,
        },
    }
    return item


def apply_source_blend(items: list[ResearchItem], ranking_profile: Optional[RankingProfile] = None) -> list[ResearchItem]:
    profile = ranking_profile or build_ranking_profile("", {"type": "topic"})
    penalties = profile.source_repeat_penalties or {}
    counts: dict[str, int] = {}

    blended: list[ResearchItem] = []
    for item in sorted(items, key=_cluster_sort_key):
        source_index = counts.get(item.source, 0) + 1
        repeat_penalty = penalties.get(item.source, 0.0) * max(0, source_index - 1)
        if repeat_penalty:
            item.final_score = max(0.0, min(1.0, item.final_score - repeat_penalty))

        adjustments = item.score_breakdown.setdefault("adjustments", {})
        adjustments["source_repeat_index"] = source_index
        adjustments["source_repeat_penalty"] = round(repeat_penalty, 4)
        adjustments["blended_score"] = round(item.final_score, 4)

        counts[item.source] = source_index
        blended.append(item)

    blended.sort(key=_cluster_sort_key)
    return blended


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def canonicalize_url(url: str) -> str:
    if not url:
        return ""

    parsed = urlsplit(url.strip())
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    if netloc.startswith("m.") and netloc.endswith("youtube.com"):
        netloc = "youtube.com"

    path = re.sub(r"/+", "/", parsed.path or "/")
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    query_pairs = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=False):
        norm_key = key.lower()
        if norm_key.startswith("utm_") or norm_key in TRACKING_QUERY_PARAMS:
            continue
        if netloc in {"youtube.com", "youtu.be"} and path == "/watch" and norm_key != "v":
            continue
        if netloc.endswith("github.com"):
            continue
        query_pairs.append((norm_key, value))

    if netloc == "youtu.be" and path.strip("/"):
        query_pairs = [("v", path.strip("/"))]
        path = "/watch"
        netloc = "youtube.com"

    if netloc.endswith("reddit.com"):
        path = re.sub(r"(/comments/[a-z0-9]+/[^/]+).*$", r"\1", path, flags=re.IGNORECASE)
        query_pairs = [(key, value) for key, value in query_pairs if key not in {"tl"}]

    if netloc in {"x.com", "twitter.com"}:
        status_match = re.match(r"^/([^/]+)/status/(\d+)", path)
        if status_match:
            path = f"/{status_match.group(1)}/status/{status_match.group(2)}"

    query = urlencode(sorted(query_pairs), doseq=True)
    return urlunsplit(("https", netloc, path or "/", query, ""))


def _hash_id(url: str, title: str) -> str:
    raw = f"{url}|{title}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _slug_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def _normalize_date(date_str: str) -> str:
    if not date_str:
        return ""
    text = date_str.strip()
    if not text:
        return ""

    iso_candidate = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_candidate).date().isoformat()
    except ValueError:
        pass

    for fmt in (
        "%Y-%m-%d", "%d %b %Y", "%b %d, %Y", "%Y/%m/%d",
        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    return ""


def _extract_subreddit(url: str) -> str:
    m = re.search(r"reddit\.com/r/([a-zA-Z0-9_]+)", url)
    if m:
        sub = f"r/{m.group(1)}"
        if sub.lower() not in UTILITY_SUBS:
            return sub
    return ""


def _extract_entities(text: str) -> list[str]:
    phrases = re.findall(r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,2})\b", text)
    out: list[str] = []
    for phrase in phrases:
        clean = " ".join(phrase.split())
        if clean and clean not in out:
            out.append(clean)
    return out


def infer_result_type(source: str, url: str, title: str, source_sub: str = "") -> str:
    parsed = urlsplit(url or "")
    netloc = parsed.netloc.lower().replace("www.", "")
    path = (parsed.path or "/").lower()
    title_l = (title or "").lower()
    source_sub_l = (source_sub or "").lower()

    if source == "github":
        if source_sub_l.startswith("repo:"):
            return "repo"
        if source_sub_l.startswith("pr:"):
            return "pr"
        if source_sub_l.startswith("issue:"):
            return "issue"
        return "repo"

    if netloc.endswith("wikipedia.org"):
        return "reference"
    if netloc in {"x.com", "twitter.com"}:
        return "social-post" if "/status/" in path else "profile"
    if netloc == "instagram.com":
        return "social-post" if path.startswith("/p/") or path.startswith("/reel/") else "profile"
    if netloc.endswith("linkedin.com"):
        if "/pulse/" in path:
            return "article"
        if "/posts/" in path or "/activity-" in path:
            return "social-post"
        return "profile"
    if netloc.endswith("reddit.com"):
        return "discussion" if "/comments/" in path else "listing"
    if netloc == "news.ycombinator.com":
        return "discussion"
    if path in {"", "/"}:
        return "homepage"
    if re.search(r"/(blog|news|article|articles|post|posts/[^/]+|p/[^/]+|updates?|changelog|release|releases|interview)(/|$)", path):
        return "article"
    if path.endswith("/posts") or path.endswith("/blog") or path.endswith("/news") or path.endswith("/articles"):
        return "listing"
    if any(word in title_l for word in ["interview", "changelog", "release", "update", "speaker"]):
        return "article"
    if source in {"reddit", "hn"}:
        return "discussion"
    return "page"


def infer_authority_tier(source: str, url: str, result_type: str) -> str:
    netloc = urlsplit(url or "").netloc.lower().replace("www.", "")
    if netloc.endswith("wikipedia.org"):
        return "reference"
    if netloc.startswith("docs.") or result_type in {"release-notes"}:
        return "official"
    if source == "github" and result_type == "repo":
        return "official"
    if netloc in {"reddit.com", "news.ycombinator.com"}:
        return "community"
    if netloc in {"x.com", "twitter.com", "linkedin.com", "instagram.com"}:
        return "social"
    if result_type in {"article", "page"}:
        return "web"
    if result_type in {"listing", "profile", "homepage"}:
        return "weak-web"
    return "unknown"


def infer_freshness_confidence(result_type: str, published_date: str) -> float:
    if published_date:
        return 1.0
    if result_type in {"listing", "profile", "homepage"}:
        return 0.72
    if result_type in {"discussion", "social-post"}:
        return 0.82
    if result_type in {"article", "reference", "repo", "issue", "pr", "page"}:
        return 0.90
    return 0.84


def infer_source_trust_score(source: str, authority_tier: str, result_type: str, url: str) -> float:
    score = 0.55
    if authority_tier == "reference":
        score = 0.95
    elif authority_tier == "official":
        score = 0.90
    elif authority_tier == "web":
        score = 0.76
    elif authority_tier == "community":
        score = 0.60
    elif authority_tier == "social":
        score = 0.50
    elif authority_tier == "weak-web":
        score = 0.42

    if result_type == "article":
        score += 0.04
    elif result_type in {"listing", "profile", "homepage"}:
        score -= 0.08
    elif result_type in {"repo", "issue", "pr"}:
        score += 0.03

    netloc = urlsplit(url or "").netloc.lower().replace("www.", "")
    if netloc.endswith("wikipedia.org"):
        score = max(score, 0.96)
    if netloc in {"reddit.com", "news.ycombinator.com"}:
        score = min(score, 0.64)
    if netloc in {"x.com", "twitter.com", "linkedin.com", "instagram.com"}:
        score = min(score, 0.58)

    return max(0.10, min(1.0, score))


def _clean_text(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"https?://\S+", " ", lowered)
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _title_tokens(text: str) -> set[str]:
    tokens = _clean_text(text).split()
    return {
        token for token in tokens
        if token not in STOPWORDS and (len(token) > 2 or token in {"ai", "gh"})
    }


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _cluster_sort_key(item: ResearchItem) -> tuple:
    return (
        -item.final_score,
        item.published_date or "",
        item.canonical_url or item.url,
        item.title.lower(),
        item.id,
    )


# ---------------------------------------------------------------------------
# Normalizers
# ---------------------------------------------------------------------------


def from_tavily(raw: dict) -> ResearchItem:
    url = raw.get("url", "")
    title = raw.get("title", "")
    snippet = raw.get("description", "") or raw.get("content", "")[:300]
    pub_date = _normalize_date(raw.get("published_date", "") or "")
    relevance = max(0.0, min(1.0, float(raw.get("_rank_signal", raw.get("score", 0.5)))))
    source_sub = _extract_subreddit(url)
    if not source_sub:
        domain = urlsplit(url).netloc.lower().replace("www.", "")
        if domain in {"x.com", "twitter.com"}:
            source_sub = "x"
        elif domain in {"youtube.com", "youtu.be"}:
            source_sub = "youtube"
        elif domain == "github.com":
            source_sub = "github-web"

    canonical_url = canonicalize_url(url)
    result_type = infer_result_type("tavily", canonical_url or url, title, source_sub)
    authority_tier = infer_authority_tier("tavily", canonical_url or url, result_type)
    freshness_confidence = infer_freshness_confidence(result_type, pub_date)
    source_trust_score = infer_source_trust_score("tavily", authority_tier, result_type, canonical_url or url)
    return ResearchItem(
        id=_hash_id(canonical_url or url, title),
        title=title,
        url=url,
        source="tavily",
        source_sub=source_sub,
        published_date=pub_date,
        engagement=Engagement(),
        relevance_signal=relevance,
        recency_score=0.0,
        final_score=0.0,
        entities=_extract_entities(title + " " + snippet),
        snippet=snippet[:500],
        canonical_url=canonical_url,
        result_type=result_type,
        authority_tier=authority_tier,
        freshness_confidence=freshness_confidence,
        source_trust_score=source_trust_score,
    )


def from_reddit(raw: dict) -> ResearchItem:
    permalink = raw.get("permalink", "") or ""
    if permalink.startswith("/"):
        permalink = f"https://www.reddit.com{permalink}"
    outbound_url = raw.get("url", "") or ""
    display_url = permalink or outbound_url
    title = raw.get("title", raw.get("text", ""))
    snippet = raw.get("selftext", "") or raw.get("body", "")[:300]
    score_value = raw.get("score", 0)
    comments = raw.get("num_comments", 0)
    created = raw.get("created_utc", 0)
    sub = raw.get("subreddit", "")
    pub_date = raw.get("published_date", "") or (
        datetime.fromtimestamp(created, tz=timezone.utc).date().isoformat()
        if created else ""
    )

    canonical_base = outbound_url if outbound_url and "reddit.com" not in outbound_url else display_url
    canonical_url = canonicalize_url(canonical_base)
    relevance = max(0.0, min(1.0, float(raw.get("_rank_signal", 0.58))))
    source_sub = f"r/{sub}" if sub else ""
    result_type = infer_result_type("reddit", canonical_url or display_url, title, source_sub)
    authority_tier = infer_authority_tier("reddit", canonical_url or display_url, result_type)
    freshness_confidence = infer_freshness_confidence(result_type, pub_date)
    source_trust_score = infer_source_trust_score("reddit", authority_tier, result_type, canonical_url or display_url)

    return ResearchItem(
        id=_hash_id(canonical_url or display_url, title),
        title=title,
        url=display_url,
        source="reddit",
        source_sub=source_sub,
        published_date=pub_date,
        engagement=Engagement(upvotes=int(score_value or 0), comments=int(comments or 0)),
        relevance_signal=relevance,
        recency_score=0.0,
        final_score=0.0,
        entities=_extract_entities(title + " " + snippet),
        snippet=snippet[:500],
        canonical_url=canonical_url,
        result_type=result_type,
        authority_tier=authority_tier,
        freshness_confidence=freshness_confidence,
        source_trust_score=source_trust_score,
    )


def from_hn(raw: dict) -> ResearchItem:
    url = raw.get("url", "") or f"https://news.ycombinator.com/item?id={raw.get('id', '')}"
    title = raw.get("title", "")
    score_value = raw.get("points", 0)
    comments = raw.get("num_comments", 0)
    pub_date = _normalize_date(raw.get("created_at", "")[:10])

    canonical_url = canonicalize_url(url)
    result_type = infer_result_type("hn", canonical_url or url, title)
    authority_tier = infer_authority_tier("hn", canonical_url or url, result_type)
    freshness_confidence = infer_freshness_confidence(result_type, pub_date)
    source_trust_score = infer_source_trust_score("hn", authority_tier, result_type, canonical_url or url)
    return ResearchItem(
        id=_hash_id(canonical_url or url, title),
        title=title,
        url=url,
        source="hn",
        source_sub="",
        published_date=pub_date,
        engagement=Engagement(upvotes=int(score_value or 0), comments=int(comments or 0)),
        relevance_signal=0.5,
        recency_score=0.0,
        final_score=0.0,
        entities=_extract_entities(title),
        snippet=(raw.get("text", "") or "")[:300],
        canonical_url=canonical_url,
        result_type=result_type,
        authority_tier=authority_tier,
        freshness_confidence=freshness_confidence,
        source_trust_score=source_trust_score,
    )


def from_github(raw: dict) -> ResearchItem:
    kind = raw.get("_kind", "github")
    url = raw.get("html_url", "") or raw.get("url", "")
    repo_name = raw.get("full_name") or raw.get("repository_full_name") or raw.get("repository", {}).get("full_name", "")
    title = raw.get("title") or raw.get("full_name") or raw.get("name") or url
    snippet = raw.get("body") or raw.get("description") or raw.get("text_matches_snippet") or ""
    pub_date = _normalize_date(
        raw.get("updated_at")
        or raw.get("pushed_at")
        or raw.get("created_at")
        or ""
    )

    if kind == "repo":
        engagement = Engagement(
            upvotes=int(raw.get("stargazers_count", 0) or 0),
            comments=int(raw.get("forks_count", 0) or 0),
            shares=int(raw.get("watchers_count", 0) or 0),
        )
    else:
        engagement = Engagement(
            upvotes=int(raw.get("reactions", {}).get("total_count", 0) or 0),
            comments=int(raw.get("comments", 0) or 0),
            shares=0,
        )

    canonical_url = canonicalize_url(url)
    sub = f"{kind}:{repo_name}" if repo_name else kind
    relevance = max(0.0, min(1.0, float(raw.get("_rank_signal", 0.55))))
    entity_text = " ".join(part for part in [title, snippet, repo_name] if part)
    result_type = infer_result_type("github", canonical_url or url, title, sub)
    authority_tier = infer_authority_tier("github", canonical_url or url, result_type)
    freshness_confidence = infer_freshness_confidence(result_type, pub_date)
    source_trust_score = infer_source_trust_score("github", authority_tier, result_type, canonical_url or url)

    return ResearchItem(
        id=_hash_id(canonical_url or url, title),
        title=title,
        url=url,
        source="github",
        source_sub=sub,
        published_date=pub_date,
        engagement=engagement,
        relevance_signal=relevance,
        recency_score=0.0,
        final_score=0.0,
        entities=_extract_entities(entity_text),
        snippet=snippet[:500],
        canonical_url=canonical_url,
        result_type=result_type,
        authority_tier=authority_tier,
        freshness_confidence=freshness_confidence,
        source_trust_score=source_trust_score,
    )


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------


def normalize_batch(raws: list[dict], source: str = "tavily", ranking_profile: Optional[RankingProfile] = None) -> list[ResearchItem]:
    normalizers = {
        "tavily": from_tavily,
        "reddit": from_reddit,
        "hn": from_hn,
        "github": from_github,
    }
    norm_fn = normalizers.get(source, from_tavily)
    items = [norm_fn(r) for r in raws if r]
    scored = [score(it, ranking_profile=ranking_profile) for it in items]
    scored.sort(key=_cluster_sort_key)
    return scored


def _cluster_match(anchor: ResearchItem, candidate: ResearchItem) -> list[str]:
    reasons: list[str] = []

    if anchor.canonical_url and anchor.canonical_url == candidate.canonical_url:
        reasons.append("canonical_url")
        return reasons

    title_a = _title_tokens(anchor.title)
    title_b = _title_tokens(candidate.title)
    title_similarity = _jaccard(title_a, title_b)

    entities_a = {entity.lower() for entity in anchor.entities}
    entities_b = {entity.lower() for entity in candidate.entities}
    entity_overlap = len(entities_a & entities_b)

    norm_title_a = _clean_text(anchor.title)
    norm_title_b = _clean_text(candidate.title)

    if norm_title_a and norm_title_a == norm_title_b:
        reasons.append("title_exact")
        return reasons

    if title_similarity >= 0.82:
        reasons.append(f"title_jaccard:{title_similarity:.2f}")
        return reasons

    if title_similarity >= 0.68 and entity_overlap >= 1:
        reasons.append(f"title_entity:{title_similarity:.2f}/{entity_overlap}")
        return reasons

    if entity_overlap >= 2 and (
        norm_title_a in norm_title_b or norm_title_b in norm_title_a
    ):
        reasons.append(f"entity_overlap:{entity_overlap}")
        return reasons

    return reasons


def _claim_confidence(members: list[ResearchItem], representative: ResearchItem) -> tuple[float, str]:
    distinct_sources = len({member.source for member in members})
    max_trust = max((member.source_trust_score for member in members), default=representative.source_trust_score)
    avg_trust = sum(member.source_trust_score for member in members) / max(1, len(members))
    published_bonus = 0.08 if any(member.published_date for member in members) else 0.0
    corroboration_bonus = min(0.18, 0.07 * max(0, distinct_sources - 1))
    cluster_bonus = min(0.10, 0.04 * max(0, len(members) - 1))
    authority_bonus = 0.05 if representative.authority_tier in {"official", "reference"} else 0.0
    freshness = max((member.freshness_confidence for member in members), default=representative.freshness_confidence)

    score = (avg_trust * 0.55) + (max_trust * 0.15) + published_bonus + corroboration_bonus + cluster_bonus + authority_bonus
    score *= (0.82 + (freshness * 0.18))
    score = max(0.12, min(0.98, score))

    if score >= 0.78:
        label = "high"
    elif score >= 0.58:
        label = "medium"
    else:
        label = "low"
    return score, label


def cluster_items(items: list[ResearchItem]) -> list[ResearchItem]:
    clusters: list[dict] = []

    for item in sorted(items, key=_cluster_sort_key):
        matched_cluster: Optional[dict] = None
        matched_reasons: list[str] = []

        for cluster in clusters:
            reasons = _cluster_match(cluster["representative"], item)
            if reasons:
                matched_cluster = cluster
                matched_reasons = reasons
                break

        if matched_cluster is None:
            clusters.append({
                "representative": item,
                "members": [item],
                "reasons": [],
            })
            continue

        matched_cluster["members"].append(item)
        matched_cluster["reasons"].extend(matched_reasons)

        if _cluster_sort_key(item) < _cluster_sort_key(matched_cluster["representative"]):
            matched_cluster["representative"] = item

    deduped: list[ResearchItem] = []
    for cluster in clusters:
        members: list[ResearchItem] = sorted(cluster["members"], key=_cluster_sort_key)
        rep = members[0]
        member_ids = sorted(member.id for member in members)
        cluster_sources = sorted({member.source for member in members})
        titles: list[str] = []
        for member in members:
            if member.title and member.title not in titles:
                titles.append(member.title)

        rep.cluster_member_ids = member_ids
        rep.cluster_sources = cluster_sources
        rep.cluster_size = len(members)
        rep.cluster_titles = titles
        rep.cluster_reasons = sorted(set(cluster["reasons"]))
        rep.cluster_id = _slug_hash("|".join(member_ids))
        rep.claim_confidence_score, rep.claim_confidence_label = _claim_confidence(members, rep)
        rep.score_breakdown.setdefault("adjustments", {})["claim_confidence_score"] = round(rep.claim_confidence_score, 4)
        rep.score_breakdown.setdefault("adjustments", {})["claim_confidence_label"] = rep.claim_confidence_label
        if not rep.snippet:
            rep.snippet = next((member.snippet for member in members if member.snippet), "")
        deduped.append(rep)

    deduped.sort(key=lambda item: (-item.final_score, -item.cluster_size, item.title.lower(), item.id))
    return deduped


def scored_to_dict(item: ResearchItem) -> dict:
    return asdict(item)


def ranking_profile_to_dict(profile: RankingProfile) -> dict:
    return asdict(profile)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    raws = json.load(sys.stdin)
    items = normalize_batch(raws)
    out = [scored_to_dict(it) for it in items]
    json.dump(out, sys.stdout, indent=2)
