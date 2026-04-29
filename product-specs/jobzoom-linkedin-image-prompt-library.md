# JobZoom + LinkedIn Image Prompt Library

Purpose: reusable GPT-Image 2 style prompts for JobZoom product assets and Ahmed/NASR executive LinkedIn content.

Source inspiration: structural patterns extracted from `EvoLinkAI/awesome-gpt-image-2-prompts`, adapted for premium GCC executive/B2B use. These are not copied prompts. They reuse the useful anatomy: subject, layout, lighting, typography, palette, aspect ratio, placeholders, and explicit constraints.

## Global Visual Direction

Use this as the default style layer unless a prompt overrides it.

```text
Premium executive B2B visual system, dark navy / charcoal background, subtle GCC-inspired geometric patterning, restrained gold/cyan accents, glassmorphism panels, clean sans-serif typography, high contrast, sharp hierarchy, realistic depth, cinematic soft lighting, polished enterprise SaaS aesthetic, no cartoon style, no childish colors, no clutter.
```

## Global Negative Prompt

```text
Avoid: cartoon, anime, childish illustration, random fake logos, distorted text, unreadable small text, messy typography, low-resolution artifacts, generic stock-photo look, exaggerated sci-fi, cheap gradients, overdecorated background, excessive icons, unrealistic hands, watermark, QR code, misspelled words.
```

## Template Variables

Use these consistently:

- `{headline}`
- `{subheadline}`
- `{country}`
- `{metric_1}`
- `{metric_2}`
- `{metric_3}`
- `{role_title}`
- `{company}`
- `{score}`
- `{cta}`
- `{brand_name}` default: `JobZoom`
- `{accent_color}` default: `cyan and muted gold`
- `{audience}` default: `senior GCC professionals`

---

# A. JobZoom Product / SaaS Assets

## 1. JobZoom Landing Page Hero

Use for website hero image, investor deck cover, or launch announcement.

```text
Create a premium SaaS landing page hero visual for {brand_name}, a private AI job-search operator for senior GCC professionals.

Composition:
- 16:9 horizontal hero image.
- Dark navy / charcoal background with subtle GCC geometric pattern.
- Center-left: large clean headline area reading: "Upload your CV once. Wake up to ready-to-apply GCC opportunities."
- Below headline: smaller subheadline reading: "Daily job matching, ATS-tailored CVs, and executive opportunity reports."
- Right side: layered glassmorphism product dashboard mockup showing a daily GCC opportunity report.
- Dashboard cards should include: "Top Matches", "ATS Ready", "Saudi", "UAE", "Qatar", and "Tailored CV ZIP".
- Add a subtle map outline of GCC countries behind the dashboard, very low opacity.

Style:
Premium executive B2B, enterprise SaaS, cinematic lighting, crisp typography, restrained gold and cyan accents, polished consulting-grade finish.

Constraints:
Text must be short, readable, correctly spelled, and not crowded. No fake company logos. No cartoon/anime style. No watermark.
```

Negative prompt:

```text
Avoid messy UI, tiny unreadable text, random app logos, exaggerated neon cyberpunk, people smiling at laptops, generic job board visuals, cartoon icons.
```

## 2. Daily Report Mockup

Use to show the core customer deliverable.

```text
Create a realistic premium mockup of a PDF report titled "JobZoom Daily Opportunity Brief".

Composition:
- Aspect ratio 4:5 vertical.
- A crisp A4 report page floating over a dark executive desk surface.
- The report should show these readable sections:
  1. "Today’s Best Matches"
  2. "Recommended Applications"
  3. "GCC Market Signals"
  4. "Tailored CVs Prepared"
- Include 3 clean job cards with placeholders: {role_title}, {company}, {country}, {score}% fit.
- Add small visual indicators for Saudi Arabia, UAE, Qatar, Kuwait, Bahrain, Oman.
- Bottom right: subtle {brand_name} wordmark.

Style:
Premium management-consulting report, clean grid, dark header, white paper, muted gold and cyan accents, realistic soft shadows, high readability.

Constraints:
Do not show internal system telemetry like scraping status, pass1/pass2, warnings, model health, or debug labels. No fake brands other than placeholders.
```

## 3. Tailored CV ZIP Visual

Use to explain “we send CVs, not just alerts.”

```text
Create a premium product visual showing JobZoom preparing tailored ATS-friendly CVs.

Composition:
- Aspect ratio 1:1 square.
- Dark executive background.
- Center: a sleek ZIP folder icon labeled "Tailored CVs".
- Around it: five clean document cards titled:
  - "CV - Program Director"
  - "CV - PMO Head"
  - "CV - Digital Transformation"
  - "CV - Operations Director"
  - "CV - Healthcare IT"
- Add small match-score badges such as "92%", "88%", "85%".
- Include a subtle arrow from "Master CV" to "Tailored CV Pack".

Style:
Enterprise SaaS, premium dark UI, glass cards, clean typography, restrained gold/cyan accents.

Constraints:
ATS-friendly should feel serious and trustworthy, not flashy. Avoid showing personal data, names, phone numbers, or real company logos.
```

## 4. GCC Opportunity Radar

Use for product storytelling or LinkedIn launch post.

```text
Create a premium visual metaphor for a daily GCC job opportunity radar.

Composition:
- Aspect ratio 16:9.
- Dark map of GCC countries with subtle glowing nodes over Saudi Arabia, UAE, Qatar, Kuwait, Bahrain, and Oman.
- Center: elegant radar sweep ring labeled "Daily GCC Scan".
- Left side: stacked cards showing "150 searches", "Top 5 roles", "ATS CVs ready".
- Right side: ranked opportunity cards with fit scores.

Style:
Executive intelligence dashboard, not military, not sci-fi overload. Clean, calm, trustworthy, premium.

Constraints:
No fake logos, no messy map labels, no surveillance feel, no warning/error labels.
```

## 5. Paid Beta Announcement Image

Use when inviting first 10 users.

```text
Create a premium LinkedIn announcement image for a controlled beta of {brand_name}.

Text:
Headline: "Private Beta: GCC Job Search, Done Daily"
Subheadline: "For senior professionals who want curated roles and tailored CVs every morning."
Badge: "10 paid beta seats"
CTA: "DM to join the waitlist"

Composition:
- Aspect ratio 4:5 LinkedIn post.
- Dark premium background, subtle GCC pattern.
- Large headline at top, short subheadline below.
- Middle: product mockup showing a daily report + tailored CV ZIP.
- Bottom: small trust line: "Saudi Arabia | UAE | Qatar | Kuwait | Bahrain | Oman".

Style:
Executive, scarce, premium, credible, not hypey.

Constraints:
Text must be readable and correctly spelled. No exaggerated claims like guaranteed jobs. No fake testimonials.
```

## 6. Product Explainer Infographic

Use to explain the 4-step workflow.

```text
Create a clean premium infographic explaining how {brand_name} works.

Aspect ratio: 4:5 vertical LinkedIn format.

Title: "How JobZoom Works"

Four-step layout:
1. "Upload CV"
   Small icon: document upload.
2. "Build Master Profile"
   Small icon: structured profile / skills graph.
3. "Scan GCC Jobs Daily"
   Small icon: GCC map radar.
4. "Receive Report + Tailored CVs"
   Small icon: PDF report and ZIP folder.

Visual style:
Dark executive background, glass cards, crisp white typography, cyan/gold accents, clean numbered flow, subtle connecting line.

Constraints:
Keep text minimal and readable. Do not include technical backend terms. Do not imply auto-application.
```

## 7. Job Match Detail Card

Use for sample report/job-card marketing.

```text
Create a premium UI card for a JobZoom job match detail.

Aspect ratio: 1:1 square.

Card content:
- Header: "Recommended Match"
- Role: "{role_title}"
- Country: "{country}"
- Fit Score: "{score}%"
- Why it fits:
  - "PMO leadership"
  - "Digital transformation"
  - "Healthcare / enterprise scale"
- Action: "Tailored CV prepared"

Composition:
A single large glassmorphism card floating on a dark background with subtle GCC map lines. Use a premium score ring and clean bullet list.

Constraints:
No real company logos. Avoid clutter. Text must remain large and readable.
```

---

# B. LinkedIn Executive Content Cards

## 8. Executive Insight Card

Use for Ahmed’s thought leadership posts.

```text
Create a premium LinkedIn executive insight card.

Aspect ratio: 4:5 vertical.

Text:
Headline: "{headline}"
Supporting line: "{subheadline}"
Footer: "Ahmed Nasr | PMO • AI Automation • Digital Transformation"

Composition:
- Large headline in top half with strong hierarchy.
- Abstract executive visual in lower half: glass boardroom table, subtle dashboard reflections, GCC skyline silhouette, or transformation roadmap lines.
- Dark navy/charcoal background, restrained gold/cyan accents.

Style:
Premium C-suite consulting aesthetic, serious, calm, high trust, no hype.

Constraints:
Do not use stock-photo people faces. Do not add fake logos. Keep typography clean and readable.
```

## 9. Transformation Framework Card

Use for PMO/digital transformation frameworks.

```text
Create a premium framework infographic for LinkedIn.

Aspect ratio: 4:5 vertical.

Title: "{headline}"
Subtitle: "{subheadline}"

Framework layout:
- 3 pillars or 4 quadrants, depending on the headline.
- Use clean cards with short labels:
  1. "Strategy"
  2. "Execution"
  3. "Adoption"
  4. "Measurement"
- Add thin connecting lines and subtle progress indicators.

Style:
Executive PMO dashboard, premium consulting slide, dark background, gold/cyan accents, crisp grid, no decorative clutter.

Constraints:
Readable text only. No tiny labels. No cheesy icons. No public-company logos.
```

## 10. “Hidden Risk” Warning Card

Use for posts about execution risk, AI risk, PMO failure, job-search mistakes.

```text
Create a premium LinkedIn warning/insight card.

Aspect ratio: 4:5 vertical.

Text:
Headline: "{headline}"
Subheadline: "{subheadline}"
Small label: "Execution Risk"

Composition:
- Dark executive background.
- Center: one elegant warning signal integrated into a dashboard card, not a hazard sign.
- Use amber/gold accent for risk, cyan for data lines.
- Include faint background elements: roadmap, KPI tiles, decision gates.

Style:
Serious boardroom-grade risk intelligence, premium, calm, credible.

Constraints:
No alarmist red explosion visuals. No cyber breach cliché. No fake data that looks too specific.
```

## 11. Before / After Executive Slide

Use for improvement narratives.

```text
Create a premium before/after LinkedIn visual.

Aspect ratio: 4:5 vertical.

Title: "{headline}"

Split layout:
Left panel: "Before"
- fragmented tools
- manual follow-up
- unclear priorities
- slow reporting

Right panel: "After"
- single command center
- daily execution rhythm
- clear accountability
- faster decisions

Style:
Dark executive consulting slide, clean contrast between messy left and refined right, subtle glassmorphism panels, gold/cyan highlights.

Constraints:
No clutter. Keep text large and readable. Do not use childish icons.
```

## 12. Quote / Principle Card

Use for concise executive principles.

```text
Create a premium quote card for LinkedIn.

Aspect ratio: 4:5 vertical.

Main quote:
"{headline}"

Footer:
"{subheadline}"

Visual style:
Minimal executive design, dark navy background, subtle spotlight gradient, thin gold line, faint geometric texture, elegant sans-serif typography, lots of negative space.

Constraints:
The quote must be the dominant element. Do not add extra decorative text. No stock people. No fake signatures.
```

## 13. Data Point Card

Use for metrics or single-stat posts.

```text
Create a premium data-point card for LinkedIn.

Aspect ratio: 4:5 vertical.

Main metric: "{metric_1}"
Headline: "{headline}"
Subheadline: "{subheadline}"

Composition:
- Large metric centered or upper-third.
- Supporting statement below.
- Background: subtle executive dashboard grid with faint trend lines.
- Accent color: {accent_color}.

Style:
Boardroom analytics, clean and premium, not startup-bright.

Constraints:
Do not invent extra numbers. Do not add fake charts with unreadable labels. Keep metric and text readable.
```

## 14. Carousel Cover Card

Use as first slide for LinkedIn carousel PDF.

```text
Create a premium LinkedIn carousel cover.

Aspect ratio: 4:5 vertical.

Text:
Title: "{headline}"
Subtitle: "{subheadline}"
Footer: "Swipe for the framework →"

Composition:
- Strong title hierarchy.
- Abstract executive visual: layered roadmap, transformation architecture, or AI operations command center.
- Bottom: subtle progress dots showing slide 1 of 6.

Style:
Premium consulting deck cover, dark, restrained, sharp, credible.

Constraints:
No clutter, no tiny text, no random screenshots. Make it feel like a boardroom-ready slide.
```

## 15. Carousel Framework Slide

Use for slides 2-5 of carousels.

```text
Create a premium LinkedIn carousel framework slide.

Aspect ratio: 4:5 vertical.

Slide title: "{headline}"
Slide point: "{subheadline}"

Layout:
- Top: small section label.
- Middle: one clear diagram or card stack.
- Bottom: one concise takeaway sentence.
- Include small progress dots at bottom.

Style:
Dark executive consulting slide, clean grid, restrained gold/cyan accent, crisp typography.

Constraints:
One idea per slide. No paragraph blocks. No decorative clutter.
```

---

# C. JobZoom Marketing / Sales Content

## 16. Problem Card: Job Alerts Are Not Enough

```text
Create a premium LinkedIn problem/positioning card for JobZoom.

Aspect ratio: 4:5 vertical.

Headline: "Job alerts are not enough."
Subheadline: "Senior professionals need filtered opportunities and ready-to-apply CVs."

Composition:
- Left side: cluttered generic job alert inbox, blurred and low-detail.
- Right side: clean JobZoom daily brief with top matches and tailored CV pack.
- Use a clear visual contrast without making the left side ugly.

Style:
Premium B2B, executive career intelligence, dark background, clean report mockups.

Constraints:
No real email provider UI. No fake company logos. No guaranteed-job language.
```

## 17. Pricing Value Card

```text
Create a premium pricing/value card for JobZoom.

Aspect ratio: 4:5 vertical.

Headline: "$200/month for a daily job-search operator"
Subheadline: "GCC-wide scan + ATS-tailored CVs + daily opportunity brief."

Include 3 value chips:
- "Daily GCC Scan"
- "Top Matches"
- "Tailored CV ZIP"

Composition:
Dark premium SaaS card, large price tag, clean feature chips, subtle GCC map in background.

Constraints:
No discount banners. No fake scarcity unless explicitly provided. Avoid cheap pricing-table look.
```

## 18. Trust / Boundary Card

Use to clarify “we don’t apply for you.”

```text
Create a premium trust card for JobZoom.

Aspect ratio: 4:5 vertical.

Headline: "We prepare. You apply."
Subheadline: "JobZoom finds relevant GCC roles and prepares tailored CVs, while you stay in control of every application."

Composition:
- Center: user-controlled approval flow visual.
- Left: "JobZoom prepares" with report and CV pack.
- Right: "You decide" with application button/checklist.

Style:
Trustworthy, privacy-conscious, executive SaaS, calm dark palette.

Constraints:
No auto-apply implication. No aggressive automation visuals. No fake application confirmations.
```

## 19. Weekly Market Intelligence Visual

```text
Create a premium weekly GCC market intelligence visual for JobZoom.

Aspect ratio: 16:9.

Title: "GCC Career Market Signals"

Dashboard sections:
- "Fastest-moving countries"
- "Most active role families"
- "Top hiring sectors"
- "Recommended focus this week"

Use placeholder labels only, not fake precise data:
- Saudi Arabia
- UAE
- Qatar
- PMO
- Digital Transformation
- Healthcare Technology

Style:
Executive intelligence dashboard, boardroom-ready, dark background, subtle map, clean charts.

Constraints:
Avoid fake exact numbers unless provided. No internal scraping telemetry. No warning labels.
```

## 20. Beta Waitlist Hero

```text
Create a premium waitlist hero image for JobZoom.

Aspect ratio: 16:9.

Headline: "Your GCC job search, prepared before breakfast."
Subheadline: "Daily matched roles, tailored CVs, and a clear action brief."
CTA text: "Join the beta"

Composition:
- Morning executive desk scene, laptop showing JobZoom report, coffee, subtle Gulf skyline sunrise through glass.
- Keep people out of frame or show only abstract hands-free desk setup.
- Product UI should be visible but not overloaded.

Style:
Calm premium morning routine, executive productivity, polished SaaS.

Constraints:
No generic smiling office workers. No fake logos. Text must be readable.
```

---

# D. Report / Document Visuals

## 21. BRD / Product Spec Cover

```text
Create a premium document cover for "JobZoom Business Requirements Document".

Aspect ratio: A4 vertical.

Text:
Title: "JobZoom Business Requirements Document"
Subtitle: "Daily GCC job-search automation for senior professionals"
Footer: "Prepared for product validation and AI-builder handoff"

Visual:
Dark executive cover with subtle GCC map, glassmorphism product cards, PDF report icon, tailored CV ZIP icon, thin gold/cyan accent lines.

Style:
Premium consulting document, boardroom-ready, clean typography, no clutter.

Constraints:
No fake company logos. No excessive decoration. Text must be correctly spelled.
```

## 22. Architecture Diagram Visual

```text
Create a premium system architecture diagram for JobZoom.

Aspect ratio: 16:9.

Diagram blocks:
1. "User CV Upload"
2. "Profile Extraction"
3. "Shared GCC Job Scan"
4. "Job Database"
5. "Per-User Matching"
6. "Tailored CV Generation"
7. "PDF + ZIP Delivery"
8. "Email Delivery"
9. "Admin Monitoring"

Style:
Clean enterprise architecture slide, dark background, glass blocks, thin connecting lines, cyan/gold accents, readable labels.

Constraints:
Do not include vendor logos or implementation-specific tools unless provided. No tiny text. No fake security certifications.
```

## 23. Data Privacy Visual

```text
Create a premium privacy/security visual for JobZoom.

Aspect ratio: 4:5 vertical.

Headline: "Career data must stay private."
Subheadline: "Separate user profiles, controlled delivery, and no public posting."

Composition:
- Central secure vault / profile card.
- Surrounding labels: "CV", "Job Matches", "Reports", "Tailored CVs".
- Use subtle lock iconography and clean data lines.

Style:
Executive SaaS security, calm, trustworthy, not cyberpunk.

Constraints:
No scary hacker imagery. No exaggerated claims like military-grade encryption unless true.
```

---

# E. Prompt Builder Meta-Templates

## 24. Reusable Executive Content Card Builder

Use this to generate a new image prompt from a post idea.

```text
You are creating a GPT-Image 2 prompt for an executive LinkedIn content card.

Input:
- Topic: {topic}
- Main point: {main_point}
- Audience: {audience}
- Desired tone: premium, executive, practical, credible
- Format: 4:5 vertical LinkedIn image

Create one image-generation prompt with:
1. Exact text to appear on the image.
2. Layout/composition instructions.
3. Visual style.
4. Lighting/color palette.
5. Typography guidance.
6. Negative prompt.

Constraints:
- Do not use anime/cartoon style.
- Do not create fake logos or fake statistics.
- Keep text minimal and readable.
- Make it feel like a boardroom-ready consulting visual.
- End with a concise negative prompt.

Output only the final image prompt.
```

## 25. Reusable JobZoom Product Visual Builder

Use this when creating new JobZoom product images.

```text
You are creating a GPT-Image 2 prompt for a JobZoom product marketing visual.

Input:
- Asset type: {asset_type}
- Core message: {core_message}
- Audience: senior GCC professionals
- Product promise: daily GCC job matching, ATS-tailored CVs, PDF report, ZIP delivery
- Required aspect ratio: {aspect_ratio}

Create one image-generation prompt with:
1. Subject and product context.
2. Required visible text.
3. Layout/composition.
4. UI/report/mockup details.
5. Visual style: premium executive SaaS, dark navy/charcoal, subtle GCC pattern, gold/cyan accents.
6. Constraints and negative prompt.

Rules:
- Never imply guaranteed employment.
- Never imply JobZoom applies automatically.
- Do not show internal telemetry, debug status, pass1/pass2 labels, scraping warnings, or model health.
- Do not include real company logos unless explicitly provided.
- Keep all visible text short and readable.

Output only the final image prompt.
```

---

# F. Recommended Usage Map

| Need | Use Prompt |
|---|---|
| Website hero | 1 or 20 |
| Explain product workflow | 6 |
| Show report deliverable | 2 |
| Show tailored CV pack | 3 |
| Beta launch LinkedIn post | 5 |
| Pricing post | 17 |
| Trust/no-auto-apply message | 18 |
| Weekly market report visual | 19 |
| LinkedIn thought leadership card | 8, 10, 12, 13 |
| LinkedIn carousel cover | 14 |
| LinkedIn carousel slide | 15 |
| BRD/spec cover | 21 |
| Architecture slide | 22 |
| Privacy/security slide | 23 |

# G. Quality Checklist

Before accepting an image:

- Is all visible text correctly spelled?
- Is text readable on mobile?
- Does it feel premium and executive, not generic?
- Does it avoid fake company logos and fake stats?
- Does it avoid implying guaranteed jobs or auto-apply?
- Is there one clear message, not five?
- Does the visual reinforce JobZoom’s positioning as a daily career operator?
- Would this look credible to a senior manager/director in GCC?

