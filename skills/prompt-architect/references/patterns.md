# Prompt Anti-Patterns

Use this when reviewing or tightening an existing prompt.

## Common fixes

| Problem | Fix |
|---|---|
| Vague task verb: “help”, “improve”, “fix” | Replace with a concrete operation and success criteria. |
| No target tool/model | Ask or state the target before writing the prompt. |
| No output contract | Specify format, length, sections, JSON schema, file type, or exact deliverable. |
| No scope boundary | Add file paths, allowed apps/sites, do-not-touch list, and permission gates. |
| Multiple unrelated tasks | Split or state priority/order and stopping condition. |
| Style adjectives only | Translate “clean/professional/Notion-like” into exact visual/tone constraints. |
| Agent has no stop condition | Add “stop after X”, “ask before Y”, and “done when Z passes”. |
| Prompt asks for reasoning transcript | Ask for final answer, assumptions, checks, or concise rationale instead. |
| Unsupported multi-pass claims | Do not ask a single prompt to perform real tree/graph/consensus/self-consistency. |
| Missing verification | Add a concrete test, lint/build command, screenshot, citation, or checklist. |

## Rewrite checklist

- Target tool named
- Outcome first
- Inputs/context bounded
- Constraints explicit
- Output contract locked
- Verification included
- Stop/approval gates included for agents
- No unnecessary verbosity
