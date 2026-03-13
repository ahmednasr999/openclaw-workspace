#!/usr/bin/env python3
"""
Quick CLI to log model usage
Usage:
  python3 log_usage.py claude-opus-4-6 anthropic "CV creation" 5000 2000
  python3 log_usage.py minimax-m2.1 minimax "chat" 1000 500
"""

import sys
from model_cost import log_usage, calculate_cost

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: log_usage.py <model> <provider> <task_type> [input_tokens] [output_tokens]")
        print("Example: log_usage.py claude-opus-4-6 anthropic CV_creation 5000 2000")
        sys.exit(1)
    
    model = sys.argv[1]
    provider = sys.argv[2]
    task_type = sys.argv[3]
    input_tokens = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    output_tokens = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    
    cost = log_usage(model, provider, task_type, input_tokens, output_tokens)
    print(f"✅ Logged: {model} ({provider}) — {task_type}")
    print(f"   Tokens: {input_tokens} in / {output_tokens} out")
    print(f"   Estimated cost: ${cost:.6f}")
