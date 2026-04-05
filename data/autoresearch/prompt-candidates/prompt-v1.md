# Prompt v1 — Auto-generated 2026-03-21

## How to apply
Run: `python3 scripts/apply-autoresearch-prompt.py` to review and apply.

## Changes from previous version
(See job-review-log.json for change details)

## Improved Prompt Block

```
{candidate_profile}

TASK: Review these {len(jobs)} jobs and score each for career fit.

{jobs_text}

For EACH job, provide:
1. Career Fit Score (1-10): How well does this role match the candidate's profile?
2. Verdict: SUBMIT (score 7+), REVIEW (score 5-6), or SKIP (score 1-4)
3. One-line reason

OUTPUT FORMAT (JSON array):
[
  {{"job_num": 1, "score": 8, "verdict": "SUBMIT", "reason": "Strong DT leadership role in target geography"}},
  {{"job_num": 2, "score": 4, "verdict": "SKIP", "reason": "Hands-on engineering focus, not strategic"}},
  ...
]


═══════════════════════════════════════════════════════════
GOLDEN RULES (DO NOT MODIFY — permanent constraints):
- Always score based on TITLE + COMPANY + LOCATION even when no description is available
- Never penalize a job for missing description — title is the primary signal
- A job titled "Director Digital Transformation" at a GCC company is MINIMUM a 7
- Never score a role 7+ if it contradicts the dealbreakers below
═══════════════════════════════════════════════════════════


AUTO-LEARNED EXCLUSION RULES (v1):

DEALBREAKER — NATIONALS ONLY (AUTOMATIC SKIP):
- If title or description contains ANY of the following, score 1 and SKIP immediately:
  "nationals only", "UAE national", "Emirati only", "Saudi only", "Kuwaiti national",
  "Bahraini national", "Qatari national", "Omani national", "citizen only", "GCC national"
- These roles are legally restricted and cannot be applied for. Do NOT score them 7+.
- Pattern to detect: parenthetical like "(UAE Nationals Only)" or dash like "– UAE National"


SCORING GUIDELINES:
- 9-10: Perfect match - exact target role (DT Director, VP PMO, Head of Technology), target location (GCC), strong domain
- 7-8: Strong match - right seniority (Director/VP/Head/SVP/C-level), relevant domain, target geography
- 5-6: Partial match - right seniority but different domain, or right domain but mid-level title
- 3-4: Weak match - some relevance but wrong seniority or wrong geography
- 1-2: No match - junior role, wrong field entirely, or anti-pattern (pure sales/HR/civil)

IMPORTANT: Score based on TITLE + COMPANY + LOCATION even when no description is available.
A job titled "Director Digital Transformation" at a GCC company is at MINIMUM a 7 based on title alone.
Do NOT penalize jobs for missing descriptions - the title is the primary signal.

Return ONLY the JSON array, no other text.
```
