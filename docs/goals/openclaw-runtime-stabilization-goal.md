# Goal Contract: OpenClaw runtime stabilization

## Goal

- Name: OpenClaw runtime stabilization
- Owner: CTO lane, with NASR/main as escalation and user-facing synthesis owner
- Status: active
- Why it matters: protect Ahmed's primary assistant channel from runtime leaks, broken updates, slow memory recall, and unsafe gateway changes while preserving GPT-5.5/OpenClaw continuity.
- Started: 2026-05-01
- Review cadence: after every OpenClaw update, runtime leak, gateway restart/reload, or material active-memory behavior change

## Success criteria

Done means the runtime is in a known-good baseline:
- `scripts/check-openclaw-runtime-patches.py` passes all tracked checks
- `openclaw --version` is captured
- `openclaw status` confirms the gateway is reachable and Telegram is OK
- active-memory live replies remain on the direct FTS path when enabled, with `directFts=1` evidence when logs are available
- no fresh user-facing leak class is observed after the latest reload/update window
- any runtime patch change has a smoke test in the checker

Not done if:
- a new leak class is only hidden by a final-output regex without checking storage/replay/injection paths
- an OpenClaw update ran without the runtime patch checker afterward
- gateway was restarted/reloaded but live status was not verified
- stale logs are treated as fresh failure evidence
- a sub-agent or command reports success without inspected output

## Operating boundaries

Allowed without extra approval:
- read-only inspections of current version, status, logs, service entrypoint, and checker output
- workspace documentation updates
- non-destructive baseline capture
- checker improvements that only add smoke tests and do not touch live runtime files

Requires explicit approval:
- OpenClaw update or dependency update
- gateway config changes
- gateway restart, stop, or start unless an urgent leak requires controlled reload and Ahmed has approved the path
- deleting or purging queued/session artifacts
- disabling active-memory beyond a temporary containment recommendation
- editing live dist/runtime files outside an approved repair window

## Current state

Last verified: 2026-04-30 dry-run baseline

Evidence recorded:
- `docs/runtime-patches/cto-runtime-patch-workflow.md`
- `docs/research/cto-runtime-baseline-2026-04-30.md`
- `docs/runtime-patches/active-memory-direct-fts.md`
- `scripts/check-openclaw-runtime-patches.py`

Known good baseline from latest dry-run:
- OpenClaw 2026.4.27
- runtime patch checker green
- gateway reachable/running
- Telegram ON/OK
- active-memory log samples showed fast `directFts=1` path

Open risks:
- future OpenClaw updates can overwrite local dist patches
- sanitizer regexes are brittle if contamination keeps entering model-visible context
- task issues/audit warnings shown by status were out of scope for the runtime-patch dry-run
- this goal contract itself has not yet been exercised during a real post-update event

Next safe action:
- On the next OpenClaw update or leak report, run `docs/runtime-patches/cto-runtime-patch-workflow.md` against this goal contract before changing runtime files.

## Pause/resume rule

Pause when:
- current checker is green
- gateway and Telegram are healthy
- there is no fresh leak or update event
- only routine monitoring remains

Resume when:
- Ahmed approves an OpenClaw update
- a user-facing leak appears
- active-memory live replies slow down or contaminate context
- gateway reload/restart happens
- `openclaw status` shows runtime/gateway degradation relevant to this goal

## Stop/escalation rule

Escalate to Ahmed when:
- a fix requires restart/stop/start of the live gateway
- a fix requires editing live runtime dist files
- active-memory may need to be disabled beyond a short containment window
- queue/session artifact purge is proposed
- the same leak source needs multiple regex patches, indicating structural containment is required

Retire this goal when:
- OpenClaw upstream includes durable equivalents for all local runtime patches
- the checker remains green after an update without manual dist patch restoration
- active-memory and queue/replay leak classes have upstream fixes or stable first-class config controls

## Verification contract

Before reporting progress or completion:
- inspect actual checker output, not just command success
- inspect current OpenClaw version and status
- separate stale pre-fix logs from fresh evidence
- record what changed, what was verified, and remaining risk
- never call the runtime "fixed" unless the relevant leak class has a checker smoke test

## Handoff note

If another agent/session takes over, include:
- this file
- `docs/runtime-patches/cto-runtime-patch-workflow.md`
- `docs/runtime-patches/active-memory-direct-fts.md`
- latest `docs/research/cto-runtime-baseline-*.md`
- the exact OpenClaw version and service entrypoint
- whether the work is inspection-only, approved repair, or escalation-needed
