# Social Media Content Extraction

Extract content from social media platforms. Always prefer free tools first, burn paid credits only when free fails.

## When to Use
- User shares any social media link (YouTube, Twitter/X, TikTok, Instagram, LinkedIn, Reddit, Facebook)
- Research tasks requiring social media content
- Content analysis of creators/influencers
- Extracting transcripts from video content

## Priority Chain (Always Follow This Order)

### 1. FREE first
### 2. PAID only if free fails

---

## YouTube
**Free → yt-dlp (always use this)**
```bash
bash scripts/youtube-transcript.sh "VIDEO_URL"
```
- Transcripts, metadata, subtitles
- No API key, no limits
- Some geo-restricted videos may fail

## Twitter/X

### Text tweets:
**Free → Composio Browser Tool** (slow, 2-3 min)
- Use `BROWSER_TOOL_CREATE_TASK` with the tweet URL
- Works reliably, just slow

**Paid → ScrapeCreators** (instant, 1 credit)
```bash
python3 scripts/scrapecreators.py twitter tweet "TWEET_URL"
```
- Use ONLY when speed matters or Browser Tool fails

### Video tweets:
**Free → yt-dlp**
```bash
yt-dlp --no-update --write-auto-sub --sub-lang en --skip-download --sub-format vtt "TWEET_URL"
```

## TikTok
**Free → Composio Browser Tool** (slow)
- Cloud IPs blocked by TikTok, yt-dlp won't work

**Paid → ScrapeCreators** (instant, 1 credit)
```bash
python3 scripts/scrapecreators.py tiktok transcript "TIKTOK_URL"
python3 scripts/scrapecreators.py tiktok profile "USERNAME"
```

## Instagram
**Free → Composio Browser Tool** (slow)
- yt-dlp Instagram extractor currently broken

**Paid → ScrapeCreators** (instant, 1 credit)
```bash
python3 scripts/scrapecreators.py instagram profile "USERNAME"
python3 scripts/scrapecreators.py instagram transcript "REEL_URL"
```

## LinkedIn
**Free → Composio LinkedIn tools** (already connected)
- Use for posting, profile info via existing Composio connection

**Paid → ScrapeCreators** (1 credit)
```bash
python3 scripts/scrapecreators.py linkedin profile "PROFILE_URL"
python3 scripts/scrapecreators.py linkedin company "COMPANY_URL"
python3 scripts/scrapecreators.py linkedin post "POST_URL"
```

## Reddit
**Free → yt-dlp** (video posts)
```bash
yt-dlp --no-update --skip-download --dump-json "REDDIT_URL"
```

**Free → web_fetch** (text posts)
- Use `web_fetch` tool to extract content from Reddit URLs

**Paid → ScrapeCreators** (1 credit)
```bash
python3 scripts/scrapecreators.py reddit search "QUERY"
```

## Facebook
**Free → yt-dlp** (public videos)
```bash
yt-dlp --no-update --write-auto-sub --skip-download "FB_VIDEO_URL"
```

**Paid → ScrapeCreators** (1 credit)
```bash
python3 scripts/scrapecreators.py facebook transcript "VIDEO_URL"
```

## Any Webpage
**Free → web_fetch** (always try first)
- Built-in tool, extracts markdown from any URL

**Free → Exa/Composio Search** (if web_fetch fails)
- Use `COMPOSIO_SEARCH_FETCH_URL_CONTENT`

**Free → Composio Browser Tool** (last resort)
- Full browser automation, handles JS-heavy pages

---

## ScrapeCreators Credit Tracker
- **Starting credits:** 100
- **Current:** 97 (as of 2026-03-19)
- **API key:** stored in ~/.env
- **Script:** `scripts/scrapecreators.py`
- **Rule:** NEVER use paid when free alternative works. Credits are finite.

## Technical
- **YouTube script:** `scripts/youtube-transcript.sh`
- **ScrapeCreators:** `scripts/scrapecreators.py`
- **yt-dlp:** `/usr/bin/yt-dlp` (pre-installed)
