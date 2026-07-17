# Model and Reasoning Picker

## Trigger

- "list models"
- "show models"
- "model picker"
- "pick model"
- "/models"

## Production Policy

The production model is `openai/gpt-5.6-sol`. Do not offer or switch to cheaper models unless Ahmed explicitly changes this policy.

Choose reasoning effort by task:

1. Low, deterministic checks, monitoring, parsing, and simple classification.
2. Medium, research, reports, analysis, and bounded reversible edits.
3. High, strategy, CVs, creative drafting, complex coding, architecture, and public-risk judgment.

Reply with the active model and recommended reasoning tier. A tier change never changes the model.
