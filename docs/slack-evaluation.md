# Slack Setup Evaluation & Recommendations

*Created: 2026-03-08*

---

## Current State

### Channels (10 total)

| ID | Name | Member | Purpose |
|----|------|--------|---------|
| C0AJMCN64V9 | #ai-codex | ✅ Yes | GPT-5.4-Pro for image generation |
| C0AJM8PR0P5 | #ai-content | ✅ Yes | Claude Sonnet 4.6 for content |
| C0AJLTEQTL3 | #ai-general | ✅ Yes | Claude Sonnet 4.6 for general |
| C0AJX895U3E | #ai-jobs | ✅ Yes | Opus 4.6 for job radar |
| C0AK6HSN2HX | #ai-system | ✅ Yes | MiniMax M2.5 for system |
| C0AJQLE957H | #council | ✅ Yes | Model council (future) |
| C0AK3KNLK6G | #nasr-tweets | ✅ Yes | (unused) |
| C0AKV41KF32 | #x-analysis | ✅ Yes | MiniMax for deep analysis |
| C0AJBRTLK71 | #openclaw | ❌ No | General OpenClaw |
| C0AKMHGFV40 | #random | ❌ No | Random chat |

### Cron Delivery (36 total)

| Target Channel | Jobs | % |
|----------------|------|---|
| #ai-system (C0AK6HSN2HX) | 9 | 25% |
| #ai-general (C0AJLTEQTL3) | 8 | 22% |
| #ai-jobs (C0AJX895U3E) | 5 | 14% |
| #ai-content (C0AJM8PR0P5) | 5 | 14% |
| Headless (last) | 6 | 17% |
| Headless (none) | 2 | 6% |
| #nasr-tweets (C0AK3KNLK6G) | 1 | 3% |

### Missing from Cron Output
- **#ai-codex (C0AJMCN64V9):** 0 jobs
- **#x-analysis (C0AKV41KF32):** 0 jobs
- **#council (C0AJQLE957H):** 0 jobs

---

## Issues Found

### 1. Orphan Cron (C0AK3KNLK6G)
- Job `53fd173d` delivers to `channel:C0AK3KNLK6G` (typo format)
- Should be `C0AK3KNLK6G` directly

### 2. Unused Channels
- **#ai-codex:** Model GPT-5.4 configured but nothing uses it
- **#x-analysis:** Configured but empty
- **#council:** Created but not active

### 3. Bot Not in Channels
- #openclaw: Bot not member
- #random: Bot not member

### 4. Headless Jobs (8 total)
- 6 jobs with `delivery: "last"` (delivers to last active session)
- 2 jobs with no delivery channel

---

## Recommendations

### Priority 1: Fix Orphan Cron
- Fix job `53fd173d` delivery format

### Priority 2: Add Jobs to Empty Channels
| Channel | Add This Cron |
|---------|---------------|
| #ai-codex | Weekly image generation test (GPT-5.4) |
| #x-analysis | Weekly "deep analysis" summary |
| #council | Model council trigger (future) |

### Priority 3: Optimize Channel Mapping

| Category | Current Channel | Recommendation |
|----------|----------------|----------------|
| Job Radar | #ai-jobs | ✅ Keep (Opus correct) |
| Content Creator | #ai-content | ✅ Keep (Sonnet correct) |
| Executive Brief | #ai-general | ✅ Keep (Sonnet correct) |
| Calendar/Alerts | #ai-system | ✅ Keep (MiniMax correct) |
| Image Generation | #ai-codex | ✅ Keep (GPT-5.4 correct) |
| Deep Analysis | #x-analysis | ✅ Keep (MiniMax correct) |

### Priority 4: Optional Improvements
- Invite bot to #openclaw and #random if you want it to participate
- Consider merging #ai-general + #x-analysis if they overlap

---

## Summary

**What's working:** Channel model assignment is correct. Each channel has the right model pinned.

**What needs fixing:** 1 orphan cron, 3 empty channels, 8 headless jobs.

**Action items:** 1 (fix orphan) + 3 (add jobs to empty channels) = 4 concrete fixes.

