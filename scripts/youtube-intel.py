#!/usr/bin/env python3
"""
YouTube Intelligence Pipeline — Extract, analyze, and extract job search value from YouTube transcripts.

Usage: python3 youtube-intel.py <youtube_url> [query]
Example: python3 youtube-intel.py "https://youtu.be/xxx" "GCC healthcare digital transformation"
"""

import sys
import os
import urllib.request
from datetime import datetime
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
OUTPUT_DIR = f"{WORKSPACE}/memory/youtube-intel"


def log(msg):
    print(f"[intel] {msg}")


def defuddle_fetch(url):
    """Fetch via Defuddle, fallback to Jina."""
    # Try Defuddle
    try:
        clean = url.replace("https://", "").replace("http://", "")
        req = urllib.request.Request(f"https://defuddle.md/{clean}", headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")
            if content and len(content) > 200:
                log(f"  Defuddle fetched {len(content)} chars")
                return content
    except Exception as e:
        log(f"  Defuddle error: {e}")
    
    # Fallback to Jina
    try:
        req = urllib.request.Request(f"https://r.jina.ai/{url}", headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")
            if content and len(content) > 200:
                log(f"  Jina fetched {len(content)} chars")
                return content
    except Exception as e:
        log(f"  Jina error: {e}")
    
    return ""


def extract_transcript(url):
    """Extract YouTube video content."""
    return defuddle_fetch(url)


def analyze_for_job_search(content, video_title, query=""):
    """Analyze transcript for job search value using LLM."""
    # Call LLM via gateway for analysis
    prompt = f"""You are an expert career coach and digital transformation executive. Analyze this YouTube transcript for job search value.

Video Title: {video_title}
Query/Context: {query}

Transcript (first 8000 chars):
{content[:8000]}

Analyze and return JSON with:
{{
    "summary": "What is this video about in 2 sentences",
    "key_insights": ["insight 1", "insight 2", "insight 3"],
    "skills_mentioned": ["skill 1", "skill 2"],
    "job_relevance": "HIGH/MEDIUM/LOW and why",
    "interview_angles": ["angle 1", "angle 2"],
    "positioning_opportunities": ["how Ahmed can position for this"],
    "recommendations": ["what Ahmed should do with this info"]
}}

Return ONLY valid JSON, no other text."""

    # Use call_llm pattern
    import json
    try:
        import urllib.request
        data = {
            "model": "anthropic/claude-sonnet-4-6",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1500
        }
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:18789/v1/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer local-dev"
            }
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        log(f"  LLM call failed: {e}")
        return None


def build_report(url, content, analysis):
    """Build intelligence report."""
    import re
    
    # Extract title from content
    title_match = re.search(r'title:\s*"([^"]+)"', content)
    title = title_match.group(1) if title_match else "Unknown"
    
    date = datetime.now().strftime("%Y-%m-%d")
    
    report = f"""# YouTube Intelligence Report — {date}

**Source:** {url}
**Title:** {title}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## Summary
{analysis.get('summary', 'See analysis below')}

---

## Key Insights
{chr(10).join(f"- {i}" for i in analysis.get('key_insights', []))}

---

## Skills Mentioned
{chr(10).join(f"- {s}" for s in analysis.get('skills_mentioned', []))}

---

## Job Relevance: {analysis.get('job_relevance', 'N/A')}
{analysis.get('job_relevance', 'See analysis')}

---

## Interview Angles
{chr(10).join(f"- {a}" for a in analysis.get('interview_angles', []))}

---

## Positioning Opportunities
{chr(10).join(f"- {p}" for p in analysis.get('positioning_opportunities', []))}

---

## Recommendations
{chr(10).join(f"- {r}" for r in analysis.get('recommendations', []))}

---

## Raw Transcript (first 2000 chars)
{content[:2000]}
"""
    
    return report


def main():
    if len(sys.argv) < 2:
        print("Usage: youtube-intel.py <youtube_url> [query/context]")
        sys.exit(1)
    
    url = sys.argv[1]
    query = sys.argv[2] if len(sys.argv) > 2 else ""
    
    log(f"Analyzing: {url}")
    log(f"Context: {query}")
    
    # Extract transcript
    content = extract_transcript(url)
    if not content:
        log("Failed to fetch content")
        sys.exit(1)
    
    # Extract title
    import re
    title_match = re.search(r'title:\s*"([^"]+)"', content)
    title = title_match.group(1) if title_match else "YouTube Video"
    
    log(f"Title: {title}")
    
    # Analyze
    log("Analyzing for job search value...")
    analysis_text = analyze_for_job_search(content, title, query)
    
    if not analysis_text:
        log("Analysis failed, saving raw content only")
        analysis_text = '{"summary": "Analysis unavailable", "error": "LLM call failed"}'
    
    # Parse analysis
    import json
    try:
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*\}', analysis_text, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            analysis = {"summary": analysis_text[:500]}
    except:
        analysis = {"summary": analysis_text[:500], "raw": analysis_text[:2000]}
    
    # Build and save report
    report = build_report(url, content, analysis)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    slug = url.split("/")[-1].split("?")[0][:30]
    filepath = f"{OUTPUT_DIR}/{date}-{slug}.md"
    date = datetime.now().strftime("%Y-%m-%d")
    filepath = f"{OUTPUT_DIR}/{date}-{slug}.md"
    Path(filepath).write_text(report)
    
    log(f"Report saved: {filepath}")
    log(f"Job Relevance: {analysis.get('job_relevance', 'N/A')}")
    
    # Print summary
    print("\n" + "="*50)
    print(f"VIDEO: {title}")
    print(f"RELEVANCE: {analysis.get('job_relevance', 'N/A')}")
    print("="*50)
    print(f"\nSUMMARY: {analysis.get('summary', 'N/A')}")
    print(f"\nKEY INSIGHTS:")
    for i in analysis.get('key_insights', [])[:3]:
        print(f"  • {i}")
    print(f"\nRECOMMENDATIONS:")
    for r in analysis.get('recommendations', [])[:3]:
        print(f"  → {r}")
    
    return {"relevance": analysis.get('job_relevance'), "filepath": filepath}


if __name__ == "__main__":
    main()
