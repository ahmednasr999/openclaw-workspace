# Interview Preparation — instructions/interviews.md

## Alert Protocol (Non-Negotiable)

**When an interview invite arrives:**
1. **IMMEDIATELY** alert CEO via sessions_send (before any other action)
2. Acknowledge to Ahmed in topic 9
3. Begin prep workflow within the same session

```python
# CEO alert template
sessions_send(
    target="agent:main:telegram:direct:866838380",
    message="🚨 [HR Agent] Interview invite received!\n\nRole: {title}\nCompany: {company}\nDate: {date/time}\nFormat: {phone/video/in-person}\n\nStarting prep workflow now."
)
```

---

## Interview Design Methodology

**Read `skills/interview-designer/SKILL.md` before preparing for any interview.**
It provides evidence-based methodology combining:
- Geoff Smart's Topgrading (structured behavioral deep-dives)
- Lou Adler's performance-based hiring (success profile matching)
- Daniel Kahneman's bias control (structured scoring, anchoring prevention)

Use it to prepare Ahmed's STAR stories with forensic precision and anticipate interviewer methodology.

---

## Prep Workflow (Execute in Order)

### 1. Company Research

**Tools:** Use `web_search` (Exa) for all research. Camofox browser for LinkedIn/Glassdoor profiles.

- Business model, revenue, key clients
- Recent news (last 90 days): acquisitions, leadership changes, launches, challenges
- Mission, values, culture signals (LinkedIn, Glassdoor reviews)
- Key competitors and market position
- GCC presence: offices, headcount, growth trajectory

### 2. Role Analysis
- Deconstruct JD: must-have vs nice-to-have
- Map requirements to Ahmed's master-cv-data
- Identify likely interview focus areas (gaps, strengths to emphasize)
- Research typical interview structure for this company/role level

### 3. Interviewer Research
- LinkedIn profile: background, tenure, posts, shared connections
- Any public content (articles, talks, posts) — align language where authentic
- Their likely priorities based on their role in the hiring process

### 4. STAR Method Stories (prepare 3 minimum)

For each story, structure:
- **Situation:** Context and stakes
- **Task:** What Ahmed was responsible for
- **Action:** Specific actions Ahmed took (quantified)
- **Result:** Outcome with numbers (%, $, time saved, headcount)

**Target story categories:**
1. Digital transformation at scale (process change, adoption, ROI)
2. Crisis leadership or turnaround situation
3. Cross-functional stakeholder alignment at C-suite level

Pull stories from: `/root/.openclaw/workspace/memory/master-cv-data.md`

### 5. Strategic Questions to Ask (prepare 5+)

Questions Ahmed should ask (signals executive thinking):
1. "What does success look like in this role at 90 days, 6 months, and 12 months?"
2. "What are the biggest transformation priorities you're tackling this year?"
3. "How does this role interact with the Board / key external stakeholders?"
4. "What's the biggest challenge the previous person in this role faced?"
5. "What's your timeline for this decision and what are the next steps?"

Customize based on company research.

### 6. Salary Market Rate Research

**Tools:** Use `web_search` (Exa) with queries like "{title} salary {country} {year}". Scrape Glassdoor via Camofox if needed.

- Research comparable roles in target geography (GCC, specific country)
- Sources: Glassdoor (Camofox scrape), LinkedIn Salary, Bayt Salary Index, web_search for recruiter salary guides
- Ahmed's target range: confirm from USER.md / MEMORY.md
- Prepare BATNA (best alternative) position before negotiation
- **Never hallucinate salary numbers.** If no data found, say "no reliable data" and provide the search URLs for Ahmed to check.

---

## Prep Package Delivery

Send to topic 9 as structured brief:
```
📋 Interview Prep: {Title} @ {Company}
📅 Date: {date/time}

🏢 Company snapshot (5 bullets)
👤 Interviewer intel
🎯 3 STAR stories ready
❓ 5 strategic questions
💰 Salary: {range} for this role/geo
📝 Next: send thank-you within 24h
```

---

## Post-Interview Protocol

### Thank-You Follow-Up (within 24 hours)
- Draft thank-you email for Ahmed's review
- Reference a specific moment from the conversation (shows genuine engagement)
- Reiterate one key value point
- Keep to 3-4 sentences

### Debrief Capture
- What went well
- What was unexpected
- Next steps communicated by interviewer
- Update Notion pipeline status to `Interview` (if not already)
- Set follow-up reminder if interviewer gave a decision timeline
