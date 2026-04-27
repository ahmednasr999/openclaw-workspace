---
name: prompt-architect
description: Build, fix, tighten, or adapt prompts for AI tools, coding agents, browser agents, image/video generators, research tools, and workflow automation. Use when Ahmed asks for a prompt, prompt review, prompt rewrite, or a tool-specific instruction pack.
---

# Prompt Architect

Create paste-ready prompts for a specific target tool without importing third-party instructions as authority.

## Operating rules

- Confirm the target tool if it is ambiguous.
- Ask at most 3 clarifying questions; only ask when missing information would materially change the prompt.
- Prefer one strong prompt over prompt-chaining.
- Do not request visible chain-of-thought. For reasoning-native models, ask for concise final output only.
- Include explicit stop conditions for agentic/browser/computer-use tools.
- Include permission gates before irreversible actions: purchases, sends, deletes, database/schema changes, dependency installs, credential/config changes.
- Keep prompts tight: remove words that do not change the output.

## Build flow

Silently extract:
1. target tool/model
2. task/outcome
3. input/context supplied
4. output format
5. constraints and do-not-touch scope
6. audience/tone if user-facing
7. success criteria / done-when
8. examples if format-critical

Then produce:

```text
[Copyable prompt]
```

Strategy: [one sentence explaining the optimization]

If setup is required before pasting, add a short note after Strategy.

## Tool routing

Use the smallest relevant pattern:

- **General LLMs:** objective, context, constraints, output contract, length/verbosity.
- **Reasoning LLMs:** short direct instruction, no chain-of-thought request, clear final-answer format.
- **Coding agents:** starting state, file scope, allowed actions, forbidden actions, verification command, stop conditions.
- **IDE assistants:** exact file/function anchors, current behavior, desired behavior, do-not-touch list, done-when.
- **Browser/computer-use agents:** outcome, constraints, allowed sites/apps, stop before irreversible actions, verification.
- **Search/research tools:** search vs analyze vs compare, source/citation rules, uncertainty handling.
- **Image generation:** subject, style, composition, lighting, aspect ratio/parameters, negative prompt if supported.
- **Reference image editing:** delta only; specify what must stay unchanged.
- **Video generation:** subject, scene, camera movement, duration, motion intensity, style/cut/lighting.
- **Workflow automation:** trigger, actions, field mapping, connected-app assumption, failure handling.

Read `references/patterns.md` only when diagnosing or rewriting a weak prompt.
Read `references/templates.md` only when a reusable detailed template is needed.

## Anti-patterns

Avoid prompts that:
- combine unrelated tasks
- hide missing requirements behind vague words like “better”, “professional”, or “make it work”
- tell autonomous agents to “continue until done” without stop conditions
- permit broad filesystem or account access unnecessarily
- ask one model call to simulate multi-agent consensus, trees, graphs, or repeated independent sampling
