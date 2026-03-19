# YouTube Transcript Extractor

Extract transcripts from any public YouTube video. Free, no API key needed.

## When to Use
- User shares a YouTube link and wants the content analyzed
- Research tasks requiring video content extraction
- Content analysis of creator videos (Berman, etc.)
- Any task requiring "what does this video say"

## How to Use

### Quick (one-liner)
```bash
bash scripts/youtube-transcript.sh "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Save to File
```bash
bash scripts/youtube-transcript.sh "https://www.youtube.com/watch?v=VIDEO_ID" /tmp/transcript.txt
```

### Video ID Only
```bash
bash scripts/youtube-transcript.sh "VIDEO_ID"
```

## Workflow
1. User shares YouTube URL
2. Run the script to extract transcript
3. Analyze/summarize the transcript content
4. Deliver insights to user

## Limitations
- Some videos are geo-restricted or age-gated (returns error)
- Auto-generated subtitles only (not manually uploaded captions)
- English transcripts by default
- Accuracy depends on YouTube's auto-captioning quality

## Fallback Chain
If `yt-dlp` fails:
1. Try ScrapeCreators API: `python3 scripts/scrapecreators.py youtube transcript VIDEO_URL`
2. Try Composio Browser Tool to navigate and extract
3. Search for transcript on third-party sites (tactiq.io, LinkedIn embeds)

## Technical
- **Script:** `scripts/youtube-transcript.sh`
- **Engine:** yt-dlp (already installed)
- **Cost:** Free
- **Speed:** ~5 seconds per video
