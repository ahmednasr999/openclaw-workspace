# Office Hours

Reframe before executing. Three forcing questions that surface hidden assumptions before any multi-step work begins.

## When to Trigger

- User requests a multi-step task (build X, create Y, set up Z)
- User describes a problem without a clear solution
- User asks for something that could be interpreted multiple ways
- NOT for: simple lookups, single-step tasks, or explicit instructions

## Workflow

### Step 1: Detect Intent
If the request is ambiguous or multi-step, enter office-hours mode.
If the request is clear and single-step, skip this skill.

### Step 2: Ask the Three Questions
Present these questions conversationally, not as a checklist:

1. **What problem are you trying to solve?**
   - Not "what do you want me to build" — what's the pain?
   - Listen for the real problem behind the feature request

2. **What does success look like in 30 days?**
   - Forces concrete outcomes, not vague goals
   - "I'll know it worked when..."

3. **What's the biggest risk if we're wrong?**
   - Surfaces hidden stakes
   - Calibrates effort to risk

### Step 3: Reframe if Needed
If the answers reveal a different problem than the original request:
- State the reframe clearly: "You asked for X, but what you're describing is Y"
- Propose 2-3 approaches with tradeoffs
- Recommend one with reasoning

### Step 4: Write the Brief
After alignment, write a brief to `memory/briefs/YYYY-MM-DD-{slug}.md`:

```markdown
# Brief: {Title}

## Problem
{The real problem, not the feature request}

## Success Criteria
{What success looks like in 30 days}

## Risk
{Biggest risk if we're wrong}

## Approach
{Chosen approach with reasoning}

## Next Steps
{Concrete actions}
```

### Step 5: Hand Off
The brief becomes the input for downstream agents. Reference it when spawning sub-agents.

## Anti-Patterns

- ❌ Asking all three questions as a numbered list (feels like an interrogation)
- ❌ Skipping straight to building without understanding the problem
- ❌ Over-applying to simple requests ("what time is it?" doesn't need office hours)
- ❌ Writing briefs for trivial tasks

## Eval Checklist

See `eval/checklist.md`
