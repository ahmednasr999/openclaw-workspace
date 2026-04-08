# Anthropic Model Prompt Guide (Opus / Sonnet)

## Strengths
- Deep reasoning, nuance, long-context analysis
- Excellent at multi-step planning
- Strong at code generation with explanation
- Best for: CV creation, strategic analysis, complex debugging

## Prompting Style
- Be direct and specific - Anthropic models respond well to structured requests
- Use XML tags for structured input/output when needed
- Leverage "thinking" for complex tasks
- Chain-of-thought works naturally without explicit prompting

## Avoid
- Don't ask it to "be creative" without constraints - give structure
- Don't use system prompts over 4000 tokens (diminishing returns)
- Don't repeat instructions - once is enough
