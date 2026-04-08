#!/usr/bin/env python3
"""
LinkedIn Prompt Improver — Karpathy-style correlation analysis.

Reads data/linkedin-research-log.json, identifies winners and losers,
finds which eval questions best predict engagement, and generates an
improved prompt. Logs the new version to prompt_history.

Usage:
  python3 scripts/linkedin-improve-prompt.py
  python3 scripts/linkedin-improve-prompt.py --min-engagement 20   # likes+comments threshold
"""

import json
import os
import sys
import re
from datetime import date
from collections import defaultdict

WORKSPACE = "/root/.openclaw/workspace"
LOG_PATH = f"{WORKSPACE}/data/linkedin-research-log.json"

# Minimum combined engagement to call a post a "winner"
DEFAULT_MIN_ENGAGEMENT = 20  # likes + comments + shares


def load_log():
    with open(LOG_PATH) as f:
        return json.load(f)


def compute_engagement(post):
    """Return total engagement score. None engagement → exclude from winner/loser analysis."""
    e = post.get("engagement")
    if e is None:
        return None
    return e.get("likes", 0) + e.get("comments", 0) + e.get("shares", 0)


def is_winner(post, min_engagement):
    """Winner: eval_score >= 7 AND above min_engagement threshold."""
    e = compute_engagement(post)
    if e is None:
        return False
    return post.get("eval_score", 0) >= 7 and e >= min_engagement


def is_loser(post, min_engagement):
    """Loser: scored well (>=7) but engagement below threshold = eval problem.
       OR scored poorly (<7) regardless of engagement."""
    score = post.get("eval_score", 0)
    e = compute_engagement(post)
    if score >= 7:
        # High score, low engagement → eval failed to predict quality
        return e is not None and e < min_engagement
    else:
        # Low score → obvious loser
        return True


def analyze_correlations(posts, min_engagement):
    """
    For each of the 10 questions, compute:
    - win_rate: % of winners who answered YES
    - lose_rate: % of losers who answered YES
    - correlation: win_rate - lose_rate (higher = more predictive)
    """
    winners = [p for p in posts if is_winner(p, min_engagement)]
    losers = [p for p in posts if is_loser(p, min_engagement)]

    print(f"\nPosts with engagement data: {sum(1 for p in posts if compute_engagement(p) is not None)}")
    print(f"Winners (score>=7, engagement>={min_engagement}): {len(winners)}")
    print(f"Losers: {len(losers)}")

    if len(winners) < 2 or len(losers) < 1:
        print("Not enough winner/loser data to generate improvements. Need ≥2 winners and ≥1 loser.")
        return None, winners, losers

    question_labels = [
        "RESULT_TRANSFORMATION", "SPECIFIC_PERSON", "SCROLL_STOPPER", "METRIC",
        "HOOK_LENGTH", "CTA", "ACHIEVE_FRAME", "NOT_PRESS_RELEASE",
        "CONTEXT_RICH", "URGENCY"
    ]

    correlations = []
    for q_idx in range(10):
        win_yes = sum(1 for p in winners if p.get("questions", [0])[q_idx] == 1)
        lose_yes = sum(1 for p in losers if p.get("questions", [0])[q_idx] == 1)
        win_rate = win_yes / len(winners)
        lose_rate = lose_yes / len(losers) if losers else 0
        corr = win_rate - lose_rate
        correlations.append({
            "question": question_labels[q_idx],
            "q_index": q_idx,
            "win_rate": round(win_rate, 3),
            "lose_rate": round(lose_rate, 3),
            "correlation": round(corr, 3),
        })

    correlations.sort(key=lambda x: x["correlation"], reverse=True)
    return correlations, winners, losers


def generate_improved_prompt(current_prompt, correlations, winners, losers):
    """
    Build an improved prompt by:
    1. Keeping everything that works (high win_rate on winners)
    2. Emphasizing questions with positive correlation (winners > losers)
    3. Flagging questions with negative or zero correlation as de-emphasized
    """
    question_descriptions = {
        "RESULT_TRANSFORMATION": "The hook MUST describe a concrete result or transformation, not a topic.",
        "SPECIFIC_PERSON": "Include a specific person's story or case study, not just company names.",
        "SCROLL_STOPPER": "First line MUST create a curiosity gap — make the reader stop scrolling.",
        "METRIC": "Include at least one specific metric or data point.",
        "HOOK_LENGTH": "Keep the hook under 300 characters.",
        "CTA": "End with a direct question or call-to-action to drive engagement.",
        "ACHIEVE_FRAME": "Frame around what the READER can achieve, not what your tool/company does.",
        "NOT_PRESS_RELEASE": "Avoid press-release or changelog language — sound like a human, not a PR team.",
        "CONTEXT_RICH": "Explain the WHY behind the WHAT — context matters.",
        "URGENCY": "Create a sense of urgency or exclusivity in the hook.",
    }

    high_corr = [c for c in correlations if c["correlation"] >= 0.2]
    low_corr = [c for c in correlations if c["correlation"] <= -0.1]
    neutral = [c for c in correlations if -0.1 < c["correlation"] < 0.2]

    improvements = []
    if high_corr:
        improvements.append("EMPHASIZE (positive correlation):")
        for c in high_corr:
            improvements.append(f"  - {c['question']}: win_rate={c['win_rate']}, corr=+{c['correlation']}")

    if low_corr:
        improvements.append("\nDE-EMPHASIZE (negative correlation — winners skip these):")
        for c in low_corr:
            improvements.append(f"  - {c['question']}: win_rate={c['win_rate']}, corr={c['correlation']}")

    if neutral:
        improvements.append("\nMAINTAIN:")
        for c in neutral:
            improvements.append(f"  - {c['question']}: win_rate={c['win_rate']}, corr={c['correlation']}")

    # Build new prompt
    new_lines = ["LinkedIn Post Writing Prompt (Auto-improved)", ""]
    new_lines.append("CORE REQUIREMENTS:")
    for c in correlations:
        label = c["question"]
        desc = question_descriptions[label]
        if c["correlation"] >= 0.2:
            new_lines.append(f"  ★ {desc}")
        elif c["correlation"] <= -0.1:
            new_lines.append(f"  ○ {desc} [review carefully — may not apply to this audience]")
        else:
            new_lines.append(f"  · {desc}")

    new_lines.append("")
    new_lines.append("PATTERN ANALYSIS (from past posts):")
    new_lines += improvements

    if winners:
        top_winners = sorted(winners, key=lambda p: compute_engagement_static(p), reverse=True)[:3]
        new_lines.append("")
        new_lines.append("TOP PERFORMING POSTS (for style reference):")
        for w in top_winners:
            new_lines.append(f"  Score {w['eval_score']}/10, engagement={compute_engagement_static(w)}:")
            new_lines.append(f"    {w['post_text'][:200]}...")

    new_prompt = "\n".join(new_lines)
    return new_prompt, "\n".join(improvements)


def compute_engagement_static(post):
    e = post.get("engagement")
    if e is None:
        return 0
    return e.get("likes", 0) + e.get("comments", 0) + e.get("shares", 0)


def main():
    min_engagement = DEFAULT_MIN_ENGAGEMENT
    if "--min-engagement" in sys.argv:
        idx = sys.argv.index("--min-engagement")
        min_engagement = int(sys.argv[idx + 1])

    if not os.path.exists(LOG_PATH):
        print(f"Log not found: {LOG_PATH}")
        sys.exit(1)

    data = load_log()
    posts = data.get("posts", [])

    if not posts:
        print("No posts in research log yet. Post something first!")
        sys.exit(1)

    posts_with_engagement = [p for p in posts if compute_engagement(p) is not None]
    print(f"=== LinkedIn Prompt Improver ===")
    print(f"Total posts logged: {len(posts)}")
    print(f"Posts with engagement data: {len(posts_with_engagement)}")
    print(f"Min engagement threshold: {min_engagement}")

    correlations, winners, losers = analyze_correlations(posts, min_engagement)

    if correlations is None:
        # Not enough data — just print current stats
        print("\nCurrent prompt version:", data.get("current_prompt_version", 1))
        print("Prompt history entries:", len(data.get("prompt_history", [])))
        sys.exit(0)

    print("\n=== Correlation Analysis ===")
    for c in correlations:
        star = "★" if c["correlation"] >= 0.2 else ("✗" if c["correlation"] <= -0.1 else " ")
        print(f"  {star} {c['question']:25s} win={c['win_rate']:.0%} lose={c['lose_rate']:.0%} corr={c['correlation']:+.2f}")

    current_version = data.get("current_prompt_version", 1)
    current_prompt = data.get("current_prompt", "")
    new_prompt, improvements_text = generate_improved_prompt(current_prompt, correlations, winners, losers)
    new_version = current_version + 1

    print(f"\n=== Suggested Prompt v{new_version} ===")
    print(new_prompt[:1000])

    # Decide whether to auto-upgrade or just show
    auto_apply = "--apply" in sys.argv
    if auto_apply:
        data["current_prompt"] = new_prompt
        data["current_prompt_version"] = new_version
        data["prompt_history"].append({
            "version": new_version,
            "prompt": new_prompt,
            "date": date.today().isoformat(),
            "reason": improvements_text[:500],
            "winners_count": len(winners),
            "losers_count": len(losers),
        })
        with open(LOG_PATH, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Applied prompt v{new_version} to {LOG_PATH}")
    else:
        print(f"\n[Not applied — run with --apply to save]")
        print(f"\nTo apply: python3 scripts/linkedin-improve-prompt.py --apply")


if __name__ == "__main__":
    main()
