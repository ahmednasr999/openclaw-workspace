# ACP Spawn Brief Template

Use this as the compact runtime template before spawning any ACP coding session.

## Fill in
- Mode: `{{simple|medium|full|plan-only|implement-from-plan}}`
- Repo/CWD: `{{repo_or_cwd}}`
- Objective: `{{objective}}`
- Success criteria: `{{success_criteria}}`
- Constraints: `{{constraints}}`
- Likely files: `{{files_or_modules}}`
- Checks: `{{checks}}`
- Main risk: `{{risk}}`
- Saved plan: `{{plan_path_or_none}}`

## Spawn brief
You are working in `{{repo_or_cwd}}`.

Mode: {{mode}}
Objective: {{objective}}

Success criteria:
{{success_criteria}}

Constraints:
{{constraints}}

Likely files/modules:
{{files_or_modules}}

Checks to run:
{{checks}}

Main risk to watch:
{{risk}}

Saved plan, if any:
{{plan_path_or_none}}

Rules:
- Do the work, do not delegate back.
- Read the relevant files before editing.
- Keep the solution as small as possible while fully solving the task.
- If the task is plan-only, do not implement.
- If a saved plan exists, use it unless the code has clearly drifted.
- Never claim success with errors present.

Final report must include:
- files changed
- checks run
- key decisions made
- anything still uncertain or risky
