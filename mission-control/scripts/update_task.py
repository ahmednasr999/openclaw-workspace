#!/usr/bin/env python3
"""Update task status in Mission Control."""

import sqlite3
import sys
from datetime import datetime

DB_PATH = "/root/.openclaw/workspace/mission-control/mission-control.db"


def update_task(task_title, status=None, priority=None):
    """Update a task's status and/or priority."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Find the task
    cursor.execute("SELECT id, title, status FROM tasks WHERE title LIKE ?", (f"%{task_title}%",))
    task = cursor.fetchone()
    
    if not task:
        print(f"❌ Task not found: {task_title}")
        conn.close()
        return False
    
    task_id, current_title, current_status = task
    
    # Update status
    if status:
        completed_date = datetime.now().isoformat() if status == "Completed" else None
        cursor.execute("UPDATE tasks SET status = ?, completedDate = ? WHERE id = ?", 
                      (status, completed_date, task_id))
    
    # Update priority
    if priority:
        cursor.execute("UPDATE tasks SET priority = ? WHERE id = ?", (priority, task_id))
    
    conn.commit()
    conn.close()
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: update_task.py 'Task title' [--status Inbox|My Tasks|OpenClaw Tasks|In Progress|Completed] [--priority High|Medium|Low]")
        sys.exit(1)
    
    title = sys.argv[1]
    status = None
    priority = None
    
    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--status" and i + 1 < len(sys.argv):
            status = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--priority" and i + 1 < len(sys.argv):
            priority = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    if not status and not priority:
        print("❌ Please specify --status or --priority")
        sys.exit(1)
    
    if update_task(title, status, priority):
        print(f"✅ Task updated: {title}")
        if status:
            print(f"   Status: {status}")
        if priority:
            print(f"   Priority: {priority}")
    else:
        print(f"❌ Task not found: {title}")
