# AFK Queue Consumer - Morning Briefing Integration

The AFK queue (`memory/agents/afk-queue.jsonl`) collects actions blocked during midnight-6AM Cairo.
The morning briefing MUST process this queue.

## Morning Briefing Integration

### During Briefing Pipeline (add to run-briefing-pipeline.sh)
After the standard briefing sections, add:

```
=== AFK Queue ===
Actions queued overnight for your review:
```

### For Each Queued Item
Read `memory/agents/afk-queue.jsonl`. For each entry:

1. **Present to Ahmed** with context:
   ```
   🕐 {timestamp} | {agent} wanted to: {action}
   Details: {args_summary}
   Reason blocked: AFK mode
   ```

2. **Offer action buttons** (Telegram inline):
   - [✅ Approve] - execute the action now
   - [✏️ Modify] - Ahmed edits before executing
   - [❌ Skip] - discard the queued action

3. **On Approve**: Execute the original tool call with the stored arguments
4. **On Skip**: Log to audit as "afk_queue_skipped" with reason
5. **On Modify**: Present the arguments for editing, then execute modified version

### Queue Entry Format (what gets written during AFK)
```json
{
  "timestamp": "ISO",
  "agent": "CMO",
  "tool": "LINKEDIN_CREATE_LINKED_IN_POST",
  "args": {"author": "urn:li:person:mm8EyA56mj", "commentary": "...", "visibility": "PUBLIC"},
  "args_summary": "LinkedIn post about AI in healthcare, 1200 chars",
  "reason": "AFK mode - queued for morning review",
  "priority": "normal",
  "auto_approve": false,
  "context": "Part of daily content pipeline"
}
```

### Auto-Approve Rules
Some items can be auto-approved without Ahmed's input:
- `auto_approve: true` AND `priority: "normal"` → execute automatically
- Pre-approved cron outputs (from cron_scheduled exceptions)
- System health notifications

### Queue Cleanup
After processing:
1. Move processed entries to `memory/agents/afk-queue-archive.jsonl` (append)
2. Clear `memory/agents/afk-queue.jsonl`
3. Log: "AFK queue processed: {approved} approved, {skipped} skipped, {modified} modified"

### If Queue is Empty
Skip the AFK Queue section entirely. Don't show "No queued items."
