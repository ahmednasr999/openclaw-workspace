# Verification Agent - Independent Quality Check

## Problem
Sub-agents mark their own work as done. No independent review. We've caught lazy completions - agents that claim "done" but left bugs, skipped edge cases, or didn't test. Self-grading is unreliable.

## Solution
A verification pattern that triggers automatically after sub-agent work. A separate agent reviews the output with fresh eyes and assigns PASS / FAIL / PARTIAL. The original agent cannot self-assign PASS.

## Trigger Conditions
Verification fires when ANY of these are true:
- Sub-agent touched 3+ files
- Sub-agent created a new script (any .py, .sh, .js file)
- Sub-agent modified a cron job or SKILL.md
- Sub-agent changed MEMORY.md, SOUL.md, TOOLS.md, or AGENTS.md
- Task was tagged as "critical" or "high-priority"

Verification SKIPS when:
- Simple file reads or appends
- Content writing (posts, drafts) - these have their own review flow
- Config changes under 5 lines
- Research-only tasks (no deliverable)

## Verification Checklist (6 checks)

### 1. Completeness
- Did the agent do what was asked? Not 80% of it.
- Are there TODOs or placeholders left in the code?

### 2. Correctness
- Does the code/config actually work? (Run it if possible)
- Are file paths correct? Do referenced files exist?

### 3. Safety
- No hardcoded credentials or API keys
- No destructive operations without confirmation
- Cron jobs have reasonable schedules (not every minute)

### 4. Integration
- Does it break existing workflows?
- Are imports/dependencies available?
- Does it follow existing patterns in the codebase?

### 5. Documentation
- Did the agent update relevant docs (TOOLS.md, AGENTS.md) if needed?
- Are new scripts documented with usage instructions?

### 6. Edge Cases
- What happens on empty input?
- What happens if a dependency is offline?
- Are error messages actionable?

## Verdict Format
```
## Verification Report

**Task:** [what was requested]
**Agent:** [who did the work]
**Files Changed:** [list]

### Checks
- [ ] Completeness: PASS/FAIL - [detail]
- [ ] Correctness: PASS/FAIL - [detail]
- [ ] Safety: PASS/FAIL - [detail]
- [ ] Integration: PASS/FAIL - [detail]
- [ ] Documentation: PASS/FAIL - [detail]
- [ ] Edge Cases: PASS/FAIL - [detail]

### Verdict: PASS / PARTIAL / FAIL
**Issues:** [if any]
**Fix Required:** [specific actions needed]
```

## Verdict Rules
- **PASS** (6/6 checks pass) → Work is accepted, notify CEO
- **PARTIAL** (4-5/6 pass, no safety fail) → Accept with noted issues, flag for follow-up
- **FAIL** (3 or fewer pass, OR safety fail) → Reject, send back to original agent with fix list

## Implementation Options

### Option A: Post-Spawn Hook (Recommended)
- After any sub-agent completes, CEO agent checks trigger conditions
- If triggered, spawn a verification sub-agent with:
  - Git diff of all changes
  - Original task description
  - The 6-point checklist
- Verification agent reviews and reports

### Option B: Skill-Based
- Create `skills/verify/SKILL.md` that any agent can invoke
- Agent calls "use verify skill" after completing work
- Problem: agents can skip it (fox guarding henhouse)

### Option C: Cron Sweep
- Hourly cron that checks recent git commits
- Runs verification on any commit from a sub-agent
- Problem: delayed feedback, harder to link to original task

**Recommendation: Option A** - it's immediate, mandatory, and the CEO agent controls it so sub-agents can't skip.

## Integration with Existing Flow
1. CEO spawns sub-agent for task
2. Sub-agent completes work, reports done
3. CEO checks trigger conditions
4. If triggered: spawn verification agent with diff + task context
5. Verification agent returns verdict
6. PASS → notify Ahmed. FAIL → send fix list back to sub-agent (or new sub-agent)
7. Log verdict to `memory/verification-logs/YYYY-MM-DD.md`

## Anti-Gaming Rules
- Verification agent gets ONLY the diff and task description, not the original agent's self-assessment
- Verification agent cannot see "this agent said it's done" - it judges independently
- If the same task fails verification twice, escalate to Ahmed
