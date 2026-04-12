# Cron Inventory

Generated from live `cron list` snapshot on 2026-04-11.

## Snapshot
- Total jobs: 27
- Primary model on active jobs: `openai-codex/gpt-5.4`
- Common execution style: isolated `agentTurn`
- Main delivery surfaces: Telegram DM `866838380` and Telegram group topics under `-1003882622947`

## Highest practical-cost lanes
- **Email Agent (Sun-Thu)**, frequent daytime cadence
- **Email Agent (Fri-Sat)**, frequent weekend cadence
- **JobZoom Daily Scan**, long runtime daily lane
- **Dream Mode - Memory Consolidation**, heavy autonomous memory-writing job
- **Weekly Skill Autoresearch**, autonomous skill-editing job

## Jobs by domain

### Main / CEO / DM layer
- Model Guardian
- Daily Intel Sweep
- Dream Mode - Memory Consolidation
- Calendar Pre-fetch
- JobZoom Daily Scan
- Weekly Self-Health Check
- Tomorrow morning post-change verification
- X Intelligence Crawler - Weekly
- Weekly Skill Autoresearch

### HR / job-search adjacent
- Email Agent (Sun-Thu)
- Email Agent (Fri-Sat)

### CTO / operations / maintenance
- Daily Session Cleanup
- LCM Nightly Health Check
- session-watchdog
- LCM Force-Compact Processor
- NASR Doctor (Daily)
- weekly-memory-hygiene
- Weekly Pipeline Audit
- Job Hunter — Weekly Domain Review
- Weekly Team Retro
- SIE Weekly Report
- LCM Midday Compaction Sweep

### CMO / content
- CMO Weekly Outreach Queue — Sunday
- CMO Weekly Drafting
- CMO Daily Post Approval Send
- RSS Intelligence - Weekly Crawl
- CMO Weekly Content Report

## Current notable jobs

### Operationally important
- **Model Guardian**: every 6h, guards GPT-5.4 routing/token posture
- **NASR Doctor (Daily)**: daily ops check in CTO lane
- **Weekly Self-Health Check**: Sunday CEO General summary
- **Tomorrow morning post-change verification**: one-shot verification after safe cron changes

### Heavy / optimization candidates
- **JobZoom Daily Scan**: long runtime lane, daily
- **Email Agent** pair: highest recurring frequency, ideal for a cheap pre-check gate

### Intentionally silent on success
- **Daily Intel Sweep**
- **Calendar Pre-fetch**

## Delivery map in practice
- DM `866838380`: main alerts, summaries, selected CMO outputs
- Topic 10: CEO General / main operational reporting
- Topic 8: CTO / maintenance lane
- Topic 9: HR lane
- Topic 7: CMO lane
- Topic 5247: JobZoom lane

## Known oddities worth cleaning later
- Some CMO jobs still carry `sessionKey` values pointing to main direct DM.
- `LCM Midday Compaction Sweep` is `agentId: cto` but carries a CMO-flavored session key.
- A few jobs rely on delivery defaults or mixed target notation styles (`:8` vs `:topic:8`).

## Reference rule
Use this page for orientation, not as the authoritative scheduler database. Live truth remains the cron registry itself.
