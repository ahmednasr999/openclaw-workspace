#!/usr/bin/env python3
"""Log agent session costs to Notion Cost Tracker DB.
Usage: python3 cost_logger.py --session "Morning Briefing" --model "MiniMax-M2.5" --agent "Morning Briefing" --duration 34 --status success
"""
import json, os, sys, time, urllib.request, argparse

def get_token():
    with open("/root/.openclaw/workspace/config/notion.json") as f:
        return json.load(f).get("token", "")

def notion_api(method, url, data=None, token=None):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

# Model cost per 1M tokens (input/output)
MODEL_COSTS = {
    "MiniMax-M2.5": {"in": 0.0, "out": 0.0},
    "minimax-portal/MiniMax-M2.5": {"in": 0.0, "out": 0.0},
    "minimax-m2.5": {"in": 0.0, "out": 0.0},
    "Claude Opus 4.6": {"in": 15.0, "out": 75.0},
    "anthropic/claude-opus-4-6": {"in": 15.0, "out": 75.0},
    "opus": {"in": 15.0, "out": 75.0},
    "Claude Sonnet 4": {"in": 3.0, "out": 15.0},
    "anthropic/claude-sonnet-4": {"in": 3.0, "out": 15.0},
    "sonnet": {"in": 3.0, "out": 15.0},
    "Kimi K2.5": {"in": 1.0, "out": 5.0},
    "moonshot/kimi-k2.5": {"in": 1.0, "out": 5.0},
}

COST_DB = "3278d599-a162-81a3-a593-f981f1e9a7af"

def estimate_cost(model, tokens_in=0, tokens_out=0):
    costs = MODEL_COSTS.get(model, {"in": 0, "out": 0})
    return (tokens_in * costs["in"] + tokens_out * costs["out"]) / 1_000_000

def normalize_model(model):
    mapping = {
        "minimax-portal/MiniMax-M2.5": "MiniMax-M2.5",
        "minimax-m2.5": "MiniMax-M2.5",
        "anthropic/claude-opus-4-6": "Claude Opus 4.6",
        "opus": "Claude Opus 4.6",
        "anthropic/claude-sonnet-4": "Claude Sonnet 4",
        "sonnet": "Claude Sonnet 4",
        "anthropic/claude-sonnet-4-6": "Claude Sonnet 4",
        "moonshot/kimi-k2.5": "Kimi K2.5",
    }
    return mapping.get(model, model)

def log_cost(session_name, model, agent, duration=0, status="success",
             tokens_in=0, tokens_out=0, notes=""):
    token = get_token()
    model_display = normalize_model(model)
    cost = estimate_cost(model, tokens_in, tokens_out)
    status_map = {"success": "✅ Completed", "failed": "❌ Failed", "running": "⏳ Running"}
    
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    props = {
        "Session": {"title": [{"text": {"content": session_name}}]},
        "Model": {"select": {"name": model_display}},
        "Agent": {"select": {"name": agent}},
        "Duration (s)": {"number": duration},
        "Status": {"select": {"name": status_map.get(status, "✅ Completed")}},
        "Est. Cost ($)": {"number": round(cost, 4)},
        "Tokens In": {"number": tokens_in},
        "Tokens Out": {"number": tokens_out},
        "Date": {"date": {"start": today}},
    }
    if notes:
        props["Notes"] = {"rich_text": [{"text": {"content": notes[:2000]}}]}
    
    notion_api("POST", "https://api.notion.com/v1/pages", {
        "parent": {"database_id": COST_DB},
        "properties": props
    }, token=token)
    print(f"💰 Logged: {session_name} | {model_display} | ${cost:.4f} | {duration}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True)
    parser.add_argument("--model", default="MiniMax-M2.5")
    parser.add_argument("--agent", default="Manual Session")
    parser.add_argument("--duration", type=int, default=0)
    parser.add_argument("--status", default="success")
    parser.add_argument("--tokens-in", type=int, default=0)
    parser.add_argument("--tokens-out", type=int, default=0)
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    log_cost(args.session, args.model, args.agent, args.duration, 
             args.status, args.tokens_in, args.tokens_out, args.notes)
