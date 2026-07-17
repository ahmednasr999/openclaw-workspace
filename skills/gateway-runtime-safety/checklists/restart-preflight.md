# Restart Preflight

Use before gateway restart or lifecycle action.

1. Confirm restart is necessary.
2. Confirm approval if not explicitly requested.
3. Capture current status/version if relevant.
4. Run `python3 scripts/check-memory-heist-security-suite.py`; `19/19` is a hard gate.
5. Identify what must be verified after boot.
6. Use first-class `gateway restart` when possible.
7. Include a clear continuation message.
8. After restart, rerun the security gate, verify gateway health, and verify the original issue.

Do not use stop/start as a restart substitute.
