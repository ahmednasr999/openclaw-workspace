# ACP Full Build Preset

Use for non-trivial features, refactors, or objective-level coding work.

## Fill in before spawn
- Repo/CWD: `{{repo_or_cwd}}`
- Objective: `{{objective}}`
- Success criteria: `{{success_criteria}}`
- Constraints: `{{constraints}}`
- Required checks: `{{checks}}`
- Optional saved plan: `{{plan_path_or_none}}`

## Spawn brief
You are working in `{{repo_or_cwd}}`.

Objective: {{objective}}

Success criteria:
{{success_criteria}}

Constraints:
{{constraints}}

Required checks:
{{checks}}

Saved plan to use if present:
{{plan_path_or_none}}

Rules:
- Do the work, do not delegate back.
- Start by reading the relevant code and understanding the current architecture.
- If a saved plan is provided, use it as the baseline unless the code has materially changed.
- Work in this order: plan, implement, self-review, validate, report.
- Prefer the safest design that satisfies the objective without unnecessary sprawl.
- If you hit a real tradeoff, choose the best option and explain why in the final report unless the task is blocked on a product decision.
- Run the required checks, plus any targeted checks needed for touched areas.
- Never claim success with errors present.

Final report must include:
- concise summary of what shipped
- files changed
- tests/checks run and results
- key technical decisions
- anything still uncertain, risky, or deferred
