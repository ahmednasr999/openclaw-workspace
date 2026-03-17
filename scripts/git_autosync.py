#!/usr/bin/env python3
"""
Git Auto-Sync — Hourly commits with automatic pushes
Prevents lost work by committing all changes
"""

import subprocess, os, sys
from datetime import datetime

REPO_PATH = "/root/.openclaw/workspace"

def run(cmd, check=True):
    """Run a shell command"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=REPO_PATH)
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(f"   Error: {result.stderr}")
        return False, result.stderr
    return True, result.stdout

def get_staged_changes():
    """Get list of staged changes"""
    success, output = run("git diff --cached --name-only")
    if not success:
        return []
    return [f for f in output.strip().split('\n') if f]

def get_unstaged_changes():
    """Get list of unstaged changes"""
    success, output = run("git diff --name-only")
    if not success:
        return []
    return [f for f in output.strip().split('\n') if f]

def get_untracked_files():
    """Get list of untracked files"""
    success, output = run("git ls-files --others --exclude-standard")
    if not success:
        return []
    return [f for f in output.strip().split('\n') if f]

def check_merge_conflicts():
    """Check for unmerged files"""
    success, output = run("git ls-files -u")
    return bool(output.strip())

def commit_all():
    """Commit all changes"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Get all changes
    staged = get_staged_changes()
    unstaged = get_unstaged_changes()
    untracked = get_untracked_files()
    
    if not staged and not unstaged and not untracked:
        print(f"🕐 {now} — No changes to sync")
        return True, "no_changes"
    
    # Add all changes
    run("git add -A")
    
    # Get staged changes after adding
    staged = get_staged_changes()
    
    # Build commit message
    if staged:
        files = ", ".join(staged[:5])
        if len(staged) > 5:
            files += f" (+{len(staged)-5} more)"
        msg = f"sync: {now} — {files}"
    else:
        msg = f"sync: {now} — auto-commit"
    
    # Commit
    success, output = run(f'git commit -m "{msg}"')
    if not success:
        return False, output
    
    return True, msg

def push():
    """Push to remote"""
    success, output = run("git push origin main")
    if not success:
        # Check if it's a merge conflict
        if "conflict" in output.lower() or "merge" in output.lower():
            print("⚠️  Merge conflict detected, notifying user")
            return False, "conflict"
        print(f"❌ Push failed: {output}")
        return False, output
    
    return True, "pushed"

def sync():
    """Main sync function"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n🔄 Git Auto-Sync — {now}")
    print("-" * 50)
    
    # Check for merge conflicts first
    if check_merge_conflicts():
        print("⚠️  Merge conflicts detected — skipping sync")
        return False, "conflict"
    
    # Commit
    success, msg = commit_all()
    if not success:
        print(f"❌ Commit failed: {msg}")
        return False, msg
    
    if msg == "no_changes":
        print("🕐 No changes to sync")
        return True, "no_changes"
    
    print(f"✅ Committed: {msg[:60]}...")
    
    # Push
    success, result = push()
    if not success:
        if result == "conflict":
            print("⚠️  Push failed — merge conflict")
            return False, "conflict"
        print(f"❌ Push failed: {result}")
        return False, result
    
    print("🚀 Pushed to GitHub")
    return True, "synced"

def send_telegram_notification(success, status):
    """Send notification to Telegram"""
    if status == "no_changes":
        return  # Don't notify for no changes
    
    if success:
        text = f"✅ Git Auto-Sync\n\nSynced workspace to GitHub"
    else:
        text = f"⚠️ Git Auto-Sync\n\nFailed: {status}"
    
    subprocess.run(
        ["openclaw", "message", "send", "--target", "telegram:866838380", "--message", text],
        capture_output=True
    )

if __name__ == "__main__":
    success, status = sync()
    
    # Only notify on changes
    if status != "no_changes":
        send_telegram_notification(success, status)
    
    sys.exit(0 if success else 1)
