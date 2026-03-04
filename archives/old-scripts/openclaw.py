#!/usr/bin/env python3
"""
OpenClaw Command Center
======================
Unified command interface for all sync and notification operations.

Usage:
    python3 openclaw.py status          # Quick status
    python3 openclaw.py sync           # Full sync
    python3 openclaw.py sync --inc     # Incremental sync
    python3 openclaw.py notify         # Send notifications
    python3 openclaw.py analytics       # Full analytics
    python3 openclaw.py dashboard       # Pipeline dashboard
    python3 openclaw.py configure      # Configure preferences
"""

import sys
import argparse
from datetime import datetime

class OpenClawCommandCenter:
    def __init__(self):
        self.workspace = "/root/.openclaw/workspace"
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"🦞 OPENCLAW - {title}")
        print(f"{'='*60}\n")
    
    def status(self):
        """Quick status check"""
        self.print_header("STATUS")
        
        import json
        from pathlib import Path
        
        # Check sync state
        state_file = Path(f"{self.workspace}/.sync_state.json")
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
            last_sync = state.get("last_sync", "Never")
            print(f"Last Sync: {last_sync}")
            print(f"Successes: {state.get('metrics', {}).get('successes', 0)}")
            print(f"Failures: {state.get('metrics', {}).get('failures', 0)}")
        else:
            print("Sync state: Not initialized")
        
        # Check notification state
        notify_state = Path(f"{self.workspace}/.notification_state.json")
        if notify_state.exists():
            with open(notify_state) as f:
                nstate = json.load(f)
            print(f"Notifications: {len(nstate)} tracked")
        
        # Check response history
        history_file = Path(f"{self.workspace}/.response_history.json")
        if history_file.exists():
            with open(history_file) as f:
                history = json.load(f)
            print(f"Applications: {len(history.get('applications', []))}")
            print(f"Offers: {len(history.get('offers', []))}")
        
        print()
    
    def sync(self, incremental=False):
        """Run sync"""
        self.print_header("SYNC")
        if incremental:
            print("Running incremental sync...\n")
            import subprocess
            result = subprocess.run(
                ["python3", f"{self.workspace}/sync_engine_enhanced.py", "--incremental"],
                capture_output=True, text=True
            )
            print(result.stdout)
        else:
            print("Running full sync...\n")
            import subprocess
            result = subprocess.run(
                ["python3", f"{self.workspace}/sync_engine_enhanced.py", "--full-sync"],
                capture_output=True, text=True
            )
            print(result.stdout)
    
    def notify(self):
        """Send notifications"""
        self.print_header("NOTIFICATIONS")
        print("Checking for alerts...\n")
        
        import subprocess
        result = subprocess.run(
            ["python3", f"{self.workspace}/notify_enhanced.py", "--check"],
            capture_output=True, text=True
        )
        print(result.stdout or "No new notifications")
    
    def analytics(self):
        """Full analytics"""
        self.print_header("ANALYTICS")
        
        # Response tracker
        print("📊 Response Metrics:")
        import subprocess
        result = subprocess.run(
            ["python3", f"{self.workspace}/response_tracker_enhanced.py", "--dashboard"],
            capture_output=True, text=True
        )
        print(result.stdout)
        
        # Sync analytics
        print("\n🔄 Sync Analytics:")
        result = subprocess.run(
            ["python3", f"{self.workspace}/sync_engine_enhanced.py", "--analytics"],
            capture_output=True, text=True
        )
        print(result.stdout)
    
    def dashboard(self):
        """Pipeline dashboard"""
        self.print_header("PIPELINE DASHBOARD")
        
        import subprocess
        result = subprocess.run(
            ["python3", f"{self.workspace}/response_tracker_enhanced.py", "--dashboard"],
            capture_output=True, text=True
        )
        print(result.stdout)
    
    def configure(self):
        """Configure preferences"""
        self.print_header("CONFIGURATION")
        
        import subprocess
        result = subprocess.run(
            ["python3", f"{self.workspace}/notify_enhanced.py", "--config"],
            capture_output=True, text=True
        )
        print(result.stdout)
    
    def quick_summary(self):
        """Quick summary for cron"""
        print(f"🦞 OpenClaw - {self.timestamp}")
        
        import json
        from pathlib import Path
        
        # Quick stats
        state_file = Path(f"{self.workspace}/.sync_state.json")
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
            print(f"  Sync: {state.get('metrics', {}).get('successes', 0)} success, {state.get('metrics', {}).get('failures', 0)} failed")
        
        history_file = Path(f"{self.workspace}/.response_history.json")
        if history_file.exists():
            with open(history_file) as f:
                history = json.load(f)
            apps = len(history.get('applications', []))
            offers = len(history.get('offers', []))
            print(f"  Pipeline: {apps} applications, {offers} offers")


if __name__ == "__main__":
    center = OpenClawCommandCenter()
    
    parser = argparse.ArgumentParser(description="OpenClaw Command Center")
    parser.add_argument("command", choices=[
        "status", "sync", "notify", "analytics", "dashboard", "configure"
    ], help="Command to run")
    parser.add_argument("--inc", "--incremental", action="store_true", 
                       help="Run incremental sync")
    
    args = parser.parse_args()
    
    if args.command == "status":
        center.status()
    elif args.command == "sync":
        center.sync(incremental=args.inc)
    elif args.command == "notify":
        center.notify()
    elif args.command == "analytics":
        center.analytics()
    elif args.command == "dashboard":
        center.dashboard()
    elif args.command == "configure":
        center.configure()
