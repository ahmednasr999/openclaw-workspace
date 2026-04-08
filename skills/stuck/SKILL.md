# Stuck Skill - Get Unstuck Protocol

When an agent hits a wall and can't proceed, this structured protocol finds a way forward.

## When This Fires
- Tool call failed AND error recovery (retry + alternative) also failed
- Agent has been working on the same sub-problem for >3 attempts
- Agent explicitly recognizes it's blocked ("I'm not sure how to...", "This isn't working...")
- Sub-agent returns without completing its task

## The Protocol (follow in order, stop when unstuck)

### Step 1: Restate the Goal (5 seconds)
Write one sentence: "I'm trying to {goal} but {blocker}."
This forces clarity. Often the restatement reveals the real issue.

### Step 2: List What Was Tried (30 seconds)
Bullet list of every approach attempted and why each failed.
Pattern recognition: Are all attempts the same type? (e.g., all API-based, all browser-based)

### Step 3: Try 3 Alternative Approaches (2 minutes max)
Generate three approaches that are DIFFERENT IN KIND from what was tried:
- If code failed → try a CLI tool
- If direct API failed → try Composio or proxy
- If automated approach failed → try scraping
- If complex approach failed → try the simplest possible version
- If VPS approach failed → try Ahmed-Mac node

Execute the most promising alternative. If it works → done.

### Step 4: Search for Solutions (1 minute)
- `web_search` for the specific error message or problem
- `lcm_grep` for similar past problems in memory
- Check `memory/lessons-learned.md` for known fixes
- Check `TOOLS.md` for documented workarounds

### Step 5: Check Memory for Past Fixes (30 seconds)
Read `memory/lessons-learned.md` - has this exact problem been solved before?
Search `memory/agents/daily-*.md` for similar issues.
If found → apply the documented fix.

### Step 6: Decompose the Problem (1 minute)
Break the goal into smaller sub-goals. Which specific sub-goal is blocked?
Can the other sub-goals proceed while this one is escalated?
Partial progress > total block.

### Step 7: Escalate with Full Context
If still stuck after Steps 1-6, escalate:

**To parent agent (if sub-agent):**
```
STUCK: {goal}
TRIED: {list of approaches}
ALTERNATIVES TRIED: {list}
SEARCHED: {what was searched}
SPECIFIC BLOCKER: {exact issue}
SUGGESTION: {best guess at solution}
```

**To Ahmed (if top-level):**
Keep it brief: "Blocked on {X}. Tried {Y} and {Z}. Need {specific thing} to proceed."

## Anti-Patterns
- ❌ Reporting "I can't do this" without trying alternatives
- ❌ Asking Ahmed for help before exhausting Steps 1-6
- ❌ Trying the same approach repeatedly with minor variations
- ❌ Giving up silently (returning incomplete work without flagging)
- ❌ Spending more than 5 minutes total on this protocol
