# Approval Boundaries

Pre-approved in normal coding scope:
- read-only repo inspection
- local tests, linters, typechecks, builds
- local workspace edits to requested files
- local Codex review that does not publish externally

Ask first:
- commits or pushes
- PR comments, issue comments, reviews submitted to GitHub
- releases, deploys, package publishes
- destructive cleanup outside the requested diff
- credential, config, gateway/runtime, or service lifecycle changes
- broad refactors not needed for the requested outcome

When in doubt, finish local verification and ask for the smallest external/risky approval separately.
