# HealthTech Directory - Day 2: Claude Code Prompts
**Cleaning, Deduplication, and Structuring**

---

## Pass 1: Deduplication

### Claude Code Prompt
```
Clean this HealthTech company list (gcc-healthtech-raw.json):

1. Remove exact duplicates (same company name)
2. Normalize company names:
   - Remove "LLC", "Inc", "Ltd", "Group", "Holding"
   - Standardize spacing and punctuation
   - Fix encoding issues

3. Flag near-duplicates (90% similarity):
   - "Dubai Health" vs "Dubai Health Authority"
   - "Al Amal" vs "Al Amal Hospital"

4. Output format:
{
  "deduplicated": [company_names],
  "near_duplicates": [[name1, name2, reason]],
  "removed": [original_names],
  "stats": {
    "original_count": X,
    "deduplicated_count": Y,
    "removed_count": Z
  }
}

Focus on accuracy over speed. Report each decision.
```

### Expected Output
- `gcc-healthtech-deduped.json`
- Statistics on duplicates removed

---

## Pass 2: Structure

### Claude Code Prompt
```
Structure each company in gcc-healthtech-deduped.json:

For each company, output JSON with:

{
  "company_name": "exact name from source",
  "website": "https://..." or null,
  "linkedin": "https://linkedin.com/company/..." or null,
  "location": {
    "country": "UAE|KSA|Egypt|Kuwait|Qatar|Bahrain|Oman|GCC",
    "city": "Dubai|Riyadh|Cairo|...",
    "address": "full address or null"
  },
  "category": "Hospital|Clinic|HealthTech|MedTech|Payer|Provider|Pharmaceutical|Biotech|Digital Health|Telemedicine|Other",
  "size": "Startup|SME|Enterprise",
  "funding": "Bootstrapped|Seed|Series A|Series B|Series C|PE|Public|Unknown",
  "contact": {
    "linkedin_url": "url or null",
    "email_domain": "company.com or null",
    "email_format": "{first}.{last} or {first}{last} or null"
  },
  "hiring": {
    "pmo_roles": boolean,
    "tech_roles": boolean,
    "careers_url": "url or null"
  },
  "data_quality": "High|Medium|Low",
  "source": "linkedin|crunchbase|manual|other"
}

Use educated guesses where data is missing. Flag uncertain fields.
```

### Expected Output
- `gcc-healthtech-structured.json`
- 3,000+ structured records

---

## Pass 3: Quality Scoring

### Claude Code Prompt
```
Add quality score (1-10) to each company in gcc-healthtech-structured.json:

Quality criteria:
- Website exists AND loads (2 points)
- LinkedIn present (2 points)
- Email format guessable from domain (2 points)
- Hiring page or PMO roles mentioned (2 points)
- Specific location (city) (2 points)

Output:
{
  "quality_scores": {
    "company_name": {
      "score": 1-10,
      "breakdown": {
        "website": 0-2,
        "linkedin": 0-2,
        "email": 0-2,
        "hiring": 0-2,
        "location": 0-2
      },
      "confidence": "High|Medium|Low"
    }
  },
  "stats": {
    "high_quality": X (score 8+),
    "medium_quality": Y (score 5-7),
    "low_quality": Z (score 1-4)
  }
}

Focus on scoring accuracy for Day 3 verification.
```

### Expected Output
- `gcc-healthtech-scored.json`
- Quality distribution statistics

---

## Day 2 Deliverables

| File | Description | Target |
|------|-------------|--------|
| `gcc-healthtech-deduped.json` | Deduplicated list | 3,000 companies |
| `gcc-healthtech-structured.json` | Structured data | 3,000 records |
| `gcc-healthtech-scored.json` | With quality scores | 3,000 records |

---

## Usage

```bash
# Run each pass with Claude Code
# Pass 1: Deduplication
cp gcc-healthtech-raw.json gcc-healthtech-deduped.json
# Edit with Claude Code

# Pass 2: Structure
cp gcc-healthtech-deduped.json gcc-healthtech-structured.json
# Edit with Claude Code

# Pass 3: Score
cp gcc-healthtech-structured.json gcc-healthtech-scored.json
# Edit with Claude Code
```

---

## Tips for Claude Code

1. **Batch processing**: Process 500-1000 records per prompt
2. **Validate output**: Check random samples
3. **Log decisions**: Keep track of edge cases
4. **Iterate**: Run passes multiple times if needed

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Missing emails | Use domain patterns |
| Duplicate detection | Lowercase + strip whitespace |
| Category assignment | Use company name + website clues |
| Location | Check website + LinkedIn |
| Funding stage | Search for "raised" on website |

---

## Quality Thresholds

| Score | Action |
|--------|--------|
| 8-10 | Auto-verify in Day 3 |
| 5-7 | Verify in Day 3 |
| 1-4 | Flag for manual review or discard |

---

*Day 2 prompts for Claude Code*
