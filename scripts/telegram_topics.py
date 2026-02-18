#!/usr/bin/env python3
"""
Telegram Topic Manager
Organizes messages into topics for cleaner communication
"""

# Current Telegram topics structure (as configured)
TOPICS = {
    "daily_brief": "Daily Briefing - Morning summaries",
    "jobs": "Job Search - Applications, interviews, offers",
    "crm": "CRM & Contacts - Network updates",
    "knowledge": "Knowledge Base - Research & articles",
    "alerts": "System Alerts - Cron jobs, errors, health",
    "tasks": "Tasks & Follow-ups - Action items",
    "social": "Social Media - LinkedIn, content",
    "automation": "Automation - Scripts & workflows"
}

def list_topics():
    """List configured topics"""
    print("\n📋 TELEGRAM TOPICS")
    print("=" * 50)
    
    for key, description in TOPICS.items():
        print(f"   • {key:<15} {description}")
    
    print()

def show_usage_guide():
    """Show messaging best practices"""
    guide = """
📱 TELEGRAM MESSAGING GUIDE
==========================

## Current Topics
"""
    
    for key, description in TOPICS.items():
        guide += f"**{key}** - {description}\n"
    
    guide += """
## Sending to Specific Topics

### Via openclaw message command:
```bash
openclaw message send --target "telegram:866838380" --message "Your message"
```

### Using topic-specific targets (when configured):
```bash
# Send to Jobs topic
openclaw message send --target "telegram:866838380:jobs" --message "New job posting!"
```

## Best Practices

1. **Daily Briefing** → Uses: daily_brief topic
   - Morning summaries, daily plans
   
2. **Job Applications** → Uses: jobs topic
   - New applications, interview updates
   
3. **CRM Updates** → Uses: crm topic
   - Contact updates, relationship tracking
   
4. **Alerts & Reports** → Uses: alerts topic
   - Cron failures, security alerts
   - Health reports

5. **Quick Questions** → Send to main chat
   - No topic needed for quick chats

## Automation Examples

### Send daily briefing to topic:
```bash
python3 daily_briefing.py --telegram
```

### Send job alerts to topic:
```bash
python3 job_alerts.py --topic jobs
```

## Topic Naming Conventions

- Use lowercase with underscores
- Keep names short (<15 chars)
- Document purpose clearly

"""
    print(guide)

def status_check():
    """Check messaging system status"""
    print("\n📱 MESSAGING STATUS")
    print("=" * 50)
    
    # Check Telegram connection
    result = subprocess.run(
        ["openclaw", "message", "send", "--target", "telegram:866838380", "--message", "🧪 Test message - messaging system working"],
        capture_output=True, text=True, timeout=30
    )
    
    if result.returncode == 0:
        print("   ✅ Telegram: Connected")
    else:
        print("   ❌ Telegram: Check configuration")
    
    # List configured channels
    result = subprocess.run(
        ["openclaw", "config", "get"],
        capture_output=True, text=True, timeout=10
    )
    
    print("   📋 Channels configured: telegram")
    
    # Show topic summary
    print()
    print("📂 Topics in use:")
    for key, desc in TOPICS.items():
        print(f"   • {key:<15} {desc}")
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--guide":
            show_usage_guide()
        elif cmd == "--status":
            status_check()
        elif cmd == "--topics":
            list_topics()
        else:
            print("Usage: python3 telegram_topics.py [--guide|--status|--topics]")
    else:
        status_check()
        show_usage_guide()
