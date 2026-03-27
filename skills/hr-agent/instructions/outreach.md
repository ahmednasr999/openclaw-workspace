# Recruiter Outreach — instructions/outreach.md

## Tracking (Ontology Graph)

All recruiter interactions are tracked as **Person** entities in the ontology graph.

```bash
# Add/update recruiter contact
python3 skills/ontology/scripts/ontology.py create --type Person --props '{
  "name": "...",
  "company": "...",
  "relationship": "recruiter",
  "last_contacted": "YYYY-MM-DD",
  "email": "...",
  "linkedin_url": "...",
  "notes": "..."
}'

# Query active recruiter relationships
python3 skills/ontology/scripts/ontology.py query --type Person \
  --where '{"relationship": "recruiter"}'
```

### Required Fields per Person Entity

| Field | Type | Notes |
|---|---|---|
| `name` | string | Full name |
| `company` | string | Recruiter's firm or employer |
| `relationship` | string | `recruiter` / `hiring_manager` / `network` |
| `last_contacted` | date | Most recent outreach |
| `email` | string | If known |
| `linkedin_url` | string | Profile URL |
| `response_status` | string | `pending` / `positive` / `negative` / `ghosted` |
| `notes` | string | Context, open roles, follow-up actions |

---

## Outreach Tone & Style

**Principles:**
- Professional, direct, and value-focused
- Lead with Ahmed's unique value proposition (20+ years operational + AI automation)
- Never beg, never over-explain, never send walls of text
- One clear ask per message

**Message structure:**
1. **Hook** (1 sentence): Why reaching out to THIS recruiter specifically
2. **Value** (2-3 sentences): Ahmed's positioning, current role, target next move
3. **Ask** (1 sentence): Specific and easy to action (quick call, share open roles, intro)
4. **Signature**: Ahmed Nasr | LinkedIn URL | Phone (if appropriate)

---

## Outreach Templates Reference

### Cold LinkedIn Message (≤300 chars for InMail preview)
```
Hi [Name], I'm Ahmed Nasr — PMO executive with 20+ years in digital transformation & healthcare ops across GCC.
Actively exploring VP/C-suite opportunities. Would love to stay on your radar for relevant mandates.
```

### Cold Email Subject Lines (A/B test)
- `Senior executive open to GCC opportunities — Ahmed Nasr`
- `VP/C-suite candidate | Healthcare & Digital Transformation | GCC`
- `Introduction: Ahmed Nasr — Available for Executive Mandates`

---

## Follow-Up Rules

| Scenario | Timing | Action |
|---|---|---|
| No response to first outreach | +7 days | One follow-up, shorter than original |
| No response to follow-up | +14 days | Final nudge or archive |
| Positive response | Same day | Loop in CEO, schedule call |
| Negative / not fit | Immediately | Thank, keep door open, update ontology |

---

## CEO Loop (Mandatory)

**Loop in CEO when:**
- Recruiter responds positively (expresses interest, wants to meet)
- Hiring manager direct contact is established
- An offer or informal offer signal is received

**How to loop in CEO:**
```python
# Via sessions_send to main agent session
sessions_send(
    target="agent:main:telegram:direct:866838380",
    message="[HR Agent] Recruiter update: [Name] at [Company] responded positively. Details: ..."
)
```

---

## Weekly Outreach Cadence

- **Target:** 5+ new outreach messages per week
- **Track:** All messages in ontology graph with `last_contacted` date
- **Review:** Sunday — check for responses needing follow-up
