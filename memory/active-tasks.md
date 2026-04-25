# Active Tasks

## 2026-04-17 - JobZoom scorer reliability check
- Priority: medium
- Status: open
- Context: ad hoc pass2 scoring of today's reconstructed 60-job pass1 pool initially appeared hung around batch 1/6 before later completing. This could silently suppress surfaced jobs if the same behavior happens in the live daily run.
- Immediate evidence:
  - delayed/no visible output for an extended period at batch 1/6
  - later completion with all 6 batches scored and 6 jobs >=70
- Risk: intermittent stall, gateway/API latency, or weak batch-run observability could cause missed surfaced jobs or misleading operator reads.
- Follow-up after taxonomy work:
  1. reproduce with timing instrumentation,
  2. inspect whether the live cron run ever stalls similarly,
  3. add clearer progress/error logging and a timeout/escalation path if needed.

## 2026-04-17 - JobZoom scraper path drift guard
- Priority: low
- Status: open
- Context: `workspace-jobzoom/scripts/daily_run.py` calls `/root/.openclaw/workspace/scripts/jobs-source-linkedin-jobspy.py` instead of the JobZoom-local copy.
- Current state: both files are identical today, so behavior is not broken now.
- Risk: they can silently drift later and JobZoom would run the wrong scraper version.
- Preferred fixes:
  1. point JobZoom to the local script path, or
  2. add a daily diff check that alerts on drift.
- Do not change this blindly during unrelated pipeline work.
