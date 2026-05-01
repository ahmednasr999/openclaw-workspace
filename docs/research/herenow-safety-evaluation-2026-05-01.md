# here.now safety evaluation - 2026-05-01

## Source

X post inspected:
`https://x.com/adamludwin/status/2049978718190506320`

Claim: agents can get 10 GB cloud storage/free publishing by installing `http://here.now/skill.md`.

## Local state

A local `here-now` skill already exists at:

`/root/.agents/skills/here-now/SKILL.md`

Skill version: `1.6.3`.

No `~/.config/herenow/credentials.json` was found during inspection. The local skill actually documents credential storage as:

`~/.herenow/credentials`

## Capabilities observed

The local skill is primarily a static hosting/publishing skill:

- publish files/folders to `{slug}.here.now`
- anonymous publishing without API key, expires in 24h
- authenticated publishing with API key, permanent or custom TTL
- max anonymous file size: 250 MB
- max authenticated file size: 5 GB
- anonymous rate limit: 5/hour/IP
- authenticated rate limit: 60/hour/account

The fetched remote skill text also mentions Drives/private cloud storage, but the locally installed skill focuses on publishing. Use local installed docs/scripts as the trusted operational path.

## Safe test performed

A non-sensitive throwaway HTML page was published from `/tmp/herenow-safe-test` using the local script:

```bash
/root/.agents/skills/here-now/scripts/publish.sh .
```

Result:

- Site URL: `https://blissful-sketch-tqcr.here.now/`
- Auth mode: `anonymous`
- Persistence: `expires_24h`
- Expires at: `2026-05-02T02:14:51.781Z`
- Claim URL was returned once by the script and stored in local `.herenow/state.json`; do not expose claim tokens casually.

Fetch verification succeeded. The published page returned HTTP 200 and contained only the throwaway safety-test text.

## Security judgment

Safe for:

- temporary public previews
- non-sensitive static artifacts
- shareable visual previews
- disposable demos

Not approved for:

- private OpenClaw memory
- CV/job-search artifacts
- credentials or configs
- private user data
- automatic cross-agent memory sync
- permanent storage without explicit API-key/account approval

## Operating rule

Use here.now only as a public publishing path unless Ahmed explicitly approves authenticated storage and the data class.

Before publishing any real artifact:

1. Confirm it is safe to be public.
2. Prefer anonymous 24h publishing for previews.
3. Share only the `siteUrl` from the current script run.
4. Do not share claim tokens unless explicitly needed.
5. Never publish secrets, credentials, raw memory, CVs, or private job-search material.

## Recommendation

Keep here.now as a lightweight preview/deployment option. Do not use it as NASR/OpenClaw memory storage yet.
