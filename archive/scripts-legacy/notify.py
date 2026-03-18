#!/usr/bin/env python3
"""
OpenClaw Notification System
============================
Telegram notifications, follow-up reminders, and alerts.

Usage:
    python3 notify.py --test          # Test notification
    python3 notify.py --status        # Check all statuses
    python3 notify.py --followups     # Generate follow-up reminders
    python3 notify.py --daily        # Daily briefing
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Load config
CONFIG = {
    "workspace": "/root/.openclaw/workspace",
    "notion_key_path": "~/.config/notion/api_key",
    "telegram_token_path": "~/.config/telegram/token",
    "telegram_chat_id": "866838380",
    "reminder_days": [3, 7, 14]  # Follow-up intervals
}

class NotificationSystem:
    def __init__(self):
        self.workspace = Path(CONFIG["workspace"])
        self.notion_key = self.load_file(CONFIG["notion_key_path"])
        self.telegram_token = self.load_file(CONFIG["telegram_token_path"])
        self.chat_id = CONFIG["telegram_chat_id"]
        
    def load_file(self, path):
        path = os.path.expanduser(path)
        if os.path.exists(path):
            return open(path).read().strip()
        return None
    
    def send_telegram(self, message, buttons=None):
        """Send notification to Telegram"""
        if not self.telegram_token:
            print("No Telegram token configured")
            return False
        
        import urllib.request
        import urllib.parse
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        if buttons:
            inline_keyboard = []
            for btn in buttons:
                inline_keyboard.append([{"text": btn["text"], "callback_data": btn["data"]}]
            data["reply_markup"] = json.dumps({"inline_keyboard": inline_keyboard})
        
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
            urllib.request.urlopen(req, timeout=10)
            return True
        except Exception as e:
            print(f"Telegram error: {e}")
            return False
    
    def get_notion_data(self):
        """Fetch all opportunities from Notion"""
        from notion_client import Client
        notion = Client(auth=self.notion_key)
        
        result = notion.search(query="", filter={"property": "object", "value": "page"})
        
        opportunities = []
        for page in result.get('results', []):
            props = page.get('properties', {})
            
            # Check if this is an opportunity
            ats = props.get('ATS Score', {}).get('number', 0)
            if ats > 0:
                name = props.get('Name', {}).get('title', [{}])[0].get('plain_text', 'Untitled')
                status = props.get('Status', {}).get('select', {}).get('name', 'Unknown')
                company = props.get('Company', {}).get('rich_text', [{}])
                company = company[0].get('plain_text', '') if company else ''
                salary = props.get('Salary Asked', {}).get('number', 0)
                last_contact = props.get('Last Contact', {}).get('date', {})
                last_contact = last_contact.get('start', '')
                
                opportunities.append({
                    "id": page['id'],
                    "name": name,
                    "company": company,
                    "status": status,
                    "salary": salary,
                    "ats": ats,
                    "last_contact": last_contact
                })
        
        return opportunities
    
    def check_status_changes(self):
        """Check for status changes and send notifications"""
        cache_file = self.workspace / ".notion_cache.json"
        
        # Load previous state
        if cache_file.exists():
            with open(cache_file) as f:
                previous = json.load(f)
        else:
            previous = {}
        
        current = {}
        changes = []
        
        opportunities = self.get_notion_data()
        for opp in opportunities:
            opp_id = opp['id']
            current[opp_id] = opp['status']
            
            # Detect changes
            if opp_id in previous:
                if previous[opp_id] != opp['status']:
                    changes.append({
                        "name": opp['name'],
                        "company": opp['company'],
                        "old_status": previous[opp_id],
                        "new_status": opp['status'],
                        "ats": opp['ats'],
                        "salary": opp['salary']
                    })
            else:
                # New opportunity
                changes.append({
                    "name": opp['name'],
                    "company": opp['company'],
                    "old_status": None,
                    "new_status": opp['status'],
                    "ats": opp['ats'],
                    "salary": opp['salary']
                })
        
        # Save current state
        with open(cache_file, 'w') as f:
            json.dump(current, f)
        
        return changes
    
    def send_notifications(self, changes):
        """Send notifications for changes"""
        for change in changes:
            if change['new_status'] == 'Interview':
                emoji = "🎉"
                msg = f"{emoji} *INTERVIEW!*"
            elif change['new_status'] == 'Offer':
                emoji = "🏆"
                msg = f"{emoji} *OFFER RECEIVED!*"
            elif change['new_status'] == 'Rejected':
                emoji = "❌"
                msg = f"{emoji} *Rejected*"
            elif change['new_status'] == 'Applied' and change['old_status'] is None:
                emoji = "📤"
                msg = f"{emoji} *New Application*"
            else:
                emoji = "📋"
                msg = f"{emoji} *Status Update*"
            
            message = f"""{msg}

📎 *{change['name']}*
🏢 {change['company']}
📊 ATS: {change['ats']} | 💰 ${change['salary']:,}/mo

_Status changed from {change['old_status'] or 'New'} to {change['new_status']}_
"""
            
            buttons = [
                {"text": "✅ Mark Done", "data": f"done_{change['id']}"},
                {"text": "⏰ Remind", "data": f"remind_{change['id']}"}
            ]
            
            self.send_telegram(message, buttons)
        
        return len(changes)
    
    def check_followups(self):
        """Generate follow-up reminders"""
        opportunities = self.get_notion_data()
        followups = []
        
        for opp in opportunities:
            if opp['status'] not in ['Offer', 'Rejected', 'Complete']:
                last = opp['last_contact']
                if last:
                    last_date = datetime.strptime(last, "%Y-%m-%d")
                    days_ago = (datetime.now() - last_date).days
                    
                    if days_ago in CONFIG["reminder_days"]:
                        followups.append({
                            **opp,
                            "days_ago": days_ago
                        })
        
        return followups
    
    def generate_followup_message(self, followups):
        """Generate follow-up reminder message"""
        if not followups:
            return None
        
        message = """🔔 *FOLLOW-UP REMINDERS*

These opportunities need attention:
"""
        
        for f in followups:
            urgency = "🚨" if f['days_ago'] == 14 else "⏰" if f['days_ago'] == 7 else "📅"
            message += f"""
{urgency} *{f['name']}*
🏢 {f['company']}
⏰ Last contact: {f['days_ago']} days ago
📊 ATS: {f['ats']} | 💰 ${f['salary']:,}/mo
"""
        
        message += """
Reply with the number to create a follow-up task."""
        
        return message
    
    def daily_briefing(self):
        """Generate daily briefing"""
        opportunities = self.get_notion_data()
        
        # Count by status
        status_counts = {}
        ats_buckets = {"80+": 0, "70-79": 0, "60-69": 0, "50-59": 0, "<50": 0}
        total_salary = 0
        count_salary = 0
        
        for opp in opportunities:
            status = opp['status']
            status_counts[status] = status_counts.get(status, 0) + 1
            
            ats = opp['ats']
            if ats >= 80:
                ats_buckets["80+"] += 1
            elif ats >= 70:
                ats_buckets["70-79"] += 1
            elif ats >= 60:
                ats_buckets["60-69"] += 1
            elif ats >= 50:
                ats_buckets["50-59"] += 1
            else:
                ats_buckets["<50"] += 1
            
            if opp['salary'] > 0:
                total_salary += opp['salary']
                count_salary += 1
        
        # Follow-ups needed
        followups = self.check_followups()
        
        message = f"""🌅 *DAILY BRIEFING* - {datetime.now().strftime('%B %d')}

📊 *PIPELINE OVERVIEW*
Total Opportunities: {len(opportunities)}

*By Status:*
"""
        
        for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
            emoji = {"Applied": "📤", "Call": "📞", "Interview": "🎯", "Offer": "🏆", "Rejected": "❌", "Complete": "✅"}.get(status, "📋")
            message += f"  {emoji} {status}: {count}\n"
        
        message += f"""
*By ATS Score:*
  🟢 80+: {ats_buckets['80+']} | 🟡 70-79: {ats_buckets['70-79']}
  🟠 60-69: {ats_buckets['60-69']} | 🔴 <60: {ats_buckets['50-59'] + ats_buckets['<50']}

💰 *Avg Salary:* ${total_salary // count_salary:,}/mo (n={count_salary})

🔔 *Follow-ups Needed:* {len(followups)}
"""
        
        if followups:
            message += """
*Top Priorities:*
"""
            for f in sorted(followups, key=lambda x: -x['days_ago'])[:3]:
                message += f"  ⏰ {f['name'][:40]} ({f['company']})\n"
        
        return message
    
    def run(self, mode="check"):
        """Run notification system"""
        if mode == "test":
            self.send_telegram("🧪 *Test Notification*\n\nYour OpenClaw notification system is working!", [
                {"text": "✅ Great", "data": "test_yes"},
                {"text": "❌ Issue", "data": "test_no"}
            ])
            return True
        
        elif mode == "status":
            opportunities = self.get_notion_data()
            return opportunities
        
        elif mode == "followups":
            followups = self.check_followups()
            if followups:
                message = self.generate_followup_message(followups)
                self.send_telegram(message)
                return followups
            return []
        
        elif mode == "daily":
            message = self.daily_briefing()
            self.send_telegram(message)
            return True
        
        else:
            # Check for changes
            changes = self.check_status_changes()
            if changes:
                count = self.send_notifications(changes)
                print(f"Sent {count} notifications")
                return changes
            
            # Also send follow-ups if needed
            followups = self.check_followups()
            if followups:
                message = self.generate_followup_message(followups)
                self.send_telegram(message)
                return followups
            
            print("No new notifications")
            return []


if __name__ == "__main__":
    import sys
    
    notify = NotificationSystem()
    
    mode = sys.argv[1].lstrip('--') if len(sys.argv) > 1 else "check"
    
    if mode == "test":
        notify.run("test")
    elif mode == "status":
        opps = notify.run("status")
        for o in opps:
            print(f"{o['status']}: {o['name'][:50]}")
    elif mode == "followups":
        fups = notify.run("followups")
        if not fups:
            print("No follow-ups needed")
    elif mode == "daily":
        notify.run("daily")
    else:
        changes = notify.run("check")
        if changes:
            print(f"Processed {len(changes)} changes")
        else:
            print("No new notifications")
