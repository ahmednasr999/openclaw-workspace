Objective: <specific implementation outcome>

Context:
- Spec/plan: <path or summary>
- Relevant files: <paths>

Success criteria:
- <observable outcome>
- <quality bar>

Permission profile:
- read-only | local-write | external-write | runtime-change | disruptive/destructive
- Continue automatically through safe in-scope steps. Stop at a new approval boundary.

Scope:
- Change only files needed for the spec.
- Do not take external/public/destructive action.
- Stop before gateway/config/runtime changes unless explicitly approved.

Verification:
- Run <test/lint/build/manual check>.
- Inspect the actual outcome, not just exit code.

Stop conditions:
- Missing input changes scope.
- Required approval is missing.
- Tests reveal broader breakage.

Final output:
- Files changed
- Tests/checks run
- Key decisions
- Remaining risk
