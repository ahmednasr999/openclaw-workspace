# Runtime Patch Verification

Runtime patches are source-sensitive. Verify them directly before claiming they are active.

## Known checker

- `/root/.openclaw/workspace/scripts/check-openclaw-runtime-patches.py`

## Verification flow

1. Run the checker when patch state matters.
2. If it times out once, rerun or inspect narrowly before escalating.
3. Treat transient checker timeout as warning only if an immediate follow-up confirms all patches OK.
4. Do not report patch success from memory.

## Closeout evidence

- Checker result.
- Gateway health result if patch affects live behavior.
- Any timeout or uncertainty clearly stated.
