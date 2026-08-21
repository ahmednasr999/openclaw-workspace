---
name: cmo-weekly-content-report
description: Use this for the existing CMO Weekly Content Report cron. It captures weekly LinkedIn evidence when the approved Windows Chrome author-analytics lane is available, evaluates the governed hook experiment without automatic adaptation, and prepares the next topic slate for Ahmed approval.
---

# CMO Weekly Content Report

Run the Friday evidence and content-planning review from `/root/.openclaw/workspace-cmo`.

## Boundaries

- Keep the model on `openai/gpt-5.6-sol`.
- Do not approve, schedule, reschedule, publish, comment, like, connect, or message third parties.
- Do not change cadence, hooks, formats, prompts, or cohort definitions automatically.
- Use only the verified Windows Chrome extension lane for LinkedIn account-state or author analytics. If Windows Chrome is unavailable or the authenticated analytics view cannot be opened, skip capture and state the evidence gap. Do not substitute Ahmed-Mac, the VPS browser, Exa, or public estimates.
- Treat internal scores and impressions as directional evidence, not business outcomes.

## Sources

- `/root/.openclaw/workspace-cmo/config/governed-content-experiment.json`
- `/root/.openclaw/workspace-cmo/data/linkedin-metrics-manual-capture.csv`
- `/root/.openclaw/workspace-cmo/LOOPS.md`
- `/root/.openclaw/workspace-cmo/content-strategy.md`
- `/root/.openclaw/workspace/memory/master-cv-data.md`
- `/root/.openclaw/workspace/data/executive-intelligence-content-candidates-latest.json`
- `/root/.openclaw/workspace/data/linkedin-rss-pillar-slate-latest.json`
- Last 30 days of the live Notion Content Calendar.

## Workflow

1. Run `python3 scripts/linkedin-cadence-metrics.py` and identify posts missing current public or grounded-outcome metrics.
2. If Windows Chrome and the authenticated author-analytics view are available, follow `/root/.openclaw/workspace-cmo/LOOPS.md` and capture the newest missing weekly evidence. Update only the canonical metrics CSV, preserve existing values unless replacing them with fresher visible evidence, and record the capture time/source.
3. If account evidence is unavailable, record one concise skip reason and continue with the last verified metrics.
4. Rerun:

   ```bash
   python3 scripts/linkedin-cadence-metrics.py
   python3 scripts/cmo_governed_outcomes.py
   ```

5. Read the active experiment config and report:
   - cadence versus the 3-4 weekly target;
   - Reach/Authority/Conversion mix, including every unclassified post;
   - role-specific outcomes: Reach by impressions/relevant followers/qualified profile visits, Authority by saves/substantive comments/qualified profile visits, and Conversion by qualified inbound conversations or attributable opportunities;
   - historical baseline, active experiment cohort, and A/B hook-variant sizes;
   - public/outcome coverage;
   - impressions, reactions, comments, reposts, saves, sends, qualified profile visits, relevant followers, and qualified inbound conversations;
   - whether the comparison gate is ready;
   - counter-metrics and evidence gaps.
6. Keep the experiment `shadow-manual-only`. Compare the direct-thesis control and executive-tension treatment only within the fixed Sun/Tue/Thu cadence; do not use the former daily cadence as a causal control. Before all six posts and the review date are complete, use a hold verdict. Afterward, recommend a change only when outcome and counter-metric evidence support it, and leave approval to Ahmed.
7. Build a seven-topic review slate:
   - up to four qualified current signals from the unified executive-intelligence feed;
   - two evergreen topics from Ahmed's least-represented positioning pillars;
   - one personal executive insight grounded only in verified career evidence.
8. For every topic include pillar, funnel role, intended reader action, source/evidence, Ahmed executive angle, opening hook, and format. The recommended four-post subset must contain 1 Reach, 2 Authority, and 1 Conversion topic; a three-post alternative must contain one of each. Reject stale, promotional, inaccessible, weakly sourced, or duplicate items. Replace current-signal shortfalls with evergreen ideas rather than lowering the gate.
9. Write `reports/latest.md` and the dated Friday report.
10. Send Ahmed one concise evidence-based summary and ask him to approve, reject, or edit the topic slate.

## Success Gate

- Both deterministic reports were rerun after any capture attempt.
- The report separates observed evidence from missing or unavailable outcomes.
- The active experiment remains manual-only.
- No public or calendar write occurred.
- The seven-topic slate contains no invented metric, career fact, or source claim.

## Failure Handling

- If Windows Chrome is unavailable or analytics are inaccessible, continue with a clearly labeled evidence gap.
- If the metrics CSV or experiment config is structurally invalid, stop the experiment analysis and report the exact file/check failure. Do not repair data by guessing.
- If Notion is unavailable, use the last verified local runway only and label it stale.
