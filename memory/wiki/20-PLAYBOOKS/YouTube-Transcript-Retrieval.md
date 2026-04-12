# YouTube Transcript Retrieval

## Current status
Reliable full transcript extraction is not yet solved from the VPS alone.

## What was proven
- The VPS can reach the video page in Chrome.
- The browser can discover YouTube's internal transcript endpoint metadata.
- The real `youtubei/v1/get_transcript` request can be triggered from inside the browser.

## What failed
- Headless Chrome path returned `400 FAILED_PRECONDITION`.
- Headful Chrome via `xvfb-run` removed the `HeadlessChrome` fingerprint, but the transcript call still returned `400 FAILED_PRECONDITION`.
- Existing cookie import improved session state only partially and did not create a truly trusted signed-in transcript session.

## Current conclusion
- Free VPS-only path: not proven.
- Better desktop cookies: worth testing.
- Proxy-backed browser extraction: still the most likely reliable path.

## Recommended next steps
1. Test a stronger desktop-exported `cookies.txt` from a real trusted browser session.
2. If that fails, stop pretending the free path is reliable.
3. Move to a proxy-backed browser worker if transcript automation is important enough.

## Anti-waste rule
Do not spend endless time on brittle transcript websites or random public proxies. Treat them as noise unless they are proven stable.
