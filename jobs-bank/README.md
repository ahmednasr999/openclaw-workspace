# 🎯 Jobs Bank — Ahmed Nasr

Single source of truth for all executive job opportunities.

## Structure

```
jobs-bank/
├── README.md              ← This file
├── pipeline.md            ← Master tracker table
└── applications/
    └── [company-role]/
        ├── job.md         ← JD + ATS score + notes
        └── cv.pdf         ← Tailored CV (ready to send)
```

## Pipeline Stages

| Stage | Meaning |
|-------|---------|
| 🔍 Radar | Found, not yet assessed |
| 📊 ATS Check | ATS analysis in progress |
| 📄 CV Ready | Tailored CV done, awaiting review |
| ✅ Applied | Submitted, tracking follow-up |
| 📞 Interview | Interview scheduled or completed |
| 🤝 Offer | Offer received |
| ❌ Rejected | Closed, no fit |

## Follow-up Rules

- Day 7 after applying → NASR drafts follow-up email for Ahmed's approval
- Day 14 → Second nudge draft
- Day 21 → Flag as stale, move to inactive

## How to Add a Job

NASR handles this automatically when a role is identified. Ahmed can also send a URL and NASR will:
1. Fetch the JD
2. Run ATS analysis
3. Tailor CV
4. Add to pipeline.md + create application folder

**Last updated:** 2026-02-27
