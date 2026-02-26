# Tools & Methods Knowledge Bank

*Auto-indexed by QMD. Search with: memory_search("framework method [topic]")*

---

## Least-to-Most + Plan-and-Solve Prompting | 2026-02-26
**Source:** Prompt Guy newsletter (thinkaiprompt.beehiiv.com)
**Type:** Newsletter / Technique Guide

**Key Insights:**
- Complex single prompts spread attention across all parts, producing breadth without depth
- Task overload: AI covers everything in the same thin layer
- Least-to-Most: List sub-problems first, solve sequentially, paste previous outputs as context
- Plan-and-Solve: Exact phrasing matters — "let's first understand the problem fully and make a plan" outperforms standard "think step by step"
- The sequencing is the skill, not the individual prompt

**Least-to-Most Template:**
- Phase 1: "I need to accomplish [task]. List the sub-problems in order. Don't solve yet."
- Phase 2: "Now solve sub-problem 1 only. Specific and thorough. Output feeds next."

**Plan-and-Solve Template:**
- Task: [specific]
- Context: [background + constraints]
- Instructions: "Let's first understand the problem fully and make a plan. Then carry out step by step."

**Actionable for Ahmed:**
- Apply to agent task design (CV Optimizer, Job Hunter, Researcher, Content Creator)
- Better prompt sequences = better agent outputs
- Use for LinkedIn content frameworks, job application analysis, research synthesis
- Next module covers Tree-of-Thought for multi-path reasoning

**Tags:** #prompting #ai-techniques #workflow-design #agent-optimization

---

## Save Thousands on OpenClaw: Claude Subscription Instead of APIs | 2026-02-26
**Source:** YouTube (Andrew from Cloud Code meetup + Caleb Hodes from God Mode)
**Type:** Video / Tutorial

**Key Insights:**
- Use Claude subscriptions ($20-$200/month) instead of pay-per-token API fees
- Connect Claude Code (VS Code extension) to your subscription token
- Process: Install Claude Code in VS Code → Get token from Anthropic → Nuke old API keys → Reconnect OpenClaw to use subscription
- OpenClaw has 430,000 lines of code, so switching LLMs can be complicated (need to nuke old configs)
- Can use Sonnet or Opus 4.6 with the subscription
- $20/month plan works for demos, $200/month for heavy use
- This bypasses API token pay-per-token pricing

**Actionable for Ahmed:**
- Consider switching from MiniMax pay-per-token to Claude subscription for cost predictability
- Current MiniMax: $40/mo + API usage
- Claude subscription: $20-$200/month flat, unlimited use within limit
- Alternative: Keep MiniMax for daily ops, use Claude subscription for heavy tasks

---

## Using Claude Subscription with OpenClaw - Full Guide | 2026-02-26
**Source:** The Next New Thing (Andrew Warner) - n.thenextnewthing.ai
**Type:** Tutorial / Guide

**Key Insights:**
- Use Claude Max subscription ($20-$200/month) instead of pay-per-token Anthropic API
- Step-by-step: Get token → Nuke API keys → Add OAuth → Restart → Set Opus 4.6 as default
- VS Code required (free download)
- Process:
  1. Terminal: `claude setup-token` to get token
  2. VS Code: Nuke old API keys (delete ~/.openclaw/auth-profiles.json, remove ANTHROPIC_API_KEY from .env)
  3. Terminal: `openclaw models auth add` → select anthropic → paste token
  4. Restart gateway: `openclaw gateway restart`
  5. Edit openclaw.json to add Opus 4.6 with proper config (baseUrl WITHOUT /v1)
- baseUrl must be "https://api.anthropic.com" (no /v1)
- Set agents.defaults.model.primary to "anthropic/claude-opus-4-6"

**Actionable for Ahmed:**
- Could switch from MiniMax to Claude subscription for cost predictability
- Would give unlimited Opus/Sonnet usage within $200/month
- Alternative: Keep MiniMax for cheap tasks, Claude subscription for heavy Opus work

**Tags:** #claude #subscription #costoptimization #openclaw #anthropic

---

## Using OpenAI Subscription with OpenClaw | 2026-02-26
**Source:** The Next New Thing (Andrew Warner)
**Type:** Video / Tutorial

**Key Insights:**
- Anthropic Claude subscriptions are NOT allowed with OpenClaw (official as of Feb 18, 2026)
- OpenAI ChatGPT subscriptions ARE allowed
- Use $20/month or $200/month ChatGPT Pro instead of pay-per-token API
- Two simple commands to switch:
  1. `openclaw onboard --auth-choice openai-codex`
  2. `openclaw models set openai-codex/gpt-5.3-codex`
- Verify with: `openclaw models status --plain`
- Why use VS Code for config changes: safer than doing it inside OpenClaw (avoids "self-surgery" issues)
- God Mode (Caleb Hodes' company) helps entrepreneurs set this up as a concierge service

**Pricing Comparison:**
- OpenAI subscription: $20/month (Plus) or $200/month (Pro)
- Anthropic subscription: NOT ALLOWED anymore
- API pricing: Pay-per-token (can get expensive)

**Actionable for Ahmed:**
- Could switch to OpenAI subscription for cost predictability
- Keep MiniMax for cheap daily ops, use OpenAI for GPT-4o/GPT-5 when needed
- Alternative to Claude subscription (which is banned)

**Tags:** #openai #chatgpt #subscription #openclaw #costoptimization

<!-- end -->
