# Crabbox Local Proof Wrapper

`/root/.openclaw/workspace/scripts/crabbox-local-proof.sh` runs a Git worktree command in a disposable Crabbox `local-container` lease and saves proof artifacts under `reports/crabbox-local-proof/`.

Use it for CTO verification, heavy checks, browser/test proof bundles, and Git repo experiments that should not pollute the VPS worktree.

```bash
scripts/crabbox-local-proof.sh --repo /path/to/repo --label tests -- pnpm test
```

Safety rules:

- Default provider is `local-container`, no cloud credentials or SSH host config.
- The target `--repo` must be a Git worktree because Crabbox sync is repository-oriented.
- The wrapper pins Crabbox `v0.36.0` and verifies the official checksum before caching the binary under `/root/.cache/openclaw/crabbox/0.36.0/`.
- It refuses to sync `/root/.openclaw/workspace` unless `--allow-workspace-sync` is passed.
- Do not run it on hostile repositories or secret-heavy worktrees. Crabbox is a developer execution tool, not a hostile-code sandbox or secrets scrubber.
- Review `summary.md`, `crabbox.log`, `stdout.txt`, `stderr.txt`, and `proof.md` before sharing artifacts externally.

Useful examples:

```bash
# Small smoke proof, after `git init /tmp/demo` or inside any existing checkout
scripts/crabbox-local-proof.sh --repo /tmp/demo --label smoke -- echo CRABBOX_REMOTE_OK

# Node checks in a repo
scripts/crabbox-local-proof.sh --repo /srv/repo --label node-checks -- bash -lc 'npm ci && npm test'

# Keep the base image after the run to avoid repeated pulls
scripts/crabbox-local-proof.sh --repo /srv/repo --label quick --keep-image -- make test
```
