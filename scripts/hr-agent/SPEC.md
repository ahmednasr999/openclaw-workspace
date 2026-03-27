# HR Agent — SPEC.md

## Purpose
A Sonnet 4.6-powered agent that acts on job recommendations from the pipeline. When Ahmed says "apply to #N" or "let's go on [role] at [company]", this agent:
1. Pulls the full job from `jobs-summary.json`
2. Checks ontology graph for prior applications + LinkedIn connections at that company
3. Builds a tailored CV (PDF)
4. Writes a cover letter
5. Drafts outreach (LinkedIn note to recruiter/connection)
6. Updates Notion Job Pipeline DB → "Applied"
7. Updates ontology graph
8. Sends summary to Telegram

## Trigger
- Ahmed says "apply to #17" or "let's do #3" in DM or thread
- Agent is spawned with: job number/nickname + Sonnet 4.6 model
- Can handle multiple jobs in one call (e.g., "apply to 3, 7, and 12")

## Input
- `data/jobs-summary.json` — job data (already scored SUBMIT/REVIEW)
- `memory/master-cv-data.md` — Ahmed's career history
- `memory/ontology/graph.jsonl` — prior applications, orgs, people

## Output (per job)
- `media/cv-temp/{Company} - {Title} - Ahmed Nasr.pdf` — tailored CV
- Notion Pipeline DB: entry updated to `Applied`, CV linked
- Ontology: JobApplication entity created/updated
- Telegram: summary card with CV + outreach draft + apply links

## Notion Job Pipeline DB
- DB ID: `3268d599-a162-81b4-b768-f162adfa4971`
- On "Applied" status: set `Stage=Applied`, `Applied Date=today`, `CV Link={pdf_path}`

## Ontology Operations
1. Find or create Organization for the company
2. Find or create JobApplication with `status=applied`, `date_applied=today`
3. Check for existing Outreach to same company (flag if duplicate)
4. Create Document entity for the tailored CV

## LinkedIn Outreach Draft (when connection found)
- Personalized note referencing shared connection or company news
- 3-4 sentences, Ahmed's voice
- Short enough for LinkedIn's 300-char limit on connection notes

## Cover Letter
- 250-300 words
- Addresses the specific role's requirements
- Ahmed's voice — direct, executive, no fluff
-结构: Hook → Alignment → Value Prop → Call to action

## Telegram Summary Card Format
```
🎯 APPLYING: {Title} @ {Company}
📍 {Location} | Fit:{N} ATS:{N}
🔗 {job_url}
📄 CV: {pdf_path}
✉️ Outreach: {draft_note or "no connection found"}
📅 Applied: {today}
```

## Model & Cost
- Sonnet 4.6 for all LLM calls (cover letter, outreach, CV commentary)
- MiniMax-M2.7 for extraction/lookup tasks if needed
- Target cost: ~$0.10-0.20 per job application (Sonnet usage)

## Error Handling
- Job not found in summary → ask Ahmed to confirm number
- Already applied (ontology check) → flag, ask Ahmed to confirm
- CV build fails → fall back to master CV with manual notes
- Notion update fails → log to ontology anyway, retry Notion separately

## File Structure
```
scripts/
  hr-agent.py                    # Main agent entry point
data/
  jobs-summary.json              # Source of truth for jobs
media/
  cv-temp/                       # Generated tailored CVs (14-day retention)
memory/
  ontology/
    graph.jsonl                   # Applications tracked here
```

## Integration with Existing Pipeline
- Does NOT replace jobs-review.py — that stays MiniMax, runs on cron
- Complements it: pipeline scores → human picks → HR agent executes
-ontology graph is shared: pipeline reads applied count, HR agent writes new applications
