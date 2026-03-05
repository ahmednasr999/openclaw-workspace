# Last Session
Updated: 2026-03-05 11:52 UTC

## What We Did (Mar 5, morning-midday)
- Discussed JobSpy, Crawlee, LinkedIn scraping approaches
- Built LinkedIn JD Fetcher: Playwright + li_at cookie, runs 100% on VPS, no Mac needed
- Built linkedin-add-to-sheet.py: auto-adds GO jobs (>=82%) to Google Sheet via gog
- Tested pipeline on 5 jobs: 4 SKIP (Dalil IT 58%, Talan CTO 68%, Insurance CTO 35%, IT Director Riyadh 66%), 1 GO (Senior Director Tech UAE 87% - added to Sheet row 7)
- CV build for Senior Director Tech (Confidential UAE) spawned as Opus sub-agent (in progress)
- Context hit 86% - session flushed

## Open Threads
1. CV build for Senior Director Technology - Opus sub-agent running, will auto-announce
2. Ahmed triaging more LinkedIn jobs - pipeline continues
3. Monthly model routing audit cron: still not created
4. "Process sheet" on-demand trigger: discussed, not yet built
5. Bayt integration into Job Radar: recommended, not yet done

## Key Decisions
- Google Sheet = primary pipeline tracker (not pipeline.md)
- LinkedIn URL workflow: send URL → VPS fetches JD → ATS score → auto-add if >=82%
- Cookie: li_at stored in config/linkedin-cookies.json (gitignored)
- ATS threshold: 82% (MiniMax calibrated)

## State
- Pipeline: 47 applied + 1 new GO (Senior Director Tech, row 7)
- LinkedIn cookie: active, months before expiry
- Scripts committed: linkedin-jd-fetcher.py, linkedin-cookie-setup.py, linkedin-add-to-sheet.py


Updated: 2026-03-05 10:27 UTC

## What We Did
- ATS scoring model benchmark (MiniMax vs Haiku vs Opus): MiniMax won, locked as primary scorer
- Claude quota full audit: all crons moved to MiniMax, 0 Claude background tasks remaining
- Google Sheet enhanced: CV GitHub Link (M), Ready to Apply (N), Duplicate Check (O)
- Built 2 CVs end-to-end: Director DT (87%) and Head PMO (88%), both ready to apply
- Borderline tie-breaker protocol automated (no manual approval)

## Open Threads
- Monthly model routing audit cron: needs to be created
- "Process sheet" on-demand trigger: discussed, not yet built
- Context hit 70%: session flushed Context

*Updated: 2026-03-05 07:31 UTC*

## What We Were Doing
Morning maintenance + job pipeline triage session with Ahmed.

## Key Decisions
- Brave Search fully removed (no API key, never had one)
- Job Radar rebuilt with JobSpy (replaces Tavily)
- Pipeline sorting rules locked: Active by date, Radar by priority
- Ahmed reviewing radar jobs one by one, skipping medium priority items
- Ahmed about to send fresh LinkedIn jobs for review/CV tailoring

## Open Threads
1. Ahmed sending fresh LinkedIn job links (in progress when session ended)
2. 11 radar items remaining (medium/low priority, can triage later)
3. Morning briefing cron had wrong post for today (showed yesterday's Salesforce post instead of today's compound growth post)

## State
- Pipeline: 47 applied, 11 radar remaining
- Fugro applied (ATS 90%)
- 4 radar items skipped (Michael Page duplicate, Bosperous PHP, The IN Group recruitment, Careem ML)
