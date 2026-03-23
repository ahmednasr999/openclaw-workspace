# CREATE Layer — Weekly Batch Content Creation

## Pre-Creation Checklist

Before writing a single word:

1. **Read performance data** → `references/content-performance.json`
2. **Check content mix** → `references/content-mix.md` — which types are underrepresented?
3. **Read active experiment** → `references/experiments.md` — what variable are we testing this week?
4. **Load voice rules** → `instructions/voice-and-format.md` (canonical — never deviate)
5. **Load image genres** → `instructions/image-genres.md` (match genre to post type)

## Post Construction System

### Step 1: Select Post Type

Based on content mix deficit. Five types, each with distinct structure:

**Story (target 30%)**
Specific moment → tension → resolution → transferable insight.
- Start with a scene, not a summary
- Include sensory detail (time, place, who was there)
- The lesson must be transferable to the reader's situation
- "Tuesday, 3 AM. I'm staring at a Salesforce migration about to blow up across 4 countries."

**Expertise (target 25%)**
One thing most people get wrong → the correct mental model → proof/example.
- Lead with the misconception
- Explain WHY it's wrong (not just that it is)
- Provide the correct framework with a named concept when possible
- "Most PMOs measure project completion rate. Here's why that's the wrong metric."

**Opinion (target 20%)**
State the take → acknowledge the counterargument → defend with evidence → invite conversation.
- The take must be genuinely arguable (not "communication matters")
- Acknowledge the strongest version of the opposing view
- Defend with specific evidence from your experience
- "Unpopular take: Certifications matter more in the GCC than in the US. Here's why."

**Data (target 15%)**
Lead with the surprising number → explain why it matters → give one actionable implication.
- The number must be specific and verifiable
- Connect it to the reader's world
- End with "what this means for you" not just "interesting, right?"
- "70% of digital transformations fail. But in regulated industries, it's 83%."

**Behind-the-Scenes (target 10%)**
Pull back the curtain on a process, decision, or failure.
- Show the messy middle, not the polished result
- Be vulnerable about what went wrong
- Make the reader feel like an insider
- "Here's the actual Slack message I sent when our $50M program almost derailed."

### Step 2: Engineer 3 Hook Variants

Every post gets 3 hooks. Pick the strongest.

- **Curiosity Gap:** Opens a loop the reader must close. "I almost turned down the role that taught me more than my MBA."
- **Bold Claim:** Challenges conventional wisdom. "Your PMO is probably measuring the wrong things."
- **Specific Story:** Drops into a scene. "8 countries. 15 hospitals. One governance framework. Here's what happened."

Test: Would YOU stop scrolling for this? Would a GCC CTO?

### Step 3: Draft the Post

Apply all rules from `instructions/voice-and-format.md`.

Key constraints:
- Under 1300 characters (unless Story format, max 2000)
- Short paragraphs (1-2 sentences)
- Line breaks between every paragraph
- Break at tension points to force "see more"
- End with specific engagement question
- 3-5 specific hashtags at the bottom ONLY
- No links in body
- No em dashes anywhere

### Step 4: Generate Image

Read `instructions/image-genres.md`. Match genre to post type:
- Story → Scene Card or Quote Card
- Expertise → Framework Diagram
- Opinion → Statement Card
- Data → Stat Card
- BTS → Raw/Minimal Card

### Step 5: Quality Gate

Run every item in `eval/checklist.md`. Binary pass/fail.
- If any item fails → revise and re-check (max 2 revision cycles)
- If still failing after 2 revisions → flag to Ahmed with explanation

### Step 6: Tag and Save

Each post saved to Notion with metadata:
- `post_type`: story | expertise | opinion | data | bts
- `pillar`: pmo | dt | ai | gcc | leadership
- `hook_style`: curiosity | bold | story
- `experiment_var`: whatever this week's test variable is (or "none")
- `Status`: Drafted

### Content Pillars (Rotate)

| Pillar | Theme | Keywords |
|--------|-------|----------|
| PMO | Governance, frameworks, multi-country coordination | PMO, governance, project management, PMP |
| DT | Digital transformation, change management, adoption | transformation, digital, change management |
| AI | AI in enterprise, regulated AI, practical AI adoption | AI, automation, machine learning, enterprise |
| GCC | Middle East market, Saudi Vision 2030, regional insights | GCC, Saudi, UAE, Vision 2030, MENA |
| Leadership | Executive decisions, team building, career lessons | leadership, executive, C-suite, career |

## AI Citation Optimization (2 posts/month minimum)

For expertise and data posts, check: does this post contain a **named concept or framework** that AI engines could cite?

Good: "The 3-Country Governance Model", "The Regulated Transformation Paradox"
Bad: Generic advice without a citable handle

Structure these posts as: clear claim → specific evidence → named framework → implications. This is the exact pattern ChatGPT, Claude, and Perplexity cite.

## Repurposing Candidates

After any post exceeds 5% engagement rate, flag it for repurposing:
- Text post → Carousel version (different format, same audience)
- Expertise post → Long-form LinkedIn article (SEO + AI citation value)
- Data post → Infographic image version
- Any top performer → X thread (when X is activated)
