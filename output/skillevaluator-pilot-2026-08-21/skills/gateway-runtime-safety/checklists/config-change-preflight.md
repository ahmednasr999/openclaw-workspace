# Config Change Preflight

Use before any gateway config write.

1. Confirm Ahmed explicitly asked for the change or maintenance window.
2. Identify the exact config path.
3. Inspect schema with `gateway config.schema.lookup`.
4. Read current relevant config with `gateway config.get`.
5. Decide patch vs full apply, prefer patch.
6. Confirm whether restart is required.
7. Prepare rollback or backup path if risk is non-trivial.
8. Apply one change only.
9. Verify actual behavior.

Stop if the schema path is unknown or the requested change would weaken safety policy without explicit approval.
