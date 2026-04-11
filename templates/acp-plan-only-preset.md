# ACP Plan-Only Preset

Use when Ahmed wants a build plan, review, or scoped approach without implementation.

## Fill in before spawn
- Repo/CWD: `{{repo_or_cwd}}`
- Planning request: `{{planning_request}}`
- Constraints: `{{constraints}}`
- Desired output path: `{{plan_output_path}}`

## Spawn brief
You are working in `{{repo_or_cwd}}`.

Planning request: {{planning_request}}

Constraints:
{{constraints}}

Save the final plan to:
{{plan_output_path}}

Rules:
- Do not implement code.
- Do the planning work, do not delegate back.
- Challenge the framing before locking the plan.
- Read the relevant code, docs, and repo instructions first.
- Produce a practical implementation plan that another ACP coding session can execute.
- Include scope, assumptions, file/module impact, risks, validation strategy, and recommended sequence.
- If there are multiple viable approaches, compare the best 2-3 briefly and recommend one.
- Save the plan to the requested path when writable.

Final report must include:
- plan path
- short summary of the recommendation
- key decisions and assumptions
- recommended next step
