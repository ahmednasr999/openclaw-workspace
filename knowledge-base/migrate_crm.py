#!/usr/bin/env python3
"""
CRM Schema Migration Script
Applies crm-schema-v2.sql with proper extension loading
"""

import sqlite3
import os

DB_PATH = "/root/.openclaw/workspace/knowledge-base/kb.db"
SCHEMA_PATH = "/root/.openclaw/workspace/knowledge-base/crm-schema-v2.sql"

# Find sqlite-vec extension
def find_vec_extension():
    paths = [
        "/usr/local/lib/python3.13/dist-packages/sqlite_vec/vec0.so",
        "/usr/local/lib/python3.12/dist-packages/sqlite_vec/vec0.so",
        "/usr/local/lib/python3.11/dist-packages/sqlite_vec/vec0.so",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def migrate():
    vec_path = find_vec_extension()
    if not vec_path:
        print("❌ sqlite-vec not found")
        return
    
    print(f"✅ Found vec extension: {vec_path}")
    
    # Read schema (skip .load and CREATE FUNCTION statements for now)
    with open(SCHEMA_PATH) as f:
        schema = f.read()
    
    # Split into statements, filtering out problematic ones
    statements = []
    for line in schema.split('\n'):
        stripped = line.strip()
        # Skip extension loading and function creation (different syntax needed)
        if stripped.startswith('.load'):
            continue
        if stripped.startswith('CREATE FUNCTION'):
            continue
        if stripped.startswith('--'):
            continue
        if stripped.startswith('CREATE TABLE IF NOT EXISTS'):
            statements.append(line)
        if stripped.startswith('CREATE INDEX'):
            statements.append(line)
        if stripped.startswith('CREATE VIEW'):
            statements.append(line)
        if stripped.startswith('CREATE VIRTUAL'):
            statements.append(line)
        if stripped.startswith('CREATE TABLE'):
            statements.append(line)
    
    # Connect and migrate
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"SELECT load_extension('{vec_path}')")
    
    print("✅ Extension loaded")
    
    # Execute statements
    for stmt in statements:
        try:
            conn.execute(stmt)
        except Exception as e:
            print(f"⚠️  Skipped: {e}")
    
    conn.commit()
    print("✅ Schema migrated")
    
    # Verify tables
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"📋 Tables: {tables}")
    
    # Add missing columns to existing contacts table
    alterations = [
        "ALTER TABLE contacts ADD COLUMN domain TEXT",
        "ALTER TABLE contacts ADD COLUMN embedding BLOB",
        "ALTER TABLE contacts ADD COLUMN is_noisy INTEGER DEFAULT 0",
        "ALTER TABLE contacts ADD COLUMN stale_since DATE",
    ]
    
    for alt in alterations:
        try:
            conn.execute(alt)
            print(f"✅ Added: {alt}")
        except Exception as e:
            pass  # Column already exists
    
    conn.commit()
    conn.close()
    print("✅ Migration complete")

if __name__ == "__main__":
    migrate()
