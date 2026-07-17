#!/usr/bin/env python3
"""Bounded, read-only GitHub workflow discovery with inert quarantine output."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

WORKSPACE = Path("/root/.openclaw/workspace")
USER_AGENT = "NASR-Skill-Discovery-Pilot/1.0"

SUSPICIOUS_PATTERNS: dict[str, tuple[str, ...]] = {
    "remote_shell_pipe": (r"curl\s+[^\n|]+\|\s*(?:ba)?sh", r"wget\s+[^\n|]+\|\s*(?:ba)?sh"),
    "destructive_or_broad_permissions": (r"rm\s+-rf\s+[/~$]", r"chmod\s+(?:-R\s+)?777"),
    "credential_collection": (
        r"(?:access[_ -]?token|api[_ -]?key|password|private[_ -]?key|ssh[_ -]?key).{0,60}(?:upload|send|copy|collect|export)",
        r"(?:\.env|id_rsa|credentials).{0,60}(?:upload|send|copy|collect)",
    ),
    "disable_security": (r"disable.{0,30}(?:firewall|monitoring|audit|security)", r"bypass.{0,30}(?:approval|security|sandbox)"),
    "external_upload": (r"upload.{0,60}(?:home directory|local files|workspace|source code)",),
}

TOKEN_RE = re.compile(r"[a-z0-9]+")
SIMILARITY_STOPWORDS = {
    "agent", "agents", "skill", "skills", "workflow", "workflows", "automation",
    "automate", "tool", "tools", "user", "users", "use", "using", "when", "with",
    "from", "into", "that", "this", "your", "their", "make", "sure", "whenever",
}


@dataclass
class Candidate:
    name: str
    url: str
    description: str
    stars: int
    created_at: str
    pushed_at: str
    archived: bool
    fork: bool
    default_branch: str
    license: str | None
    topics: list[str]
    readme_headings: list[str]
    provenance_score: int
    safety_categories: list[str]
    safety_count: int
    relevance_score: int
    relevance_terms: list[str]
    duplicate_score: float
    duplicate_skill: str | None
    decision: str
    reasons: list[str]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def request_json(url: str) -> dict[str, Any]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def request_text(url: str, max_bytes: int = 200_000) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read(max_bytes).decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return ""


def tokenize(text: str, *, for_similarity: bool = False) -> set[str]:
    tokens = {token for token in TOKEN_RE.findall(text.lower()) if len(token) > 2}
    return tokens - SIMILARITY_STOPWORDS if for_similarity else tokens


def installed_skills(skills_root: Path) -> list[tuple[str, set[str]]]:
    found: list[tuple[str, set[str]]] = []
    for path in sorted(skills_root.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8", errors="replace")[:5000]
        description = ""
        match = re.search(r"^description:\s*[\"']?(.*?)[\"']?\s*$", text, re.M)
        if match:
            description = match.group(1)
        name = path.parent.name
        found.append((name, tokenize(f"{name} {description}", for_similarity=True)))
    return found


def duplicate_match(text: str, skills: list[tuple[str, set[str]]], candidate_name: str = "") -> tuple[float, str | None]:
    candidate_tokens = tokenize(text, for_similarity=True)
    candidate_leaf = candidate_name.rsplit("/", 1)[-1].replace("-", " ").replace("_", " ").lower().strip()
    best_score = 0.0
    best_name: str | None = None
    for name, skill_tokens in skills:
        if not candidate_tokens or not skill_tokens:
            continue
        overlap = candidate_tokens & skill_tokens
        # One shared routing word is not evidence of duplication. Require at
        # least two meaningful tokens, or an exact normalized skill name.
        normalized_name = name.replace("-", " ").replace("_", " ").lower().strip()
        exact_name = bool(candidate_leaf and candidate_leaf == normalized_name)
        if len(overlap) < 2 and not exact_name:
            score = 0.0
        else:
            score = len(overlap) / max(len(skill_tokens), 1)
            if exact_name:
                score = max(score, 0.8)
        if score > best_score:
            best_score, best_name = score, name
    return round(best_score, 3), best_name


def scan_suspicious(text: str) -> list[str]:
    lowered = text.lower()
    categories = []
    for category, patterns in SUSPICIOUS_PATTERNS.items():
        if any(re.search(pattern, lowered, re.I | re.S) for pattern in patterns):
            categories.append(category)
    return categories


def term_present(text: str, term: str) -> bool:
    escaped = re.escape(term.lower()).replace(r"\ ", r"\s+")
    return bool(re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text.lower()))


def relevance_evidence(repo: dict[str, Any], readme: str, terms: list[str]) -> tuple[int, list[str]]:
    primary = " ".join(
        [repo.get("full_name") or "", repo.get("description") or "", " ".join(repo.get("topics") or [])]
    )
    heading_text = " ".join(headings(readme))
    primary_matches = {term for term in terms if term_present(primary, term)}
    heading_matches = {term for term in terms if term_present(heading_text, term)} - primary_matches
    # README headings can add one supporting point, but cannot turn a broadly
    # matching repository into a high-value candidate by repetition alone.
    score = min(5, len(primary_matches) + (1 if heading_matches else 0))
    return score, sorted(primary_matches | heading_matches)


def headings(text: str) -> list[str]:
    result = []
    for line in text.splitlines():
        match = re.match(r"^#{1,3}\s+(.+?)\s*$", line)
        if match:
            clean = re.sub(r"[`*_\[\]]", "", match.group(1)).strip()[:120]
            if clean and clean not in result:
                result.append(clean)
        if len(result) >= 12:
            break
    return result


def provenance_score(repo: dict[str, Any], now: datetime) -> int:
    score = 0
    if repo.get("html_url") and repo.get("full_name"):
        score += 1
    if not repo.get("archived") and not repo.get("fork"):
        score += 1
    pushed_raw = repo.get("pushed_at") or ""
    try:
        pushed = datetime.fromisoformat(pushed_raw.replace("Z", "+00:00"))
        if now - pushed <= timedelta(days=180):
            score += 1
    except ValueError:
        pass
    if (repo.get("license") or {}).get("spdx_id") not in {None, "NOASSERTION"}:
        score += 1
    if int(repo.get("stargazers_count") or 0) >= 20:
        score += 1
    return score


def decide(repo: dict[str, Any], safety: list[str], relevance: int, duplicate: float, provenance: int) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if repo.get("archived") or repo.get("fork"):
        reasons.append("archived or forked repository")
        return "REJECT_PROVENANCE", reasons
    if len(safety) >= 2:
        reasons.append(f"{len(safety)} suspicious instruction categories")
        return "REJECT_SAFETY", reasons
    if duplicate >= 0.75:
        reasons.append(f"strong installed-skill overlap ({duplicate:.2f})")
        return "REJECT_DUPLICATE", reasons
    license_id = (repo.get("license") or {}).get("spdx_id")
    if license_id in {None, "NOASSERTION"}:
        reasons.append("missing or indeterminate license")
        if safety:
            reasons.append("one suspicious instruction category requires inspection")
        return "WATCH", reasons
    if provenance >= 4 and relevance >= 3 and duplicate < 0.55 and not safety:
        reasons.extend(["credible provenance", "relevant workflow evidence", "low duplication and no suspicious text match"])
        return "REVIEW", reasons
    if provenance < 3:
        reasons.append("insufficient provenance or maintenance evidence")
    if relevance < 3:
        reasons.append("weak workflow relevance")
    if duplicate >= 0.55:
        reasons.append(f"moderate installed-skill overlap ({duplicate:.2f})")
    if safety:
        reasons.append("one suspicious instruction category requires inspection")
    return "WATCH", reasons or ["requires manual evidence review"]


def search_repositories(config: dict[str, Any]) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    created_after = (now - timedelta(days=int(config["lookback_days"]))).date().isoformat()
    repos: dict[str, dict[str, Any]] = {}
    for query in config["queries"]:
        q = f'{query} stars:>={int(config["min_stars"])} created:>={created_after}'
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
            {"q": q, "sort": "updated", "order": "desc", "per_page": 10}
        )
        for repo in request_json(url).get("items", []):
            repos[repo["full_name"]] = repo
    terms = [str(term).lower() for term in config["relevance_terms"]]
    ranked = sorted(repos.values(), key=lambda item: (
        sum(
            1 for term in terms
            if term_present(
                " ".join([item.get("full_name") or "", item.get("description") or "", " ".join(item.get("topics") or [])]),
                term,
            )
        ),
        int(item.get("stargazers_count") or 0),
        item.get("pushed_at") or "",
    ), reverse=True)
    return ranked[: int(config["max_candidates"])]


def load_fixture(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    repositories = payload["repositories"] if isinstance(payload, dict) else payload
    for repo in repositories:
        if "readme_parts" in repo and "readme" not in repo:
            repo["readme"] = "".join(str(part) for part in repo.pop("readme_parts"))
    return repositories


def readme_for(repo: dict[str, Any]) -> str:
    if "readme" in repo:
        return str(repo.get("readme") or "")
    branch = repo.get("default_branch") or "main"
    base = f"https://raw.githubusercontent.com/{repo['full_name']}/{branch}"
    for filename in ("README.md", "readme.md", "README.rst"):
        text = request_text(f"{base}/{filename}")
        if text:
            return text
    return ""


def evaluate(repos: list[dict[str, Any]], config: dict[str, Any], run_dir: Path) -> list[Candidate]:
    skills = installed_skills(WORKSPACE / "skills")
    relevance_terms = [str(term).lower() for term in config["relevance_terms"]]
    now = datetime.now(timezone.utc)
    quarantine = run_dir / "quarantine"
    quarantine.mkdir(parents=True, exist_ok=True)
    candidates: list[Candidate] = []
    for repo in repos:
        readme = readme_for(repo)
        safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "__", repo.get("full_name", "unknown"))
        (quarantine / f"{safe_name}.readme.txt").write_text(readme, encoding="utf-8")
        relevant_score, matched_terms = relevance_evidence(repo, readme[:50_000], relevance_terms)
        safety = scan_suspicious(readme[:100_000])
        duplicate, duplicate_skill = duplicate_match(
            " ".join([repo.get("full_name") or "", repo.get("description") or "", " ".join(repo.get("topics") or []), " ".join(headings(readme))]),
            skills,
            repo.get("full_name") or "",
        )
        provenance = provenance_score(repo, now)
        decision, reasons = decide(repo, safety, relevant_score, duplicate, provenance)
        license_data = repo.get("license") or {}
        candidates.append(
            Candidate(
                name=repo.get("full_name") or "unknown",
                url=repo.get("html_url") or "",
                description=(repo.get("description") or "")[:300],
                stars=int(repo.get("stargazers_count") or 0),
                created_at=repo.get("created_at") or "",
                pushed_at=repo.get("pushed_at") or "",
                archived=bool(repo.get("archived")),
                fork=bool(repo.get("fork")),
                default_branch=repo.get("default_branch") or "",
                license=license_data.get("spdx_id"),
                topics=list(repo.get("topics") or [])[:20],
                readme_headings=headings(readme),
                provenance_score=provenance,
                safety_categories=safety,
                safety_count=len(safety),
                relevance_score=relevant_score,
                relevance_terms=matched_terms[:12],
                duplicate_score=duplicate,
                duplicate_skill=duplicate_skill,
                decision=decision,
                reasons=reasons,
            )
        )
    return candidates


def render_report(candidates: list[Candidate], run_dir: Path, source: str) -> str:
    counts: dict[str, int] = {}
    for candidate in candidates:
        counts[candidate.decision] = counts.get(candidate.decision, 0) + 1
    lines = [
        "# Skill Discovery Pilot",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Source: {source}",
        f"- Candidates: {len(candidates)}",
        f"- Decisions: {', '.join(f'{key}={value}' for key, value in sorted(counts.items())) or 'none'}",
        f"- Quarantine: `{run_dir / 'quarantine'}`",
        "- Safety boundary: metadata and inert text only; no clone, execution, install, merge, or external write.",
        "",
        "## Candidates",
        "",
    ]
    for candidate in candidates:
        overlap = f"{candidate.duplicate_score:.2f}"
        if candidate.duplicate_skill:
            overlap += f" with `{candidate.duplicate_skill}`"
        lines.extend(
            [
                f"### {candidate.decision}: [{candidate.name}]({candidate.url})",
                "",
                f"- Why: {'; '.join(candidate.reasons)}",
                f"- Provenance: {candidate.provenance_score}/5, {candidate.stars} stars, license `{candidate.license or 'missing'}`, pushed `{candidate.pushed_at or 'unknown'}`",
                f"- Safety: {candidate.safety_count} suspicious categories" + (f" ({', '.join(candidate.safety_categories)})" if candidate.safety_categories else ""),
                f"- Relevance: {candidate.relevance_score}/5, terms: {', '.join(candidate.relevance_terms) or 'none'}",
                f"- Installed-skill overlap: {overlap}",
                f"- Workflow headings: {', '.join(candidate.readme_headings[:6]) or 'none extracted'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Promotion gate",
            "",
            "`REVIEW` means inspect next, not install. Any promotion requires a separate approved task, isolated source/dependency review, license validation, deduplication, a draft outside the active skill path, and representative tests.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(WORKSPACE / "config/skill-discovery-pilot.json"))
    parser.add_argument("--fixture")
    parser.add_argument("--max-candidates", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = load_json(config_path)
    if args.max_candidates is not None:
        config["max_candidates"] = args.max_candidates
    limit = int(config.get("max_candidates", 0))
    if not 5 <= limit <= 10:
        print("max_candidates must be between 5 and 10", file=sys.stderr)
        return 2
    source = f"fixture:{args.fixture}" if args.fixture else "github-api"
    repos = load_fixture(Path(args.fixture)) if args.fixture else search_repositories(config)
    repos = repos[:limit]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_root = WORKSPACE / config["output_root"]
    run_dir = output_root / stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    candidates = evaluate(repos, config, run_dir)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "candidate_limit": limit,
        "candidate_count": len(candidates),
        "safety_boundary": "metadata-and-inert-text-only",
        "candidates": [asdict(candidate) for candidate in candidates],
    }
    (run_dir / "results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report = render_report(candidates, run_dir, source)
    (run_dir / "report.md").write_text(report, encoding="utf-8")
    report_path = WORKSPACE / config["report_path"]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(json.dumps({"status": "ok", "run_dir": str(run_dir), "report": str(report_path), "candidate_count": len(candidates)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
