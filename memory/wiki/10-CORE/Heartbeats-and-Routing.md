# Heartbeats and Routing

## Intent
Keep heartbeat routing explicit, predictable, and topic-safe.

## Current routing model
- `main`: direct heartbeat allowed
- `hr`: routed to Telegram topic 9, direct blocked
- `cto`: routed to Telegram topic 8, direct blocked
- `cmo`: routed to Telegram topic 7, direct blocked
- `jobzoom`: routed to Telegram topic 5247, direct blocked

## Why this matters
Without explicit direct-delivery policy, routed subagent heartbeats can drift into the wrong place after updates or config interpretation changes.

## Operational rule
When asked "are heartbeats OK?", separate two answers:
- config and routing correctness
- actual observed delivery

Do not claim the second when only the first was checked.

## Topic map
- topic 7 → CMO
- topic 8 → CTO
- topic 9 → HR
- topic 10 → main / CEO General
- topic 5247 → JobZoom

## Debug order for heartbeat confusion
1. Check live config.
2. Confirm topic bindings.
3. Check whether the alert was a real runtime failure or a tooling false alarm.
4. Review gateway logs around the event.
5. Only then conclude delivery failure.

## Known gotcha
A failed config schema lookup can look like a heartbeat failure in alerts even when heartbeat runtime is fine.
