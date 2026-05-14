# Codex Review Command

Use the local Codex review command when it is available in the environment. Do not invent flags. If unsure, check help first.

## Typical patterns

- Uncommitted local diff: `codex review --uncommitted`
- Branch/base review: use the form shown by `codex review --help` for base or target branch review.
- If command help is unavailable or the CLI is missing, state that Codex review was unavailable and rely on manual diff review plus tests.

## Safe execution rules

- Run from the repository root.
- Do not use review commands that post comments or write externally unless Ahmed approved that action.
- Do not pipe secrets, env dumps, token files, credentials, or private config into review.
- Keep review focused on the edited diff, not the whole repo, unless the user requested a broad audit.
- If a review command fails, capture the error, try the documented/help-supported variant once, then stop and report the blocker.

## Review is not completion

A clean review is not enough. Completion still requires the actual outcome to be inspected and the relevant tests/checks to pass or be named as blocked.
