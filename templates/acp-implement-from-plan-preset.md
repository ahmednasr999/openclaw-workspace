# ACP Implement-From-Plan Preset

Use when a saved plan already exists and the next step is execution.

## Fill in before spawn
- Repo/CWD: `{{repo_or_cwd}}`
- Plan path: `{{plan_path}}`
- Task scope: `{{task_scope}}`
- Required checks: `{{checks}}`

## Spawn brief
You are working in `{{repo_or_cwd}}`.

Use this saved plan as the baseline:
{{plan_path}}

Task scope:
{{task_scope}}

Required checks:
{{checks}}

Rules:
- Do the work, do not delegate back.
- Read the saved plan and the relevant current code before editing.
- Follow the saved plan unless the code has drifted or a clear bug in the plan appears.
- If you deviate materially from the plan, explain why in the final report.
- Implement cleanly, validate, then self-review before reporting done.
- Never claim success with errors present.

Final report must include:
- files changed
- checks run
- deviations from the plan, if any
- key decisions made
- anything still uncertain or risky
