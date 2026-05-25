# Update Preflight

Use before OpenClaw self-update.

1. Confirm Ahmed explicitly asked for an update.
2. Confirm `/tmp` has at least 2GB free.
3. Back up config/state as appropriate.
4. Check current version and active binary/service path.
5. Review release notes or docs for version-sensitive config changes.
6. Run controlled update via first-class gateway update tool.
7. Run `scripts/openclaw-update-guard.py --write-report`; it must check the sandbox image and Telegram visible-reply config.
8. Verify gateway returns and session/model state is correct.
9. For Telegram closeout, send `/new`, then `ping`, and verify a visible `pong` in the DM.

Do not run updates proactively.
