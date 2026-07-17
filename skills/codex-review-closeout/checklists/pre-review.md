# Pre-Review Checklist

- Identify repo root.
- Inspect `git status --short`.
- Inspect changed files and the actual diff.
- If an implementation plan exists, confirm its planned-at revision, drift check, and source anchors were validated before editing.
- Trace every changed file to an authorized plan step; flag out-of-scope changes even when they look useful.
- Confirm no unrelated dirty changes will be reviewed as if they are part of this task.
- Run the smallest meaningful test/check for the edited area first when practical.
- Confirm review command will stay local and not publish externally.
