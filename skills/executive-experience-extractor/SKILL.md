---
name: executive-experience-extractor
description: Build and use Ahmed Nasr's private, evidence-backed executive experience bank. Use whenever Ahmed shares a voice note, transcript, CV detail, project story, achievement, leadership lesson, career memory, or asks for STAR stories, interview examples, executive case studies, proof points, content angles, an achievement inventory, or the best experience for a role. Extract direct actions, scope, outcomes, attribution, provenance, disclosure limits, and missing evidence without inventing facts. Route finished evidence to the executive CV, interview, and LinkedIn content workflows.
metadata:
  owner: NASR
  status: active
  privacy: private-career-data
---

# Executive Experience Extractor

Turn Ahmed's career history into reusable, evidence-backed executive stories without overstating causality or leaking private context.

## Source of truth

Read only what the request needs, in this order:

1. `/root/.openclaw/workspace/memory/executive-experience-bank.json` for the canonical experience records.
2. `/root/.openclaw/workspace/memory/master-cv-data.md` for approved role, employer, date, scope, and metric facts.
3. `/root/.openclaw/workspace/memory/cv-pending-updates.md` for approved facts not yet reflected in the master CV.
4. Material Ahmed provides in the current request, such as a voice note, transcript, document, correction, or answer.
5. Other local notes only as discovery evidence. Treat them as candidate claims until they agree with an approved source or Ahmed confirms them.

Do not silently promote a draft post, generated CV, inferred lesson, or old archive into verified career evidence.

## Select the operating mode

| Request | Mode |
|---|---|
| New project memory, voice note, transcript, or achievement | Capture |
| "What story should I use?" or role/JD matching | Retrieve |
| Interview, STAR, CAR, or behavioral question | Interview |
| CV bullet, executive bio, case study, or profile proof | Career asset |
| LinkedIn post, authority series, or thought-leadership angle | Content |
| Thin story, uncertain number, or missing result | Gap fill |

If several modes apply, capture or verify the evidence first, then produce the requested asset.

## Evidence contract

Read `references/evidence-model.md` before creating or changing records.

Protect four distinctions:

- **Ahmed's action:** what he personally led, built, decided, designed, governed, changed, or delivered.
- **Organizational outcome:** what happened to the company, portfolio, platform, or market while he contributed.
- **Scope fact:** budget, countries, users, projects, clients, team size, hospitals, or duration.
- **Leadership lesson:** a useful interpretation, not automatically a historical fact.

Use these attribution labels for outcomes:

- `direct`: the source supports Ahmed causing or delivering the result.
- `shared`: Ahmed contributed materially, but the result belonged to a wider team or organization.
- `contextual`: the result describes the environment and must not be claimed as Ahmed's achievement.

When evidence is incomplete, narrow the claim or mark it `partial`. Never repair a weak story with invented numbers, dates, savings, adoption, revenue, delivery percentages, or causal language.

## Capture workflow

1. Search the bank by organization, role, date, metric, domain, and semantic story match before adding a record.
2. Extract a claim ledger from the source:
   - context and business problem
   - Ahmed's responsibility
   - specific decisions and actions
   - scope and constraints
   - outcomes with attribution
   - stakeholders and operating environment
   - leadership lesson or reusable angle
   - source and exact supporting claim
3. Classify every record:
   - `verified`: supported by the master CV, approved pending update, or Ahmed's explicit confirmation
   - `partial`: core experience is supported but material STAR detail is missing
   - `candidate`: found only in a secondary note or generated artifact
4. Merge with the strongest existing record. Preserve the existing ID and add evidence rather than duplicating the story.
5. Add only material questions to `questions_to_complete`. Prefer questions that unlock a result, decision, trade-off, obstacle, or personal action.
6. Update the JSON bank, then validate and render it:

```bash
python3 skills/executive-experience-extractor/scripts/experience_bank.py validate memory/executive-experience-bank.json
python3 skills/executive-experience-extractor/scripts/experience_bank.py render memory/executive-experience-bank.json memory/executive-experience-bank.md
```

7. Report what changed, what remains uncertain, and which downstream assets became stronger.

## Interview workflow

Read `references/interview-playbook.md` when the request involves interview preparation or gap filling.

For each answer:

1. Match the question to two or three bank records.
2. Prefer the record with the strongest direct action, measurable scope, and relevant lesson.
3. Produce a 60-90 second answer using Situation, Responsibility, Action, Result, Reflection.
4. Use first person only for Ahmed's supported actions. Phrase shared outcomes as "the platform scaled" or "we delivered," then name Ahmed's contribution precisely.
5. Add one short follow-up proof line and one likely interviewer probe.
6. Mark any missing fact instead of improvising it.

## Career asset workflow

- For a CV or ATS request, hand verified evidence to `executive-cv-builder`; that skill owns tailoring, scoring, PDF generation, and delivery.
- Do not change `memory/master-cv-data.md` automatically. Propose a source-backed delta and wait for Ahmed's approval before promoting it.
- For bios, profiles, or case studies, preserve exact titles, dates, employers, and attribution from approved sources.
- Candidate records cannot become external claims until Ahmed confirms them.

## Content workflow

- Start from a verified record and select one unexpected operating lesson.
- Use the pattern `verified experience -> tension -> leadership rule -> peer question` when it fits.
- Read the active content skill before drafting or scheduling content.
- Current-employer material requires extra care: avoid confidential detail, patient information, internal names, unreleased results, or claims that identify sensitive operations.
- Drafting is allowed; public posting, scheduling, commenting, or messaging remains approval-gated.

## Retrieval output

When Ahmed asks for the best stories, return a compact ranked table:

| Rank | Story | Why it fits | Proof | Attribution | Gap/risk |
|---:|---|---|---|---|---|

Then provide the strongest story in the requested format. Do not dump the whole bank unless asked.

## Capture closeout

Use this structure after an update:

```markdown
## Experience captured
- Record: [id and title]
- Status: [verified / partial / candidate]
- Strongest proof: [fact]
- Reuse unlocked: [CV / interview / content / case study]

## Still worth clarifying
1. [highest-value question]

## Files updated
- [canonical bank]
- [rendered view]
```

## Approval and privacy boundaries

- Keep the bank local and private by default.
- Do not send, upload, publish, or sync career evidence to a third party without explicit approval.
- Do not expose private contact details or confidential current-employer information in derived assets.
- Never infer that a metric is public merely because it appears in a local CV or draft.
- User corrections override older records. Preserve the correction source and retire the contradicted claim.

## Verification

Read `eval/checklist.md` before claiming a capture or derived asset is complete.

Done means:

- the bank validates successfully
- record IDs are unique
- every metric and outcome points to source evidence
- attribution is explicit
- unsupported claims are excluded or visibly marked
- the rendered Markdown reflects the JSON bank
- no external action occurred without approval

## Bundled resources

- `references/evidence-model.md` - canonical record model and evidence rules
- `references/interview-playbook.md` - high-yield questioning and answer construction
- `eval/checklist.md` - binary quality gate
- `evals/evals.json` - realistic test prompts
- `scripts/experience_bank.py` - standard-library validator, statistics, and renderer

