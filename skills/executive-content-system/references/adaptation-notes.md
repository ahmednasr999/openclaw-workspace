# Adaptation Notes - charlie947/social-media-skills

Repo audited: `https://github.com/charlie947/social-media-skills`
Commit audited: `94f72ea` (2026-05-20)

## 2026-05-23 refresh

Latest main delta reviewed:
- `content-matrix` now branches output by surface: interactive table on chat surfaces, saved markdown plus inline table in code/file-system surfaces, plain markdown fallback elsewhere.
- This is worth adapting because Ahmed's content planning needs readable topic grids, not fenced monospace tables.

Open watch item:
- PR #4, `feat: add x-signal-research skill`, adds focused X/Twitter signal mining. Do not import until merged and reviewed. If useful later, adapt the evidence schema and query recipes into the CMO research lane without adding Hermes/third-party write actions by default.

## What to adapt

- Voice source of truth: general profile plus voice profile, read by every content workflow.
- Content matrix: pair pillars with proven formats to create specific post ideas.
- Content matrix output: make the grid readable for the current surface, and save it as an artifact when working in a file-system surface.
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
- Current default visual gates in `/root/.openclaw/workspace/skills/content-claw/SKILL.md`; `/root/.openclaw/workspace-cmo/scripts/generate-premium-content-card.py` is legacy dark-card tooling only when Ahmed explicitly requests that direction.
- `/root/.openclaw/workspace/skills/content-claw/SKILL.md`
