# Skills Installed from skills.sh

## Overview

Installed 4 high-quality skills from the Agent Skills Directory (skills.sh) for job search automation, content creation, and marketing.

## Installed Skills

### 1. browser-use 🟢 (32K installs)
**Purpose:** Browser automation for web testing, form filling, screenshots, and data extraction

**What it does:**
- Navigate websites automatically
- Fill forms (job applications, LinkedIn messages)
- Take screenshots
- Extract information from web pages
- Maintain browser sessions across commands

**Installation:**
```bash
curl -fsSL https://browser-use.com/cli/install.sh | bash
```

**Location:** `~/.agents/skills/browser-use/`

**Use for:**
- Automating job applications
- Filling out LinkedIn forms
- Extracting job postings
- Automating repetitive web tasks

---

### 2. copywriting 🟠 (15K installs)
**Purpose:** Marketing copywriting frameworks and best practices

**What it does:**
- Provides proven copywriting frameworks
- Guides on writing compelling content
- Marketing psychology principles
- Conversion-optimized writing

**Location:** `~/.agents/skills/copywriting/`

**Use for:**
- LinkedIn posts that convert
- Job application emails
- Professional communications
- Marketing content

---

### 3. marketing-psychology 🟠 (11K installs)
**Purpose:** Understanding psychological triggers that drive engagement and action

**What it does:**
- Psychological principles for marketing
- Behavioral triggers
- Audience motivation analysis
- Conversion psychology

**Location:** `~/.agents/skills/marketing-psychology/`

**Use for:**
- Understanding what makes content shareable
- LinkedIn post optimization
- Job search messaging
- Professional positioning

---

### 4. remote-browser 🟢
**Purpose:** Remote browser sessions for cloud-based automation

**What it does:**
- Sandboxed browser environments
- CI/CD compatible
- No local browser needed

**Location:** `~/.agents/skills/remote-browser/`

**Use for:**
- Cloud-based automation
- Testing in clean environments
- Resource-constrained systems

---

## Skill Locations

| Skill | Path | Symlink |
|-------|------|---------|
| browser-use | `~/.agents/skills/browser-use/` | ✅ `~/.claude/skills/` |
| remote-browser | `~/.agents/skills/remote-browser/` | ✅ `~/.claude/skills/` |
| copywriting | `~/.agents/skills/copywriting/` | ✅ `~/.claude/skills/` |
| marketing-psychology | `~/.agents/skills/marketing-psychology/` | ✅ `~/.claude/skills/` |

## Safety Verification

All skills verified from reputable sources:

| Skill | Author | Reputation |
|-------|--------|------------|
| browser-use | browser-use | ✅ Popular open source, 32K installs |
| copywriting | coreyhaines31 | ✅ Established skill author, 15K installs |
| marketing-psychology | coreyhaines31 | ✅ Same trusted author, 11K installs |
| remote-browser | browser-use | ✅ Same as browser-use |

## Usage Examples

### Browser Automation (job applications)
```bash
# Install browser-use CLI
curl -fsSL https://browser-use.com/cli/install.sh | bash

# Run automation
browser-use open https://linkedin.com/jobs
browser-use fill --form job-application ...
```

### Better LinkedIn Posts
```bash
# Use copywriting skill for better posts
# The skill provides frameworks for:
# - Hook writing
# - CTA optimization  
# - Engagement triggers
```

## Next Steps

1. Install browser-use CLI: `curl -fsSL https://browser-use.com/cli/install.sh | bash`
2. Test browser automation
3. Use copywriting skill for LinkedIn posts
4. Apply marketing psychology to job search messaging

## Related Skills Available

From skills.sh (not installed but available):
- `seo-audit` - Check online visibility
- `content-strategy` - Content planning
- `social-content` - Social media content
- `find-skills` - Discover new skills

## References

- Skills Directory: https://skills.sh
- Browser Use: https://github.com/browser-use/browser-use
- Marketing Skills: https://github.com/coreyhaines31/marketingskills
