# Repository Cleanup Loop

Use when branches, worktrees, old clones, generated research repos, PRs, or local changes make repository state unclear.

## Inputs

- Target repo or directory tree.
- Cleanup authority: inspect-only, archive, delete, close PR, or move work.
- What must be preserved: active work, ledgers, reports, backups, media, databases, credentials, snapshots.

## Loop

1. Inventory before cleanup:
   - `git status --short --branch`
   - branches and upstreams
   - worktrees
   - untracked/ignored large files
   - recent commits and stashes
   - linked PRs if applicable
2. Classify each item:
   - active or recently used
   - valuable but misplaced
   - generated/rebuildable
   - stale but uncertain
   - proven safe to remove
3. Recover valuable work first: branch it, patch it, archive it, or document it.
4. Remove only proven stale or rebuildable state within the approved boundary.
5. Re-run the inventory and compare before/after.
6. Stop if uncertainty remains around ownership or value.

## Stop States

- `success`: valuable work is preserved and remaining state is intentional.
- `clean-noop`: inventory is already clean.
- `blocked`: ownership, branch purpose, or data value cannot be determined.
- `approval-required`: deletion, PR closure, remote branch changes, or discarding uncommitted work is needed.

## Evidence

Close with before/after inventory, items preserved, items removed or archived, exact paths, and verification commands. Never discard uncommitted changes or someone else's work without explicit confirmation.
