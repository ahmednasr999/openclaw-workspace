# Larry's TikTok Automation System

*Source: @oliverhenry (Oliver Henry)*
*Tweet: https://x.com/oliverhenry/status/2022011925903667547*
*Date: Feb 12, 2026*

---

## The Results

| Metric | Value |
|--------|-------|
| Total views | 500K+ in one week |
| Top post | 234K views |
| Posts over 100K | 4 |
| MRR | $588/month |
| Subscribers | 108 paying |
| Cost per post | $0.50 (API) |
| Ollie's time per post | 60 seconds |

---

## Who is Larry?

OpenClaw agent running on:
- Old gaming PC (NVIDIA 2070 Super)
- Ubuntu Linux
- Claude (Anthropic) as brain

### Larry's Capabilities
- Own personality and memory that persists between conversations
- Access to read/write files on machine
- Generate images through OpenAI API
- Post to TikTok via Postiz
- Skill files that teach specific workflows
- Memory files for long-term learning

---

## The Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Agent | OpenClaw | Brain + identity + memory |
| Image generation | GPT-image-1.5 (OpenAI) | Create slideshow images |
| Video posting | Postiz | Schedule to TikTok as drafts |
| Skills | Custom markdown files | Workflow automation |
| Memory | Long-term memory files | Learn from failures |

---

## Hardware Requirements

| Spec | Minimum | Recommended |
|------|---------|-------------|
| RAM | 2GB | 4GB |
| CPU | 1-2 vCPU | Any |
| Storage | 20GB SSD | Any |
| GPU | Optional | NVIDIA (for local) |

> "Almost any spare computer, a Raspberry Pi, or cheap VPS will work"

---

## The Content Strategy

### Slideshow Format (TikTok's Sweet Spot)
- 6 slides exactly
- Text overlay on slide 1 with hook
- Story-style caption
- Max 5 hashtags

### Image Generation (GPT-image-1.5)
- Portrait orientation (1024x1536)
- "iPhone photo" + "realistic lighting" for authenticity
- Lock the architecture, change only the style

### Prompt Engineering
The key: lock everything except style.

**Example:**
```
iPhone photo of a small UK rental kitchen. Narrow galley style kitchen, 
roughly 2.5m x 4m. Shot from the doorway... 
**Beautiful modern country style. Sage green painted shaker cabinets...**
```

The bold part changes. Everything else stays identical across all 6 slides.

---

## The Posting Workflow

1. Larry generates images, adds text overlays, writes caption
2. Larry uploads to TikTok as draft via Postiz
3. Larry sends Ollie the caption in a message
4. Ollie picks trending sound, pastes caption, hits publish

### Why Drafts?
- Can't add music via API
- Trending sounds change constantly
- Manual step takes 60 seconds

---

## The Hook Formula (The Golden Rule)

> "[Another person] + [conflict or doubt] → showed them AI → they changed their mind"

| Hook | Views |
|------|-------|
| "My landlord said I can't change anything..." | 234K |
| "I showed my mum what AI thinks..." | 167K |
| "My landlord wouldn't let me decorate..." | 147K |

**What failed:**
- Self-focused hooks (about app features)
- Generic room descriptions
- Wrong image sizes

---

## How Larry Learns

### Skill Files
- Markdown documents that teach Larry specific workflows
- TikTok skill file: 500+ lines
- Contains every rule, formatting spec, lesson learned

### Memory Files
- Long-term memory persisting between sessions
- Every post, view count, insight gets logged
- References actual performance data for brainstorming

### The Loop
> "Every failure becomes a rule. Every success becomes a formula. He compounds."

---

## Lessons Learned (Failures)

### 1. Local Generation Failed
- Stable Diffusion image quality wasn't photorealistic enough
- API costs turned out to be tiny anyway ($0.50/post)
- **Lesson:** Don't waste time on inferior free options

### 2. Wrong Image Size
- Generated landscape (1536x1024) instead of portrait (1024x1536)
- Black bars killed engagement
- **Fix:** Always 1024x1536 portrait

### 3. Vague Prompts
- Windows moved between slides
- Rooms looked fake
- **Fix:** Obsessively specific architecture descriptions

### 4. Unreadable Text
- Font too small (5% instead of 6.5%)
- Positioned too high (hidden by TikTok UI)
- **Fix:** Test on actual phone before posting

### 5. Bad Hooks
- Self-focused: "Why does my flat look like..."
- **Fix:** Focus on other people's reactions

---

## OpenClaw Application

| Pattern | Your Current | Action |
|---------|-------------|--------|
| Skill files | ✅ lessons-learned.md | Add TikTok-style detailed rules |
| Memory files | ✅ active-tasks.md | Track performance metrics |
| Image generation | ❌ | Not needed for your use case |
| Social posting | ❌ | Could add for LinkedIn |

---

## Key Insight

> "The agent is only as good as its memory. Larry didn't start good. His first posts were honestly embarrassing. Wrong image sizes, unreadable text, hooks that nobody clicked on. But every failure became a rule. Every success became a formula. He compounds. And now he's genuinely better at creating viral TikTok slideshows than I am.

> That's the real unlock. Not the AI itself. The system you build around it."

---

## Related

- [[eval-suite/README.md]] - Skill evaluation framework
- [[memory/agent-tool-design-lessons.md]] - Agent tool design
- [[memory/openclaw-codex-swarm-setup.md]] - Elvis's swarm architecture

---

## Quote

> "I didn't design a single image. I didn't write a single caption. I barely even opened TikTok."
