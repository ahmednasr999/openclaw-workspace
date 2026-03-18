---
name: content-creator-prebuild
description: "Friday pre-build: generate next week's LinkedIn posts with images, hooks, and scheduling plan."
---

# Content Creator - Friday Pre-Build (Next Week Posts + Images)

Generate complete LinkedIn posts for next week with images and scheduling plan.

## Prerequisites
- Notion Content Calendar with approved topics/angles
- LinkedIn Writer skill: `skills/linkedin-writer/SKILL.md` for voice/tone
- Image generation capability
- Content pipeline: `coordination/content-calendar.json`

## Steps

### Step 1: Review approved topics
Check Content Calendar for topics in "📝 Outline" or "💡 Ideas" status.
Select 3-5 posts for next week (Mon-Fri schedule).

### Step 2: Write each post
For each post, using Ahmed's voice (reference linkedin-writer skill):
- Write the hook (first 2 lines - must stop the scroll)
- Write the body (value-driven, experience-based)
- Write the CTA (question or engagement prompt)
- Target length: 150-250 words
- End with relevant hashtags (3-5 max)

### Step 3: Generate images
For each post:
- Create a relevant image or graphic
- Ensure text is readable if included
- Save to `media/linkedin-posts/`

### Step 4: Schedule in Content Calendar
Update each post in Notion:
- Status: "✍️ Draft"
- Scheduled date
- Full post content in page body
- Image attached or linked

### Step 5: Report
"📝 Pre-build complete: [X] posts drafted for [dates]. Ready for Ahmed's review."

## Error Handling
- If fewer than 3 topics available: Generate additional angles from Content Intelligence
- If image generation fails: Flag post as "needs image" and continue

## Quality Gates
- Each post must have hook + body + CTA
- No post over 300 words
- No duplicate themes from last 2 weeks
- Images must be original, not stock-looking
- All posts must align with executive positioning

## Output Rules
- No em dashes. Hyphens only.
- Posts must sound human, not corporate AI
- Follow linkedin-writer skill voice guidelines
