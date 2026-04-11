#!/usr/bin/env node

import fs from "fs";

const MCP_URL = "https://connect.composio.dev/mcp";
const OPENCLAW_CONFIG = "/root/.openclaw/openclaw.json";

function usage() {
  console.error(`Usage: research-search.mjs "query" [-n 10] [--category news|github|company|linkedin\ profile|research\ paper|tweet|video] [--type auto|neural|keyword] [--start YYYY-MM-DD]`);
  process.exit(2);
}

function loadConsumerKey() {
  const envKey = (process.env.COMPOSIO_CONSUMER_KEY ?? "").trim();
  if (envKey) return envKey;

  try {
    const raw = fs.readFileSync(OPENCLAW_CONFIG, "utf8");
    const parsed = JSON.parse(raw);
    return String(parsed?.plugins?.entries?.composio?.config?.consumerKey ?? "").trim();
  } catch {
    return "";
  }
}

async function mcpCall(method, params, consumerKey, timeoutMs = 45000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const resp = await fetch(MCP_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "x-consumer-api-key": consumerKey,
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: Date.now() % 1000000,
        method,
        params,
      }),
      signal: controller.signal,
    });

    const text = await resp.text();
    if (!resp.ok) {
      throw new Error(`research search failed (${resp.status}): ${text.slice(0, 400)}`);
    }

    for (const line of text.split("\n")) {
      if (!line.startsWith("data:")) continue;
      const payload = JSON.parse(line.slice(5).trim());
      if (payload.error) {
        throw new Error(typeof payload.error === "string" ? payload.error : JSON.stringify(payload.error));
      }
      return payload.result ?? null;
    }

    throw new Error("No MCP result returned");
  } finally {
    clearTimeout(timeout);
  }
}

async function initialize(consumerKey) {
  await mcpCall("initialize", {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: "research-search", version: "1.1" },
  }, consumerKey);
}

async function runTool(tool_slug, argumentsPayload, consumerKey, timeoutMs = 60000) {
  const result = await mcpCall("tools/call", {
    name: "COMPOSIO_MULTI_EXECUTE_TOOL",
    arguments: {
      tools: [{ tool_slug, arguments: argumentsPayload }],
      thought: "Run research search through the configured Composio path.",
      sync_response_to_workbench: false,
      current_step: "RESEARCH_SEARCH",
      current_step_metric: "1/1 query",
    },
  }, consumerKey, timeoutMs);

  const content = result?.content ?? [];
  const text = content?.[0]?.text ?? "";
  if (!text) throw new Error(`No content returned for ${tool_slug}`);
  return JSON.parse(text);
}

async function exaSearch({ query, numResults, category, type, startPublishedDate }, consumerKey) {
  const argumentsPayload = {
    query,
    type,
    numResults,
  };

  if (category) argumentsPayload.category = category;
  if (startPublishedDate) argumentsPayload.startPublishedDate = startPublishedDate;

  const outer = await runTool("EXA_SEARCH", argumentsPayload, consumerKey);
  const run = outer?.data?.results?.[0]?.response ?? {};

  if (!outer?.successful || !run?.successful) {
    const msg = run?.error || outer?.error || "Exa search returned unsuccessful response";
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }

  return {
    provider: "exa-via-composio",
    answer: null,
    results: run?.data?.results ?? [],
  };
}

async function searchWeb(query, consumerKey) {
  const outer = await runTool("COMPOSIO_SEARCH_WEB", { query }, consumerKey, 45000);
  const run = outer?.data?.results?.[0]?.response ?? {};

  if (!outer?.successful || !run?.successful) {
    const msg = run?.error || outer?.error || "Composio search returned unsuccessful response";
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }

  const data = run?.data ?? {};
  return {
    provider: "composio-search-web",
    answer: data?.answer ?? null,
    results: (data?.citations ?? []).map(c => ({
      title: c.title,
      url: c.url,
      text: c.snippet || c.text || "",
      publishedDate: c.publishedDate || "",
    })),
  };
}

function printResults({ query, category, type, answer, provider, note, results }) {
  if (answer) {
    console.log("## Answer\n");
    console.log(answer);
    console.log("\n---\n");
  }

  console.log("## Research Sources\n");
  const bits = [`provider: ${provider}`, `type: ${type}`];
  if (category) bits.push(`category: ${category}`);
  if (note) bits.push(note);
  console.log(`_(${bits.join(", ")})_\n`);
  console.log(`query: ${query}\n`);

  for (const r of results) {
    const title = String(r?.title ?? "").trim();
    const url = String(r?.url ?? "").trim();
    const text = String(r?.text ?? r?.snippet ?? r?.content ?? "").trim();
    const published = String(r?.publishedDate ?? "").trim();
    const score = typeof r?.score === "number" ? ` (relevance: ${(r.score * 100).toFixed(0)}%)` : "";

    if (!title || !url) continue;
    console.log(`- **${title}**${score}`);
    console.log(`  ${url}`);
    if (published) console.log(`  published: ${published}`);
    if (text) console.log(`  ${text.slice(0, 400)}${text.length > 400 ? "..." : ""}`);
    console.log();
  }
}

const args = process.argv.slice(2);
if (args.length === 0 || args[0] === "-h" || args[0] === "--help") usage();

const query = args[0];
let numResults = 10;
let category = "";
let type = "auto";
let startPublishedDate = "";

for (let i = 1; i < args.length; i++) {
  const a = args[i];
  if (a === "-n") {
    numResults = Number.parseInt(args[i + 1] ?? "10", 10);
    i++;
    continue;
  }
  if (a === "--category") {
    category = args[i + 1] ?? "";
    i++;
    continue;
  }
  if (a === "--type") {
    type = args[i + 1] ?? "auto";
    i++;
    continue;
  }
  if (a === "--start") {
    startPublishedDate = args[i + 1] ?? "";
    i++;
    continue;
  }
  console.error(`Unknown arg: ${a}`);
  usage();
}

numResults = Math.max(1, Math.min(numResults, 20));
const consumerKey = loadConsumerKey();
if (!consumerKey) {
  console.error("Missing Composio consumer key in env or local config");
  process.exit(1);
}

try {
  await initialize(consumerKey);

  try {
    const exa = await exaSearch({ query, numResults, category, type, startPublishedDate }, consumerKey);
    printResults({ query, category, type, ...exa });
  } catch (err) {
    console.error(`[research-search] Exa path unavailable, falling back to Composio search web: ${err.message}`);
    const fallback = await searchWeb(query, consumerKey);
    printResults({ query, category, type, ...fallback, note: "exa path unavailable, used search-web fallback" });
  }
} catch (err) {
  console.error(err?.message || String(err));
  process.exit(1);
}
