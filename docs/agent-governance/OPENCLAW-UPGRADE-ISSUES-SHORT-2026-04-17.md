# OpenClaw Upgrade Issues - Short GitHub-Native Versions

## 1) Unified run trace schema across agent, ACP, subagent, and task flows

**Labels:** `architecture`, `observability`, `tracing`, `P0`

### Summary
Create one canonical run trace schema that works across main agent runs, ACP sessions, subagents, and task flows.

### Why
Tracing exists, but it is fragmented and too low-level. When a run goes wrong, it is hard to quickly answer:
- what happened
- what step failed
- what tools were involved
- whether delegation happened
- how parent and child runs relate

### Scope
Define a schema with fields like:
- `runId`
- `sessionKey`
- `parentRunId`
- `taskId`
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

### Likely files
- `src/agents/trace-base.ts`
- `src/agents/cache-trace.ts`
- `src/agents/acp-spawn-parent-stream.ts`
- `src/tasks/task-executor.ts`
- new: `src/agents/run-trace.ts`

### Acceptance criteria
- one canonical trace schema exists
- main, ACP, and subagent/task runs emit into it
- parent-child linkage is preserved
- step-level and tool-level events are supported
- trace data can reconstruct a compact run timeline

### Checklist
- [ ] define schema types
- [ ] add parent-child linkage fields
- [ ] map current trace producers to schema
- [ ] update ACP relay path
- [ ] update task executor paths
- [ ] add tests

---

## 2) Add a core eval harness for memory, tool routing, delegation, and proactive behavior

**Labels:** `quality`, `evals`, `regression`, `P0`

### Summary
Add a small, fixture-driven eval harness to catch core behavior regressions before they hit production use.

### Why
OpenClaw is now powerful enough that regressions are more dangerous than missing features. Changes can silently break:
- memory continuity
- tool routing discipline
- untrusted content handling
- delegation quality
- proactive and cron behavior

### Scope
Build a lightweight eval runner with an initial gold set of 10 to 15 cases covering:
1. memory continuity
2. tool routing
3. untrusted external content handling
4. delegation quality
5. proactive and cron behavior

### Likely files
- new: `qa/evals/` or `test/evals/`
- new: `qa/fixtures/`
- runner/bootstrap glue as needed

### Acceptance criteria
- eval harness runs locally
- at least 10 to 15 core cases exist
- failures are readable and actionable
- memory, tool, delegation, and proactive behaviors are each covered

### Checklist
- [ ] choose eval directory structure
- [ ] define fixture format
- [ ] build minimal eval runner
- [ ] add memory cases
- [ ] add tool routing cases
- [ ] add untrusted-content cases
- [ ] add delegation cases
- [ ] add proactive and cron cases
- [ ] document how to add new evals

---

## 3) Introduce typed handoff contracts for expert, worker, and agent-as-tool delegation

**Labels:** `architecture`, `multi-agent`, `delegation`, `P0`

### Summary
Introduce explicit handoff types and required contracts so delegation is predictable, traceable, and easier to evaluate.

### Why
Several delegation patterns are currently mixed together:
- expert delegation
- bounded worker execution
- agent-as-tool behavior

That creates ambiguity in:
- how briefs are written
- what outputs are expected
- how runs should be traced
- how parent sessions interpret child results

### Scope
Define these handoff types:
- `expert_delegate`
- `worker_delegate`
- `agent_as_tool`

Each handoff should declare:
- `handoffType`
- `objective`
- `scope`
- `constraints`
- `expectedOutput`
- `stopConditions`
- `parentRunId`
- `requesterSessionKey`

Delegated runs should return structured results where possible:
- `status`
- `summary`
- `artifacts`
- `blockers`
- `recommendedNextStep`

### Likely files
- new: `src/agents/handoff-types.ts`
- new: `src/agents/handoffs.ts`
- `src/agents/acp-spawn-parent-stream.ts`
- `src/tasks/task-executor.ts`

### Acceptance criteria
- handoff types are defined in code
- handoff creation requires objective, scope, constraints, and output expectations
- parent-child linkage includes handoff type
- delegated runs can return structured payloads
- trace events include handoff metadata

### Checklist
- [ ] define handoff types
- [ ] define handoff payload schema
- [ ] define structured return schema
- [ ] update delegation entry points
- [ ] update traces
- [ ] update task flow summaries
- [ ] add tests

---

## Recommended order
1. Unified run trace schema
2. Core eval harness
3. Typed handoff contracts
