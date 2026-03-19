---
name: skill-name-here
description: "One-paragraph description. Be pushy: include specific trigger phrases, contexts, and explicit 'ALWAYS use when...' guidance. Include what NOT to use (anti-overlap with similar skills). Make it hard to undertrigger."
metadata: {"openclaw":{"emoji":"🔧"}}
---

# Skill Name

One-line summary of what this skill does and why it exists.

**This SKILL.md is orchestrator only. All rules live in sub-files.**

---

## Workflow

### Phase 1 - Setup
1. [Pre-flight checks] → read `instructions/pre-flight.md`
2. [Load context/inputs] → read `instructions/[step-name].md`

### Phase 2 - Execute
3. [Core step 1] → read `instructions/[step-name].md`
4. [Core step 2] → read `instructions/[step-name].md`

### Phase 3 - Evaluate
5. Run quality checks → read `eval/checklist.md`
6. Revise if any checks fail

### Phase 4 - Deliver
7. [Output/delivery step] → read `templates/[template-name].md`

---

## Folder Structure

```
skill-name/
├── SKILL.md                    # This file - orchestrator only, NO rules
├── instructions/               # One file per concern
│   ├── pre-flight.md           # Blocking checks before execution
│   └── [step-name].md          # Instructions for each major step
├── eval/
│   └── checklist.md            # Pass/fail quality checks (3-6 items)
├── examples/
│   ├── good/                   # Annotated examples of great output
│   └── bad/                    # Anti-patterns to avoid
└── templates/
    └── [output-template].md    # Output format templates
```

### Design Rules
- SKILL.md contains ZERO rules - only workflow steps pointing to files
- Each instruction file covers ONE concern (don't mix voice rules with formatting rules)
- eval/checklist.md has 3-6 binary yes/no quality checks
- Examples go in examples/ not inline in instructions
- Each step loads ONLY what it needs (minimize context per step)

### Links
- `instructions/[file].md` - [description]
- `eval/checklist.md` - Quality checks
- `examples/` - Good and bad output examples
- `templates/` - Output format templates
