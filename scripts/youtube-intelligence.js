#!/usr/bin/env node
/**
 * YouTube Intelligence Scraper v3
 * Uses Tavily to find latest videos from tracked channels.
 * Saves to memory/knowledge/youtube-intelligence.md
 *
 * Run: node youtube-intelligence.js
 * Scheduled: Weekly Fridays 6 AM Cairo
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const CHANNELS = [
  // AI / Dev Tools
  { name: "Alex Finn", query: "Alex Finn OpenClaw YouTube 2026", topic: "openclaw,claude,ai-agents" },
  { name: "Nate Herk", query: "Nate Herk AI automation YouTube 2026", topic: "ai-automation,claude-code" },
  { name: "NetworkChuck", query: "NetworkChuck YouTube AI 2026", topic: "ai-tools,tech" },
  { name: "Matt Wolfe", query: "Matt Wolfe AI YouTube 2026", topic: "ai-news,tools" },
  // HealthTech
  { name: "Health Catalyst", query: "Health Catalyst YouTube digital health 2026", topic: "healthtech,analytics" },
  { name: "HIMSS", query: "HIMSS YouTube healthcare IT 2026", topic: "healthtech,healthcare-it" },
  // Leadership
  { name: "Harvard Business Review", query: "Harvard Business Review YouTube leadership 2026", topic: "strategy,leadership" },
  { name: "Simon Sinek", query: "Simon Sinek YouTube 2026", topic: "leadership,executive" },
];

const WORKSPACE = "/root/.openclaw/workspace";
const OUTPUT_FILE = path.join(WORKSPACE, "memory/knowledge/youtube-intelligence.md");
const TAVILY_KEY = "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";

function searchChannel(channel) {
  try {
    const result = execSync(
      `node ${WORKSPACE}/skills/tavily-search/scripts/search.mjs "${channel.query}" -n 4`,
      { env: { ...process.env, TAVILY_API_KEY: TAVILY_KEY }, encoding: "utf8", timeout: 20000 }
    );
    return result;
  } catch (e) {
    return "";
  }
}

function parseResults(raw) {
  const videos = [];
  const lines = raw.split("\n");
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.match(/^- \*\*(.+)\*\* \(relevance/)) {
      const title = line.match(/^- \*\*(.+)\*\*/)?.[1] || "";
      const urlLine = lines[i + 1]?.trim() || "";
      const snippet = lines[i + 2]?.trim() || "";
      if (urlLine.includes("youtube.com/watch")) {
        videos.push({ title, url: urlLine, snippet: snippet.substring(0, 200) });
      }
      i += 3;
    } else {
      i++;
    }
  }
  return videos.slice(0, 3);
}

function getAnswer(raw) {
  const match = raw.match(/## Answer\n\n([\s\S]*?)(?=\n---|\n## Sources|$)/);
  return match ? match[1].trim().substring(0, 400) : "";
}

async function main() {
  const now = new Date().toISOString().split("T")[0];
  const channelResults = [];

  console.log(`YouTube Intelligence — ${now}`);
  console.log(`Scanning ${CHANNELS.length} channels...\n`);

  for (const ch of CHANNELS) {
    process.stdout.write(`  ${ch.name}... `);
    const raw = searchChannel(ch);
    const videos = parseResults(raw);
    const answer = getAnswer(raw);

    if (videos.length > 0 || answer) {
      channelResults.push({ ...ch, videos, answer });
      console.log(`✅ ${videos.length} videos`);
    } else {
      console.log("nothing");
    }
  }

  // Build markdown output
  let output = `\n\n---\n\n## YouTube Weekly Scan | ${now}\n*${channelResults.length}/${CHANNELS.length} channels had content*\n\n`;

  for (const ch of channelResults) {
    output += `### ${ch.name}\n`;
    output += `**Tags:** #${ch.topic.replace(/,/g, " #")}\n\n`;
    if (ch.answer) output += `${ch.answer}\n\n`;
    for (const v of ch.videos) {
      output += `- **[${v.title}](${v.url})**\n`;
      if (v.snippet) output += `  ${v.snippet}\n`;
    }
    output += "\n";
  }

  output += `*For full transcripts: ask NASR to pull any URL above via Browser Relay*\n`;

  fs.appendFileSync(OUTPUT_FILE, output);
  console.log(`\n✅ Saved to youtube-intelligence.md`);
}

main().catch(console.error);
