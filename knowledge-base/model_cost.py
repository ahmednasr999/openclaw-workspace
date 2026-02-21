#!/usr/bin/env python3
"""
Model Cost Tracker
Tracks API usage across Claude, MiniMax, Kimi and estimates costs
"""

import sqlite3, json, os, subprocess
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = "/root/.openclaw/workspace/knowledge-base/kb.db"

# Pricing (approximate - verify with providers)
# Claude: $15/M input, $75/M output (Opus), $3/M input, $15/M output (Sonnet)
# MiniMax: ~$0.001/1K tokens (varies by model)
# Kimi: ~$0.001/1K tokens

PRICING = {
    # Claude Opus 4.6
    "claude-opus-4-6": {"input": 0.015, "output": 0.075, "unit": "M tokens"},
    "claude-opus-4-5": {"input": 0.015, "output": 0.075, "unit": "M tokens"},
    "claude-opus-4": {"input": 0.015, "output": 0.075, "unit": "M tokens"},
    # Claude Sonnet 4.6
    "claude-sonnet-4-6": {"input": 0.003, "output": 0.015, "unit": "M tokens"},
    "claude-sonnet-4": {"input": 0.003, "output": 0.015, "unit": "M tokens"},
    # MiniMax (per 1K tokens)
    "minimax-m2.1": {"input": 0.001, "output": 0.001, "unit": "K tokens"},
    "minimax-m2.5": {"input": 0.001, "output": 0.001, "unit": "K tokens"},
    "MiniMax-M2.1": {"input": 0.001, "output": 0.001, "unit": "K tokens"},
    "MiniMax-M2.5": {"input": 0.001, "output": 0.001, "unit": "K tokens"},
    # Kimi
    "kimi-k2.5": {"input": 0.001, "output": 0.001, "unit": "K tokens"},
}

# Fallback pricing for unknown models
DEFAULT_PRICING = {"input": 0.001, "output": 0.001, "unit": "K tokens"}

def get_model_pricing(model):
    """Get pricing for a model"""
    model_lower = model.lower() if model else ""
    for key, pricing in PRICING.items():
        if key.lower() in model_lower or model_lower in key.lower():
            return pricing
    return DEFAULT_PRICING

def init_db():
    """Initialize the cost tracking database"""
    conn = sqlite3.connect(DB_PATH)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS model_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            model TEXT,
            provider TEXT,
            task_type TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            estimated_cost REAL DEFAULT 0,
            session_key TEXT,
            notes TEXT
        )
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON model_usage(timestamp)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_usage_model ON model_usage(model)
    """)
    
    conn.commit()
    conn.close()

def calculate_cost(model, input_tokens, output_tokens):
    """Calculate estimated cost for a request"""
    pricing = get_model_pricing(model)
    
    if pricing["unit"] == "M tokens":
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
    else:  # K tokens
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
    
    return round(input_cost + output_cost, 6)

def log_usage(model, provider, task_type, input_tokens, output_tokens, session_key=None, notes=None):
    """Log an API call"""
    conn = sqlite3.connect(DB_PATH)
    
    cost = calculate_cost(model, input_tokens, output_tokens)
    
    conn.execute("""
        INSERT INTO model_usage (model, provider, task_type, input_tokens, output_tokens, estimated_cost, session_key, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (model, provider, task_type, input_tokens, output_tokens, cost, session_key, notes))
    
    conn.commit()
    conn.close()
    return cost

def get_summary(period="week"):
    """Get usage summary for a period"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    if period == "day":
        filter_sql = "WHERE timestamp >= datetime('now', '-1 day')"
    elif period == "week":
        filter_sql = "WHERE timestamp >= datetime('now', '-7 days')"
    elif period == "month":
        filter_sql = "WHERE timestamp >= datetime('now', '-30 days')"
    else:
        filter_sql = ""
    
    # Total cost
    total = conn.execute(f"""
        SELECT SUM(estimated_cost) as total FROM model_usage {filter_sql}
    """).fetchone()["total"] or 0
    
    # By provider
    by_provider = conn.execute(f"""
        SELECT provider, 
               SUM(input_tokens) as input, 
               SUM(output_tokens) as output,
               SUM(estimated_cost) as cost
        FROM model_usage {filter_sql}
        GROUP BY provider
    """).fetchall()
    
    # By model
    by_model = conn.execute(f"""
        SELECT model, 
               provider,
               SUM(input_tokens) as input, 
               SUM(output_tokens) as output,
               SUM(estimated_cost) as cost,
               COUNT(*) as requests
        FROM model_usage {filter_sql}
        GROUP BY model
        ORDER BY cost DESC
    """).fetchall()
    
    # By task type
    by_task = conn.execute(f"""
        SELECT task_type,
               SUM(estimated_cost) as cost,
               COUNT(*) as requests
        FROM model_usage {filter_sql}
        GROUP BY task_type
        ORDER BY cost DESC
    """).fetchall()
    
    # Recent requests
    recent = conn.execute(f"""
        SELECT model, provider, task_type, input_tokens, output_tokens, estimated_cost, timestamp
        FROM model_usage {filter_sql}
        ORDER BY timestamp DESC
        LIMIT 10
    """).fetchall()
    
    conn.close()
    
    return {
        "total_cost": round(total, 4),
        "by_provider": [dict(r) for r in by_provider],
        "by_model": [dict(r) for r in by_model],
        "by_task": [dict(r) for r in by_task],
        "recent": [dict(r) for r in recent]
    }

def print_report(period="week"):
    """Print a cost report"""
    s = get_summary(period)
    
    period_name = {"day": "Today", "week": "This Week", "month": "This Month"}.get(period, period)
    
    print(f"\n📊 MODEL COST REPORT — {period_name}")
    print("=" * 50)
    
    print(f"\n💰 TOTAL ESTIMATED COST: ${s['total_cost']:.4f}")
    
    print(f"\n🏢 BY PROVIDER:")
    for p in s["by_provider"]:
        print(f"   {p['provider']:15} ${p['cost']:.4f} ({p['input']:,} in / {p['output']:,} out)")
    
    print(f"\n🤖 BY MODEL:")
    for m in s["by_model"]:
        print(f"   {m['model']:25} ${m['cost']:.4f} ({m['requests']} requests)")
    
    if s["by_task"]:
        print(f"\n📋 BY TASK TYPE:")
        for t in s["by_task"]:
            print(f"   {t['task_type']:20} ${t['cost']:.4f} ({t['requests']} requests)")
    
    print(f"\n🕐 RECENT REQUESTS:")
    for r in s["recent"][:5]:
        ts = r["timestamp"][:16] if r["timestamp"] else ""
        print(f"   {ts} {r['model'][:20]:20} ${r['estimated_cost']:.4f} — {r['task_type']}")
    
    print(f"\n🤖 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

def send_to_telegram(period="week"):
    """Send report to Telegram"""
    s = get_summary(period)
    
    period_name = {"day": "Today", "week": "This Week", "month": "This Month"}.get(period, period)
    
    text = f"📊 *MODEL COST REPORT — {period_name}*\n"
    text += "=" * 40 + "\n\n"
    
    text += f"💰 *TOTAL:* ${s['total_cost']:.4f}\n\n"
    
    text += "🏢 *BY PROVIDER:*\n"
    for p in s["by_provider"]:
        text += f"  • {p['provider']:10} ${p['cost']:.4f}\n"
    
    text += "\n🤖 *BY MODEL:*\n"
    for m in s["by_model"][:5]:
        text += f"  • {m['model'][:22]:22} ${m['cost']:.4f} ({m['requests']} calls)\n"
    
    text += f"\n🤖 {datetime.now().strftime('%H:%M')}"
    
    # Send via openclaw
    result = subprocess.run(
        ["openclaw", "message", "send", "--target", "telegram:866838380", "--message", text],
        capture_output=True, text=True
    )
    
    return result.returncode == 0

# Initialize on import
init_db()

if __name__ == "__main__":
    import sys
    period = sys.argv[1] if len(sys.argv) > 1 else "week"
    
    if len(sys.argv) > 2 and sys.argv[2] == "--telegram":
        send_to_telegram(period)
        print("✅ Sent to Telegram")
    else:
        print_report(period)
