# Memory Heist Egress Guard

This local OpenClaw plugin blocks native `web_fetch` calls and explicit browser
navigation unless the exact HTTP(S) URL was supplied in the host-observed raw
inbound message for the current run or returned in a structured URL field by
`web_search`.

For search results, only direct URL fields on recognized result entries are
trusted. URL-shaped fields nested inside snippets, metadata, debug data, or
other untrusted result content never gain navigation authority. Structured
result parsing is also depth-, size-, field-, and node-bounded.

The policy deliberately does not trust URLs found only in assembled prompts,
reply context, memory, fetched pages, snippets, or arbitrary text. This prevents
those sources from gaining authority to encode private data into attacker-visible
URL paths.

Run identifiers must agree across the hook event and context. Provenance is
revoked on `agent_end`, with TTL cleanup retained as a bounded fallback.

## Verification

```bash
python3 scripts/check-memory-heist-security-suite.py
node --input-type=module -e "const m=await import('./plugins/memory-heist-guard/index.js'); if(m.default?.id!=='memory-heist-guard'||typeof m.default?.register!=='function') process.exit(1)"
python3 -m json.tool plugins/memory-heist-guard/openclaw.plugin.json >/dev/null
```

## Boundaries

- Redirects performed inside an already authorized `web_fetch` remain governed
  by OpenClaw's existing redirect and SSRF controls.
- Browser clicks whose destination is not present in tool parameters are outside
  this hook's visibility.
- Arbitrary subprocess or custom-plugin network sockets are outside this guard.
- A page-discovered URL must be supplied explicitly by the user or rediscovered
  through `web_search` before native navigation is allowed.
