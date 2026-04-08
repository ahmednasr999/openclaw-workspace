#!/usr/bin/env python3
"""
notebook-agent.py — Analyze YouTube videos using NotebookLM (free, uses Google's tokens).

Usage:
  python3 notebook-agent.py <YouTube_URL> [question]

Examples:
  python3 notebook-agent.py "https://www.youtube.com/watch?v=abc" "What are the key points?"
  python3 notebook-agent.py "https://www.youtube.com/watch?v=abc"  # Uses default question
"""

import subprocess
import sys
import re

NOTEBOOKLM = "/usr/local/bin/notebooklm"
DEFAULT_QUESTION = "Summarize this content. What are the key topics, tools, or concepts covered?"

def run(cmd, timeout=60):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {result.stderr}")
    return result.stdout

def get_or_create_notebook(name="YouTube Analysis"):
    output = run(f"{NOTEBOOKLM} list")
    for line in output.split("\n"):
        if name in line:
            match = re.search(r'([a-f0-9-]{36})', line)
            if match:
                return match.group(1)
    result = run(f"{NOTEBOOKLM} create '{name}'")
    match = re.search(r'Created notebook: ([a-f0-9-]{36})', result)
    if match:
        return match.group(1)
    raise RuntimeError("Could not create notebook")

def add_source_and_ask(notebook_id, url, question):
    run(f"{NOTEBOOKLM} use {notebook_id}")
    run(f"{NOTEBOOKLM} source add '{url}'", timeout=120)
    result = run(f"{NOTEBOOKLM} ask '{question}'", timeout=60)
    return result

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    url = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_QUESTION
    
    print(f"📹 Analyzing: {url}")
    print(f"❓ Question: {question}")
    
    notebook_id = get_or_create_notebook()
    print(f"📓 Using notebook: {notebook_id}")
    
    print("⏳ Adding source (YouTube)...")
    output = add_source_and_ask(notebook_id, url, question)
    print(output)

if __name__ == "__main__":
    main()
