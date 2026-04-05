---
description: "Notes on skill shaping methodology: how to design and improve OpenClaw skills"
type: reference
topics: [knowledge, system-ops]
updated: 2026-03-14
---

# Shaping Skills

*Source: rjs/shaping-skills (GitHub)*
*Saved: 2026-02-21*

---

## What It Is

Skills for Claude Code based on **Shape Up** methodology from Basecamp.

## The Two Skills

### 1. /shaping
- Iterate on problem (requirements) AND solution (shapes)
- Separates "what you need" from "how you build it"
- Fit checks to see what's solved

### 2. /breadboarding
- Map system into:
  - UI affordances (what users can do)
  - Code affordances (how it works)
  - Wiring (how parts connect)
- Shows everything in one view
- Good for slicing into vertical scopes

---

## The Hook: Ripple Check

Reminds Claude to check for ripple effects when editing .md files.

**Setup:**
```bash
# Symlink hook
ln -s ~/.local/share/shaping-skills/hooks/shaping-ripple.sh ~/.claude/hooks/shaping-ripple.sh

# Add to settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/shaping-ripple.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

---

## Case Study

[Shaping 0-1 with Claude Code](https://x.com/rjs/status/2020184079350563263) - builds a project from scratch using these skills.

---

## How It Works

### Before Building:
1. Shape the problem (what's the real need?)
2. Shape the solution (how might we build it?)
3. Fit check (does this solve it?)

### During Building:
- Breadboard the system
- Check for ripple effects
- Slice into vertical scopes

---

## Our Use Case

This could help us:
- Better define requirements before building
- Avoid over-engineering
- Break projects into manageable pieces

---

## Related to Our Framework

This aligns with **Ashpreet's Levels**:
- Level 1: Agent with tools
- +Shaping: Better requirements first
- +Breadboarding: System design before coding

**Instead of jumping in and building, we shape first.**

---

## Key Quote

> "Separate what you need from how you might build it."

---

## Installation (For Claude Code on Mac)

```bash
git clone https://github.com/rjs/shaping-skills.git ~/.local/share/shaping-skills
ln -s ~/.local/share/shaping-skills/breadboarding ~/.claude/skills/breadboarding
ln -s ~/.local/share/shaping-skills/shaping ~/.claude/skills/shaping
```

---

*This is for Claude Code, not OpenClaw - but the methodology applies to any agent workflow.*
