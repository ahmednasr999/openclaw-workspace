# ACP Medium Coding Preset

Use for multi-file coding work where the implementation path is mostly obvious.

## Fill in before spawn
- Repo/CWD: `{{repo_or_cwd}}`
- Task: `{{task}}`
- Likely files: `{{files}}`
- Validation: `{{test_or_check}}`
- Main risk: `{{risk}}`

## Spawn brief
You are working in `{{repo_or_cwd}}`.

Task: {{task}}

Likely files:
{{files}}

Validation to run:
{{test_or_check}}

Main risk to watch:
{{risk}}

Rules:
- Do the work, do not delegate back.
- Read the relevant files before editing.
- Keep a short 5-line plan in mind: what, why, files, test case, risk.
- If the scope turns out not to be obvious, stop and report the fork instead of improvising a large redesign.
- Make the smallest clean change that fully solves the task.
- Run the validation above, or the closest equivalent available in the repo.
- Never claim success with errors present.

Report back with:
- files changed
- checks run
- key decision made
- anything still uncertain or risky
