---
name: executive-account-intelligence
description: Maintain bounded, evidence-linked dossiers for Ahmed's highest-priority employers and opportunities. Use when a high-value role is application-ready, when preparing employer strategy or networking, or during the weekly CEO/NASR operating review.
---

# Executive Account Intelligence

Treat an employer dossier as persistent decision support, not as an autonomous agent identity or permission boundary.

## Workflow

1. Select only current high-value employers: application-ready executive roles, strong strategic access, or an active interview/recruiter signal. Keep at most seven active dossiers.
2. Read the existing dossier before writing. Update by evidence, never by assumption.
3. Separate these fields:
   - verified strategy and company context;
   - decision-makers with exact source and retrieval date;
   - recent signals with source and date;
   - application history and current stage;
   - hypotheses explicitly marked as not facts;
   - next actions and approval boundary.
4. Store JSON under `data/account-experts/accounts/` and refresh the registry and Markdown views:

   ```bash
   python3 scripts/account-experts.py refresh
   python3 scripts/account-experts.py audit
   ```

5. Refresh a dossier when the opportunity stage changes or after 14 days. Archive only through a reviewed, recoverable operation; never auto-delete.

## Evidence Rules

- Prefer the employer's official site, official leadership pages, filings, and official announcements.
- A JobZoom report proves the role was found and scored; it does not prove employer strategy, reporting lines, or relationships.
- Leave decision-makers empty when the hiring chain is not verified.
- Mark ambiguous company identity as `ambiguous` and block networking recommendations until resolved.
- Re-derive material claims before using them in a CV, interview brief, or outreach draft.

## Guardrails

- No public posts, applications, recruiter messages, or third-party contact without the existing approval and workflow gates.
- Do not change JobZoom prompts, thresholds, scope, or applied ledgers.
- Do not store credentials, private correspondence, or raw session text.
- The weekly audit may recommend refresh, combine, or archive; it may not perform those mutations.
