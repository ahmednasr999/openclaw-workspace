#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_TASKS = ROOT / "memory" / "active-tasks.md"
PIPELINE = ROOT / "jobs-bank" / "pipeline.md"
GOALS = ROOT / "GOALS.md"
OUT_DIR = ROOT / "advisory-board" / "outputs"

LENSES = [
    "CSO", "CRO", "COO", "CFO", "CBO", "CTO", "CPO", "Devils Advocate"
]

@dataclass
class Item:
    title: str
    source: str
    due: dt.date | None
    impact: float
    urgency: float
    confidence: float
    effort: float
    alignment: float
    lens: str

    @property
    def score(self) -> float:
        denom = self.effort * (1.1 - self.alignment)
        return round((self.impact * self.urgency * self.confidence) / max(denom, 0.1), 2)


def parse_date_any(text: str) -> dt.date | None:
    patterns = [r"(20\d\d-\d\d-\d\d)", r"(March\s+\d{1,2})"]
    for p in patterns:
        m = re.search(p, text, flags=re.I)
        if not m:
            continue
        val = m.group(1)
        try:
            if "-" in val:
                return dt.date.fromisoformat(val)
            # fallback for month name without year
            return dt.datetime.strptime(f"{val} {dt.date.today().year}", "%B %d %Y").date()
        except Exception:
            pass
    return None


def days_to_due(due: dt.date | None) -> int | None:
    if not due:
        return None
    return (due - dt.date.today()).days


def urgency_from_due(due: dt.date | None) -> float:
    d = days_to_due(due)
    if d is None:
        return 5
    if d <= 0:
        return 10
    if d <= 1:
        return 9
    if d <= 3:
        return 8
    if d <= 7:
        return 7
    if d <= 14:
        return 6
    return 4


def alignment_for_title(title: str) -> float:
    t = title.lower()
    if any(k in t for k in ["delphi", "follow-up", "vp", "director", "application", "pipeline"]):
        return 0.95
    if any(k in t for k in ["linkedin", "brand", "post"]):
        return 0.85
    if any(k in t for k in ["topmed", "pmo"]):
        return 0.9
    return 0.7


def lens_for_title(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["risk", "expire", "jwt", "2fa"]):
        return "CRO"
    if any(k in t for k in ["follow-up", "pipeline", "apply", "application", "interview"]):
        return "CSO"
    if any(k in t for k in ["linkedin", "threads", "brand", "post"]):
        return "CBO"
    return "COO"


def parse_active_tasks(md: str) -> List[Item]:
    items: List[Item] = []
    for line in md.splitlines():
        s = line.strip()
        if not s.startswith("- "):
            continue
        if "~~" in s or "✅" in s and "RESOLVED" in s:
            continue
        title = re.sub(r"^-\s*", "", s).replace("—", "-")
        due = parse_date_any(title)
        lens = lens_for_title(title)
        urgency = urgency_from_due(due)
        align = alignment_for_title(title)
        impact = 8 if "delphi" in title.lower() else 7
        confidence = 0.8
        effort = 3 if "update" in title.lower() else 4
        if "2fa" in title.lower():
            impact, effort = 8, 2
        items.append(Item(title=title, source="active-tasks", due=due, impact=impact, urgency=urgency, confidence=confidence, effort=effort, alignment=align, lens=lens))
    return items


def parse_pipeline(md: str) -> List[Item]:
    items: List[Item] = []
    for line in md.splitlines():
        if not line.startswith("|") or "| # |" in line or "---" in line:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 11:
            continue
        company = cols[2]
        role = cols[3]
        stage = cols[6]
        follow = cols[9]
        if "Applied" not in stage and "Interview" not in stage:
            continue
        due = None
        try:
            due = dt.date.fromisoformat(follow)
        except Exception:
            pass
        title = f"{company}: {role} ({stage})"
        items.append(Item(
            title=title,
            source="pipeline",
            due=due,
            impact=9,
            urgency=urgency_from_due(due),
            confidence=0.75,
            effort=5,
            alignment=0.95,
            lens="CSO",
        ))
    return items


def stale_flags() -> List[str]:
    flags: List[str] = []
    for p in [ACTIVE_TASKS, PIPELINE, GOALS]:
        if not p.exists():
            flags.append(f"Missing source: {p}")
            continue
        age_hours = (dt.datetime.now() - dt.datetime.fromtimestamp(p.stat().st_mtime)).total_seconds() / 3600
        if age_hours > 48:
            flags.append(f"Stale source (>48h): {p.relative_to(ROOT)}")
    return flags


def recommendation(items: List[Item]) -> str:
    if not items:
        return "No scored items found. Update active tasks and pipeline first."
    top = items[0].title.lower()
    if "delphi" in top:
        return "Send the Delphi follow-up first thing tomorrow morning, then batch all due follow-ups in one 30-minute block."
    return "Execute the top scored item first, then clear the other two top priorities before noon."


def build_brief(items: List[Item], flags: List[str]) -> str:
    now = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# Advisory Board Daily Brief | {now}", ""]
    lines.append("Top 3 priorities:")
    top = sorted(items, key=lambda x: x.score, reverse=True)[:3]
    for i, it in enumerate(top, 1):
        due = it.due.isoformat() if it.due else "n/a"
        lines.append(f"{i}. [{it.score}] {it.title} | Lens: {it.lens} | Due: {due} | Source: {it.source}")

    lines.append("")
    lines.append("Conflicts:")
    if len(top) >= 2 and all(t.lens == "CSO" for t in top[:2]):
        lines.append("- Job-search heavy day risk: reserve one protected block for TopMed/operations work.")
    else:
        lines.append("- No major cross-domain collision detected.")

    lines.append("")
    lines.append("New idea:")
    lines.append("- Add a 15-minute daily recruiter signal scan after follow-up block to catch reply windows early.")

    lines.append("")
    lines.append("Input health:")
    if flags:
        for f in flags:
            lines.append(f"- {f}")
    else:
        lines.append("- All core inputs are fresh.")

    lines.append("")
    lines.append("Recommendation:")
    lines.append(f"- {recommendation(top)}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="YYYY-MM-DD override")
    args = parser.parse_args()

    if args.date:
        target = dt.date.fromisoformat(args.date)
    else:
        target = dt.date.today()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    active_md = ACTIVE_TASKS.read_text(encoding="utf-8") if ACTIVE_TASKS.exists() else ""
    pipeline_md = PIPELINE.read_text(encoding="utf-8") if PIPELINE.exists() else ""

    items = parse_active_tasks(active_md) + parse_pipeline(pipeline_md)
    flags = stale_flags()
    brief = build_brief(items, flags)

    out = OUT_DIR / f"daily-brief-{target.isoformat()}.md"
    out.write_text(brief, encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
