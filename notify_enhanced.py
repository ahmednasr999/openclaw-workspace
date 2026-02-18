#!/usr/bin/env python3
"""
Enhanced Notification System
============================
Rich notifications, escalation rules, and notification preferences.

Usage:
    python3 notify_enhanced.py --config        # Configure preferences
    python3 notify_enhanced.py --test         # Test notification
    python3 notify_enhanced.py --summary      # Quick summary
    python3 notify_enhanced.py --alerts       # Check for alerts
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import urllib.request
import urllib.parse

class NotificationPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class NotificationPreferences:
    def __init__(self):
        self.config_file = Path("/root/.openclaw/workspace/.notify_preferences.json")
        self.config = self.load_config()
    
    def load_config(self):
        """Load notification preferences"""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        
        # Default preferences
        return {
            "enabled": True,
            "channels": {
                "telegram": True,
                "email": False,
                "sms": False
            },
            "alerts": {
                "new_application": True,
                "status_change": True,
                "interview": True,
                "offer": True,
                "rejection": False,
                "followup_reminder": True,
                "weekly_summary": True,
                "daily_briefing": True
            },
            "priority_rules": {
                "offer": "CRITICAL",
                "interview": "HIGH",
                "new_application": "MEDIUM",
                "rejection": "LOW"
            },
            "followup_days": [3, 7, 14],
            "quiet_hours": {
                "enabled": False,
                "start": "22:00",
                "end": "08:00"
            },
            "escalation": {
                "enabled": True,
                "max_retries": 3,
                "retry_interval": 300  # 5 minutes
            }
        }
    
    def save_config(self):
        """Save preferences"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def configure(self):
        """Interactive configuration"""
        print("\n=== NOTIFICATION CONFIGURATION ===\n")
        
        # Enable/disable
        self.config["enabled"] = input("Enable notifications? [Y/n]: ").lower() != "n"
        
        # Channels
        print("\nChannels:")
        self.config["channels"]["telegram"] = input("  Telegram? [Y/n]: ").lower() != "n"
        self.config["channels"]["email"] = input("  Email? [Y/n]: ").lower() != "n"
        self.config["channels"]["sms"] = input("  SMS? [Y/n]: ").lower() != "n"
        
        # Alert types
        print("\nAlert Types:")
        for alert, enabled in self.config["alerts"].items():
            response = input(f"  {alert.replace('_', ' ').title()}? [Y/n]: ").lower()
            self.config["alerts"][alert] = response != "n"
        
        # Follow-up days
        print(f"\nFollow-up days (currently: {self.config['followup_days']}):")
        days = input("  Enter days (comma-separated, e.g., 3,7,14): ").strip()
        if days:
            self.config["followup_days"] = [int(d.strip()) for d in days.split(",")]
        
        # Quiet hours
        print(f"\nQuiet hours (currently: {self.config['quiet_hours']['enabled']}):")
        response = input("  Enable quiet hours? [Y/n]: ").lower()
        self.config["quiet_hours"]["enabled"] = response == "y"
        
        self.save_config()
        print("\n✅ Configuration saved!")
    
    def should_notify(self, alert_type):
        """Check if notification should be sent"""
        if not self.config["enabled"]:
            return False, "Notifications disabled"
        
        if alert_type not in self.config["alerts"]:
            return False, "Unknown alert type"
        
        if not self.config["alerts"][alert_type]:
            return False, f"Alerts.{alert_type} disabled"
        
        # Check quiet hours
        if self.config["quiet_hours"]["enabled"]:
            now = datetime.now()
            start = datetime.strptime(self.config["quiet_hours"]["start"], "%H:%M").time()
            end = datetime.strptime(self.config["quiet_hours"]["end"], "%H:%M").time()
            
            if start > end:
                # Wraps around midnight
                if now.time() >= start or now.time() <= end:
                    return False, "Quiet hours"
            else:
                if start <= now.time() <= end:
                    return False, "Quiet hours"
        
        return True, "OK"


class EnhancedNotifications:
    def __init__(self):
        self.prefs = NotificationPreferences()
        self.workspace = Path("/root/.openclaw/workspace")
        self.telegram_token = self.load_file("~/.config/telegram/token")
        self.chat_id = "866838380"
    
    def load_file(self, path):
        path = os.path.expanduser(path)
        if os.path.exists(path):
            return open(path).read().strip()
        return None
    
    def send_telegram(self, message, priority=NotificationPriority.MEDIUM, buttons=None):
        """Send Telegram notification with priority"""
        if not self.telegram_token:
            print("No Telegram token")
            return False
        
        # Determine emoji based on priority
        priority_emoji = {
            NotificationPriority.LOW: "ℹ️",
            NotificationPriority.MEDIUM: "📬",
            NotificationPriority.HIGH: "⚠️",
            NotificationPriority.URGENT: "🚨",
            NotificationPriority.CRITICAL: "🏆"
        }
        
        emoji = priority_emoji.get(priority, "📬")
        formatted_message = f"{emoji} {message}"
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": formatted_message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        
        if buttons:
            inline_keyboard = []
            for btn in buttons:
                inline_keyboard.append([{"text": btn["text"], "callback_data": btn["data"]}])
            data["reply_markup"] = json.dumps({"inline_keyboard": inline_keyboard})
        
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
            urllib.request.urlopen(req, timeout=10)
            return True
        except Exception as e:
            print(f"Telegram error: {e}")
            return False
    
    def format_opportunity(self, opp, alert_type):
        """Format opportunity for notification"""
        priority = NotificationPriority.MEDIUM
        
        if alert_type == "offer":
            priority = NotificationPriority.CRITICAL
            emoji = "🏆"
            header = "OFFER RECEIVED"
        elif alert_type == "interview":
            priority = NotificationPriority.HIGH
            emoji = "🎉"
            header = "INTERVIEW SCHEDULED"
        elif alert_type == "new_application":
            priority = NotificationPriority.MEDIUM
            emoji = "📤"
            header = "APPLICATION SENT"
        elif alert_type == "rejection":
            priority = NotificationPriority.LOW
            emoji = "❌"
            header = "NOTICE RECEIVED"
        else:
            emoji = "📋"
            header = alert_type.replace("_", " ").title()
        
        message = f"""*{emoji} {header}*

📎 *{opp['name']}*
🏢 {opp.get('company', 'N/A')}
📊 ATS: {opp.get('ats', 'N/A')}
💰 ${opp.get('salary', 0):,}/mo

_Status: {opp.get('status', 'Unknown')}_
"""
        
        return message, priority
    
    def get_opportunities(self):
        """Fetch opportunities from Notion"""
        from notion_client import Client
        
        notion = Client(auth=self.load_file("~/.config/notion/api_key"))
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
                
                opportunities.append({
                    "id": page['id'],
                    "name": name,
                    "company": company,
                    "status": status,
                    "salary": salary,
                    "ats": ats,
                    "last_contact": props.get('Last Contact', {}).get('date', {}).get('start', '')
                })
        
        return opportunities
    
    def check_alerts(self):
        """Check for new alerts"""
        should_notify, reason = self.prefs.should_notify("status_change")
        if not should_notify:
            print(f"Notifications disabled: {reason}")
            return
        
        opportunities = self.get_opportunities()
        
        # Load previous state
        state_file = self.workspace / ".notification_state.json"
        if state_file.exists():
            with open(state_file) as f:
                previous = json.load(f)
        else:
            previous = {}
        
        current = {}
        alerts = []
        
        for opp in opportunities:
            opp_id = opp['id']
            current[opp_id] = opp['status']
            
            # Detect changes
            if opp_id in previous:
                if previous[opp_id] != opp['status']:
                    # Status changed
                    alert_type = self.map_status_to_alert(opp['status'])
                    should_alert, _ = self.prefs.should_notify(alert_type)
                    
                    if should_alert:
                        message, priority = self.format_opportunity(opp, alert_type)
                        alerts.append({
                            "type": alert_type,
                            "priority": priority,
                            "message": message,
                            "opportunity": opp,
                            "old_status": previous[opp_id],
                            "new_status": opp['status']
                        })
            else:
                # New opportunity
                should_alert, _ = self.prefs.should_notify("new_application")
                if should_alert:
                    message, priority = self.format_opportunity(opp, "new_application")
                    alerts.append({
                        "type": "new_application",
                        "priority": priority,
                        "message": message,
                        "opportunity": opp
                    })
        
        # Save state
        with open(state_file, 'w') as f:
            json.dump(current, f)
        
        return alerts
    
    def map_status_to_alert(self, status):
        """Map Notion status to alert type"""
        status_map = {
            "Interview": "interview",
            "Offer": "offer",
            "Rejected": "rejection",
            "Applied": "new_application"
        }
        return status_map.get(status, "status_change")
    
    def check_followups(self):
        """Check for follow-up reminders"""
        should_notify, _ = self.prefs.should_notify("followup_reminder")
        if not should_notify:
            return []
        
        opportunities = self.get_opportunities()
        followups = []
        today = datetime.now()
        
        for opp in opportunities:
            if opp['status'] in ['Offer', 'Rejected', 'Complete']:
                continue
            
            last_contact = opp.get('last_contact', '')
            if last_contact:
                last_date = datetime.strptime(last_contact, "%Y-%m-%d")
                days_ago = (today - last_date).days
                
                if days_ago in self.prefs.config["followup_days"]:
                    followups.append({
                        **opp,
                        "days_ago": days_ago
                    })
        
        return followups
    
    def send_summary(self):
        """Send daily summary"""
        opportunities = self.get_opportunities()
        
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
        
        followups = self.check_followups()
        
        message = f"""🌅 *DAILY BRIEFING* - {today.strftime('%B %d')}

📊 *PIPELINE*
Total: {len(opportunities)}

*By Status:*
  📤 Applied: {status_counts.get('Applied', 0)}
  📞 Call: {status_counts.get('Call', 0)}
  🎯 Interview: {status_counts.get('Interview', 0)}
  🏆 Offer: {status_counts.get('Offer', 0)}
  ❌ Rejected: {status_counts.get('Rejected', 0)}

*ATS Scores:*
  🟢 80+: {ats_buckets['80+']} | 🟡 70-79: {ats_buckets['70-79']}
  🟠 60-69: {ats_buckets['60-69']} | 🔴 <60: {ats_buckets['50-59'] + ats_buckets['<50']}

💰 *Avg Salary:* ${total_salary // count_salary:,}/mo (n={count_salary})

🔔 *Follow-ups:* {len(followups)}
"""
        
        if followups:
            message += "\n*Needs Attention:*\n"
            for f in sorted(followups, key=lambda x: -x['days_ago'])[:5]:
                message += f"  ⏰ {f['name'][:40]} ({f['company']})\n"
        
        self.send_telegram(message, NotificationPriority.LOW)
        return message
    
    def run_alerts(self):
        """Run alert check and send notifications"""
        alerts = self.check_alerts()
        
        for alert in sorted(alerts, key=lambda x: x['priority'].value, reverse=True):
            self.send_telegram(
                alert["message"],
                alert["priority"],
                buttons=[
                    {"text": "✅ View", "data": f"view_{alert['opportunity']['id']}"},
                    {"text": "⏰ Remind", "data": f"remind_{alert['opportunity']['id']}"}
                ]
            )
        
        # Also check follow-ups
        followups = self.check_followups()
        if followups:
            message = f"""🔔 *FOLLOW-UP REMINDERS*

*{len(followups)} opportunities need attention:*
"""
            for f in followups:
                urgency = "🚨" if f['days_ago'] >= 14 else "⏰"
                message += f"\n{urgency} *{f['name']}*\n  {f['company']} - {f['days_ago']} days"
            
            self.send_telegram(message, NotificationPriority.MEDIUM)
        
        return len(alerts)


if __name__ == "__main__":
    import sys
    
    notify = EnhancedNotifications()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "--config":
            notify.prefs.configure()
        elif cmd == "--test":
            notify.send_telegram("🧪 *Test Notification*\n\nYour notification system is working!", NotificationPriority.MEDIUM)
        elif cmd == "--alerts":
            alerts = notify.check_alerts()
            print(f"Found {len(alerts)} alerts")
            for a in alerts:
                print(f"  - {a['type']}: {a['opportunity']['name']}")
        elif cmd == "--summary":
            notify.send_summary()
        elif cmd == "--check":
            count = notify.run_alerts()
            print(f"Sent {count} notifications")
        else:
            print(f"Unknown command: {cmd}")
    else:
        # Default: run alerts
        count = notify.run_alerts()
        print(f"Processed {count} alerts")
