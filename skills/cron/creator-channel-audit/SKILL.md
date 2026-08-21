---
name: creator-channel-audit-batch
description: Advance the active seven-creator YouTube audit in one bounded, evidence-backed daily batch. Use only for the scheduled continuation of output/creator-channel-audit-20260819; never start a different channel audit from this skill.
metadata:
  owner: NASR
  status: active
---

# Creator Channel Audit Batch

Advance exactly one creator-balanced batch without weakening the acceptance contract.

## Source of truth

Read before acting:

1. `/root/.openclaw/workspace/output/creator-channel-audit-20260819/TASK-BRIEF.md`
2. `/root/.openclaw/workspace/output/creator-channel-audit-20260819/STATUS.md`
3. `/root/.openclaw/workspace/output/creator-channel-audit-20260819/review-dispositions.ndjson`
4. `/root/.openclaw/workspace/TOOLS.md` YouTube capture rule

Run `node scripts/reconcile-creator-channel-audit.cjs` before selecting work. Stop if it fails.

## Batch boundary

- Select the highest-score unresolved `P1 transcript` item for each of the seven creators: at most seven new IDs per run.
- Exclude every ID already present in `review-dispositions.ndjson`.
- Do not use subagents or parallel agent delegation.
- Process captures one at a time so the authenticated browser's focused tab and caption hook remain deterministic.
- Stop after seven new final dispositions, after 1,800 seconds, or at an approval boundary—whichever comes first.

## Evidence workflow

For each selected item:

1. Capture captions with:
   `node scripts/capture-youtube-browser-transcript.cjs --url <url> --out output/creator-channel-audit-20260819/transcripts/<creator-slug>/<video-id>.txt`
2. Retry a failed capture once only after checking the authenticated browser is running and the video ID is correct.
3. Read the complete transcript. Do not infer lessons from the title.
4. Write `video-analyses/<creator-slug>/<video-id>.md` with source, evidence level, executive verdict, timestamped benefits, risks/limits, and one final disposition.
5. Append one NDJSON row to `review-dispositions.ndjson`. Allowed dispositions: `actionable`, `actionable-limited`, `duplicate`, `outdated`, `promotional`, or `irrelevant`.
6. Link a duplicate to its canonical theme and confirm whether it adds anything distinct.

If captions do not exist or approved capture paths fail twice, record the ID in `STATUS.md` under an evidence-blocked subsection. Do not give it a final disposition and do not replace missing evidence with title inference.

## Judgment rules

- Promote durable operating principles, not creator hype or transient interface steps.
- Treat revenue, quality, speed, labor-replacement, and vendor-performance claims as unverified unless independently evidenced.
- Keep Ahmed's external-write, public-posting, messaging, credential, paid-service, destructive, and runtime gates unchanged.
- Do not install tools, buy services, change accounts, post, message, email, or modify production workflows.
- A creator's successful demo is not proof of security, legality, reliability, or business value.

## Closeout

1. Run `node scripts/reconcile-creator-channel-audit.cjs` and require `ok: true`.
2. Update `STATUS.md` with the exact reviewed and remaining counts, batch IDs, new canonical lessons, blocked evidence, and next eligible action.
3. Run `git diff --check` only on task-owned text files.
4. Return one compact internal result: reviewed count, remaining count, reconciliation state, and evidence path.

The audit is complete only when reconciliation reports 10,868 reviewed and zero remaining, and `FINAL-BENEFIT-MAP.md` satisfies the task brief. Otherwise report the run as an interim batch, never as completion.
