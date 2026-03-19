# Evaluation Loop - The Core Autoresearch Engine

## Baseline Run

Before any changes, run the skill on ALL test inputs and score:

1. For each test input:
   - Run the target skill exactly as written
   - Score the output against every checklist question (PASS/FAIL)
   - Save output to `baseline/test-[n].md`

2. Calculate baseline score:
   - Score = (total passes) / (total checks across all tests) * 100
   - Record per-question pass rates (this reveals which questions fail most)

3. Log baseline: `echo "0\tbaseline\t-\t[score]%\t-" >> log.tsv`

## Improvement Loop

For each iteration:

### 1. Diagnose
Look at which checklist questions are failing:
- Sort by failure rate (highest first)
- Focus on the SINGLE most-failing question
- Read the failing outputs - what pattern causes the failure?

### 2. Hypothesize
Form a specific, testable change:
- "Add a rule that says X"
- "Add a bad example showing pattern Y"
- "Reword instruction Z to be more specific"
- "Add a constraint: never do W"

**ONE change per iteration. Never batch changes.**
This is critical - if you change two things and the score goes up, you don't know which one helped. If it goes down, you don't know which one hurt.

### 3. Apply
Make the change to `skill-snapshot.md`:
- Record exactly what changed (before/after diff)
- Keep the change minimal and surgical

### 4. Test
Run the modified skill on ALL test inputs:
- Score every output against every checklist question
- Save outputs to `iterations/iter-[n]/test-[n].md`

### 5. Compare
Calculate new score vs previous best:
- Score improved → **KEEP** the change
- Score same or dropped → **REVERT** to previous version
- Record decision and reasoning

### 6. Log
Append to `log.tsv`:
```
[iteration]\t[change_description]\t[keep/revert]\t[new_score]%\t[delta]
```

### 7. Repeat
Go back to step 1 with the updated (or reverted) skill.

## Variance Handling

AI output is non-deterministic. To handle variance:
- Run each test input ONCE per iteration (not multiple times - too expensive)
- BUT: if a change shows < 3% improvement, run the test inputs a SECOND time to confirm the gain is real
- If the second run doesn't confirm, treat as no improvement and REVERT

## What Changes Are Allowed

✅ **Allowed modifications:**
- Add specific rules or constraints
- Add bad examples / anti-patterns
- Add good examples
- Reword existing instructions for clarity
- Add formatting constraints
- Reorder instructions (put critical rules first)

❌ **Never modify:**
- The skill's core purpose or identity
- The YAML frontmatter
- File references in modular skills (those point to real files)
- External tool calls or commands
- Security boundaries or permissions
