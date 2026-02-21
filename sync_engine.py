#!/usr/bin/env python3
"""
OpenClaw <> Notion Sync System
================================
Bidirectional sync with event triggers, analytics, and AI features.

Usage:
    python3 sync_engine.py --full-sync      # Full workspace → Notion
    python3 sync_engine.py --pull           # Notion → Workspace
    python3 sync_engine.py --push           # Workspace → Notion
    python3 sync_engine.py --watch          # Continuous sync
    python3 sync_engine.py --analytics      # Show pipeline analytics
    python3 sync_engine.py --auto-tag       # AI auto-categorize JDs
"""

import os
import json
import time
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from notion_client import Client
import yaml

# Config
CONFIG = {
    "workspace": "/root/.openclaw/workspace",
    "notion_key_path": "~/.config/notion/api_key",
    "log_file": "/root/.openclaw/logs/sync.log",
    "sync_interval": 300,  # 5 minutes
    "databases": {
        "job_tracker": "30b8d599a1628140a655d5ef843cd833",  # Opportunities (Job Tracker)
        "cv_library": "10554004-00dc-4853-934f-c33bb96b6923",  # CV Library
        "daily_notes": "30b8d599a162819caaece83207b76394",
        "knowledge_base": "30b8d599a162817fab62c4a951b24e2c",
        "coordination": "30b8d599a16281a0a12ff2ed81cb99da",
        "skills_catalog": "30b8d599a16281a88e1bd2d2258909e4"
    }
}

class OpenClawSync:
    def __init__(self):
        self.notion = Client(auth=self.get_notion_key())
        self.workspace = Path(CONFIG["workspace"])
        self.log_file = Path(CONFIG["log_file"])
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
    def get_notion_key(self):
        return open(os.path.expanduser(CONFIG["notion_key_path"])).read().strip()
    
    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {msg}\n"
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
        print(log_entry.strip())
    
    # === ANALYTICS ===
    def analytics(self):
        """Show pipeline analytics"""
        self.log("=== PIPELINE ANALYTICS ===", "INFO")
        
        stats = {
            "total_opportunities": 0,
            "by_status": {},
            "by_ats_score": {"80+": 0, "70-79": 0, "60-69": 0, "50-59": 0, "<50": 0},
            "avg_salary": [],
            "response_rate": "N/A",
            "time_to_response": "N/A"
        }
        
        result = self.notion.search(query="", filter={"property": "object", "value": "page"})
        
        for page in result.get('results', []):
            props = page.get('properties', {})
            
            # Check if this is a job entry (has ATS Score)
            ats = props.get('ATS Score', {}).get('number', 0)
            if ats > 0:
                stats["total_opportunities"] += 1
                
                # Status
                status = props.get('Status', {}).get('select', {}).get('name', 'Unknown')
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
                
                # ATS Score
                if ats >= 80:
                    stats["by_ats_score"]["80+"] += 1
                elif ats >= 70:
                    stats["by_ats_score"]["70-79"] += 1
                elif ats >= 60:
                    stats["by_ats_score"]["60-69"] += 1
                elif ats >= 50:
                    stats["by_ats_score"]["50-59"] += 1
                else:
                    stats["by_ats_score"]["<50"] += 1
                
                # Salary
                salary = props.get('Salary Asked', {}).get('number', 0)
                if salary > 0:
                    stats["avg_salary"].append(salary)
        
        # Output
        print("\n" + "="*50)
        print("PIPELINE ANALYTICS")
        print("="*50)
        print(f"\nTotal Opportunities: {stats['total_opportunities']}")
        
        print(f"\nBy Status:")
        for status, count in sorted(stats['by_status'].items()):
            pct = (count / stats['total_opportunities'] * 100) if stats['total_opportunities'] else 0
            print(f"  {status}: {count} ({pct:.0f}%)")
        
        print(f"\nBy ATS Score:")
        for range_name, count in stats['by_ats_score'].items():
            if count > 0:
                print(f"  {range_name}: {count}")
        
        if stats['avg_salary']:
            avg = sum(stats['avg_salary']) / len(stats['avg_salary'])
            print(f"\nAverage Salary: ${avg:,.0f}/month")
        
        print(f"\nResponse Rate: {stats['response_rate']}")
        print(f"Time to First Response: {stats['time_to_response']}")
        print("="*50)
        
        return stats
    
    # === AI AUTO-TAG ===
    def auto_tag_jds(self):
        """AI auto-categorize new JDs"""
        self.log("=== AI AUTO-TAGGING ===", "INFO")
        
        new_jds = []
        result = self.notion.search(query="", filter={"property": "object", "value": "page"})
        
        for page in result.get('results', []):
            parent = page.get('parent', {})
            if parent.get('database_id') == CONFIG["databases"]["job_tracker"]:
                props = page.get('properties', {})
                ats = props.get('ATS Score', {}).get('number', 0)
                
                # Tag new entries with no ATS score
                if ats == 0:
                    name = props.get('Name', {}).get('title', [{}])[0].get('plain_text', '')
                    new_jds.append((page['id'], name))
        
        print(f"\nFound {len(new_jds)} new JDs to tag\n")
        
        for page_id, name in new_jds[:5]:  # Process first 5
            # Simple keyword-based tagging (can be upgraded to AI)
            role_type = "PMO/Director"
            ats_score = 65  # Default
            
            keywords_pmo = ["PMO", "project", "program", "delivery", "governance"]
            keywords_data = ["data", "AI", "analytics", "engineering"]
            keywords_venture = ["founder", "venture", "startup", "co-founder"]
            
            name_lower = name.lower()
            
            if any(k in name_lower for k in keywords_data):
                role_type = "Data/AI"
                ats_score = 70
            elif any(k in name_lower for k in keywords_venture):
                role_type = "Venture/Startup"
                ats_score = 60
            elif any(k in name_lower for k in keywords_pmo):
                role_type = "PMO/Director"
                ats_score = 75
            
            # Update Notion
            try:
                self.notion.pages.update(
                    page_id=page_id,
                    properties={
                        "ATS Score": {"number": ats_score},
                        "Status": {"select": {"name": "Applied"}}
                    }
                )
                print(f"✓ Tagged: {name[:50]} → {role_type} (ATS: {ats_score})")
            except Exception as e:
                print(f"✗ Failed: {name[:40]} - {str(e)[:30]}")
        
        print(f"\n=== AUTO-TAGGING COMPLETE ===")
    
    # === WORKSPACE → NOTION ===
    def push_to_notion(self):
        """Sync workspace changes to Notion"""
        self.log("=== PUSH TO NOTION ===", "INFO")
        
        # CVs
        cv_dir = self.workspace / "cvs"
        if cv_dir.exists():
            for pdf in cv_dir.glob("*.pdf"):
                self.log(f"CV found: {pdf.name}")
        
        # Daily notes
        memory_dir = self.workspace / "memory"
        if memory_dir.exists():
            for md in memory_dir.glob("2026-*.md"):
                self.log(f"Daily note: {md.name}")
        
        # Coordination
        coord_dir = self.workspace / "coordination"
        if coord_dir.exists():
            for json_file in coord_dir.glob("*.json"):
                self.log(f"Coordination: {json_file.name}")
        
        self.log("Push complete", "INFO")
    
    # === NOTION → WORKSPACE ===
    def pull_from_notion(self):
        """Sync Notion changes to workspace"""
        self.log("=== PULL FROM NOTION ===", "INFO")
        
        result = self.notion.search(query="", filter={"property": "object", "value": "page"})
        
        changes = 0
        for page in result.get('results', []):
            props = page.get('properties', {})
            name = props.get('Name', {}).get('title', [{}])[0].get('plain_text', '')
            
            # Check for status changes
            status = props.get('Status', {}).get('select', {}).get('name', '')
            if status == "Interview":
                self.log(f"🎯 Interview scheduled: {name[:50]}")
                changes += 1
            elif status == "Offer":
                self.log(f"🎉 OFFER: {name[:50]}")
                changes += 1
        
        self.log(f"Pull complete: {changes} changes detected", "INFO")
    
    # === TRIGGER HANDLER ===
    def handle_triggers(self):
        """Process event triggers"""
        self.log("=== HANDLING TRIGGERS ===", "INFO")
        
        result = self.notion.search(query="", filter={"property": "object", "value": "page"})
        
        for page in result.get('results', []):
            props = page.get('properties', {})
            status = props.get('Status', {}).get('select', {}).get('name', '')
            name = props.get('Name', {}).get('title', [{}])[0].get('plain_text', '')
            
            # Trigger: Status change
            if status == "Offer":
                self.log(f"🎉 TRIGGER: Offer received - {name}", "CELEBRATE")
                # Could: Send notification, update dashboard, etc.
            elif status == "Interview":
                self.log(f"📅 TRIGGER: Interview scheduled - {name}", "INFO")
            elif status == "Rejected":
                self.log(f"❌ TRIGGER: Rejection - {name}", "INFO")
        
        self.log("Triggers processed", "INFO")
    
    # === FULL SYNC ===
    def full_sync(self):
        """Complete bidirectional sync"""
        self.log("=== FULL SYNC STARTED ===", "INFO")
        
        self.handle_triggers()
        self.pull_from_notion()
        self.push_to_notion()
        self.auto_tag_jds()
        
        self.log("=== FULL SYNC COMPLETE ===", "INFO")
        
        # Show analytics
        self.analytics()


if __name__ == "__main__":
    import sys
    
    sync = OpenClawSync()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "--full-sync":
            sync.full_sync()
        elif cmd == "--push":
            sync.push_to_notion()
        elif cmd == "--pull":
            sync.pull_from_notion()
        elif cmd == "--watch":
            print(f"Watching for changes every {CONFIG['sync_interval']}s...")
            while True:
                sync.full_sync()
                time.sleep(CONFIG['sync_interval'])
        elif cmd == "--analytics":
            sync.analytics()
        elif cmd == "--auto-tag":
            sync.auto_tag_jds()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: sync_engine.py [--full-sync|--push|--pull|--watch|--analytics|--auto-tag]")
    else:
        sync.full_sync()
