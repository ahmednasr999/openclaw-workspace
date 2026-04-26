# Worker vs Front-Facing Agents

Last updated: 2026-04-21
Owner: NASR
Status: proposed policy
Purpose: define when work should stay in the conversational assistant lane versus when it should run in a worker-style execution lane.

## Core idea

Not every task should run in the same kind of agent context.

A front-facing agent is optimized for:
- conversation
- judgment
- synthesis
- approval handling
- identity continuity

A worker lane is optimized for:
- bounded execution
- tool-heavy jobs
- repetitive automation
- proofs, exports, and audits
- less chatter, more result

## Front-facing lane

Use when the value is primarily:
- thinking with Ahmed
- clarifying tradeoffs
- asking for approval
- summarizing complex outputs
- coordinating multiple workers
- holding long-lived conversational context

Examples:
- strategy discussion
- architecture decisions
- final explanation back to Ahmed
- approval-sensitive publishing step

## Worker lane

Use when the value is primarily:
- running tools
- producing an artifact
- validating an export
- checking a schedule or monitor
- performing repetitive or scoped execution
- collecting facts for later synthesis

Examples:
- cron-driven checks
- report generation
- export/render pipeline
- bounded research sweep
- verification pass
- preflight audit before a publish step

## Decision rule

If the user would be annoyed by the intermediate steps, it should probably be a worker lane.

If the user benefits from the reasoning and tradeoff handling in real time, it should stay front-facing.

## Practical OpenClaw rule set

### Prefer front-facing for
- direct Telegram interactions
- approvals
- final summaries
- multi-option recommendations
- sensitive external communications

### Prefer worker style for
- cron-triggered jobs
- bounded subagent tasks
- ACP/background executions
- validation passes
- export/render/reformat jobs
- repetitive monitoring and collection

## Output contract

### Worker outputs should be
- concise
- structured
- evidence-bearing
- easy for a front-facing agent to summarize

### Front-facing outputs should be
- human
- selective
- decision-oriented
- not full of tool noise

## Anti-patterns

### Do not
- make Ahmed watch raw tool chatter from bounded automation
- force the front-facing session to babysit long repetitive runs
- give background workers unnecessary personality overhead
- create many named agents without clear boundaries

### Also do not
- hide approvals inside workers when a real human decision is needed
- over-isolate work that requires strategic context mid-flight

## Suggested initial policy changes

1. Cron jobs that only collect, verify, or export should default to worker-style execution.
2. Front-facing sessions should summarize worker results instead of replaying raw execution noise.
3. Proof-sensitive production jobs should run with receipts and verification expectations.
4. If a worker blocks, it should surface a structured blocked reason back to the front-facing lane.

## Relationship to receipts

Worker lanes become much more trustworthy once they emit receipts.

That is why receipts should land before any ambitious worker-board or control-plane work.

## Definition of success

This policy is working when:
- Ahmed sees fewer noisy progress messages
- bounded jobs return cleaner outputs
- cron work is easier to trust
- front-facing conversations feel sharper because they synthesize instead of stream tool exhaust
