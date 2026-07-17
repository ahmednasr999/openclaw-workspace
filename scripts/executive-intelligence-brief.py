#!/usr/bin/env python3
"""Build Ahmed's ranked, cross-source executive intelligence brief.

The script is deliberately deterministic. It consumes existing collectors,
normalizes and deduplicates their outputs, applies Ahmed's five positioning
pillars, and writes review inputs for the CEO, HR and CMO lanes. It never
publishes content or changes Notion approval state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

BASE = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE / "config" / "executive-intelligence.json"
RSS_PATH = BASE / "data" / "rss-content-candidates-latest.json"
FINTECH_DIR = BASE / "intel" / "fintech-radar"
X_JSON_PATHS = [
    BASE / "data" / "x-intelligence-candidates-latest.json",
    BASE / "data" / "x-bookmarks-latest.json",
]
X_INBOX = BASE / "data" / "executive-intelligence-inbox.jsonl"
FEEDBACK_PATH = BASE / "data" / "executive-intelligence-feedback.jsonl"
LATEST_JSON = BASE / "data" / "executive-intelligence-latest.json"
CONTENT_JSON = BASE / "data" / "executive-intelligence-content-candidates-latest.json"
STATE_PATH = BASE / "data" / "executive-intelligence-state.json"
HISTORY_PATH = BASE / "data" / "executive-intelligence-history.jsonl"
DAILY_MD = BASE / "intel" / "DAILY-INTEL.md"
LATEST_MD = BASE / "intel" / "EXECUTIVE-INTELLIGENCE.md"


@dataclass
class Signal:
    title: str
    url: str
    summary: str = ""
    source: str = ""
    source_type: str = "daily_web"
    published: str = ""
    category: str = ""
    pillar: str = ""
    pillar_matches: list[str] = field(default_factory=list)
    angle: str = ""
    take: str = ""
    risk: str = ""
    rule: str = ""
    hook: str = ""
    evidence_grade: str = ""
    gcc_relevance: str = ""
    company: str = ""
    score: int = 0
    score_reasons: list[str] = field(default_factory=list)
    signal_id: str = ""

    def text(self) -> str:
        return " ".join((self.title, self.summary, self.category, self.angle, self.take)).lower()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def canonical_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    try:
        parts = urlsplit(url)
        query = [(k, v) for k, v in parse_qsl(parts.query) if k.lower() not in {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "s", "t", "ref", "source"
        }]
        host = parts.netloc.lower().removeprefix("www.")
        path = re.sub(r"/+$", "", parts.path) or "/"
        return urlunsplit((parts.scheme.lower() or "https", host, path, urlencode(query), ""))
    except ValueError:
        return url


def domain_of(url: str) -> str:
    try:
        return urlsplit(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def clean_text(value: Any, limit: int = 420) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit].rstrip()


def title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", title.lower()).strip()


def parse_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return parsedate_to_datetime(value).date()
        except (TypeError, ValueError):
            return None


def normalized_domain_match(domain: str, candidates: Iterable[str]) -> bool:
    d = domain.lower()
    return any(d == c.lower() or d.endswith("." + c.lower()) for c in candidates)


def load_rss() -> list[Signal]:
    data = load_json(RSS_PATH, {})
    rows = data.get("candidates", []) if isinstance(data, dict) else data
    out = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        out.append(Signal(
            title=clean_text(row.get("title"), 220),
            url=canonical_url(row.get("link") or row.get("url") or ""),
            summary=clean_text(row.get("signal") or row.get("description")),
            source=clean_text(row.get("source"), 100),
            source_type="rss",
            published=clean_text(row.get("published"), 60),
            category=clean_text(row.get("category"), 80),
            pillar=clean_text(row.get("pillar"), 100),
            pillar_matches=list(row.get("pillar_matches") or []),
            angle=clean_text(row.get("angle"), 140),
            take=clean_text(row.get("take")),
            risk=clean_text(row.get("risk")),
            rule=clean_text(row.get("rule")),
            hook=clean_text(row.get("hook")),
        ))
    return out


def latest_fintech_file() -> Path | None:
    candidates = []
    for path in FINTECH_DIR.glob("fintech-radar-*.json"):
        if "content-job" in path.name:
            continue
        data = load_json(path, {})
        if isinstance(data, dict) and data.get("stories"):
            candidates.append(path)
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def load_fintech() -> list[Signal]:
    path = latest_fintech_file()
    data = load_json(path, {}) if path else {}
    out = []
    for row in data.get("stories", []) if isinstance(data, dict) else []:
        if not isinstance(row, dict):
            continue
        out.append(Signal(
            title=clean_text(row.get("title"), 220),
            url=canonical_url(row.get("primary_url") or row.get("url") or ""),
            summary=clean_text(row.get("snippet")),
            source=clean_text(row.get("source"), 100),
            source_type="fintech_radar",
            published=clean_text(row.get("published"), 80),
            category=clean_text(row.get("category"), 80),
            pillar="Fintech operations",
            pillar_matches=["Fintech operations"],
            angle="fintech operating signal",
            evidence_grade=clean_text(row.get("evidence_grade"), 80),
            gcc_relevance=clean_text(row.get("gcc_relevance"), 40),
            company=clean_text(row.get("companies"), 120),
        ))
    return out


MD_LINK = re.compile(r"^- \[([^]]+)]\((https?://[^)]+)\)")


def raw_daily_path(today: date) -> Path:
    dated = BASE / "intel" / f"intel-{today.isoformat()}.md"
    return dated if dated.exists() else DAILY_MD


def load_daily_web(today: date) -> list[Signal]:
    path = raw_daily_path(today)
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    out: list[Signal] = []
    section = ""
    company = ""
    for i, line in enumerate(lines):
        if line.startswith("## "):
            section = line[3:].strip()
            company = ""
            continue
        if line.startswith("### "):
            company = line[4:].strip()
            continue
        match = MD_LINK.match(line.strip())
        if not match:
            continue
        title, url = match.groups()
        summary = ""
        if i + 1 < len(lines) and lines[i + 1].strip().startswith("_"):
            summary = lines[i + 1].strip().strip("_")
        source_type = "company_intel" if "Company Intel" in section else "daily_web"
        category = section.split(".", 1)[-1].strip()
        out.append(Signal(
            title=clean_text(title, 220),
            url=canonical_url(url),
            summary=clean_text(summary),
            source=domain_of(url),
            source_type=source_type,
            published=today.isoformat(),
            category=category,
            company=company,
        ))
    return out


def rows_from_json(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    if isinstance(value, dict):
        for key in ("signals", "candidates", "items", "posts", "bookmarks"):
            if isinstance(value.get(key), list):
                return [x for x in value[key] if isinstance(x, dict)]
    return []


def load_x_signals() -> list[Signal]:
    rows: list[dict[str, Any]] = []
    for path in X_JSON_PATHS:
        rows.extend(rows_from_json(load_json(path, {})))
    if X_INBOX.exists():
        for line in X_INBOX.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
            except json.JSONDecodeError:
                continue
    out = []
    for row in rows:
        url = canonical_url(row.get("url") or row.get("link") or row.get("tweet_url") or "")
        title = clean_text(row.get("title") or row.get("text") or row.get("name"), 220)
        if not title or not url:
            continue
        out.append(Signal(
            title=title,
            url=url,
            summary=clean_text(row.get("summary") or row.get("description") or row.get("text")),
            source=clean_text(row.get("author") or row.get("source") or "X", 100),
            source_type="x_signal",
            published=clean_text(row.get("published") or row.get("created_at") or row.get("date"), 80),
            category=clean_text(row.get("category"), 80),
            pillar=clean_text(row.get("pillar"), 100),
            angle=clean_text(row.get("angle"), 140),
            take=clean_text(row.get("take")),
        ))
    return out


def infer_pillars(signal: Signal, cfg: dict[str, Any]) -> None:
    text = f" {signal.text()} "
    scores: list[tuple[int, str]] = []
    for pillar, words in cfg.get("pillars", {}).items():
        count = sum(1 for word in words if str(word).lower() in text)
        if count:
            scores.append((count, pillar))
    scores.sort(reverse=True)
    existing = [p for p in signal.pillar_matches if p]
    if signal.pillar and signal.pillar not in existing:
        existing.insert(0, signal.pillar)
    for _, pillar in scores:
        if pillar not in existing:
            existing.append(pillar)
    signal.pillar_matches = existing[:5]
    if not signal.pillar and signal.pillar_matches:
        signal.pillar = signal.pillar_matches[0]


def load_feedback() -> dict[str, int]:
    feedback: dict[str, int] = {}
    if not FEEDBACK_PATH.exists():
        return feedback
    for line in FEEDBACK_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        key = canonical_url(item.get("url") or "") or clean_text(item.get("signal_id"), 80)
        decision = str(item.get("decision") or "").lower()
        if key:
            feedback[key] = 7 if decision in {"use", "accepted", "promote"} else -10 if decision in {"reject", "dismiss"} else 0
    return feedback


def score_signal(signal: Signal, cfg: dict[str, Any], today: date, feedback: dict[str, int]) -> None:
    score = int(cfg.get("source_weights", {}).get(signal.source_type, 6))
    reasons = [f"{signal.source_type.replace('_', ' ')} source"]
    domain = domain_of(signal.url) or signal.source.lower()
    if normalized_domain_match(domain, cfg.get("trusted_domains", [])):
        score += 12
        reasons.append("trusted source")
    if normalized_domain_match(domain, cfg.get("weak_domains", [])):
        score -= 18
        reasons.append("weak or promotional source")
    if signal.evidence_grade.upper() in {"PRIMARY", "OFFICIAL", "TRUSTED_REPORTING"}:
        score += 8
        reasons.append("strong evidence")
    published = parse_date(signal.published)
    if published:
        age = max(0, (today - published).days)
        if age <= 2:
            score += 18
            reasons.append("very fresh")
        elif age <= 7:
            score += 13
            reasons.append("fresh")
        elif age <= int(cfg.get("freshness_days", 21)):
            score += 6
        else:
            score -= min(20, age // 14 * 4)
            reasons.append("stale")
    else:
        score -= 4
    if signal.pillar_matches:
        score += 18 + min(6, 3 * (len(signal.pillar_matches) - 1))
        reasons.append("pillar fit")
    else:
        score -= 15
        reasons.append("no positioning fit")
    text = signal.text()
    gcc_words = ("gcc", "saudi", "uae", "dubai", "riyadh", "jeddah", "abu dhabi", "gulf", "vision 2030")
    if signal.gcc_relevance.lower() in {"high", "medium"} or any(w in text for w in gcc_words):
        score += 12
        reasons.append("GCC relevance")
    if signal.source_type == "company_intel" or signal.company:
        score += 8
        reasons.append("company or career relevance")
    if any(w in text for w in ("decision", "governance", "workflow", "operating model", "risk", "execution")):
        score += 8
        reasons.append("executive actionability")
    if signal.take or signal.hook or signal.angle:
        score += 6
        reasons.append("content-ready angle")
    key = signal.url or signal.signal_id
    if feedback.get(key):
        score += feedback[key]
        reasons.append("feedback adjustment")
    signal.score = max(0, min(100, score))
    signal.score_reasons = reasons


def duplicate(a: Signal, b: Signal) -> bool:
    if a.url and b.url and a.url == b.url:
        return True
    ak, bk = title_key(a.title), title_key(b.title)
    if not ak or not bk:
        return False
    return SequenceMatcher(None, ak, bk).ratio() >= 0.88


def dedupe(signals: list[Signal]) -> list[Signal]:
    kept: list[Signal] = []
    for signal in sorted(signals, key=lambda x: x.score, reverse=True):
        if not signal.title or not signal.url:
            continue
        if any(duplicate(signal, old) for old in kept):
            continue
        kept.append(signal)
    return kept


def select_balanced(signals: list[Signal], cfg: dict[str, Any]) -> list[Signal]:
    selected: list[Signal] = []
    type_counts: dict[str, int] = {}
    domain_counts: dict[str, int] = {}
    for signal in signals:
        if signal.score < int(cfg.get("minimum_score", 48)):
            continue
        domain = domain_of(signal.url)
        if type_counts.get(signal.source_type, 0) >= int(cfg.get("max_per_source_type", 4)):
            continue
        if domain and domain_counts.get(domain, 0) >= int(cfg.get("max_per_domain", 2)):
            continue
        selected.append(signal)
        type_counts[signal.source_type] = type_counts.get(signal.source_type, 0) + 1
        if domain:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        if len(selected) >= int(cfg.get("max_brief_items", 10)):
            break
    return selected


def select_content_candidates(signals: list[Signal], cfg: dict[str, Any]) -> list[Signal]:
    """Prefer distinct pillars and angles so CMO receives a useful slate."""
    eligible = [s for s in signals if s.score >= int(cfg.get("minimum_content_score", 58))]
    limit = int(cfg.get("content_candidate_limit", 4))
    selected: list[Signal] = []
    primary_counts: dict[str, int] = {}
    angle_keys: set[str] = set()
    for signal in eligible:
        primary = signal.pillar or "Unmapped"
        angle = title_key(signal.angle or signal.hook)
        if primary_counts.get(primary, 0) >= 1 or (angle and angle in angle_keys):
            continue
        selected.append(signal)
        primary_counts[primary] = primary_counts.get(primary, 0) + 1
        if angle:
            angle_keys.add(angle)
        if len(selected) >= limit:
            return selected
    for signal in eligible:
        if signal in selected:
            continue
        primary = signal.pillar or "Unmapped"
        angle = title_key(signal.angle or signal.hook)
        if primary_counts.get(primary, 0) >= 2 or (angle and angle in angle_keys):
            continue
        selected.append(signal)
        primary_counts[primary] = primary_counts.get(primary, 0) + 1
        if angle:
            angle_keys.add(angle)
        if len(selected) >= limit:
            break
    return selected


def ensure_executive_fields(signal: Signal) -> None:
    if not signal.angle:
        signal.angle = {
            "AI execution and governance": "execution and control implications",
            "PMO and decision discipline": "decision rights and delivery discipline",
            "Healthcare transformation": "workflow and care-delivery implications",
            "Fintech operations": "operating and regulatory implications",
            "GCC transformation leadership": "GCC leadership and execution implications",
        }.get(signal.pillar, "executive operating implication")
    if not signal.take:
        signal.take = {
            "AI execution and governance": "The advantage will come from operating discipline around AI, not access to another model.",
            "PMO and decision discipline": "The management question is who owns the decision, control point, and measurable outcome.",
            "Healthcare transformation": "Technology creates value only when it improves the clinical workflow and accountability path.",
            "Fintech operations": "Regulatory and market shifts matter when they change operating choices, controls, or customer trust.",
            "GCC transformation leadership": "The signal matters when it changes a GCC leader's investment, governance, or execution decision.",
        }.get(signal.pillar, "Convert the signal into a decision, risk, or operating action.")
    if not signal.risk:
        signal.risk = "Treating the development as news without changing an operating decision."
    if not signal.rule:
        signal.rule = "Assign an owner to test the implication against current priorities and evidence."
    if not signal.hook:
        signal.hook = f"The important part of {signal.title} is the operating decision behind it."


def action_for(signal: Signal) -> str:
    if signal.source_type == "company_intel":
        return "Use in target-company or interview preparation; verify the development with a primary source."
    if signal.score >= 76:
        return "Review today and convert it into one decision, risk, or executive point of view."
    if signal.score >= 62:
        return "Watch and validate with a second credible source before acting."
    return "Retain as background context; no immediate action."


def render_markdown(selected: list[Signal], all_count: int, source_counts: dict[str, int], generated: datetime) -> str:
    date_label = generated.astimezone().strftime("%Y-%m-%d %H:%M %Z")
    lines = [
        "# Daily Executive Intelligence",
        "",
        f"*Generated: {date_label}*",
        f"*Ranked {len(selected)} signals from {all_count} normalized candidates. Investment/on-chain monitoring is excluded.*",
        "",
    ]
    if selected:
        lead = selected[0]
        lines += [
            "## Priority decision",
            "",
            f"**{lead.title}**",
            f"{lead.take} {action_for(lead)}",
            f"[Source]({lead.url})",
            "",
            "## Ranked signals",
            "",
        ]
    else:
        lines += ["## Priority decision", "", "No signal cleared today's quality threshold.", ""]
    for idx, signal in enumerate(selected, 1):
        pillars = ", ".join(signal.pillar_matches[:3]) or "No pillar match"
        lines += [
            f"### {idx}. {signal.title} | {signal.score}/100",
            "",
            f"- **Source:** {signal.source or domain_of(signal.url)} ({signal.source_type.replace('_', ' ')})",
            f"- **Positioning:** {pillars}",
            f"- **Why it matters:** {signal.take}",
            f"- **Risk:** {signal.risk}",
            f"- **Recommended action:** {action_for(signal)}",
            f"- **Content angle:** {signal.hook}",
            f"- **Evidence:** [Open source]({signal.url})",
            "",
        ]
    lines += [
        "## Feed health",
        "",
        "- " + ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in sorted(source_counts.items())),
        "- X signals appear only when a local selected-account/bookmark export or inbox item exists.",
        "- Strong content signals are routed to CMO review only. Nothing is auto-approved or published.",
        "",
    ]
    return "\n".join(lines)


def append_history(record: dict[str, Any]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    run_id = record.get("run_id")
    if HISTORY_PATH.exists():
        for line in HISTORY_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-20:]:
            try:
                if json.loads(line).get("run_id") == run_id:
                    return
            except json.JSONDecodeError:
                pass
    with HISTORY_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def run(today: date, dry_run: bool = False) -> dict[str, Any]:
    cfg = load_json(CONFIG_PATH, {})
    if not cfg:
        raise RuntimeError(f"Missing or invalid config: {CONFIG_PATH}")
    sources = {
        "rss": load_rss(),
        "fintech_radar": load_fintech(),
        "daily_web": load_daily_web(today),
        "x_signal": load_x_signals(),
    }
    signals = [item for rows in sources.values() for item in rows]
    feedback = load_feedback()
    for signal in signals:
        infer_pillars(signal, cfg)
        signal.signal_id = hashlib.sha256((signal.url or title_key(signal.title)).encode()).hexdigest()[:16]
        score_signal(signal, cfg, today, feedback)
        ensure_executive_fields(signal)
    unique = dedupe(signals)
    selected = select_balanced(unique, cfg)
    generated = datetime.now().astimezone()
    source_counts: dict[str, int] = {}
    for signal in signals:
        source_counts[signal.source_type] = source_counts.get(signal.source_type, 0) + 1
    content = select_content_candidates(selected, cfg)
    result = {
        "generated_at": generated.isoformat(),
        "run_date": today.isoformat(),
        "status": "ok",
        "input_counts": source_counts,
        "normalized_count": len(signals),
        "unique_count": len(unique),
        "selected_count": len(selected),
        "signals": [asdict(s) for s in selected],
    }
    content_payload = {
        "generated_at": generated.isoformat(),
        "status": "review_input_only",
        "approval_required": True,
        "candidates": [asdict(s) for s in content],
    }
    markdown = render_markdown(selected, len(signals), source_counts, generated)
    if dry_run:
        print(markdown)
        return result
    atomic_write(LATEST_JSON, json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    atomic_write(CONTENT_JSON, json.dumps(content_payload, indent=2, ensure_ascii=False) + "\n")
    atomic_write(LATEST_MD, markdown)
    atomic_write(DAILY_MD, markdown)
    archive = BASE / "intel" / f"executive-intelligence-{today.isoformat()}.md"
    atomic_write(archive, markdown)
    state = {
        "last_success": generated.isoformat(),
        "last_run_date": today.isoformat(),
        "selected_signal_ids": [s.signal_id for s in selected],
        "top_score": selected[0].score if selected else 0,
    }
    atomic_write(STATE_PATH, json.dumps(state, indent=2) + "\n")
    run_id = hashlib.sha256((today.isoformat() + "|" + "|".join(state["selected_signal_ids"])).encode()).hexdigest()[:20]
    append_history({
        "run_id": run_id,
        "generated_at": generated.isoformat(),
        "selected": [{"signal_id": s.signal_id, "score": s.score, "pillar": s.pillar, "url": s.url} for s in selected],
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Run date in YYYY-MM-DD format")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        run_date = date.fromisoformat(args.date) if args.date else datetime.now().astimezone().date()
        result = run(run_date, dry_run=args.dry_run)
        if not args.dry_run:
            print(json.dumps({
                "ok": True,
                "selected": result["selected_count"],
                "normalized": result["normalized_count"],
                "brief": str(DAILY_MD),
                "content_feed": str(CONTENT_JSON),
            }))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
