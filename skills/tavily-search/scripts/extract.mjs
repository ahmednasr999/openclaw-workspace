#!/usr/bin/env node

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

function usage() {
  console.error(`Usage: extract.mjs "url1" ["url2" ...]`);
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

const urls = args.filter(a => !a.startsWith("-"));

if (urls.length === 0) {
  console.error("No URLs provided");
  usage();
}

const apiKey = loadTavilyKey();
if (!apiKey) {
  console.error("Missing Tavily API key (env or config/tavily.json)");
  process.exit(1);
}

const resp = await fetch("https://api.tavily.com/extract", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    api_key: apiKey,
    urls,
  }),
});

if (!resp.ok) {
  const text = await resp.text().catch(() => "");
  throw new Error(`Tavily Extract failed (${resp.status}): ${text}`);
}

const data = await resp.json();

const results = data.results ?? [];
const failed = data.failed_results ?? [];

for (const r of results) {
  const url = String(r?.url ?? "").trim();
  const content = String(r?.raw_content ?? "").trim();

  console.log(`# ${url}\n`);
  console.log(content || "(no content extracted)");
  console.log("\n---\n");
}

if (failed.length > 0) {
  console.log("## Failed URLs\n");
  for (const f of failed) {
    console.log(`- ${f.url}: ${f.error}`);
  }
}
