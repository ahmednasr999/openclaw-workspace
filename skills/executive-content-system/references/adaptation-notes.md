# Adaptation Notes - charlie947/social-media-skills

Repo audited: `https://github.com/charlie947/social-media-skills`
Commit audited: `06f64c8`

## What to adapt

- Voice source of truth: general profile plus voice profile, read by every content workflow.
- Content matrix: pair pillars with proven formats to create specific post ideas.
- Post writer: plan angle before drafting, then write in voice.
- Post scorer: compare drafts to actual performance patterns when data exists.
- Visual routing: choose HTML/card vs infographic/carousel based on content structure.
- Approval gate: approve brief before generating carousel/infographic assets.
- Analytics dashboard concept: turn exports/performance files into strategic recommendations.

## What to reject

- Charlie-specific persona, examples, humour, and pinned-comment logic.
- Creator-bro hooks and clickbait as default.
- Generic motivational quote posts unless Ahmed explicitly wants that format.
- Claude/Cowork-specific tool assumptions like AskUserQuestion.
- Claude for Chrome dependency. In OpenClaw, prefer local files, Camoufox, direct APIs, or existing CMO scripts.
- Apify/Gemini dependency unless Ahmed approves credentials/cost/path.

## Ahmed-specific adaptation

Ahmed's content system should reinforce:
- GCC digital transformation leadership
- healthcare transformation credibility
- PMO/governance/execution excellence
- AI automation as operating-model change
- readiness for VP/C-suite roles

Default tone:
- executive
- practical
- specific
- calm authority
- no hype
- no em dashes

## Integration targets

Existing CMO files:
- `/root/.openclaw/workspace-cmo/content-strategy.md`
- `/root/.openclaw/workspace-cmo/references/content-performance.json`
- `/root/.openclaw/workspace-cmo/scripts/generate-premium-content-card.py`
- `/root/.openclaw/workspace/skills/content-claw/SKILL.md`
