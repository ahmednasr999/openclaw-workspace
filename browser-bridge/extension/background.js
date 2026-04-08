// NASR Browser Bridge - Background Service Worker

let ws = null;
let reconnectTimer = null;
let primaryTabId = null;
let pendingFetches = new Map();
let pendingEvals = new Map();

const BRIDGE_URL = 'ws://76.13.46.115:3010';

function connect() {
  ws = new WebSocket(BRIDGE_URL);

  ws.onopen = () => {
    console.log('[Bridge] Connected');
    clearTimeout(reconnectTimer);
  };

  ws.onmessage = async (event) => {
    let msg;
    try { msg = JSON.parse(event.data); } catch { return; }

    // --- SNAPSHOT ---
    if (msg.type === 'snapshot') {
      try {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tabs[0]) primaryTabId = tabs[0].id;
        ws.send(JSON.stringify({ type: 'snapshot_result', id: msg.id, tabId: primaryTabId }));
      } catch(e) { ws.send(JSON.stringify({ type: 'snapshot_result', id: msg.id, error: e.message })); }
    }

    // --- NAVIGATE: reuse existing primary agent tab ---
    else if (msg.type === 'navigate') {
      try {
        if (!primaryTabId) {
          const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
          if (tabs[0]) primaryTabId = tabs[0].id;
        }
        if (primaryTabId) {
          await chrome.tabs.update(primaryTabId, { url: msg.url });
          ws.send(JSON.stringify({ type: 'navigate_result', id: msg.id, ok: true, pushed_to: 1, url: msg.url }));
        } else {
          ws.send(JSON.stringify({ type: 'navigate_result', id: msg.id, ok: false, error: 'NO_TAB' }));
        }
      } catch(e) { ws.send(JSON.stringify({ type: 'navigate_result', id: msg.id, ok: false, error: e.message })); }
    }

    // --- FETCH_TRANSCRIPT: intercept YouTube's own /api/timedtext XHR/fetch call ---
    else if (msg.type === 'fetch_transcript') {
      try {
        const tabId = primaryTabId;
        if (!tabId) throw new Error('No primary tab');

        // Step 1: Inject XHR/fetch interceptor into MAIN world
        await chrome.scripting.executeScript({
          target: { tabId },
          world: 'MAIN',
          func: () => {
            window.__ytTranscript = null;

            // Intercept XHR
            const OrigXHR = window.XMLHttpRequest;
            window.XMLHttpRequest = function() {
              const xhr = new OrigXHR();
              const origOpen = xhr.open.bind(xhr);
              const origSend = xhr.send.bind(xhr);
              let reqUrl = '';
              xhr.open = function(method, url, ...args) { reqUrl = url; return origOpen(method, url, ...args); };
              xhr.send = function(...args) {
                xhr.addEventListener('readystatechange', function() {
                  if (this.readyState === 4 && this.status === 200 && reqUrl.includes('/api/timedtext') && !window.__ytTranscript) {
                    window.__ytTranscript = { url: reqUrl, text: this.responseText, via: 'xhr' };
                  }
                });
                return origSend(...args);
              };
              return xhr;
            };

            // Intercept fetch
            const OrigFetch = window.fetch;
            window.fetch = async function(input, init) {
              const url = typeof input === 'string' ? input : input?.url || '';
              const resp = await OrigFetch.apply(this, arguments);
              if (url.includes('/api/timedtext') && resp.ok && !window.__ytTranscript) {
                try {
                  const text = await resp.clone().text();
                  window.__ytTranscript = { url, text, via: 'fetch' };
                } catch(e) {}
              }
              return resp;
            };
          }
        });

        // Step 2: Click the CC button to trigger YouTube to load captions
        await chrome.scripting.executeScript({
          target: { tabId },
          world: 'MAIN',
          func: () => {
            // Try to click CC/subtitles button
            const ccBtn = document.querySelector('.ytp-subtitles-button') ||
                          document.querySelector('button.ytp-button[data-tooltip-target-id="ytp-subtitles-button"]') ||
                          document.querySelector('[aria-label*="subtitle" i]') ||
                          document.querySelector('[aria-label*="caption" i]');
            if (ccBtn) {
              // If already on, turn off then on to trigger fresh load
              const isOn = ccBtn.getAttribute('aria-pressed') === 'true';
              if (isOn) { ccBtn.click(); setTimeout(() => ccBtn.click(), 500); }
              else { ccBtn.click(); }
            }
          }
        });

        // Step 3: Poll for transcript (up to 20s)
        let transcript = null;
        for (let i = 0; i < 20; i++) {
          await new Promise(r => setTimeout(r, 1000));
          const poll = await chrome.scripting.executeScript({
            target: { tabId },
            world: 'MAIN',
            func: () => window.__ytTranscript
          });
          const result = poll?.[0]?.result;
          if (result?.text) { transcript = result; break; }
        }

        if (!transcript) {
          ws.send(JSON.stringify({ type: 'eval_result', id: msg.id, ok: false, error: 'TIMEOUT_NO_TIMEDTEXT' }));
          return;
        }

        // Step 4: Parse - YouTube returns JSON3 or XML
        let segs = [];
        const text = transcript.text;
        try {
          const data = JSON.parse(text);
          // JSON3 format
          const events = data.events || [];
          for (const ev of events) {
            if (ev.segs) {
              const line = ev.segs.map(s => s.utf8 || '').join('').trim();
              if (line) segs.push(line);
            }
          }
        } catch {
          // XML format fallback
          const matches = text.matchAll(/<text[^>]*>([^<]+)<\/text>/g);
          for (const m of matches) {
            const t = m[1].replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&#39;/g,"'").trim();
            if (t) segs.push(t);
          }
        }

        if (segs.length > 0) {
          ws.send(JSON.stringify({ type: 'eval_result', id: msg.id, ok: true, transcript: segs.join(' '), count: segs.length, via: transcript.via }));
        } else {
          ws.send(JSON.stringify({ type: 'eval_result', id: msg.id, ok: false, error: 'PARSED_EMPTY', raw: text.slice(0,300) }));
        }

      } catch(e) {
        ws.send(JSON.stringify({ type: 'eval_result', id: msg.id, ok: false, error: e.message }));
      }
    }

    // --- GET_YT_DATA ---
    else if (msg.type === 'get_yt_data') {
      try {
        const tabId = primaryTabId;
        const result = await chrome.scripting.executeScript({
          target: { tabId },
          world: 'MAIN',
          func: () => {
            const apiKey = window.ytcfg?.get?.('INNERTUBE_API_KEY') || '';
            const clientVersion = window.ytcfg?.get?.('INNERTUBE_CLIENT_VERSION') || '';
            const panels = window.ytInitialData?.engagementPanels || [];
            const tp = panels.find(p =>
              (p?.engagementPanelSectionListRenderer?.panelIdentifier || '').includes('transcript')
            );
            const ci = tp?.engagementPanelSectionListRenderer?.content?.continuationItemRenderer;
            return { apiKey, clientVersion, panelCount: panels.length, hasTranscriptPanel: !!tp, continuationApiUrl: JSON.stringify(ci) };
          }
        });
        ws.send(JSON.stringify({ type: 'eval_result', id: msg.id, ...result?.[0]?.result }));
      } catch(e) {
        ws.send(JSON.stringify({ type: 'eval_result', id: msg.id, error: e.message }));
      }
    }

  };

  ws.onclose = () => {
    console.log('[Bridge] Disconnected, reconnecting in 3s...');
    reconnectTimer = setTimeout(connect, 3000);
  };

  ws.onerror = () => ws.close();
}

connect();

// Keep service worker alive
chrome.alarms.create('keepAlive', { periodInMinutes: 0.4 });
chrome.alarms.onAlarm.addListener(() => {});
