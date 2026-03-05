# AI Automation Roadmap

*Last updated: 2026-03-05 06:37 UTC*

## ✅ Live Automations

| # | Automation | Status | Model | Cron |
|---|-----------|--------|-------|------|
| 1 | Executive Intelligence Briefing | ✅ Live | MiniMax M2.5 | Daily 6 AM Cairo |
| 2 | Job Radar v3 (JobSpy) | ✅ Live | MiniMax M2.5 | Daily 7 AM Cairo |
| 3 | LinkedIn Content Engine | ✅ Live | MiniMax M2.5 | Sun-Thu 11:30 AM Cairo |
| 4 | Advisory Board (Daily + Weekly) | ✅ Live | Python (local) | Daily 5 AM UTC |
| 5 | Heartbeat Monitor | ✅ Live | MiniMax M2.5 | Hourly |
| 6 | Gmail Automation (Himalaya) | ✅ Live | CLI | On demand |
| 7 | Quota Monitor + Fallback Validator | ✅ Live | Bash/Node | Daily 00:00 + 06:00 UTC |
| 8 | Monthly Maintenance | ✅ Live | MiniMax M2.5 | 1st of month 9 AM Cairo |
| 9 | Memory Indexing (QMD) | ✅ Live | Ollama | 5min debounce |
| 10 | Mission Control v3 Dashboard | ✅ Live | Next.js | PM2 managed |

## 🟡 Next High-Value Automations

| # | Automation | Value | Effort | Priority |
|---|-----------|-------|--------|----------|
| 1 | Auto CV Tailoring on new JD | Saves 2-3h per application | Medium | HIGH |
| 2 | LinkedIn Comment Radar (enhanced) | Engagement + visibility | Medium | MEDIUM |
| 3 | Interview Prep Auto-Generator | On-demand prep packs per company | Low | MEDIUM |
| 4 | Recruiter Outreach Pipeline | Automated follow-ups + tracking | Medium | HIGH |
| 5 | Calendar Integration (Google) | Auto-block interview slots | Low | LOW |

## Architecture

- VPS: Hostinger (Ubuntu)
- Orchestrator: OpenClaw
- Models: MiniMax M2.5 (default), Claude Opus/Sonnet/Haiku, GPT-5.3-Codex, Kimi K2.5
- Interface: Telegram
- Dashboard: Mission Control v3 (Tailscale HTTPS)
- Memory: Markdown + QMD semantic search
- Version Control: GitHub (openclaw-nasr + mission-control)

---

**Links:** [[../TOOLS.md]] | [[../GOALS.md]] | [[active-tasks.md]]
