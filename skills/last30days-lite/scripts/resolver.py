#!/usr/bin/env python3
"""
resolver.py — Pre-research query planner.

Prefers the local OpenClaw gateway for structured planning. If no live model path
works, falls back to a deterministic planner that is stronger than the previous
single-query generic fallback.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional

from llm_utils import chat_complete, extract_json_object

SKILL_ROOT = Path(__file__).parent.parent.resolve()
CACHE_DIR = Path.home() / ".cache" / "nasr-research"

PERSON_CODE_HINTS = {
    "developer", "engineer", "founder", "builder", "programmer", "open source",
    "github", "repo", "repository", "sdk", "api", "cli", "tool", "tooling",
    "framework", "library", "package", "python", "javascript", "typescript",
    "swift", "ios", "android", "llm", "ai",
}
PRODUCT_HINTS = {
    "tool", "platform", "app", "sdk", "api", "framework", "library", "package",
    "model", "assistant", "agent", "workflow", "plugin", "extension", "startup",
}
AI_HINTS = {"ai", "llm", "agent", "agents", "model", "models", "openai", "anthropic", "gemini"}
DEFAULT_SUBREDDITS = {
    "code": ["r/programming", "r/MachineLearning"],
    "ai": ["r/artificial", "r/LocalLLaMA"],
}


# ---------------------------------------------------------------------------
# LLM prompt
# ---------------------------------------------------------------------------


def build_prompt(topic: str) -> str:
    return f'''You are a precise research query planner.

Return ONLY valid JSON, no markdown, no extra text.
Use the exact schema below.
Be conservative: do not invent handles or communities unless you are reasonably confident.
Keep every query list to max 3 short English queries.
Prefer high-signal queries for the last 30 days.

Schema:
{{
  "canonical_topic": "...",
  "type": "person|product|topic",
  "intent_mode": "person-recent|person-bio|product-momentum|product-releases|topic-landscape|topic-discussion",
  "queries": {{
    "reddit": ["..."],
    "hackernews": ["..."],
    "web": ["..."],
    "youtube": ["..."]
  }},
  "handles": {{"x": "@username", "github": "username"}},
  "subreddits": ["r/name1", "r/name2"],
  "youtube_channels": [],
  "confidence": "high|medium"
}}

Guidance:
- PERSON: resolve likely X/GitHub handles if well known, add 1-2 relevant subreddits.
- PRODUCT/TOOL: add release, launch, comparison, company/founder angles.
- TOPIC: generate 2-3 search-friendly variants, not just the raw string.
- Set intent_mode to the best fit for the topic.
- If this is code/tooling-centric, include one GitHub-friendly web query.
- If unsure, leave handles empty rather than guessing.

Topic: {topic}'''


# ---------------------------------------------------------------------------
# Deterministic fallback planner
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", text.strip()).lower().strip("-")


def _handle_from_name(name: str) -> str:
    tokens = [re.sub(r"[^a-zA-Z0-9]", "", part).lower() for part in name.split()]
    return "".join(part for part in tokens if part)


def _dedupe_keep_order(values: list[str], limit: int = 3) -> list[str]:
    out: list[str] = []
    for value in values:
        clean = " ".join(str(value or "").split()).strip()
        if not clean or clean in out:
            continue
        out.append(clean)
        if len(out) >= limit:
            break
    return out


def _sanitize_subreddits(values: list[str], limit: int = 3) -> list[str]:
    out: list[str] = []
    for value in values or []:
        clean = str(value or "").strip().replace("https://www.reddit.com/", "").strip("/")
        if not clean:
            continue
        if not clean.lower().startswith("r/"):
            clean = f"r/{clean}"
        if clean not in out:
            out.append(clean)
        if len(out) >= limit:
            break
    return out


def _looks_like_person(topic: str) -> bool:
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'-]+", topic) if w]
    if not (2 <= len(words) <= 4):
        return False
    capitalized = sum(1 for word in words if word[:1].isupper())
    lowered = topic.lower()
    if any(hint in lowered for hint in PRODUCT_HINTS):
        return False
    return capitalized >= max(2, len(words) - 1)


def _topic_keywords(topic: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z0-9]+", topic) if len(token) >= 3}


def _infer_type(topic: str) -> str:
    lowered = topic.lower()
    if _looks_like_person(topic):
        return "person"
    if any(hint in lowered for hint in PRODUCT_HINTS):
        return "product"
    return "topic"


def _infer_intent_mode(topic: str, inferred_type: str) -> str:
    lowered = topic.lower()
    if inferred_type == "person":
        if any(term in lowered for term in {"bio", "story", "who is", "background"}):
            return "person-bio"
        return "person-recent"
    if inferred_type == "product":
        if any(term in lowered for term in {"release", "changelog", "launch", "version", "update"}):
            return "product-releases"
        return "product-momentum"
    if any(term in lowered for term in {"vs", "compare", "debate", "controversy", "reddit", "hn", "hacker news"}):
        return "topic-discussion"
    return "topic-landscape"


def _infer_subreddits(topic: str, inferred_type: str) -> list[str]:
    lowered = topic.lower()
    picks: list[str] = []
    if any(hint in lowered for hint in AI_HINTS):
        picks.extend(DEFAULT_SUBREDDITS["ai"])
    if inferred_type in {"person", "product"} or any(hint in lowered for hint in PERSON_CODE_HINTS):
        picks.extend(DEFAULT_SUBREDDITS["code"])
    return _sanitize_subreddits(picks, limit=2)


def deterministic_plan(topic: str) -> dict:
    topic_clean = topic.strip()
    inferred_type = _infer_type(topic_clean)
    intent_mode = _infer_intent_mode(topic_clean, inferred_type)
    lowered = topic_clean.lower()
    exact = f'"{topic_clean}"'
    keyword_blob = " ".join(sorted(_topic_keywords(topic_clean))[:4]) or topic_clean
    code_centric = any(hint in lowered for hint in PERSON_CODE_HINTS)
    ai_centric = any(hint in lowered for hint in AI_HINTS)

    if inferred_type == "person":
        if intent_mode == "person-bio":
            web_queries = [
                f'{exact} biography OR background',
                f'{exact} interview OR profile',
                f'{topic_clean} github OR official site',
            ]
            reddit_queries = [topic_clean, f'{topic_clean} profile', f'{topic_clean} background']
        else:
            web_queries = [
                f'{exact} last 30 days',
                f'{exact} interview OR talk OR podcast',
                f'{topic_clean} github OR open source OR AI',
            ]
            reddit_queries = [topic_clean, f'{topic_clean} interview', f'{topic_clean} open source']
        youtube_queries = [
            f'{topic_clean} interview',
            f'{topic_clean} talk',
            f'{topic_clean} podcast',
        ]
    elif inferred_type == "product":
        if intent_mode == "product-releases":
            web_queries = [
                f'{exact} release OR changelog',
                f'{topic_clean} version OR launch',
                f'{topic_clean} docs OR github',
            ]
            reddit_queries = [topic_clean, f'{topic_clean} release', f'{topic_clean} changelog']
        else:
            web_queries = [
                f'{exact} release OR launch',
                f'{topic_clean} update OR benchmark OR review',
                f'{topic_clean} github OR docs',
            ]
            reddit_queries = [topic_clean, f'{topic_clean} review', f'{topic_clean} alternatives']
        youtube_queries = [
            f'{topic_clean} demo',
            f'{topic_clean} review',
            f'{topic_clean} tutorial',
        ]
    else:
        if intent_mode == "topic-discussion":
            web_queries = [
                f'{topic_clean} last 30 days',
                f'{topic_clean} debate OR comparison',
                f'{topic_clean} analysis',
            ]
            reddit_queries = [topic_clean, f'{topic_clean} discussion', f'{topic_clean} debate']
        else:
            web_queries = [
                f'{topic_clean} last 30 days',
                f'{keyword_blob} trends',
                f'{topic_clean} analysis',
            ]
            reddit_queries = [topic_clean, f'{topic_clean} discussion', f'{keyword_blob} news']
        youtube_queries = [
            f'{topic_clean} analysis',
            f'{topic_clean} discussion',
            f'{topic_clean} podcast',
        ]

    if code_centric and inferred_type != "person":
        web_queries.insert(0, f'{topic_clean} github')
    if ai_centric and not any("reddit" in q.lower() for q in reddit_queries):
        reddit_queries.append(f'{topic_clean} openai OR anthropic')

    return {
        "canonical_topic": topic_clean,
        "type": inferred_type,
        "intent_mode": intent_mode,
        "queries": {
            "reddit": _dedupe_keep_order(reddit_queries, limit=3),
            "hackernews": _dedupe_keep_order([topic_clean, f'{topic_clean} launch'], limit=2),
            "web": _dedupe_keep_order(web_queries, limit=3),
            "youtube": _dedupe_keep_order(youtube_queries, limit=3),
        },
        "handles": {},
        "subreddits": _infer_subreddits(topic_clean, inferred_type),
        "youtube_channels": [],
        "confidence": "medium" if inferred_type != "topic" else "low",
        "resolver_backend": "deterministic-fallback",
    }


# ---------------------------------------------------------------------------
# Validation and normalization
# ---------------------------------------------------------------------------


def _plan_from_handle(handle: str, topic: str) -> dict:
    return {
        "canonical_topic": handle,
        "type": "person",
        "intent_mode": "person-recent",
        "queries": {
            "reddit": _dedupe_keep_order([handle, f'@{handle}', f'{handle} github']),
            "hackernews": _dedupe_keep_order([handle, f'{handle} launch']),
            "web": _dedupe_keep_order([f'@{handle} last 30 days', f'{handle} github', f'{handle} interview']),
            "youtube": _dedupe_keep_order([f'@{handle} interview', f'{handle} podcast']),
        },
        "handles": {"x": f"@{handle}"},
        "subreddits": [],
        "youtube_channels": [],
        "confidence": "high",
        "resolver_backend": "handle-shortcut",
    }


def _plan_from_github_url(topic: str, username: str, repo: str = "") -> dict:
    canonical_topic = repo or username
    inferred_type = "product" if repo else "person"
    web = [f'{canonical_topic} github', f'{canonical_topic} last 30 days']
    if repo:
        web.insert(1, f'{username}/{repo} release OR changelog')
    return {
        "canonical_topic": canonical_topic,
        "type": inferred_type,
        "intent_mode": "product-momentum" if repo else "person-recent",
        "queries": {
            "reddit": _dedupe_keep_order([canonical_topic, f'{canonical_topic} review']),
            "hackernews": _dedupe_keep_order([canonical_topic]),
            "web": _dedupe_keep_order(web),
            "youtube": _dedupe_keep_order([f'{canonical_topic} demo', f'{canonical_topic} review']),
        },
        "handles": {"github": username},
        "subreddits": _infer_subreddits(canonical_topic, inferred_type),
        "youtube_channels": [],
        "confidence": "high",
        "resolver_backend": "github-shortcut",
    }


def normalize_plan(plan: dict, topic: str, backend: str) -> dict:
    canonical_topic = " ".join(str(plan.get("canonical_topic") or topic).split()).strip() or topic.strip()
    plan_type = str(plan.get("type") or _infer_type(canonical_topic)).strip().lower()
    if plan_type not in {"person", "product", "topic"}:
        plan_type = _infer_type(canonical_topic)
    intent_mode = str(plan.get("intent_mode") or _infer_intent_mode(canonical_topic, plan_type)).strip().lower()

    queries = plan.get("queries") or {}
    web_queries = _dedupe_keep_order(list(queries.get("web") or []), limit=3)
    reddit_queries = _dedupe_keep_order(list(queries.get("reddit") or []), limit=3)
    hackernews_queries = _dedupe_keep_order(list(queries.get("hackernews") or []), limit=3)
    youtube_queries = _dedupe_keep_order(list(queries.get("youtube") or []), limit=3)

    if not web_queries or len(web_queries) < 2:
        fallback = deterministic_plan(canonical_topic)
        web_queries = _dedupe_keep_order(web_queries + fallback["queries"]["web"], limit=3)
        reddit_queries = _dedupe_keep_order(reddit_queries + fallback["queries"]["reddit"], limit=3)
        hackernews_queries = _dedupe_keep_order(hackernews_queries + fallback["queries"]["hackernews"], limit=3)
        youtube_queries = _dedupe_keep_order(youtube_queries + fallback["queries"]["youtube"], limit=3)

    handles = dict(plan.get("handles") or {})
    if handles.get("x") and not str(handles["x"]).startswith("@"):
        handles["x"] = f'@{str(handles["x"]).lstrip("@")}';
    if handles.get("github"):
        handles["github"] = str(handles["github"]).strip().strip("/")

    out = {
        "canonical_topic": canonical_topic,
        "type": plan_type,
        "intent_mode": intent_mode,
        "queries": {
            "reddit": reddit_queries,
            "hackernews": hackernews_queries,
            "web": web_queries,
            "youtube": youtube_queries,
        },
        "handles": {k: v for k, v in handles.items() if str(v or "").strip()},
        "subreddits": _sanitize_subreddits(plan.get("subreddits") or []),
        "youtube_channels": _dedupe_keep_order(list(plan.get("youtube_channels") or []), limit=3),
        "confidence": str(plan.get("confidence") or ("medium" if plan_type != "topic" else "low")).lower(),
        "resolver_backend": backend,
    }

    if not out["subreddits"]:
        out["subreddits"] = _infer_subreddits(canonical_topic, plan_type)
    if out["confidence"] not in {"high", "medium", "low"}:
        out["confidence"] = "medium"
    return out


# ---------------------------------------------------------------------------
# Core resolver
# ---------------------------------------------------------------------------


def resolve(topic: str, save_dir: Optional[Path] = None) -> dict:
    """Returns a query plan dict for the given topic and saves resolve.json."""
    topic_clean = topic.strip()

    if re.match(r"^@[a-zA-Z0-9_]{1,15}$", topic_clean):
        plan = _plan_from_handle(topic_clean.lstrip("@"), topic_clean)
        return _save_plan(plan, topic_clean, save_dir)

    gh_match = re.search(r"github\.com/([A-Za-z0-9_.-]+)(?:/([A-Za-z0-9_.-]+))?", topic_clean)
    if gh_match:
        plan = _plan_from_github_url(topic_clean, gh_match.group(1), gh_match.group(2) or "")
        return _save_plan(plan, topic_clean, save_dir)

    prompt = build_prompt(topic_clean)
    raw, backend = chat_complete(
        [{"role": "user", "content": prompt}],
        max_tokens=900,
        temperature=0.1,
        timeout=90,
    )

    plan: dict
    try:
        plan = json.loads(extract_json_object(raw)) if raw else deterministic_plan(topic_clean)
    except json.JSONDecodeError:
        plan = deterministic_plan(topic_clean)
        backend = "deterministic-fallback"

    normalized = normalize_plan(plan, topic_clean, backend or "deterministic-fallback")
    return _save_plan(normalized, topic_clean, save_dir)


# ---------------------------------------------------------------------------
# Save helper
# ---------------------------------------------------------------------------


def _save_plan(plan: dict, topic_clean: str, save_dir: Optional[Path]) -> dict:
    slug = _slugify(topic_clean)
    if save_dir:
        out = save_dir if save_dir.name == slug else save_dir / slug
    else:
        out = CACHE_DIR / slug
    out.mkdir(parents=True, exist_ok=True)
    (out / "resolve.json").write_text(json.dumps(plan, indent=2))
    print(f"[resolver] saved  → {out}/resolve.json", file=sys.stderr)
    print(f"[resolver] backend → {plan.get('resolver_backend', 'unknown')}", file=sys.stderr)
    return plan


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 resolver.py <topic> [save-dir]")
        sys.exit(1)

    topic = sys.argv[1]
    save_d = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    result = resolve(topic, save_d)
    print(json.dumps(result, indent=2))
