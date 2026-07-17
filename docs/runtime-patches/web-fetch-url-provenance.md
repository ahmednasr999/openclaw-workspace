# Web Fetch URL Provenance Guard

Status: enabled for the built-in OpenClaw `web_fetch` tool.

## Threat model

This guard contains the Memory Heist attack class: untrusted page content instructs an agent to encode private memory into attacker-visible URL paths or query strings, then asks the agent to fetch those generated URLs.

Prompt instructions alone are not the boundary. The network tool must reject destinations that did not originate from a trusted user URL or an exact structured `web_search` result in the same agent run.

## Policy

`web_fetch` accepts only:

- an exact HTTP(S) URL present in the current user prompt; or
- an exact URL field returned by an earlier `web_search` call in the same run.

URL fragments are ignored for matching because they are not sent to the server. Changes to the origin, path, or query produce a different URL and are rejected. URLs found only inside search snippets or fetched page text are not authorized.

Common sentence-ending punctuation and closing ASCII or typographic quote delimiters are treated as prose rather than URL content. Apostrophes inside a URL path remain valid. A URL that intentionally ends in punctuation or an apostrophe must percent-encode that final character, such as `%2E` for a literal period or `%27` for an apostrophe.

Ambiguous URL tokens ending in Markdown-sensitive markers (`*`, `_`, or `~`) authorize nothing. The guard does not attempt to implement CommonMark inside the network boundary. Supply the URL without emphasis formatting or percent-encode a literal terminal marker, such as `%2A`, `%5F`, or `%7E`.

The network boundary fails closed: if the provenance guard is absent or unwired, `web_fetch` rejects the request instead of proceeding.

Existing SSRF, redirect, and response-sanitization controls remain active.

## Regression coverage

`scripts/check-memory-heist-security-suite.py` is the mandatory plugin-level
update/restart gate. It runs the production guard tests and the held-out GPT-Red
pilot suite and fails unless the result is exactly `19/19`.

`scripts/check-openclaw-runtime-patches.py` verifies:

- exact current-user URLs are allowed;
- exact structured search-result URLs are allowed;
- model-generated path and query mutations are blocked;
- character-by-character exfiltration paths are blocked;
- encoded memory values are blocked;
- deceptive URLs embedded in search snippets are not authorized; and
- missing guard wiring fails closed before network access;
- a Claude-style user agent cannot bypass the decision.

## Update survival

`scripts/reapply-openclaw-2026-5-18-runtime-patches.py` reapplies the guard to the current hashed OpenClaw bundles. The gateway service runs the reapply script and checker before startup.

After an OpenClaw update, run:

```bash
python3 scripts/check-memory-heist-security-suite.py
python3 scripts/reapply-openclaw-2026-5-18-runtime-patches.py
python3 scripts/check-openclaw-runtime-patches.py
```

## Scope and residual risk

This patch governs the built-in `web_fetch` path. Browser automation, shell tools, custom MCP tools, and third-party network tools have separate authorization surfaces and require their own egress controls.
