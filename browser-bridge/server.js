/**
 * Browser Bridge - WebSocket server
 * VPS side: receives navigate commands from NASR, pushes to Chrome extension
 * Port: 3010
 */

const http = require('http');
const { WebSocketServer } = require('ws');

const PORT = 3010;
const SECRET = process.env.BRIDGE_SECRET || 'nasr-bridge-2026';

const pendingFetches = new Map();
const pendingEvals = new Map();

const server = http.createServer((req, res) => {
  // Health check
  if (req.method === 'GET' && req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, clients: extensionClients.size }));
    return;
  }

  // Navigate command from NASR agent
  if (req.method === 'POST' && req.url === '/navigate') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { url, secret } = JSON.parse(body);
        if (secret !== SECRET) {
          res.writeHead(403);
          res.end(JSON.stringify({ error: 'Forbidden' }));
          return;
        }
        if (!url) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: 'url required' }));
          return;
        }

        if (extensionClients.size === 0) {
          res.writeHead(503);
          res.end(JSON.stringify({ error: 'No extension connected', clients: 0 }));
          return;
        }

        // Push to all connected extensions
        const msg = JSON.stringify({ type: 'navigate', url, id: Date.now() });
        extensionClients.forEach(ws => {
          if (ws.readyState === 1) ws.send(msg);
        });

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, pushed_to: extensionClients.size, url }));
      } catch (e) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }

  // fetch_transcript - call YouTube's InnerTube API from inside browser with session cookies
  if (req.method === 'POST' && req.url === '/fetch_transcript') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { secret } = JSON.parse(body || '{}');
        if (secret !== SECRET) { res.writeHead(403); res.end(JSON.stringify({ error: 'Forbidden' })); return; }
        if (extensionClients.size === 0) { res.writeHead(503); res.end(JSON.stringify({ error: 'No extension connected' })); return; }
        const id = Date.now();
        const timeout = setTimeout(() => {
          pendingEvals.delete(id);
          res.writeHead(408); res.end(JSON.stringify({ error: 'Timeout' }));
        }, 30000);
        pendingEvals.set(id, { res, timeout });
        for (const client of extensionClients) { client.send(JSON.stringify({ type: 'fetch_transcript', id })); break; }
      } catch(e) { res.writeHead(500); res.end(JSON.stringify({ error: e.message })); }
    });
    return;
  }

  // get_yt_data - dump ytInitialData panel structure
  if (req.method === 'POST' && req.url === '/get_yt_data') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { secret } = JSON.parse(body || '{}');
        if (secret !== SECRET) { res.writeHead(403); res.end(JSON.stringify({ error: 'Forbidden' })); return; }
        if (extensionClients.size === 0) { res.writeHead(503); res.end(JSON.stringify({ error: 'No extension connected' })); return; }
        const id = Date.now();
        const timeout = setTimeout(() => {
          pendingEvals.delete(id);
          res.writeHead(408); res.end(JSON.stringify({ error: 'Timeout' }));
        }, 20000);
        pendingEvals.set(id, { res, timeout });
        for (const client of extensionClients) { client.send(JSON.stringify({ type: 'get_yt_data', id })); break; }
      } catch(e) { res.writeHead(500); res.end(JSON.stringify({ error: e.message })); }
    });
    return;
  }

  // raw_eval - run arbitrary JS in MAIN world of primary tab
  if (req.method === 'POST' && req.url === '/raw_eval') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { secret, code } = JSON.parse(body || '{}');
        if (secret !== SECRET) { res.writeHead(403); res.end(JSON.stringify({ error: 'Forbidden' })); return; }
        if (extensionClients.size === 0) { res.writeHead(503); res.end(JSON.stringify({ error: 'No extension connected' })); return; }
        const id = Date.now();
        const msg = JSON.stringify({ type: 'raw_eval', id, code });
        const timeout = setTimeout(() => {
          pendingEvals.delete(id);
          res.writeHead(408); res.end(JSON.stringify({ error: 'Eval timeout' }));
        }, 20000);
        pendingEvals.set(id, { res, timeout });
        for (const client of extensionClients) { client.send(msg); break; }
      } catch(e) { res.writeHead(500); res.end(JSON.stringify({ error: e.message })); }
    });
    return;
  }

  // get_yt_transcript - extracts YouTube transcript from current tab
  if (req.method === 'POST' && (req.url === '/get_yt_transcript' || req.url === '/eval')) {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { secret } = JSON.parse(body || '{}');
        if (secret !== SECRET) { res.writeHead(403); res.end(JSON.stringify({ error: 'Forbidden' })); return; }
        if (extensionClients.size === 0) { res.writeHead(503); res.end(JSON.stringify({ error: 'No extension connected' })); return; }

        const id = Date.now();
        const msg = JSON.stringify({ type: 'get_yt_transcript', id });

        const timeout = setTimeout(() => {
          pendingFetches.delete(id);
          res.writeHead(504); res.end(JSON.stringify({ error: 'Eval timeout' }));
        }, 30000);

        pendingFetches.set(id, (result) => {
          clearTimeout(timeout);
          pendingFetches.delete(id);
          res.writeHead(result.ok ? 200 : 500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify(result));
        });

        extensionClients.forEach(ws => { if (ws.readyState === 1) ws.send(msg); });
      } catch (e) {
        res.writeHead(400); res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }

  // Read DOM - reads current tab's rendered text content
  if (req.method === 'POST' && req.url === '/read_dom') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { secret } = JSON.parse(body || '{}');
        if (secret !== SECRET) { res.writeHead(403); res.end(JSON.stringify({ error: 'Forbidden' })); return; }
        if (extensionClients.size === 0) { res.writeHead(503); res.end(JSON.stringify({ error: 'No extension connected' })); return; }

        const id = Date.now();
        const msg = JSON.stringify({ type: 'read_dom', id });

        const timeout = setTimeout(() => {
          pendingFetches.delete(id);
          res.writeHead(504); res.end(JSON.stringify({ error: 'Timeout' }));
        }, 15000);

        pendingFetches.set(id, (result) => {
          clearTimeout(timeout);
          pendingFetches.delete(id);
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify(result));
        });

        extensionClients.forEach(ws => { if (ws.readyState === 1) ws.send(msg); });
      } catch (e) {
        res.writeHead(400); res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }

  // Fetch command - fetches URL via extension (with browser cookies) and returns body
  if (req.method === 'POST' && req.url === '/fetch') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { url, secret } = JSON.parse(body);
        if (secret !== SECRET) { res.writeHead(403); res.end(JSON.stringify({ error: 'Forbidden' })); return; }
        if (!url) { res.writeHead(400); res.end(JSON.stringify({ error: 'url required' })); return; }
        if (extensionClients.size === 0) { res.writeHead(503); res.end(JSON.stringify({ error: 'No extension connected' })); return; }

        const id = Date.now();
        const msg = JSON.stringify({ type: 'fetch', url, id });

        // Wait for fetch_result with matching id (30s timeout)
        const timeout = setTimeout(() => {
          pendingFetches.delete(id);
          res.writeHead(504); res.end(JSON.stringify({ error: 'Fetch timeout' }));
        }, 30000);

        pendingFetches.set(id, (result) => {
          clearTimeout(timeout);
          pendingFetches.delete(id);
          res.writeHead(result.ok ? 200 : 500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify(result));
        });

        extensionClients.forEach(ws => { if (ws.readyState === 1) ws.send(msg); });
      } catch (e) {
        res.writeHead(400); res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }

  res.writeHead(404);
  res.end('Not found');
});

// WebSocket server for Chrome extension
const wss = new WebSocketServer({ server });
const extensionClients = new Set();

wss.on('connection', (ws, req) => {
  console.log(`[bridge] Extension connected from ${req.socket.remoteAddress}`);
  extensionClients.add(ws);

  ws.on('message', (data) => {
    try {
      const msg = JSON.parse(data);
      // Extension can send back tab info
      if (msg.type === 'tab_opened' || msg.type === 'tab_navigated') {
        console.log(`[bridge] Tab navigated: tabId=${msg.tabId} url=${msg.url}`);
      }
      // Handle fetch/read_dom/eval results from extension
      if ((msg.type === 'fetch_result' || msg.type === 'read_dom_result' || msg.type === 'eval_result') && msg.id) {
        // pendingFetches stores resolve functions; pendingEvals stores {res, timeout}
        const fetchResolve = pendingFetches.get(msg.id);
        if (fetchResolve) { pendingFetches.delete(msg.id); fetchResolve(msg); }
        const evalEntry = pendingEvals.get(msg.id);
        if (evalEntry) {
          pendingEvals.delete(msg.id);
          clearTimeout(evalEntry.timeout);
          evalEntry.res.writeHead(200, {'Content-Type':'application/json'});
          evalEntry.res.end(JSON.stringify(msg));
        }
      }
    } catch (e) {}
  });

  ws.on('close', () => {
    console.log('[bridge] Extension disconnected');
    extensionClients.delete(ws);
  });

  ws.on('error', () => extensionClients.delete(ws));

  // Ping to keep connection alive
  ws.send(JSON.stringify({ type: 'connected', server: 'nasr-bridge' }));
});

// Keepalive ping every 30s
setInterval(() => {
  extensionClients.forEach(ws => {
    if (ws.readyState === 1) ws.ping();
  });
}, 30000);

server.listen(PORT, '0.0.0.0', () => {
  console.log(`[bridge] WebSocket server listening on port ${PORT}`);
});
