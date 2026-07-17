---
description: Run Claude CLI auth and model smoke tests before using Claude-backed sessions
argument-hint: [--auth-only|--all-models|--model MODEL --expect TEXT]
---

# /ai-smoke-test

Run the local smoke-test script from the project root:

```bash
bash scripts/claude-cli-smoke-test.sh $ARGUMENTS
```

If the script reports `not logged in`, `invalid API key`, `authentication_failed`, or `401`, stop. Tell Ahmed the Claude CLI auth state and ask for `claude auth login` to be run outside the agent session. Do not send more Claude prompts until this command passes.

Default behavior checks auth and the Sonnet exact-output route. Use `--all-models` when model routing changed or when Opus availability matters.
