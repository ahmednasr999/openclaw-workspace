#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve('output/creator-channel-audit-20260819');
const RAW = path.join(ROOT, 'raw');

const creators = [
  ['Sabrina Ramonov', 'sabrina-ramonov.ndjson'],
  ['Jack Roberts', 'jack-roberts.ndjson'],
  ['Nate Herk', 'nate-herk.ndjson'],
  ['Chase AI', 'chase-ai.ndjson'],
  ['Dan Martell', 'dan-martell.ndjson'],
  ['Kyle Balmer — AI with Kyle', 'kyle-balmer.ndjson'],
  ['Riley Brown', 'riley-brown.ndjson'],
];

const themes = [
  {
    name: 'Agent systems',
    weight: 5,
    patterns: [
      /\bai agents?\b/i, /\bagentic\b/i, /\bmulti[- ]?agent\b/i, /\bopenclaw\b/i,
      /\bhermes\b/i, /\bclaude (?:code|cowork)\b/i, /\bcodex\b/i, /\bmcp\b/i,
      /\bcomputer use\b/i, /\bautonomous\b/i, /\bmanus\b/i, /\bantigravity\b/i,
    ],
  },
  {
    name: 'Automation and orchestration',
    weight: 5,
    patterns: [
      /\bautomation\b/i, /\bautomate\b/i, /\bworkflow\b/i, /\bn8n\b/i,
      /\bzapier\b/i, /\bmake\.com\b/i, /\bwebhooks?\b/i, /\bapi\b/i,
      /\bnotion\b/i, /\bairtable\b/i, /\borchestrat/i,
    ],
  },
  {
    name: 'Executive AI governance',
    weight: 5,
    patterns: [
      /\bgovernance\b/i, /\benterprise ai\b/i, /\bsecurity\b/i, /\bprivacy\b/i,
      /\brisk\b/i, /\bcompliance\b/i, /\bproject management\b/i, /\bpmo\b/i,
      /\broadmap\b/i, /\boperating model\b/i,
    ],
  },
  {
    name: 'Career and LinkedIn',
    weight: 5,
    patterns: [
      /\blinkedin\b/i, /\bresume\b/i, /\bcv\b/i, /\binterviews?\b/i,
      /\bjob search\b/i, /\bcareer\b/i, /\brecruit/i,
    ],
  },
  {
    name: 'Research, memory, and knowledge',
    weight: 4,
    patterns: [
      /\bresearch\b/i, /\brag\b/i, /\bvector\b/i, /\bknowledge base\b/i,
      /\bmemory\b/i, /\bscrap(?:e|ing|er)\b/i, /\bdatabase\b/i,
      /\bspreadsheet\b/i, /\bpdf\b/i, /\bnotebooklm\b/i,
    ],
  },
  {
    name: 'Content and executive brand',
    weight: 4,
    patterns: [
      /\bcontent\b/i, /\bsocial media\b/i, /\byoutube\b/i, /\bvideo\b/i,
      /\bimages?\b/i, /\bvisual\b/i, /\bavatar\b/i, /\bvoice\b/i,
      /\bheygen\b/i, /\bcanva\b/i, /\bgamma\b/i, /\bstorytell/i, /\bviral\b/i,
    ],
  },
  {
    name: 'Products, apps, and websites',
    weight: 3,
    patterns: [
      /\bwebsite\b/i, /\bapps?\b/i, /\bbuild\b/i, /\bcode\b/i,
      /\bno[- ]?code\b/i, /\blovable\b/i, /\breplit\b/i, /\bbolt\b/i,
      /\bv0\b/i, /\bdesign\b/i, /\bsaas\b/i,
    ],
  },
  {
    name: 'AI tools and prompting',
    weight: 3,
    patterns: [
      /\bchatgpt\b/i, /\bclaude\b/i, /\bgemini\b/i, /\bgrok\b/i,
      /\bperplexity\b/i, /\bdeepseek\b/i, /\bprompts?\b/i, /\bllm\b/i,
      /\bartificial intelligence\b/i, /\bai tools?\b/i, /\bai model\b/i,
    ],
  },
  {
    name: 'Business and productization',
    weight: 3,
    patterns: [
      /\bbusiness\b/i, /\bagency\b/i, /\bconsult/i, /\bclients?\b/i,
      /\boffer\b/i, /\bpricing\b/i, /\bstartup\b/i, /\bmonetiz/i,
      /\bmake money\b/i, /\bincome\b/i, /\bsales?\b/i, /\bmarket/i,
    ],
  },
  {
    name: 'Leadership and productivity',
    weight: 2,
    patterns: [
      /\bleadership\b/i, /\bceo\b/i, /\bexecutive\b/i, /\bdelegate\b/i,
      /\bteam\b/i, /\bproductivity\b/i, /\btime management\b/i,
      /\bscale\b/i, /\bsystems?\b/i, /\bdecision/i,
    ],
  },
];

const directBoosts = [
  /\bopenclaw\b/i, /\bhermes\b/i, /\bcodex\b/i, /\bn8n\b/i, /\bmcp\b/i,
  /\blinkedin\b/i, /\bai agents?\b/i, /\bclaude (?:code|cowork)\b/i,
  /\bgovernance\b/i, /\bproject management\b/i, /\bpmo\b/i,
];

function readNdjson(file) {
  return fs.readFileSync(file, 'utf8').split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
}

function classify(title) {
  const matched = [];
  let score = 0;
  for (const theme of themes) {
    if (theme.patterns.some((pattern) => pattern.test(title))) {
      matched.push(theme.name);
      score += theme.weight;
    }
  }
  score += directBoosts.filter((pattern) => pattern.test(title)).length * 2;
  const priority = score >= 10 ? 'P1 transcript' : score >= 6 ? 'P2 transcript' : score >= 3 ? 'P3 review' : 'P4 low signal';
  return { score, priority, themes: matched };
}

function csv(value) {
  const text = value == null ? '' : Array.isArray(value) ? value.join(' | ') : String(value);
  return `"${text.replaceAll('"', '""')}"`;
}

function formatHours(seconds) {
  return (seconds / 3600).toFixed(1);
}

const inventory = [];
const rollups = [];

for (const [creator, filename] of creators) {
  const records = readNdjson(path.join(RAW, filename));
  const seen = new Set();
  let knownDurationSeconds = 0;
  let missingDuration = 0;
  for (const record of records) {
    if (seen.has(record.id)) throw new Error(`Duplicate video id ${record.id} in ${creator}`);
    seen.add(record.id);
    if (record.duration == null) missingDuration += 1;
    else knownDurationSeconds += record.duration;
    inventory.push({ creator, ...record, ...classify(record.title || '') });
  }
  rollups.push({ creator, count: records.length, knownDurationSeconds, missingDuration });
}

fs.mkdirSync(ROOT, { recursive: true });

const headers = ['creator', 'id', 'title', 'webpage_url', 'duration_seconds', 'score', 'priority', 'themes', 'screening_evidence'];
const rows = inventory.map((item) => [
  item.creator,
  item.id,
  item.title,
  item.webpage_url,
  item.duration,
  item.score,
  item.priority,
  item.themes,
  'Title metadata only; transcript verification pending',
]);
fs.writeFileSync(path.join(ROOT, 'inventory-screening.csv'), [headers, ...rows].map((row) => row.map(csv).join(',')).join('\n') + '\n');

for (const priority of ['P1 transcript', 'P2 transcript', 'P3 review', 'P4 low signal']) {
  const target = inventory.filter((item) => item.priority === priority);
  const slug = priority.toLowerCase().replaceAll(' ', '-');
  fs.writeFileSync(path.join(ROOT, `${slug}.ndjson`), target.map((item) => JSON.stringify(item)).join('\n') + (target.length ? '\n' : ''));
}

const totalKnownSeconds = rollups.reduce((sum, item) => sum + item.knownDurationSeconds, 0);
const totalMissingDuration = rollups.reduce((sum, item) => sum + item.missingDuration, 0);
const priorityCounts = Object.fromEntries(['P1 transcript', 'P2 transcript', 'P3 review', 'P4 low signal'].map((priority) => [priority, inventory.filter((item) => item.priority === priority).length]));

const report = [
  '# Seven-creator YouTube audit — inventory screening',
  '',
  'This is a complete title-level screening of every public upload found on the standard Videos and Shorts tabs. It is not transcript-level completion. Screening labels are routing decisions, not claims about unseen content.',
  '',
  '## Scope',
  '',
  `- ${inventory.length.toLocaleString('en-US')} distinct uploads inventoried.`,
  `- At least ${formatHours(totalKnownSeconds)} hours of known-duration material, plus ${totalMissingDuration.toLocaleString('en-US')} Shorts whose flat-playlist records omit duration.`,
  `- P1 transcript: ${priorityCounts['P1 transcript'].toLocaleString('en-US')}`,
  `- P2 transcript: ${priorityCounts['P2 transcript'].toLocaleString('en-US')}`,
  `- P3 review: ${priorityCounts['P3 review'].toLocaleString('en-US')}`,
  `- P4 low signal: ${priorityCounts['P4 low signal'].toLocaleString('en-US')}`,
  '',
  '## Creator scale',
  '',
  '| Creator | Uploads | Known-duration hours | Shorts/records missing duration |',
  '|---|---:|---:|---:|',
  ...rollups.map((item) => `| ${item.creator} | ${item.count.toLocaleString('en-US')} | ${formatHours(item.knownDurationSeconds)} | ${item.missingDuration.toLocaleString('en-US')} |`),
  '',
  '## Highest-priority candidates by creator',
  '',
];

for (const [creator] of creators) {
  report.push(`### ${creator}`, '');
  const candidates = inventory.filter((item) => item.creator === creator).sort((a, b) => b.score - a.score || a.title.localeCompare(b.title)).slice(0, 20);
  for (const item of candidates) report.push(`- [${item.title}](${item.webpage_url}) — ${item.priority}; ${item.themes.join(', ') || 'no title match'}`);
  report.push('');
}

report.push(
  '## Evidence limitation',
  '',
  'YouTube allowed complete channel inventory retrieval but blocked direct caption downloads from the VPS. Transcript extraction is available through the authenticated browser UI and is being used for the P1/P2 queues. No title-only inference is accepted as a verified lesson.',
  '',
);
fs.writeFileSync(path.join(ROOT, 'INVENTORY-SCREENING.md'), report.join('\n'));

process.stdout.write(JSON.stringify({
  total: inventory.length,
  knownHours: Number(formatHours(totalKnownSeconds)),
  missingDuration: totalMissingDuration,
  priorityCounts,
  outputs: {
    csv: path.join(ROOT, 'inventory-screening.csv'),
    report: path.join(ROOT, 'INVENTORY-SCREENING.md'),
  },
}, null, 2) + '\n');
