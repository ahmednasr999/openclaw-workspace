#!/usr/bin/env python3
"""
Earnings Reports
Checks upcoming earnings and generates summaries
"""

import subprocess, json, sqlite3
from datetime import datetime, timedelta
from urllib.request import urlopen
from urllib.error import URLError

DB_PATH = "/root/.openclaw/workspace/knowledge-base/kb.db"

# Your watchlist (add tickers you care about)
WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]

# Free earnings calendar API (Alpha Vantage or similar)
EARNINGS_API = "https://api.alphavantage.co/query"

def get_earnings_date(ticker):
    """Get next earnings date for a ticker (mock - replace with real API)"""
    # This would use a real API like Alpha Vantage or Yahoo Finance
    # For now, return mock data
    
    # Real implementation would be:
    # import requests
    # response = requests.get(f"{EARNINGS_API}?function=EARNINGS&symbol={ticker}&apikey={API_KEY}")
    
    return {
        "ticker": ticker,
        "date": None,  # Would be actual date
        "estimated": None,  # EPS estimate
        "last_report": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
        "api_status": "not_configured"
    }

def check_upcoming_earnings():
    """Check upcoming earnings for watchlist"""
    results = []
    
    for ticker in WATCHLIST:
        data = get_earnings_date(ticker)
        results.append(data)
    
    return results

def get_watchlist():
    """Get user's earnings watchlist"""
    conn = sqlite3.connect(DB_PATH)
    
    tickers = conn.execute("SELECT DISTINCT company FROM job_pipeline WHERE company IS NOT NULL").fetchall()
    
    conn.close()
    
    # Extract tickers (simplified - would need mapping company→ticker)
    watchlist = [t[0] for t in tickers if len(t[0]) <= 5]  # Simple filter
    return WATCHLIST + watchlist

def check_earnings():
    """Check earnings and return upcoming ones"""
    watchlist = get_watchlist()
    results = []
    
    for ticker in set(watchlist):
        data = get_earnings_date(ticker)
        results.append(data)
    
    # Filter for upcoming (within 30 days)
    upcoming = [r for r in results if r["date"]]
    
    return {
        "watchlist_count": len(watchlist),
        "results": results,
        "upcoming": upcoming
    }

def generate_report():
    """Generate earnings report"""
    print("\n📈 EARNINGS REPORT")
    print("=" * 50)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    result = check_earnings()
    
    print(f"📊 Watchlist: {result['watchlist_count']} companies")
    print()
    
    # Show all in watchlist
    print("📋 WATCHLIST:")
    for r in result["results"]:
        ticker = r["ticker"]
        last = r["last_report"]
        status = r["api_status"]
        
        if status == "not_configured":
            print(f"   • {ticker}: API not configured")
        else:
            print(f"   • {ticker}: Last reported {last}")
    
    print()
    
    if result["upcoming"]:
        print("🚨 UPCOMING (within 30 days):")
        for r in result["upcoming"]:
            print(f"   • {r['ticker']}: {r['date']}")
    else:
        print("📭 No upcoming earnings in watchlist (API not configured)")
    
    print()
    print("💡 To enable: Add Alpha Vantage API key to EARNINGS_API")
    
    return result

def send_telegram_report():
    """Send brief earnings update to Telegram"""
    result = check_earnings()
    
    text = f"📈 *Earnings Watchlist*\n\n"
    text += f"🕐 {datetime.now().strftime('%m/%d')}\n\n"
    
    configured = [r for r in result["results"] if r["api_status"] == "configured"]
    
    if configured:
        text += f"*{len(configured)} companies tracked:*\n"
        for r in configured[:5]:
            text += f"• {r['ticker']}: last {r['last_report']}\n"
    else:
        text += "⚠️ API not configured\n\n"
        text += "Add API key to enable tracking."
    
    subprocess.run(
        ["openclaw", "message", "send", "--target", "telegram:866838380", "--message", text],
        capture_output=True
    )

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--telegram":
            send_telegram_report()
            print("✅ Sent to Telegram")
        else:
            generate_report()
    else:
        generate_report()
