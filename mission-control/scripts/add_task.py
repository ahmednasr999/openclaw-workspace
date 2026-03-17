#!/usr/bin/env python3
"""Add a task to Mission Control via command line."""

import sqlite3
import sys
from datetime import datetime

DB_PATH = "/root/.openclaw/workspace/mission-control/mission-control.db"


def add_task(title, description=None, assignee="Ahmed", priority="Medium", 
             category="Task", status="Inbox", due_date=None):
    """Add a task to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO tasks (title, description, assignee, status, priority, category, dueDate, completedDate, relatedTo, createdAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        title,
        description,
        assignee,
        status,
        priority,
        category,
        due_date,
        None,
        None,
        datetime.now().isoformat()
    ))
    
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return task_id


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: add_task.py 'Task title' [--description 'desc'] [--assignee Ahmed|OpenClaw|Both] [--priority High|Medium|Low] [--category Job Search|Content|Networking|Applications|Interviews|Task]")
        sys.exit(1)
    
    title = sys.argv[1]
    description = None
    assignee = "Ahmed"
    priority = "Medium"
    category = "Task"
    
    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--description" and i + 1 < len(sys.argv):
            description = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--assignee" and i + 1 < len(sys.argv):
            assignee = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--priority" and i + 1 < len(sys.argv):
            priority = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--category" and i + 1 < len(sys.argv):
            category = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    task_id = add_task(title, description, assignee, priority, category)
    print(f"✅ Task added successfully! ID: {task_id}")
    print(f"   Title: {title}")
    print(f"   Assignee: {assignee}")
    print(f"   Priority: {priority}")
    print(f"   Category: {category}")
