# Autoreview Command

Use the installed structured helper from the repository root:

```bash
AUTOREVIEW="/root/.openclaw/workspace/skills/autoreview/scripts/autoreview"
```

## Target selection

- Dirty local diff: `"$AUTOREVIEW" --mode local`
- Branch against its base: `"$AUTOREVIEW" --mode branch --base origin/main`
- One committed change: `"$AUTOREVIEW" --mode commit --commit HEAD`

Select the smallest truthful target. Do not force local mode after committing and do not include unrelated dirty workspace files.

## NASR model rule

Codex defaults to `gpt-5.6-sol` with high reasoning. This installation disables automatic Codex fallback. If Sol is inaccessible, capacity-limited, or otherwise unavailable, stop and report the exact failure. Never substitute Terra or another model unless Ahmed explicitly authorizes that model change.

Claude fallback chains remain opt-in and apply only when Claude was explicitly selected.

## Safe execution

- Run focused tests before or alongside review.
- Keep the helper local. Do not post comments, push, merge, release, or deploy without the normal approval path.
- Let advancing heartbeat lines continue; a structured review can take up to 30 minutes.
- Treat findings as advisory. Verify each finding against the real code and classify it as accepted, rejected, or deferred.
- If an accepted fix changes code, rerun focused checks and autoreview.
- Stop once the final helper run exits clean with no accepted/actionable findings.

## Smoke checks

```bash
python3 "$AUTOREVIEW" --self-test
/root/.openclaw/workspace/skills/autoreview/scripts/test-review-harness --fixture benign --engine codex
```

The deterministic self-test validates helper behavior. The benign harness exercises a real isolated Codex review.
