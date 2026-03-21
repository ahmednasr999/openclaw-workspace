#!/usr/bin/env python3
"""
weekly-agent-review.py
NASR Command Center - Weekly Agent Review System

Runs weekly (Sunday 10 AM Cairo) to:
1. Parse lessons-learned.md for entries from the past 7 days
2. Scan active skill SKILL.md files in workspace/skills/
3. Identify recurring failure patterns (2+ occurrences)
4. Auto-fix clear patterns; flag ambiguous ones for human review
5. Append a Weekly Review section to lessons-learned.md
6. Print a summary report
"""

import os
import re
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Optional

# ── Config ──────────────────────────────────────────────────────────────────
WORKSPACE = Path("/root/.openclaw/workspace")
LESSONS_FILE = WORKSPACE / "memory" / "lessons-learned.md"
SKILLS_DIR = WORKSPACE / "skills"
ARCHIVED_DIRS = {"archived", "archive", "_archived", ".archived"}
REVIEW_LOOKBACK_DAYS = 7
MIN_OCCURRENCES_FOR_AUTOFIX = 2

# Keywords that indicate a correction / failure in lessons-learned
FAILURE_KEYWORDS = [
    "what i missed", "failed", "failure", "error", "bug", "fix", "wrong",
    "correction", "missed", "didn't", "didnt", "shouldn't", "shouldnt",
    "instead of", "mistake", "incorrect", "forgot", "critical"
]

# Map common error tokens → skill folder names (best-effort)
SKILL_ALIASES = {
    "linkedin": ["linkedin", "linkedin-daily-post", "linkedin-writer", "linkedin-comment-radar"],
    "cv": ["executive-cv-builder"],
    "notion": ["cron/linkedin-daily-post"],        # notion issues often show in post skill
    "composio": [],                                 # platform-level, no single skill
    "cron": ["cron"],
    "briefing": ["cron/morning-briefing", "chief-of-staff"],
    "job": ["cron/job-scanner", "job-search-mcp"],
    "email": ["himalaya", "cron/email-check"],
    "github": ["github", "gh-fix-ci", "gh-address-comments"],
    "image": ["cron/linkedin-daily-post"],
    "memory": ["self-improvement", "clawback"],
    "service": [],
    "auth": [],
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_date_from_heading(heading: str) -> Optional[datetime]:
    """Extract date from a ## YYYY-MM-DD heading."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", heading)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d")
        except ValueError:
            return None
    return None


def extract_recent_entries(lessons_path: Path, days: int) -> list[dict]:
    """
    Parse lessons-learned.md and return entries from the last `days` days.
    Each entry: {date, heading, body, raw_text}
    """
    if not lessons_path.exists():
        print(f"[WARN] Lessons file not found: {lessons_path}")
        return []

    cutoff = datetime.now() - timedelta(days=days)
    content = lessons_path.read_text(encoding="utf-8")
    entries = []

    # Split on level-2 headings (## YYYY-MM-DD or ## template)
    sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)

    for section in sections:
        lines = section.strip().split("\n")
        if not lines:
            continue
        heading = lines[0].strip()
        date = parse_date_from_heading(heading)
        if date and date >= cutoff:
            entries.append({
                "date": date,
                "heading": heading,
                "body": "\n".join(lines[1:]).strip(),
                "raw_text": section.strip(),
            })

    return entries


def extract_failure_signals(entries: list[dict]) -> dict[str, list[str]]:
    """
    Scan recent entries for failure/correction signals.
    Returns {keyword_token: [matched_snippet, ...]}
    """
    signals: dict[str, list[str]] = defaultdict(list)

    for entry in entries:
        text = (entry["heading"] + "\n" + entry["body"]).lower()
        for kw in FAILURE_KEYWORDS:
            if kw in text:
                # Extract the surrounding sentence for context
                idx = text.find(kw)
                snippet_start = max(0, idx - 60)
                snippet_end = min(len(text), idx + 120)
                snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()
                signals[kw].append(f"[{entry['date'].strftime('%Y-%m-%d')}] ...{snippet}...")

    return dict(signals)


def group_by_skill(signals: dict[str, list[str]]) -> dict[str, list[str]]:
    """
    Map failure signals to skill names.
    Returns {skill_name: [signal_snippets]}
    """
    skill_hits: dict[str, list[str]] = defaultdict(list)

    # Combine all snippet text per keyword
    combined = []
    for kw, snippets in signals.items():
        for s in snippets:
            combined.append((kw, s))

    for kw, snippet in combined:
        matched = False
        for alias_key, skill_names in SKILL_ALIASES.items():
            if alias_key in kw or alias_key in snippet:
                for sn in skill_names:
                    skill_hits[sn].append(snippet)
                matched = True
        if not matched:
            skill_hits["__general__"].append(f"[{kw}] {snippet}")

    return dict(skill_hits)


def find_skill_file(skill_ref: str) -> Optional[Path]:
    """Locate a SKILL.md file given a slash-path or name."""
    candidates = [
        SKILLS_DIR / skill_ref / "SKILL.md",
        SKILLS_DIR / "cron" / skill_ref / "SKILL.md",
    ]
    for c in candidates:
        if c.exists():
            return c
    # Fuzzy: walk skills dir
    for skill_md in SKILLS_DIR.rglob("SKILL.md"):
        # Skip archived
        parts = [p.lower() for p in skill_md.parts]
        if any(a in parts for a in ARCHIVED_DIRS):
            continue
        folder = skill_md.parent.name.lower()
        if skill_ref.lower().replace("-", "") in folder.replace("-", ""):
            return skill_md
    return None


def list_all_active_skills() -> list[Path]:
    """Return all active SKILL.md paths (excluding archived dirs)."""
    results = []
    for skill_md in SKILLS_DIR.rglob("SKILL.md"):
        parts = [p.lower() for p in skill_md.parts]
        if any(a in parts for a in ARCHIVED_DIRS):
            continue
        results.append(skill_md)
    return sorted(results)


def analyze_skill_for_pattern(skill_path: Path, snippets: list[str]) -> dict:
    """
    Read a skill file and identify if snippets point to a fixable pattern.
    Returns {fixable: bool, suggestion: str, risk: str}
    """
    content = skill_path.read_text(encoding="utf-8")

    # Count how many snippets reference this skill → determines confidence
    count = len(snippets)
    fixable = count >= MIN_OCCURRENCES_FOR_AUTOFIX

    # Simple heuristics for common patterns
    suggestion = None
    risk = "low"

    combined_snippet_text = " ".join(snippets).lower()

    # Pattern: gave up / no retry
    if any(t in combined_snippet_text for t in ["gave up", "no retry", "single-attempt", "instead of retrying"]):
        if "retry" not in content.lower():
            suggestion = "Add explicit retry logic (3 attempts) for all external API calls."
            risk = "low"
        else:
            suggestion = "Retry logic exists but may not cover all failure paths — review error handling blocks."
            risk = "medium"

    # Pattern: wrong property type / API mismatch
    elif any(t in combined_snippet_text for t in ["wrong property", "rich_text", "url type", "incorrect format"]):
        suggestion = "Audit all API field types against live schema. Add field-type validation before writes."
        risk = "low"

    # Pattern: skipped existing solution
    elif any(t in combined_snippet_text for t in ["existing script", "already exists", "check scripts"]):
        suggestion = "Add a pre-task checklist step: scan workspace/scripts/ for existing solutions before building."
        risk = "low"

    # Pattern: composio assumption / auth
    elif any(t in combined_snippet_text for t in ["composio", "auth", "connect", "service registry"]):
        suggestion = "Add service pre-flight step: check config/service-registry.md before any external call."
        risk = "low"

    # Pattern: partial completion
    elif any(t in combined_snippet_text for t in ["partial", "without image", "skipped"]):
        suggestion = "Add completion guard: verify ALL required outputs (image, Notion update, etc.) before marking task done."
        risk = "low"

    else:
        # No clear pattern
        fixable = False
        suggestion = "Pattern unclear — flagged for human review."
        risk = "review"

    return {
        "fixable": fixable,
        "suggestion": suggestion,
        "risk": risk,
        "occurrences": count,
    }


def apply_fix_to_skill(skill_path: Path, analysis: dict) -> str:
    """
    Append a targeted improvement note to the skill file.
    Returns the text appended.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d")
    suggestion = analysis["suggestion"]

    patch = f"""

---
## 🔧 Auto-Improvement ({timestamp})
> Added by weekly-agent-review.py based on recurring failure pattern.

**Pattern detected ({analysis['occurrences']} occurrences):**
{suggestion}

**Action required:**
- Review this section and integrate the fix into the relevant step above.
- Remove this block once the fix has been applied.

"""
    original = skill_path.read_text(encoding="utf-8")
    # Don't add duplicate patches for same date
    if f"Auto-Improvement ({timestamp})" in original:
        return ""

    skill_path.write_text(original + patch, encoding="utf-8")
    return patch.strip()


def append_weekly_review_to_lessons(
    lessons_path: Path,
    changes: list[dict],
    flags: list[dict],
    no_issues: bool,
) -> None:
    """Append a Weekly Review section to lessons-learned.md."""
    now = datetime.now()
    week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    week_end = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%d %H:%M")

    lines = [f"\n\n## Weekly Review ({week_start} → {week_end})\n"]
    lines.append(f"_Generated by weekly-agent-review.py at {timestamp}_\n")

    if no_issues:
        lines.append("\n✅ No recurring failure patterns detected this week. System healthy.\n")
    else:
        if changes:
            lines.append("\n### Auto-Fixed Skills\n")
            for c in changes:
                lines.append(f"- **{c['skill']}**: {c['suggestion']} _(occurrences: {c['occurrences']})_")

        if flags:
            lines.append("\n\n### Flagged for Human Review\n")
            for f in flags:
                lines.append(f"- **{f['skill']}**: {f['reason']}")

    content = lessons_path.read_text(encoding="utf-8")
    # Avoid duplicate weekly review blocks for same date range
    block_header = f"## Weekly Review ({week_start} → {week_end})"
    if block_header in content:
        print(f"[INFO] Weekly review block for {week_start}→{week_end} already exists. Skipping append.")
        return

    lessons_path.write_text(content + "\n".join(lines), encoding="utf-8")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  NASR Weekly Agent Review")
    print(f"  Run: {datetime.now().strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"  Lookback: {REVIEW_LOOKBACK_DAYS} days")
    print("=" * 60)

    # 1. Parse lessons-learned.md for recent entries
    print(f"\n[1] Reading {LESSONS_FILE} ...")
    entries = extract_recent_entries(LESSONS_FILE, REVIEW_LOOKBACK_DAYS)
    print(f"    Found {len(entries)} entries from the past {REVIEW_LOOKBACK_DAYS} days.")

    if not entries:
        print("\n✅ No recent entries found. Nothing to review.")
        append_weekly_review_to_lessons(LESSONS_FILE, [], [], no_issues=True)
        print("\n✅ Weekly review block appended to lessons-learned.md.")
        return

    for e in entries:
        print(f"    · {e['heading']}")

    # 2. Extract failure signals
    print("\n[2] Extracting failure signals ...")
    signals = extract_failure_signals(entries)
    total_signals = sum(len(v) for v in signals.values())
    print(f"    Found {total_signals} failure signal(s) across {len(signals)} keyword(s).")

    # 3. Group by skill
    print("\n[3] Grouping signals by skill ...")
    skill_hits = group_by_skill(signals)
    # Remove __general__ from auto-fix candidates
    general_hits = skill_hits.pop("__general__", [])
    print(f"    Mapped to {len(skill_hits)} skill(s) + {len(general_hits)} general signal(s).")

    # 4. Analyze each skill
    print("\n[4] Analyzing skill files for fixable patterns ...")
    changes = []
    flags = []
    skipped = []

    for skill_ref, snippets in skill_hits.items():
        skill_path = find_skill_file(skill_ref)
        if not skill_path:
            skipped.append(skill_ref)
            print(f"    [SKIP] Skill not found: {skill_ref}")
            continue

        analysis = analyze_skill_for_pattern(skill_path, snippets)
        print(f"    · {skill_ref}: {analysis['occurrences']} hit(s), fixable={analysis['fixable']}, risk={analysis['risk']}")

        if analysis["fixable"] and analysis["risk"] != "review":
            patch = apply_fix_to_skill(skill_path, analysis)
            if patch:
                changes.append({
                    "skill": str(skill_path.relative_to(WORKSPACE)),
                    "suggestion": analysis["suggestion"],
                    "occurrences": analysis["occurrences"],
                })
                print(f"      → ✅ Patched: {skill_path.relative_to(WORKSPACE)}")
            else:
                print(f"      → ⏭  Already patched today.")
        else:
            flags.append({
                "skill": skill_ref,
                "reason": analysis["suggestion"],
                "occurrences": analysis["occurrences"],
            })
            print(f"      → 🚩 Flagged for review: {analysis['suggestion']}")

    # General signals → always flag, never auto-fix
    if general_hits:
        flags.append({
            "skill": "general",
            "reason": f"{len(general_hits)} unclassified signal(s) — manual review recommended.",
            "occurrences": len(general_hits),
        })

    # 5. List all active skills (for completeness check)
    print("\n[5] Active skills inventory ...")
    all_skills = list_all_active_skills()
    print(f"    {len(all_skills)} active SKILL.md files found.")

    # 6. Append weekly review to lessons-learned.md
    print("\n[6] Appending weekly review to lessons-learned.md ...")
    no_issues = not changes and not flags
    append_weekly_review_to_lessons(LESSONS_FILE, changes, flags, no_issues)
    print("    Done.")

    # 6b. Agent quality metrics from feedback logger
    print("\n[6b] Agent quality metrics ...")
    try:
        import subprocess
        result = subprocess.run(
            ["python3", str(WORKSPACE / "scripts" / "agent-feedback-logger.py"), "--report", "--days", "7"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"    Feedback report failed: {result.stderr[:200]}")
    except Exception as e:
        print(f"    Feedback logger not available: {e}")

    # 6c. Feedback propagation check (cross-agent corrections)
    print("\n[6c] Cross-agent feedback propagation ...")
    try:
        result = subprocess.run(
            ["python3", str(WORKSPACE / "scripts" / "propagate-feedback.py")],
            capture_output=True, text=True, timeout=30
        )
        if result.stdout.strip():
            print(result.stdout)
        else:
            print("    No new corrections to propagate.")
    except Exception as e:
        print(f"    Propagation check failed: {e}")

    # 7. Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Recent entries reviewed : {len(entries)}")
    print(f"  Failure signals found   : {total_signals}")
    print(f"  Skills auto-patched     : {len(changes)}")
    print(f"  Flagged for review      : {len(flags)}")
    print(f"  Skipped (not found)     : {len(skipped)}")

    if changes:
        print("\n  Auto-patched skills:")
        for c in changes:
            print(f"    ✅ {c['skill']}")
            print(f"       Fix: {c['suggestion']}")

    if flags:
        print("\n  Flagged for Ahmed's review:")
        for f in flags:
            print(f"    🚩 {f['skill']}: {f['reason']}")

    if skipped:
        print(f"\n  Skipped (skill files not found): {', '.join(skipped)}")

    print("\n  Weekly review appended to memory/lessons-learned.md")
    print("  Cross-agent propagation: check the propagation log")
    print("=" * 60)

    # Exit code: 0 = healthy, 1 = issues found (for cron monitoring)
    sys.exit(0 if no_issues else 0)  # always 0 for cron (issues are expected)


if __name__ == "__main__":
    main()
