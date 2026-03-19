---
name: skill-autoresearch
description: "Meta-skill that auto-improves any other skill using the Karpathy autoresearch loop. Run it on any skill to go from 60% pass rate to 90%+. Usage: 'run autoresearch on my [skill name] skill'. Triggers on 'improve this skill', 'optimize skill', 'autoresearch', 'skill is inconsistent', or 'skill fails sometimes'. Based on Ole Lehmann's implementation of Karpathy's autoresearch method."
metadata: {"openclaw":{"emoji":"🔬"}}
---

# Skill Autoresearch

Auto-improves any skill by running it in a loop, scoring the output, making one small change, and keeping or reverting based on the score.

**This SKILL.md is orchestrator only. All rules live in sub-files.**

---

## Workflow

### Phase 1 - Setup (read `instructions/setup.md`)
1. Identify the target skill to improve
2. Read the target skill's SKILL.md (and any sub-files if modular)
3. Define test inputs (realistic scenarios the skill should handle)
4. Build or load the evaluation checklist

### Phase 2 - Baseline (read `instructions/eval-loop.md`)
5. Run the target skill on ALL test inputs
6. Score each output against the checklist
7. Record baseline score (% of checks passing)

### Phase 3 - Improvement Loop (read `instructions/eval-loop.md`)
8. Analyze which checklist items are failing most
9. Make ONE small, atomic change to the skill instructions
10. Re-run on all test inputs
11. Re-score against checklist
12. If score improved: KEEP the change
13. If score dropped or stayed same: REVERT
14. Log the iteration to `eval/autoresearch-log.tsv`
15. Repeat from step 8

### Phase 4 - Completion (read `instructions/completion.md`)
16. Stop when: score hits 95%+ three times in a row, OR 10 iterations with no improvement, OR max 20 iterations
17. Save improved skill as `[skill-name].improved.md` (original untouched)
18. Generate improvement report
19. Ask user to review and approve changes

### Links
- `instructions/setup.md` - Setup and checklist building
- `instructions/eval-loop.md` - The core improvement loop
- `instructions/completion.md` - Stop conditions and reporting
- `eval/checklist-template.md` - Template for building checklists
- `examples/good-checklists.md` - Example checklists for common skill types
