#!/usr/bin/env python3
"""
Simple keyword-based memory search - works without API keys
"""
import os
import json
import re
from pathlib import Path

MEMORY_DIR = "/root/.openclaw/workspace/memory"

def search_memory(query, max_results=5):
    """
    Keyword-based search across all memory files.
    Works without API keys.
    """
    results = []
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))
    
    # Find all .md files
    md_files = []
    for root, dirs, files in os.walk(MEMORY_DIR):
        for f in files:
            if f.endswith('.md'):
                md_files.append(os.path.join(root, f))
    
    # Search each file
    for filepath in md_files:
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                content_lower = content.lower()
                
                # Calculate relevance score
                matches = 0
                for word in query_words:
                    if len(word) > 2:
                        matches += content_lower.count(word) * len(word)
                
                if matches > 0:
                    # Get relevant excerpt
                    lines = content.split('\n')
                    excerpt_lines = []
                    for line in lines:
                        if query_lower in line.lower():
                            excerpt_lines.append(line.strip())
                        elif any(word in line.lower() for word in query_words if len(word) > 3):
                            excerpt_lines.append(line.strip())
                    
                    excerpt = '\n'.join(excerpt_lines[:3])[:500]
                    
                    results.append({
                        'file': filepath,
                        'score': matches,
                        'excerpt': excerpt
                    })
        except Exception as e:
            continue
    
    # Sort by score and return top results
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:max_results]

def get_memory_content(filepath, max_chars=1000):
    """Get content from a specific memory file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            return content[:max_chars]
    except Exception as e:
        return f"Error reading {filepath}: {e}"

# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python simple_memory_search.py <query>")
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    results = search_memory(query)
    
    if not results:
        print(f"No results found for: {query}")
    else:
        print(f"Found {len(results)} results for: {query}\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['file']} (score: {r['score']})")
            print(f"   {r['excerpt'][:200]}...")
            print()
