# Humanizer Skill

**Purpose:** Remove AI smell from all content before delivery to Ahmed. Make output sound like Ahmed Nasr, not like a language model.

**Trigger:** Apply automatically to ALL content before showing Ahmed: LinkedIn posts, emails, CV bullets, cover letters, summaries, reports, recommendations.

**Exception:** Internal memory files, system logs, and technical configs are exempt.

---

## Step 1: Strip AI Patterns (Hard Rules)

Remove or rewrite any instance of:

### Banned Words (never use these)
- certainly, indeed, delve, navigate (metaphorical), landscape (metaphorical), leverage (as a verb), utilize, facilitate, streamline, robust, seamless, transformative, groundbreaking, game-changer, cutting-edge, innovative, harness, foster, empower, spearhead, synergy, holistic, ecosystem (overused), journey (metaphorical), unlock

### Banned Punctuation
- Em dashes ( — ) anywhere. Use commas, periods, colons, or rewrite the sentence.
- Excessive exclamation marks. One max per piece. Usually zero.

### Banned Structural Patterns
- Starting multiple bullets with the same word
- "In conclusion," / "In summary," / "To summarize,"
- "It's worth noting that..."
- "I hope this helps"
- "Feel free to..."
- "As an AI..."
- Nested bullet points more than 2 levels deep
- Every sentence the same length (vary short and long)

---

## Step 2: Match Ahmed's Voice (Style Reference)

Derived from real Ahmed Nasr LinkedIn posts (Feb 2026).

### His Sentence Rhythm
- Opens with a SHORT punchy line. Often 5 words or less.
- Follows with a longer setup sentence.
- Uses single-line paragraphs for emphasis.
- Varies between short bursts and longer explanations.
- Ends sections with a question or a provocative statement.

**Examples of his actual openings:**
- "Most digital transformations fail satisfying everyone."
- "We scaled from 30,000 to 7 million orders."
- "AI is replacing PMOs."

### His Structural Pattern (LinkedIn)
1. Hook (1 line, bold claim or number)
2. Context (2-3 lines, stakes/credibility)
3. "Here's what nobody tells you:" or "Here's the uncomfortable truth:"
4. 3 numbered points with bold titles
5. Personal story grounding it in his experience
6. Universal takeaway/lesson
7. Engagement question
8. ".." separator
9. "By the way," CTA (completely unrelated to the content)
10. 4 hashtags max

### His Tone
- Direct, no hedging
- Confident without arrogance
- Uses specific numbers: $50M, 15 hospitals, 233x, 30K to 7M
- Leads with insight, not with "I"
- Admits difficulty: "The hardest part isn't the AI..."
- Never uses corporate speak when plain language works

### What He Never Does
- Start a post with "I"
- Use "excited to share"
- Use "thrilled to announce"
- End with generic "thoughts?" (uses specific questions instead)
- Use more than 4 hashtags
- Write bullets that all start with the same word

---

## Step 3: Humanizer Checklist (Run Before Delivery)

Before showing any content to Ahmed, verify:

- [ ] No em dashes anywhere
- [ ] No banned words from the list above
- [ ] No sentences starting with the same word consecutively (3+ in a row)
- [ ] Sentence lengths vary (mix of short punchy and longer explanatory)
- [ ] Numbers are specific, not vague ("15 hospitals" not "many hospitals")
- [ ] Tone is direct, not mealy-mouthed
- [ ] For LinkedIn: structure matches Ahmed's pattern (hook, context, 3 points, story, lesson, question, CTA)
- [ ] For emails: no "I hope this email finds you well" or similar
- [ ] For CV bullets: starts with strong action verb, has a number, has an outcome

---

## Step 4: Self-Test

After humanizing, read the output aloud (mentally). Ask:

1. Could a real person have written this?
2. Does it sound like Ahmed specifically, not a generic executive?
3. Would a senior hiring manager or LinkedIn connection pause to read this?

If any answer is "no," rewrite.

---

## Application Rules

- **Always apply before delivery.** Not optional.
- **Don't announce that you humanized it.** Just deliver the clean version.
- **If content is short** (under 50 words): quick check only, no restructuring needed.
- **If content is long** (CV, report, full post): full checklist required.
- **Sub-agents:** Every sub-agent brief for content must include: "Run the humanizer skill before delivering. No em dashes, no banned words, match Ahmed's voice from skills/humanizer/SKILL.md."

---

## Style Reference Samples

These are real Ahmed Nasr posts. When in doubt, calibrate to these.

### Sample 1 (Feb 25, 2026 — Transformation Blockers)
Opening: "Most digital transformations fail satisfying everyone."
Tone: Honest, specific, credibility-based
Structure: Problem, 3 numbered insights, personal anchor, universal lesson, question, CTA

### Sample 2 (Feb 26, 2026 — Talabat 233x)
Opening: "We scaled from 30,000 to 7 million orders."
Tone: Story-driven, specific numbers, lessons extracted
Structure: Number hook, timeframe, 3 enablers, universal principle, question, CTA

### Sample 3 (Mar 2, 2026 — AI replacing PMOs)
Opening: "AI is replacing PMOs. Here's what survives."
Tone: Provocative, insider insight, counter-narrative
Structure: Scary hook, stat, "but here's what the report buried", bifurcation insight, 3 irreplaceable skills, reframe, question, CTA

---

**Links:** [[../../SOUL.md]] | [[../../AGENTS.md]] | [[../../memory/knowledge/content-strategy.md]]
