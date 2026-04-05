# Active Tasks - Updated 2026-04-03 (9:10 PM)

## Completed Today (2026-04-03)
- [x] Exec-approvals crash fixed — converted defaults from allowlist to full, gateway restarted
- [x] Cron list crash fixed — Job 10 (LinkedIn Pre-Flight Check) had legacy format, converted to proper schedule object, gateway restarted
- [x] Gmail watcher expired OAuth — already resolved Mar 21 (replaced with Himalaya IMAP), stale task cleaned up

## Completed (March 21)
- [x] 8 SUBMIT jobs processed - all 8 applied
- [x] 7 REVIEW jobs processed - 1 applied (Miral), 4 skipped, 2 already applied
- [x] 10 CVs tailored on Opus 4.6
- [x] Notion sync before every pipeline run
- [x] JD stored in Notion Pipeline pages
- [x] Briefing dedup fixed
- [x] Applied-list double-guard in jobs-review.py
- [x] Autoresearch loop, JD enrichment, model router, SIE 360 split
- [x] GitHub Discovery v3, Watchdog v3, briefing 7/week
- [x] SIE Learner cron fixed

## Open / Backlog
- [ ] Google Jobs native scraping (currently using Indeed proxy via JobSpy)
- [ ] Location verification in job pipeline
- [ ] LinkedIn autoresearch loop for content optimization
- [ ] Security audit: 7 critical items (accepted risk — exec=full intentional, open channel policies)
- [ ] Unused API keys: HeyGen, ElevenLabs, ScrapeCreators (no active work using them, low priority)

## Pending on Ahmed
- None

## Notes
- Mission Control task board decommissioned (per Ahmed)
- Cron system fully operational — 29 jobs across all 4 agents
- Gateway stable, exec-approvals working without manual approval prompts
