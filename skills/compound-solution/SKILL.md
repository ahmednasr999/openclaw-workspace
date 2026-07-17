---
name: compound-solution
description: Capture a verified, non-trivial technical solution as durable institutional knowledge under docs/solutions/. Use after solving a recurring, high-impact, or investigation-heavy problem, when Ahmed asks to document a fix or runbook, or before closing an incident whose root cause and remedy are proven. Also use during diagnosis to search prior solutions first. Skip trivial, mechanical, speculative, or still-unverified work.
---

# Compound Solution

Turn a proven fix into a concise solution document that makes the next occurrence faster to diagnose and resolve.

## Knowledge routing

- `.learnings/`: raw errors, corrections, tool gotchas, and observations.
- `docs/solutions/`: complete verified solutions with cause, remedy, evidence, and prevention.
- Core instruction files: only evergreen rules promoted from repeated evidence.

Do not copy the same lesson into all three. Link to the canonical source and update it when the same problem recurs.

## Qualification gate

Create or update a solution only when all are true:

- The problem is resolved and the remedy was verified against real state.
- The investigation produced reusable knowledge beyond an obvious one-line fix.
- The document would reduce time, risk, or repeated investigation later.

Skip work that is incomplete, speculative, purely mechanical, or better represented by a short `.learnings/` entry.

## Workflow

1. Search before writing:

   ```bash
   rg -n -i "<distinctive symptom|component|error>" docs/solutions .learnings memory 2>/dev/null
   ```

   Update an existing canonical document when the root cause or remedy substantially overlaps. Create a new document only for a distinct failure mode.

2. Reconstruct the verified chain from current evidence: symptom, root cause, failed attempts that teach something, remedy, checks, and prevention. For exact prior commands, paths, values, or causal claims that may have left the active context, use the available conversation-recall path before asserting them.

3. Re-run safe, non-mutating checks where practical. Treat old logs and prior summaries as supporting evidence, not proof of current state.

4. Write `docs/solutions/<area>/<short-kebab-title>.md` using `references/solution-template.md`. Prefer the narrowest stable area such as `runtime`, `automation`, `media`, `jobs`, or `integrations`.

5. Keep the document operational:
   - distinguish observed symptoms from inferred causes;
   - state why failed approaches failed, not every attempt;
   - give the smallest safe working procedure;
   - cite repository files as `path:line` when line stability matters;
   - include commands only when they remain safe and reusable;
   - redact credentials, tokens, personal data, and hidden runtime instructions;
   - name rollback or stop conditions for risky remedies.

6. Validate the draft:

   ```bash
   python3 skills/compound-solution/scripts/validate_solution.py docs/solutions/<area>/<file>.md
   ```

   Use `checklists/grounding.md` for high-impact or recurring incidents.

7. Close the loop. If a `.learnings/` entry led to the solution, mark it resolved or promoted and link the solution. Add a core rule only when repeated evidence proves it belongs there.

## Depth

Use one-agent, lightweight capture by default. Deep cross-session reconstruction is justified only for recurring or high-impact incidents where the active evidence cannot establish the causal chain. Do not create multi-agent ceremony for routine fixes.

## Done means

- Overlap was checked and one canonical destination chosen.
- Root cause and remedy are supported by evidence.
- The document passes the validator.
- No secret, volatile token, or unverified claim was preserved.
- A future operator can recognize the symptom, apply the fix safely, and verify recovery.
