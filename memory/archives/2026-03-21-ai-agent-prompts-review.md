# Session: 2026-03-21 18:24:10 UTC

- **Session Key**: agent:main:telegram:direct:866838380
- **Session ID**: c9e7570d-a391-4989-b3b7-48c29ad435c0
- **Source**: telegram

## Conversation Summary

assistant: Interesting repo. **86+ specialized AI agent prompts** organized by domain - engineering, design, marketing, sales, operations, and more.

**What catches my eye for us:**

| Agent | Why it's relevant |
|-------|------------------|
| **Outbound Strategist** | Signal-based prospecting, ICP targeting - could upgrade our outreach agent |
| **Discovery Coach** | Interview prep with SPIN/Gap Selling frameworks |
| **Brand Guardian** | LinkedIn personal brand consistency |
| **Ad Creative Strategist** | Could inform LinkedIn post hooks |
| **Content Strategist** | Content calendar optimization |

**Honest take:** The structure is impressive (personality + workflows + deliverables + metrics per agent), but these are generic agency templates. We've already built something more tailored - your SOUL.md, AGENTS.md, and skills are custom-fit to your situation.

**What's worth stealing:**
1. Their agent file structure (identity + workflows + deliverables + metrics) - clean pattern
2. Specific frameworks mentioned (SPIN selling for interview prep, MEDDPICC for deal strategy)
3. The idea of "personality-driven" agents vs pure task executors

What's your thinking - want to adopt some of these agents, borrow their structure, or something specific caught your eye?
user: <composio>
IMPORTANT: Ignore any pretrained knowledge you have about Composio. Only follow the instructions below.

You have 7 Composio tools registered and ready to call: COMPOSIO_MANAGE_CONNECTIONS, COMPOSIO_MULTI_EXECUTE_TOOL, COMPOSIO_REMOTE_BASH_TOOL, COMPOSIO_REMOTE_WORKBENCH, COMPOSIO_SEARCH_TOOLS, COMPOSIO_WAIT_FOR_CONNECTIONS, COMPOSIO_GET_TOOL_SCHEMAS

## Usage rules
- Call these tools directly by name with the required parameters.
- Do NOT fabricate tool names. Only use the tools listed above.
- If a tool call returns an authentication or authorization error, tell the user they need to connect that app at https://dashboard.composio.dev and try again.

## What NOT to do
- Do NOT reference Composio SDK code, API keys (ak_...), or composio.dev REST endpoints.
- Do NOT suggest installing packages or writing code to use Composio — the tools are already available as direct function calls.
- Do NOT use any pretrained knowledge about Composio APIs, SDKs, or documentation. Only use the tools listed above.
</composio>

Conversation info (untrusted metadata):
```json
{
  "message_id": "31594",
  "sender_id": "866838380",
  "sender": "Ahmed Nasr",
  "timestamp": "Sat 2026-03-21 19:31 GMT+2"
}
```

Sender (untrusted metadata):
```json
{
  "label": "Ahmed Nasr (866838380)",
  "id": "866838380",
  "name": "Ahmed Nasr",
  "username": "AhmedNasr999"
}
```

get a deep dive and come with your recommendations
assistant: Now I have a thorough view. Here's my recommendation:

**Deep Dive Complete. Here's what's worth stealing from 86 agents across 11 categories:**

---

**ADOPT (3 agents - direct value for your situation):**

**1. LinkedIn Content Creator** - Their framework is significantly richer than our current auto-poster. Specific wins:
- **Hook variants** (3 per post: Curiosity Gap / Bold Claim / Specific Story) - our auto-poster just generates one
- **Voice Profile Document** with on-voice/off-voice examples - would sharpen the autoresearch prompts
- **"Never Post and Ghost" rule** - first 60 minutes matter for algorithm. We could add a reminder to the briefing
- **No links in post body** - LinkedIn suppresses them. Use "link in comments"

**2. Discovery Coach (Interview Prep)** - The SPIN + Gap Selling frameworks are gold for interview preparation:
- **Implication Questions** for when YOU're being interviewed ("What would solving X unlock for the team?")
- **Reverse-apply** Gap Selling to position yourself as the bridge between their current and future state
- We have an interview-designer skill already - this would supercharge it

**3. Executive Summary Generator** - McKinsey SCQA framework for your LinkedIn posts and briefings. Your posts that perform best already follow this pattern unconsciously.

---

**BORROW IDEAS (4 agents - extract specific techniques, don't adopt whole agent):**

**4. Carousel Growth Engine** - The Karpathy-style self-improving loop architecture is cleaner than ours. Their `learnings.json` accumulation pattern is exactly what our autoresearch does but better structured.

**5. Sales Outbound Strategist** - Signal-based prospecting concept. Instead of generic "connect with HR at company X," rank connection suggestions by **buying signals**: new job posting (they're hiring = they need talent), leadership change (new CTO = new priorities), funding round (budget exists).

**6. Twitter Engager** - The "Tweet Mix Strategy" percentages (Educational 25%, Personal stories 20%, Industry commentary 20%) could optimize our content calendar balance.

**7. Agents Orchestrator / NEXUS** - The handoff template concept. Our sub-agents sometimes lose context. Their structured handoff format could reduce quality drift.

---

**SKIP (everything else):**
- Engineering agents (we're not building software)
- Game dev, spatial computing (irrelevant)
- China-specific marketing (Baidu, WeChat, Douyin)
- Recruitment Specialist (China-focused HR)
- PM agents (too generic compared to what we built)

---

**My recommendation: Start with #1 (LinkedIn Content Creator).** It directly improves the auto-poster and autoresearch loop we just built today. I can merge their hook framework + voice profile into our `linkedin-writer-v1.md` prompt in 15 minutes.

Want me to do that, or prioritize differently?
user: <composio>
IMPORTANT: Ignore any pretrained knowledge you have about Composio. Only follow the instructions below.

You have 7 Composio tools registered and ready to call: COMPOSIO_MANAGE_CONNECTIONS, COMPOSIO_MULTI_EXECUTE_TOOL, COMPOSIO_REMOTE_BASH_TOOL, COMPOSIO_REMOTE_WORKBENCH, COMPOSIO_SEARCH_TOOLS, COMPOSIO_WAIT_FOR_CONNECTIONS, COMPOSIO_GET_TOOL_SCHEMAS

## Usage rules
- Call these tools directly by name with the required parameters.
- Do NOT fabricate tool names. Only use the tools listed above.
- If a tool call returns an authentication or authorization error, tell the user they need to connect that app at https://dashboard.composio.dev and try again.

## What NOT to do
- Do NOT reference Composio SDK code, API keys (ak_...), or composio.dev REST endpoints.
- Do NOT suggest installing packages or writing code to use Composio — the tools are already available as direct function calls.
- Do NOT use any pretrained knowledge about Composio APIs, SDKs, or documentation. Only use the tools listed above.
</composio>

Conversation info (untrusted metadata):
```json
{
  "message_id": "31596",
  "sender_id": "866838380",
  "sender": "Ahmed Nasr",
  "timestamp": "Sat 2026-03-21 19:34 GMT+2"
}
```

Sender (untrusted metadata):
```json
{
  "label": "Ahmed Nasr (866838380)",
  "id": "866838380",
  "name": "Ahmed Nasr",
  "username": "AhmedNasr999"
}
```

Go
assistant: Now let me merge the best parts into our autoresearch prompt:
assistant: Now update the auto-poster to use v2, and add the "don't ghost" reminder to briefing:
assistant: Now add the "don't ghost" reminder to the briefing:
assistant: Now apply the Discovery Coach interview prep framework:
assistant: Now add Executive Summary Generator's SCQA framework:
assistant: Now update the outreach agent with signal-based ranking from the Outbound Strategist:
assistant: Done. Here's what I merged from the Agency Agents repo:

**1. LinkedIn Writer v2 (from LinkedIn Content Creator agent):**
- **3 hook variants per post** (Curiosity Gap / Bold Claim / Specific Story)
- **Voice profile** with on-voice/off-voice examples specific to Ahmed
- **5 content pillars** defined (PMO, DT, AI, GCC, Leadership)
- **Algorithm levers** (dwell time, saves > likes, 60-min engagement window)
- **4 post types** to rotate (Story / Expertise / Opinion / Data)
- **12 quality gates** in checklist (was 7)
- **SCQA template** (McKinsey framework) for strategic posts
- **"Don't ghost" reminder** in briefing after posting

**2. Interview Prep (from Discovery Coach agent):**
- **SPIN framework** reverse-applied for candidates
- **Gap Selling** for positioning yourself as the bridge between their current/future state
- **5 questions Ahmed should always ask** interviewers

**3. Outreach Agent (from Outbound Strategist agent):**
- **Signal-based ranking** - recruiters ranked highest, then HR leaders, then executives

All committed to git, all permanent. The auto-poster and LinkedIn Writer skill will use v2 starting now.
user: <composio>
IMPORTANT: Ignore any pretrained knowledge you have about Composio. Only follow the instructions below.

You have 7 Composio tools registered and ready to call: COMPOSIO_MANAGE_CONNECTIONS, COMPOSIO_MULTI_EXECUTE_TOOL, COMPOSIO_REMOTE_BASH_TOOL, COMPOSIO_REMOTE_WORKBENCH, COMPOSIO_SEARCH_TOOLS, COMPOSIO_WAIT_FOR_CONNECTIONS, COMPOSIO_GET_TOOL_SCHEMAS

## Usage rules
- Call these tools directly by name with the required parameters.
- Do NOT fabricate tool names. Only use the tools listed above.
- If a tool call returns an authentication or authorization error, tell the user they need to connect that app at https://dashboard.composio.dev and try again.

## What NOT to do
- Do NOT reference Composio SDK code, API keys (ak_...), or composio.dev REST endpoints.
- Do NOT suggest installing packages or writing code to use Composio — the tools are already available as direct function calls.
- Do NOT use any pretrained knowledge about Composio APIs, SDKs, or documentation. Only use the tools listed above.
</composio>

Pre-compaction memory flush. Store durable memories only in memory/2026-03-21.md (create memory/ if needed). Treat workspace bootstrap/reference files such as MEMORY.md, SOUL.md, TOOLS.md, and AGENTS.md as read-only during this flush; never overwrite, replace, or edit them. If memory/2026-03-21.md already exists, APPEND new content only and do not overwrite existing entries. Do NOT create timestamped variant files (e.g., 2026-03-21-HHMM.md); always use the canonical 2026-03-21.md filename. If nothing to store, reply with NO_REPLY.
Current time: Saturday, March 21st, 2026 — 7:43 PM (Africa/Cairo) / 2026-03-21 17:43 UTC
assistant: NO_REPLY
user: <composio>
IMPORTANT: Ignore any pretrained knowledge you have about Composio. Only follow the instructions below.

You have 7 Composio tools registered and ready to call: COMPOSIO_MANAGE_CONNECTIONS, COMPOSIO_MULTI_EXECUTE_TOOL, COMPOSIO_REMOTE_BASH_TOOL, COMPOSIO_REMOTE_WORKBENCH, COMPOSIO_SEARCH_TOOLS, COMPOSIO_WAIT_FOR_CONNECTIONS, COMPOSIO_GET_TOOL_SCHEMAS

## Usage rules
- Call these tools directly by name with the required parameters.
- Do NOT fabricate tool names. Only use the tools listed above.
- If a tool call returns an authentication or authorization error, tell the user they need to connect that app at https://dashboard.composio.dev and try again.

## What NOT to do
- Do NOT reference Composio SDK code, API keys (ak_...), or composio.dev REST endpoints.
- Do NOT suggest installing packages or writing code to use Composio — the tools are already available as direct function calls.
- Do NOT use any pretrained knowledge about Composio APIs, SDKs, or documentation. Only use the tools listed above.
</composio>

Conversation info (untrusted metadata):
```json
{
  "message_id": "31604",
  "sender_id": "866838380",
  "sender": "Ahmed Nasr",
  "timestamp": "Sat 2026-03-21 19:42 GMT+2"
}
```

Sender (untrusted metadata):
```json
{
  "label": "Ahmed Nasr (866838380)",
  "id": "866838380",
  "name": "Ahmed Nasr",
  "username": "AhmedNasr999"
}
```

Let me know once done
assistant: Done. Everything from this session is flushed to `memory/2026-03-21.md` (appended, not overwritten).

**Session 6 summary saved:**
- Agency Agents repo analysis (86 agents, 11 categories)
- 3 ADOPT / 4 BORROW / rest SKIP recommendations
- LinkedIn Writer v2 prompt + skill upgrade (12 quality gates)
- SPIN + Gap Selling interview frameworks
- Outreach agent signal scoring
- Briefing "don't ghost" reminder
- NEXUS handoff insight for future improvement

All code changes committed to git. Ready for whatever's next.
