# OpenClaw Ecosystem Adoption Register

Date: 2026-05-29
Owner: NASR
Status: active planning register

## Executive Decision

Adopt OpenClaw as Ahmed's personal AI operating layer, but selectively. The target is not to install every ecosystem project. The target is to harden six operating lanes:

1. Memory and retrieval
2. Executive job search and CV generation
3. LinkedIn and content production
4. Runtime health and recovery
5. Research and decision briefs
6. Agent/workflow automation with proof gates

Live baseline checked on 2026-05-29:

- OpenClaw version: `2026.5.27 (27ae826)`
- Skills: 118 total, 79 eligible/model-visible, 78 command-available, 0 missing requirements
- Plugins: 15 enabled out of 94 installed/available
- Agent skill matrix: `docs/agent-governance/openclaw-agent-skill-matrix-2026-05-29.md`
- Known runtime gap: LCM reports `runtime.llm.complete` unavailable, which limits plugin-side autonomous summarization/compaction until the runtime build includes Plugin SDK runtime LLM support

## Adoption Principles

- Prefer durable workflows over one-off tool use.
- Keep JobZoom isolated and protected.
- Keep CMO focused on content and LinkedIn.
- Keep CTO focused on runtime, monitoring, recovery, agents, and infrastructure.
- Add a dedicated research lane only if long-form research starts polluting NASR's front-facing session memory.
- Do not expose public surfaces such as Canvas, WebChat, or control UIs unless hardened separately.
- Require proof receipts for external side effects: posts, messages, config changes, CV/PDF delivery, and public artifacts.

## Priority Register

| Priority | Component | Adopt? | Owner | Purpose For Ahmed | Risk | Next Action | Status |
|---|---|---:|---|---|---|---|---|
| P0 | Runtime LLM support for plugins | Yes | CTO | Enables higher-quality plugin-side LCM summaries and autonomous plugin workflows | Runtime upgrade risk | Track fixed build, upgrade in controlled window, verify Telegram, model router, LCM, JobZoom | Open |
| P0 | Skill governance | Yes | NASR/CTO | Reduce prompt/context noise and make recurring work reusable | Too many visible skills dilute behavior | Audit top active skills and define allowed skills by agent | Open |
| P1 | telecrawl | Pilot | NASR/CTO | Local searchable Telegram history for decision recall and memory reconstruction | Privacy, duplication, schema drift | Installed and doctor/status verified; import must run on Ahmed-Mac or copied Telegram Desktop archive because VPS has no `tdata` source | Source-blocked |
| P1 | gitcrawl | Pilot | CTO | Track OpenClaw repos, issues, PRs, runtime changes, plugin changes | Noise if not scoped | Installed and verified with one-thread `openclaw/openclaw` sync into isolated SQLite; next build weekly digest | Pilot passed |
| P1 | notcrawl | Conditional | NASR/CMO | Mirror Notion content pipeline and job/CV workflow data | Already have direct Notion credentials, avoid duplicate source of truth | Use only if Notion mirror adds retrieval value beyond direct API | Hold |
| P1 | Tavily skill | Yes | Research | Reliable deep search and URL extraction for research briefs | API quota/cost, source quality | Use for deep current research, vendor scans, ecosystem tracking | Ready |
| P1 | Research agent lane | Conditional | NASR | Keeps long research out of front-facing memory | More agents without ownership creates ambiguity | Add only if repeated long research threads continue | Hold |
| P2 | Lobster workflows | Pilot | CTO | Convert repeated procedures into typed local-first pipelines | Premature if gates are weak | Start with job-link-to-ATS-CV-PDF workflow | Open |
| P2 | Crabfleet | Later pilot | CTO | Fleet execution, monitoring, intervention for multi-agent work | Public/side-effect tasks can duplicate actions | Pilot only on non-public research and diagnostics first | Hold |
| P2 | acpx | Experiment | CTO | Headless stateful ACP sessions for scripts, tests, and cron | Protocol churn | Use for one repeatable research or CTO diagnostic run | Open |
| P2 | clawbench-style evaluation | Yes | CTO | Regression tests for agents and workflows | False confidence if test set is weak | Build small benchmark around NASR, CMO, JobZoom, CTO tasks | Open |
| P2 | Local document extraction router | Yes, bounded | CTO/HR/JobZoom | Faster, broader local extraction for CVs, reports, and office files | AnyDoc is young, lacks OCR, and loses PPTX slide boundaries | Pinned AnyDoc for non-presentations; retain MarkItDown for PPTX and fallback | Ready (2026-08-05) |
| P3 | ClickClack | Defer | CTO | Desktop-style control surface | Low value while Telegram is primary | Revisit only if operator UI becomes a real bottleneck | Deferred |
| P3 | Canvas / broad web UI | Defer | CTO | Visual control and UI rendering | Exposure risk | Keep disabled unless hardened and needed | Deferred |
| P3 | Hardware/ESP nodes | Defer | CTO | Physical automation | Not aligned to current executive/job/content lanes | No action | Deferred |

## 30-Day Execution Plan

### Week 1: Stabilize And Register

- Track the `runtime.llm.complete` limitation as a CTO/runtime item.
- Create an approved skill matrix by agent: NASR, CTO, CMO, JobZoom, Research.
- Identify the top 15 actually useful skills and the skills that should stay command-only or disabled.
- Define the NASR Knowledge Lake shape: SQLite archives plus normalized Markdown, with source, timestamp, thread/session id, and retention rules.
- Run the telecrawl import pilot on Ahmed-Mac or a copied Telegram Desktop archive after `doctor` passes.

### Week 2: Retrieval Foundation

- Convert the passed gitcrawl one-thread pilot into a read-only OpenClaw repo digest.
- Decide whether Notion should be mirrored through notcrawl or kept direct-API only.
- Add a daily memory delta report design: what changed, what matters, what requires action.
- Convert one current manual research workflow to Tavily deep search plus a written decision brief.

### Weeks 3-4: Workflow Hardening

- Build the first typed workflow around job link to ATS score to tailored CV to PDF to Telegram delivery.
- Add receipt/proof gates to CV/PDF delivery, LinkedIn posting, and gateway/config changes.
- Pilot acpx behind CTO automation for one repeatable diagnostic or research run.
- Draft a private skill quality checklist: owner, trigger, inputs, outputs, verification, failure modes, and rollback.

## 90-Day Target State

By the end of 90 days, the system should have:

- A local searchable memory substrate for Telegram, GitHub/OpenClaw repos, selected Notion data, and important generated artifacts.
- Clear agent ownership: NASR front-facing, CTO runtime, CMO content, JobZoom jobs/CVs, optional Research long-form analysis.
- Typed workflows for the highest-repeat lanes.
- Receipts for proof-sensitive actions.
- A small benchmark suite that catches regressions in agent behavior, output quality, and delivery verification.
- A private/personal skill registry of proven Ahmed-specific workflows.

## Immediate Backlog

1. CTO: investigate the runtime build path for Plugin SDK `runtime.llm.complete` support.
2. NASR/CTO: create the agent skill allowlist matrix.
3. CTO: move telecrawl import pilot to Ahmed-Mac or a copied Telegram Desktop archive, because VPS has no `tdata` source.
4. CTO: build the first read-only gitcrawl OpenClaw repo digest after the one-thread sync pilot passed.
5. CTO/HR/JobZoom: monitor the pinned AnyDoc parser and keep scanned-document OCR as a separate controlled lane.
6. NASR: create the first Tavily-backed ecosystem radar brief template.
7. CTO: define receipt schema adoption for proof-sensitive workflows, aligned with the existing April roadmap.

## Non-Goals

- Do not expose control UIs publicly.
- Do not move LinkedIn posting or JobZoom onto fleet execution until duplicate prevention and receipts are proven.
- Do not add a new agent unless it reduces memory pollution or creates a clear ownership boundary.
- Do not replace working Notion/Telegram direct credentials with Composio or extra OAuth flows.
- Do not treat an installed skill as adopted until it has an owner, trigger, output contract, and verification gate.
