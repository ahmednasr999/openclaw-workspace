# Transcription Source Priority

Always try the fastest method first, fall back to slower ones.

## Priority Order

### 1. Platform Subtitles (instant, free)
**YouTube, Vimeo, and most major platforms** have auto-generated or manual captions.

```bash
# Check if subtitles exist
yt-dlp --list-subs <url>

# Download subtitles (SRT format)
yt-dlp --write-auto-sub --sub-lang en --sub-format srt --skip-download -o "/tmp/transcribe/output" <url>
```

**When to use:** YouTube, Vimeo, or any platform where `--list-subs` returns results.
**Speed:** 2-5 seconds regardless of video length.

### 2. Local Whisper (offline, free, no API key)
Use `faster-whisper` with CPU inference when platform subtitles aren't available.

```bash
/tmp/whisper-env/bin/python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
segments, info = model.transcribe('/path/to/audio.mp3', beam_size=5)
for seg in segments:
    print(f'[{seg.start:.1f}s - {seg.end:.1f}s] {seg.text}')
"
```

**When to use:** TikTok, Instagram Reels, audio files, voice messages, or any source without subtitles.
**Speed:** ~30 seconds per minute of audio (CPU). Use `tiny` model for speed, `small` for accuracy.

### 3. OpenAI Whisper API (best quality, paid)
Use when maximum accuracy is needed or for very long content.

```bash
python3 "$TRANSCRIBE_CLI" audio.mp3 --model gpt-4o-mini-transcribe --out transcript.txt
```

**When to use:** When local Whisper quality isn't sufficient, or for speaker diarization.
**Speed:** Fast (API), but requires OPENAI_API_KEY.
**Cost:** ~$0.006/minute.

## Decision Matrix

| Source | Has Subs? | Method | Speed |
|--------|-----------|--------|-------|
| YouTube | Usually yes | yt-dlp subtitles | Instant |
| Vimeo | Often yes | yt-dlp subtitles | Instant |
| TikTok | No | Download + Whisper | ~30s/min |
| Instagram | No | Download + Whisper | ~30s/min |
| X/Twitter | No | Download + Whisper | ~30s/min |
| Audio file | N/A | Whisper directly | ~30s/min |
| Voice message | N/A | Whisper directly | ~30s/min |

## Download Audio (when needed)

```bash
yt-dlp -x --audio-format mp3 -o "/tmp/transcribe/output.%(ext)s" <url>
```

Works with 1000+ sites including TikTok, Instagram, Twitter, etc.
