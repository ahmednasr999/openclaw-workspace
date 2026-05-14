# Restart Preflight

Use before gateway restart or lifecycle action.

1. Confirm restart is necessary.
2. Confirm approval if not explicitly requested.
3. Capture current status/version if relevant.
4. Identify what must be verified after boot.
5. Use first-class `gateway restart` when possible.
6. Include a clear continuation message.
7. After restart, verify gateway health and the original issue.

Do not use stop/start as a restart substitute.
