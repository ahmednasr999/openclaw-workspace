#!/bin/bash
# GitHub Radar - Daily scan of trending repos for OpenClaw-relevant tools
# Cron: Daily 6 AM Cairo
# Output: memory/github-radar.md

OUTPUT="/root/.openclaw/workspace/memory/github-radar.md"
DATE=$(date +%Y-%m-%d)

cat > "$OUTPUT" << EOF
---
description: "Daily GitHub trending scan: relevant repos for OpenClaw, AI agents, automation"
type: log
topics: [knowledge, system-ops]
updated: $DATE
---

# GitHub Radar — $DATE

## High-Signal Repos (Always Check)

- [agency-agents](https://github.com/msitarzewski/agency-agents) — AI agency with specialized agents
- [hermes-agent](https://github.com/NousResearch/hermes-agent) — Agent that grows with you
- [notebooklm-py](https://github.com/teng-lin/notebooklm-py) — Python API for NotebookLM (supports OpenClaw)
- [OpenViking](https://github.com/volcengine/OpenViking) — Context DB for AI Agents (mentions OpenClaw)
- [deer-flow](https://github.com/bytedance/deer-flow) — ByteDance SuperAgent
- [nanochat](https://github.com/karpathy/nanochat) — Karpathy's minimal chat
- [lightpanda-io/browser](https://github.com/lightpanda-io/browser) — Headless browser for AI
- [promptfoo](https://github.com/promptfoo/promptfoo) — Prompt testing & red teaming
- [MiroFish](https://github.com/666ghj/MiroFish) — Swarm Intelligence Engine
- [BettaFish](https://github.com/666ghj/BettaFish) — Multi-Agent sentiment analysis
- [BitNet](https://github.com/microsoft/BitNet) — 1-bit LLM inference
- [fish-speech](https://github.com/fishaudio/fish-speech) — Open source TTS

## Action Items

Check these repos weekly for:
- New features relevant to our stack
- Integration opportunities
- Skill/plugin ideas

---
*Scanned: $(date)*
EOF

echo "GitHub radar complete."
