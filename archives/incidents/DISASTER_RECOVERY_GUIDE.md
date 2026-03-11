# OpenClaw Full System Recovery Guide

**Created:** 2026-02-25  
**Purpose:** Rebuild the EXACT current system from scratch on any new VPS, Mac, or machine.  
**Estimated Time:** 45-60 minutes  
**Requires:** Ubuntu 24.04+ (or macOS), root/sudo access, internet connection

---

## Prerequisites

Before you start, you need these credentials (stored securely, NOT in GitHub):

| Credential | Where to Get |
|---|---|
| GitHub Personal Access Token | github.com/settings/tokens |
| Anthropic API Key | console.anthropic.com |
| MiniMax OAuth credentials | minimax portal |
| Moonshot API Key | platform.moonshot.cn |
| Telegram Bot Token | @BotFather on Telegram |
| Google OAuth (nasr-agent project) | console.cloud.google.com (project 438071512086) |
| Tailscale auth key | login.tailscale.com/admin/settings/keys |
| SSH private key (id_ed25519) | Backup from current system |
| GOG_KEYRING_PASSWORD | pass@123 |

---

## Phase 1: Base System (10 min)

### 1.1 Update System

```bash
apt update && apt upgrade -y
```

### 1.2 Install System Dependencies

```bash
apt install -y \
  git curl wget unzip jq \
  build-essential \
  python3 python3-pip python3-venv \
  pandoc \
  texlive-xetex texlive-latex-extra texlive-fonts-recommended \
  chromium-browser chromium-chromedriver \
  fuser lsof net-tools \
  trash-cli
```

### 1.3 Install NVM + Node.js v22

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
source ~/.bashrc
nvm install 22.22.0
nvm use 22.22.0
nvm alias default 22.22.0
node -v  # Should show v22.22.0
```

### 1.4 Install Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --authkey=YOUR_TAILSCALE_AUTH_KEY
```

### 1.5 Install Go Tools (GOG + Himalaya)

```bash
# GOG (Google Workspace CLI)
curl -sSL https://github.com/bytebutcher/gog/releases/latest/download/gog_linux_amd64.tar.gz | tar xz -C /usr/local/bin/

# Himalaya (Email CLI)
curl -sSL https://github.com/pimalaya/himalaya/releases/latest/download/himalaya-x86_64-linux.tar.gz | tar xz -C /usr/local/bin/
```

---

## Phase 2: OpenClaw Installation (5 min)

### 2.1 Install OpenClaw

```bash
npm install -g openclaw@2026.2.24
```

### 2.2 Run Initial Setup

```bash
openclaw onboard
```

Follow the wizard. When asked:
- **Mode:** Local
- **Telegram Bot Token:** Paste your bot token
- **Default Model:** minimax-portal/MiniMax-M2.5

---

## Phase 3: Restore From GitHub (5 min)

### 3.1 Clone Workspace Repo

```bash
# Remove the default workspace
rm -rf /root/.openclaw/workspace

# Clone your workspace
git clone https://github.com/ahmednasr999/openclaw-nasr.git /root/.openclaw/workspace
```

### 3.2 Restore Config Repo

```bash
# Back up any auto-generated config
cp /root/.openclaw/openclaw.json /root/.openclaw/openclaw.json.auto-generated

# Clone config (careful: don't overwrite identity/)
cd /tmp
git clone https://github.com/ahmednasr999/openclaw-config.git
cp /tmp/openclaw-config/openclaw.json /root/.openclaw/openclaw.json
cp /tmp/openclaw-config/cron/jobs.json /root/.openclaw/cron/jobs.json
cp -r /tmp/openclaw-config/agents/ /root/.openclaw/agents/
rm -rf /tmp/openclaw-config
```

### 3.3 Set Git Remotes (if needed)

```bash
cd /root/.openclaw/workspace
git remote set-url origin https://github.com/ahmednasr999/openclaw-nasr.git

cd /root/.openclaw
git init
git remote add origin https://github.com/ahmednasr999/openclaw-config.git
```

---

## Phase 4: Install NPM Global Packages (5 min)

```bash
npm install -g \
  @moona3k/excalidraw-export@0.2.1 \
  @steipete/summarize@0.11.1 \
  @tobilu/qmd@1.0.7 \
  agent-content-pipeline@0.2.3 \
  clawhub@0.6.1 \
  chrome-devtools-mcp@0.17.3 \
  excalidraw-mcp@1.0.0 \
  googleapis@171.4.0 \
  markdown-pdf@11.0.0 \
  mcp-diagram-generator@1.1.1 \
  mcporter@0.7.3 \
  pm2@6.0.14 \
  puppeteer-core@24.37.3 \
  puppeteer@24.37.5 \
  opencode-ai@1.1.4
```

---

## Phase 5: Restore API Keys & Credentials (10 min)

### 5.1 OpenClaw Config (openclaw.json)

The config was restored from GitHub in Phase 3. But you MUST re-enter API keys:

```bash
# Edit the config
nano /root/.openclaw/openclaw.json

# Find and replace these placeholder values:
# - anthropic apiKey: paste your Anthropic API key
# - Telegram botToken: paste your bot token
# - moonshot apiKey: paste your Moonshot key
```

### 5.2 Re-authenticate MiniMax Portal OAuth

```bash
openclaw auth login minimax-portal
# Follow the browser OAuth flow
```

### 5.3 Re-authenticate Google Workspace

```bash
# Copy your Google OAuth credentials
mkdir -p /root/.openclaw/workspace/config
# Place ahmed-google.json in config/ (from your secure backup)

# Re-authenticate GOG
export GOG_KEYRING_PASSWORD=pass@123
gog auth login --account ahmednasr999@gmail.com
```

### 5.4 Restore Himalaya Config

```bash
mkdir -p /root/.config/himalaya
# Copy from the system-config backup in workspace:
cp /root/.openclaw/workspace/system-config/himalaya/config.toml /root/.config/himalaya/
```

### 5.5 Restore GOG Config

```bash
mkdir -p /root/.config/gog
cp /root/.openclaw/workspace/system-config/gog/config.json /root/.config/gog/
```

### 5.6 Restore SSH Keys

```bash
mkdir -p /root/.ssh && chmod 700 /root/.ssh
# Copy your id_ed25519 and id_ed25519.pub from secure backup
chmod 600 /root/.ssh/id_ed25519
chmod 644 /root/.ssh/id_ed25519.pub
```

---

## Phase 6: Systemd Services (5 min)

### 6.1 Install All Service Files

```bash
mkdir -p /root/.config/systemd/user

# Copy from workspace backup
cp /root/.openclaw/workspace/system-config/systemd/*.service /root/.config/systemd/user/

# Reload systemd
systemctl --user daemon-reload
```

### 6.2 Enable and Start Services

```bash
# Enable all services (auto-start on boot)
systemctl --user enable openclaw-gateway.service
systemctl --user enable calendar-webhook.service
systemctl --user enable github-webhook.service

# Start the gateway
systemctl --user start openclaw-gateway.service

# Enable lingering (keeps services running after logout)
loginctl enable-linger root
```

### 6.3 Verify Gateway

```bash
systemctl --user status openclaw-gateway.service
# Should show: active (running)

openclaw gateway status
# Should show: Runtime: running
```

---

## Phase 7: Cron Jobs (2 min)

### 7.1 Restore Crontab

```bash
crontab /root/.openclaw/workspace/system-config/crontab.txt
crontab -l  # Verify
```

**Expected crontab (9 entries):**

```
0 20 * * * /root/.openclaw/workspace/scripts/daily-backup.sh
0 20 1 * * /root/.openclaw/workspace/scripts/archive-daily-notes.sh
0 23 * * * /root/.openclaw/workspace/scripts/daily-snapshot.sh
30 20 * * * /root/.openclaw/workspace/scripts/retention-backups.sh
30 23 * * * /root/.openclaw/workspace/scripts/retention-snapshots.sh
15 3 * * * /root/.openclaw/workspace/scripts/retention-caches.sh
0 9 * * * /root/.openclaw/workspace/scripts/disk-health-check.sh
0 6 * * * /root/.openclaw/workspace/scripts/job-radar.sh
0 6 * * * /root/.openclaw/workspace/scripts/morning-brief.sh
```

---

## Phase 8: Tailscale Serve (2 min)

### 8.1 Configure Tailscale Serve

```bash
# Proxy gateway to Tailscale
tailscale serve --bg http://127.0.0.1:18789

# Proxy Gmail webhook
tailscale serve --bg --set-path /gmail-pubsub http://127.0.0.1:8788
```

### 8.2 Verify

```bash
tailscale serve status
# Should show:
# https://YOUR-HOSTNAME.tail*.ts.net
# |-- /             proxy http://127.0.0.1:18789
# |-- /gmail-pubsub proxy http://127.0.0.1:8788
```

---

## Phase 9: QMD Memory Index (2 min)

### 9.1 Re-index Memory

```bash
openclaw memory index
# This rebuilds the semantic search index for all memory/*.md files
```

---

## Phase 10: Verification Checklist (5 min)

Run each of these and confirm output:

```bash
# 1. Gateway running
openclaw gateway status | grep "Runtime: running"

# 2. Telegram connected
openclaw message send --target "telegram:866838380" --message "✅ New system online — $(hostname) — $(date)"

# 3. Cron jobs loaded
openclaw cron list | wc -l  # Should be 13+

# 4. Memory search works
openclaw memory search "job search"

# 5. Git repos connected
cd /root/.openclaw/workspace && git remote -v | grep openclaw-nasr
cd /root/.openclaw && git remote -v | grep openclaw-config

# 6. Node version correct
node -v  # v22.22.0

# 7. All systemd services
systemctl --user list-units --type=service | grep -E "openclaw|calendar|github|gog"

# 8. No delivery queue stuck
ls /root/.openclaw/delivery-queue/*.json 2>/dev/null | wc -l  # Should be 0

# 9. Tailscale accessible
curl -s https://$(tailscale status --json | jq -r '.Self.DNSName')/ | head -1

# 10. Scripts executable
ls -la /root/.openclaw/workspace/scripts/*.sh | grep "^-rwx"  # All should have execute
```

---

## Phase 11: Post-Setup Housekeeping

### 11.1 Run OpenClaw Doctor

```bash
openclaw doctor --repair
```

### 11.2 First Message Test

Open Telegram and send a message to @NasrOpenClawnBot. You should get a response from NASR.

### 11.3 Set Up Git Credentials

```bash
git config --global user.name "Ahmed Nasr"
git config --global user.email "ahmednasr999@gmail.com"
git config --global credential.helper store
```

---

## Critical Files NOT in GitHub

These must be backed up separately (encrypted recommended):

| File | Location | Why Not in Git |
|---|---|---|
| Anthropic API Key | openclaw.json | Security |
| Telegram Bot Token | openclaw.json | Security |
| Moonshot API Key | openclaw.json | Security |
| Google OAuth tokens | config/ahmed-google.json | Security |
| SSH private key | ~/.ssh/id_ed25519 | Security |
| Device identity | ~/.openclaw/identity/ | Unique per install |
| Telegram pairing | ~/.openclaw/credentials/ | Unique per install |
| Himalaya config | ~/.config/himalaya/config.toml | Contains passwords |
| GOG config | ~/.config/gog/config.json | Contains tokens |

**Recommendation:** Keep an encrypted backup of these files in a secure location (e.g., 1Password, encrypted USB, private cloud storage).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                    VPS (8GB RAM)                 │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │     Systemd: openclaw-gateway.service    │    │
│  │     Port: 18789 (loopback)               │    │
│  │     KillMode: mixed                      │    │
│  │     TimeoutStopSec: 15                   │    │
│  └────────────┬────────────────────────────┘    │
│               │                                  │
│  ┌────────────▼────────────────────────────┐    │
│  │         OpenClaw Gateway (Node.js)       │    │
│  │                                          │    │
│  │  Channels: Telegram (@NasrOpenClawnBot)  │    │
│  │  Agents: main (NASR)                     │    │
│  │  Models: MiniMax M2.5 (default)          │    │
│  │          Opus 4.6 / Sonnet 4.6 / Haiku   │    │
│  │          Kimi K2.5                        │    │
│  │  Cron: 13 jobs                            │    │
│  │  Heartbeat: 1hr interval                  │    │
│  │  Memory: QMD (BM25 + vectors)             │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Calendar │  │ GitHub   │  │ Gmail    │      │
│  │ Webhook  │  │ Webhook  │  │ Watcher  │      │
│  │ (Python) │  │ (Python) │  │ (GOG)    │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │           Tailscale (VPN/Serve)           │    │
│  │  https://srv*.tail*.ts.net → :18789       │    │
│  │  /gmail-pubsub → :8788                    │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │           GitHub Repos                    │    │
│  │  openclaw-nasr (workspace)                │    │
│  │  openclaw-config (config)                 │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  System Crontab: 9 jobs                          │
│  Scripts: /root/.openclaw/workspace/scripts/     │
│  Skills: 30 workspace + 4 custom                 │
└─────────────────────────────────────────────────┘
```

---

## Version Reference

| Component | Version | Notes |
|---|---|---|
| Ubuntu | 24.04+ (6.17 kernel) | Or macOS equivalent |
| Node.js | 22.22.0 | Via NVM |
| OpenClaw | 2026.2.24 | npm global |
| Python | 3.13.7 | System |
| Tailscale | 1.94.1 | Apt |
| GOG | 0.11.0 | Binary |
| Himalaya | 1.1.0 | Binary |
| PM2 | 6.0.14 | npm global |
| Pandoc | 3.1.11 | Apt |
| XeLaTeX | 2024 (texlive) | Apt |
| Chromium | Snap | Apt |

---

## Troubleshooting

**Gateway won't start:**
```bash
journalctl --user -u openclaw-gateway.service -n 50
fuser -k 18789/tcp  # Kill anything on the port
systemctl --user restart openclaw-gateway.service
```

**Telegram not responding:**
```bash
openclaw gateway status  # Check if running
grep "telegram" /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | tail -5
```

**Memory search returns nothing:**
```bash
openclaw memory index  # Re-index
```

**Cron jobs not firing:**
```bash
openclaw cron list  # Check status
openclaw cron run JOB_ID  # Force run one
```

**Gmail watcher fails:**
```bash
export GOG_KEYRING_PASSWORD=pass@123
gog gmail watch --account ahmednasr999@gmail.com
```

---

**This guide assumes a clean Ubuntu 24.04 VPS. For macOS, replace `apt` with `brew`, systemd services with launchd plists, and adjust paths accordingly.**

**Estimated total recovery time: 45-60 minutes (with all credentials ready).**
