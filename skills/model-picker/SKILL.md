# Model Picker Skill

## Trigger
- "list models" 
- "show models"
- "model picker"
- "pick model"
- "/models"

## What it does
Responds with a numbered list of available models. User picks by number.

## Available Models
1. minimax-m2.5 — MiniMax M2.5 (default, free)
2. gpt54 — GPT-5.4 (coding, agentic)
3. gpt54pro — GPT-5.4 Pro (max performance)
4. gpt53codex — GPT-5.3 Codex
5. opus46 — Claude Opus 4.6 (deep strategy)
6. sonnet46 — Claude Sonnet 4.6 (drafting)
7. haiku — Claude Haiku 4.5 (fast)
8. kimi — Kimi K2.5 (long context)

## Response Format
```
Available models:

1. MiniMax M2.5 — Default, crons, quick tasks (free)
2. GPT-5.4 — Coding, agentic work
3. GPT-5.4 Pro — Maximum performance
4. GPT-5.3 Codex — Legacy coding
5. Claude Opus 4.6 — Deep strategy, CVs
6. Claude Sonnet 4.6 — Drafting, content
7. Claude Haiku 4.5 — Fast, lightweight
8. Kimi K2.5 — Long context

Reply with the number to switch.
```

## After user picks
Extract the number, map to model, respond with "/model [model]" command.
