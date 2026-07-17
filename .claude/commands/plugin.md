---
description: Route plugin management requests without treating /plugin as an unknown skill
argument-hint: [list|install|status|help]
---

# /plugin

Do not treat this as a generic in-session skill. First clarify whether Ahmed means Claude plugins, OpenClaw plugins, or Codex skills.

For read-only discovery, inspect local help first:

```bash
claude plugin --help
openclaw plugin --help
openclaw plugins --help
```

For installs, removals, marketplace changes, or runtime configuration, stop for explicit approval unless Ahmed has already requested that exact change. After changing plugin state, run `/ai-smoke-test --auth-only` if the change affects Claude-backed sessions.
