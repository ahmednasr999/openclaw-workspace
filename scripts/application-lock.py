#!/usr/bin/env python3
"""
application-lock.py - Distributed lock service for job applications.

Prevents duplicate job submissions by using SQLite-based locking mechanism.
Handles lock acquisition, release, and timeout auto-release.

Usage:
  from application_lock import ApplicationLockService
  
  lock_service = ApplicationLockService()
  if lock_service.acquire_lock("Google", "Senior PM"):
      try:
          # Submit application
          submit_to_notion(...)
      finally:
          lock_service.release_lock("Google", "Senior PM")
  else:
      print("Job already being processed")
"""

import sqlite3
import os
import time
import hashlib
from datetime import datetime
from pathlib import Path


class ApplicationLockService:
    """Manages application locks to prevent duplicate submissions."""
    
    def __init__(self, db_path="/root/.openclaw/workspace/data/nasr-pipeline.db"):
        self.db_path = db_path
        self.process_id = os.getpid()
        self.lock_timeout = 300  # 5 minutes in seconds
        self._init_table()
    
    def _init_table(self):
        """Create the application_locks table if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS application_locks (
                    lock_key TEXT PRIMARY KEY,
                    company TEXT NOT NULL,
                    title TEXT NOT NULL,
                    locked_at INTEGER NOT NULL,
                    locked_by TEXT NOT NULL
                )
            """)
            
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to initialize locks table: {e}")
    
    def _normalize_key(self, company, title):
        """
        Create a normalized lock key from company and title.
        Uses composite key: LOWER(company || '|' || title)
        """
        normalized = f"{company}|{title}".lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _get_stale_locks(self, conn):
        """Find and auto-release locks older than timeout period."""
        cursor = conn.cursor()
        current_time = int(time.time())
        stale_threshold = current_time - self.lock_timeout
        
        cursor.execute("""
            SELECT lock_key, company, title, locked_at, locked_by
            FROM application_locks
            WHERE locked_at < ?
        """, (stale_threshold,))
        
        stale = cursor.fetchall()
        
        if stale:
            for lock_key, company, title, locked_at, locked_by in stale:
                age_seconds = current_time - locked_at
                print(f"[LOCK] Auto-releasing stale lock: {company} | {title} "
                      f"(age: {age_seconds}s, held by pid {locked_by})")
                
                cursor.execute("DELETE FROM application_locks WHERE lock_key = ?", (lock_key,))
            
            conn.commit()
        
        return stale
    
    def acquire_lock(self, company, title):
        """
        Attempt to acquire a lock for a job application.
        
        Returns:
            True if lock acquired successfully
            False if already locked or on error
        """
        lock_key = self._normalize_key(company, title)
        current_time = int(time.time())
        locked_by = str(self.process_id)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for and release stale locks
            self._get_stale_locks(conn)
            
            # Check if lock exists
            cursor.execute("""
                SELECT locked_at, locked_by
                FROM application_locks
                WHERE lock_key = ?
            """, (lock_key,))
            
            existing = cursor.fetchone()
            
            if existing:
                locked_at, locked_by_prev = existing
                age_seconds = current_time - locked_at
                print(f"[LOCK] Lock already held: {company} | {title} "
                      f"(age: {age_seconds}s, held by pid {locked_by_prev})")
                conn.close()
                return False
            
            # Acquire lock
            try:
                cursor.execute("""
                    INSERT INTO application_locks
                    (lock_key, company, title, locked_at, locked_by)
                    VALUES (?, ?, ?, ?, ?)
                """, (lock_key, company, title, current_time, locked_by))
                
                conn.commit()
                conn.close()
                print(f"[LOCK] Lock acquired: {company} | {title}")
                return True
                
            except sqlite3.IntegrityError:
                # Race condition: lock acquired between our check and insert
                conn.close()
                print(f"[LOCK] Race condition: lock acquired by another process: {company} | {title}")
                return False
        
        except sqlite3.Error as e:
            print(f"[LOCK] Database error acquiring lock: {e}")
            return False
    
    def release_lock(self, company, title):
        """
        Release a lock after successful application submission.
        
        Returns:
            True if lock was released
            False if lock didn't exist or on error
        """
        lock_key = self._normalize_key(company, title)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM application_locks
                WHERE lock_key = ?
            """, (lock_key,))
            
            rows_deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_deleted > 0:
                print(f"[LOCK] Lock released: {company} | {title}")
                return True
            else:
                print(f"[LOCK] No lock found to release: {company} | {title}")
                return False
        
        except sqlite3.Error as e:
            print(f"[LOCK] Database error releasing lock: {e}")
            return False
    
    def is_locked(self, company, title):
        """
        Check if a job is currently locked (being processed).
        
        Returns:
            True if locked
            False if not locked
        """
        lock_key = self._normalize_key(company, title)
        current_time = int(time.time())
        stale_threshold = current_time - self.lock_timeout
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for stale locks but don't delete (just check)
            cursor.execute("""
                SELECT locked_at, locked_by
                FROM application_locks
                WHERE lock_key = ? AND locked_at >= ?
            """, (lock_key, stale_threshold))
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
        
        except sqlite3.Error as e:
            print(f"[LOCK] Database error checking lock: {e}")
            return False
    
    def get_lock_status(self, company, title):
        """
        Get detailed lock status for debugging.
        
        Returns:
            dict with lock info, or None if not locked
        """
        lock_key = self._normalize_key(company, title)
        current_time = int(time.time())
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT company, title, locked_at, locked_by
                FROM application_locks
                WHERE lock_key = ?
            """, (lock_key,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                company_l, title_l, locked_at, locked_by = row
                age_seconds = current_time - locked_at
                is_stale = age_seconds > self.lock_timeout
                
                return {
                    "company": company_l,
                    "title": title_l,
                    "locked_at": locked_at,
                    "locked_by_pid": locked_by,
                    "age_seconds": age_seconds,
                    "is_stale": is_stale,
                    "lock_timeout": self.lock_timeout,
                }
            
            return None
        
        except sqlite3.Error as e:
            print(f"[LOCK] Database error getting lock status: {e}")
            return None
    
    def list_all_locks(self):
        """List all active locks."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT company, title, locked_at, locked_by
                FROM application_locks
                ORDER BY locked_at DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return rows
        
        except sqlite3.Error as e:
            print(f"[LOCK] Database error listing locks: {e}")
            return []
    
    def cleanup_all_locks(self):
        """Force cleanup all locks (use with caution)."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM application_locks")
            deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            print(f"[LOCK] Cleaned up {deleted} locks")
            return deleted
        
        except sqlite3.Error as e:
            print(f"[LOCK] Database error cleaning up locks: {e}")
            return 0


if __name__ == "__main__":
    # Simple CLI for testing
    import sys
    
    service = ApplicationLockService()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 application-lock.py acquire <company> <title>")
        print("  python3 application-lock.py release <company> <title>")
        print("  python3 application-lock.py check <company> <title>")
        print("  python3 application-lock.py status <company> <title>")
        print("  python3 application-lock.py list")
        print("  python3 application-lock.py cleanup")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "acquire" and len(sys.argv) >= 4:
        company = sys.argv[2]
        title = sys.argv[3]
        if service.acquire_lock(company, title):
            print(f"SUCCESS: Lock acquired for {company} | {title}")
            sys.exit(0)
        else:
            print(f"FAILED: Lock already held or error")
            sys.exit(1)
    
    elif command == "release" and len(sys.argv) >= 4:
        company = sys.argv[2]
        title = sys.argv[3]
        if service.release_lock(company, title):
            print(f"SUCCESS: Lock released for {company} | {title}")
            sys.exit(0)
        else:
            print(f"FAILED: No lock found")
            sys.exit(1)
    
    elif command == "check" and len(sys.argv) >= 4:
        company = sys.argv[2]
        title = sys.argv[3]
        if service.is_locked(company, title):
            print(f"LOCKED: {company} | {title}")
            sys.exit(0)
        else:
            print(f"FREE: {company} | {title}")
            sys.exit(1)
    
    elif command == "status" and len(sys.argv) >= 4:
        company = sys.argv[2]
        title = sys.argv[3]
        status = service.get_lock_status(company, title)
        if status:
            print(f"Lock Status: {company} | {title}")
            print(f"  Held by PID: {status['locked_by_pid']}")
            print(f"  Age: {status['age_seconds']}s")
            print(f"  Stale: {status['is_stale']}")
            print(f"  Timeout: {status['lock_timeout']}s")
        else:
            print(f"Not locked: {company} | {title}")
    
    elif command == "list":
        locks = service.list_all_locks()
        if locks:
            print(f"Active locks ({len(locks)}):")
            for company, title, locked_at, locked_by in locks:
                age = int(time.time()) - locked_at
                print(f"  {company} | {title} (age: {age}s, pid: {locked_by})")
        else:
            print("No active locks")
    
    elif command == "cleanup":
        count = service.cleanup_all_locks()
        print(f"Cleaned up {count} locks")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
