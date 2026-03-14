---
description: "Current financial overview: subscription costs, model spend, budget tracking"
type: data
topics: [strategy]
updated: 2026-03-14
---

# Financial Snapshot: AI Infrastructure

*Last updated: 2026-03-05 06:37 UTC*

## Monthly Costs (Fixed)

| Provider | Plan | Cost | Billing |
|----------|------|------|---------|
| Claude Max 20x | Opus + Sonnet + Haiku | EGP 9,000/mo | Monthly |
| MiniMax Coding Plus | M2.5-highspeed | $40/mo | Monthly |
| ChatGPT Plus | GPT-5.3-Codex | $20/mo (cancelled, active until Apr 1) | Cancelled |
| Hostinger VPS | Ubuntu server | ~$10/mo | Annual |
| Tailscale | Free tier | $0 | Free |
| GitHub | Free tier (2 repos) | $0 | Free |

## Monthly Total

| Period | Cost |
|--------|------|
| Mar 2026 | EGP 9,000 + $50/mo (~$70 total USD portion) |
| Apr 2026+ | EGP 9,000 + $40/mo (~$50 total USD portion, Codex dropped) |

## Cost Optimization Actions Taken

- 2026-03-04: Cancelled ChatGPT Plus ($20/mo saved from Apr 1)
- 2026-03-04: Upgraded Claude from Max 5x to Max 20x (EGP 4,399 to EGP 9,000, 4x quota)
- 2026-02-24: All crons/heartbeats moved to MiniMax M2.5 (flat rate, no per-token cost)
- 2026-02-27: Quota monitoring deployed (prevents cascade failures)

## Free Tier Usage

| Service | Allocation | Usage |
|---------|-----------|-------|
| Tavily Search | 1,000 credits/mo | Low (~50/mo) |
| Kimi K2.5 | Essentially free | Backup only |
| Ollama (local) | Free | Memory indexing |

## Budget Rule

All three primary providers are flat-fee subscriptions. Optimization = spreading load across providers, not saving per-token costs. Default to MiniMax for background tasks, reserve Claude for quality-critical work.

---

**Links:** [[../TOOLS.md]] | [[../MEMORY.md]]
