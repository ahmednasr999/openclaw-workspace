#!/usr/bin/env node
/**
 * fetch-guard.mjs
 * Lightweight guarded fetch helper for job-intel workflows.
 *
 * Usage:
 *   node scripts/fetch-guard.mjs <url>
 *
 * Exit codes:
 *   0 success
 *   2 blocked domain (403 / bot protection)
 *   3 dead URL (404)
 *   4 transient server error (5xx after max retries)
 *   5 dns / network resolution error
 *   9 invalid usage
 */

import { appendFileSync } from 'fs';

const url = process.argv[2];
if (!url) {
  console.error('Usage: node scripts/fetch-guard.mjs <url>');
  process.exit(9);
}

const MAX_RETRIES = 2;
const BLOCK_PATTERNS = [/just a moment/i, /cf-browser-verification/i, /cloudflare/i, /attention required/i];
const BLOCK_LOG = '/root/.openclaw/workspace/memory/blocked-domains.log';
const FATAL_LOG = '/root/.openclaw/workspace/memory/fetch-fatal.log';

function ts() {
  return new Date().toISOString();
}

function domainOf(input) {
  try {
    return new URL(input).hostname;
  } catch {
    return 'invalid-domain';
  }
}

function logLine(path, line) {
  appendFileSync(path, line + '\n');
}

async function attemptFetch(target) {
  let lastStatus = 0;
  let lastErr = null;

  for (let i = 0; i <= MAX_RETRIES; i++) {
    try {
      const res = await fetch(target, {
        redirect: 'follow',
        headers: {
          'user-agent': 'Mozilla/5.0 (compatible; NASR-fetch-guard/1.0)',
          'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
      });

      const body = await res.text();
      const blockedByBody = BLOCK_PATTERNS.some((p) => p.test(body));
      lastStatus = res.status;

      if (res.status === 403 || blockedByBody) {
        const d = domainOf(target);
        logLine(BLOCK_LOG, `${ts()}\t${d}\tblocked\tstatus=${res.status}\turl=${target}`);
        console.log(JSON.stringify({ outcome: 'blocked_domain', status: res.status, domain: d, url: target }));
        process.exit(2);
      }

      if (res.status === 404) {
        console.log(JSON.stringify({ outcome: 'dead_url', status: 404, url: target }));
        process.exit(3);
      }

      if (res.status >= 500) {
        if (i < MAX_RETRIES) continue;
        logLine(FATAL_LOG, `${ts()}\tserver_error\tstatus=${res.status}\turl=${target}`);
        console.log(JSON.stringify({ outcome: 'transient_server_error', status: res.status, url: target }));
        process.exit(4);
      }

      if (!res.ok) {
        logLine(FATAL_LOG, `${ts()}\thttp_error\tstatus=${res.status}\turl=${target}`);
        console.log(JSON.stringify({ outcome: 'http_error', status: res.status, url: target }));
        process.exit(4);
      }

      console.log(JSON.stringify({ outcome: 'ok', status: res.status, url: target, bytes: body.length }));
      process.exit(0);
    } catch (err) {
      lastErr = err;
      const msg = String(err?.message || err || 'unknown').toLowerCase();
      const causeCode = String(err?.cause?.code || '').toLowerCase();
      const dnsLike = msg.includes('enotfound') || msg.includes('eai_again') || msg.includes('dns') || causeCode.includes('enotfound') || causeCode.includes('eai_again');

      if (dnsLike) {
        logLine(FATAL_LOG, `${ts()}\tdns_error\turl=${target}\terr=${msg.replace(/\s+/g, ' ')}`);
        console.log(JSON.stringify({ outcome: 'dns_error', code: 'ENOTFOUND', url: target }));
        process.exit(5);
      }

      if (i < MAX_RETRIES) continue;
    }
  }

  logLine(FATAL_LOG, `${ts()}\tunknown_fetch_error\tstatus=${lastStatus}\turl=${target}\terr=${String(lastErr?.message || lastErr || 'unknown')}`);
  console.log(JSON.stringify({ outcome: 'fetch_failed', status: lastStatus, url: target }));
  process.exit(4);
}

attemptFetch(url);
