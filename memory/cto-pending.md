# CTO Pending Issues — Updated 2026-04-05 12:07 Cairo

## Open

1. **exec-approvals.json CTO allowlist wiped on gateway restart** — CTO entries restored 2026-04-03. sqlite3 already present in allowlist. Persistent fix still requires SSH edit of openclaw.json (execApprovals.enabled + targets). Awaiting Ahmed's SSH access.
2. **content-orchestrator.py archived** — `scripts/.archived/content-orchestrator.py.archived` exists; `test-content-agent.py` broken. Needs review to determine if archived version is still needed or should be restored/deprecated.
3. **CV test failures** — Flagged April 1 morning. Never investigated. Details in earlier CTO session history.

## Resolved This Session

- **SQLite VACUUM executed 2026-04-05 12:07 Cairo** — DB reduced from 535MB to 4.2MB. SIE had deferred twice. Notified CEO.
- **sqlite3 exec allowlist** — Confirmed present in exec-approvals.json. SIE recommendation #4: closed.
