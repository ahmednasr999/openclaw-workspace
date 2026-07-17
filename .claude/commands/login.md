---
description: Show login guidance for Claude CLI auth failures
argument-hint: none
---

# /login

This is not a model skill. Treat login as an operator or CLI action.

1. Run `claude auth status` or `bash scripts/claude-cli-smoke-test.sh --auth-only`.
2. If auth is missing or invalid, tell Ahmed to run `claude auth login` outside the agent session.
3. After login, rerun `/ai-smoke-test --auth-only` before sending Claude prompts.

Do not retry failed Claude prompts while auth is still broken.
