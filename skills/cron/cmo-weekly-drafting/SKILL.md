---
name: cmo-weekly-drafting
summary: Cron skill for the Sunday CMO weekly research, drafting, asset, and approval-calendar workflow.
description: Use this when running or migrating the CMO Weekly Drafting cron. It preserves the existing Sunday workflow while moving the operational prompt out of cron payload storage.
---

# CMO Weekly Drafting

Run the Sunday CMO drafting workflow from the CMO workspace. This skill is the standing-order source for the `CMO Weekly Drafting` cron job.

## Non-negotiable rules

- Operate only from `/root/.openclaw/workspace-cmo` for CMO artifacts.
- Use Africa/Cairo date context for `YYYY-MM-DD` output paths unless the cron run provides a more specific date.
- Treat these as source-of-truth inputs:
  - `/root/.openclaw/workspace-cmo/content-strategy.md`
  - `/root/.openclaw/workspace-cmo/post-quality-rules.md`
  - `/root/.openclaw/workspace-cmo/SOUL.md`
  - `/root/.openclaw/workspace/memory/master-cv-data.md`
  - `/root/.openclaw/workspace/data/sayyad-company-watchlist.json`
- Do not auto-publish anything.
- Do not invent approvals. The approval calendar must be seeded from the actual draft file.
- If image generation or asset creation fails, mark the affected post text-only and continue.
- Keep the final report concise enough for Telegram delivery.

## Workflow

1. Read the source-of-truth files listed above.
2. Research current topics in:
   - digital transformation
   - PMO and program delivery
   - GCC technology and policy
   - healthcare IT and healthcare digitization
   - fintech and digital payments
3. Scan recent Saudi Vision 2030, UAE technology policy, and GCC healthcare digitization themes.
4. Check the SAYYAD watchlist companies for relevant news or signals, but do not revive disabled SAYYAD automation.
5. Save research to:

   ```text
   /root/.openclaw/workspace-cmo/research/YYYY-MM-DD-weekly-scan.md
   ```

6. Draft four posts for the next posting week and save them to:

   ```text
   /root/.openclaw/workspace-cmo/drafts/YYYY-MM-DD-draft.md
   ```

7. Generate simple branded images for each post when possible and save them under:

   ```text
   /root/.openclaw/workspace-cmo/drafts/images/
   ```

8. Immediately seed the approval calendar from the draft file:

   ```bash
   python3 /root/.openclaw/workspace-cmo/scripts/build-post-approval-calendar.py --batch /root/.openclaw/workspace-cmo/drafts/YYYY-MM-DD-draft.md --week-mode next
   ```

9. Update:

   ```text
   /root/.openclaw/workspace-cmo/reports/latest.md
   ```

10. Send Ahmed a concise Telegram DM summary with:
    - the four draft angles
    - suggested posting days
    - where the draft, research, images, and latest report were saved
    - any text-only asset fallbacks

## Failure handling

- If research access is partial, continue with available evidence and mark gaps in the summary.
- If approval-calendar seeding fails, do not publish or work around it silently. Report the exact command and error.
- If a source-of-truth file is missing, stop and report the missing path unless it is non-critical to a single post angle.

## Suggested slim cron prompt

Do not apply this from inside the skill. A future gateway edit can replace the large inline prompt with:

```text
Use the CMO Weekly Drafting cron skill at `/root/.openclaw/workspace/skills/cron/cmo-weekly-drafting/SKILL.md`. Execute the Sunday workflow for this run.
```
