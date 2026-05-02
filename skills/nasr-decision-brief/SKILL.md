---
name: nasr-decision-brief
description: Produce concise NASR-style decision briefs for high-stakes choices, tradeoffs, role/job offers, salary/relocation, OpenClaw architecture, tooling purchases, public content strategy, or any decision where Ahmed asks for recommendations, options, risks, kill criteria, or a 72-hour action plan.
---

# NASR Decision Brief

Use this skill when Ahmed needs a recommendation, not generic advice.

## Operating stance

- Lead with the recommendation.
- Ask questions only when a missing fact changes the decision or creates real risk.
- Prefer 2-3 realistic options, not exhaustive possibility lists.
- Surface hidden assumptions and reversibility.
- Include kill criteria whenever the decision can be reversed or stopped.
- Separate what Ahmed must decide from what NASR can execute.
- Keep routine decisions short; expand only for high-stakes choices.

## Decision filters

Evaluate against the relevant filters:

- Money: salary, cost, upside, downside exposure.
- Time: Ahmed's attention cost and execution load.
- Reputation: executive credibility, public risk, relationship risk.
- Executive-role upside: GCC/C-suite/healthcare/digital transformation/PMO relevance.
- AI automation leverage: does it improve durable systems or reduce future work?
- Reversibility: reversible, hard to reverse, irreversible.
- Evidence quality: live facts, source strength, confidence, missing data.
- Approval boundary: NASR can execute vs Ahmed must approve.

## Output format

Use the compact format by default:

```markdown
Recommendation: <clear answer>
Confidence: high | medium | low

Why:
- <1-3 bullets>

Options:
1. <option> - upside / downside / reversibility
2. <option> - upside / downside / reversibility
3. <option> - upside / downside / reversibility

Hidden assumptions:
- <assumption>

Biggest risk:
- <risk>

Kill criteria:
- <specific signal that means stop, reverse, or revisit>

72-hour action plan:
- <step 1>
- <step 2>
- <step 3>

Decision boundary:
- Ahmed: <what only Ahmed can decide>
- NASR: <what I can execute without more input>
```

## Short-form variant

For small decisions, use:

```markdown
Recommendation: <answer>
Why: <one or two bullets>
Risk: <main risk>
Next move: <one concrete action>
```

## Quality bar

Before finalizing:

- The recommendation is explicit.
- The reasoning includes tradeoffs, not vibes.
- Kill criteria are concrete, not vague.
- The next action is executable.
- No external/public/destructive action is implied without approval.
