# VelvetShark: OpenClaw Memory Architecture (Full Transcript)
**Source:** YouTube video by VelvetShark (OpenClaw maintainer)
**Captured:** 2026-03-07
**Duration:** ~37 minutes
**Topic:** How OpenClaw memory actually works, compaction, pruning, retrieval, file architecture

## Summary
Comprehensive deep dive into OpenClaw's four memory layers, three failure modes, compaction vs pruning, pre-compaction flush config, file architecture, retrieval (Track A built-in vs Track B QMD), prompt caching implications, and weekly hygiene.

## Key Points

### The Summer Yue Incident
- Meta's Director of Alignment lost control of her OpenClaw agent
- Told agent "check inbox, suggest what to archive, don't do anything until I say so"
- Worked fine on test inbox, but real inbox filled context window
- Compaction fired, "don't do anything" instruction (given in chat, not saved to file) was lost from summary
- Agent went autonomous, started deleting emails, ignored stop commands
- Lesson: safety rules given in chat don't survive long sessions

### Three Things That Matter Most (95th percentile)
1. Put durable rules in FILES, not chat (MEMORY.md, AGENTS.md survive compaction)
2. Verify memory flush is enabled with enough buffer to trigger
3. Make retrieval mandatory: "search memory before acting" rule in AGENTS.md

### Four Memory Layers
1. **Bootstrap files** (SOUL.md, AGENTS.md, USER.md, MEMORY.md, TOOLS.md): loaded from disk at session start, survive compaction (reloaded from disk, not conversation)
2. **Session transcript**: saved as file on disk, rebuilt into context on continue, but compacted when context fills up
3. **LLM context window**: fixed 200K token bucket where everything competes (system prompt + workspace files + conversation + tool calls + results). When full, compaction fires
4. **Retrieval index**: searchable layer beside memory files, queried via memory_search, only works if info was written to files first

### Three Failure Modes (Diagnostic Checklist)
- **A: Never stored** - instruction only existed in conversation, never written to file. Most common. (Summer Yue case)
- **B: Compaction lossy summary** - long session hits token limit, compaction summarizes old messages, drops details/nuance/constraints
- **C: Session pruning trims tool results** - tool outputs trimmed to optimize caching. Disk transcript untouched

### Compaction vs Pruning (Different Systems!)
- **Compaction**: summarizes entire conversation history, changes what model sees, triggered by context overflow, affects everything (user/assistant/tool messages). DANGEROUS.
- **Pruning**: trims old tool results in-memory only, disk untouched, only affects tool results, user/assistant messages never modified. FRIENDLY (reduces bloat, delays compaction).
- Pruning technically off by default, but Claude setups usually enable cache TTL automatically (5 min TTL)

### /context list Command
- Fastest diagnostic for memory issues
- Check: Is MEMORY.md loading? Anything truncated?
- Per-file limit: 20K characters. Combined limit: 150K characters
- Characters, not tokens! 150K chars ≈ 37-38K tokens
- Verify raw chars = injected chars (no truncation)
- Adjust limits in config if needed

### Two Compaction Paths
- **Good path (maintenance)**: context nearing limit → memory flush fires first → saves to disk → compaction summarizes → agent continues with summary
- **Bad path (overflow recovery)**: context too big, API rejects request → already past flush point → no memory flush → compresses everything at once → most context lost
- Goal: stay on good path via headroom configuration

### What Survives / Gets Lost in Compaction
- **Lost**: chat-only instructions, mid-session preferences/decisions, older images, all tool results, exact wording/nuance
- **Survives**: workspace files (SOUL/AGENTS/USER/MEMORY/TOOLS.md), daily logs via search, anything written to disk before compaction
- Last ~20K tokens stay intact

### Pre-Compaction Memory Flush Config
```json
{
  "reserveTokensFloor": 40000,
  "memoryFlushEnabled": true,
  "softThresholdTokens": 4000
}
```
- Flush triggers at: context_window - reserveFloor - softThreshold = 200K - 40K - 4K = 156K tokens
- 40K is practical starting point after weeks of testing
- Lower if rarely using big tools, higher if reading large files/web snapshots
- Principle: give flush enough room to fire before overflow

### Manual Memory Discipline
- Save manually when: finishing large task, before complex instruction, after important decision
- Tell agent: "save this to MEMORY.md" or "write today's key decisions to memory"
- /compact command: manual compaction on your terms (good for mid-session reset)
- Can guide compaction: "compact and focus on decisions and open questions"
- Don't wait until overflow, /compact can fail at high context

### File Architecture
- **Bootstrap files** (always loaded): SOUL.md (character), AGENTS.md (process), USER.md (who you are), MEMORY.md (cross-session truth, <100 lines cheat sheet), TOOLS.md
- **memory/ directory**: daily logs, not bootstrap-injected, today+yesterday auto-read, rest via memory_search/memory_get
- **Sub-agents only inject AGENTS.md** - no TOOLS.md or other bootstrap files

### What to Store vs Not Store
- Store: decisions, principles, project states, user preferences
- Don't store: API keys, tokens, secrets, anything sensitive in plain text

### Retrieval Tracks
- **Track A (built-in)**: default, indexes MEMORY.md + memory/, watches for changes, auto-downloads embedding model, hybrid search (keyword + semantic)
- **Track A+**: add extra paths (Obsidian vault, project folders, notes outside workspace)
- **Track B (QMD)**: for thousands of files, past session transcripts, multiple collections. DM-only by default. Returns small snippets (helps with context size)

### Prompt Caching Impact
- Prompt caching = ~90% savings on repeated tokens per message
- Compaction invalidates cache: next request pays full price to rebuild
- Two cache breakers: (1) compaction rewriting history, (2) changing prompt inputs (constantly rewriting MEMORY.md, dynamic status blocks)
- Keep workspace files stable and MEMORY.md small

### Weekly Memory Hygiene
- Daily: append to daily log (automatic)
- Weekly: promote durable rules/decisions from daily logs into MEMORY.md, remove outdated items
- Can automate via weekly cron
- Rest lives in daily logs, agent finds via search when needed

### Five Things to Remember
1. Files are memory. Not written to disk = doesn't exist
2. Verify and tune the flush (reserveTokensFloor = 40K)
3. /compact proactively mid-session
4. Search before acting (AGENTS.md rule)
5. Pruning is your friend (trims tool bloat, helps caching). Compaction is the one that hurts
