# Graph of Skills sidecar MVP for OpenClaw

Last updated: 2026-04-14
Owner: NASR
Status: Recommended as shadow-mode experiment, not core dispatch replacement

## Executive summary

Graph of Skills is worth testing in this stack, but only as a sidecar.

The right first move is not to replace OpenClaw skill triggering. The right first move is to add a retrieval advisor that:

1. indexes the installed skill library offline
2. returns a ranked skill set plus likely dependencies for each task
3. logs what it would have recommended
4. compares those recommendations with what OpenClaw actually exposed and what the model actually used

This lets us answer the only question that matters:

**Does dependency-aware retrieval materially improve real Ahmed workflows enough to justify runtime complexity?**

My current view: useful research direction, medium priority, safe to test, not yet core-path worthy.

## What OpenClaw does today

Current skill behavior is prompt-centric, not retrieval-centric.

### Current runtime flow

1. OpenClaw loads skills from several roots.
2. It merges them by precedence.
3. It filters to eligible skills.
4. It renders `<available_skills>` into the system prompt.
5. The model is instructed to pick exactly one clearly applicable skill up front.
6. The model reads that `SKILL.md` only after selection.

### Confirmed local hook points

#### 1) Skill contract in the system prompt
- File: `/root/openclaw/src/agents/system-prompt.ts`
- Function: `buildSkillsSection(...)`
- Current behavior: injects the mandatory rules that tell the model to scan `<available_skills>`, choose the most specific skill, and read only one `SKILL.md` up front.

#### 2) Skill loading and prompt construction
- File: `/root/openclaw/src/agents/skills/workspace.ts`
- Relevant functions:
  - `loadWorkspaceSkillEntries(...)`
  - `buildWorkspaceSkillSnapshot(...)`
  - `buildWorkspaceSkillsPrompt(...)`
  - `resolveSkillsPromptForRun(...)`
- Current behavior:
  - loads skills from bundled, managed, personal `.agents/skills`, project `.agents/skills`, and workspace `skills/`
  - merges by precedence
  - filters eligible skills
  - renders full or compact `<available_skills>` prompt text

#### 3) Per-session skill snapshot generation
- File: `/root/openclaw/src/auto-reply/reply/session-updates.ts`
- Function: `ensureSkillSnapshot(...)`
- Current behavior: creates or refreshes the session skill snapshot before runs.

#### 4) Main reply pipeline
- File: `/root/openclaw/src/auto-reply/reply/get-reply-run.ts`
- Current behavior: calls `ensureSkillSnapshot(...)` before the reply run proceeds.

#### 5) CLI and embedded runner prompt assembly
- Files:
  - `/root/openclaw/src/agents/cli-runner/prepare.ts`
  - `/root/openclaw/src/agents/pi-embedded-runner/run/attempt.ts`
- Current behavior: both call `resolveSkillsPromptForRun(...)` and include the skill prompt in the final system prompt.

#### 6) Skill status and audit surface
- File: `/root/openclaw/src/agents/skills-status.ts`
- Relevant function: `buildWorkspaceSkillStatus(...)`
- Current behavior: exposes eligibility, missing requirements, install options, and source for each skill.

## What this means

OpenClaw already has the right insertion points.

We do **not** need to replace the whole prompt system to test Graph of Skills.
We only need a new retrieval sidecar that can optionally produce a ranked `skillFilter` or advisory list before `ensureSkillSnapshot(...)` builds the prompt.

## Recommendation

## Phase 0 - shadow mode only

No runtime behavior change.

Add a sidecar that runs before skill snapshot generation, but only logs:
- top retrieved skills
- inferred dependencies
- score/rank
- latency
- current eligible OpenClaw skill set
- eventual skill actually read by the model, if observable from transcript/tool usage

This is the safest MVP.

## Why shadow mode first

Because the current system's biggest failures are not skill lookup failures.
They are:
- plugin/runtime bugs
- fragile integrations
- cron/session reliability
- config safety
- recovery discipline

A retrieval engine does not fix those.
So the burden of proof is high.

## Proposed MVP architecture

## A. Offline indexer

Build a local index over the same skill universe OpenClaw already uses.

### Skill roots to index
Mirror OpenClaw's real sources as closely as possible:
- bundled skills
- managed skills
- personal `~/.agents/skills`
- project `.agents/skills`
- workspace `skills/`
- plugin-provided skills where present

### Required normalized skill record
Each indexed skill should capture at least:
- `skill_name`
- `skill_key` if present in metadata
- `file_path`
- `source`
- `description`
- `frontmatter metadata`
- `workspace / agent scope`
- `dependencies` inferred from references or explicit metadata if later added
- `related_skills` inferred offline

### Important constraint
The sidecar index must not invent a different skill universe than OpenClaw runtime. If the sidecar sees skills that runtime cannot load, results become misleading fast.

## B. Retrieval adapter

For a task string, the adapter returns:
- top K primary skills
- dependency/supporting skills
- confidence or rank score
- explanation fields for debugging only

Example return shape:

```json
{
  "query": "fix failing GitHub PR checks",
  "primary": ["gh-fix-ci", "github"],
  "supporting": ["coding-agent", "gh-address-comments"],
  "latency_ms": 74
}
```

## C. OpenClaw bridge

This is the critical part.

The bridge should map GoS output into **existing OpenClaw knobs**, not invent a new dispatch model on day 1.

### Best bridge target for MVP
Use `skillFilter` as the runtime bridge.

Why:
- it already exists in reply/session code
- it constrains loaded skills without redesigning prompt semantics
- it lets OpenClaw remain the decision-maker inside a reduced candidate set

### Bridge modes

#### Mode 0 - log only
- do not change prompt
- save retrieval results to diagnostics

#### Mode 1 - advisory only
- keep full skill prompt
- prepend a tiny note such as:
  - "Candidate high-confidence skills: github, gh-fix-ci, coding-agent"
- lower risk than hard filtering, but still changes prompt behavior

#### Mode 2 - filtered candidate set
- pass GoS-ranked names into `skillFilter`
- let OpenClaw build `<available_skills>` from only those entries
- keep current one-skill selection contract intact

### Recommendation
Start at Mode 0.
Move to Mode 2 only after evidence.
Skip Mode 1 unless we need an intermediate test.

## D. Diagnostics and storage

Store shadow-mode logs under a dedicated local path, for example:
- `/root/.openclaw/workspace/data/gos-shadow/`

Suggested artifacts:
- `queries.jsonl`
- `comparisons.jsonl`
- `daily-summary.json`

Each shadow record should include:
- timestamp
- session key
- agent id
- user request text hash
- GoS top skills
- GoS supporting skills
- OpenClaw eligible skills count
- final skill prompt size in chars
- final skill actually read, if observed
- verdict: win / loss / neutral
- notes

## Exact hook strategy

## Hook 1 - safest insertion point
- File: `/root/openclaw/src/auto-reply/reply/get-reply-run.ts`
- Why: it already calls `ensureSkillSnapshot(...)` before reply execution.
- Use: add a shadow retrieval call here before snapshot creation, log results, then continue unchanged.

## Hook 2 - first real runtime intervention
- File: `/root/openclaw/src/auto-reply/reply/session-updates.ts`
- Why: `ensureSkillSnapshot(...)` already accepts `skillFilter`.
- Use: if shadow mode proves value, derive `skillFilter` from GoS results here.

## Hook 3 - keep prompt contract stable
- File: `/root/openclaw/src/agents/skills/workspace.ts`
- Why: `buildWorkspaceSkillSnapshot(...)` and `buildWorkspaceSkillsPrompt(...)` are the source of truth for what reaches the model.
- Use: avoid rewriting selection rules here early. Let this layer keep doing what it already does.

## Hook 4 - later only, not MVP
- File: `/root/openclaw/src/agents/system-prompt.ts`
- Why: changing the skill contract changes model behavior globally.
- Use: only touch this after shadow data proves current one-skill contract is the limiting factor.

## What not to do

Do not start with:
- replacing `<available_skills>` entirely
- letting GoS choose the skill with no model check
- changing all runners at once
- adding a second parallel prompt contract for skills
- indexing third-party skill repos without audit

That would create complexity before evidence.

## Evaluation plan

Use Ahmed's real task mix, not benchmark theater.

## Evaluation windows

### Window 1 - passive observation
Duration: 3 to 5 days
Mode: shadow only
Goal: learn distribution of task types and current miss patterns

### Window 2 - replay evaluation
Duration: 1 to 2 days
Mode: offline replay against recent transcripts
Goal: compare GoS candidate quality against actual chosen skills

### Window 3 - limited live filtering
Duration: 3 to 7 days
Mode: filtered candidate set for a narrow subset of tasks only
Goal: verify real runtime benefit without broad blast radius

## Task categories to score

Use real categories from this environment:
- GitHub and PR maintenance
- gateway/config/debugging
- CV and job workflows
- LinkedIn/content workflows
- reminders/calendar/productivity
- research/summarization
- file transformation tasks like docs, slides, spreadsheet, PDF

## Primary metrics

### 1) Top-1 skill quality
Did the top recommended skill match the best obvious skill?

### 2) Dependency recall
Did GoS include a genuinely useful supporting skill that baseline likely would not surface?

### 3) False positive rate
How often did GoS include distracting or irrelevant skills?

### 4) Prompt reduction
How much did candidate filtering reduce skill prompt size in chars/tokens?

### 5) Latency overhead
How much time did retrieval add before reply generation?

### 6) Outcome improvement
Most important metric.
Did the task complete more reliably, with fewer wrong turns, fewer extra reads, or fewer missed prerequisites?

## Suggested scorecard

Per task, label:
- `baseline_better`
- `gos_better`
- `tie`
- `unclear`

And capture why:
- better primary skill
- better dependency skill
- reduced prompt clutter
- false positive clutter
- no material difference

## Promotion criteria

Do **not** move beyond shadow mode unless these are true:
- clear win rate over baseline on real tasks
- low false-positive rate
- acceptable latency
- no new fragility in reply path
- at least one concrete class of recurring task improves materially

My threshold would be roughly:
- GoS better on 20%+ of evaluated multi-skill tasks
- false-positive clutter low enough that prompt quality is not degraded
- added latency small enough to be invisible in normal usage

## Good first scope

If we test live filtering, start only on tasks where skill overlap is real.

Best candidates:
- GitHub related work where `github`, `gh-fix-ci`, `gh-address-comments`, and `coding-agent` can overlap
- content workflows where research, writing, brand, and posting skills overlap
- complex file workflows where multiple document skills could apply

Bad first candidates:
- weather
- one-shot simple lookups
- narrow tasks with one obvious skill
- fragile gateway recovery tasks where extra moving parts are unwelcome

## Risks

### 1) Dual truth problem
If GoS indexes a different skill set than runtime, evaluation data becomes garbage.

### 2) Overfitting to descriptions
If dependencies are inferred poorly from prose only, the graph may look smart but retrieve junk.

### 3) Latency tax
Even a good retrieval layer can be net negative if it slows every turn.

### 4) Hidden prompt conflicts
If GoS advice fights the current system prompt, the model can become less predictable rather than more accurate.

### 5) Maintenance burden
A retrieval layer needs its own indexing, refresh, logging, and debugging path. That is real cost.

## Recommendation by phase

### Now
Build the design and measurement path only.

### Next
Implement a shadow-mode adapter with zero behavior change.

### Later, only if earned
Use GoS output to drive `skillFilter` for selected task families.

### Not recommended yet
Any full replacement of OpenClaw skill selection.

## Concrete implementation path

### Step 1
Create a local skill export command or adapter that serializes the exact runtime-visible skill set.

### Step 2
Feed that export into the GoS workspace builder.

### Step 3
Add a shadow retrieval call in `get-reply-run.ts`.

### Step 4
Write results to `data/gos-shadow/`.

### Step 5
Review 50 to 100 real tasks.

### Step 6
If it wins, test `skillFilter` on one narrow task family.

## Side findings

- OpenClaw already has most of the plumbing needed for a filtered-skill experiment. That is good news.
- The biggest architecture risk is not technical feasibility. It is whether the gain is large enough to justify another reliability surface.
- Before importing or trusting any third-party skill repo at scale, use the local read-only audit utility documented in `/root/.openclaw/workspace/docs/agent-governance/skill-audit.md`.

## Bottom line

Graph of Skills is promising for this environment **only if it proves it can improve multi-skill retrieval without hurting reliability**.

So the correct move is:
- measure first
- keep OpenClaw's current prompt contract intact
- use `skillFilter` as the first real bridge if the data is strong
- do not make it part of the critical path yet
