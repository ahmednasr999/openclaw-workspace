#!/usr/bin/env node
/**
 * quota-monitor.js — OpenClaw Quota Monitoring Module
 * 
 * PURPOSE: Track model usage and forecast depletion BEFORE cascade failures occur.
 * INCIDENT: Feb 27, 2026 07:28 UTC — all 6 models failed after 26 parallel CV generations.
 * 
 * Usage:
 *   node quota-monitor.js status              — Print current quota status
 *   node quota-monitor.js check-spawn <n>     — Pre-spawn check for N parallel agents
 *   node quota-monitor.js estimate-cv <n>     — Estimate cost for N CV generations
 *   node quota-monitor.js record <model> <in> <out>  — Record token usage
 *   node quota-monitor.js reset               — Reset daily counters (run at midnight UTC)
 *   node quota-monitor.js validate-keys       — Quick key format validation
 */

'use strict';

const fs = require('fs');
const path = require('path');
const https = require('https');

// ── Config ──────────────────────────────────────────────────────────────────

const QUOTA_DIR = path.dirname(__filename);
const USAGE_FILE = path.join(QUOTA_DIR, 'daily-usage.json');
const ALERT_THRESHOLD = 0.70;   // 70% — warn before exhaustion
const CRITICAL_THRESHOLD = 0.90; // 90% — hard stop recommendation
const MAX_CHECK_MS = 500;        // SLA: checks must complete within 500ms

// Model definitions — cost in USD per 1M tokens
const MODELS = {
  'anthropic/claude-opus-4-6': {
    name: 'Claude Opus 4.6',
    provider: 'anthropic',
    inputCost: 5.00,
    outputCost: 25.00,
    // Anthropic rate limits: ~40k tokens/min on standard tier
    dailyTokenLimit: 1_000_000,   // Conservative: 1M tokens/day (rate limit proxy)
    rpmLimit: 50,                  // Requests per minute
    tpmLimit: 40_000,              // Tokens per minute
    avgCvTokens: { input: 8000, output: 4000 },  // Per CV generation
  },
  'anthropic/claude-sonnet-4-6': {
    name: 'Claude Sonnet 4.6',
    provider: 'anthropic',
    inputCost: 3.00,
    outputCost: 15.00,
    dailyTokenLimit: 2_000_000,
    rpmLimit: 50,
    tpmLimit: 40_000,
    avgCvTokens: { input: 6000, output: 3000 },
  },
  'anthropic/claude-haiku-4-5': {
    name: 'Claude Haiku 4.5',
    provider: 'anthropic',
    inputCost: 1.00,
    outputCost: 5.00,
    dailyTokenLimit: 5_000_000,
    rpmLimit: 50,
    tpmLimit: 100_000,
    avgCvTokens: { input: 5000, output: 2500 },
  },
  'minimax-portal/MiniMax-M2.5': {
    name: 'MiniMax M2.5',
    provider: 'minimax-portal',
    inputCost: 0,
    outputCost: 0,
    dailyTokenLimit: 10_000_000,  // Flat rate plan — effectively unlimited
    rpmLimit: 120,
    tpmLimit: 200_000,
    avgCvTokens: { input: 5000, output: 2500 },
    flatRate: true,               // $40/mo plan — no per-token cost
  },
  'moonshot/kimi-k2.5': {
    name: 'Kimi K2.5',
    provider: 'moonshot',
    inputCost: 0.60,
    outputCost: 3.00,
    dailyTokenLimit: 5_000_000,
    rpmLimit: 60,
    tpmLimit: 128_000,
    avgCvTokens: { input: 6000, output: 3000 },
  },
  'openai-codex/gpt-5.1': {
    name: 'GPT-5.1',
    provider: 'openai-codex',
    inputCost: 2.00,
    outputCost: 8.00,
    dailyTokenLimit: 2_000_000,
    rpmLimit: 60,
    tpmLimit: 60_000,
    avgCvTokens: { input: 6000, output: 3000 },
  },
};

// Fallback chain (ordered — primary first)
const FALLBACK_CHAIN = [
  'minimax-portal/MiniMax-M2.5',
  'anthropic/claude-haiku-4-5',
  'anthropic/claude-sonnet-4-6',
  'anthropic/claude-opus-4-6',
  'moonshot/kimi-k2.5',
  'openai-codex/gpt-5.1',
];

// ── Usage Store ──────────────────────────────────────────────────────────────

function loadUsage() {
  try {
    if (!fs.existsSync(USAGE_FILE)) return createFreshUsage();
    const data = JSON.parse(fs.readFileSync(USAGE_FILE, 'utf8'));
    // Auto-reset if it's a new UTC day
    const today = new Date().toISOString().split('T')[0];
    if (data.date !== today) {
      console.error(`[quota-monitor] New day detected (${today} vs ${data.date}) — resetting counters`);
      return createFreshUsage();
    }
    return data;
  } catch (e) {
    console.error('[quota-monitor] Could not load usage file, starting fresh:', e.message);
    return createFreshUsage();
  }
}

function createFreshUsage() {
  const today = new Date().toISOString().split('T')[0];
  const usage = {
    date: today,
    resetAt: new Date().toISOString(),
    models: {},
    events: [],
  };
  Object.keys(MODELS).forEach(modelId => {
    usage.models[modelId] = {
      inputTokens: 0,
      outputTokens: 0,
      requests: 0,
      estimatedCostUSD: 0,
      lastUsed: null,
      rateLimitHits: 0,
    };
  });
  saveUsage(usage);
  return usage;
}

function saveUsage(data) {
  fs.writeFileSync(USAGE_FILE, JSON.stringify(data, null, 2));
}

// ── Core Functions ───────────────────────────────────────────────────────────

/**
 * Record token usage after a model call.
 * Call this AFTER every model invocation.
 */
function recordUsage(modelId, inputTokens, outputTokens, rateLimitHit = false) {
  const usage = loadUsage();
  if (!usage.models[modelId]) {
    usage.models[modelId] = { inputTokens: 0, outputTokens: 0, requests: 0, estimatedCostUSD: 0, lastUsed: null, rateLimitHits: 0 };
  }

  const model = MODELS[modelId];
  const m = usage.models[modelId];

  m.inputTokens += inputTokens;
  m.outputTokens += outputTokens;
  m.requests += 1;
  m.lastUsed = new Date().toISOString();
  if (rateLimitHit) m.rateLimitHits += 1;

  if (model) {
    const cost = (inputTokens / 1_000_000) * model.inputCost + (outputTokens / 1_000_000) * model.outputCost;
    m.estimatedCostUSD += cost;
  }

  usage.events.push({
    ts: new Date().toISOString(),
    model: modelId,
    inputTokens,
    outputTokens,
    rateLimitHit,
  });

  // Keep events capped at 500 entries
  if (usage.events.length > 500) usage.events = usage.events.slice(-500);

  saveUsage(usage);
  return m;
}

/**
 * Get quota status for all models.
 * Returns within 500ms (pure file read — no API calls).
 */
function getQuotaStatus() {
  const start = Date.now();
  const usage = loadUsage();
  const status = { models: {}, summary: {}, timestamp: new Date().toISOString() };
  let totalHealthy = 0, totalWarning = 0, totalCritical = 0;

  FALLBACK_CHAIN.forEach(modelId => {
    const model = MODELS[modelId];
    if (!model) return;

    const m = usage.models[modelId] || { inputTokens: 0, outputTokens: 0, requests: 0, estimatedCostUSD: 0, rateLimitHits: 0 };
    const totalTokens = m.inputTokens + m.outputTokens;
    const usagePct = totalTokens / model.dailyTokenLimit;

    let health = 'healthy';
    if (usagePct >= CRITICAL_THRESHOLD) { health = 'critical'; totalCritical++; }
    else if (usagePct >= ALERT_THRESHOLD) { health = 'warning'; totalWarning++; }
    else { totalHealthy++; }

    // Estimate time to exhaustion based on hourly burn rate
    const hoursElapsed = (Date.now() - new Date(usage.resetAt).getTime()) / 3_600_000;
    const tokensPerHour = hoursElapsed > 0.1 ? totalTokens / hoursElapsed : 0;
    const tokensRemaining = model.dailyTokenLimit - totalTokens;
    const hoursToExhaustion = tokensPerHour > 0 ? tokensRemaining / tokensPerHour : Infinity;

    status.models[modelId] = {
      name: model.name,
      provider: model.provider,
      health,
      usage: {
        inputTokens: m.inputTokens,
        outputTokens: m.outputTokens,
        totalTokens,
        limitTokens: model.dailyTokenLimit,
        usagePct: Math.round(usagePct * 1000) / 10, // one decimal
        estimatedCostUSD: Math.round(m.estimatedCostUSD * 100) / 100,
      },
      requests: m.requests,
      rateLimitHits: m.rateLimitHits,
      forecast: {
        tokensPerHour: Math.round(tokensPerHour),
        hoursToExhaustion: isFinite(hoursToExhaustion) ? Math.round(hoursToExhaustion * 10) / 10 : null,
        willExhaustToday: hoursToExhaustion < (24 - hoursElapsed),
      },
      flatRate: model.flatRate || false,
    };
  });

  status.summary = {
    healthy: totalHealthy,
    warning: totalWarning,
    critical: totalCritical,
    fallbacksAvailable: FALLBACK_CHAIN.filter(m => status.models[m]?.health !== 'critical').length,
    checkMs: Date.now() - start,
    date: usage.date,
  };

  return status;
}

/**
 * Pre-spawn check: should we proceed with N parallel agents?
 * Returns { proceed: bool, recommendation: string, warnings: [] }
 */
function checkPreSpawn(parallelCount, primaryModel = 'anthropic/claude-sonnet-4-6') {
  const start = Date.now();
  const status = getQuotaStatus();
  const warnings = [];
  let proceed = true;
  let recommendation = 'PROCEED';

  const modelStatus = status.models[primaryModel];
  if (!modelStatus) {
    return {
      proceed: false,
      recommendation: 'BLOCK — unknown primary model',
      warnings: [`Unknown model: ${primaryModel}`],
      checkMs: Date.now() - start,
    };
  }

  // Check primary model
  if (modelStatus.health === 'critical') {
    proceed = false;
    recommendation = 'BLOCK — primary model at critical quota (>90%)';
    warnings.push(`⛔ ${modelStatus.name} is at ${modelStatus.usage.usagePct}% daily limit`);
  } else if (modelStatus.health === 'warning') {
    warnings.push(`⚠️  ${modelStatus.name} is at ${modelStatus.usage.usagePct}% daily limit (>70% warning)`);
    recommendation = 'CAUTION — consider using MiniMax M2.5 for screening pass';
  }

  // Check if spawning N parallel agents would exhaust quota
  const model = MODELS[primaryModel];
  if (model) {
    const tokensPerCv = model.avgCvTokens.input + model.avgCvTokens.output;
    const projectedTokens = parallelCount * tokensPerCv;
    const currentTokens = modelStatus.usage.totalTokens;
    const projectedPct = (currentTokens + projectedTokens) / model.dailyTokenLimit;

    if (projectedPct >= CRITICAL_THRESHOLD) {
      proceed = false;
      recommendation = `BLOCK — spawning ${parallelCount} agents would push ${modelStatus.name} to ${Math.round(projectedPct * 100)}% (>${CRITICAL_THRESHOLD * 100}%)`;
      warnings.push(`⛔ Projected usage after spawn: ${Math.round(projectedPct * 100)}%`);
    } else if (projectedPct >= ALERT_THRESHOLD) {
      warnings.push(`⚠️  After spawn, ${modelStatus.name} would be at ${Math.round(projectedPct * 100)}%`);
      if (recommendation === 'PROCEED') recommendation = 'CAUTION — quota will enter warning zone after this spawn';
    }
  }

  // Hard cap: >10 parallel = always require M2.5 screening first
  if (parallelCount > 10) {
    warnings.push(`⚠️  ${parallelCount} parallel agents exceeds safe limit (10). Recommend 2-phase: screen with M2.5 first, then top-10 with primary model.`);
    if (proceed) recommendation = 'CAUTION — batch too large; recommend phased approach';
  }

  // Check fallback health
  const availableFallbacks = FALLBACK_CHAIN.filter(m => {
    const s = status.models[m];
    return s && s.health !== 'critical' && m !== primaryModel;
  });

  if (availableFallbacks.length < 2) {
    warnings.push(`🔴 DANGER: Only ${availableFallbacks.length} healthy fallback(s) available. DO NOT proceed with large batch.`);
    if (availableFallbacks.length === 0) {
      proceed = false;
      recommendation = 'HARD BLOCK — no healthy fallbacks available. All models at risk.';
    }
  }

  return {
    proceed,
    recommendation,
    warnings,
    primaryModel,
    parallelCount,
    fallbacksAvailable: availableFallbacks.length,
    checkMs: Date.now() - start,
  };
}

/**
 * Estimate token cost for N CV generations.
 * Returns breakdown + recommendation.
 */
function estimateCvBatch(roleCount, primaryModel = 'anthropic/claude-sonnet-4-6') {
  const model = MODELS[primaryModel];
  const m2_5 = MODELS['minimax-portal/MiniMax-M2.5'];

  if (!model) return { error: `Unknown model: ${primaryModel}` };

  const perCvInput = model.avgCvTokens.input;
  const perCvOutput = model.avgCvTokens.output;
  const totalInput = roleCount * perCvInput;
  const totalOutput = roleCount * perCvOutput;
  const totalTokens = totalInput + totalOutput;
  const estimatedCost = (totalInput / 1_000_000) * model.inputCost + (totalOutput / 1_000_000) * model.outputCost;

  // Check current usage headroom
  const usage = loadUsage();
  const usedTokens = usage.models[primaryModel] ? usage.models[primaryModel].inputTokens + usage.models[primaryModel].outputTokens : 0;
  const headroom = model.dailyTokenLimit - usedTokens;
  const willFitToday = totalTokens <= headroom;

  // M2.5 screening estimate (cheaper first pass)
  const m2_5PerCv = m2_5.avgCvTokens.input + m2_5.avgCvTokens.output;
  const m2_5ScreeningTokens = Math.ceil(roleCount * m2_5PerCv * 0.5); // Screening = 50% of full CV work

  // Spacing recommendation
  const parallelSafe = Math.min(10, Math.floor(headroom / (perCvInput + perCvOutput)));
  const batchesNeeded = Math.ceil(roleCount / parallelSafe);
  const minutesBetweenBatches = 2; // 2-minute cooldown between batches

  return {
    roleCount,
    primaryModel: model.name,
    perRole: {
      inputTokens: perCvInput,
      outputTokens: perCvOutput,
      estimatedCostUSD: Math.round(((perCvInput / 1_000_000) * model.inputCost + (perCvOutput / 1_000_000) * model.outputCost) * 1000) / 1000,
    },
    total: {
      inputTokens: totalInput,
      outputTokens: totalOutput,
      totalTokens,
      estimatedCostUSD: Math.round(estimatedCost * 100) / 100,
    },
    quota: {
      dailyLimitTokens: model.dailyTokenLimit,
      usedTodayTokens: usedTokens,
      headroomTokens: headroom,
      willFitToday,
      usagePctAfterBatch: Math.round(((usedTokens + totalTokens) / model.dailyTokenLimit) * 1000) / 10,
    },
    recommendation: roleCount > 10 ? (
      `PHASE IT: Run ${parallelSafe} at a time, ${batchesNeeded} batches, ${minutesBetweenBatches}min cooldown. ` +
      `OR: Pre-screen all ${roleCount} with M2.5 (free, ~${Math.round(m2_5ScreeningTokens / 1000)}K tokens), then run top-10 with ${model.name}.`
    ) : (
      willFitToday ? `SAFE: ${roleCount} CVs fit within today's quota headroom.` :
        `CAUTION: ${roleCount} CVs may exceed today's headroom (${Math.round(headroom / 1000)}K tokens left). Recommend waiting for quota reset or switching models.`
    ),
    m2_5Screening: {
      tokensEstimate: m2_5ScreeningTokens,
      costUSD: 0,
      note: 'MiniMax M2.5 is flat-rate — screening is effectively free. Recommended for batches >10.',
    },
  };
}

/**
 * Record a rate limit hit for a model.
 */
function recordRateLimitHit(modelId) {
  const usage = loadUsage();
  if (!usage.models[modelId]) {
    usage.models[modelId] = { inputTokens: 0, outputTokens: 0, requests: 0, estimatedCostUSD: 0, lastUsed: null, rateLimitHits: 0 };
  }
  usage.models[modelId].rateLimitHits += 1;
  usage.events.push({ ts: new Date().toISOString(), model: modelId, event: 'rate_limit_hit' });
  saveUsage(usage);
}

// ── Formatting ───────────────────────────────────────────────────────────────

function formatStatus(status) {
  const bars = { healthy: '🟢', warning: '🟡', critical: '🔴' };
  const lines = [
    `\n📊 QUOTA STATUS — ${status.summary.date} UTC`,
    `   Healthy: ${status.summary.healthy} | Warning: ${status.summary.warning} | Critical: ${status.summary.critical}`,
    `   Fallbacks available: ${status.summary.fallbacksAvailable}/${FALLBACK_CHAIN.length}`,
    `   Check latency: ${status.summary.checkMs}ms`,
    '',
    '┌─────────────────────────────────────────────────────────────────┐',
  ];

  FALLBACK_CHAIN.forEach(modelId => {
    const m = status.models[modelId];
    if (!m) return;
    const bar = bars[m.health] || '⚫';
    const pct = m.usage.usagePct;
    const exhaustion = m.forecast.hoursToExhaustion !== null
      ? `(~${m.forecast.hoursToExhaustion}h left)`
      : '(stable)';
    const cost = m.flatRate ? '$0 (flat)' : `$${m.usage.estimatedCostUSD}`;
    const ratelimit = m.rateLimitHits > 0 ? ` ⚡${m.rateLimitHits}RL` : '';

    lines.push(`│ ${bar} ${m.name.padEnd(22)} ${String(pct + '%').padStart(6)} │ ${m.requests}req ${cost}${ratelimit} ${exhaustion}`);
  });

  lines.push('└─────────────────────────────────────────────────────────────────┘');
  return lines.join('\n');
}

// ── CLI ──────────────────────────────────────────────────────────────────────

function main() {
  const [,, command, ...args] = process.argv;

  switch (command) {
    case 'status': {
      const status = getQuotaStatus();
      console.log(formatStatus(status));
      // Exit with non-zero if any model is critical
      if (status.summary.critical > 0) process.exit(2);
      if (status.summary.warning > 0) process.exit(1);
      process.exit(0);
    }

    case 'check-spawn': {
      const n = parseInt(args[0], 10) || 1;
      const model = args[1] || 'anthropic/claude-sonnet-4-6';
      const result = checkPreSpawn(n, model);
      console.log(JSON.stringify(result, null, 2));
      if (!result.proceed) process.exit(2);
      if (result.warnings.length > 0) process.exit(1);
      process.exit(0);
    }

    case 'estimate-cv': {
      const n = parseInt(args[0], 10) || 1;
      const model = args[1] || 'anthropic/claude-sonnet-4-6';
      const result = estimateCvBatch(n, model);
      console.log(JSON.stringify(result, null, 2));
      process.exit(0);
    }

    case 'record': {
      const [modelId, inputTokens, outputTokens] = args;
      if (!modelId || !inputTokens) {
        console.error('Usage: record <modelId> <inputTokens> <outputTokens>');
        process.exit(1);
      }
      const result = recordUsage(modelId, parseInt(inputTokens, 10), parseInt(outputTokens || '0', 10));
      console.log(JSON.stringify(result, null, 2));
      process.exit(0);
    }

    case 'rate-limit': {
      const modelId = args[0];
      if (!modelId) { console.error('Usage: rate-limit <modelId>'); process.exit(1); }
      recordRateLimitHit(modelId);
      console.log(`Recorded rate limit hit for ${modelId}`);
      process.exit(0);
    }

    case 'reset': {
      const fresh = createFreshUsage();
      console.log(`Usage counters reset for ${fresh.date}`);
      process.exit(0);
    }

    case 'validate-keys': {
      // Fast key format validation (no API call — just sanity check format)
      const openclaw = JSON.parse(fs.readFileSync(path.join(process.env.HOME, '.openclaw/openclaw.json'), 'utf8'));
      const models = openclaw.models?.providers || {};
      const issues = [];

      Object.entries(models).forEach(([provider, cfg]) => {
        const key = cfg.apiKey || '';
        if (!key) {
          issues.push({ provider, issue: 'MISSING — no apiKey configured' });
        } else if (key === 'minimax-oauth') {
          issues.push({ provider, issue: 'INFO — uses OAuth (no key needed)' });
        } else if (key.length < 20) {
          issues.push({ provider, issue: `SUSPICIOUS — key too short (${key.length} chars)` });
        } else {
          const prefix = key.substring(0, 10) + '***';
          issues.push({ provider, issue: `OK — key present (${prefix}...)` });
        }
      });

      console.log(JSON.stringify(issues, null, 2));
      const hasErrors = issues.some(i => i.issue.startsWith('MISSING') || i.issue.startsWith('SUSPICIOUS'));
      process.exit(hasErrors ? 2 : 0);
    }

    default: {
      console.log(`
quota-monitor.js — OpenClaw Quota Monitor
Usage:
  node quota-monitor.js status                              Print quota status table
  node quota-monitor.js check-spawn <n> [model]            Pre-spawn safety check
  node quota-monitor.js estimate-cv <n> [model]            Estimate CV batch cost
  node quota-monitor.js record <model> <inputTok> <outTok> Record usage
  node quota-monitor.js rate-limit <model>                 Record rate limit hit
  node quota-monitor.js reset                              Reset daily counters
  node quota-monitor.js validate-keys                      Validate API key formats
      `);
      process.exit(0);
    }
  }
}

// Export for use as a module
module.exports = { recordUsage, getQuotaStatus, checkPreSpawn, estimateCvBatch, recordRateLimitHit, MODELS, FALLBACK_CHAIN };

// Run CLI if invoked directly
if (require.main === module) main();
