const assert = require('node:assert/strict');
const test = require('node:test');

const {
  captionResponseCommand,
  formatTimestamp,
  normalizeYouTubeUrl,
  parseCaptionResponse,
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

test('arms requested-video caption interception before navigation', () => {
  assert.deepEqual(captionResponseCommand('abcdefghijk'), [
    '--json',
    'responsebody',
    '**/api/timedtext**v=abcdefghijk**',
    '--timeout-ms',
    '30000',
    '--max-chars',
    '5000000',
  ]);
});

test('accepts only complete JSON3 responses for the requested video', () => {
  const output = JSON.stringify({
    url: 'https://www.youtube.com/api/timedtext?v=abcdefghijk&fmt=json3',
    status: 200,
    body: JSON.stringify({ events: [{ tStartMs: 1000, segs: [{ utf8: 'grounded caption' }] }] }),
  });
  assert.deepEqual(parseCaptionResponse(output, 'abcdefghijk').events, [
    { startMs: 1000, durationMs: 0, text: 'grounded caption' },
  ]);
  assert.throws(() => parseCaptionResponse(output, 'differentID'), /video ID mismatch/i);
  assert.throws(
    () => parseCaptionResponse(JSON.stringify({
      url: 'https://www.youtube.com/api/timedtext?v=abcdefghijk',
      status: 200,
      truncated: true,
      body: '{}',
    }), 'abcdefghijk'),
    /capture limit/i,
  );
});
