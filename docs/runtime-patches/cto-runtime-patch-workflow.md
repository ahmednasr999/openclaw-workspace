# CTO Runtime Patch Workflow

Purpose: keep OpenClaw runtime hot patches safe, source-driven, and verifiable after updates or leak regressions.

Use this when:
- OpenClaw was updated and local runtime patches may have been overwritten.
- Telegram/user-facing output leaked runtime, queue, tool, heartbeat, cron, reply-context, or active-memory internals.
- Active-memory live replies become slow or start contaminating context.
- A gateway reload/restart is being considered to load patched runtime files.

Do not use this for routine feature work or cosmetic cleanup.

## Lifecycle

### 1. DEFINE

State the exact defect class before editing.

Examples:
- runtime-context preface leaked to user-facing output
- queued/restart-sentinel prompt replay leaked as user text
- reply-context metadata leaked before the real user message
- active-memory semantic path slowed or contaminated live Telegram replies
- session-resume fallback prefix appeared in direct chat

Required scope statement:
- live OpenClaw version
- active gateway/service entrypoint
- affected channel/session, if known
- expected user-visible safe output
- whether this is final-output sanitization, storage/replay sanitization, active-memory path control, or service reload only

### 2. PLAN

Prefer structural containment over one more regex when contamination enters model-visible context.

Order of preference:
1. Prevent internal artifacts from being stored or replayed as user content.
2. Sanitize queue/replay/reply-context before model injection.
3. Keep active-memory live recall on the direct FTS path only.
4. Use final-output sanitizer as last defense, not the only defense.
5. Purge contaminated queued/restart artifacts when safe.

Before editing:
- inspect current dist filenames, because hashed bundles change after updates
- inspect current checker coverage in `scripts/check-openclaw-runtime-patches.py`
- inspect the relevant current bundle/source section, not an old backup only
- identify the smallest patch that addresses the defect class

### 3. BUILD

Patch one defect class at a time.

Rules:
- back up every live file before editing
- do not bulk-edit unrelated dist files
- do not change config or restart unless the patch explicitly requires loading new runtime code
- update the checker with a smoke test for the exact leak class fixed
- preserve existing local patches unless intentionally replacing them

Known local patch families:
- session-resume fallback prefix suppression
- active-memory direct SQLite FTS live-reply path
- runtime-context custom-message queue disabled
- runtime-context plain-header stripping
- user-facing sanitizer for tool/heartbeat/cron/restart/reply-context leak variants
- queued-message sanitizer/rendering to avoid raw internal prompt fallback
- built-in `web_fetch` exact-URL provenance enforcement for Memory Heist containment

### 4. VERIFY

Minimum verification before saying fixed:

```bash
python3 scripts/check-openclaw-runtime-patches.py
openclaw --version
openclaw status
```

The checker must include a smoke test for the new defect class, not just pass older checks.

For active-memory live path, look for log evidence like:

```text
active-memory ... status=ok ... directFts=1
```

For sanitizer work, prove the sample input reduces to the expected safe output:
- internal-only prompt -> empty string
- metadata + real user text -> only the real user text
- system/background/tool completion lines -> stripped

Exit code 0 alone is not proof. Inspect the actual checker lines and output sample.

### 5. REVIEW

Before reload/restart, ask:
- Is this patch source-driven against the current version/bundle?
- Does the checker cover the new failure mode?
- Is the patch narrow enough to avoid breaking unrelated rendering?
- Is a reload necessary, or is file verification enough?
- Could active-memory injection be temporarily disabled instead of adding brittle regexes?

If two regex patches target the same contamination source, stop and consider structural containment.

### 6. SHIP

Closeout must include:
- exact files changed
- backup paths created
- checker result
- version/status result
- reload/restart action, if any
- remaining risk and next trigger for deeper action

Do not say "fixed" if:
- the checker does not cover the new variant
- stale logs are being confused with fresh evidence
- the live gateway has not loaded changed runtime code when loading is required
- a real user-visible replay has not been explained or contained

## Anti-rationalization table

| Risky thought | Counter-rule |
|---|---|
| "The checker is green, so this new leak is fixed" | Add a smoke test for the new leak class first. |
| "A final sanitizer regex is enough" | If contamination enters model-visible context, patch storage/replay/injection too. |
| "The update succeeded, so patches survived" | Updates can overwrite dist patches. Run the checker after every update. |
| "Old log noise means the patch failed" | Separate stale pre-fix logs from fresh post-reload evidence. |
| "Restart now to be safe" | Reload/restart only when needed and after verification/backups. |
| "Active-memory semantic recall is better" | Keep live Telegram on direct FTS until isolated p95/relevance tests pass. |

## Related files

- `scripts/check-openclaw-runtime-patches.py`
- `docs/runtime-patches/active-memory-direct-fts.md`
- `TOOLS.md` gateway/runtime patch notes
- `AGENTS.md` verified closeout and sub-agent rules
- `docs/agent-governance/NASR-Coding-Rules-v1.md`
- `docs/agent-governance/NASR-ACP-Coding-Brief.md`

## When to escalate

Escalate to Ahmed before:
- disabling active-memory for live replies for more than a temporary containment window
- restarting/stopping the live gateway during an active conversation unless urgent
- changing gateway config
- applying an OpenClaw update
- deleting/purging queued/session artifacts when user-visible content might be lost
