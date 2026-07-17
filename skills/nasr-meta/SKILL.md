---
name: nasr-meta
description: Build consistent sub-agent briefs for CV, job scoring, content, and research tasks. Use only when a sub-agent is actually being spawned.
metadata:
  owner: NASR
  status: active
---

# NASR Meta Brief Router

## Route

| Task | Behavioral source |
|---|---|
| CV or ATS tailoring | `agents/cv-builder.md` |
| Job scoring or ranking | `agents/job-scorer.md` |
| LinkedIn content | `agents/content-writer.md` |
| Company, salary, or market research | `agents/researcher.md` |

Skip this skill for unrelated or one-step work.

## Brief Contract

Every brief contains:

1. Outcome and exact scope
2. Required behavioral source
3. Input and source-of-truth files
4. Constraints and approval boundary
5. Output path and format
6. Success criteria and verification
7. Timeout and stop conditions
8. No fabrication and no unrelated changes

Use `openai/gpt-5.6-sol` for every sub-agent. Use high reasoning for CVs, final job scoring, content drafting, and executive synthesis. Use medium reasoning for bounded research collection. Do not test or route to cheaper models.

Use isolated context unless the child truly needs the current transcript. The owning session reviews evidence and artifacts before delivery. Missing proof is incomplete work, not success.

Do not paste broad global prompts into every brief. Link the smallest relevant behavioral file and restate only task-specific constraints.
