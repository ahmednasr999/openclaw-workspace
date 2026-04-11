#!/usr/bin/env node

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

function usage() {
  console.error(`Usage: search.mjs "query" [-n 5] [--deep] [--topic general|news] [--days 7]`);
  process.exit(2);
}

function loadTavilyKey() {
  const envKey = (process.env.TAVILY_API_KEY ?? "").trim();
  if (envKey) return envKey;

  try {
    const here = path.dirname(fileURLToPath(import.meta.url));
    const configPath = path.resolve(here, "../../../config/tavily.json");
    const raw = fs.readFileSync(configPath, "utf8");
    const parsed = JSON.parse(raw);
    return String(parsed?.api_key ?? "").trim();
  } catch {
    return "";
  }
}

const args = process.argv.slice(2);
if (args.length === 0 || args[0] === "-h" || args[0] === "--help") usage();

const query = args[0];
let n = 5;
let searchDepth = "basic";
let topic = "general";
let days = null;

for (let i = 1; i < args.length; i++) {
  const a = args[i];
  if (a === "-n") {
    n = Number.parseInt(args[i + 1] ?? "5", 10);
    i++;
    continue;
  }
  if (a === "--deep") {
    searchDepth = "advanced";
    continue;
  }
  if (a === "--topic") {
    topic = args[i + 1] ?? "general";
    i++;
    continue;
  }
  if (a === "--days") {
    days = Number.parseInt(args[i + 1] ?? "7", 10);
    i++;
    continue;
  }
  console.error(`Unknown arg: ${a}`);
  usage();
}

const maxResults = Math.max(1, Math.min(n, 20));
const apiKey = loadTavilyKey();
const searxngUrl = (process.env.SEARXNG_URL ?? "http://127.0.0.1:8090").replace(/\/$/, "");

function printResults({ answer, results, provider, note }) {
  if (answer) {
    console.log("## Answer\n");
    console.log(answer);
    console.log("\n---\n");
  }

  console.log("## Sources\n");
  if (provider || note) {
    const bits = [];
    if (provider) bits.push(`provider: ${provider}`);
    if (note) bits.push(note);
    console.log(`_(${bits.join(", ")})_\n`);
  }

  for (const r of results.slice(0, maxResults)) {
    const title = String(r?.title ?? "").trim();
    const url = String(r?.url ?? "").trim();
    const content = String(r?.content ?? r?.snippet ?? "").trim();
    const score = r?.score ? ` (relevance: ${(r.score * 100).toFixed(0)}%)` : "";

    if (!title || !url) continue;
    console.log(`- **${title}**${score}`);
    console.log(`  ${url}`);
    if (content) {
      console.log(`  ${content.slice(0, 300)}${content.length > 300 ? "..." : ""}`);
    }
    console.log();
  }
}

async function runTavily() {
  if (!apiKey) {
    throw new Error("Missing Tavily API key (env or config/tavily.json)");
  }

  const body = {
    api_key: apiKey,
    query,
    search_depth: searchDepth,
    topic,
    max_results: maxResults,
    include_answer: true,
    include_raw_content: false,
  };

  if (topic === "news" && days) {
    body.days = days;
  }

  const resp = await fetch("https://api.tavily.com/search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`Tavily Search failed (${resp.status}): ${text}`);
  }

  const data = await resp.json();
  return {
    provider: "tavily",
    answer: data.answer,
    results: data.results ?? [],
  };
}

async function runSearxng() {
  const params = new URLSearchParams({
    q: query,
    format: "json",
    language: "all",
    safesearch: "0",
    categories: topic === "news" ? "news" : "general",
  });

  const resp = await fetch(`${searxngUrl}/search?${params.toString()}`);
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`SearXNG search failed (${resp.status}): ${text}`);
  }

  const data = await resp.json();
  return {
    provider: "searxng",
    answer: null,
    note: topic === "news" && days ? `days filter not applied on fallback (${days})` : null,
    results: (data.results ?? []).map(r => ({
      title: r.title,
      url: r.url,
      content: r.content,
    })),
  };
}

try {
  try {
    const tavily = await runTavily();
    printResults(tavily);
  } catch (err) {
    console.error(`[search-router] Tavily unavailable, falling back to local SearXNG: ${err.message}`);
    const fallback = await runSearxng();
    printResults(fallback);
  }
} catch (err) {
  console.error(err.message || String(err));
  process.exit(1);
}
