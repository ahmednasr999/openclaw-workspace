#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const root = path.resolve('output/creator-channel-audit-20260819');
const queueFiles = [
  'p1-transcript.ndjson',
  'p2-transcript.ndjson',
  'p3-review.ndjson',
  'p4-low-signal.ndjson',
];

function readNdjson(file) {
  return fs.readFileSync(file, 'utf8')
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

const inventory = queueFiles.flatMap((file) => readNdjson(path.join(root, file)));
const dispositions = readNdjson(path.join(root, 'review-dispositions.ndjson'));
const inventoryById = new Map();
const dispositionById = new Map();
const errors = [];

for (const item of inventory) {
  if (inventoryById.has(item.id)) errors.push(`Duplicate inventory ID: ${item.id}`);
  inventoryById.set(item.id, item);
}

for (const item of dispositions) {
  if (dispositionById.has(item.id)) errors.push(`Duplicate disposition ID: ${item.id}`);
  dispositionById.set(item.id, item);
  const source = inventoryById.get(item.id);
  if (!source) {
    errors.push(`Disposition missing from inventory: ${item.id}`);
    continue;
  }
  if (source.creator !== item.creator) errors.push(`Creator mismatch for ${item.id}`);
  if (source.priority !== item.priority) errors.push(`Priority mismatch for ${item.id}: ${item.priority} != ${source.priority}`);

  for (const field of ['transcript_path', 'analysis_path']) {
    const file = path.join(root, item[field]);
    if (!fs.existsSync(file)) errors.push(`Missing ${field} for ${item.id}: ${item[field]}`);
  }
  const transcriptFile = path.join(root, item.transcript_path);
  if (fs.existsSync(transcriptFile)) {
    const transcript = fs.readFileSync(transcriptFile, 'utf8');
    if (!transcript.includes(`Video ID: ${item.id}`)) errors.push(`Transcript ID mismatch for ${item.id}`);
  }
  const analysisFile = path.join(root, item.analysis_path);
  if (fs.existsSync(analysisFile)) {
    const analysis = fs.readFileSync(analysisFile, 'utf8');
    if (!analysis.includes(`watch?v=${item.id}`) && !analysis.includes(`shorts/${item.id}`)) {
      errors.push(`Analysis source mismatch for ${item.id}`);
    }
  }
}

const priorities = ['P1 transcript', 'P2 transcript', 'P3 review', 'P4 low signal'];
const reviewedByPriority = Object.fromEntries(priorities.map((priority) => [
  priority,
  dispositions.filter((item) => item.priority === priority).length,
]));

const summary = {
  ok: errors.length === 0,
  inventory: inventory.length,
  reviewed: dispositions.length,
  remaining: inventory.length - dispositions.length,
  reviewedByPriority,
  reviewedByCreator: Object.fromEntries([...new Set(dispositions.map((item) => item.creator))].sort().map((creator) => [
    creator,
    dispositions.filter((item) => item.creator === creator).length,
  ])),
  dispositions: Object.fromEntries([...new Set(dispositions.map((item) => item.disposition))].sort().map((status) => [
    status,
    dispositions.filter((item) => item.disposition === status).length,
  ])),
  errors,
};

process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
if (errors.length) process.exitCode = 1;
