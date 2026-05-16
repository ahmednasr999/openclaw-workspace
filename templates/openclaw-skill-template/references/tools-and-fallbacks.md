# Tools and Fallbacks

## Preferred order

1. First-class OpenClaw tool.
2. Existing safe wrapper.
3. New small reusable wrapper.
4. Shell only when necessary.
5. External/destructive/runtime action only when approved.

## Avoid

- Inline eval for routine checks.
- Long shell pipelines.
- Repeating failed queries without inspecting source/schema.

## If blocked

State the missing permission, source, or decision. Do not pretend tool success proves outcome success.
