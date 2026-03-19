# Step 2.5 — Autoresearch Optimization Loop

After ATS scoring in Step 2, if the score is between 82-89%, run the autoresearch loop to push it to 90%+:

1. Read the full autoresearch prompt: `scripts/cv-autoresearch.md`
2. Run the loop: baseline → identify gaps → make ONE atomic change → re-score → keep/revert → repeat
3. Max 10 iterations, stop at 90%+ or after 5 consecutive no-improvement iterations
4. Log all iterations to `/tmp/cv-autoresearch-log.tsv`

If score is already 90%+, skip the loop and proceed to Step 3.
If score is below 82%, recommend SKIP (do not enter the loop).

The loop ONLY adjusts: keyword selection, bullet ordering, summary wording, competency selection.
The loop NEVER: fabricates data, adds fake roles, invents metrics.
