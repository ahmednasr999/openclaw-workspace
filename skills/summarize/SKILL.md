# summarize

Summarize web pages, YouTube videos, podcasts, and local files using AI.

## Usage

```
summarize <url|file|-> [options]
```

## Options

| Flag | Description |
|------|-------------|
| `--youtube <mode>` | YouTube transcript source: auto, web, no-auto, yt-dlp, apify |
| `--transcriber <name>` | Audio transcription: auto, whisper, parakeet, canary |
| `--video-mode <mode>` | Video handling: auto, transcript, understand |
| `--slides` | Extract slides from YouTube presentations |
| `--lang <code>` | Language for summarization (e.g., en, ar) |
| `--markdown` | Output in markdown format |

## Examples

### Summarize a YouTube video
```bash
summarize https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### Extract slides from presentation
```bash
summarize https://www.youtube.com/watch?v=example --slides
```

### Summarize a web article
```bash
summarize https://example.com/article
```

### Summarize a local PDF
```bash
summarize ./document.pdf
```

### Summarize from stdin
```bash
echo "text to summarize" | summarize -
```

## Requirements

- API keys for at least one provider:
  - `OPENAI_API_KEY` (OpenAI)
  - `ANTHROPIC_API_KEY` (Anthropic)
  - `GOOGLE_GENERATIVE_AI_API_KEY` (Google)
  - Or use `--cli agent` for Cursor/Claude Code

## Notes

- Uses Groq for fast transcription when available
- Automatically falls back between providers
- Supports 100+ languages
- YouTube summaries include timestamps for easy navigation
