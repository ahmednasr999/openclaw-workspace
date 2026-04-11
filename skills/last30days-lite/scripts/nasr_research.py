#!/usr/bin/env python3
"""
nasr_research.py — Main orchestrator for NASR Research v2.

Usage:
    python3 nasr_research.py "<topic>" [--save-dir DIR] [--max-items N]
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from llm_utils import chat_complete
from resolver import resolve
from normalize import (
    RankingProfile,
    ResearchItem,
    apply_source_blend,
    build_ranking_profile,
    cluster_items,
    normalize_batch,
    ranking_profile_to_dict,
    scored_to_dict,
)

SKILL_ROOT = Path(__file__).parent.parent.resolve()
CONFIG_DIR = SKILL_ROOT.parent.parent / "config"
CACHE_DIR = Path.home() / ".cache" / "nasr-research"
SAVE_DIR = Path.home() / "Documents" / "NASR-Research"

GENERIC_TOPIC_TOKENS = {
    "ai", "agent", "agents", "api", "app", "apps", "assistant", "code",
    "copilot", "framework", "github", "llm", "llms", "model", "models",
    "openai", "platform", "sdk", "software", "tool", "tools", "workflow",
}
SOCIAL_NOISE_DOMAINS = {"x.com", "twitter.com"}
SOCIAL_NOISE_PHRASES = {
    "last30days",
    "slashlast30days",
    "clawhub",
    "install the last30days skill",
}


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def lane_report(status: str, count: int = 0, note: str = "", **extra: object) -> dict:
    payload = {"status": status, "count": count}
    if note:
        payload["note"] = note
    payload.update(extra)
    return payload


# ---------------------------------------------------------------------------
# Tavily search
# ---------------------------------------------------------------------------

def search_tavily(query: str, api_key: str, max_results: int = 8) -> list[dict]:
    if not api_key:
        print("[tavily] skipped, no API key available", file=sys.stderr)
        return []

    payload = json.dumps({
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
    }).encode()

    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            return data.get("results", [])
    except urllib.error.HTTPError as exc:
        print(f"[tavily] ERROR {exc.code}: {exc.read().decode()}", file=sys.stderr)
        return []
    except Exception as exc:
        print(f"[tavily] ERROR: {exc}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Reddit lane
# ---------------------------------------------------------------------------

def _reddit_fetch_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "nasr-research/2.1",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def _clean_reddit_query(query: str) -> str:
    clean = " ".join(str(query or "").split()).strip()
    clean = re.sub(r"\b(?:last|past)\s+30\s+days\b", " ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bthis\s+month\b", " ", clean, flags=re.IGNORECASE)
    clean = clean.replace("site:reddit.com", " ")
    clean = re.sub(r"\s+OR\s+", " ", clean, flags=re.IGNORECASE)
    clean = clean.strip(" '\"")
    return " ".join(clean.split())


def _reddit_queries(topic: str, plan: dict) -> list[str]:
    canonical = (plan.get("canonical_topic") or topic or "").strip()
    handles = plan.get("handles") or {}
    queries = list((plan.get("queries") or {}).get("reddit", [])[:3])
    queries.extend((plan.get("queries") or {}).get("web", [])[:1])
    if canonical:
        queries.append(canonical)
    if handles.get("x"):
        queries.append(str(handles["x"]).lstrip("@"))
    if handles.get("github"):
        queries.append(str(handles["github"]))

    out: list[str] = []
    for query in queries:
        clean = _clean_reddit_query(str(query or ""))
        if clean and clean not in out:
            out.append(clean)
    return out[:4]


def _reddit_relevance(item: dict, aliases: set[str], tokens: set[str]) -> tuple[bool, float]:
    title = item.get("title") or ""
    selftext = item.get("selftext") or item.get("body") or ""
    url = item.get("url") or ""
    subreddit = item.get("subreddit") or ""
    match = _topic_match_metrics(
        " ".join([title, url, subreddit]),
        selftext[:600],
        aliases,
        tokens,
    )
    keep = _passes_topic_gate(match, lane="reddit", domain=_domain_from_url(url or "https://www.reddit.com"))
    engagement_hint = min(1.0, ((item.get("score") or 0) + (item.get("num_comments") or 0) * 2) / 200.0)
    strength = _topic_rank_signal(0.46 + engagement_hint * 0.24, match, lane="reddit", domain="reddit.com")
    return keep, min(0.90, strength)


def _reddit_url_is_listing(url: str) -> bool:
    lowered = str(url or "").lower()
    path = urllib.parse.urlsplit(lowered).path
    return bool(re.match(r"^/r/[^/]+/?$", path)) or "/comments/" not in path


def _reddit_url_is_noise(url: str) -> bool:
    lowered = str(url or "").lower()
    if any(token in lowered for token in ["?tl=", "&tl=", "/user/", "/u/"]):
        return True
    if "reddit.com" in lowered and _reddit_url_is_listing(lowered):
        return True
    return False


def _reddit_item_from_tavily(raw: dict) -> dict:
    url = str(raw.get("url") or "")
    title = str(raw.get("title") or "").strip()
    title = re.sub(r"\s+-\s+Reddit$", "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"\s*:\s*r/[A-Za-z0-9_]+$", "", title).strip()
    subreddit_match = re.search(r"reddit\.com/r/([A-Za-z0-9_]+)/", url)
    return {
        "title": title,
        "url": url,
        "permalink": url,
        "selftext": str(raw.get("description") or raw.get("content") or "")[:500],
        "subreddit": subreddit_match.group(1) if subreddit_match else "",
        "published_date": raw.get("published_date", "") or "",
        "score": int(round(max(0.0, min(1.0, float(raw.get("score") or 0.0))) * 100)),
        "num_comments": 0,
        "_rank_signal": float(raw.get("_rank_signal") or raw.get("score") or 0.6),
    }


def _search_reddit_json_legacy(topic: str, plan: dict, max_results: int = 8) -> tuple[list[dict], dict]:
    queries = _reddit_queries(topic, plan)
    aliases = _topic_aliases(topic, plan)
    tokens = _topic_tokens(topic, plan)
    seen: set[str] = set()
    lane_items: list[dict] = []
    base_limit = max(4, min(max_results, 8))
    blocked_codes: list[int] = []
    attempt_count = 0

    def collect(search_url: str, label: str) -> None:
        nonlocal attempt_count
        attempt_count += 1
        try:
            payload = _reddit_fetch_json(search_url)
        except urllib.error.HTTPError as exc:
            print(f"[reddit] legacy {label} failed: HTTP {exc.code}", file=sys.stderr)
            if exc.code in {403, 429}:
                blocked_codes.append(exc.code)
            return
        except Exception as exc:
            print(f"[reddit] legacy {label} failed: {exc}", file=sys.stderr)
            return

        kept = 0
        for child in payload.get("data", {}).get("children", []):
            item = child.get("data") or {}
            identity = str(item.get("id") or item.get("permalink") or item.get("url") or "")
            item_url = str(item.get("url") or item.get("permalink") or "")
            if _reddit_url_is_noise(item_url):
                continue
            if not identity or identity in seen:
                continue
            keep, relevance = _reddit_relevance(item, aliases, tokens)
            if not keep:
                continue
            item["_rank_signal"] = relevance
            lane_items.append(item)
            seen.add(identity)
            kept += 1
            if len(lane_items) >= max_results:
                break
        print(f"[reddit] legacy {label} → {kept} kept results", file=sys.stderr)

    for query in queries[:3]:
        if len(lane_items) >= max_results:
            break
        url = "https://www.reddit.com/search.json?" + urllib.parse.urlencode(
            {
                "q": query,
                "sort": "top",
                "t": "month",
                "limit": str(base_limit),
            }
        )
        collect(url, f"search '{query}'")

    subreddit_queries = queries[:2] or [(plan.get("canonical_topic") or topic or "").strip()]
    for subreddit in (plan.get("subreddits") or [])[:2]:
        if len(lane_items) >= max_results:
            break
        sub = str(subreddit).strip().replace("r/", "")
        if not sub:
            continue
        for query in subreddit_queries[:2]:
            if len(lane_items) >= max_results:
                break
            url = f"https://www.reddit.com/r/{sub}/search.json?" + urllib.parse.urlencode(
                {
                    "q": query,
                    "restrict_sr": "1",
                    "sort": "top",
                    "t": "month",
                    "limit": str(base_limit),
                }
            )
            collect(url, f"r/{sub} '{query}'")

    if not lane_items:
        if blocked_codes and len(blocked_codes) == attempt_count:
            code_list = ", ".join(str(code) for code in sorted(set(blocked_codes)))
            return [], lane_report(
                "soft-skipped",
                note=f"legacy Reddit JSON blocked ({code_list})",
                queries=queries,
                attempts=attempt_count,
                blocked_codes=sorted(set(blocked_codes)),
                subreddits=(plan.get("subreddits") or [])[:2],
                route="legacy-json",
            )

        return [], lane_report(
            "soft-skipped",
            note="legacy Reddit JSON returned no topical matches",
            queries=queries,
            attempts=attempt_count,
            subreddits=(plan.get("subreddits") or [])[:2],
            route="legacy-json",
        )

    lane_items.sort(key=lambda item: (float(item.get("_rank_signal") or 0.0), int(item.get("score") or 0), int(item.get("num_comments") or 0)), reverse=True)
    return lane_items[:max_results], lane_report(
        "ok",
        count=len(lane_items[:max_results]),
        note="legacy Reddit JSON lane active",
        queries=queries,
        attempts=attempt_count,
        subreddits=(plan.get("subreddits") or [])[:2],
        route="legacy-json",
    )


def search_reddit(topic: str, plan: dict, api_key: str, max_results: int = 8) -> tuple[list[dict], dict]:
    queries = _reddit_queries(topic, plan)
    if not queries:
        print("[reddit] skipped, no queries available", file=sys.stderr)
        return [], lane_report("skipped", note="no queries available", queries=[])

    aliases = _topic_aliases(topic, plan)
    tokens = _topic_tokens(topic, plan)
    subreddits = [str(sub).strip().replace("r/", "") for sub in (plan.get("subreddits") or [])[:2] if str(sub).strip()]
    seen: set[str] = set()
    lane_items: list[dict] = []
    attempt_count = 0

    search_specs: list[tuple[str, str]] = []
    for query in queries[:3]:
        search_specs.append((f'site:reddit.com "{query}"', f'site:reddit {query}'))
        for subreddit in subreddits:
            search_specs.append((f'site:reddit.com/r/{subreddit} "{query}"', f'r/{subreddit} {query}'))

    deduped_specs: list[tuple[str, str]] = []
    seen_specs: set[str] = set()
    for search_query, label in search_specs:
        if search_query in seen_specs:
            continue
        deduped_specs.append((search_query, label))
        seen_specs.add(search_query)

    if api_key:
        for search_query, label in deduped_specs[:6]:
            attempt_count += 1
            results = search_tavily(search_query, api_key, max_results=max(4, min(max_results, 6)))
            kept = 0
            for raw in results:
                url = str(raw.get("url") or "")
                domain = _domain_from_url(url)
                if "reddit.com" not in domain or url in seen or _reddit_url_is_noise(url):
                    continue
                title = str(raw.get("title") or "")
                snippet = str(raw.get("description") or raw.get("content") or "")[:800]
                match = _topic_match_metrics(" ".join([title, url]), snippet, aliases, tokens)
                if not _passes_topic_gate(match, lane="reddit", domain=domain):
                    continue

                item = _reddit_item_from_tavily(raw)
                item["_rank_signal"] = _topic_rank_signal(raw.get("score", 0.5), match, lane="reddit", domain=domain)
                lane_items.append(item)
                seen.add(url)
                kept += 1
            print(f"[reddit] {label} via Tavily → {kept} kept results", file=sys.stderr)

        if lane_items:
            lane_items.sort(
                key=lambda item: (
                    float(item.get("_rank_signal") or 0.0),
                    str(item.get("published_date") or ""),
                    item.get("title") or "",
                ),
                reverse=True,
            )
            return lane_items[:max_results], lane_report(
                "ok",
                count=len(lane_items[:max_results]),
                note="Reddit lane via Tavily site:reddit.com",
                queries=queries,
                attempts=attempt_count,
                subreddits=[f"r/{sub}" for sub in subreddits],
                route="tavily-site-reddit",
            )

    legacy_items, legacy_report = _search_reddit_json_legacy(topic, plan, max_results=max_results)
    if legacy_items:
        return legacy_items, legacy_report

    note = "Reddit lane found no topical matches via Tavily site:reddit.com"
    if legacy_report.get("note"):
        note = f"{note}; {legacy_report['note']}"
    return [], lane_report(
        "soft-skipped",
        note=note,
        queries=queries,
        attempts=attempt_count + int(legacy_report.get("attempts") or 0),
        subreddits=[f"r/{sub}" for sub in subreddits],
        route="tavily-site-reddit",
        fallback=legacy_report,
    )


# ---------------------------------------------------------------------------
# GitHub lane
# ---------------------------------------------------------------------------

def _gh_available() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        return False, "gh CLI not installed"
    except subprocess.TimeoutExpired:
        return False, "gh auth status timed out"

    detail = (result.stderr or result.stdout or "").strip()
    if result.returncode != 0:
        return False, detail or "gh auth unavailable"
    return True, detail


def _gh_api_json(endpoint: str, **params: str) -> dict:
    cmd = ["gh", "api", "--method", "GET", endpoint]
    for key, value in params.items():
        cmd.extend(["-f", f"{key}={value}"])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "gh api failed").strip())
    return json.loads(result.stdout or "{}")


def search_hn(topic: str, plan: dict, max_results: int = 8) -> tuple[list[dict], dict]:
    aliases = _topic_aliases(topic, plan)
    tokens = _topic_tokens(topic, plan)
    queries = list((plan.get("queries") or {}).get("hackernews", [])[:2])
    if not queries:
        canonical = (plan.get("canonical_topic") or topic or "").strip()
        if canonical:
            queries = [canonical]
    if not queries:
        print("[hn] skipped, no queries available", file=sys.stderr)
        return [], lane_report("skipped", note="no queries available", queries=[])

    seen: set[str] = set()
    kept_items: list[dict] = []
    attempts = 0
    for query in queries[:2]:
        attempts += 1
        url = "https://hn.algolia.com/api/v1/search_by_date?" + urllib.parse.urlencode(
            {
                "query": query,
                "tags": "story",
                "hitsPerPage": str(max(6, min(max_results * 2, 20))),
            }
        )
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                payload = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            print(f"[hn] query '{query}' failed: HTTP {exc.code}", file=sys.stderr)
            continue
        except Exception as exc:
            print(f"[hn] query '{query}' failed: {exc}", file=sys.stderr)
            continue

        local_kept = 0
        for raw in payload.get("hits", []):
            identity = str(raw.get("objectID") or raw.get("url") or raw.get("story_url") or "")
            if not identity or identity in seen:
                continue
            item_url = str(raw.get("url") or raw.get("story_url") or f"https://news.ycombinator.com/item?id={raw.get('objectID','')}")
            title = str(raw.get("title") or raw.get("story_title") or "")
            snippet = str(raw.get("story_text") or raw.get("comment_text") or "")[:700]
            domain = _domain_from_url(item_url)
            match = _topic_match_metrics(" ".join([title, item_url]), snippet, aliases, tokens)
            if not _passes_topic_gate(match, lane="hn", domain=domain):
                continue
            item = dict(raw)
            item["url"] = item_url
            item["title"] = title
            item["_rank_signal"] = _topic_rank_signal(0.52, match, lane="hn", domain=domain)
            kept_items.append(item)
            seen.add(identity)
            local_kept += 1
            if len(kept_items) >= max_results:
                break
        print(f"[hn] query '{query}' → {local_kept} kept results", file=sys.stderr)
        if len(kept_items) >= max_results:
            break

    if not kept_items:
        return [], lane_report(
            "soft-skipped",
            note="HN returned no topical matches",
            queries=queries,
            attempts=attempts,
            route="algolia-public",
        )

    kept_items.sort(
        key=lambda item: (
            float(item.get("_rank_signal") or 0.0),
            str(item.get("created_at") or ""),
            str(item.get("title") or ""),
        ),
        reverse=True,
    )
    return kept_items[:max_results], lane_report(
        "ok",
        count=len(kept_items[:max_results]),
        note="HN lane via public Algolia search",
        queries=queries,
        attempts=attempts,
        route="algolia-public",
    )


def _topic_aliases(topic: str, plan: dict) -> set[str]:
    aliases: set[str] = set()
    for candidate in [topic, plan.get("canonical_topic")]:
        clean = " ".join(str(candidate or "").split()).strip().lower()
        if clean:
            aliases.add(clean)
    for handle in (plan.get("handles") or {}).values():
        clean = str(handle or "").strip().lower().lstrip("@")
        if clean:
            aliases.add(clean)
    return aliases


def _topic_tokens(topic: str, plan: dict) -> set[str]:
    canonical = " ".join(
        part for part in [str(plan.get("canonical_topic") or "").strip(), str(topic or "").strip()] if part
    )
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9]+", canonical)
        if len(token) >= 3
    }


def _distinctive_topic_tokens(tokens: set[str]) -> set[str]:
    distinctive = {
        token for token in tokens
        if len(token) >= 4 and token not in GENERIC_TOPIC_TOKENS
    }
    return distinctive or {token for token in tokens if len(token) >= 4} or tokens


def _domain_from_url(url: str) -> str:
    netloc = urllib.parse.urlsplit(url or "").netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def _topic_match_metrics(primary_text: str, secondary_text: str, aliases: set[str], tokens: set[str]) -> dict:
    primary = " ".join(primary_text.split()).lower()
    secondary = " ".join(secondary_text.split()).lower()
    distinctive_tokens = _distinctive_topic_tokens(tokens)

    alias_hits_primary = {alias for alias in aliases if alias and alias in primary}
    alias_hits_secondary = {alias for alias in aliases if alias and alias in secondary}
    token_hits_primary = {token for token in tokens if re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", primary)}
    token_hits_secondary = {token for token in tokens if token not in token_hits_primary and re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", secondary)}
    all_hits = token_hits_primary | token_hits_secondary
    distinctive_hits = {token for token in distinctive_tokens if token in all_hits}

    token_count = len(tokens)
    if token_count >= 4:
        required_hits = 3
    elif token_count >= 2:
        required_hits = 2
    else:
        required_hits = 1

    return {
        "exact_alias": bool(alias_hits_primary),
        "alias_hits_primary": alias_hits_primary,
        "alias_hits_secondary": alias_hits_secondary,
        "token_hits_primary": token_hits_primary,
        "token_hits_secondary": token_hits_secondary,
        "all_hits": all_hits,
        "primary_hit_count": len(token_hits_primary),
        "coverage": len(all_hits) / max(1, token_count),
        "primary_coverage": len(token_hits_primary) / max(1, token_count),
        "distinctive_tokens": distinctive_tokens,
        "distinctive_hits": distinctive_hits,
        "distinctive_hit_count": len(distinctive_hits),
        "required_hits": required_hits,
    }


def _passes_topic_gate(match: dict, *, lane: str, domain: str = "") -> bool:
    if match["exact_alias"]:
        return True

    total_hits = len(match["all_hits"])
    primary_hits = match["primary_hit_count"]
    required_hits = match["required_hits"]
    distinctive_hits = match["distinctive_hit_count"]
    coverage = match["coverage"]

    if lane == "github":
        return (
            total_hits >= required_hits
            or (primary_hits >= 1 and distinctive_hits >= 1 and coverage >= 0.5)
        )

    if lane == "reddit":
        if domain and "reddit.com" not in domain:
            return False
        return (
            primary_hits >= required_hits
            or (total_hits >= required_hits and distinctive_hits >= 1)
            or coverage >= 0.8
        )

    # Tavily: require stronger topical signal — coverage alone is insufficient
    # to block tangential X posts or vaguely related web results.
    if lane == "tavily":
        if domain in SOCIAL_NOISE_DOMAINS:
            return primary_hits >= required_hits and distinctive_hits >= 1
        return (
            primary_hits >= required_hits
            or (primary_hits >= 1 and distinctive_hits >= 2 and coverage >= 0.5)
        )

    if domain in SOCIAL_NOISE_DOMAINS:
        return primary_hits >= required_hits and distinctive_hits >= 1

    return (
        primary_hits >= required_hits
        or coverage >= 0.75
        or (primary_hits >= 1 and distinctive_hits >= 1 and coverage >= 0.5)
    )


def _topic_rank_signal(base_score: float, match: dict, *, lane: str, domain: str = "") -> float:
    base = max(0.0, min(1.0, float(base_score or 0.0)))
    coverage = match["coverage"]
    primary_coverage = match["primary_coverage"]
    distinctive_ratio = match["distinctive_hit_count"] / max(1, len(match["distinctive_tokens"]))
    alias_bonus = 0.18 if match["exact_alias"] else 0.0

    signal = (
        base * 0.44
        + coverage * 0.24
        + primary_coverage * 0.16
        + distinctive_ratio * 0.10
        + alias_bonus
    )

    if lane == "reddit":
        signal += 0.04
    if lane == "github" and coverage >= 0.8:
        signal += 0.03
    if domain in SOCIAL_NOISE_DOMAINS and not match["exact_alias"]:
        signal -= 0.10

    return max(0.18, min(0.95, signal))


def _filter_tavily_results(results: list[dict], topic: str, plan: dict, *, max_results: int) -> list[dict]:
    aliases = _topic_aliases(topic, plan)
    tokens = _topic_tokens(topic, plan)
    filtered: list[dict] = []
    seen: set[str] = set()

    for raw in results:
        url = str(raw.get("url") or "")
        if not url or url in seen:
            continue
        title = str(raw.get("title") or "")
        snippet = str(raw.get("description") or raw.get("content") or "")[:800]
        domain = _domain_from_url(url)
        match = _topic_match_metrics(" ".join([title, url]), snippet, aliases, tokens)
        if domain in SOCIAL_NOISE_DOMAINS:
            social_text = f"{title} {snippet}".lower()
            if any(phrase in social_text for phrase in SOCIAL_NOISE_PHRASES) and not match["exact_alias"]:
                continue
        if not _passes_topic_gate(match, lane="tavily", domain=domain):
            continue

        item = dict(raw)
        item["_rank_signal"] = _topic_rank_signal(raw.get("score", 0.5), match, lane="tavily", domain=domain)
        filtered.append(item)
        seen.add(url)
        if len(filtered) >= max_results:
            break

    return filtered


def _github_relevance(item: dict, aliases: set[str], tokens: set[str]) -> tuple[bool, float]:
    title = item.get("title") or item.get("full_name") or item.get("name") or ""
    repo_name = item.get("full_name") or item.get("repository_full_name") or ""
    url = item.get("html_url") or ""
    snippet = (item.get("body") or item.get("description") or "")[:500]

    match = _topic_match_metrics(
        " ".join(part for part in [title, repo_name, url] if part),
        snippet,
        aliases,
        tokens,
    )
    keep = _passes_topic_gate(match, lane="github", domain=_domain_from_url(url))
    strength = _topic_rank_signal(0.56, match, lane="github", domain=_domain_from_url(url))
    return keep, min(0.82, strength)


def search_github(topic: str, plan: dict, max_results: int = 8) -> tuple[list[dict], dict]:
    available, detail = _gh_available()
    if not available:
        print(f"[github] skipped, {detail}", file=sys.stderr)
        return [], lane_report("skipped", note=detail)

    since = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
    handles = plan.get("handles", {}) or {}
    github_handle = (handles.get("github") or "").lstrip("@")
    canonical_topic = plan.get("canonical_topic") or topic
    aliases = _topic_aliases(topic, plan)
    tokens = _topic_tokens(topic, plan)

    repo_query = f'user:{github_handle} pushed:>={since}' if github_handle else f'"{canonical_topic}" pushed:>={since}'
    issue_query = f'author:{github_handle} updated:>={since}' if github_handle else f'"{canonical_topic}" updated:>={since}'

    lane_items: list[dict] = []

    try:
        repo_payload = _gh_api_json(
            "/search/repositories",
            q=repo_query,
            sort="updated",
            order="desc",
            per_page=str(max(3, min(max_results, 10))),
        )
        kept = 0
        for idx, item in enumerate(repo_payload.get("items", [])[:max_results]):
            keep, relevance = _github_relevance(item, aliases, tokens)
            if not keep:
                continue
            item["_kind"] = "repo"
            item["_rank_signal"] = max(0.24, min(0.68, relevance - (idx * 0.05)))
            lane_items.append(item)
            kept += 1
        print(f"[github] repositories query → {kept} kept results", file=sys.stderr)
    except Exception as exc:
        print(f"[github] repositories failed: {exc}", file=sys.stderr)

    try:
        issue_payload = _gh_api_json(
            "/search/issues",
            q=issue_query,
            sort="updated",
            order="desc",
            per_page=str(max(3, min(max_results, 10))),
        )
        kept = 0
        for idx, item in enumerate(issue_payload.get("items", [])[:max_results]):
            keep, relevance = _github_relevance(item, aliases, tokens)
            if not keep:
                continue
            repo_url = item.get("repository_url", "")
            repo_name = repo_url.split("/repos/")[-1] if "/repos/" in repo_url else ""
            item["_kind"] = "pr" if item.get("pull_request") else "issue"
            item["repository_full_name"] = repo_name
            item["_rank_signal"] = max(0.28, min(0.76, relevance - (idx * 0.04)))
            lane_items.append(item)
            kept += 1
        print(f"[github] issues/prs query → {kept} kept results", file=sys.stderr)
    except Exception as exc:
        print(f"[github] issues/prs failed: {exc}", file=sys.stderr)

    status = "ok" if lane_items else "soft-skipped"
    note = "gh CLI lane active" if lane_items else "no relevant GitHub results kept"
    return lane_items, lane_report(status, count=len(lane_items), note=note)


# ---------------------------------------------------------------------------
# LLM synthesis
# ---------------------------------------------------------------------------

def _display_quality_score(item: ResearchItem, ranking_profile: RankingProfile) -> float:
    score = float(item.final_score)
    url = (item.canonical_url or item.url or "").lower()
    score += max(-0.08, min(0.08, (item.claim_confidence_score - 0.5) * 0.20))
    if item.cluster_size > 1:
        score += 0.03
    if item.published_date:
        score += 0.02
    if item.authority_tier == "reference":
        score += 0.05
    elif item.authority_tier == "official":
        score += 0.04
    elif item.authority_tier == "community" and ranking_profile.name in {"person-balanced", "general-balanced"}:
        score -= 0.05
    elif item.authority_tier == "social":
        score -= 0.04
    elif item.authority_tier == "weak-web":
        score -= 0.07

    if item.result_type == "article":
        score += 0.04
    elif item.result_type == "social-post":
        score -= 0.08
    elif item.result_type in {"listing", "profile", "homepage"}:
        score -= 0.10
    elif item.result_type == "discussion" and ranking_profile.name == "person-balanced":
        score -= 0.05

    if item.source == "reddit" and not item.published_date:
        score -= 0.18
    if item.source == "reddit" and item.cluster_size <= 1:
        score -= 0.04
    if item.source == "hn" and not item.published_date:
        score -= 0.03
    if item.source == "github" and ranking_profile.name in {"person-balanced", "general-balanced"}:
        score -= 0.02
    if any(domain in url for domain in SOCIAL_NOISE_DOMAINS):
        score -= 0.08
    return score


def _select_featured_items(items: list[ResearchItem], ranking_profile: RankingProfile, limit: int = 15) -> list[ResearchItem]:
    if not items:
        return []
    source_caps = {"tavily": 3, "reddit": 2, "hn": 2, "github": 2}
    if ranking_profile.name == "person-balanced":
        source_caps = {"tavily": 3, "reddit": 1, "hn": 2, "github": 1}
    elif ranking_profile.name == "general-balanced":
        source_caps = {"tavily": 3, "reddit": 2, "hn": 2, "github": 1}
    elif ranking_profile.name == "repo-centric":
        source_caps = {"tavily": 2, "reddit": 1, "hn": 1, "github": 4}

    ordered = sorted(items, key=lambda it: (_display_quality_score(it, ranking_profile), it.final_score), reverse=True)
    chosen: list[ResearchItem] = []
    source_counts: dict[str, int] = {}
    reddit_sub_counts: dict[str, int] = {}

    for item in ordered:
        if len(chosen) >= limit:
            break
        source = item.source
        if source_counts.get(source, 0) >= source_caps.get(source, limit):
            continue
        if source == "reddit":
            sub = item.source_sub or "reddit"
            if reddit_sub_counts.get(sub, 0) >= 1 and ranking_profile.name in {"person-balanced", "general-balanced"}:
                continue
        chosen.append(item)
        source_counts[source] = source_counts.get(source, 0) + 1
        if source == "reddit":
            sub = item.source_sub or "reddit"
            reddit_sub_counts[sub] = reddit_sub_counts.get(sub, 0) + 1

    if not chosen:
        return ordered[:limit]
    return chosen


def synthesize(items: list[ResearchItem], topic: str, ranking_profile: RankingProfile) -> str:
    if not items:
        return "- No results found in the current run.\n- Next move: broaden the topic or add source-specific queries."

    featured = _select_featured_items(items, ranking_profile, limit=12)
    lines = []
    for i, it in enumerate(featured[:20], 1):
        eng = it.engagement
        cluster_note = ""
        if it.cluster_size > 1:
            cluster_note = f" | cluster {it.cluster_size} across {', '.join(it.cluster_sources)}"
        lines.append(
            f"{i}. [{it.source.upper()}] {it.title}\n"
            f"   URL: {it.url}\n"
            f"   Date: {it.published_date or 'n/a'}  Score: {it.final_score:.3f}  Trust: {it.source_trust_score:.2f}  Claim confidence: {it.claim_confidence_label}{cluster_note}\n"
            f"   Engagement: upvotes={eng.upvotes}, comments={eng.comments}, shares={eng.shares}\n"
            f"   Snippet: {it.snippet[:200]}"
        )
    table = "\n".join(lines)

    prompt = textwrap.dedent(f"""\
    You are a research analyst. Write a tight, factual research brief for the topic below.

    Rules:
    - Do NOT make up facts. Stick to what's in the items.
    - Use bullet points. No headers beyond the ones given.
    - Highlight engagement signals where available.
    - Distinguish clearly between weakly supported claims and cross-source corroborated claims.
    - If a finding represents a cluster, mention that it was corroborated across multiple items or sources.
    - End with a "Key Takeaways" section (3-5 bullets).
    - Keep the total brief under 600 words.

    Topic: {topic}

    Top findings (already deduped and clustered):
    {table}
    """).strip()

    text, backend = chat_complete(
        [{"role": "user", "content": prompt}],
        max_tokens=1200,
        temperature=0.3,
        timeout=120,
    )
    if not text:
        return deterministic_synthesis(items, topic, ranking_profile)
    print(f"[synthesis] backend → {backend}", file=sys.stderr)
    return text


def deterministic_synthesis(items: list[ResearchItem], topic: str, ranking_profile: RankingProfile) -> str:
    top = _select_featured_items(items, ranking_profile, limit=6)
    domains: list[str] = []
    by_source: dict[str, int] = {}
    corroborated = 0
    lines: list[str] = []

    for it in top:
        by_source[it.source] = by_source.get(it.source, 0) + 1
        if it.cluster_size > 1:
            corroborated += 1
        match = re.search(r"https?://([^/]+)", it.url)
        if match:
            domain = match.group(1).replace("www.", "")
            if domain not in domains:
                domains.append(domain)

    lines.append("### Overview")
    if top:
        lines.append(f"- Highest-ranked finding: {top[0].title} ({top[0].source}, score {top[0].final_score:.3f})")
    if by_source:
        mix = ", ".join(f"{src} {count}" for src, count in sorted(by_source.items(), key=lambda pair: (-pair[1], pair[0])))
        lines.append(f"- Source mix across top findings: {mix}")
    if corroborated:
        lines.append(f"- {corroborated} top findings were corroborated by merged duplicates or cross-source clusters.")

    lines.append("")
    lines.append("### Momentum Signals")
    for it in top[:4]:
        eng = it.engagement
        signal_bits = []
        if eng.upvotes:
            signal_bits.append(f"{eng.upvotes}↑")
        if eng.comments:
            signal_bits.append(f"{eng.comments} comments")
        if eng.shares:
            signal_bits.append(f"{eng.shares} shares")
        if it.cluster_size > 1:
            signal_bits.append(f"cluster {it.cluster_size}")
        signal_text = f" | {'; '.join(signal_bits)}" if signal_bits else ""
        lines.append(
            f"- [{it.source.upper()}] {it.title} ({it.published_date or 'n/d'}, score {it.final_score:.3f}){signal_text}"
        )

    lines.append("")
    lines.append("### Key Takeaways")
    if top:
        lines.append(f"- The run is currently anchored by {top[0].source} evidence, but the ranking already blends source-specific adjustments before sorting.")
    if domains:
        lines.append(f"- Main domains surfaced: {', '.join(domains[:5])}")
    if any(it.source == "reddit" for it in top):
        lines.append("- Reddit added community discussion signals, which helps separate live conversation from static reference pages.")
    lines.append("- This brief used deterministic fallback synthesis because no live model backend responded for synthesis.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def render(
    topic: str,
    plan: dict,
    items: list[ResearchItem],
    synthesis: str,
    ranking_profile: RankingProfile,
    slug: str,
    save_dir: Path,
    raw_counts: dict[str, int],
    lane_reports: dict[str, dict],
) -> str:
    top_score = f"{items[0].final_score:.3f}" if items else "?"

    source_counts: dict[str, int] = {}
    for it in items:
        for source in it.cluster_sources or [it.source]:
            source_counts[source] = source_counts.get(source, 0) + 1

    stats_lines = [
        f"- **{src.upper()}**: {n} deduped findings"
        for src, n in sorted(source_counts.items(), key=lambda pair: (-pair[1], pair[0]))
    ] or ["- No sources found"]

    featured_items = _select_featured_items(items, ranking_profile, limit=15)
    findings_lines = []
    for it in featured_items:
        eng = it.engagement
        meta_bits = [
            it.published_date or "n/d",
            f"score {it.final_score:.3f}",
            f"trust {it.source_trust_score:.2f}",
            f"claim {it.claim_confidence_label}",
        ]
        blend_penalty = float((it.score_breakdown.get("adjustments") or {}).get("source_repeat_penalty", 0.0) or 0.0)
        if blend_penalty:
            meta_bits.append(f"blend -{blend_penalty:.2f}")
        if eng.upvotes:
            meta_bits.append(f"{eng.upvotes}↑")
        if eng.comments:
            meta_bits.append(f"{eng.comments} comments")
        if it.cluster_size > 1:
            meta_bits.append(f"cluster {it.cluster_size}")
        cluster_note = ""
        if it.cluster_size > 1:
            reasons = ", ".join(it.cluster_reasons) or "similarity"
            cluster_note = f"\n  Cluster sources: {', '.join(it.cluster_sources)} | reasons: {reasons}"
        findings_lines.append(
            f"- **{it.title}** [{it.source}{it.source_sub and f'/{it.source_sub}'}]\n"
            f"  {' | '.join(meta_bits)}\n"
            f"  {it.url}{cluster_note}\n"
            f"  {it.snippet[:200]}"
        )

    handles = []
    for platform, handle in (plan.get("handles") or {}).items():
        if not handle:
            continue
        handles.append(handle if str(handle).startswith("@") else f"{platform}:{handle}")

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ranking_bits = [
        f"- **Profile:** {ranking_profile.name}",
        f"- **Why:** {'; '.join(ranking_profile.reasons) or 'balanced default'}",
        "- **Source multipliers:** " + ", ".join(
            f"{src} ×{value:.2f}" for src, value in sorted(ranking_profile.source_multipliers.items())
        ),
        "- **Source bonuses:** " + ", ".join(
            f"{src} {value:+.2f}" for src, value in sorted(ranking_profile.source_bonuses.items())
        ),
        "- **Source repeat penalties:** " + ", ".join(
            f"{src} -{value:.2f} per extra result" for src, value in sorted(ranking_profile.source_repeat_penalties.items())
        ),
    ]
    lane_bits = []
    for lane in ["tavily", "reddit", "hn", "github"]:
        report = lane_reports.get(lane, {})
        status = report.get("status", "unknown")
        count = report.get("count", raw_counts.get(lane, 0))
        note = report.get("note", "")
        extras = []
        if report.get("attempts"):
            extras.append(f"attempts {report['attempts']}")
        if note:
            extras.append(str(note))
        lane_bits.append(
            f"- **{lane.upper()}**: {status} ({count} items)" + (f" | {'; '.join(extras)}" if extras else "")
        )

    out = "\n".join([
        f"# Research Brief: {topic}",
        "",
        f"**Generated:** {date_str}",
        f"**Topic type:** {plan.get('type', '?')} | **Confidence:** {plan.get('confidence', '?')}",
        f"**Raw inputs:** Tavily {raw_counts.get('tavily', 0)} + Reddit {raw_counts.get('reddit', 0)} + HN {raw_counts.get('hn', 0)} + GitHub {raw_counts.get('github', 0)}",
        f"**Deduped findings:** {len(items)} | **Top score:** {top_score}",
        "",
        "## Source Breakdown",
        *(stats_lines or ["- No sources found"]),
        "",
        "## Resolved Query Plan",
        f"- **Resolver backend:** {plan.get('resolver_backend', 'unknown')}",
        f"- **Intent mode:** {plan.get('intent_mode', 'unknown')}",
        f"- **Handles:** {', '.join(handles) or 'none'}",
        f"- **Subreddits:** {', '.join(plan.get('subreddits', []) or ['none'])}",
        f"- **Reddit queries:** {', '.join(plan.get('queries', {}).get('reddit', []) or ['none'])}",
        f"- **Web queries:** {', '.join(plan.get('queries', {}).get('web', []) or ['none'])}",
        "",
        "## Lane Status",
        *lane_bits,
        "",
        "## Ranking Blend",
        *ranking_bits,
        "",
        "## Top Findings",
        *(findings_lines or ["- No findings"]),
        "",
        "## Synthesis",
        synthesis,
        "",
        "---",
        f"*Auto-saved to {save_dir}/{slug}.md*",
    ]).strip()

    save_dir.mkdir(parents=True, exist_ok=True)
    out_path = save_dir / f"{slug}.md"
    out_path.write_text(out)
    print(f"[saved] {out_path}", file=sys.stderr)

    json_path = save_dir / f"{slug}.json"
    json_path.write_text(json.dumps({
        "topic": topic,
        "date": date_str,
        "plan": plan,
        "ranking_profile": ranking_profile_to_dict(ranking_profile),
        "raw_counts": raw_counts,
        "lane_reports": lane_reports,
        "items": [scored_to_dict(it) for it in items],
        "synthesis": synthesis,
    }, indent=2))
    print(f"[saved] {json_path}", file=sys.stderr)

    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(topic: str, save_dir: Path = SAVE_DIR, max_items: int = 20) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", topic.strip()).lower().strip("-")
    run_dir = CACHE_DIR / slug
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Researching: {topic}", file=sys.stderr)

    plan = resolve(topic, save_dir=run_dir)
    print("[+] resolver done", file=sys.stderr)
    ranking_profile = build_ranking_profile(topic, plan)
    print(f"[ranking] profile → {ranking_profile.name}", file=sys.stderr)

    tavily_key = os.environ.get("TAVILY_API_KEY", "")
    if not tavily_key:
        cfg = CONFIG_DIR / "tavily.json"
        if cfg.exists():
            tavily_key = json.loads(cfg.read_text()).get("api_key", "")

    web_queries = (plan.get("queries") or {}).get("web", [])[:3]
    raw_lanes: dict[str, list[dict]] = {"tavily": [], "reddit": [], "hn": [], "github": []}
    lane_reports: dict[str, dict] = {
        "tavily": lane_report("pending", count=0, note="awaiting Tavily queries", queries=web_queries),
        "reddit": lane_report("pending", count=0, note="awaiting Reddit community search"),
        "hn": lane_report("pending", count=0, note="awaiting HN community search"),
        "github": lane_report("pending", count=0, note="awaiting gh CLI lane"),
    }

    with ThreadPoolExecutor(max_workers=max(3, len(web_queries) + 2)) as pool:
        futures = {}
        for query in web_queries:
            futures[pool.submit(search_tavily, query, tavily_key, max(6, max_items))] = ("tavily", query)
        futures[pool.submit(search_reddit, topic, plan, tavily_key, max(6, max_items))] = ("reddit", "lane")
        futures[pool.submit(search_hn, topic, plan, max(6, max_items))] = ("hn", "lane")
        futures[pool.submit(search_github, topic, plan, max(6, max_items))] = ("github", "lane")

        for future in as_completed(futures):
            lane, label = futures[future]
            try:
                results = future.result()
            except Exception as exc:
                print(f"[{lane}] failed for {label}: {exc}", file=sys.stderr)
                results = [] if lane == "tavily" else ([], lane_report("soft-skipped", note=str(exc)))

            if lane == "tavily":
                filtered_results = _filter_tavily_results(results, topic, plan, max_results=max(6, max_items))
                print(
                    f"[+] tavily '{label}' → {len(filtered_results)} topical results (from {len(results)} raw)",
                    file=sys.stderr,
                )
                raw_lanes["tavily"].extend(filtered_results)
            elif lane == "reddit":
                lane_items, report = results
                print(f"[+] reddit lane → {len(lane_items)} results ({report.get('status')})", file=sys.stderr)
                raw_lanes["reddit"].extend(lane_items)
                lane_reports["reddit"] = report
            elif lane == "hn":
                lane_items, report = results
                print(f"[+] hn lane → {len(lane_items)} results ({report.get('status')})", file=sys.stderr)
                raw_lanes["hn"].extend(lane_items)
                lane_reports["hn"] = report
            else:
                lane_items, report = results
                print(f"[+] github lane → {len(lane_items)} results ({report.get('status')})", file=sys.stderr)
                raw_lanes["github"].extend(lane_items)
                lane_reports["github"] = report

    if not tavily_key:
        lane_reports["tavily"] = lane_report("skipped", count=0, note="no API key available", queries=web_queries)
    elif raw_lanes["tavily"]:
        lane_reports["tavily"] = lane_report(
            "ok",
            count=len(raw_lanes["tavily"]),
            note="parallel Tavily web queries with topical filtering",
            queries=web_queries,
        )
    else:
        lane_reports["tavily"] = lane_report(
            "soft-skipped",
            count=0,
            note="queries returned no topical results",
            queries=web_queries,
        )

    save_json(run_dir / "tavily_raw.json", raw_lanes["tavily"])
    save_json(run_dir / "reddit_raw.json", raw_lanes["reddit"])
    save_json(run_dir / "hn_raw.json", raw_lanes["hn"])
    save_json(run_dir / "github_raw.json", raw_lanes["github"])
    save_json(run_dir / "lane_reports.json", lane_reports)

    normalized_items: list[ResearchItem] = []
    if raw_lanes["tavily"]:
        normalized_items.extend(normalize_batch(raw_lanes["tavily"], source="tavily", ranking_profile=ranking_profile))
    if raw_lanes["reddit"]:
        normalized_items.extend(normalize_batch(raw_lanes["reddit"], source="reddit", ranking_profile=ranking_profile))
    if raw_lanes["hn"]:
        normalized_items.extend(normalize_batch(raw_lanes["hn"], source="hn", ranking_profile=ranking_profile))
    if raw_lanes["github"]:
        normalized_items.extend(normalize_batch(raw_lanes["github"], source="github", ranking_profile=ranking_profile))

    print(f"[+] {len(normalized_items)} normalized items before clustering", file=sys.stderr)
    deduped_items = cluster_items(normalized_items)
    print(f"[+] {len(deduped_items)} items after clustering/dedupe", file=sys.stderr)
    deduped_items = apply_source_blend(deduped_items, ranking_profile=ranking_profile)
    print(f"[+] {len(deduped_items)} items after source blending", file=sys.stderr)

    save_json(run_dir / "items_deduped.json", [asdict(item) for item in deduped_items])

    synthesis = synthesize(deduped_items[:max_items], topic, ranking_profile)
    print("[+] synthesis done", file=sys.stderr)

    brief = render(
        topic=topic,
        plan=plan,
        items=deduped_items[:max_items],
        synthesis=synthesis,
        ranking_profile=ranking_profile,
        slug=slug,
        save_dir=save_dir,
        raw_counts={lane: len(items) for lane, items in raw_lanes.items()},
        lane_reports=lane_reports,
    )
    return brief


def main() -> None:
    args = sys.argv[1:]
    save_dir = SAVE_DIR
    max_items = 20
    topic = ""
    i = 0
    while i < len(args):
        if args[i] == "--save-dir" and i + 1 < len(args):
            save_dir = Path(args[i + 1])
            i += 2
        elif args[i] == "--max-items" and i + 1 < len(args):
            max_items = int(args[i + 1])
            i += 2
        elif not args[i].startswith("--"):
            topic = args[i]
            i += 1
        else:
            i += 1

    if not topic:
        print("Usage: nasr_research.py <topic> [--save-dir DIR] [--max-items N]", file=sys.stderr)
        raise SystemExit(1)

    print(run(topic, save_dir, max_items))


if __name__ == "__main__":
    main()
