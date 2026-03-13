#!/usr/bin/env python3
"""
Advisory Board v3 Engine
- Change-first analysis: only surface what CHANGED since last run
- Dynamic recommendations based on actual changes
- Cross-domain dot-connecting
- Concise output: 15 lines max daily, 25 lines max weekly
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# =============================================================================
# PATHS
# =============================================================================
ROOT = Path(__file__).resolve().parents[1]
ADVISORY_DIR = ROOT / "advisory-board"
OUT_DIR = ADVISORY_DIR / "outputs"
STATE_DIR = ADVISORY_DIR / "state"

# Input source paths
ACTIVE_TASKS = ROOT / "memory" / "active-tasks.md"
PIPELINE = ROOT / "jobs-bank" / "pipeline.md"
CONTENT_CALENDAR = ROOT / "memory" / "linkedin_content_calendar.md"
GOALS = ROOT / "GOALS.md"
MEMORY_DIR = ROOT / "memory"
JOBS_DIR = ROOT / "jobs-bank"
KNOWLEDGE_DIR = ROOT / "memory" / "knowledge"


# =============================================================================
# DATA STRUCTURES
# =============================================================================
@dataclass
class Change:
    """Represents a change detected since last run."""
    category: str  # NEW, CHANGED, RESOLVED, STALE
    item: str
    details: str
    domain: str
    evidence: str


@dataclass
class Signal:
    """A signal from any input source."""
    source: str
    domain: str  # career, brand, time, risk, financial, market
    title: str
    raw: str
    score: float = 0.0
    timestamp: dt.datetime | None = None


@dataclass
class DailyState:
    """Snapshot of current state for change detection."""
    date: str
    signals: list[Signal] = field(default_factory=list)
    pipeline_count: int = 0
    interview_count: int = 0
    active_tasks: int = 0
    content_scheduled: int = 0
    recruiters_responded: int = 0
    jobs_scouted: int = 0
    stale_sources: list[str] = field(default_factory=list)


# =============================================================================
# UTILITIES
# =============================================================================
def load_file(path: Path) -> str:
    """Load file contents, return empty string if missing."""
    try:
        if path.exists():
            return path.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""


def file_age_hours(path: Path) -> float | None:
    """Return file age in hours, or None if doesn't exist."""
    if not path.exists():
        return None
    try:
        age = dt.datetime.now() - dt.datetime.fromtimestamp(path.stat().st_mtime)
        return age.total_seconds() / 3600
    except Exception:
        return None


def find_recent_files(pattern: str, days: int = 3) -> list[Path]:
    """Find files matching pattern modified within last N days."""
    base = Path(pattern.replace("*", ""))
    if "*" not in pattern:
        return [base] if base.exists() else []
    
    # Get directory and glob
    parent = base.parent
    glob_pat = base.name
    cutoff = dt.datetime.now() - dt.timedelta(days=days)
    
    results = []
    try:
        for p in parent.glob(glob_pat):
            try:
                mtime = dt.datetime.fromtimestamp(p.stat().st_mtime)
                if mtime >= cutoff:
                    results.append(p)
            except Exception:
                continue
    except Exception:
        pass
    return sorted(results, key=lambda x: x.stat().st_mtime, reverse=True)


def parse_pipeline_status(line: str) -> dict | None:
    """Parse a pipeline markdown row."""
    if not line.startswith("|") or "| # |" in line or "---" in line:
        return None
    cols = [c.strip() for c in line.strip("|").split("|")]
    if len(cols) < 11:
        return None
    try:
        idx = int(cols[0])
    except ValueError:
        return None
    return {
        "idx": idx,
        "company": cols[2],
        "role": cols[3],
        "stage": cols[6],
        "follow_up": cols[9],
    }


def extract_dates(text: str) -> list[dt.date]:
    """Extract ISO dates from text."""
    dates = []
    for m in re.finditer(r"(\d{4}-\d{2}-\d{2})", text):
        try:
            dates.append(dt.date.fromisoformat(m.group(1)))
        except Exception:
            continue
    return dates


def count_pattern(text: str, pattern: str, case_insensitive: bool = True) -> int:
    """Count pattern occurrences in text."""
    flags = re.I if case_insensitive else 0
    return len(re.findall(pattern, text, flags))


# =============================================================================
# INPUT READERS
# =============================================================================
def read_active_tasks() -> list[Signal]:
    """Read current active tasks."""
    signals = []
    content = load_file(ACTIVE_TASKS)
    if not content:
        return signals
    
    for line in content.splitlines():
        s = line.strip()
        if not s.startswith("- "):
            continue
        # Skip resolved items
        if any(k in s.lower() for k in ["resolved", "completed", "~~", "✅"]):
            continue
        
        title = s[2:].strip()
        # Skip metadata lines
        if re.match(r"^(interviewer|status|position|outcome|resources|links)\s*:", title.lower()):
            continue
        
        # Domain detection
        domain = "career"
        if any(k in title.lower() for k in ["linkedin", "post", "content", "bio", "threads"]):
            domain = "brand"
        elif any(k in title.lower() for k in ["2fa", "jwt", "token expire", "credentials expire", "security"]):
            domain = "risk"
        
        signals.append(Signal(
            source="active-tasks",
            domain=domain,
            title=title,
            raw=line,
        ))
    return signals


def read_pipeline() -> tuple[list[Signal], int, int]:
    """Read job pipeline, return signals and counts."""
    signals = []
    content = load_file(PIPELINE)
    if not content:
        return signals, 0, 0
    
    total = 0
    interviews = 0
    for line in content.splitlines():
        parsed = parse_pipeline_status(line)
        if not parsed:
            continue
        
        total += 1
        stage = parsed["stage"]
        
        if "Interview" in stage:
            interviews += 1
            domain = "career"
            score = 9.0
        elif "Applied" in stage:
            domain = "career"
            score = 5.0
        elif "CV Ready" in stage:
            domain = "career"
            score = 4.0
        else:
            domain = "career"
            score = 3.0
        
        signals.append(Signal(
            source="pipeline",
            domain=domain,
            title=f"{parsed['company']}: {parsed['role']} [{stage}]",
            raw=line,
            score=score,
        ))
    
    return signals, total, interviews


def read_content_calendar() -> list[Signal]:
    """Read content calendar."""
    signals = []
    content = load_file(CONTENT_CALENDAR)
    if not content:
        return signals
    
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("- "):
            title = s[2:]
            # Check if scheduled for this week
            dates = extract_dates(title)
            today = dt.date.today()
            week_end = today + dt.timedelta(days=7)
            
            is_upcoming = any(d for d in dates if today <= d <= week_end) if dates else True
            
            signals.append(Signal(
                source="content-calendar",
                domain="brand",
                title=title,
                raw=line,
                score=6.0 if is_upcoming else 3.0,
            ))
    return signals


def read_goals() -> list[Signal]:
    """Read strategic goals."""
    signals = []
    content = load_file(GOALS)
    if not content:
        return signals
    
    in_section = False
    for line in content.splitlines():
        if line.strip().lower().startswith("## goals") or line.strip().lower().startswith("## priorities"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.strip().startswith("- "):
            title = line.strip()[2:]
            signals.append(Signal(
                source="goals",
                domain="strategic",
                title=title,
                raw=line,
                score=7.0,
            ))
    return signals


def read_dossiers() -> list[Signal]:
    """Read recent dossier activity."""
    dossiers_dir = JOBS_DIR / "dossiers"
    signals = []
    
    if not dossiers_dir.exists():
        return signals
    
    # Get recent dossier files
    for p in sorted(dossiers_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
        content = load_file(p)
        if not content:
            continue
        
        # Check for recent activity
        if "updated" in content.lower() or "reviewed" in content.lower():
            signals.append(Signal(
                source="dossiers",
                domain="career",
                title=f"Dossier: {p.stem}",
                raw=content[:200],
                score=5.0,
            ))
    return signals


def read_handoffs() -> list[Signal]:
    """Read pending review items from handoff directory."""
    handoff_dir = JOBS_DIR / "handoff"
    signals = []
    
    if not handoff_dir.exists():
        return signals
    
    for p in handoff_dir.glob("*.trigger"):
        content = load_file(p)
        if "NASR_REVIEW_NEEDED" in content:
            signals.append(Signal(
                source="handoff",
                domain="career",
                title=f"Review needed: {p.stem}",
                raw=content[:200],
                score=8.0,
            ))
    return signals


def read_recruiter_responses() -> list[Signal]:
    """Read recruiter response activity."""
    content = load_file(ROOT / "memory" / "recruiter-responses.md")
    signals = []
    if not content:
        return signals
    
    # Count responses
    response_count = count_pattern(content, "response|replied|contacted", case_insensitive=True)
    
    if response_count > 0:
        signals.append(Signal(
            source="recruiter-responses",
            domain="career",
            title=f"{response_count} recruiter interactions tracked",
            raw=content[:300],
            score=7.0,
        ))
    return signals


def read_job_scout() -> list[Signal]:
    """Read latest job scout results."""
    signals = []
    
    # Look for recent job scout files
    for p in find_recent_files(str(MEMORY_DIR / "linkedin-job-scout*.md"), days=3):
        content = load_file(p)
        if not content:
            continue
        
        # Extract job count
        job_count = len(re.findall(r"\|.*\|.*\|", content.splitlines()[2:10] if len(content.splitlines()) > 2 else []))
        
        signals.append(Signal(
            source="job-scout",
            domain="career",
            title=f"Job scout: {job_count} opportunities found",
            raw=content[:300],
            score=6.0,
        ))
    return signals


def read_job_hunter_weekly() -> list[Signal]:
    """Read latest job hunter weekly report."""
    signals = []
    
    for p in find_recent_files(str(MEMORY_DIR / "job-hunter-weekly*.md"), days=7):
        content = load_file(p)
        if not content:
            continue
        
        # Extract key metrics
        applied = count_pattern(content, "applied|application", case_insensitive=True)
        
        signals.append(Signal(
            source="job-hunter",
            domain="career",
            title=f"Job hunter weekly: {applied} applications tracked",
            raw=content[:300],
            score=6.0,
        ))
    return signals


def read_content_creator_weekly() -> list[Signal]:
    """Read latest content creator weekly report."""
    signals = []
    
    for p in find_recent_files(str(MEMORY_DIR / "content-creator-weekly*.md"), days=7):
        content = load_file(p)
        if not content:
            continue
        
        # Extract key metrics
        posts = count_pattern(content, "post|published", case_insensitive=True)
        
        signals.append(Signal(
            source="content-creator",
            domain="brand",
            title=f"Content weekly: {posts} posts tracked",
            raw=content[:300],
            score=5.0,
        ))
    return signals


def read_weekly_content_brief() -> list[Signal]:
    """Read weekly content intelligence brief."""
    signals = []
    path = KNOWLEDGE_DIR / "weekly-content-brief.md"
    content = load_file(path)
    
    if content:
        signals.append(Signal(
            source="content-brief",
            domain="brand",
            title="Weekly content intelligence available",
            raw=content[:300],
            score=5.0,
        ))
    return signals


def read_recent_logs() -> list[Signal]:
    """Read recent daily logs (last 3 days)."""
    signals = []
    today = dt.date.today()
    
    for i in range(3):
        check_date = today - dt.timedelta(days=i)
        log_path = MEMORY_DIR / f"{check_date.isoformat()}.md"
        
        if log_path.exists():
            content = load_file(log_path)
            if content:
                # Extract key events
                lines = content.splitlines()
                key_events = [l for l in lines if l.strip().startswith("- ") and any(k in l.lower() for k in ["completed", "started", "decided", "scheduled"])]
                
                for event in key_events[:3]:
                    signals.append(Signal(
                        source="daily-log",
                        domain="misc",
                        title=event.strip()[2:80],
                        raw=event,
                        score=4.0,
                    ))
    return signals


def get_stale_sources() -> list[str]:
    """Identify stale input sources."""
    stale = []
    sources = [
        ACTIVE_TASKS,
        PIPELINE,
        CONTENT_CALENDAR,
        GOALS,
    ]
    
    for s in sources:
        age = file_age_hours(s)
        if age is not None and age > 48:
            stale.append(f"{s.name} ({age:.0f}h old)")
    
    return stale


# =============================================================================
# CHANGE DETECTION
# =============================================================================
def load_previous_state() -> DailyState | None:
    """Load previous run state for change detection."""
    state_file = STATE_DIR / "latest_state.json"
    
    if not state_file.exists():
        return None
    
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        return DailyState(
            date=data.get("date", ""),
            pipeline_count=data.get("pipeline_count", 0),
            interview_count=data.get("interview_count", 0),
            active_tasks=data.get("active_tasks", 0),
            content_scheduled=data.get("content_scheduled", 0),
            recruiters_responded=data.get("recruiters_responded", 0),
            jobs_scouted=data.get("jobs_scouted", 0),
            stale_sources=data.get("stale_sources", []),
        )
    except Exception:
        return None


def save_current_state(state: DailyState) -> None:
    """Save current state for next run."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / "latest_state.json"
    
    data = {
        "date": state.date,
        "pipeline_count": state.pipeline_count,
        "interview_count": state.interview_count,
        "active_tasks": state.active_tasks,
        "content_scheduled": state.content_scheduled,
        "recruiters_responded": state.recruiters_responded,
        "jobs_scouted": state.jobs_scouted,
        "stale_sources": state.stale_sources,
    }
    
    state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def detect_changes(current: DailyState, previous: DailyState | None) -> list[Change]:
    """Detect what changed since last run."""
    changes = []
    
    if previous is None:
        # First run - treat everything as new
        if current.interview_count > 0:
            changes.append(Change(
                category="NEW",
                item=f"{current.interview_count} interview-stage opportunities",
                details="Interview-stage opportunities detected in pipeline",
                domain="career",
                evidence="pipeline analysis",
            ))
        if current.active_tasks > 0:
            changes.append(Change(
                category="NEW",
                item=f"{current.active_tasks} active tasks",
                details="Active tasks loaded from memory",
                domain="career",
                evidence="active-tasks.md",
            ))
        return changes
    
    # Pipeline changes
    if current.interview_count > previous.interview_count:
        diff = current.interview_count - previous.interview_count
        changes.append(Change(
            category="NEW",
            item=f"+{diff} interview-stage opportunities",
            details=f"Interview count: {previous.interview_count} → {current.interview_count}",
            domain="career",
            evidence="pipeline stage change",
        ))
    elif current.interview_count < previous.interview_count:
        diff = previous.interview_count - current.interview_count
        changes.append(Change(
            category="RESOLVED",
            item=f"{diff} interview threads resolved",
            details=f"Interview count: {previous.interview_count} → {current.interview_count}",
            domain="career",
            evidence="pipeline stage change",
        ))
    
    # Active task changes
    if abs(current.active_tasks - previous.active_tasks) >= 2:
        diff = current.active_tasks - previous.active_tasks
        cat = "NEW" if diff > 0 else "RESOLVED"
        changes.append(Change(
            category=cat,
            item=f"{abs(diff)} active tasks {'added' if diff > 0 else 'completed'}",
            details=f"Task count: {previous.active_tasks} → {current.active_tasks}",
            domain="career",
            evidence="active-tasks.md",
        ))
    
    # Content changes
    if current.content_scheduled > previous.content_scheduled:
        changes.append(Change(
            category="NEW",
            item="Content scheduled for this week",
            details=f"Content items: {previous.content_scheduled} → {current.content_scheduled}",
            domain="brand",
            evidence="content calendar",
        ))
    
    # Recruiter activity
    if current.recruiters_responded > previous.recruiters_responded:
        changes.append(Change(
            category="NEW",
            item="Recruiter response received",
            details="New recruiter interaction detected",
            domain="career",
            evidence="recruiter-responses.md",
        ))
    
    # Stale source warnings
    if current.stale_sources != previous.stale_sources:
        for s in current.stale_sources:
            if s not in previous.stale_sources:
                changes.append(Change(
                    category="STALE",
                    item=f"Stale source: {s}",
                    details="This source hasn't been updated recently",
                    domain="risk",
                    evidence="file age check",
                ))
    
    return changes


# =============================================================================
# CROSS-DOMAIN ANALYSIS
# =============================================================================
def cross_domain_connect(signals: list[Signal], changes: list[Change]) -> str:
    """Generate cross-domain insights linking multiple signals."""
    insights = []
    
    # Collect domains
    domains = {}
    for s in signals:
        domains[s.domain] = domains.get(s.domain, 0) + 1
    
    # Career + Brand connection
    if domains.get("career", 0) > 0 and domains.get("brand", 0) > 0:
        # Check for interview + content timing
        has_interview = any("interview" in s.title.lower() for s in signals)
        has_content = any("content" in s.title.lower() for s in signals)
        
        if has_interview and has_content:
            insights.append("Interview activity aligns with content push - good timing for LinkedIn visibility while momentum builds")
        elif has_interview:
            insights.append("Interview momentum detected - consider amplifying content to maximize visibility during active search")
    
    # Career + Risk connection
    if any(s.domain == "risk" for s in signals) and any(s.domain == "career" for s in signals):
        insights.append("Risk items (credentials/expiry) detected alongside career activity - prioritize security before outreach")
    
    # Time-based insight
    if len(signals) > 15:
        insights.append("High signal volume - prioritize ruthlessly, focus on top 3 only")
    
    # Change-based insight
    if changes:
        new_count = sum(1 for c in changes if c.category == "NEW")
        if new_count >= 3:
            insights.append(f"{new_count} new items detected - review priorities before executing")
    
    return insights[0] if insights else "No significant cross-domain patterns detected"


# =============================================================================
# DYNAMIC RECOMMENDATION
# =============================================================================
def generate_recommendation(changes: list[Change], signals: list[Signal], cross_domain: str) -> str:
    """Generate dynamic recommendation based on actual changes."""
    
    if not changes and not signals:
        return "No active signals. Refresh sources or add active tasks."
    
    # Priority 1: Interview-stage opportunities
    interview_signals = [s for s in signals if "interview" in s.title.lower()]
    if interview_signals:
        return f"Follow up on interview-stage opportunity first. {len(interview_signals)} active in pipeline."
    
    # Priority 2: Recruiter responses
    recruiter_changes = [c for c in changes if "recruit" in c.item.lower()]
    if recruiter_changes:
        return "Respond to recruiter immediately. Time-sensitive and high-impact."
    
    # Priority 3: Risk items
    risk_signals = [s for s in signals if s.domain == "risk"]
    if risk_signals:
        return f"Clear credential/expiry risk first. {risk_signals[0].title[:50]}"
    
    # Priority 4: New tasks
    new_changes = [c for c in changes if c.category == "NEW"]
    if new_changes:
        return f"Address {new_changes[0].item}. {new_changes[0].details}"
    
    # Priority 5: Cross-domain insight
    if cross_domain and cross_domain != "No significant cross-domain patterns detected":
        return cross_domain
    
    # Default
    return "Execute highest-scored task from active items. Protect focus time."


# =============================================================================
# OUTPUT BUILDERS
# =============================================================================
def build_daily_brief(changes: list[Change], signals: list[Signal], cross_domain: str, recommendation: str, date: str) -> str:
    """Build concise daily brief (max 15 lines)."""
    lines = [
        f"🎯 ADVISORY BOARD DAILY BRIEF — {date}",
        "",
        "WHAT CHANGED:",
    ]
    
    if not changes:
        lines.append("- No significant changes since last run")
    else:
        for c in changes[:4]:
            lines.append(f"- [{c.category}] {c.item}")
    
    lines.extend(["", "TOP 3 TODAY:"])
    
    # Get top 3 by score
    top_signals = sorted(signals, key=lambda s: s.score, reverse=True)[:3]
    for i, s in enumerate(top_signals, 1):
        lines.append(f"{i}. {s.title[:80]}")
    
    lines.extend(["", f"🔗 CONNECTION: {cross_domain}"])
    lines.extend(["", f"📌 DO THIS: {recommendation}"])
    
    return "\n".join(lines)


def build_weekly_report(changes: list[Change], signals: list[Signal], cross_domain: str, recommendation: str, week: str) -> str:
    """Build concise weekly report (max 25 lines)."""
    # Count movements
    new_count = sum(1 for c in changes if c.category == "NEW")
    resolved_count = sum(1 for c in changes if c.category == "RESOLVED")
    stale_count = sum(1 for c in changes if c.category == "STALE")
    
    # Pipeline stats
    career_signals = [s for s in signals if s.domain == "career"]
    interview_count = sum(1 for s in career_signals if "interview" in s.title.lower())
    
    # Content stats
    brand_signals = [s for s in signals if s.domain == "brand"]
    
    lines = [
        f"📊 WEEKLY STRATEGY REPORT — {week}",
        "",
        f"THIS WEEK'S MOVEMENT:",
        f"- {new_count} new, {resolved_count} resolved, {stale_count} stale items",
        "",
    ]
    
    # Risks and opportunities
    risk_signals = [s for s in signals if s.domain == "risk"]
    if risk_signals:
        lines.append(f"🔴 BIGGEST RISK: {risk_signals[0].title[:50]}")
    else:
        lines.append("🔴 BIGGEST RISK: None critical")
    
    # Opportunity
    if interview_count > 0:
        lines.append(f"🟢 BIGGEST OPPORTUNITY: {interview_count} interview-stage opportunities in pipeline")
    elif career_signals:
        lines.append(f"🟢 BIGGEST OPPORTUNITY: {len(career_signals)} active career items")
    else:
        lines.append("🟢 BIGGEST OPPORTUNITY: No active opportunities detected")
    
    lines.extend(["", "PIPELINE:"])
    lines.append(f"- {len(career_signals)} active, {interview_count} interviews")
    
    lines.extend(["", "CONTENT:"])
    if brand_signals:
        lines.append(f"- {len(brand_signals)} content items tracked")
    else:
        lines.append("- No content signals detected")
    
    lines.extend(["", f"🔗 PATTERNS: {cross_domain}"])
    
    lines.extend(["", "📌 TOP 3 NEXT WEEK:"])
    top_signals = sorted(signals, key=lambda s: s.score, reverse=True)[:3]
    for i, s in enumerate(top_signals, 1):
        lines.append(f"{i}. {s.title[:80]}")
    
    return "\n".join(lines)


# =============================================================================
# MAIN
# =============================================================================
def collect_all_signals() -> tuple[list[Signal], DailyState]:
    """Collect all signals from all input sources."""
    signals = []
    
    # Static sources
    signals.extend(read_active_tasks())
    pipeline_signals, pipeline_count, interview_count = read_pipeline()
    signals.extend(pipeline_signals)
    signals.extend(read_content_calendar())
    signals.extend(read_goals())
    
    # Dynamic sources
    signals.extend(read_dossiers())
    signals.extend(read_handoffs())
    signals.extend(read_recruiter_responses())
    signals.extend(read_job_scout())
    signals.extend(read_job_hunter_weekly())
    signals.extend(read_content_creator_weekly())
    signals.extend(read_weekly_content_brief())
    signals.extend(read_recent_logs())
    
    # Build current state
    state = DailyState(
        date=dt.date.today().isoformat(),
        signals=signals,
        pipeline_count=pipeline_count,
        interview_count=interview_count,
        active_tasks=len([s for s in signals if s.source == "active-tasks"]),
        content_scheduled=len([s for s in signals if s.source == "content-calendar"]),
        recruiters_responded=len([s for s in signals if s.source == "recruiter-responses"]),
        jobs_scouted=len([s for s in signals if s.source == "job-scout"]),
        stale_sources=get_stale_sources(),
    )
    
    return signals, state


def run(mode: str, target_date: dt.date | None = None) -> Path:
    """Run the advisory board engine."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    if target_date is None:
        target_date = dt.date.today()
    
    # Collect signals
    signals, current_state = collect_all_signals()
    
    # Load previous state
    previous_state = load_previous_state()
    
    # Detect changes
    changes = detect_changes(current_state, previous_state)
    
    # Generate cross-domain insight
    cross_domain = cross_domain_connect(signals, changes)
    
    # Generate recommendation
    recommendation = generate_recommendation(changes, signals, cross_domain)
    
    # Build output
    if mode == "daily":
        output = build_daily_brief(changes, signals, cross_domain, recommendation, target_date.isoformat())
        out_file = OUT_DIR / f"daily-brief-{target_date.isoformat()}.md"
    else:  # weekly
        iso = target_date.isocalendar()
        week_str = f"{iso[0]}-W{iso[1]:02d}"
        output = build_weekly_report(changes, signals, cross_domain, recommendation, week_str)
        out_file = OUT_DIR / f"weekly-report-{week_str}.md"
    
    # Save output
    out_file.write_text(output, encoding="utf-8")
    
    # Save state for change detection
    save_current_state(current_state)
    
    return out_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Advisory Board v3 Engine")
    parser.add_argument("--mode", choices=["daily", "weekly"], default="daily")
    parser.add_argument("--date", help="YYYY-MM-DD override")
    args = parser.parse_args()
    
    target = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    
    out = run(args.mode, target)
    print(str(out))
    
    # Also print the output
    print("\n" + "="*50)
    print(out.read_text(encoding="utf-8"))
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
