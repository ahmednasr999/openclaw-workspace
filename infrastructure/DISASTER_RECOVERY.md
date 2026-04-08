# NASR System Disaster Recovery Guide

**Last Updated:** 2026-02-25  
**Purpose:** Rebuild Ahmed Nasr's entire OpenClaw AI assistant system from scratch on ANY new machine (VPS, Mac Mini, etc.)  
**Time Estimate:** 45-60 minutes for full setup  
**Result:** 100% identical to current production system

---

## Prerequisites

- A fresh Ubuntu 24.04+ machine (VPS or local) with at least 8GB RAM, 40GB disk
- Root/sudo access
- Internet connection
- Access to Ahmed's GitHub account (ahmednasr999)
- Access to Ahmed's Google account (ahmednasr999@gmail.com) for OAuth re-auth
- Tailscale account login
- Telegram Bot Father token (stored in this guide)

---

## Phase 1: Base System (10 min)

### 1.1 System Update

```bash
apt update && apt upgrade -y
```

### 1.2 Install NVM + Node.js 22

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.bashrc
nvm install 22
nvm alias default 22
node -v  # Should show v22.x.x
```

### 1.3 Install System Packages

```bash
# PDF generation (XeLaTeX)
apt install -y texlive-xetex texlive-latex-extra texlive-fonts-recommended texlive-latex-recommended texlive-pictures texlive-plain-generic

# Document conversion
apt install -y pandoc

# Browser automation
apt install -y chromium-browser chromium-chromedriver

# Python (should already be installed)
apt install -y python3 python3-pip

# Utilities
apt install -y jq fzf htop trash-cli fuser net-tools
```

### 1.4 Install Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --ssh
# Login with Ahmed's Tailscale account when prompted
```

### 1.5 Install Go Binaries

```bash
# gog (Google Workspace CLI)
# Check latest release at: https://github.com/pomdtr/gog/releases
# Download the Linux amd64 binary
curl -L https://github.com/pomdtr/gog/releases/download/v0.11.0/gog_linux_amd64 -o /usr/local/bin/gog
chmod +x /usr/local/bin/gog

# himalaya (Email CLI)
# Check latest at: https://github.com/pimalaya/himalaya/releases
curl -L https://github.com/pimalaya/himalaya/releases/download/v1.1.0/himalaya-v1.1.0-x86_64-linux.tar.gz | tar xz -C /usr/local/bin/
chmod +x /usr/local/bin/himalaya
```

### 1.6 Install Python Dependencies

```bash
pip3 install google-auth google-auth-oauthlib
```

---

## Phase 2: OpenClaw Installation (5 min)

### 2.1 Install OpenClaw

```bash
npm install -g openclaw@2026.2.24
```

### 2.2 Install NPM Global Packages

```bash
npm install -g @moona3k/excalidraw-export@0.2.1
npm install -g @steipete/summarize@0.11.1
npm install -g @tobilu/qmd@1.0.7
npm install -g agent-content-pipeline@0.2.3
npm install -g clawhub@0.6.1
npm install -g chrome-devtools-mcp@0.17.3
npm install -g excalidraw-mcp@1.0.0
npm install -g googleapis@171.4.0
npm install -g markdown-pdf@11.0.0
npm install -g mcp-diagram-generator@1.1.1
npm install -g mcporter@0.7.3
npm install -g pm2@6.0.14
npm install -g puppeteer@24.37.5
npm install -g puppeteer-core@24.37.3
npm install -g opencode-ai@1.1.4
npm install -g bun@1.3.9
```

### 2.3 Run OpenClaw Onboard

```bash
openclaw onboard
# Follow the wizard:
# - Interface: Telegram
# - Bot token: 8213291111:AAHCk2J4XIRQaTsBkACl_Xpla7LFvVx1304
# - Default model: minimax-portal/MiniMax-M2.5
# - Allowed Telegram users: 866838380 (Ahmed's chat ID)
```

---

## Phase 3: Restore Configuration (10 min)

### 3.1 Clone Config Repo

```bash
cd /root/.openclaw
# Initialize git if not already
git init
git remote add origin https://github.com/ahmednasr999/openclaw-config.git
git fetch origin
git checkout -f master
```

**Important:** This restores:
- `openclaw.json` (all auth profiles, model configs, browser settings)
- `cron/jobs.json` (all 13 cron jobs)
- `agents/main/agent/models.json` (model routing)

### 3.2 Clone Workspace Repo

```bash
cd /root/.openclaw/workspace
git init
git remote add origin https://github.com/ahmednasr999/openclaw-nasr.git
git fetch origin
git checkout -f master
```

**This restores:**
- All memory files (MEMORY.md, daily logs, active tasks, knowledge bank)
- All CVs and job pipeline data
- SOUL.md, AGENTS.md, USER.md, GOALS.md, TOOLS.md, HEARTBEAT.md
- All scripts (job-radar, backup, morning-brief, etc.)
- All skills (30+ workspace skills)
- Infrastructure backup (systemd services, package manifest)
- Post-mortem reports and documentation

### 3.3 Re-enter API Keys

API keys are NOT stored in Git (security). You must re-enter them:

```bash
# Anthropic (Claude)
openclaw config set auth.profiles.anthropic:manual.apiKey "sk-ant-XXXXX"

# MiniMax Portal (OAuth - re-authenticate)
openclaw auth login minimax-portal

# Moonshot (Kimi)
openclaw config set auth.profiles.moonshot:default.apiKey "XXXXX"

# OpenAI Codex (OAuth - re-authenticate)
openclaw auth login openai-codex
```

**Where to find the keys:**
- Anthropic: https://console.anthropic.com/settings/keys
- MiniMax: https://www.minimax.io (OAuth flow)
- Moonshot: https://platform.moonshot.cn/console/api-keys
- Codex: OAuth via OpenAI

### 3.4 Re-enter Tavily API Key

Set in environment or config:
```bash
# Key: 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
export TAVILY_API_KEY="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"
```

---

## Phase 4: Systemd Services (5 min)

### 4.1 Install Service Files

```bash
mkdir -p /root/.config/systemd/user/

# Copy from backed-up infrastructure directory
cp /root/.openclaw/workspace/infrastructure/systemd/openclaw-gateway.service /root/.config/systemd/user/
cp /root/.openclaw/workspace/infrastructure/systemd/calendar-webhook.service /root/.config/systemd/user/
cp /root/.openclaw/workspace/infrastructure/systemd/github-webhook.service /root/.config/systemd/user/
cp /root/.openclaw/workspace/infrastructure/systemd/gog-calendar-watch.service /root/.config/systemd/user/
cp /root/.openclaw/workspace/infrastructure/systemd/gog-gmail-watch.service /root/.config/systemd/user/

# Reload systemd
systemctl --user daemon-reload
```

### 4.2 Enable and Start Services

```bash
# Main gateway (MUST start first)
systemctl --user enable openclaw-gateway.service
systemctl --user start openclaw-gateway.service

# Calendar webhook
systemctl --user enable calendar-webhook.service
systemctl --user start calendar-webhook.service

# Verify all services
systemctl --user status openclaw-gateway.service
systemctl --user status calendar-webhook.service
```

### 4.3 Enable Lingering (Keep Services Running After Logout)

```bash
loginctl enable-linger root
```

---

## Phase 5: System Crontab (2 min)

### 5.1 Restore Crontab

```bash
crontab /root/.openclaw/workspace/infrastructure/system-crontab.txt
crontab -l  # Verify
```

**This restores 9 system cron jobs:**
- Daily backup (8 PM UTC)
- Monthly archive (8 PM UTC, 1st of month)
- Daily snapshot (11 PM UTC)
- Retention: backups, snapshots, caches
- Disk health check (9 AM UTC)
- Job radar (6 AM UTC)
- Morning brief (6 AM UTC)

---

## Phase 6: Google OAuth Re-authentication (5 min)

### 6.1 Gmail + Calendar

```bash
# Re-authenticate gog for ahmednasr999@gmail.com
export GOG_KEYRING_PASSWORD=pass@123
gog auth login --account ahmednasr999@gmail.com

# Test Gmail
gog gmail list --account ahmednasr999@gmail.com --max 3

# Test Calendar
gog calendar list --account ahmednasr999@gmail.com
```

### 6.2 Google OAuth Credentials

The OAuth client credentials for the `nasr-agent` project:
- **Client ID:** 438071512086
- **Project:** nasr-agent
- **Console:** https://console.cloud.google.com/apis/credentials?project=nasr-agent

You may need to re-download the OAuth JSON and place it at:
```bash
/root/.openclaw/workspace/config/ahmed-google.json
```

---

## Phase 7: Tailscale Serve Configuration (2 min)

### 7.1 Configure Serve Proxy

```bash
# Proxy gateway (main)
tailscale serve --bg --https=443 http://127.0.0.1:18789

# Proxy Gmail webhook
tailscale funnel --bg --https=8788 http://127.0.0.1:8788
```

### 7.2 Verify

```bash
tailscale serve status
```

**Expected:**
```
https://[hostname].tail945bbc.ts.net (tailnet only)
|-- /             proxy http://127.0.0.1:18789
|-- /gmail-pubsub proxy http://127.0.0.1:8788
```

---

## Phase 8: Memory Index Rebuild (2 min)

### 8.1 Rebuild QMD Index

```bash
openclaw memory index
# This re-indexes all memory/*.md files for semantic search
```

### 8.2 Verify

```bash
openclaw memory search "job pipeline"
# Should return results from memory files
```

---

## Phase 9: Verification Checklist (5 min)

Run these checks to confirm everything works:

```bash
echo "=== 1. Gateway ==="
openclaw gateway status

echo ""
echo "=== 2. Telegram ==="
openclaw message send --target "telegram:866838380" --message "Recovery test: $(date)"

echo ""
echo "=== 3. Cron Jobs ==="
openclaw cron list

echo ""
echo "=== 4. Memory Search ==="
openclaw memory search "Delphi interview"

echo ""
echo "=== 5. Git Repos ==="
cd /root/.openclaw/workspace && git status && git remote -v
cd /root/.openclaw && git status && git remote -v

echo ""
echo "=== 6. Services ==="
systemctl --user list-units --type=service --state=running

echo ""
echo "=== 7. Tailscale ==="
tailscale serve status

echo ""
echo "=== 8. System Health ==="
free -m
df -h /
```

### Expected Results:

| Check | Expected |
|-------|----------|
| Gateway | active (running), port 18789 |
| Telegram | Message delivered |
| Cron | 13 jobs listed |
| Memory | Results for "Delphi interview" |
| Git (workspace) | Clean, remote = openclaw-nasr |
| Git (config) | Clean, remote = openclaw-config |
| Services | openclaw-gateway + calendar-webhook running |
| Tailscale | Serve enabled on 443 + 8788 |
| Memory | < 2GB used |
| Disk | < 50% used |

---

## Phase 10: Post-Recovery Tasks

After the system is verified:

1. **Send test message** to Telegram and confirm NASR responds
2. **Check heartbeat** fires within 1 hour
3. **Run `openclaw doctor`** and fix any warnings
4. **Wait for next cron cycle** to confirm cron jobs fire
5. **Update MEMORY.md** with migration date and new hostname

---

## Credentials Quick Reference

**KEEP THIS SECURE. These are the credentials needed for full recovery.**

| Credential | Where to Get It |
|-----------|----------------|
| Anthropic API Key | https://console.anthropic.com/settings/keys |
| Telegram Bot Token | `8213291111:AAHCk2J4XIRQaTsBkACl_Xpla7LFvVx1304` |
| Telegram Chat ID | `866838380` |
| MiniMax Portal | OAuth login at https://www.minimax.io |
| Moonshot API Key | https://platform.moonshot.cn/console/api-keys |
| Tavily API Key | `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` |
| GitHub | https://github.com/ahmednasr999 (repos: openclaw-nasr, openclaw-config) |
| Google OAuth | Project: nasr-agent (438071512086) |
| GOG Keyring Password | `pass@123` |
| Tailscale | Login via Ahmed's account |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│                   VPS (8GB RAM)                  │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │         OpenClaw Gateway (port 18789)        │ │
│  │  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │ │
│  │  │ Telegram  │ │   Cron   │ │  Heartbeat  │ │ │
│  │  │   Bot     │ │ 13 Jobs  │ │  (hourly)   │ │ │
│  │  └──────────┘ └──────────┘ └─────────────┘ │ │
│  │  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │ │
│  │  │  Agent   │ │  Memory  │ │   Browser   │ │ │
│  │  │  (NASR)  │ │  (QMD)   │ │  (18791)    │ │ │
│  │  └──────────┘ └──────────┘ └─────────────┘ │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  ┌──────────────┐ ┌──────────────┐               │
│  │ Calendar     │ │ Gmail        │               │
│  │ Webhook      │ │ Watcher      │               │
│  │ (python)     │ │ (gog)        │               │
│  └──────────────┘ └──────────────┘               │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │              Tailscale Serve                  │ │
│  │  443 → 18789 (gateway)                        │ │
│  │  8788 → 8788 (gmail pubsub)                   │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │   Git    │ │  System  │ │    Backups       │ │
│  │ 2 repos  │ │ Crontab  │ │ daily+retention  │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## File Locations Summary

| What | Path |
|------|------|
| OpenClaw config | `/root/.openclaw/openclaw.json` |
| Agent models | `/root/.openclaw/agents/main/agent/models.json` |
| Cron jobs | `/root/.openclaw/cron/jobs.json` |
| Workspace | `/root/.openclaw/workspace/` |
| Memory files | `/root/.openclaw/workspace/memory/` |
| Knowledge bank | `/root/.openclaw/workspace/memory/knowledge/` |
| Scripts | `/root/.openclaw/workspace/scripts/` |
| Skills | `/root/.openclaw/workspace/skills/` |
| Systemd services | `/root/.config/systemd/user/` |
| Device identity | `/root/.openclaw/identity/` |
| Telegram config | `/root/.openclaw/credentials/` |
| Google OAuth | `/root/.openclaw/workspace/config/ahmed-google.json` |
| QMD index | `/root/.openclaw/agents/main/qmd/` |

---

## Recovery Time Objective (RTO)

| Phase | Time | Cumulative |
|-------|------|-----------|
| Base system | 10 min | 10 min |
| OpenClaw + packages | 5 min | 15 min |
| Config + workspace restore | 10 min | 25 min |
| Systemd services | 5 min | 30 min |
| Crontab | 2 min | 32 min |
| Google re-auth | 5 min | 37 min |
| Tailscale | 2 min | 39 min |
| Memory re-index | 2 min | 41 min |
| Verification | 5 min | 46 min |

**Total: ~46 minutes to full recovery.**

---

**This guide is version-controlled in the workspace Git repo.**  
**Path:** `infrastructure/DISASTER_RECOVERY.md`
