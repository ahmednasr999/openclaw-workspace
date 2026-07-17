const DEFAULT_TTL_MS = 30 * 60 * 1000;
const DEFAULT_MAX_RUNS = 256;
const DEFAULT_MAX_URLS_PER_RUN = 256;
const MAX_URL_LENGTH = 4096;
const MAX_JSON_LENGTH = 1_000_000;
const MAX_RESULT_NODES = 2048;
const MAX_RESULT_DEPTH = 8;
const MAX_RESULT_FIELDS = 64;

const STRUCTURED_URL_KEYS = new Set([
  "url",
  "link",
  "href",
  "finalurl",
  "permalink",
]);

const JSON_CONTAINER_KEYS = new Set(["content", "data", "result", "results"]);
const STRUCTURED_WRAPPER_KEYS = new Set(["data", "details", "result"]);

function trimUnbalancedUrlClosers(value) {
  // Terminal prose punctuation is not URL authority. Literal terminal
  // punctuation must be percent-encoded so the network boundary is explicit.
  let candidate = value.replace(/[.,;:!?]+$/u, "");
  const pairs = { ")": "(", "]": "[", "}": "{" };
  while (candidate) {
    const closer = candidate.at(-1);
    const opener = pairs[closer];
    if (!opener) break;
    const openerCount = candidate.split(opener).length - 1;
    const closerCount = candidate.split(closer).length - 1;
    if (closerCount <= openerCount) break;
    candidate = candidate.slice(0, -1);
  }
  return candidate;
}

function trimMarkdownUrlToken(value) {
  const escapedClosers = [];
  const protectedValue = value.replace(/\\([)\]}])/g, (_match, closer) => {
    const index = escapedClosers.push(closer) - 1;
    return `\uE000${index}\uE001`;
  });
  const trimmed = trimUnbalancedUrlClosers(protectedValue);
  return trimmed.replace(/\uE000(\d+)\uE001/g, (_match, index) => escapedClosers[Number(index)] ?? "");
}

const MARKDOWN_MARKERS = ["***", "___", "**", "~~", "__", "*", "_"];

function scanMarkdownProse(prompt, start, end, state) {
  for (let position = start; position < end; position += 1) {
    if (prompt[position] === "`") {
      let tickCount = 1;
      while (prompt[position + tickCount] === "`") tickCount += 1;
      let backslashes = 0;
      for (let index = position - 1; index >= 0 && prompt[index] === "\\"; index -= 1) {
        backslashes += 1;
      }
      if (backslashes % 2 === 1) {
        position += tickCount - 1;
        continue;
      }
      if (state.codeTicks === 0) state.codeTicks = tickCount;
      else if (state.codeTicks === tickCount) state.codeTicks = 0;
      position += tickCount - 1;
      continue;
    }
    if (state.codeTicks !== 0) continue;

    for (const marker of MARKDOWN_MARKERS) {
      if (prompt.slice(position, position + marker.length) !== marker) continue;
      const markerChar = marker[0];
      if (prompt[position - 1] === markerChar || prompt[position + marker.length] === markerChar) continue;
      let backslashes = 0;
      for (let index = position - 1; index >= 0 && prompt[index] === "\\"; index -= 1) {
        backslashes += 1;
      }
      if (backslashes % 2 === 1) break;

      const previous = prompt[position - 1];
      const next = prompt[position + marker.length];
      const previousWhitespace = previous === undefined || /\s/u.test(previous);
      const nextWhitespace = next === undefined || /\s/u.test(next);
      const previousPunctuation = previous !== undefined && /[\p{P}\p{S}]/u.test(previous);
      const nextPunctuation = next !== undefined && /[\p{P}\p{S}]/u.test(next);
      const leftFlanking = !nextWhitespace && (!nextPunctuation || previousWhitespace || previousPunctuation);
      const rightFlanking = !previousWhitespace && (!previousPunctuation || nextWhitespace || nextPunctuation);
      const underscore = markerChar === "_";
      const canOpen = leftFlanking && (!underscore || !rightFlanking || previousPunctuation);
      const canClose = rightFlanking && (!underscore || !leftFlanking || nextPunctuation);
      if (canClose && state.markers.at(-1) === marker) state.markers.pop();
      else if (canOpen) state.markers.push(marker);
      position += marker.length - 1;
      break;
    }
  }
}

function normalizeEscapedTerminalMarker(value) {
  for (const marker of MARKDOWN_MARKERS) {
    if (!value.endsWith(marker)) continue;
    const trailingBackslashes = trailingBackslashCountBeforeMarker(value, marker);
    if (trailingBackslashes % 2 !== 1) continue;
    return {
      escaped: true,
      value: trailingBackslashes === 1
        ? `${value.slice(0, -marker.length - 1)}${marker}`
        : "",
    };
  }
  return { escaped: false, value };
}

function stripMarkdownClosingSuffix(value, markerStack) {
  for (let count = markerStack.length; count >= 1; count -= 1) {
    const suffix = markerStack.slice(-count).reverse().join("");
    if (!value.endsWith(suffix)) continue;
    markerStack.splice(-count, count);
    return value.slice(0, -suffix.length);
  }
  return value;
}

function trailingBackslashCountBeforeMarker(value, marker) {
  let count = 0;
  for (
    let index = value.length - marker.length - 1;
    index >= 0 && value[index] === "\\";
    index -= 1
  ) {
    count += 1;
  }
  return count;
}

export function normalizeHttpUrl(value, { stripFragment = true } = {}) {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  if (!trimmed || trimmed.length > MAX_URL_LENGTH) return null;

  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return null;
    if (parsed.username || parsed.password) return null;
    if (stripFragment) parsed.hash = "";
    return parsed.href;
  } catch {
    return null;
  }
}

export function extractPromptUrls(prompt, { stripFragment = true } = {}) {
  if (typeof prompt !== "string" || !prompt) return [];
  const normalized = [];
  const markdownState = { codeTicks: 0, markers: [] };
  let cursor = 0;
  for (const match of prompt.matchAll(/https?:\/\/[^\s<>"'`]+/giu)) {
    scanMarkdownProse(prompt, cursor, match.index, markdownState);
    let candidateText = match[0].replace(/[.,;:!?]+$/u, "");
    const escapedTerminal = normalizeEscapedTerminalMarker(candidateText);
    candidateText = escapedTerminal.value;
    if (!escapedTerminal.escaped && markdownState.codeTicks === 0) {
      candidateText = stripMarkdownClosingSuffix(candidateText, markdownState.markers);
    }
    const candidate = normalizeHttpUrl(trimMarkdownUrlToken(candidateText), { stripFragment });
    if (candidate) normalized.push(candidate);
    cursor = match.index + match[0].length;
  }
  return [...new Set(normalized)];
}

function maybeParseJsonContainer(key, value) {
  if (!JSON_CONTAINER_KEYS.has(key) || typeof value !== "string") return null;
  if (value.length > MAX_JSON_LENGTH) return null;
  const trimmed = value.trim();
  if (!trimmed || trimmed.length > MAX_JSON_LENGTH) return null;
  if (!trimmed.startsWith("{") && !trimmed.startsWith("[")) return null;
  try {
    return JSON.parse(trimmed);
  } catch {
    return null;
  }
}

function addDirectResultUrls(entry, urls, stripFragment, budget) {
  if (budget.remaining <= 0) return;
  budget.remaining -= 1;
  if (!entry || typeof entry !== "object" || Array.isArray(entry)) return;

  let inspectedFields = 0;
  for (const rawKey in entry) {
    if (!Object.hasOwn(entry, rawKey)) continue;
    inspectedFields += 1;
    if (inspectedFields > MAX_RESULT_FIELDS) break;
    const key = rawKey.toLowerCase();
    const value = entry[rawKey];
    if (!STRUCTURED_URL_KEYS.has(key) || typeof value !== "string") continue;
    const normalized = normalizeHttpUrl(value, { stripFragment });
    if (normalized) urls.add(normalized);
  }
}

export function extractStructuredSearchUrls(result, { stripFragment = true } = {}) {
  const urls = new Set();
  const seen = new Set();
  const budget = { remaining: MAX_RESULT_NODES };

  function visitContainer(value, depth = 0) {
    if (budget.remaining <= 0 || depth > MAX_RESULT_DEPTH || value === null || value === undefined) return;
    if (typeof value === "string" || typeof value !== "object" || seen.has(value)) return;
    budget.remaining -= 1;
    seen.add(value);

    if (Array.isArray(value)) {
      // Generic arrays are untrusted content. Result entries are accepted only
      // by the explicit `results` branch below.
      return;
    }

    if (Object.hasOwn(value, "results")) {
      const rawResults = value.results;
      const parsedResults = maybeParseJsonContainer("results", rawResults);
      const results = parsedResults ?? rawResults;
      if (Array.isArray(results)) {
        for (const entry of results) {
          if (budget.remaining <= 0) break;
          addDirectResultUrls(entry, urls, stripFragment, budget);
        }
      } else {
        visitContainer(results, depth + 1);
      }
    }

    let inspectedFields = 0;
    for (const rawKey in value) {
      if (!Object.hasOwn(value, rawKey)) continue;
      inspectedFields += 1;
      if (inspectedFields > MAX_RESULT_FIELDS || budget.remaining <= 0) break;
      const key = rawKey.toLowerCase();
      if (key === "results") continue;
      budget.remaining -= 1;
      const childValue = value[rawKey];
      const parsed = maybeParseJsonContainer(key, childValue);
      if (parsed !== null) {
        visitContainer(parsed, depth + 1);
      } else if (STRUCTURED_WRAPPER_KEYS.has(key)) {
        visitContainer(childValue, depth + 1);
      }
    }
  }

  visitContainer(result);
  return [...urls];
}

function guardedCandidate(toolName, params) {
  if (toolName === "web_fetch") return { guarded: true, url: params?.url };
  if (toolName !== "browser") return { guarded: false };

  const action = typeof params?.action === "string" ? params.action.toLowerCase() : "";
  if (action === "evaluate") return { guarded: true, javascript: true };
  if (action === "wait" && typeof params?.fn === "string" && params.fn.trim()) {
    return { guarded: true, javascript: true };
  }
  if (action === "act") {
    const request = params?.request;
    const kind = typeof request?.kind === "string" ? request.kind.toLowerCase() : "";
    if (kind === "evaluate" || (kind === "wait" && typeof request?.fn === "string" && request.fn.trim())) {
      return { guarded: true, javascript: true };
    }
    return { guarded: false };
  }
  if (!new Set(["open", "navigate", "goto"]).has(action)) return { guarded: false };
  const targetUrl = typeof params?.targetUrl === "string" ? params.targetUrl : undefined;
  const url = typeof params?.url === "string" ? params.url : undefined;
  if (
    targetUrl
    && url
    && normalizeHttpUrl(targetUrl, { stripFragment: false })
      !== normalizeHttpUrl(url, { stripFragment: false })
  ) {
    return { guarded: true, conflict: true };
  }
  return { guarded: true, url: targetUrl || url };
}

export class EgressProvenancePolicy {
  constructor({
    ttlMs = DEFAULT_TTL_MS,
    maxRuns = DEFAULT_MAX_RUNS,
    maxUrlsPerRun = DEFAULT_MAX_URLS_PER_RUN,
  } = {}) {
    this.ttlMs = Math.max(1, ttlMs);
    this.maxRuns = Math.max(1, maxRuns);
    this.maxUrlsPerRun = Math.max(1, maxUrlsPerRun);
    this.runs = new Map();
  }

  sweep(now = Date.now()) {
    for (const [runId, state] of this.runs) {
      if (now - state.updatedAt > this.ttlMs) this.runs.delete(runId);
    }
    while (this.runs.size > this.maxRuns) {
      const oldestRunId = this.runs.keys().next().value;
      if (oldestRunId === undefined) break;
      this.runs.delete(oldestRunId);
    }
  }

  beginRun(runId, prompt, now = Date.now()) {
    if (typeof runId !== "string" || !runId.trim()) return false;
    this.sweep(now);
    const allowed = new Set(extractPromptUrls(prompt).slice(0, this.maxUrlsPerRun));
    const browserAllowed = new Set(
      extractPromptUrls(prompt, { stripFragment: false }).slice(0, this.maxUrlsPerRun),
    );
    this.runs.delete(runId);
    this.runs.set(runId, { allowed, browserAllowed, updatedAt: now });
    this.sweep(now);
    return true;
  }

  hasRun(runId, now = Date.now()) {
    this.sweep(now);
    return typeof runId === "string" && this.runs.has(runId);
  }

  recordSearchResults(runId, result, now = Date.now()) {
    this.sweep(now);
    if (typeof runId !== "string" || !runId.trim()) return 0;
    let state = this.runs.get(runId);
    if (!state) {
      state = { allowed: new Set(), browserAllowed: new Set(), updatedAt: now };
      this.runs.set(runId, state);
      this.sweep(now);
    }

    let added = 0;
    for (const url of extractStructuredSearchUrls(result)) {
      if (state.allowed.size >= this.maxUrlsPerRun) break;
      if (!state.allowed.has(url)) {
        state.allowed.add(url);
        added += 1;
      }
    }
    for (const url of extractStructuredSearchUrls(result, { stripFragment: false })) {
      if (state.browserAllowed.size >= this.maxUrlsPerRun) break;
      state.browserAllowed.add(url);
    }
    state.updatedAt = now;
    this.runs.delete(runId);
    this.runs.set(runId, state);
    return added;
  }

  authorize(toolName, params, runId, now = Date.now()) {
    const candidate = guardedCandidate(toolName, params);
    if (!candidate.guarded) return { allowed: true, reason: "not-guarded" };
    if (candidate.javascript) return { allowed: false, reason: "javascript-capable" };
    if (candidate.conflict) return { allowed: false, reason: "conflicting-url" };

    this.sweep(now);
    if (typeof runId !== "string" || !runId.trim()) {
      return { allowed: false, reason: "missing-run" };
    }
    const state = this.runs.get(runId);
    if (!state) return { allowed: false, reason: "unknown-run" };

    const browserNavigation = toolName === "browser";
    const normalized = normalizeHttpUrl(candidate.url, { stripFragment: !browserNavigation });
    if (!normalized) return { allowed: false, reason: "invalid-url" };
    const allowedUrls = browserNavigation ? state.browserAllowed : state.allowed;
    if (!allowedUrls.has(normalized)) return { allowed: false, reason: "unproven-url" };

    state.updatedAt = now;
    return { allowed: true, reason: "proven-url" };
  }

  endRun(runId) {
    if (typeof runId === "string") this.runs.delete(runId);
  }

  stats() {
    return {
      runs: this.runs.size,
      urls: [...this.runs.values()].reduce((sum, state) => sum + state.allowed.size, 0),
    };
  }
}
