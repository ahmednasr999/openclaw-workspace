#!/usr/bin/env python3
"""Clear stale OpenClaw context-engine maintenance tasks.

Narrow guardrail: only marks old queued/running `context_engine_turn_maintenance`
records as lost. These are deferred best-effort maintenance tasks; if one gets
stuck, it can keep a session lane looking busy and block replies.
"""
from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
import time
from pathlib import Path

DEFAULT_DB = Path("/root/.openclaw/tasks/runs.sqlite")
MIGRATED_DB = Path("/root/.openclaw/tasks/runs.sqlite.migrated")
DEFAULT_TTL_MINUTES = 15
TASK_KIND = "context_engine_turn_maintenance"
TASK_RUNS_TABLE = "task_runs"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default=str(DEFAULT_DB), help="task registry sqlite path")
    p.add_argument("--ttl-minutes", type=int, default=DEFAULT_TTL_MINUTES)
    p.add_argument("--apply", action="store_true", help="apply changes; otherwise dry-run")
    p.add_argument("--backup-dir", default="/root/.openclaw/tasks")
    return p.parse_args()


def has_table(db: Path, table: str) -> bool:
    if not db.exists():
        return False
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            row = con.execute(
                "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = ?",
                (table,),
            ).fetchone()
            return row is not None
        finally:
            con.close()
    except sqlite3.Error:
        return False


def main() -> int:
    args = parse_args()
    db = Path(args.db)
    if db == DEFAULT_DB and not has_table(db, TASK_RUNS_TABLE) and has_table(MIGRATED_DB, TASK_RUNS_TABLE):
        db = MIGRATED_DB
        print(f"INFO using migrated task registry: {db}")
    if not db.exists():
        print(f"ERROR db not found: {db}", file=sys.stderr)
        return 2
    if not has_table(db, TASK_RUNS_TABLE):
        print(f"ERROR db missing {TASK_RUNS_TABLE} table: {db}", file=sys.stderr)
        return 2

    ttl_ms = max(1, args.ttl_minutes) * 60 * 1000
    now_ms = int(time.time() * 1000)
    cutoff_ms = now_ms - ttl_ms

    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT task_id, status, owner_key, task, task_kind, created_at, started_at,
               last_event_at, progress_summary
          FROM task_runs
         WHERE task_kind = ?
           AND status IN ('queued','running')
           AND COALESCE(last_event_at, started_at, created_at, 0) < ?
         ORDER BY COALESCE(last_event_at, started_at, created_at, 0) ASC
        """,
        (TASK_KIND, cutoff_ms),
    ).fetchall()

    if not rows:
        print(f"OK no stale {TASK_KIND} tasks older than {args.ttl_minutes}m")
        return 0

    print(f"FOUND {len(rows)} stale {TASK_KIND} task(s) older than {args.ttl_minutes}m")
    for r in rows:
        last = r["last_event_at"] or r["started_at"] or r["created_at"] or 0
        age_s = int((now_ms - last) / 1000)
        print(f"- {r['task_id']} status={r['status']} age={age_s}s owner={r['owner_key']}")

    if not args.apply:
        print("DRY_RUN use --apply to mark these tasks lost")
        return 1

    backup_dir = Path(args.backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"runs.sqlite.backup-stale-context-{time.strftime('%Y%m%dT%H%M%S')}"
    shutil.copy2(db, backup)
    print(f"BACKUP {backup}")

    ids = [r["task_id"] for r in rows]
    placeholders = ",".join("?" for _ in ids)
    error = (
        f"Automatically marked stale {TASK_KIND} task lost after exceeding "
        f"{args.ttl_minutes}m TTL; safe deferred maintenance cleanup."
    )
    before = con.total_changes
    con.execute(
        f"""
        UPDATE task_runs
           SET status = 'lost',
               delivery_status = 'not_applicable',
               ended_at = ?,
               last_event_at = ?,
               error = ?,
               progress_summary = 'Stale deferred context maintenance cleared automatically.'
         WHERE task_id IN ({placeholders})
           AND task_kind = ?
           AND status IN ('queued','running')
        """,
        [now_ms, now_ms, error, *ids, TASK_KIND],
    )
    con.commit()
    print(f"CLEARED {con.total_changes - before} task(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
