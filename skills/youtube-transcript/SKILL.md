# YouTube Transcript Skill

## Trigger
User shares a YouTube URL and asks for transcript, summary, or analysis.

---

## Workflow

### Step 1: Run the transcript script

```bash
/root/.openclaw/workspace/scripts/youtube_transcript.sh "<youtube_url>" [output_file]
```

The script:
- Uses cookies from `~/.cookie-jar/youtube_cookies.txt`
- Downloads VTT subtitles via yt-dlp
- Parses to clean plain text (no timestamps, no duplicates, no HTML tags)
- Outputs file path

**Cookie check:** If the cookie file has <5 lines, cookies are expired → go to Step 2.

---

### Step 2: Refresh cookies (only when expired)

**On Ahmed's Mac:**

1. Start Chrome with remote debugging:
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="$HOME/Library/Application Support/Google/Chrome/Default"
```

2. Run the cookie extraction script:
```bash
python3 /tmp/cdp_cookies.py > ~/Desktop/youtube_cookies.txt
```

3. Ahmed sends the file to the agent

4. Agent saves it:
```bash
# Save Ahmed's cookies to sandbox
# The file content goes into: ~/.cookie-jar/youtube_cookies.txt
```

**Why CDP instead of SQLite:** Chrome on macOS encrypts cookies with the user's login keyring. SQLite export produces unusable encrypted values. CDP reads directly from Chrome's memory, bypassing encryption.

---

### Step 3: Verify coverage

After downloading, check that the transcript covers the full video:
```bash
grep -E "^[0-9]{2}:[0-9]{2}:[0-9]{2}" <vtt_file> | tail -1
yt-dlp --cookies ~/.cookie-jar/youtube_cookies.txt --skip-download --print "%(duration_string)s" "<youtube_url>"
```
Compare last timestamp vs video duration. If they match → 100% coverage.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Sign in to confirm you're not a bot" | Cookies expired → Step 2 |
| "No subtitles downloaded" | Video has no English auto-captions. Try `--sub-lang en-US` or manual caption request |
| yt-dlp hangs | Run with `--no-update` flag |
| Cookie file <5 lines | Cookies expired → Step 2 |
| Video is a stream/live | No subtitles available |

---

## Files

- **Script:** `/root/.openclaw/workspace/scripts/youtube_transcript.sh`
- **Cookies:** `~/.cookie-jar/youtube_cookies.txt`
- **Cookie refresh script (Mac):** `/tmp/cdp_cookies.py`

---

## Dependencies

- `yt-dlp` — installed in sandbox
- `youtube-cookies.txt` — Netscape format, 29 cookies typical
- Mac with Chrome remote debugging (for cookie refresh only)
- CDP Python script on Mac (`websockets` package)

---

## Cookie Refresh on Mac

The CDP cookie extraction script (`/tmp/cdp_cookies.py`) on Ahmed's Mac:
```python
import asyncio, json, websockets, sys

async def main():
    ws_url = "ws://localhost:9222/devtools/page/EBA54133055D8A7E4150EBF580A7816B"
    async with websockets.connect(ws_url, ping_timeout=10) as ws:
        cmd = {"id": 1, "method": "Network.getAllCookies", "params": {}}
        await ws.send(json.dumps(cmd))
        resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
        cookies = resp.get("result", {}).get("cookies", [])
        yt_cookies = [c for c in cookies if "youtube" in c["domain"].lower()]
        lines = ["# Netscape HTTP Cookie File"]
        for c in yt_cookies:
            domain = c["domain"]; name = c["name"]; value = c["value"]
            path = c.get("path", "/"); secure = "TRUE" if c.get("secure") else "FALSE"
            expires = int(c.get("expires") or 0)
            lines.append(f"{domain}\tTRUE\t{path}\t{secure}\t{expires}\t{name}\t{value}")
        sys.stdout.write("\n".join(lines) + "\n")

asyncio.run(main())
```

The WebSocket URL (page ID) changes each Chrome session. Run without a specific page ID to get all pages first, then pick the YouTube page.
