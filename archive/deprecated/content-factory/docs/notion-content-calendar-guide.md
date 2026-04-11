# Notion Content Calendar — How to Create a Post

*Source of truth for consistent post structure in the content calendar database.*

---

## Required Properties (Fill These)

| Property | Type | What to Enter | Example |
|----------|------|---------------|---------|
| **Title** | Title | Short hook (max 50 chars, no quotes) | `The room went quiet when I said it` |
| **Planned Date** | Date | The date for posting | `2026-04-12` |
| **Status** | Select | One of: `Drafted` → `Scheduled` → `Published` / `Posted` | `Drafted` |
| **Topic** | Select | Match one existing topic, don't create new ones | `Leadership`, `AI`, `GCC`, `PMO`, `Strategy`, `Digital Transformation`, `Healthcare`, `HealthTech`, `FinTech`, `Operation Excellence`, `Leadership` |
| **Hook** | Rich Text | The first line of the post (opening hook) | `The room went quiet when I said it.` |
| **Draft** | Rich Text | **THE FULL POST — this is the most important field** | Full post body text (see format rules below) |
| **Day** | Select | Day of the week (auto-fills when you set date) | `Sunday` |
| **Published Post** | Relation | Leave blank until published | — |
| **Post URL** | URL | Fill after posting goes live | LinkedIn post URL |

---

## Format Rules for Draft Field

### 1. Content goes in the "Draft" property, NOT in page body
- **DO:** Paste the full post text into the Draft rich-text field
- **DO NOT:** Write content as page body blocks — the API and auto-poster read from Draft, not blocks

### 2. No Em Dashes (—)
- **DO:** Use hyphens (-) or commas instead
- ❌ "The difference wasn't the data — it was the mental model"
- ✅ "The difference wasn't the data - it was the mental model"

### 3. Bold Text
- LinkedIn doesn't render markdown (`**bold**`)
- Use Unicode Mathematical Bold characters for important phrases
- Keep bold for 2-3 key phrases max: usually a metric, a key statement, and the CTA question
- Post text uses Unicode bold (mathematical bold), but the Draft field stores regular text — the auto-poster converts "**text**" to Unicode bold before posting

### 4. Structure Pattern
Every post should follow this flow:
```
Hook (1-2 short lines to grab attention)

Context or story (2-4 paragraphs, short sentences)

Insight or turn (the "but here's the thing" moment)

Takeaway or lesson (practical, not theoretical)

**CTA question** (bold, drives engagement)

#Hashtags (3-5 relevant tags)
```

### 5. CTA Question
- Always end with a question to drive engagement
- Bold the CTA question in the Draft field
- Must relate to the post topic, not generic

### 6. Hashtags
- 3-5 max, relevant to topic
- CamelCase: `#HealthcareAI` not `#healthcareai`
- Standard tags used: `#GCC`, `#DigitalTransformation`, `#Leadership`, `#AI`, `#PMO`, `#HealthcareAI`, `#Strategy`

### 7. Paragraph Length
- Short paragraphs, 1-3 lines max
- Blank line between each paragraph
- No long blocks of text

---

## Quick Checklist Before Marking "Drafted"

- [ ] Draft field has the full post text
- [ ] NO em dashes (—) anywhere — only hyphens (-)
- [ ] Hook field has the opening line
- [ ] Topic is assigned (matching existing topic list)
- [ ] Planned Date is set
- [ ] CTA question at the end
- [ ] 3-5 hashtags

---

## What NOT to Do

- ❌ Write content in the page body (blocks) instead of the Draft property
- ❌ Use em dashes (—)
- ❌ Leave Draft field empty
- ❌ Create new Topic values without checking existing ones first
- ❌ Skip the CTA question
- ❌ Post text-only without checking the auto-poster setup first

---

## Workflow Status Definitions

| Status | Meaning |
|--------|---------|
| **Ideas** | Raw inspiration, article links, concepts — not a full draft yet |
| **Drafted** | Full post written in Draft field, ready for review |
| **Scheduled** | Reviewed, approved, locked in for a specific date |
| **Posted** / **Published** | Already went live on LinkedIn |
