# Final CV Acceptance Checklist

Every answer must be **YES** before delivery. Any **NO** blocks delivery and requires regeneration or correction.

- [ ] Was the CV generated only from `memory/master-cv-data.md`, `memory/cv-pending-updates.md`, the full JD, and verified application context?
- [ ] Are all employers and role titles exact, with no recruiter name substituted as the company and no unsupported skill, keyword, metric, achievement, or credential?
- [ ] Does extracted text contain separated role metadata, real bullet formatting, at least 12 experience bullets, and no artificial sections such as `Role Keywords Matched` or `Target Role`?
- [ ] Is ATS fit at least 82%, with the full-JD source recorded?
- [ ] Did `pdftotext`, `pdfinfo`, `file`, `mutool`, or `qpdf` validate the PDF structure and text, using `identify` only if its availability was confirmed first?
- [ ] Does the final PDF exist under the canonical `/root/.openclaw/workspace/cvs/` directory, and if a wrapper verifier rejects only that allowed path, were the documented direct PDF checks run instead of moving or duplicating the artifact?
- [ ] Were every rendered page visually reviewed and all checks in `quality-gates.md` and `post-gen-checks.md` passed?
- [ ] Is the final filename exactly `Ahmed Nasr - [Role] - [Company].pdf`, and is delivery eligibility clear from the applied-job ledger when applicable?
