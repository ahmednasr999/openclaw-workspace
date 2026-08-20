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

function parseCaptionResponse(response, expectedVideoId) {
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

function spaNavigationStatement(expectedVideoId, navigationUrl) {
  return `const link = document.querySelector('a#video-title[href], a.yt-simple-endpoint[href*="/watch"]'); if (!link?.data) return { installed: true, navigated: false }; const endpoint = structuredClone(link.data); endpoint.commandMetadata = { webCommandMetadata: { url: "/watch?v=${encodeURIComponent(expectedVideoId)}", webPageType: "WEB_PAGE_TYPE_WATCH", rootVe: 3832 } }; endpoint.watchEndpoint = { videoId: ${JSON.stringify(expectedVideoId)} }; link.data = endpoint; link.setAttribute("href", ${JSON.stringify(navigationUrl)}); link.href = ${JSON.stringify(navigationUrl)}; link.click(); return { installed: true, navigated: true };`;
}

function installHookAndNavigateScript(expectedVideoId, navigationUrl) {
  return `() => { window.__captionCapture = null; window.__captionExpectedId = ${JSON.stringify(expectedVideoId)}; const store = (url, text) => { if (window.__captionCapture || !String(url).includes("/api/timedtext") || !text) return; try { const requestVideoId = new URL(String(url), location.href).searchParams.get("v"); if (requestVideoId !== window.__captionExpectedId) return; const payload = JSON.parse(text); const events = (payload.events || []).filter((event) => Array.isArray(event.segs)).map((event) => ({ startMs: Number(event.tStartMs || 0), durationMs: Number(event.dDurationMs || 0), text: event.segs.map((segment) => segment.utf8 || "").join("").replace(/\\s+/g, " ").trim() })).filter((event) => event.text); if (events.length) window.__captionCapture = { events, responseUrl: String(url) }; } catch {} }; if (!window.__captionHookInstalled) { window.__captionHookInstalled = true; const originalOpen = XMLHttpRequest.prototype.open; const originalSend = XMLHttpRequest.prototype.send; XMLHttpRequest.prototype.open = function(method, url, ...rest) { this.__captionUrl = String(url); return originalOpen.call(this, method, url, ...rest); }; XMLHttpRequest.prototype.send = function(...args) { if (this.__captionUrl?.includes("/api/timedtext")) this.addEventListener("loadend", () => store(this.__captionUrl, this.responseText || "")); return originalSend.apply(this, args); }; const originalFetch = window.fetch; window.fetch = async function(...args) { const response = await originalFetch.apply(this, args); const url = String(args[0]?.url || args[0]); if (url.includes("/api/timedtext")) response.clone().text().then((text) => store(url, text)); return response; }; } ${spaNavigationStatement(expectedVideoId, navigationUrl)} }`;
}

function clickTargetScript(expectedVideoId, navigationUrl) {
  return `() => { if (!window.__captionHookInstalled) return { installed: false, navigated: false }; ${spaNavigationStatement(expectedVideoId, navigationUrl)} }`;
}

async function evaluateTarget(targetId, functionSource) {
  return parseJsonOutput(await runBrowser([
    'evaluate', '--fn', functionSource, '--target-id', targetId,
  ]));
}

function stableTabReference(opened) {
  return opened.tabId || opened.suggestedTargetId || '';
}

async function captureInManagedBrowser(requested) {
  const opened = parseJsonOutput(await runBrowser(['--json', 'open', 'https://www.youtube.com/']));
  const targetId = stableTabReference(opened);
  if (!targetId) {
    if (opened.targetId) await runBrowser(['close', opened.targetId]).catch(() => {});
    throw new Error('OpenClaw browser did not return a stable tab handle for the capture tab');
  }
  try {
    let navigation = await evaluateTarget(
      targetId,
      installHookAndNavigateScript(requested.videoId, requested.navigationUrl),
    );
    for (let attempt = 0; !navigation.navigated && attempt < 8; attempt += 1) {
      if (!navigation.installed) throw new Error('Caption hook was not installed before navigation');
      await new Promise((resolve) => setTimeout(resolve, 500));
      navigation = await evaluateTarget(
        targetId,
        clickTargetScript(requested.videoId, requested.navigationUrl),
      );
    }
    if (!navigation.navigated) throw new Error('YouTube SPA navigation link was not available');

    let state;
    for (let attempt = 0; attempt < 20; attempt += 1) {
      state = await evaluateTarget(targetId, '() => { const initial = window.ytInitialPlayerResponse || {}; const player = document.getElementById("movie_player"); const playerData = player?.getVideoData?.() || {}; const playerTracks = player?.getOption?.("captions", "tracklist") || []; const initialTracks = initial.captions?.playerCaptionsTracklistRenderer?.captionTracks || []; const tracks = playerTracks.length ? playerTracks.map((track) => ({ languageCode: track.languageCode, name: track.displayName || track.languageName || track.name || "", kind: track.kind || "" })) : initialTracks.map((track) => ({ languageCode: track.languageCode, name: track.name?.simpleText || track.name?.runs?.map((run) => run.text).join("") || "", kind: track.kind || "" })); const videoId = playerData.video_id || initial.videoDetails?.videoId || ""; return { installed: Boolean(window.__captionHookInstalled), ready: Boolean(window.__captionCapture), count: window.__captionCapture?.events?.length || 0, title: playerData.title || initial.videoDetails?.title || document.title, videoId, playability: videoId ? "OK" : initial.playabilityStatus?.status || "UNKNOWN", tracks }; }');
      if (!state.installed) {
        throw new Error('YouTube navigation replaced the hooked document; caption evidence is unsafe');
      }
      if (
        state.videoId === requested.videoId
        && state.playability !== 'UNKNOWN'
        && state.tracks.length > 0
      ) break;
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    if (state.playability !== 'OK') throw new Error(`Video is not playable: ${state.playability}`);
    if (state.videoId !== requested.videoId) {
      throw new Error(`Authenticated player video ID mismatch: expected ${requested.videoId}, got ${state.videoId || 'none'}`);
    }
    if (!state.tracks.length) throw new Error('No caption track is advertised by the authenticated player');
    const metadata = {
      title: state.title,
      videoId: state.videoId,
      playability: state.playability,
      tracks: state.tracks,
    };

    if (!state.ready) {
      await runBrowser(['press', 'c', '--target-id', targetId]);
      await new Promise((resolve) => setTimeout(resolve, 900));
      await runBrowser(['press', 'c', '--target-id', targetId]);
    }
    for (let attempt = 0; !state.ready && attempt < 8; attempt += 1) {
      state = await evaluateTarget(targetId, '() => ({ installed: Boolean(window.__captionHookInstalled), ready: Boolean(window.__captionCapture), count: window.__captionCapture?.events?.length || 0 })');
      if (!state.installed) throw new Error('Caption hook disappeared before evidence capture');
      if (!state.ready) await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    if (!state.ready || !state.count) throw new Error('Authenticated caption response was not captured');

    const events = [];
    for (let start = 0; start < state.count; start += 500) {
      const end = Math.min(state.count, start + 500);
      events.push(...await evaluateTarget(
        targetId,
        `() => window.__captionCapture.events.slice(${start}, ${end})`,
      ));
    }
    return {
      metadata,
      payload: { events },
    };
  } finally {
    await runBrowser(['close', targetId]).catch(() => {});
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const requested = normalizeYouTubeUrl(args.url);
  const { metadata, payload } = await captureInManagedBrowser(requested);
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
  captureInManagedBrowser,
  clickTargetScript,
  formatTimestamp,
  installHookAndNavigateScript,
  normalizeYouTubeUrl,
  parseCaptionResponse,
  parseArgs,
  parseJsonOutput,
  stableTabReference,
  transcriptEvents,
};
