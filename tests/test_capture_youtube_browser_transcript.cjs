const assert = require('node:assert/strict');
const test = require('node:test');

const {
  clickTargetScript,
  formatTimestamp,
  installHookAndNavigateScript,
  normalizeYouTubeUrl,
  parseCaptionResponse,
  stableTabReference,
  transcriptEvents,
} = require('../scripts/capture-youtube-browser-transcript.cjs');

test('normalizes supported YouTube URL forms to the requested video ID', () => {
  for (const url of [
    'https://www.youtube.com/watch?v=abcdefghijk',
    'https://youtube.com/shorts/abcdefghijk?feature=share',
    'https://m.youtube.com/embed/abcdefghijk',
    'https://youtu.be/abcdefghijk?t=12',
  ]) {
    assert.deepEqual(normalizeYouTubeUrl(url), {
      videoId: 'abcdefghijk',
      navigationUrl: 'https://www.youtube.com/watch?v=abcdefghijk',
    });
  }
});

test('rejects non-YouTube hosts and missing video IDs', () => {
  assert.throws(() => normalizeYouTubeUrl('https://example.com/watch?v=abcdefghijk'), /youtube\.com or youtu\.be/i);
  assert.throws(() => normalizeYouTubeUrl('https://youtube.com/watch'), /valid video ID/i);
});

test('prefers OpenClaw stable tab handles over raw Chromium target IDs', () => {
  assert.equal(stableTabReference({
    targetId: 'volatile-cdp-target',
    suggestedTargetId: 't42',
    tabId: 't42',
  }), 't42');
  assert.equal(stableTabReference({ targetId: 'volatile-only' }), '');
});

test('normalizes JSON3 caption events and timestamps', () => {
  assert.deepEqual(
    transcriptEvents({
      events: [
        { tStartMs: 65000, dDurationMs: 1500, segs: [{ utf8: 'hello ' }, { utf8: ' world' }] },
        { startMs: 3723000, durationMs: 1000, text: 'later' },
        { tStartMs: 0, segs: [] },
      ],
    }),
    [
      { startMs: 65000, durationMs: 1500, text: 'hello world' },
      { startMs: 3723000, durationMs: 1000, text: 'later' },
    ],
  );
  assert.equal(formatTimestamp(65000), '1:05');
  assert.equal(formatTimestamp(3723000), '1:02:03');
});

test('installs interception before same-task YouTube SPA navigation', () => {
  const source = installHookAndNavigateScript(
    'abcdefghijk',
    'https://www.youtube.com/watch?v=abcdefghijk',
  );
  const installedAt = source.indexOf('window.__captionHookInstalled = true');
  const clickedAt = source.indexOf('link.click()');
  assert.ok(installedAt > 0);
  assert.ok(clickedAt > installedAt);
  assert.match(source, /__captionExpectedId = "abcdefghijk"/);
  const retrySource = clickTargetScript(
    'abcdefghijk',
    'https://www.youtube.com/watch?v=abcdefghijk',
  );
  assert.ok(retrySource.indexOf('if (!window.__captionHookInstalled)') < retrySource.indexOf('link.click()'));
  assert.match(retrySource, /endpoint\.watchEndpoint = \{ videoId: "abcdefghijk" \}/);
});

test('accepts only complete JSON3 responses for the requested video', () => {
  const output = {
    url: 'https://www.youtube.com/api/timedtext?v=abcdefghijk&fmt=json3',
    status: 200,
    body: JSON.stringify({ events: [{ tStartMs: 1000, segs: [{ utf8: 'grounded caption' }] }] }),
  };
  assert.deepEqual(parseCaptionResponse(output, 'abcdefghijk').events, [
    { startMs: 1000, durationMs: 0, text: 'grounded caption' },
  ]);
  assert.throws(() => parseCaptionResponse(output, 'differentID'), /video ID mismatch/i);
  assert.throws(
    () => parseCaptionResponse({
      url: 'https://www.youtube.com/api/timedtext?v=abcdefghijk',
      status: 200,
      truncated: true,
      body: '{}',
    }, 'abcdefghijk'),
    /capture limit/i,
  );
});
