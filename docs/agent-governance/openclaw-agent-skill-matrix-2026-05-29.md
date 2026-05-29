# OpenClaw Agent Skill Matrix

Date: 2026-05-29
Owner: NASR
Status: first control draft

## Purpose

Keep each agent focused, reduce model-visible noise, and prevent powerful tools from drifting into the wrong lane.

Live baseline checked on 2026-05-29: 118 skills installed, 79 model-visible, 78 command-available.

## Agent Boundaries

| Agent/Lane | Primary Job | Should Own | Should Avoid |
|---|---|---|---|
| NASR | Front-facing executive partner, decision support, orchestration | decision briefs, memory recall, lightweight research, routing | long raw research crawls, runtime repairs, public posting mechanics |
| CTO | Runtime, monitoring, recovery, infrastructure, agent/workflow engineering | gateway-runtime-safety, healthcheck, openclaw-backup, cron, node-connect, taskflow, github/gh-fix-ci | content drafting, CV tailoring, public posting |
| CMO | LinkedIn/content pipeline and premium visuals | content-claw, executive-content-system, linkedin, premium-frontend-design, Image, avoid-ai-writing | gateway changes, job scoring, credentials work |
| JobZoom/HR | Job search, ATS scoring, CV generation, job reports | executive-cv-builder, ai-pdf-builder, xlsx/spreadsheet, Job Search MCP, summarize | runtime upgrades, public content, broad crawler pilots |
| Research | Long-form research, market maps, ecosystem scans | tavily, ai-research-scraper, crawlee, scrapling, summarize, nasr-decision-brief | external side effects, posting, config changes |

## Recommended Visible Skills By Lane

### NASR Front-Facing

- `nasr-decision-brief`
- `knowledge-brain-briefing`
- `nasr-knowledge-ingestion`
- `lossless-claw`
- `summarize`
- `tavily` for current or source-sensitive research
- `reminder`
- `taskflow` only for structured follow-through

Keep NASR lean. NASR should delegate heavy crawling, build/debug work, and content production when possible.

### CTO Runtime Lane

- `gateway-runtime-safety`
- `healthcheck`
- `openclaw-backup`
- `cron-skills-index`
- `node-connect`
- `tmux`
- `github`
- `gh-fix-ci`
- `gh-address-comments`
- `taskflow`
- `sweeper-status-loop`
- `security-best-practices`
- `self-improvement`

CTO owns the installed crawler binaries: `/usr/local/bin/gitcrawl` and `/usr/local/bin/telecrawl`. `gitcrawl` is ready for read-only repo digest pilots. `telecrawl` is source-blocked on the VPS and should be piloted against Ahmed-Mac or a copied Telegram Desktop archive.

### CMO Content Lane

- `content-claw`
- `executive-content-system`
- `content-publishing-safety`
- `linkedin`
- `premium-frontend-design`
- `Image`
- `avoid-ai-writing`
- `slides`
- `visual-explainer`
- `meme-maker` only when explicitly requested

LinkedIn posting remains proof-gated. Never post text-only when an image is expected.

### JobZoom / HR Lane

- `executive-cv-builder`
- `ai-pdf-builder`
- `Job Search MCP`
- `spreadsheet`
- `xlsx`
- `summarize`
- `doc`
- `himalaya` only for email classification workflows
- `document-extract` plugin: review before enabling broadly

JobZoom stays isolated and protected. Do not reduce scan scope or move it into generic fleet execution.

### Research Lane

- `tavily`
- `ai-research-scraper`
- `crawlee`
- `scrapling`
- `summarize`
- `browser-automation` only when page interaction is required
- `nasr-decision-brief`
- `skill-autoresearch`

Research outputs should end as briefs or registers, not large raw transcript pollution in NASR's main memory.

## Command-Only Or Restricted Skills

These should not be freely used by every front-facing turn:

- `gateway-runtime-safety`: CTO only, because runtime/config work is high-risk.
- `openclaw-backup`: CTO only, because backup/restore has operational risk.
- `node-connect`: CTO only, because node/file operations can affect paired devices.
- `browser-automation`: restricted to cases where account/session state is required and source inspection is necessary.
- `content-publishing-safety` and `linkedin`: CMO lane and explicit approval/posting rules only.
- `executive-cv-builder`: HR/JobZoom lane, must read master CV data first.
- `Image`: CMO/content visual lane unless the user directly asks for image generation.

## Ecosystem Tool Availability Notes

Checked on 2026-05-29:

- `gitcrawl` is installed at `/usr/local/bin/gitcrawl` and `/root/go/bin/gitcrawl`. The first isolated sync pilot passed against `openclaw/openclaw` PR #1.
- `telecrawl` is installed at `/usr/local/bin/telecrawl` and `/root/go/bin/telecrawl`. CLI/status/doctor work, but the VPS has no Telegram Desktop `tdata` source.

Next action: CTO should build a read-only `gitcrawl` digest job and move the `telecrawl` import pilot to Ahmed-Mac or a copied Telegram Desktop archive.

## Governance Rules

- A skill is adopted only when it has an owner, trigger, input contract, output contract, verification gate, and failure mode.
- External side-effect skills require receipts.
- Agent-specific skills should be added only when they reduce repeated work or improve verification.
- Broad search/crawler skills should write summarized artifacts, not dump raw results into front-facing memory.
- If a workflow is repeated twice manually, consider turning it into a skill or typed workflow.
