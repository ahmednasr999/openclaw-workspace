#!/usr/bin/env python3
"""
Proactive Job Scanning - Heartbeat Check
"""
import json
from datetime import datetime

TRACKING_FILE = "/root/.openclaw/workspace/memory/proactive_tracking.json"

def run_proactive_check():
    """Run proactive check during heartbeat"""
    
    print("🔍 RUNNING PROACTIVE CHECK...")
    print("="*50)
    
    with open(TRACKING_FILE, 'r') as f:
        data = json.load(f)
    
    data['heartbeat_count'] += 1
    data['last_proactive_check'] = datetime.utcnow().isoformat()
    
    # Job search terms to monitor
    job_terms = data.get('job_search_terms', [])
    
    print(f"\n📊 Job Search Terms ({len(job_terms)}):")
    for term in job_terms:
        print(f"   • {term}")
    
    # Check upcoming deadlines (would check calendar here)
    print(f"\n📅 Upcoming Deadlines:")
    deadlines = data.get('upcoming_deadlines', [])
    if deadlines:
        for d in deadlines:
            print(f"   • {d}")
    else:
        print("   • None pending")
    
    # Pending actions
    print(f"\n⏳ Pending Actions:")
    actions = data.get('pending_actions', [])
    if actions:
        for a in actions:
            print(f"   • {a}")
    else:
        print("   • None")
    
    # Opportunities found
    print(f"\n🎯 Opportunities Found:")
    opps = data.get('opportunities_found', [])
    if opps:
        for o in opps:
            print(f"   • {o}")
    else:
        print("   • None yet - Will scan when web access available")
    
    data['last_proactive_check'] = datetime.utcnow().isoformat()
    
    with open(TRACKING_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Proactive check #{data['heartbeat_count']} complete!")
    print("="*50)

if __name__ == "__main__":
    run_proactive_check()
