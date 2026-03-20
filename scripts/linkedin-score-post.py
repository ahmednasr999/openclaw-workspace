#!/usr/bin/env python3
"""
LinkedIn Post Scorer — Karpathy-style binary eval (10 questions).

Usage:
  python3 linkedin-score-post.py "POST TEXT HERE"
  python3 linkedin-score-post.py --file /path/to/post.txt
  python3 linkedin-score-post.py --json '{"content": "...", "date": "2026-03-20"}'
"""

import json
import re
import sys
import os
import subprocess
from datetime import date

WORKSPACE = "/root/.openclaw/workspace"
LOG_PATH = f"{WORKSPACE}/data/linkedin-research-log.json"
DEFAULT_MODEL = "MiniMax-M2.7"

# The 10 eval questions (indexed 0-9)
QUESTIONS = [
    "RESULT_TRANSFORMATION: Does the hook describe a RESULT or TRANSFORMATION (not just a topic)? Answer YES or NO.",
    "SPECIFIC_PERSON: Does the post feature a SPECIFIC PERSON or STORY (not just a company)? Answer YES or NO.",
    "SCROLL_STOPPER: Is the first line a SCROLL-STOPPER that creates a curiosity gap? Answer YES or NO.",
    "METRIC: Does the post include a specific METRIC or DATA POINT? Answer YES or NO.",
    "HOOK_LENGTH: Is the hook under 300 characters? Answer YES or NO.",
    "CTA: Does the post END WITH A QUESTION or CTA for engagement? Answer YES or NO.",
    "ACHIEVE_FRAME: Is the framing about WHAT YOU CAN ACHIEVE (not what the tool/company does)? Answer YES or NO.",
    "NOT_PRESS_RELEASE: Does it avoid sounding like a press release or changelog? Answer YES or NO.",
    "CONTEXT_RICH: Is it CONTEXT-RICH — does it explain WHY, not just WHAT? Answer YES or NO.",
    "URGENCY: Does it create a SENSE OF URGENCY or exclusivity? Answer YES or NO.",
]


def get_post_text():
    """Resolve post text from CLI args."""
    if "--file" in sys.argv:
        idx = sys.argv.index("--file")
        path = sys.argv[idx + 1]
        with open(path) as f:
            return f.read().strip()
    elif "--json" in sys.argv:
        idx = sys.argv.index("--json")
        data = json.loads(sys.argv[idx + 1])
        return data.get("content", "")
    elif len(sys.argv) > 1:
        return sys.argv[1]
    else:
        print("Usage: linkedin-score-post.py [--file path | --json '{}' | 'post text']")
        sys.exit(1)


def call_llm(prompt: str) -> str:
    """Call MiniMax-M2.7 via OpenAI-compatible API endpoint."""
    # Read API key from config
    cfg_path = f"{WORKSPACE}/config/models.json"
    if os.path.exists(cfg_path):
        cfg = json.load(open(cfg_path))
        api_key = cfg.get("minimax_api_key") or cfg.get("api_key")
        base_url = cfg.get("minimax_base_url", "https://api.minimax.chat/v1")
    else:
        api_key = os.environ.get("MINIMAX_API_KEY", "")
        base_url = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")

    if not api_key:
        # Fallback: try openai with known env
        api_key = os.environ.get("OPENAI_API_KEY", "")
        base_url = "https://api.openai.com/v1"

    payload = {
        "model": "MiniMax-M2.7",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 64,
        "temperature": 0.0,
    }
    import urllib.request, ssl
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            resp = json.loads(r.read())
            return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"ERROR: {e}"


def parse_answer(text: str) -> int:
    """Parse YES=1 / NO=0 from LLM response."""
    t = text.upper().strip()
    if "YES" in t and "NO" not in t:
        return 1
    if "NO" in t and "YES" not in t:
        return 0
    # Ambiguous — default to 0
    return 0


def score_post(post_text: str, prompt_version: int = 1, prompt_used: str = "") -> dict:
    """
    Run all 10 questions against the post text.
    Returns a dict with score, per-question results, and answers.
    """
    results = []
    raw_answers = []

    for i, question in enumerate(QUESTIONS):
        full_prompt = f"{question}\n\nPost to evaluate:\n{post_text[:2000]}"
        answer = call_llm(full_prompt)
        score = parse_answer(answer)
        results.append(score)
        raw_answers.append(answer)
        print(f"  Q{i+1:2d}: {question.split(':')[0]:20s} → {answer[:60]:60s} ({score})")

    total = sum(results)
    return {
        "total": total,
        "questions": results,
        "raw_answers": raw_answers,
        "prompt_version": prompt_version,
        "prompt_used": prompt_used,
    }


def get_current_prompt_version(log_path: str) -> tuple[int, str]:
    """Read current prompt version and text from log."""
    if os.path.exists(log_path):
        with open(log_path) as f:
            data = json.load(f)
        version = data.get("current_prompt_version", 1)
        current_prompt = data.get("current_prompt", "")
        return version, current_prompt
    return 1, ""


def log_result(log_path: str, post_text: str, result: dict, engagement: dict = None, post_url: str = ""):
    """Append scored post to the research log."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    if os.path.exists(log_path):
        with open(log_path) as f:
            data = json.load(f)
    else:
        data = {"posts": [], "current_prompt": "", "prompt_history": [], "current_prompt_version": 1}

    entry = {
        "date": date.today().isoformat(),
        "post_text": post_text[:5000],
        "eval_score": result["total"],
        "questions": result["questions"],
        "engagement": engagement,
        "prompt_version": result.get("prompt_version", data.get("current_prompt_version", 1)),
        "prompt_used": result.get("prompt_used", ""),
        "post_url": post_url or None,
    }
    data["posts"].append(entry)

    with open(log_path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nLogged to {log_path} | Score: {result['total']}/10")


# ── CLI ────────────────────────────────────────────────────────

if __name__ == "__main__":
    post_text = get_post_text()
    version, current_prompt = get_current_prompt_version(LOG_PATH)

    print(f"\n=== Scoring Post ({date.today()}) — Prompt v{version} ===")
    result = score_post(post_text, prompt_version=version, prompt_used=current_prompt)

    print(f"\n=== RESULT: {result['total']}/10 ===")
    for i, (q, a, s) in enumerate(zip(QUESTIONS, result["raw_answers"], result["questions"])):
        label = q.split(":")[0]
        print(f"  {i+1:2d}. [{s}] {label}: {a[:80]}")

    # Auto-log
    if "--no-log" not in sys.argv:
        log_result(LOG_PATH, post_text, result)

    print("\nDone.")
