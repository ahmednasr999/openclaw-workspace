#!/usr/bin/env node

import { loadTavilyKey } from "./tavily-key.mjs";

function usage() {
  console.error(`Usage: research-search.mjs "query" [-n 10] [--category news|github|company|linkedin\ profile|research\ paper|tweet|video] [--type auto|neural|keyword] [--start YYYY-MM-DD]`);
  process.exit(2);
}

async function tavilySearch({ query, numResults, category, type, startPublishedDate }, apiKey) {
  const body = {
    api_key: apiKey,
    query,
    search_depth: type === "keyword" ? "basic" : "advanced",
    topic: category === "news" ? "news" : "general",
    max_results: numResults,
    include_answer: true,
    include_raw_content: false,
  };

  if (category === "news" && startPublishedDate) {
    const start = new Date(`${startPublishedDate}T00:00:00Z`);
    if (!Number.isNaN(start.getTime())) {
      const days = Math.max(1, Math.ceil((Date.now() - start.getTime()) / 86400000));
      body.days = days;
    }
  }

  const resp = await fetch("https://api.tavily.com/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`Tavily research search failed (${resp.status}): ${text.slice(0, 400)}`);
  }

  const data = await resp.json();
  return {
    provider: "tavily",
    answer: data?.answer ?? null,
    results: data?.results ?? [],
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
const apiKey = loadTavilyKey();
if (!apiKey) {
  console.error("Missing Tavily API key (env or config/tavily.json)");
  process.exit(1);
}

try {
  const result = await tavilySearch({ query, numResults, category, type, startPublishedDate }, apiKey);
  printResults({ query, category, type, ...result });
} catch (err) {
  console.error(err?.message || String(err));
  process.exit(1);
}
