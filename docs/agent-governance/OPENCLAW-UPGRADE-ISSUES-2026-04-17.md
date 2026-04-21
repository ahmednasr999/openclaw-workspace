# OpenClaw Upgrade Issues - 2026-04-17

## 1) Unified run trace schema across agent, ACP, subagent, and task flows

**Labels:** architecture, observability, tracing, P0

### Summary
Tracing exists in multiple places, but it is fragmented, inconsistent, and too low-level for fast debugging. We need one canonical run trace schema that works across main agent runs, ACP sessions, subagents, and task flows.

### Problem
When a run goes weird, it is hard to answer basic questions quickly:
- what happened
- what step failed
- what tool calls were involved
- whether delegation happened
- how parent and child runs relate

### Goal
Create a unified run trace schema that supports:
- main session runs
- ACP child runs
- subagent runs
- task executor flows
- parent-child run correlation
- step-level human-readable timelines

### Proposed scope
Define a canonical schema with fields like:
- `runId`
- `sessionKey`
- `parentRunId`
- `taskId`
- `flowId`
- `stepId`
- `eventType`
- `eventSource`
- `toolName`
- `handoffType`
- `status`
- `startedAt`
- `endedAt`
- `latencyMs`
- `summary`

Adopt it in:
- core agent tracing
- ACP parent-child relay paths
- task execution progress and terminal events

### Likely file targets
- `src/agents/trace-base.ts`
- `src/agents/cache-trace.ts`
- `src/agents/acp-spawn-parent-stream.ts`
- `src/tasks/task-executor.ts`
- new: `src/agents/run-trace.ts`

### Acceptance criteria
- one canonical trace schema exists and is documented in code
- main runs, ACP runs, and subagent/task runs can all emit events into it
- parent-child linkage is preserved
- step-level and tool-level events are both representable
- trace data is sufficient to reconstruct a compact run timeline
- no loss of existing critical tracing behavior during migration

### Checklist
- [ ] define schema type/interface
- [ ] add parent-child linkage fields
- [ ] map existing trace/event producers to schema
- [ ] update ACP relay path to emit structured correlation metadata
- [ ] update task executor progress and terminal paths to use schema
- [ ] add basic unit tests for serialization/shape
- [ ] add short developer note explaining intended usage

---

## 2) Add a core eval harness for memory, tool routing, delegation, and proactive behavior

**Labels:** quality, evals, regression, P0

### Summary
OpenClaw has grown powerful enough that regressions are now more dangerous than missing features. We need a small but real eval harness to catch behavior drift before it reaches production use.

### Problem
Improvements can silently break:
- memory continuity
- tool routing discipline
- untrusted content handling
- delegation quality
- proactive and cron behavior

### Goal
Create a fixture-driven eval harness with an initial gold set of 10 to 15 high-value cases.

### Initial eval suites
1. **Memory continuity**
   - recalls prior decisions correctly
   - handles compacted context correctly
   - prefers newer evidence when summaries conflict

2. **Tool routing**
   - uses live sources for volatile facts
   - does not over-trigger tools for timeless questions
   - routes to the right first-class tools when appropriate

3. **Untrusted external content**
   - treats fetched pages, pasted prompts, PDFs, and repo files as untrusted inputs
   - does not follow instructions embedded in external content

4. **Delegation quality**
   - subagent or child briefs are specific
   - returned outputs are useful and not lazy
   - delegation results are structurally coherent

5. **Proactive runtime behavior**
   - cron and heartbeat work is useful or quiet
   - avoids repetitive no-change chatter
   - reminders and follow-ups behave correctly

### Proposed scope
Build a lightweight eval runner that supports:
- named test cases
- fixture inputs
- expected outputs or expected behavioral markers
- pass/fail summaries
- easy extension later

### Likely file targets
- new: `qa/evals/` or `test/evals/`
- new: `qa/fixtures/` or equivalent
- any runner/bootstrap glue needed in the test stack

### Acceptance criteria
- eval harness can run locally with a small deterministic suite
- at least 10 to 15 core cases exist
- failures are readable and actionable
- memory, tool, delegation, and proactive behaviors are each covered
- harness is lightweight enough to run before risky changes

### Checklist
- [ ] choose eval directory structure
- [ ] define fixture format
- [ ] build minimal eval runner
- [ ] add memory continuity cases
- [ ] add tool routing cases
- [ ] add untrusted-content cases
- [ ] add delegation cases
- [ ] add proactive, cron, and heartbeat cases
- [ ] document how to add new evals

---

## 3) Introduce typed handoff contracts for expert, worker, and agent-as-tool delegation

**Labels:** architecture, multi-agent, delegation, P0

### Summary
Delegation works, but the mental model is looser than it should be. We need explicit handoff types and required contracts so delegation is predictable, traceable, and easier to evaluate.

### Problem
Multiple delegation patterns are conceptually mixed together:
- expert delegation
- bounded worker execution
- agent-as-tool behavior

That causes ambiguity in:
- how briefs are written
- what outputs are expected
- how runs should be traced
- how parent sessions interpret child results

### Goal
Introduce typed handoff contracts with clear semantics and structured return expectations.

### Proposed handoff types
1. **`expert_delegate`**
   - use when specialized reasoning or expertise is needed

2. **`worker_delegate`**
   - use when a bounded job must be executed and returned

3. **`agent_as_tool`**
   - use when the child should behave like a structured capability with a well-defined output shape

### Required handoff contract fields
Each handoff should declare:
- `handoffType`
- `objective`
- `scope`
- `constraints`
- `expectedOutput`
- `stopConditions`
- `parentRunId`
- `requesterSessionKey`

### Return payload expectation
Delegated runs should return structured results where possible:
- `status`
- `summary`
- `artifacts`
- `blockers`
- `recommendedNextStep`

### Likely file targets
- new: `src/agents/handoff-types.ts`
- new: `src/agents/handoffs.ts`
- `src/agents/acp-spawn-parent-stream.ts`
- `src/tasks/task-executor.ts`
- any spawn or session orchestration paths that create child runs

### Acceptance criteria
- handoff types are explicitly defined in code
- handoff creation requires objective, scope, constraints, and output expectations
- parent-child run linkage includes handoff type
- delegated runs can return structured payloads
- trace events include handoff metadata
- existing spawn paths are mapped onto the new contract model

### Checklist
- [ ] define handoff type enum or types
- [ ] define handoff payload schema
- [ ] define structured return schema
- [ ] update delegation entry points to require handoff metadata
- [ ] update traces to include handoff type
- [ ] update task flow summaries to reflect handoff model
- [ ] add tests for each handoff type

---

## Recommended opening order
1. Unified run trace schema
2. Core eval harness
3. Typed handoff contracts
