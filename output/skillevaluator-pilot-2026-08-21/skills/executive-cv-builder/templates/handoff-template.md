# Step 6 — Handoff Update (if running inside Pipeline 1)

If a handoff file exists at `jobs-bank/handoff/<job-id>.json`:

1. Populate the `cv` section:
```json
"cv": {
  "path": "cvs/Ahmed Nasr - [Role] - [Company].pdf",
  "github_url": "https://github.com/ahmednasr999/openclaw-nasr/blob/master/cvs/...",
  "ats_score": [score],
  "tailoring_notes": "[key adjustments made]",
  "pending_review": false
}
```
2. Update `status` to `"cv_ready"`
3. Update `nasr_review.approved` to `false`
4. Overwrite trigger file with: `NASR_REVIEW_NEEDED`
