# Post-Change Verification

Use before saying gateway/runtime work is done.

1. Confirm gateway status or health.
2. Confirm the original requested behavior now works.
3. For Telegram update/reply-delivery incidents, validate the real DM path with `/new`, then `ping`, and verify a visible `pong`; session-log assistant text alone is not enough.
4. Confirm model/router state if model-sensitive.
5. Confirm no new warnings/errors were introduced.
6. Confirm any changed config path and whether restart/hot reload occurred.
7. State remaining risk or uncertainty.
8. If verification cannot be run, state exactly why.
9. If Ahmed approved the repair but runtime policy blocks the required host/gateway capability, record the exact missing policy key and treat it as an OpenClaw permission defect, not a user-approval gap.

Tool success alone is not completion.
