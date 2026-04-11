---
name: agent-content-pipeline
description: Safe content workflow (drafts/reviewed/revised/approved/posted) with human-in-the-loop approval, plus CLI to list/move/review and post to LinkedIn/X. Use when setting up a content pipeline, drafting content, managing review threads, or posting approved content.
---

# Content Pipeline Skill

Safe content automation with human-in-the-loop approval. Draft → Review → Approve → Post.

## Setup

```bash
npm install -g agent-content-pipeline
content init . # Creates folders + global config (in current directory)
```

For cryptographic approval signatures (password-protected):
```bash
content init . --secure
```

This creates:
- `drafts/` — work in progress (one post per file)
- `reviewed/` — human reviewed, awaiting your revision
- `revised/` — you revised, ready for another look
- `approved/` — human-approved, ready to post
- `posted/` — archive after posting
- `templates/` — review and customize before use
- `.content-pipeline/threads/` — feedback thread logs (not posted)

## Workflow Overview

```
drafts/ → reviewed/ → revised/ → approved/ → posted/
              ↑          │
              └──────────┘
               more feedback
```

1. Agent writes draft to `drafts/`
2. Human reviews via `content review <file>`
3. Agent revises based on feedback, moves to `revised/`
4. Human approves → `approved/`
5. Human posts via `content post`

## Detailed Instructions

Each topic has its own reference file:

| Topic | File |
|-------|------|
| Agent permissions (can/cannot do) | [`instructions/permissions.md`](instructions/permissions.md) |
| File naming, frontmatter, one-post-per-file rule | [`instructions/creating-content.md`](instructions/creating-content.md) |
| Review flow diagram + step-by-step process | [`instructions/review-loop.md`](instructions/review-loop.md) |
| LinkedIn, X, Reddit rules and auth details | [`instructions/platform-guidelines.md`](instructions/platform-guidelines.md) |
| YAML frontmatter examples per platform | [`templates/frontmatter-template.md`](templates/frontmatter-template.md) |
| CLI commands reference | [`reference/commands.md`](reference/commands.md) |
| Security model + platform auth table | [`reference/security-model.md`](reference/security-model.md) |
