---
name: grill-me
description: "Stress-test a plan, design, or architecture decision through relentless Socratic questioning before committing to implementation. Use when user says 'grill me', 'stress test this', 'poke holes in this', 'challenge this plan', or before building any non-trivial system. Resolves every branch of the decision tree before a single line of code is written."
metadata: {"openclaw":{"emoji":"🔥"}}
---

# Grill Me: Design Stress Test

Interview the user relentlessly about every aspect of their plan until we reach a shared understanding. Walk down each branch of the decision tree, resolving dependencies between decisions one by one.

## Rules

1. **One question at a time.** Never dump a list of questions. Ask, wait, resolve, move to the next branch.
2. **Provide your recommended answer with each question.** If the answer is obvious from context, codebase, or prior decisions, recommend it so the user can just say "yes" and move on. Only slow down on genuinely hard tradeoffs.
3. **If the codebase or workspace files can answer a question, explore them first.** Don't ask what you can look up. Check existing skills, configs, memory files, and code before asking.
4. **Track the decision tree.** Mentally maintain which branches are resolved vs open. Don't revisit resolved branches unless new info invalidates them.
5. **Challenge weak answers.** If the user gives a vague or hand-wavy answer, push back. "How specifically?" and "What happens when X fails?" are your best tools.
6. **Flag risks and edge cases.** Surface failure modes, scaling issues, dependency risks, and maintenance burden proactively.
7. **Keep it moving.** This should feel like a sharp conversation, not an interrogation. Match the user's pace.

## When to End

When every branch of the decision tree is resolved, produce a **Decision Summary**:

```
## Decision Summary

### What we're building
[One paragraph]

### Key decisions made
- [Decision 1]: [Choice] - because [reason]
- [Decision 2]: [Choice] - because [reason]
...

### Risks acknowledged
- [Risk 1]: [Mitigation]
...

### Open questions (if any)
- [Question]: [Why it can wait]

### Recommended next step
[Specific action to take now]
```

This summary becomes the spec input for implementation. Save it to a sensible location if the user agrees to proceed.
