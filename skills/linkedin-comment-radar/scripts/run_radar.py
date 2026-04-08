#!/usr/bin/env python3
import argparse
import json
import os
import re
from datetime import datetime, timezone
from urllib.request import Request, urlopen

TAVILY_URL = "https://api.tavily.com/search"
PILLARS = ["digital transformation", "pmo", "healthtech", "fintech", "ai", "program management", "strategy execution", "gcc", "uae", "saudi"]
TITLE_STRONG = ["chief", "cxo", "ceo", "coo", "cto", "cio", "vp", "vice president", "director", "head"]
TITLE_MED = ["manager", "lead", "principal"]


def http_get(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="ignore")


def tavily_search(query, n, api_key):
    payload = json.dumps({
        "api_key": api_key,
        "query": query,
        "max_results": n,
        "include_raw_content": True,
    }).encode()
    req = Request(TAVILY_URL, data=payload, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=35) as r:
        data = json.loads(r.read().decode("utf-8", errors="ignore"))
    return data.get("results", [])


def parse_author(blob):
    if not blob:
        return "unknown"
    # best effort, first possessive pattern: "Name’s Post"
    m = re.search(r"([A-Z][A-Za-z\-\s\.]{2,60})’s Post", blob)
    if m:
        return m.group(1).strip()
    return "unknown"


def extract_engagement(blob):
    if not blob:
        return None
    m = re.search(r"(\d[\d,]*)\s+reactions?", blob, re.I)
    if m:
        return int(m.group(1).replace(",", ""))
    return None


def extract_meta(html):
    date = None
    comment_count = 0

    m = re.search(r'"datePublished":"([^"]+)"', html)
    if m:
        date = m.group(1)

    m = re.search(r'"commentCount":(\d+)', html)
    if m:
        comment_count = int(m.group(1))

    age_hours = None
    age = "N/A"
    if date:
        try:
            dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
            delta = datetime.now(timezone.utc) - dt
            age_hours = int(delta.total_seconds() // 3600)
            if age_hours < 24:
                age = f"{age_hours}h"
            else:
                age = f"{age_hours//24}d"
        except Exception:
            pass

    return {
        "published": date or "N/A",
        "age": age,
        "age_hours": age_hours,
        "comments": comment_count,
    }


def load_commented_urls(path):
    seen = set()
    if not os.path.exists(path):
        return seen
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                u = rec.get("url")
                if u:
                    seen.add(u)
            except Exception:
                continue
    return seen


def load_commented_authors(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def freshness_score(age_hours):
    if age_hours is None:
        return 0
    if age_hours < 6:
        return 30
    if age_hours < 24:
        return 25
    if age_hours < 48:
        return 20
    if age_hours < 72:
        return 15
    if age_hours <= 168:
        return 5
    return 0


def author_score(author, title_blob, author_history):
    blob = (author + " " + (title_blob or "")).lower()
    s = 5
    if any(k in blob for k in TITLE_STRONG):
        s = 25
    elif any(k in blob for k in TITLE_MED):
        s = 15
    # anti-repeat penalty: if same author commented in last 7 records
    recent_hits = author_history.get(author, 0)
    if recent_hits >= 2:
        s -= 8
    return max(0, s)


def topic_score(blob):
    b = (blob or "").lower()
    hits = sum(1 for p in PILLARS if p in b)
    return min(25, hits * 5)


def engagement_score(reactions, comments):
    x = reactions if reactions is not None else comments
    if x >= 20:
        return 20
    if x >= 10:
        return 15
    if x >= 5:
        return 10
    if x >= 1:
        return 5
    return 2


def compute_pqs(age_hours, author, title_blob, topic_blob, reactions, comments, author_history):
    return (
        freshness_score(age_hours)
        + author_score(author, title_blob, author_history)
        + topic_score(topic_blob)
        + engagement_score(reactions, comments)
    )


def build_queries(hashtags, countries, after_date):
    queries = []
    for h in hashtags:
        for c in countries:
            queries.append(
                f'site:linkedin.com/posts "{h}" "{c}" after:{after_date} ("PMO" OR "Digital Transformation" OR "Program Management") -jobs -hiring -apply'
            )
    return queries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hashtags", default="#PMO,#DigitalTransformation,#AI,#ProgramManagement,#StrategyExecution,#Transformation")
    ap.add_argument("--countries", default="UAE,Saudi Arabia,Qatar,Bahrain,Kuwait,Oman")
    ap.add_argument("--after", default="2026-02-24")
    ap.add_argument("-n", type=int, default=10)
    ap.add_argument("--per-query", type=int, default=5)
    ap.add_argument("--min-pqs", type=int, default=40)
    ap.add_argument("--commented-jsonl", default="/root/.openclaw/workspace/memory/commented-posts.jsonl")
    ap.add_argument("--commented-authors", default="/root/.openclaw/workspace/memory/commented-authors.json")
    args = ap.parse_args()

    key = os.getenv("TAVILY_API_KEY")
    if not key:
        raise SystemExit("Missing TAVILY_API_KEY")

    hashtags = [x.strip() for x in args.hashtags.split(",") if x.strip()]
    countries = [x.strip() for x in args.countries.split(",") if x.strip()]
    queries = build_queries(hashtags, countries, args.after)

    commented_urls = load_commented_urls(args.commented_jsonl)
    author_history = load_commented_authors(args.commented_authors)

    pool = {}
    for q in queries:
        try:
            results = tavily_search(q, args.per_query, key)
        except Exception:
            continue

        for r in results:
            url = r.get("url")
            if not url or "linkedin.com" not in url:
                continue
            if url in commented_urls or url in pool:
                continue

            snippet = r.get("content", "") or ""
            raw = r.get("raw_content", "") or ""
            combined = f"{snippet}\n{raw}"
            author = parse_author(combined)
            reactions = extract_engagement(combined)

            try:
                html = http_get(url)
                meta = extract_meta(html)
            except Exception:
                meta = {"published": "N/A", "age": "N/A", "age_hours": None, "comments": 0}

            if meta.get("age_hours") is None or meta.get("age_hours", 10**9) > 168:
                continue

            pqs = compute_pqs(
                meta.get("age_hours"), author, snippet, combined, reactions, meta.get("comments", 0), author_history
            )
            if pqs < args.min_pqs:
                continue

            pool[url] = {
                "url": url,
                "author": author,
                "age": meta.get("age", "N/A"),
                "age_hours": meta.get("age_hours"),
                "reactions": reactions if reactions is not None else "N/A",
                "comments": meta.get("comments", 0),
                "pqs": pqs,
            }

    rows = list(pool.values())
    rows.sort(key=lambda x: (-x.get("pqs", 0), x.get("age_hours", 10**9)))
    rows = rows[: args.n]

    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
