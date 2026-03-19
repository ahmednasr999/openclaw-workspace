# Completion - Stop Conditions and Reporting

## Stop Conditions (any of these)

1. **Target reached:** Score hits 95%+ on THREE consecutive iterations
2. **Plateau:** 5 consecutive iterations with no improvement (all reverted)
3. **Max iterations:** 20 iterations total (hard cap to prevent runaway)
4. **User interrupt:** User asks to stop

## Output

### 1. Improved Skill File
Save the final improved version:
- For monolithic skills: `skills/[name]/SKILL.improved.md`
- For modular skills: save modified instruction files to `skills/[name]/instructions/[file].improved.md`
- **NEVER overwrite the original.** The user decides when to promote.

### 2. Improvement Report
Generate and display:

```
AUTORESEARCH COMPLETE
=====================
Skill: [skill name]
Baseline score: [X]%
Final score: [Y]%
Improvement: +[delta]%
Iterations: [n]
Changes kept: [k] / Changes reverted: [r]

Changes made:
1. [Change 1 - description] → +[delta]%
2. [Change 2 - description] → +[delta]%
3. [Change 3 - reverted] → -[delta]%
...

Per-checklist improvement:
- [Question 1]: [before]% → [after]%
- [Question 2]: [before]% → [after]%
...

Recommendation: [PROMOTE / REVIEW FIRST / MINIMAL GAIN]
```

### 3. Diff
Show a clean diff of original vs improved skill instructions. Only show what changed, not the whole file.

## Promotion

When the user is ready to adopt the changes:
1. Back up the original: `cp SKILL.md SKILL.backup.md`
2. Copy improved version over original
3. Delete the .improved.md and .backup.md files
4. Rebuild workspace index: `bash skills/workspace-index/generate-index.sh`

## When NOT to Run Autoresearch

- Skills that don't produce measurable output (e.g., setup skills, config skills)
- Skills that require external API calls per run (too expensive to loop)
- Skills where "good" is purely subjective and can't be checklistified
- Skills that are already at 95%+ (diminishing returns)
