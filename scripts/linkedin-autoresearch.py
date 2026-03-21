#!/usr/bin/env python3
"""
linkedin-autoresearch.py - Karpathy-style autoresearch loop for LinkedIn content.

Analyzes engagement data from linkedin-engagement-collector.py to find patterns,
then generates improved writing prompts to maximize engagement.

Loss function: avg_engagement per post
Target: increase avg_engagement by 2x over 30-day baseline

Flow:
1. Load engagement data
2. Analyze patterns (hook type, topic, length, time, format)
3. Generate insights
4. Create optimized prompt for LinkedIn Writer skill
5. Log results for next iteration

Runs: Weekly (Sundays) via cron, after engagement collector
"""
import json, re, sys, os
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
ENGAGEMENT_FILE = DATA_DIR / "linkedin-engagement.json"
AUTORESEARCH_DIR = DATA_DIR / "linkedin-autoresearch"
RESEARCH_LOG = AUTORESEARCH_DIR / "research-log.json"
PROMPT_DIR = AUTORESEARCH_DIR / "prompts"
CAIRO = timezone(timedelta(hours=2))

# LLM gateway
GATEWAY_URL = "http://127.0.0.1:18789/v1/chat/completions"
MODEL = "minimax-portal/MiniMax-M2.7"


def llm_call(prompt, max_tokens=2000):
    """Call LLM via gateway."""
    import requests
    
    # Load gateway auth token
    gw_token = ""
    try:
        with open("/root/.openclaw/openclaw.json") as f:
            cfg = json.load(f)
        gw_token = cfg.get("gateway", {}).get("auth", {}).get("token", "")
    except Exception:
        pass
    
    headers = {"Content-Type": "application/json"}
    if gw_token:
        headers["Authorization"] = f"Bearer {gw_token}"
    
    resp = requests.post(GATEWAY_URL, json={
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }, headers=headers, timeout=60)
    if resp.status_code != 200:
        print(f"LLM error: {resp.status_code}")
        return ""
    return resp.json()["choices"][0]["message"]["content"]


def analyze_patterns(posts):
    """Analyze engagement patterns using LLM."""
    # Prepare post data for LLM
    post_summaries = []
    for i, p in enumerate(sorted(posts, key=lambda x: x["engagement"], reverse=True)):
        title = p.get("title", p.get("text_preview", "?"))[:80]
        hook_type = classify_hook(title)
        post_summaries.append({
            "rank": i + 1,
            "engagement": p["engagement"],
            "reactions": p["reactions"],
            "comments": p["comments"],
            "title": title,
            "hook_type": hook_type,
            "topic": p.get("topic", ""),
            "text_length": len(p.get("text_preview", "")),
        })
    
    prompt = f"""Analyze these LinkedIn post engagement patterns. Posts are ranked by total engagement (reactions + comments).

DATA:
{json.dumps(post_summaries, indent=2)}

Analyze and return a JSON object with these fields:
{{
  "top_patterns": ["list of 3-5 patterns that HIGH engagement posts share"],
  "bottom_patterns": ["list of 3-5 patterns that LOW engagement posts share"],
  "hook_analysis": "which hook types (story, statistic, question, bold claim, personal) get most engagement",
  "topic_analysis": "which topics resonate most",
  "length_insight": "optimal length observation",
  "actionable_rules": ["5-7 specific writing rules derived from the data"],
  "avoid": ["3-5 things to avoid based on low performers"]
}}

Return ONLY the JSON object, no other text."""

    response = llm_call(prompt, max_tokens=1500)
    
    # Parse JSON
    try:
        # Find JSON in response
        match = re.search(r'\{[\s\S]+\}', response)
        if match:
            return json.loads(match.group())
    except:
        pass
    
    return {"error": "Failed to parse LLM response", "raw": response[:500]}


def classify_hook(text):
    """Classify the hook type of a post."""
    text = text.lower()
    if any(w in text for w in ["i ", "my ", "me "]):
        if any(w in text for w in ["built", "learned", "taught", "scaled", "managed"]):
            return "personal_story"
    if "?" in text:
        return "question"
    if re.search(r'\d+[%xX]|\$\d+|million|billion', text):
        return "statistic"
    if any(w in text for w in ["never", "always", "most", "every", "no one"]):
        return "bold_claim"
    if any(w in text for w in ["just", "breaking", "announced"]):
        return "news"
    if any(w in text for w in ["hiring", "looking for"]):
        return "hiring"
    return "insight"


def generate_optimized_prompt(analysis, iteration):
    """Generate an optimized writing prompt based on patterns."""
    prompt = f"""Based on this LinkedIn engagement analysis, create an optimized writing prompt for an AI assistant that writes LinkedIn posts.

ANALYSIS:
{json.dumps(analysis, indent=2)}

Create a detailed writing prompt that:
1. Incorporates the top-performing patterns
2. Avoids the low-performing patterns
3. Includes specific rules for hooks, structure, and topics
4. Targets the same audience (tech executives, PMO professionals, AI/digital transformation leaders)
5. The author is Ahmed Nasr - PMO & Regional Engagement Lead, 20+ years tech leadership

The prompt should be ready to use as system instructions for a LinkedIn post writer.
Keep it under 800 words. Be specific and actionable, not generic.

Return the prompt text only, no meta-commentary."""

    return llm_call(prompt, max_tokens=2000)


def main():
    AUTORESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=== LinkedIn Autoresearch Loop ===")
    print(f"Time: {datetime.now(CAIRO).strftime('%Y-%m-%d %H:%M')}")
    
    # Load engagement data
    if not ENGAGEMENT_FILE.exists():
        print("ERROR: No engagement data. Run linkedin-engagement-collector.py first.")
        sys.exit(1)
    
    data = json.load(open(ENGAGEMENT_FILE))
    posts = data.get("posts", [])
    
    if len(posts) < 5:
        print(f"ERROR: Only {len(posts)} posts. Need at least 5 for analysis.")
        sys.exit(1)
    
    print(f"Loaded {len(posts)} posts (avg engagement: {data['analysis']['avg_engagement']})")
    
    # Load previous research log
    log = {"iterations": [], "best_avg_engagement": 0}
    if RESEARCH_LOG.exists():
        log = json.load(open(RESEARCH_LOG))
    
    iteration = len(log["iterations"]) + 1
    print(f"\n--- Iteration {iteration} ---")
    
    # Step 1: Analyze patterns
    print("Analyzing patterns...")
    analysis = analyze_patterns(posts)
    
    if "error" in analysis:
        print(f"Analysis error: {analysis['error']}")
        # Still continue with basic analysis
        analysis = {
            "top_patterns": ["Posts with personal stories get higher engagement"],
            "bottom_patterns": ["Generic posts without personal angle get low engagement"],
            "actionable_rules": ["Start with personal story", "Include specific numbers", "End with question"],
            "avoid": ["Generic hooks", "Pure hiring posts"]
        }
    
    print(f"Patterns found: {len(analysis.get('actionable_rules', []))}")
    
    # Step 2: Generate optimized prompt
    print("Generating optimized prompt...")
    optimized_prompt = generate_optimized_prompt(analysis, iteration)
    
    if not optimized_prompt or len(optimized_prompt) < 100:
        print("ERROR: Failed to generate prompt")
        sys.exit(1)
    
    # Step 3: Save prompt
    prompt_file = PROMPT_DIR / f"linkedin-writer-v{iteration}.md"
    with open(prompt_file, "w") as f:
        f.write(f"# LinkedIn Writer Prompt v{iteration}\n")
        f.write(f"# Generated: {datetime.now(CAIRO).isoformat()}\n")
        f.write(f"# Based on {len(posts)} posts, avg engagement: {data['analysis']['avg_engagement']}\n\n")
        f.write(optimized_prompt)
    print(f"Prompt saved: {prompt_file}")
    
    # Step 4: Log iteration
    iteration_data = {
        "iteration": iteration,
        "timestamp": datetime.now(CAIRO).isoformat(),
        "post_count": len(posts),
        "avg_engagement": data["analysis"]["avg_engagement"],
        "max_engagement": data["analysis"]["max_engagement"],
        "analysis_summary": {
            "top_patterns": analysis.get("top_patterns", [])[:3],
            "actionable_rules": analysis.get("actionable_rules", [])[:5],
        },
        "prompt_file": str(prompt_file),
    }
    
    log["iterations"].append(iteration_data)
    log["best_avg_engagement"] = max(log.get("best_avg_engagement", 0), data["analysis"]["avg_engagement"])
    log["last_updated"] = datetime.now(CAIRO).isoformat()
    
    with open(RESEARCH_LOG, "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    
    # Print results
    print(f"\n=== Results ===")
    print(f"Iteration: {iteration}")
    print(f"Posts analyzed: {len(posts)}")
    print(f"Avg engagement: {data['analysis']['avg_engagement']}")
    print(f"Top patterns:")
    for rule in analysis.get("actionable_rules", [])[:5]:
        print(f"  - {rule}")
    print(f"\nOptimized prompt: {prompt_file}")
    print(f"Prompt length: {len(optimized_prompt)} chars")
    
    return iteration_data


if __name__ == "__main__":
    main()
