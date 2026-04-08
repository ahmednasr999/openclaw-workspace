# CV JSON Schema — Required Field Names
# Source: generate_resume_pdf.py (verified 2026-02-27)
# USE THESE EXACT FIELD NAMES — no aliases, no variations

## Top-level structure
```json
{
  "format": "chronological",
  "contact": {
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "linkedin": ""
  },
  "summary": "",
  "skills": [
    {
      "category": "Category Name",
      "items": ["skill1", "skill2"]
    }
  ],
  "experience": [
    {
      "title": "",
      "company": "",
      "location": "",
      "dates": "Mon YYYY - Mon YYYY",
      "bullets": ["bullet 1", "bullet 2"]
    }
  ],
  "education": [
    {
      "degree": "",
      "major": "",
      "school": "",
      "location": "",
      "date": "YYYY",
      "details": []
    }
  ],
  "certifications": [
    {
      "name": "",
      "issuer": "",
      "date": ""
    }
  ]
}
```

## Critical rules
- experience: use `dates` (NOT start_date/end_date)
- education: use `school` (NOT institution), `date` (NOT graduation_year)
- skills: must be array of objects with `category` + `items` (NOT flat string array)
- certifications: must be array of objects with `name`/`issuer`/`date` (NOT flat string array)
