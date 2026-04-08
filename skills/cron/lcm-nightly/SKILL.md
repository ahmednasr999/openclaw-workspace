---
name: lcm-nightly
description: "Nightly LCM (Lossless Context Management) database health: inspect tree compaction, prune stale summaries, report LCM stats to Telegram."
---

# LCM Nightly Health Check

Run every command in sequence. Report actual numbers. Never delete without archiving. Deliver report to Telegram group.

## Context
- Timezone: Africa/Cairo
- Notify: telegram:866838380
- LCM DB: /root/.openclaw/lcm.db
- Deliver to: -1003882622947:7 (Mission Control group)

---

## Step 1: LCM Database Stats

Run all queries against the SQLite LCM database.

```bash
sqlite3 /root/.openclaw/lcm.db "
SELECT 'CONVERSATIONS', COUNT(*) FROM conversations
UNION ALL SELECT 'MESSAGES', COUNT(*) FROM messages
UNION ALL SELECT 'SUMMARIES', COUNT(*) FROM summaries
UNION ALL SELECT 'LEAF_SUMMARIES', COUNT(*) FROM summaries WHERE kind='leaf'
UNION ALL SELECT 'CONDENSED_SUMMARIES', COUNT(*) FROM summaries WHERE kind='condensed'
UNION ALL SELECT 'TOTAL_TOKENS', SUM(token_count) FROM messages
UNION ALL SELECT 'TOTAL_MESSAGE_PARTS', COUNT(*) FROM message_parts;
" 2>/dev/null

echo "---"
echo "=== LAST 7 DAYS SUMMARY CREATION ==="
sqlite3 /root/.openclaw/lcm.db "
SELECT date(created_at) as created_date, COUNT(*) as count, SUM(token_count) as tokens
FROM summaries
WHERE created_at >= datetime('now', '-7 days')
GROUP BY date(created_at)
ORDER BY created_date DESC;" 2>/dev/null

echo "---"
echo "=== LARGEST SUMMARIES BY TOKEN COUNT ==="
sqlite3 /root/.openclaw/lcm.db "
SELECT summary_id, kind, depth, token_count, descendant_count, descendant_token_count,
       ROUND(100.0*descendant_token_count/NULLIF(token_count,0), 1) as compression_ratio
FROM summaries
ORDER BY token_count DESC
LIMIT 10;" 2>/dev/null

echo "---"
echo "=== MOST ACTIVE CONVERSATIONS ==="
sqlite3 /root/.openclaw/lcm.db "
SELECT c.conversation_id, c.session_id, COUNT(m.message_id) as msg_count,
       SUM(m.token_count) as total_tokens,
       MAX(c.updated_at) as last_activity,
       COUNT(s.summary_id) as summary_count
FROM conversations c
LEFT JOIN messages m ON m.conversation_id = c.conversation_id
LEFT JOIN summaries s ON s.conversation_id = c.conversation_id
GROUP BY c.conversation_id
ORDER BY total_tokens DESC
LIMIT 10;" 2>/dev/null
```

---

## Step 2: Identify Stale Conversations

A conversation is "stale" if no activity in 14+ days and it has more than 10 messages (worth keeping summaries for) but fewer than 3 summaries.

```bash
echo "=== STALE CONVERSATIONS (14+ days, active but under-summarized) ==="
sqlite3 /root/.openclaw/lcm.db "
SELECT c.conversation_id, c.session_id,
       COUNT(m.message_id) as msg_count,
       SUM(m.token_count) as total_tokens,
       COUNT(s.summary_id) as summary_count,
       c.updated_at as last_activity,
       ROUND(JULIANDAY('now') - JULIANDAY(c.updated_at)) as days_stale
FROM conversations c
LEFT JOIN messages m ON m.conversation_id = c.conversation_id
LEFT JOIN summaries s ON s.conversation_id = c.conversation_id
GROUP BY c.conversation_id
HAVING days_stale > 14
   AND msg_count > 10
   AND summary_count < 3
ORDER BY total_tokens DESC
LIMIT 20;" 2>/dev/null

echo "---"
echo "=== ORPHANED SUMMARIES (completely disconnected from DAG) ==="
echo "Note: Condensed summaries at depth>0 connect via summary_parents, not summary_messages."
echo "Only flag summaries with ZERO connections (no message links, no parent links, no child links)."
sqlite3 /root/.openclaw/lcm.db "
SELECT COUNT(*) as true_orphans FROM summaries s
WHERE NOT EXISTS (SELECT 1 FROM summary_messages sm WHERE sm.summary_id = s.summary_id)
AND NOT EXISTS (SELECT 1 FROM summary_parents sp WHERE sp.summary_id = s.summary_id)
AND NOT EXISTS (SELECT 1 FROM summary_parents sp WHERE sp.parent_summary_id = s.summary_id);" 2>/dev/null

echo ""
echo "=== UNCOMPACTED CONVERSATIONS (30+ messages, 0 summaries) ==="
sqlite3 /root/.openclaw/lcm.db "
SELECT c.conversation_id, c.session_id,
  (SELECT COUNT(*) FROM messages WHERE conversation_id = c.conversation_id) as msg_count,
  (SELECT SUM(token_count) FROM messages WHERE conversation_id = c.conversation_id) as total_tokens
FROM conversations c
WHERE (SELECT COUNT(*) FROM messages WHERE conversation_id = c.conversation_id) >= 30
AND (SELECT COUNT(*) FROM summaries WHERE conversation_id = c.conversation_id) = 0
ORDER BY msg_count DESC
LIMIT 10;" 2>/dev/null
```

---

## Step 3: LCM Tree Depth Analysis

Check how deep the summary tree goes per conversation.

```bash
echo "=== SUMMARY TREE DEPTH BY CONVERSATION ==="
sqlite3 /root/.openclaw/lcm.db "
SELECT conversation_id,
       COUNT(*) as total_summaries,
       MAX(depth) as max_depth,
       COUNT(CASE WHEN kind='leaf' THEN 1 END) as leaves,
       COUNT(CASE WHEN kind='condensed' THEN 1 END) as condensed,
       SUM(token_count) as total_summary_tokens
FROM summaries
GROUP BY conversation_id
ORDER BY total_summaries DESC
LIMIT 15;" 2>/dev/null
```

---

## Step 4: Check lcm_expand Works (Spot Test)

Pick the most recent summary and verify lcm_expand can retrieve it.

```bash
RECENT_SUM=$(sqlite3 /root/.openclaw/lcm.db "SELECT summary_id FROM summaries ORDER BY created_at DESC LIMIT 1;" 2>/dev/null)
echo "Testing lcm_expand on: $RECENT_SUM"
# Note: lcm_expand is a tool call, not a bash command
# For the report, note whether the summary exists and is accessible
if [ -n "$RECENT_SUM" ]; then
    sqlite3 /root/.openclaw/lcm.db "SELECT summary_id, kind, depth, token_count, LENGTH(content) as content_chars FROM summaries WHERE summary_id='$RECENT_SUM';" 2>/dev/null
fi
```

---

## Step 5: Disk & DB Size Check

```bash
echo "=== LCM DATABASE SIZE ==="
ls -lh /root/.openclaw/lcm.db 2>/dev/null
du -sh /root/.openclaw/lcm.db* 2>/dev/null

echo "=== WAL CHECKPOINT RECOMMENDATION ==="
# If WAL file is large, a checkpoint is needed
WAL_SIZE=$(ls -l /root/.openclaw/lcm.db-wal 2>/dev/null | awk '{print $5}')
echo "WAL file size: $WAL_SIZE"
WAL_CHECKPOINT_LOG="/tmp/lcm_wal_checkpoint_$(date +%Y%m%d).log"
if [ -n "$WAL_SIZE" ] && [ "$WAL_SIZE" -gt 10485760 ]; then
    echo "ACTION: WAL checkpoint recommended (>10MB)"
    sqlite3 /root/.openclaw/lcm.db "PRAGMA wal_checkpoint(PASSIVE);" > "$WAL_CHECKPOINT_LOG" 2>&1
    CP_EXIT=$?
    if [ $CP_EXIT -eq 0 ]; then
        echo "Checkpoint OK."
    else
        echo "WARNING: Checkpoint returned exit code $CP_EXIT. Check $WAL_CHECKPOINT_LOG"
        echo "ACTION: Checkpoint failed — WAL may need manual vacuum."
    fi
else
    echo "WAL size OK."
fi
```

---

## Step 6: Compile Report

Based on all outputs above, compile a Telegram report:

```
LCM Nightly Report — [DATE]
DB: /root/.openclaw/lcm.db

STATS:
- Conversations: [X]
- Messages: [X]
- Total message tokens: [X]
- Summaries: [X] (leaf + condensed)
- LCM tree depth max: [X]
- DB size: [X]MB

WEEK SUMMARY:
[summaries created per day table]

TOP ACTIVE CONVERSATIONS:
[top 3 by token count]

STALE CONVERSATIONS: [X] found
[if X > 0: list top 5 by token count]

TREE HEALTH:
- Conversations with 0 summaries (30+ msgs): [X]
- Conversations with 3+ summaries: [X]
- True orphaned summaries (disconnected from DAG): [X]
- Uncompacted tokens (30+ msg convs with 0 summaries): [X]

ACTIONS TAKEN:
[list any checkpoint or other actions]
```

---

## Step 7: Deliver to Telegram

Send the compiled report to the Mission Control group using the message tool (action=send, channel=telegram, target=-1003882622947).

**Track consecutive delivery failures:**
```bash
ERROR_LOG="/root/.openclaw/workspace/memory/lcm-nightly-errors.md"
CONSECUTIVE_FILE="/tmp/lcm_delivery_failures.txt"

# Read current consecutive failure count
FAIL_COUNT=$(cat "$CONSECUTIVE_FILE" 2>/dev/null || echo "0")
echo "Consecutive delivery failures before this run: $FAIL_COUNT"

# After attempting delivery (from Step 6):
# If delivery SUCCEEDS: reset counter
# If delivery FAILS: increment counter, log to error file

# Reset on success (agent will set this if message.send succeeds):
# echo "0" > "$CONSECUTIVE_FILE"

# Escalate after 2 consecutive failures:
if [ "$FAIL_COUNT" -ge 2 ]; then
    echo "ESCALATION: 2+ consecutive Telegram delivery failures"
    echo "LCM Health Check report undelivered for $FAIL_COUNT runs" >> "$ERROR_LOG"
    echo "Manually review: $ERROR_LOG"
fi
```

---

---

## Step 5.5: Self-Healing — Auto-Compact Flagged Conversations

**Run this BEFORE compiling the report.** If Step 2 found conversations with 30+ messages and 0 summaries, auto-compact them now.

```bash
echo "=== SELF-HEALING: Running force-compact on uncompacted convos ==="
cd /root/.openclaw/workspace-cto/scripts && node --experimental-strip-types lcm-force-compact.mjs --mode all 2>&1
echo "Force-compact exit code: $?"
```

- If compaction ran successfully → note "Auto-compacted X sessions" in the report under ACTIONS TAKEN
- If compaction returned 0 candidates → note "No compaction needed"
- If compaction errored → log the error and continue to report (do not block delivery)

After running, re-check the uncompacted count:

```bash
sqlite3 /root/.openclaw/lcm.db "
SELECT COUNT(*) as still_uncompacted
FROM conversations c
WHERE (SELECT COUNT(*) FROM messages WHERE conversation_id = c.conversation_id) >= 30
AND (SELECT COUNT(*) FROM summaries WHERE conversation_id = c.conversation_id) = 0;" 2>/dev/null
```

Report the before/after counts. Quality gate passes (✅) only if still_uncompacted = 0.

---

## Error Handling
- Never delete rows from lcm.db directly
- Never truncate messages table
- If sqlite3 fails: report the error and continue to next step
- If Telegram delivery fails: log to /root/.openclaw/workspace/memory/lcm-nightly-errors.md, increment consecutive failure counter, escalate after 2 failures
- WAL checkpoint failure: log exit code, do not silently continue

## Quality Gates
- DB size less than 500MB
- WAL file less than 50MB after checkpoint
- Zero true orphaned summaries (completely disconnected from DAG - no summary_messages, no summary_parents in either direction)
- At least 1 summary created in the last 7 days
- No conversation with 30+ messages and 0 summaries (lowered from 50)
