# ENGAGE Layer — Engagement Velocity Protocol

## The 60-Minute Window

LinkedIn's algorithm uses first-hour engagement as its primary quality signal. This isn't optional - it's physics.

## Daily Engagement Sequence

### Phase 1: Pre-Post Priming (9:00 AM Cairo - BEFORE our post)

**Why:** Commenting on 3-5 posts before publishing primes the algorithm. LinkedIn's feed logic favors accounts that are active participants, not just broadcasters.

**Steps:**
1. Run Comment Radar (existing skill: `skills/linkedin-comment-radar/`)
2. Filter: last 24 hours, GCC geography, PQS >= 40
3. Select top 5 posts from target accounts (ideal: GCC executives, transformation leaders, healthcare/fintech decision-makers)
4. Draft 3-5 substantive comments following comment rules below
5. Present to Ahmed for approval
6. Ahmed posts comments manually (bot never posts comments)

### Phase 2: Post Goes Live (9:30 AM Cairo)

- Auto-poster publishes from Notion (existing `linkedin-auto-poster.py`)
- Telegram alert fires: "Post live. 60-min engagement window open. [post topic]"

### Phase 3: Active Engagement Window (9:30-10:30 AM Cairo)

- Monitor incoming comments on our post
- Draft reply suggestions for Ahmed (never auto-reply)
- Prioritize: questions first, then substantive comments, then likes
- Reply style: conversational, adds new value, asks a follow-up question when natural

### Phase 4: Window Closing (10:30 AM Cairo)

- Telegram alert: "Engagement window closing. Comments received: X."
- Summary of engagement quality (substantive vs. emoji-only ratio)

## Comment Style Rules (Hard Lint)

These apply to both pre-post priming comments AND replies to comments on our posts.

**Structure:** 2-4 lines max. No walls of text.

**Opening:** Start with insight, NEVER with:
- "Great post!"
- "Thanks for sharing!"  
- "Love this!"
- "So true!"
- Any generic praise opener

**Body:** Include ONE concrete anchor:
- A governance framework you've used
- A metric from your experience
- A specific challenge you faced
- A tool or approach that worked

**Ending:** ~40% of comments should include one sharp question. Not "what do you think?" but "How did you handle the adoption curve in the first 90 days?"

**Tone:** Executive peer, not fan. Direct and practical.

**Hard rules:**
- No em dashes
- No self-promotion (never mention your availability, services, or job search)
- No linking to your own content
- 100% value. Zero pitch. The profile does the selling.

**The Reddit Rule (adapted):** 90% value-add, 10% professional identity showing through naturally. If Ahmed's comment could have been written by anyone, it's not good enough. His unique experience (multi-country PMO, regulated environments, $50M programs) should show in the specificity of his response.

## Target Accounts

Prioritize engagement with:
1. GCC-based C-suite and VPs (healthcare, fintech, government)
2. Transformation leaders and consultants in MENA
3. PMO practitioners managing large programs
4. Recruiters and headhunters active in GCC executive roles
5. Industry voices who post about Vision 2030, digital transformation, AI adoption

## Metrics to Track

- Pre-post comments completed: target 3-5/day
- Reply time on our posts: target <15 min for first 3 comments
- Comment quality ratio (substantive vs. emoji): target 40%+ substantive
- Connection requests from engagement: track weekly
