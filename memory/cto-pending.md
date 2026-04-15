# CTO Pending Issues — Updated 2026-04-05 12:07 Cairo

## Open

1. **Workspace root has untracked files** — Detected 2026-04-14 during heartbeat. Current root-level untracked items include `.agents/`, `.notifications/`, `Ahmed Nasr - TimesFM Editorial Systems Carousel.pptx`, `Ahmed Nasr - TimesFM Premium Carousel v2.pptx`, `Ahmed Nasr - TimesFM Premium Carousel.pptx`, `artifacts/`, `backups/`, `plans/`, and `skills-lock.json`. HEARTBEAT threshold says to escalate immediately because root-level untracked files can indicate a leak or misplaced outputs. Triage on 2026-04-14 22:45 Cairo: `.notifications/` mtime `2026-03-19 02:41`, `plans/` `2026-04-11 20:46`, the rest are mostly recent on `2026-04-13` (`.agents/` `00:06`, `skills-lock.json` `00:06`, PPTX files `00:15` to `01:01`, `artifacts/` `21:01`, `backups/` `23:15`).
2. **exec-approvals.json CTO allowlist wiped on gateway restart** — CTO entries restored 2026-04-03. sqlite3 already present in allowlist. Persistent fix still requires SSH edit of openclaw.json (execApprovals.enabled + targets). Awaiting Ahmed's SSH access.
3. **content-orchestrator.py archived** — `scripts/.archived/content-orchestrator.py.archived` exists; `test-content-agent.py` broken. Needs review to determine if archived version is still needed or should be restored/deprecated.
4. **CV test failures** — Flagged April 1 morning. Still showing in NASR Doctor as of 2026-04-14, with `cv_validator.py` reported missing.
5. **LinkedIn/content test failures** — NASR Doctor still reports LinkedIn tests failing and content tests failing with FileNotFoundError as of 2026-04-14.

## Resolved This Session

- **SQLite VACUUM executed 2026-04-05 12:07 Cairo** — DB reduced from 535MB to 4.2MB. SIE had deferred twice. Notified CEO.
- **sqlite3 exec allowlist** — Confirmed present in exec-approvals.json. SIE recommendation #4: closed.
