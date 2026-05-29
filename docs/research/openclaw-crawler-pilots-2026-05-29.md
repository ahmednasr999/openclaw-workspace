# OpenClaw Crawler Pilot Report

Date: 2026-05-29
Owner: CTO lane
Status: gitcrawl pilot passed, telecrawl installed but source-blocked on VPS

## Executive Result

`gitcrawl` is usable now on this VPS. It installed cleanly, authenticated with the existing GitHub CLI token when passed as `GITHUB_TOKEN`, synced one public OpenClaw PR into a throwaway local SQLite archive, and returned the expected thread data.

`telecrawl` is installed and operational as a CLI, but this VPS does not have a Telegram Desktop `tdata` archive. Import is therefore blocked on source availability, not on the tool itself. Do not attempt to scrape Telegram through the bot API as a substitute for this pilot. The intended path is a local Telegram Desktop or macOS Postbox archive, ideally from Ahmed-Mac or a controlled exported/copy source.

## Install Evidence

Installed binaries:

- `/root/go/bin/gitcrawl`, symlinked to `/usr/local/bin/gitcrawl`
- `/root/go/bin/telecrawl`, symlinked to `/usr/local/bin/telecrawl`

Version checks:

- `gitcrawl --version` returned `dev` because it was built via `go install` without release ldflags.
- `telecrawl version` returned `0.1.0`.

The host Go version is `go1.24.4`, but Go automatically downloaded and used toolchain `go1.26.3` because both crawlers require Go `>=1.26.2`.

## gitcrawl Pilot

Pilot mode: isolated throwaway HOME at `/tmp/openclaw-crawler-pilots/gitcrawl-home`.

Commands used in substance:

```bash
HOME=/tmp/openclaw-crawler-pilots/gitcrawl-home gitcrawl init --json
HOME=/tmp/openclaw-crawler-pilots/gitcrawl-home GITHUB_TOKEN=<gh token> gitcrawl doctor --json
HOME=/tmp/openclaw-crawler-pilots/gitcrawl-home GITHUB_TOKEN=<gh token> gitcrawl sync openclaw/openclaw --numbers 1 --json
HOME=/tmp/openclaw-crawler-pilots/gitcrawl-home GITHUB_TOKEN=<gh token> gitcrawl status --json
HOME=/tmp/openclaw-crawler-pilots/gitcrawl-home GITHUB_TOKEN=<gh token> gitcrawl threads openclaw/openclaw --numbers 1 --json
```

Observed result:

- Config path: `/tmp/openclaw-crawler-pilots/gitcrawl-home/.config/gitcrawl/config.toml`
- Database path: `/tmp/openclaw-crawler-pilots/gitcrawl-home/.config/gitcrawl/gitcrawl.db`
- Database size: about `392K`
- Repositories: `1`
- Threads: `1`
- Open threads: `0`
- Synced object: `openclaw/openclaw` PR `#1`
- PR title: `fix: add @lid format support and allowFrom wildcard handling`
- SQLite tables include `repositories`, `threads`, `documents_fts`, `sync_runs`, `pull_request_details`, `comments`, and cluster/vector tables.

Decision: adopt `gitcrawl` for a scoped weekly OpenClaw repo digest pilot. Keep it read-only at first: sync, status, threads, search, and report. Do not use governance commands like close/reopen until a separate policy exists.

## telecrawl Pilot

Pilot mode: isolated DB at `/tmp/openclaw-crawler-pilots/telecrawl-pilot.db`.

Commands used in substance:

```bash
telecrawl --db /tmp/openclaw-crawler-pilots/telecrawl-pilot.db --json status
telecrawl --db /tmp/openclaw-crawler-pilots/telecrawl-pilot.db --json doctor
```

Observed result:

- DB path: `/tmp/openclaw-crawler-pilots/telecrawl-pilot.db`
- Chats: `0`
- Messages: `0`
- Media messages: `0`
- Doctor source path checked: `/root/.local/share/TelegramDesktop/tdata`
- Source exists: `false`
- Error: `stat /root/.local/share/TelegramDesktop/tdata: no such file or directory`

Decision: keep `telecrawl` installed, but move the import pilot to a machine or copied source that actually has Telegram Desktop data. Ahmed-Mac is the likely target if Telegram Desktop is installed there. Use read-only source mounts and avoid backup push until the local archive quality is verified.


## Digest Script Added

Created reusable read-only digest script:

- Script: `scripts/openclaw-gitcrawl-digest.py`
- State home: `/root/.local/share/openclaw-gitcrawl-digest`
- Report output: `reports/openclaw-gitcrawl-digest-2026-05-29.md`
- Verified run: synced `openclaw/openclaw.ai` open PRs and produced a report showing 5 cached open threads across 3 repository records.

Important path note: using `/root/.openclaw/state/gitcrawl-openclaw-digest` caused `gitcrawl` to report a portable source DB error before the SQLite archive existed. The working state path is outside `.openclaw`, under `/root/.local/share/openclaw-gitcrawl-digest`.

## Operational Recommendations

1. Promote `gitcrawl` to CTO tooling for OpenClaw repo monitoring.
2. Keep the first `gitcrawl` job read-only and small: selected OpenClaw repos, open issues/PRs, status, search, and weekly digest.
3. Do not run embeddings/clustering until OpenAI key/model cost and value are explicitly justified.
4. Run `telecrawl` import only against a known Telegram Desktop/Postbox source, preferably on Ahmed-Mac or a read-only copied archive.
5. Treat `telecrawl backup push` as out of scope until archive contents and encryption/recipient handling are reviewed.
6. Add both binaries to the CTO lane, not NASR front-facing context.

## Next Actions

1. Review one more manual run of `scripts/openclaw-gitcrawl-digest.py`, then decide whether to schedule it weekly under CTO.
2. Check Ahmed-Mac for Telegram Desktop archive availability before attempting `telecrawl import`.
3. If Ahmed-Mac has a source, run `telecrawl doctor` first, then a limited import such as latest 20 dialogs and 50 messages per dialog into an isolated DB.
4. After one successful import, inspect counts and sample search results before deciding whether to add a scheduled memory-delta workflow.
