---
title: "Safe OpenClaw VPS disk cleanup without deleting recovery state"
status: verified
verified_on: 2026-07-12
area: runtime
tags: [disk-pressure, retention, snap, cache, openclaw]
---

# Safe OpenClaw VPS disk cleanup without deleting recovery state

## Summary

OpenClaw disk pressure was reduced safely by separating disposable caches, superseded packages, and routine duplicate backups from active state and unique recovery artifacts. The working approach removed only redownloadable or explicitly superseded data, preserved the latest and named rollback databases, and verified OpenClaw after cleanup.

## Symptoms

- Root filesystem use had reached a level where builds, updates, and runtime writes had little margin.
- Large consumers included disabled Snap revisions, package and compile caches, unused local-model assets, unused global tools, and accumulating routine database backups.
- Active agent state, LCM recovery data, session archives, the latest system snapshot, Git history, and the Hermes pilot were also large but had different recovery value and could not be treated as cache.

## Root cause

Disk growth came from multiple retention classes being handled as one cleanup problem. Redownloadable caches and superseded package revisions accumulated alongside routine database copies, while unique recovery and runtime state lived under the same broad OpenClaw tree. The existing retention process did not cover every current backup filename pattern, so routine pipeline copies continued to accumulate.

## Failed approaches

- Treating the largest directories as deletion candidates was unsafe because size alone did not distinguish active state from disposable data.
- Assuming the latest top-level snapshot contained every archive or database backup was incorrect; archive membership had to be checked before relying on it as recovery evidence.
- A compound diagnostic command returned non-zero when a search produced no match, even though earlier checks succeeded. Independent checks are clearer for destructive-decision gates.

## Verified solution

1. Measure the filesystem and rank consumers without deleting anything.
2. Classify each candidate as active state, unique recovery, named rollback, routine duplicate, superseded package, or redownloadable cache.
3. Verify current configuration and process use before removing optional tools or model caches.
4. Remove only disabled Snap revisions through `snap remove SNAP_NAME --revision REVISION`, clear redownloadable caches, and uninstall optional global packages through their package manager.
5. For routine database backups, preserve the newest valid copy and every explicitly named rollback copy before deleting older routine copies.
6. Stop if a candidate's owner, recovery coverage, or active use is uncertain. Do not delete LCM databases, active agent state, session archives, Git objects, current snapshots, or Hermes state as part of generic cleanup.
7. Recheck free space, configuration validity, gateway reachability, active memory backends, and preserved database integrity.

Rollback consists of reinstalling removed optional packages or allowing caches to regenerate. Database cleanup is not reversible, so the preserved-copy verification is a mandatory stop gate before deletion.

## Evidence

- After cleanup, `/` had 26 GB available and was at 74% use on 2026-07-12.
- No disabled Snap revisions remained, the unused llama.cpp cache was absent, and QMD/OpenCode were not present in the global package list.
- The routine pipeline set was reduced to the latest database plus the named RAKBANK rollback database, and both were preserved as SQLite files.
- OpenClaw configuration validation and gateway reachability checks passed after the cleanup.

## Prevention

- Extend retention logic to match the live routine backup naming scheme while exempting named rollback copies.
- Keep a latest-only policy for routine backups where another verified recovery tier exists.
- Report disk composition by retention class, not only by directory size.
- Run destructive candidates as separate checks so a harmless no-match does not obscure other evidence.

## When to revisit

Reassess this procedure when backup naming, OpenClaw state layout, memory backend, snapshot coverage, package manager, or recovery policy changes. Revalidate every path before using these classifications on another host.
