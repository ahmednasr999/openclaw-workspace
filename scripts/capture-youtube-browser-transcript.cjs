#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');
const { promisify } = require('util');

const execFileAsync = promisify(execFile);

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const value = argv[i];
    if (!value.startsWith('--')) continue;
    const key = value.slice(2);
    args[key] = argv[i + 1];
    i += 1;
  }
  if (!args.url || !args.out) {
    throw new Error('Usage: capture-youtube-browser-transcript.cjs --url <youtube-url> --out <transcript.txt>');
  }
  return args;
}

function normalizeYouTubeUrl(rawUrl) {
  const sourceUrl = new URL(rawUrl);
  const hostname = sourceUrl.hostname.toLowerCase().replace(/^www\./, '').replace(/^m\./, '');
  let videoId = '';
  if (hostname === 'youtu.be') {
    videoId = sourceUrl.pathname.split('/').filter(Boolean)[0] || '';
  } else if (hostname === 'youtube.com' || hostname.endsWith('.youtube.com')) {
    const pathMatch = sourceUrl.pathname.match(/^\/(?:shorts|embed)\/([^/]+)/);
    videoId = pathMatch ? pathMatch[1] : sourceUrl.searchParams.get('v') || '';
  } else {
    throw new Error('URL must use youtube.com or youtu.be');
  }
  if (!/^[A-Za-z0-9_-]{6,20}$/.test(videoId)) {
    throw new Error('YouTube URL does not contain a valid video ID');
  }
  return {
    videoId,
    navigationUrl: `https://www.youtube.com/watch?v=${encodeURIComponent(videoId)}`,
  };
}

function formatTimestamp(milliseconds) {
  const totalSeconds = Math.max(0, Math.floor(milliseconds / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  return `${minutes}:${String(seconds).padStart(2, '0')}`;
}

function transcriptEvents(payload) {
  return (payload.events || [])
    .map((event) => {
      const text = typeof event.text === 'string'
        ? event.text.replace(/\s+/g, ' ').trim()
        : Array.isArray(event.segs)
          ? event.segs.map((segment) => segment.utf8 || '').join('').replace(/\s+/g, ' ').trim()
          : '';
      return {
        startMs: Number(event.startMs ?? event.tStartMs ?? 0),
        durationMs: Number(event.durationMs ?? event.dDurationMs ?? 0),
        text,
      };
    })
    .filter((event) => event.text);
}

async function runBrowser(args, options = {}) {
  const result = await execFileAsync('openclaw', ['browser', ...args], {
    cwd: process.cwd(),
    timeout: options.timeout || 60000,
    maxBuffer: options.maxBuffer || 4 * 1024 * 1024,
  });
  return result.stdout.trim();
}

function parseJsonOutput(output) {
  const jsonStart = output.indexOf('{');
  const arrayStart = output.indexOf('[');
  const start = jsonStart < 0 ? arrayStart : arrayStart < 0 ? jsonStart : Math.min(jsonStart, arrayStart);
  if (start < 0) throw new Error(`Browser output did not contain JSON: ${output.slice(0, 200)}`);
  return JSON.parse(output.slice(start));
}

function captionResponseCommand(expectedVideoId) {
  return [
    '--json',
    'responsebody',
    `**/api/timedtext**v=${encodeURIComponent(expectedVideoId)}**`,
    '--timeout-ms',
    '30000',
    '--max-chars',
    '5000000',
  ];
}

function parseCaptionResponse(output, expectedVideoId) {
  const response = parseJsonOutput(output);
  const responseUrl = new URL(response.url);
  if (!responseUrl.pathname.endsWith('/api/timedtext')) {
    throw new Error(`Captured response was not a timed-text endpoint: ${response.url}`);
  }
  if (responseUrl.searchParams.get('v') !== expectedVideoId) {
    throw new Error(`Caption response video ID mismatch: expected ${expectedVideoId}`);
  }
  if (response.status !== 200) throw new Error(`Caption response returned HTTP ${response.status}`);
  if (response.truncated) throw new Error('Caption response exceeded the capture limit');
  const payload = JSON.parse(response.body);
  const events = transcriptEvents(payload);
  if (!events.length) throw new Error('Caption payload contained no usable transcript events');
  return { events, responseUrl: response.url };
}

async function capture(expectedVideoId, armedResponse) {
  await runBrowser(['press', 'c']);
  await new Promise((resolve) => setTimeout(resolve, 900));
  await runBrowser(['press', 'c']);
  const result = await armedResponse;
  if (!result.ok) throw result.error;
  return parseCaptionResponse(result.output, expectedVideoId);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const requested = normalizeYouTubeUrl(args.url);
  // responsebody registers a Playwright network listener in a separate CLI process.
  // Start it before navigation so cached or eager caption requests cannot beat interception.
  const captionResponse = runBrowser(captionResponseCommand(requested.videoId), {
    timeout: 35000,
    maxBuffer: 6 * 1024 * 1024,
  }).then(
    (output) => ({ ok: true, output }),
    (error) => ({ ok: false, error }),
  );
  await new Promise((resolve) => setTimeout(resolve, 250));
  await runBrowser(['navigate', requested.navigationUrl]);
  const metadataOutput = await runBrowser([
    'evaluate',
    '--fn',
    '() => { const player = window.ytInitialPlayerResponse || {}; const tracks = player.captions?.playerCaptionsTracklistRenderer?.captionTracks || []; return { title: player.videoDetails?.title || document.title, videoId: player.videoDetails?.videoId || new URL(location.href).searchParams.get("v"), playability: player.playabilityStatus?.status || "UNKNOWN", tracks: tracks.map((track) => ({ languageCode: track.languageCode, name: track.name?.simpleText || track.name?.runs?.map((run) => run.text).join("") || "", kind: track.kind || "" })) }; }',
  ]);
  const metadata = parseJsonOutput(metadataOutput);

  if (metadata.playability !== 'OK') throw new Error(`Video is not playable: ${metadata.playability}`);
  if (metadata.videoId !== requested.videoId) {
    throw new Error(`Authenticated player video ID mismatch: expected ${requested.videoId}, got ${metadata.videoId || 'none'}`);
  }
  if (!metadata.tracks.length) throw new Error('No caption track is advertised by the authenticated player');

  const payload = await capture(requested.videoId, captionResponse);
  const events = transcriptEvents(payload);
  if (!events.length) throw new Error('Caption payload contained no usable transcript events');

  const lines = [
    `Title: ${metadata.title}`,
    `Source: ${args.url}`,
    `Video ID: ${metadata.videoId}`,
    `Track: ${metadata.tracks[0].name || metadata.tracks[0].languageCode}${metadata.tracks[0].kind ? ` (${metadata.tracks[0].kind})` : ''}`,
    `Evidence: ${events.length} timestamped JSON3 caption events captured through the authenticated YouTube player`,
    '',
    ...events.map((event) => `[${formatTimestamp(event.startMs)}] ${event.text}`),
    '',
  ];

  fs.mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
  fs.writeFileSync(path.resolve(args.out), lines.join('\n'));
  process.stdout.write(`${JSON.stringify({
    ok: true,
    output: path.resolve(args.out),
    title: metadata.title,
    videoId: metadata.videoId,
    track: metadata.tracks[0],
    events: events.length,
    firstTimestampMs: events[0].startMs,
    lastTimestampMs: events.at(-1).startMs,
  }, null, 2)}\n`);
}

if (require.main === module) {
  main().catch((error) => {
    process.stderr.write(`${error.stack || error.message}\n`);
    process.exitCode = 1;
  });
}

module.exports = {
  captionResponseCommand,
  formatTimestamp,
  normalizeYouTubeUrl,
  parseCaptionResponse,
  parseArgs,
  parseJsonOutput,
  transcriptEvents,
};
