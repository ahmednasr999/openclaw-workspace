#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "advisory-board" / "outputs"

ACTIVE_TASKS = ROOT / "memory" / "active-tasks.md"
PIPELINE = ROOT / "jobs-bank" / "pipeline.md"
GOALS = ROOT / "GOALS.md"
AI_ROADMAP = ROOT / "memory" / "ai-automation-roadmap.md"
FINANCIAL = ROOT / "memory" / "financial-snapshot.md"
CALENDAR = ROOT / "memory" / "linkedin_content_calendar.md"


@dataclass
class Item:
    title: str
    source: str
    domain: str
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
    for pat in [r"(20\d\d-\d\d-\d\d)", r"(March\s+\d{1,2})", r"(April\s+\d{1,2})"]:
        m = re.search(pat, text, flags=re.I)
        if not m:
            continue
        val = m.group(1)
        try:
            if "-" in val:
                return dt.date.fromisoformat(val)
            return dt.datetime.strptime(f"{val} {dt.date.today().year}", "%B %d %Y").date()
        except Exception:
            continue
    return None


def days_to_due(due: dt.date | None) -> int | None:
    if due is None:
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


def parse_active_tasks(md: str) -> List[Item]:
    out: List[Item] = []
    for line in md.splitlines():
        s = line.strip()
        if not s.startswith("- "):
            continue
        if "RESOLVED" in s or "COMPLETED" in s or "~~" in s:
            continue
        title = re.sub(r"^-\s*", "", s).replace("—", "-")
        tl = title.lower()
        due = parse_date_any(title)
        domain = "career"
        lens = "COO"
        align = 0.8
        impact = 7
        effort = 4

        if any(k in tl for k in ["delphi", "follow-up", "apply", "pipeline", "interview"]):
            domain, lens, align, impact = "career", "CSO", 0.95, 9
        elif any(k in tl for k in ["threads", "linkedin", "post", "bio"]):
            domain, lens, align, impact = "brand", "CBO", 0.85, 6
        elif any(k in tl for k in ["2fa", "jwt", "expires", "critical", "urgent"]):
            domain, lens, align, impact, effort = "risk", "CRO", 0.9, 8, 2

        out.append(Item(title=title, source="active-tasks", domain=domain, due=due, impact=impact,
                        urgency=urgency_from_due(due), confidence=0.8, effort=effort,
                        alignment=align, lens=lens))
    return out


def parse_pipeline(md: str) -> List[Item]:
    out: List[Item] = []
    for line in md.splitlines():
        if not line.startswith("|") or "| # |" in line or "---" in line:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 11:
            continue
        company, role, stage, follow = cols[2], cols[3], cols[6], cols[9]
        # Follow-up policy: do not prompt proactive follow-up for generic LinkedIn "Applied" rows.
        # Keep interview-stage threads as active priorities.
        if "Interview" not in stage:
            continue
        try:
            due = dt.date.fromisoformat(follow)
        except Exception:
            due = None

        out.append(Item(
            title=f"{company}: {role} ({stage})",
            source="pipeline",
            domain="career",
            due=due,
            impact=9,
            urgency=urgency_from_due(due),
            confidence=0.75,
            effort=5,
            alignment=0.95,
            lens="CSO",
        ))
    return out


def parse_ai_automation(md: str) -> List[Item]:
    out: List[Item] = []
    if not md.strip():
        out.append(Item(
            title="AI roadmap file is empty, define next 2 automation milestones",
            source="ai-roadmap",
            domain="ai",
            due=None,
            impact=6,
            urgency=5,
            confidence=0.7,
            effort=3,
            alignment=0.75,
            lens="CTO",
        ))
        return out

    for line in md.splitlines():
        s = line.strip()
        if not s.startswith("- "):
            continue
        title = s[2:]
        due = parse_date_any(title)
        out.append(Item(title=title, source="ai-roadmap", domain="ai", due=due, impact=7,
                        urgency=urgency_from_due(due), confidence=0.7, effort=4,
                        alignment=0.8, lens="CTO"))
    return out


def parse_financial(md: str) -> List[Item]:
    out: List[Item] = []
    if not md.strip():
        out.append(Item(
            title="Financial snapshot missing, add monthly burn and runway",
            source="financial",
            domain="financial",
            due=None,
            impact=7,
            urgency=6,
            confidence=0.7,
            effort=2,
            alignment=0.7,
            lens="CFO",
        ))
        return out

    low_cash = re.search(r"(runway|cash|burn)", md, re.I) is None
    if low_cash:
        out.append(Item(
            title="Financial snapshot lacks runway and burn fields",
            source="financial",
            domain="financial",
            due=None,
            impact=6,
            urgency=5,
            confidence=0.7,
            effort=2,
            alignment=0.7,
            lens="CFO",
        ))
    return out


def parse_time_allocation(md_active: str, md_calendar: str) -> List[Item]:
    out: List[Item] = []
    followups = len(re.findall(r"follow-up", md_active, re.I))
    topmed_refs = len(re.findall(r"topmed", md_active, re.I))
    if followups >= 3 and topmed_refs == 0:
        out.append(Item(
            title="Follow-up load is high, reserve one protected TopMed block",
            source="time-allocation",
            domain="time",
            due=dt.date.today(),
            impact=7,
            urgency=8,
            confidence=0.8,
            effort=2,
            alignment=0.85,
            lens="COO",
        ))
    if not md_calendar.strip():
        out.append(Item(
            title="Content calendar appears empty or unavailable",
            source="time-allocation",
            domain="time",
            due=None,
            impact=5,
            urgency=5,
            confidence=0.6,
            effort=3,
            alignment=0.7,
            lens="COO",
        ))
    return out


def parse_risk(items: List[Item]) -> List[Item]:
    out: List[Item] = []
    for it in items:
        tl = it.title.lower()
        if any(k in tl for k in ["jwt", "2fa", "expires", "critical"]):
            out.append(Item(
                title=f"Risk watch: {it.title}",
                source="risk",
                domain="risk",
                due=it.due,
                impact=9,
                urgency=max(it.urgency, 8),
                confidence=0.85,
                effort=2,
                alignment=0.9,
                lens="CRO",
            ))
    return out


def stale_flags() -> List[str]:
    flags: List[str] = []
    for p in [ACTIVE_TASKS, PIPELINE, GOALS, AI_ROADMAP, FINANCIAL]:
        if not p.exists():
            flags.append(f"Missing source: {p.relative_to(ROOT)}")
            continue
        age = (dt.datetime.now() - dt.datetime.fromtimestamp(p.stat().st_mtime)).total_seconds() / 3600
        if age > 48:
            flags.append(f"Stale source (>48h): {p.relative_to(ROOT)}")
    return flags


def detect_conflicts(items: List[Item]) -> List[str]:
    conflicts: List[str] = []
    top = sorted(items, key=lambda i: i.score, reverse=True)[:5]
    if sum(1 for t in top if t.domain == "career") >= 3:
        conflicts.append("Career tasks dominate top priorities, protect one block for core role execution.")

    due_today = [t for t in top if t.due and (t.due - dt.date.today()).days <= 0]
    if len(due_today) >= 2:
        conflicts.append("Multiple overdue or due-now items compete for attention, run one focused execution sprint.")

    if any("risk watch" in t.title.lower() for t in items) and any(t.domain == "career" for t in top):
        conflicts.append("Risk and execution collision detected, clear security/credential risk before outreach tasks.")

    if not conflicts:
        conflicts.append("No major cross-domain collision detected.")
    return conflicts


def build_daily(items: List[Item], flags: List[str], conflicts: List[str]) -> str:
    now = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")
    top = sorted(items, key=lambda i: i.score, reverse=True)[:3]

    lines = [f"# Advisory Board Daily Brief | {now}", "", "Top 3 priorities:"]
    for i, it in enumerate(top, 1):
        due = it.due.isoformat() if it.due else "n/a"
        lines.append(f"{i}. [{it.score}] {it.title} | Lens: {it.lens} | Domain: {it.domain} | Due: {due}")

    lines.extend(["", "Conflicts:"] + [f"- {c}" for c in conflicts[:3]])
    lines.extend(["", "Input health:"] + ([f"- {f}" for f in flags] if flags else ["- All core inputs are fresh."]))
    lines.extend(["", "Recommendation:", f"- {recommendation(top)}", ""])
    return "\n".join(lines)


def recommendation(top: List[Item]) -> str:
    if not top:
        return "No scored priorities found, refresh active tasks and pipeline first."
    t0 = top[0].title.lower()
    if "delphi" in t0:
        return "Send Delphi follow-up first, then clear one more due application thread, then switch to TopMed execution block."
    if "risk watch" in t0 or "jwt" in t0 or "2fa" in t0:
        return "Clear the risk item first, then run execution tasks, because blocked credentials can stall all workflows."
    return "Execute top priority first, then close one supporting task in the same domain before switching context."


def iso_week(d: dt.date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def domain_balance(items: List[Item]) -> List[str]:
    counts = {}
    for i in items:
        counts[i.domain] = counts.get(i.domain, 0) + 1
    domains = ["career", "brand", "ai", "risk", "time", "financial"]
    missing = [d for d in domains if counts.get(d, 0) == 0]
    notes = []
    if missing:
        notes.append("Missing domains this week: " + ", ".join(missing))
    notes.append("Domain counts: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return notes


def strategic_bets(top: List[Item]) -> List[str]:
    bets = []
    for t in top[:3]:
        bets.append(f"BET: {t.title} | Target score >= {max(20, int(t.score))} | Owner: Ahmed | Horizon: 7 days")
    return bets


def build_weekly(items: List[Item], flags: List[str], conflicts: List[str], target: dt.date) -> str:
    top = sorted(items, key=lambda i: i.score, reverse=True)[:5]
    lines = [f"# Advisory Board Weekly Strategy Report | {iso_week(target)}", ""]
    lines.append("Top strategic priorities:")
    for i, it in enumerate(top, 1):
        lines.append(f"{i}. [{it.score}] {it.title} ({it.domain}, {it.lens})")

    lines.extend(["", "Conflicts detected:"] + [f"- {c}" for c in conflicts])
    lines.extend(["", "Strategic bets for next week:"] + [f"- {b}" for b in strategic_bets(top)])
    lines.extend(["", "Balance check:"] + [f"- {n}" for n in domain_balance(items)])
    lines.extend(["", "Input health:"] + ([f"- {f}" for f in flags] if flags else ["- All core inputs are fresh."]))
    lines.extend(["", "Recommendation:", f"- {recommendation(top)}", ""])
    return "\n".join(lines)


def build_calibration(items: List[Item], target: dt.date) -> str:
    top = sorted(items, key=lambda i: i.score, reverse=True)[:5]
    payload = {
        "month": target.strftime("%Y-%m"),
        "generatedAt": dt.datetime.now(dt.UTC).isoformat(),
        "top5": [
            {
                "title": i.title,
                "score": i.score,
                "domain": i.domain,
                "lens": i.lens,
                "confidence": i.confidence,
                "alignment": i.alignment,
            }
            for i in top
        ],
        "notes": [
            "If all top5 are from one domain, reduce that domain impact by 10 percent next cycle.",
            "If confidence is below 0.7 on top items, request more evidence in source files.",
        ],
    }
    return json.dumps(payload, indent=2)


def ensure_stubs() -> List[Path]:
    created: List[Path] = []
    if not AI_ROADMAP.exists():
        AI_ROADMAP.write_text("# AI Automation Roadmap\n\n- Define next 2 high-value automations\n", encoding="utf-8")
        created.append(AI_ROADMAP)
    if not FINANCIAL.exists():
        FINANCIAL.write_text("# Financial Snapshot\n\n- Monthly burn: TBD\n- Runway: TBD\n", encoding="utf-8")
        created.append(FINANCIAL)
    return created


def load(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def run(mode: str, target: dt.date) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ensure_stubs()

    active = load(ACTIVE_TASKS)
    pipeline = load(PIPELINE)
    ai = load(AI_ROADMAP)
    fin = load(FINANCIAL)
    cal = load(CALENDAR)

    items = []
    items.extend(parse_active_tasks(active))
    items.extend(parse_pipeline(pipeline))
    items.extend(parse_ai_automation(ai))
    items.extend(parse_financial(fin))
    items.extend(parse_time_allocation(active, cal))
    items.extend(parse_risk(items))

    flags = stale_flags()
    conflicts = detect_conflicts(items)

    if mode == "daily":
        body = build_daily(items, flags, conflicts)
        out = OUT_DIR / f"daily-brief-{target.isoformat()}.md"
    elif mode == "weekly":
        body = build_weekly(items, flags, conflicts, target)
        out = OUT_DIR / f"weekly-report-{iso_week(target)}.md"
    else:
        body = build_calibration(items, target)
        out = OUT_DIR / f"monthly-calibration-{target.strftime('%Y-%m')}.json"

    out.write_text(body, encoding="utf-8")
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["daily", "weekly", "calibrate"], default="daily")
    p.add_argument("--date", help="YYYY-MM-DD override")
    args = p.parse_args()

    target = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    out = run(args.mode, target)
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
