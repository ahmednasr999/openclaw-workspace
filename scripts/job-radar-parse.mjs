#!/usr/bin/env node
// Job Radar v2 — Parser, deduplicator, and profile matcher
// Usage: node job-radar-parse.mjs <date> <seen-file-path>

import { readFileSync, writeFileSync, appendFileSync, existsSync } from 'fs';
import { createHash } from 'crypto';

const TAVILY_API_KEY = process.env.TAVILY_API_KEY;
const date = process.argv[2] || new Date().toISOString().split('T')[0];
const seenFile = process.argv[3] || '/root/.openclaw/workspace/memory/job-radar-seen.txt';

// Ahmed's profile — used for matching
const AHMED_PROFILE = {
  titles: ['VP', 'Director', 'Head of', 'CTO', 'COO', 'Chief', 'SVP', 'GM'],
  sectors: ['HealthTech', 'FinTech', 'Digital Transformation', 'PMO', 'AI', 'e-commerce', 'Digital Health', 'Technology'],
  locations: ['Dubai', 'UAE', 'Abu Dhabi', 'Riyadh', 'Saudi Arabia', 'Doha', 'Qatar', 'Bahrain', 'Kuwait', 'Oman', 'Muscat', 'GCC', 'Remote'],
  strengths: ['transformation', 'PMO', 'agile', 'scrum', 'AI', 'HealthTech', 'FinTech', 'hospitals', 'e-commerce', 'Talabat', 'TopMed', 'Saudi German'],
  salaryFloor: 50000, // AED
};

// Load seen URLs to avoid duplicates
function loadSeen() {
  if (!existsSync(seenFile)) return new Set();
  return new Set(readFileSync(seenFile, 'utf8').split('\n').filter(Boolean));
}

function saveSeen(seen) {
  writeFileSync(seenFile, [...seen].join('\n') + '\n');
}

// Hash a URL for deduplication
function hashUrl(url) {
  return createHash('md5').update(url).digest('hex').slice(0, 8);
}

// Score how well a result matches Ahmed's profile (0-100)
function profileMatch(result) {
  const text = `${result.title || ''} ${result.content || ''} ${result.url || ''}`.toLowerCase();
  let score = 0;
  const reasons = [];

  // Title match (40 points)
  for (const t of AHMED_PROFILE.titles) {
    if (text.includes(t.toLowerCase())) {
      score += 15;
      reasons.push(`${t}-level role`);
      break;
    }
  }

  // Sector match (30 points)
  const matchedSectors = AHMED_PROFILE.sectors.filter(s => text.includes(s.toLowerCase()));
  score += Math.min(matchedSectors.length * 10, 30);
  if (matchedSectors.length > 0) reasons.push(matchedSectors.slice(0, 2).join(', '));

  // Location match (20 points)
  const matchedLoc = AHMED_PROFILE.locations.find(l => text.includes(l.toLowerCase()));
  if (matchedLoc) {
    score += 20;
    reasons.push(matchedLoc);
  }

  // Strengths match (10 points)
  const matchedStrengths = AHMED_PROFILE.strengths.filter(s => text.includes(s.toLowerCase()));
  score += Math.min(matchedStrengths.length * 5, 10);
  if (matchedStrengths.length > 0) reasons.push(`matches: ${matchedStrengths.slice(0, 2).join(', ')}`);

  return { score: Math.min(score, 100), reasons };
}

// Tavily search
async function tavilySearch(query, maxResults = 8) {
  const response = await fetch('https://api.tavily.com/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      api_key: TAVILY_API_KEY,
      query,
      search_depth: 'basic',
      max_results: maxResults,
      include_answer: false,
    }),
  });
  const data = await response.json();
  return data.results || [];
}

// Format a single job result
function formatJob(result, match, rank) {
  const title = result.title || 'Unknown Role';
  const url = result.url || '';
  const snippet = (result.content || '').slice(0, 200).trim();
  const matchBar = '█'.repeat(Math.round(match.score / 10)) + '░'.repeat(10 - Math.round(match.score / 10));

  return [
    `### ${rank}. ${title}`,
    `**Match:** ${matchBar} ${match.score}% — ${match.reasons.join(' | ')}`,
    `**Link:** ${url}`,
    `**Summary:** ${snippet}...`,
    '',
  ].join('\n');
}

async function main() {
  const seen = loadSeen();
  const searches = [
    {
      label: 'VP/C-Suite Digital Transformation — UAE/Dubai',
      query: 'VP Director "Digital Transformation" OR "AI Strategy" OR "HealthTech" Dubai UAE 2026 job opening',
    },
    {
      label: 'PMO / Technology Leadership — GCC',
      query: '"Head of PMO" OR "Director PMO" OR "Head of Technology" OR "Head of AI" GCC UAE Saudi Arabia 2026 job',
    },
    {
      label: 'HealthTech / FinTech Executive — GCC',
      query: 'VP Director "Digital Health" OR "HealthTech" OR "FinTech" executive GCC Dubai Abu Dhabi 2026',
    },
    {
      label: 'C-Suite / GM — Saudi Arabia / Qatar',
      query: 'CTO COO "Chief Digital Officer" OR "General Manager" technology Riyadh Doha "Saudi Arabia" OR Qatar 2026',
    },
  ];

  const allResults = [];

  for (const search of searches) {
    try {
      const results = await tavilySearch(search.query);
      for (const r of results) {
        const url = r.url || '';
        const urlHash = hashUrl(url);

        // Skip if already seen
        if (seen.has(urlHash)) continue;

        const match = profileMatch(r);
        if (match.score >= 30) { // Only include relevant results
          allResults.push({ ...r, match, searchLabel: search.label });
          seen.add(urlHash);
        }
      }
    } catch (err) {
      process.stdout.write(`\n> Search failed: ${search.label} — ${err.message}\n`);
    }
  }

  // Sort by match score, take top 10
  allResults.sort((a, b) => b.match.score - a.match.score);
  const top = allResults.slice(0, 10);

  // Write output
  if (top.length === 0) {
    process.stdout.write(`\n> No new roles found today (all duplicates or below threshold).\n\n`);
    return;
  }

  process.stdout.write(`\n**${top.length} new roles found — sorted by profile match:**\n\n`);

  top.forEach((result, i) => {
    process.stdout.write(formatJob(result, result.match, i + 1));
  });

  // Save updated seen list
  saveSeen(seen);
}

main().catch(err => {
  process.stdout.write(`\n> Job Radar v2 error: ${err.message}\n`);
  process.exit(1);
});
