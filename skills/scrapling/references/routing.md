# Scrapling routing

Use this file to decide whether Scrapling is the right tool.

## Tool selection
| Situation | Use | Why |
|---|---|---|
| One public page, readable content needed fast | `web_fetch` | Lowest cost and least moving parts |
| Static site crawl, list/detail extraction, normal selectors | `crawlee` | Already fits most structured crawling |
| Selector drift, changing layouts, fingerprint-sensitive targets, stronger session handling, recurring hard scrapes | `scrapling` | Better specialist path |
| Login, clicks, forms, account state, interactive debugging | Browser tools | Real browser control |

## Good Scrapling use cases
- Public sites where simple fetchers get blocked or degraded
- Repeated extraction from pages that change layout often
- Dynamic pages that need rendering but not manual interaction
- Medium-sized crawling jobs where pause/resume or stronger fetch behavior matters
- A pilot where Ahmed wants to test if a hard target can be stabilized

## Bad Scrapling use cases
- Documentation reads
- Easy news/article pages
- Tasks already solved by `web_fetch`
- Logged-in workflows
- LinkedIn job scraping
- Anything where browser tools are required for clicking through stateful UI

## Escalation path
1. Try `web_fetch` if the request is basically a read.
2. Try `crawlee` if the request is a normal static extraction or crawl.
3. Escalate to Scrapling only when the target is hard enough to justify it.
4. Escalate to browser automation if login or real interaction is required.

## Pilot checklist
Before recommending Scrapling as the preferred path for a target, confirm:
- output quality is better than `web_fetch` or `crawlee`
- it does not add unacceptable latency or operational pain
- it works on at least 2 or 3 real targets that previously caused problems
- failures are understandable enough to debug, not just opaque stealth errors
