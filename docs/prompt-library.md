# Prompt Engineering Library
## Best practices for Claude Opus 4.6 and other models

---

## Key Discoveries (from gist #16)

### ❌ DON'T Use
- ALL-CAPS urgency markers: CRITICAL, MUST, NEVER, ALWAYS
  → These cause over-triggering in newer models
  
- "If in doubt, use this tool"
  → Causes tools to trigger too often

- Showing anti-patterns or bad examples
  → Model sometimes focuses on and replicates anti-patterns

### ✅ DO Use
- Explain WHY a rule exists, not just WHAT
  → Model generalizes better from explanations

- Show examples of desired behavior only
  → Model learns what to do, not what not to do

- Match prompt formatting to desired output
  → If you want JSON, ask for JSON

---

## Prompt Templates

### CV Creation Prompt
```
You are creating a tailored CV for a job application.

Job Description:
{jd_text}

Master CV Data:
{master_cv}

Rules:
1. Mirror exact keywords from JD (not synonyms)
2. ATS-compliant: single column, no tables
3. AVR bullets: Action + Value + Result
4. Filename: "Ahmed Nasr - {Title} - {Company}.pdf"

Create a tailored CV that:
- Matches job requirements exactly
- Uses ATS-friendly formatting
- Highlights relevant achievements
```

### Daily Briefing Prompt
```
Generate a morning briefing with:

1. Today's calendar (with CRM context for each attendee)
2. Urgent emails from last 48 hours
3. Pending follow-ups
4. Job pipeline status
5. Stale relationships to re-engage

Format: Markdown with emojis for readability
Tone: Professional but concise
```

### Meeting Notes Prompt
```
Extract from this meeting transcript:

{transcript}

Return:
1. Key decisions made
2. Action items with owners
3. Questions raised
4. Next steps

Format:
## Decisions
- ...

## Action Items
- [ ] Owner: Task

## Questions
- ...

## Next Steps
- ...
```

### Email Response Prompt
```
Draft a response to this email:

From: {sender_name}
Subject: {subject}
Body:
{email_body}

Context from CRM:
- Relationship: {relationship}
- Last contact: {last_contact}
- Company: {company}

Write a response that:
- Matches my tone (professional, direct)
- Addresses the main point
- Keeps it concise
- Includes appropriate CTA
```

### Knowledge Base Query Prompt
```
Based on my knowledge base, answer:

{user_question}

Sources available:
{source_list}

Provide answer with:
1. Direct response
2. Source attribution
3. Relevant links
4. Confidence level (High/Medium/Low)
```

---

## Model-Specific Notes

### Claude Opus 4.6
- Responds well to explanations
- Good at following formatting instructions
- Best for: CV creation, complex analysis

### Claude Sonnet 4.6  
- Faster, good for routine tasks
- Best for: Daily briefings, simple queries

### MiniMax M2.1
- Free tier, good for simple tasks
- Best for: Quick lookups, status checks

### Kimi K2.5
- Good at reasoning
- Best for: Research, comparisons

---

## Anti-Patterns to Avoid

| Bad Pattern | Why | Fix |
|------------|-----|-----|
| "CRITICAL: You MUST..." | Over-triggering | Calm, specific instructions |
| "Don't do X" | Model may do X | "Do Y instead" |
| "If unsure, ask" | Too many questions | "Make reasonable assumption" |
| Long lists of rules | Hard to follow | Few principles + examples |
| Vague constraints | Unpredictable | Specific, measurable goals |

---

## Quick Reference

```
For CVs → Use AVR format, ATS keywords
For emails → Brief, action-oriented
For meetings → Extract decisions + actions
For knowledge → Source + confidence
For code → Task + constraints + examples
```
