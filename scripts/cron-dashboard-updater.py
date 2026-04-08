#!/usr/bin/env python3
"""
Cron Dashboard Updater
Discovers all crons (system + openclaw native) and updates the Notion Cron Dashboard.
Checks log files to determine last run status and schedules next runs.
"""

import os
import sys
import json
import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path
import requests
from zoneinfo import ZoneInfo

# Configuration
NOTION_DB_ID = "3268d599-a162-8188-b531-e25071653203"
NOTION_VERSION = "2022-06-28"
WORKSPACE_ROOT = "/root/.openclaw/workspace"
CAIRO_TZ = ZoneInfo("Africa/Cairo")


def load_notion_token():
    token = os.getenv("NOTION_TOKEN", "").strip()
    if token:
        return token

    config_path = Path(WORKSPACE_ROOT) / "config" / "notion.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            cfg = json.load(f)
        token = str(cfg.get("token", "")).strip()
        if token:
            return token

    raise RuntimeError("Missing Notion token. Set NOTION_TOKEN or config/notion.json")

# Cron log mappings (script path -> log file)
LOG_PATHS = {
    "daily-backup.sh": "/tmp/openclaw-backup.log",
    "archive-daily-notes.sh": "/tmp/openclaw-archive.log",
    "daily-snapshot.sh": "/tmp/openclaw-snapshot.log",
    "retention-backups.sh": "/tmp/openclaw-retention-backups.log",
    "retention-snapshots.sh": "/tmp/openclaw-retention-snapshots.log",
    "retention-caches.sh": "/tmp/openclaw-retention-caches.log",
    "disk-health-check.sh": "/tmp/disk-health-cron.log",
    "job-radar.sh": "/tmp/job-radar.log",
    "morning-brief.sh": "/tmp/morning-brief.log",
    "cron-watchdog-v3.sh": "/root/.openclaw/workspace/logs/watchdog/cron.log",
    "run-briefing-pipeline.sh": "/var/log/briefing/cron.log",
    "linkedin-autoresearch.py": "/tmp/linkedin-autoresearch.log",
    "autoresearch-job-review.py": "/tmp/autoresearch-job-review.log",
    "github-radar.sh": "/root/.openclaw/workspace/logs/github-radar.log",
    "key-health-check.sh": None,
    "token-health-check.sh": None,
    "x-radar.sh": "/root/.openclaw/workspace/logs/x-radar.log",
    "sie-360-checks.py": "/tmp/sie-360-checks.log",
    "weekly-agent-review.py": "/root/.openclaw/workspace/memory/cron-weekly-review.log",
    "rss-to-content-calendar.py": "/root/.openclaw/workspace/logs/rss-to-calendar.log",
    "content-factory-health-monitor.py": "/root/.openclaw/workspace/logs/cf-health.log",
    "cf-weekday-check.sh": None,
    "linkedin-auto-poster-safe.py": "/root/.openclaw/workspace/logs/linkedin-poster.log",
    "ontology-notion-sync.py": "/root/.openclaw/workspace/logs/ontology-sync.log",
    "ontology-pipeline-sync.py": "/root/.openclaw/workspace/logs/ontology-sync.log",
    "linkedin-engagement-agent.py": "/root/.openclaw/workspace/logs/linkedin-engagement.log",
}


class CronDashboardUpdater:
    def __init__(self):
        self.token = load_notion_token()
        self.db_id = NOTION_DB_ID
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }
        self.crons = []
        self.results = {"updated": 0, "created": 0, "errors": []}

    def parse_system_crontab(self):
        """Parse user crontab (actual active cron jobs)"""
        crons = []
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    parts = line.split(maxsplit=5)
                    if len(parts) < 6:
                        continue

                    minute, hour, day, month, dow = parts[:5]
                    command = parts[5]

                    crons.append({
                        "type": "system",
                        "schedule": f"{minute} {hour} {day} {month} {dow}",
                        "command": command,
                        "name": self._extract_script_name(command),
                    })
        except Exception as e:
            self.results["errors"].append(f"Error parsing crontab: {str(e)}")
        return crons

    def parse_openclaw_crons(self):
        """Parse openclaw native crons via 'openclaw cron list'"""
        try:
            result = subprocess.run(
                ["openclaw", "cron", "list"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0:
                return []

            crons = []
            lines = result.stdout.split("\n")
            
            # Find header line with dashes
            header_idx = -1
            for i, line in enumerate(lines):
                if "---" in line:
                    header_idx = i
                    break
            
            if header_idx < 0:
                return []

            # Parse data rows after header
            for line in lines[header_idx + 1:]:
                line = line.strip()
                if not line or "---" in line:
                    continue

                # Extract fields from space-separated table
                # Format: ID | Name | Schedule | Next | Last | Status | ...
                parts = line.split()
                if len(parts) < 3:
                    continue

                # Use regex to split more intelligently
                # Look for UUID pattern (ID), then name, then schedule components
                import re
                id_match = re.match(r'^([a-f0-9\-]+|[\w\-]+)\s+(.+)', line)
                if not id_match:
                    continue
                
                cron_id = id_match.group(1)
                rest = id_match.group(2)
                
                # Extract name (everything until first "cron" keyword)
                name_match = re.match(r'^(.+?)\s+cron\s+(.+)', rest)
                if name_match:
                    name = name_match.group(1).strip()
                    schedule_part = name_match.group(2).strip()
                    
                    crons.append({
                        "type": "openclaw",
                        "cron_id": cron_id,
                        "name": name,
                        "schedule": schedule_part,
                        "command": f"openclaw cron {cron_id}",
                    })
            
            return crons
        except Exception as e:
            self.results["errors"].append(f"Error parsing openclaw crons: {str(e)}")
            return []

    def _extract_script_name(self, command):
        """Extract script name from command"""
        # Handle complex commands like "cd ... && python3 ..."
        parts = command.split()
        for i, part in enumerate(parts):
            if part.endswith(".py") or part.endswith(".sh"):
                return Path(part).name
        return command.split("/")[-1]

    def get_last_run_status(self, script_name, log_path=None):
        """Determine last run status from log file"""
        if not log_path:
            log_path = LOG_PATHS.get(script_name)

        if not log_path or not Path(log_path).exists():
            return {
                "status": "⚠️ Unknown",
                "last_run": None,
                "error": "No log file found",
            }

        try:
            stat = os.stat(log_path)
            last_run = datetime.fromtimestamp(stat.st_mtime, tz=CAIRO_TZ)

            # Read last 50 lines to detect error
            with open(log_path, "r") as f:
                content = f.read()

            # Check for common error patterns
            error_patterns = [
                r"error",
                r"failed",
                r"exception",
                r"traceback",
                r"exit code",
            ]
            has_error = any(
                re.search(pattern, content, re.IGNORECASE) for pattern in error_patterns
            )

            return {
                "status": "❌ Failed" if has_error else "✅ OK",
                "last_run": last_run,
                "error": None if not has_error else "Check log for details",
            }
        except Exception as e:
            return {"status": "⚠️ Unknown", "last_run": None, "error": str(e)}

    def calculate_next_run(self, schedule_str):
        """Calculate next run time from cron expression (simplified)"""
        now = datetime.now(tz=CAIRO_TZ)

        # Parse basic cron format "minute hour day month dow"
        parts = schedule_str.split()
        if len(parts) < 5:
            return None

        minute_str, hour_str = parts[0], parts[1]

        # Simple parser - just get hour and minute
        try:
            if "*" in hour_str or "," in hour_str or "/" in hour_str:
                # Complex expression - estimate next run
                return now + timedelta(hours=1)

            hour = int(hour_str)
            minute = int(minute_str) if minute_str != "*" else 0

            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        except:
            return now + timedelta(hours=1)

    def notion_find_page(self, name):
        """Find existing page in Notion by name"""
        url = f"https://api.notion.com/v1/databases/{self.db_id}/query"
        data = {
            "filter": {
                "property": "Name",
                "title": {"equals": name},
            }
        }

        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            if response.status_code == 200:
                results = response.json().get("results", [])
                return results[0] if results else None
        except Exception as e:
            self.results["errors"].append(f"Error finding page '{name}': {str(e)}")
        return None

    def notion_create_page(self, cron_data):
        """Create a new page in the Notion database"""
        last_run_info = self.get_last_run_status(
            cron_data["name"], cron_data.get("log_path")
        )
        next_run = self.calculate_next_run(cron_data["schedule"])

        # Map status to Notion select option
        status_map = {
            "✅ OK": "37a2c83d-39ad-493c-a837-bffa65ba5a69",
            "❌ Failed": "cdacc20b-5ec4-41fb-b45f-a038a495a916",
            "⚠️ Unknown": "5ceefcdb-6030-4fa3-8fa4-0d56a8735b1a",
        }

        properties = {
            "Name": {"title": [{"text": {"content": cron_data["name"]}}]},
            "Schedule": {
                "rich_text": [{"text": {"content": cron_data["schedule"]}}]
            },
            "Last Status": {
                "select": {
                    "id": status_map.get(
                        last_run_info["status"],
                        "5ceefcdb-6030-4fa3-8fa4-0d56a8735b1a",
                    )
                }
            },
            "Enabled": {"checkbox": True},
        }

        if last_run_info["last_run"]:
            properties["Last Run"] = {
                "date": {"start": last_run_info["last_run"].isoformat()}
            }

        if next_run:
            properties["Next Run"] = {"date": {"start": next_run.isoformat()}}

        if "cron_id" in cron_data:
            properties["Cron ID"] = {
                "rich_text": [{"text": {"content": cron_data["cron_id"]}}]
            }

        url = "https://api.notion.com/v1/pages"
        data = {"parent": {"database_id": self.db_id}, "properties": properties}

        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            if response.status_code == 200:
                self.results["created"] += 1
                return response.json()
            else:
                self.results["errors"].append(
                    f"Error creating page for '{cron_data['name']}': {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.results["errors"].append(
                f"Exception creating page for '{cron_data['name']}': {str(e)}"
            )
        return None

    def notion_update_page(self, page_id, cron_data):
        """Update an existing page in the Notion database"""
        last_run_info = self.get_last_run_status(
            cron_data["name"], cron_data.get("log_path")
        )
        next_run = self.calculate_next_run(cron_data["schedule"])

        status_map = {
            "✅ OK": "37a2c83d-39ad-493c-a837-bffa65ba5a69",
            "❌ Failed": "cdacc20b-5ec4-41fb-b45f-a038a495a916",
            "⚠️ Unknown": "5ceefcdb-6030-4fa3-8fa4-0d56a8735b1a",
        }

        properties = {
            "Schedule": {
                "rich_text": [{"text": {"content": cron_data["schedule"]}}]
            },
            "Last Status": {
                "select": {
                    "id": status_map.get(
                        last_run_info["status"],
                        "5ceefcdb-6030-4fa3-8fa4-0d56a8735b1a",
                    )
                }
            },
        }

        if last_run_info["last_run"]:
            properties["Last Run"] = {
                "date": {"start": last_run_info["last_run"].isoformat()}
            }

        if next_run:
            properties["Next Run"] = {"date": {"start": next_run.isoformat()}}

        url = f"https://api.notion.com/v1/pages/{page_id}"
        data = {"properties": properties}

        try:
            response = requests.patch(url, headers=self.headers, json=data, timeout=10)
            if response.status_code == 200:
                self.results["updated"] += 1
                return response.json()
            else:
                self.results["errors"].append(
                    f"Error updating page '{cron_data['name']}': {response.status_code}"
                )
        except Exception as e:
            self.results["errors"].append(
                f"Exception updating page '{cron_data['name']}': {str(e)}"
            )
        return None

    def run(self):
        """Main execution"""
        print(f"[{datetime.now(CAIRO_TZ).isoformat()}] Starting Cron Dashboard Update...")

        # Discover crons
        system_crons = self.parse_system_crontab()
        openclaw_crons = self.parse_openclaw_crons()

        all_crons = system_crons + openclaw_crons
        print(f"Discovered {len(all_crons)} crons ({len(system_crons)} system, {len(openclaw_crons)} openclaw)")

        # Update Notion
        for cron in all_crons:
            existing = self.notion_find_page(cron["name"])
            if existing:
                self.notion_update_page(existing["id"], cron)
            else:
                self.notion_create_page(cron)

        # Output summary
        print(f"\nUpdate Summary:")
        print(f"  Created: {self.results['created']}")
        print(f"  Updated: {self.results['updated']}")
        if self.results["errors"]:
            print(f"  Errors: {len(self.results['errors'])}")
            for err in self.results["errors"]:
                print(f"    - {err}")

        # Output JSON summary
        summary = {
            "timestamp": datetime.now(CAIRO_TZ).isoformat(),
            "total_crons": len(all_crons),
            "system_crons": len(system_crons),
            "openclaw_crons": len(openclaw_crons),
            "notion_created": self.results["created"],
            "notion_updated": self.results["updated"],
            "errors": self.results["errors"],
            "crons": [
                {
                    "name": c["name"],
                    "schedule": c["schedule"],
                    "type": c["type"],
                    "last_status": self.get_last_run_status(c["name"]),
                }
                for c in all_crons
            ],
        }

        # Save to JSON
        summary_file = Path(WORKSPACE_ROOT) / "logs" / "cron-dashboard-summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"\nSummary saved to {summary_file}")
        return 0 if not self.results["errors"] else 1


if __name__ == "__main__":
    updater = CronDashboardUpdater()
    sys.exit(updater.run())
