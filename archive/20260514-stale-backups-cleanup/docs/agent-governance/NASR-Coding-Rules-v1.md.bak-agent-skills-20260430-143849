# NASR Coding Rules v1

## Why this exists

This document is the coding-specific source of truth for NASR-style implementation discipline.

It exists to reduce four recurring failure modes in coding agents:
- silent assumptions
- overbuilt solutions
- unrelated edits
- weak verification

This is not meant to add another layer of generic prompt sludge. It is meant to consolidate the strongest coding rules already present across the workspace into one reusable doctrine.

## Audit summary

### Already present in `SOUL.md`
- State assumptions explicitly
- Prefer the simplest complete solution
- Verify before declaring success

### Already present in `coding-agent` SKILL.md
- explicit assumptions and tradeoffs
- smallest complete change
- surgical edits only
- define success before implementation
- evidence-based completion format
- verification with concrete commands
- drift control and scope control

### Gap
The gap is not lack of principles. The gap is that the principles are spread across multiple places.

## The rules

### 1. State assumptions before implementation
If something important is uncertain, name it before coding.
Do not silently choose an interpretation and proceed as if it were confirmed.

### 2. Surface forks instead of hiding them
When there are multiple valid interpretations or fixes, show the options briefly and recommend one.
Do not bury tradeoffs inside implementation.

### 3. Prefer the smallest complete solution
Solve the actual problem with the least moving parts that fully satisfy the request.
No speculative architecture, no future-proofing theater, no optionality that was not asked for.

### 4. Keep abstractions earned, not imagined
Do not add helpers, wrappers, layers, config, or reusable patterns unless the task genuinely requires them now.
Single-use code should stay simple.

### 5. Make surgical edits
Touch only the files, functions, and lines required for the task.
Do not refactor adjacent code, rewrite comments, restyle formatting, or clean up unrelated problems unless explicitly asked.

### 6. Clean up only the mess created by the change
If the implementation creates dead imports, variables, branches, or helpers, remove those.
If unrelated dead code was already there, mention it, do not silently remove it.

### 7. Define success in a verifiable form before coding
Before implementation, identify at least one real check that will prove completion.
Prefer a test, build, reproduction step, or exact command over vague notions like "should work."

### 8. Read the target before editing it
Read the exact file or function being changed and its direct caller, dependent, or interface before broad exploration.
If you cannot name the primary target after the first read, stop and re-anchor.

### 9. Treat drift as failure, not motion
If the investigation starts producing output that is not directly tied to the stated objective, stop and re-center.
Logs, searches, and large outputs are not progress unless they sharpen the diagnosis.

### 10. Verify the result, not the effort
A command succeeding is not proof.
A patch applying is not proof.
A test that was not relevant is not proof.
The only proof is a verification step that demonstrates the requested behavior actually changed as intended.

### 11. Completion notes must include evidence
Do not say "done" without proof.
Completion should include:
- what changed
- how it was verified
- the exact command or test used
- the key output or result

### 12. Escalate after repeated failure
If two materially different attempts hit the same wall, or three approaches fail overall, stop improvising.
Report the blocker, diagnosis, and the smallest decision needed from Ahmed.

## Default execution pattern

For non-trivial coding work, default to this sequence:

1. Name the target artifact.
2. Name the likely defect or decision.
3. Read the target and direct dependency.
4. State assumptions or forks if ambiguity exists.
5. Define the success check.
6. Make the smallest complete change.
7. Run a real verification step.
8. Report with evidence.

## Completion format

Use this compact completion format by default:

- CHANGED: files or scopes touched
- WHAT: concrete behavior change
- VERIFIED: exact command plus key output
- TEST: real test or reproduction result
- RISK: remaining caveat, if any
- NEXT: only if a real next step exists

## Integration recommendation

### Done
- `coding-agent` now references this file as the source-of-truth instead of carrying a duplicated doctrine block.
- `NASR-ACP-Coding-Brief.md` now provides a reusable ACP/sub-agent briefing template that points back here. <!-- updated 2026-04-13 -->

### Next
Use this document as the canonical reference for coding-task discipline in future ACP or coding sub-agent launches.

### Do not do
- Do not paste this wholesale into `SOUL.md`
- Do not duplicate it across multiple skills
- Do not create separate variants for Codex, Claude Code, and ACP unless behavior materially differs

## Bottom line

The right move is consolidation, not more instruction volume.

We already have the right instincts.
What we need is one clean coding doctrine that agents can inherit without noise.
