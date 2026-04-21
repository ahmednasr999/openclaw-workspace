import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { renderSlide, type SlidePayload } from './renderSlide.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, '../..');
const buildsDir = path.join(root, 'builds', 'latest');
const themeCssPath = path.join(root, 'themes', 'executive', 'theme.css');
const outlinePath = path.join(root, 'planning', 'latest', 'slide_outline.json');
const outputPath = path.join(buildsDir, 'index.html');

type PlannedSlide = {
  pattern: string;
  payload: Record<string, unknown>;
};

const fallbackDeck: SlidePayload[] = [
  {
    pattern: 'cover',
    eyebrow: 'Executive strategy system',
    title: 'Premium HTML slides from any content',
    subtitle: 'A deterministic planning and rendering pipeline for executive presentations.',
    heroText: 'Planning chooses the story. Templates choose the layout. Tokens choose the style. QA decides whether it ships.',
    visual: { src: 'https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=1200&q=80', alt: 'Executive workshop' },
    notes: 'Cover slide example'
  },
  {
    pattern: 'agenda',
    eyebrow: 'Outline',
    title: 'System flow',
    subtitle: 'The minimum viable premium slide engine',
    items: ['Ingest content', 'Plan narrative and slide outline', 'Assign patterns', 'Render templates', 'Run QA and export'],
    notes: 'Agenda example'
  },
  {
    pattern: 'thesis',
    eyebrow: 'Core thesis',
    title: 'Polish comes from systems, not prompts',
    thesis: 'The fastest way to improve slide quality is to stop generating raw layouts and start rendering structured slide patterns.',
    supportingPoints: ['Use a planner to define one message per slide', 'Use templates to remove layout randomness', 'Use theme tokens to keep style consistent', 'Use QA to catch density and hierarchy problems'],
    notes: 'Thesis example'
  },
  {
    pattern: 'comparison',
    eyebrow: 'Trade-off',
    title: 'Prompt-only generation vs structured rendering',
    leftTitle: 'Prompt-only slides',
    leftBody: 'Fast to try, hard to control, inconsistent layouts, too much text, and weak repeatability.',
    rightTitle: 'Structured rendering',
    rightBody: 'Slightly more setup, much stronger consistency, better QA, reusable patterns, and reliable executive-grade output.',
    preferredSide: 'right',
    notes: 'Comparison example'
  },
  {
    pattern: 'kpi-hero',
    eyebrow: 'KPI example',
    title: 'Template systems reduce cleanup effort',
    metric: '70%',
    metricLabel: 'Less manual deck cleanup',
    supportingText: 'Once layouts are deterministic, the AI focuses on story quality instead of fighting spacing and formatting every time.',
    footnote: 'Illustrative metric'
  },
  {
    pattern: 'timeline',
    eyebrow: 'Implementation',
    title: 'Recommended build sequence',
    phases: [
      { label: 'Phase 1', title: 'Schemas', detail: 'Define planner and render payload contracts.' },
      { label: 'Phase 2', title: 'Templates', detail: 'Build 8 premium slide patterns.' },
      { label: 'Phase 3', title: 'Renderer', detail: 'Render HTML from deterministic payloads.' },
      { label: 'Phase 4', title: 'QA', detail: 'Add screenshot and structural checks before shipping.' }
    ],
    currentLabel: 'Phase 2',
    notes: 'Timeline example'
  },
  {
    pattern: 'table',
    eyebrow: 'Pattern contract',
    title: 'Example table slide',
    columns: ['Capability', 'Prompt-only', 'Structured system'],
    rows: [
      ['Layout consistency', 'Low', 'High'],
      ['Reusability', 'Low', 'High'],
      ['QA readiness', 'Weak', 'Strong'],
      ['Executive polish', 'Unreliable', 'Reliable']
    ],
    highlightColumn: 2,
    footnote: 'Table example'
  },
  {
    pattern: 'closing',
    eyebrow: 'Closing',
    title: 'Build the system once, reuse it everywhere',
    closingStatement: 'Executive slide quality becomes repeatable when planning, patterning, theming, and QA are separated cleanly.',
    supportingText: 'This starter kit gives you the first working layer: a theme, templates, a renderer, and a sample deck you can extend.',
    cta: 'Next: add planner + export + QA'
  }
];

function loadDeck(): SlidePayload[] {
  if (!fs.existsSync(outlinePath)) return fallbackDeck;
  const raw = fs.readFileSync(outlinePath, 'utf8');
  const parsed = JSON.parse(raw) as { slides?: PlannedSlide[] };
  if (!parsed.slides?.length) return fallbackDeck;
  return parsed.slides.map((slide) => ({ pattern: slide.pattern, ...(slide.payload ?? {}) })) as SlidePayload[];
}

function buildHtml(slides: string[], themeCss: string): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>HTML Slides System</title>
  <style>${themeCss}</style>
</head>
<body>
  <main class="deck">
    ${slides.join('\n')}
  </main>
</body>
</html>`;
}

function main() {
  fs.mkdirSync(buildsDir, { recursive: true });
  const themeCss = fs.readFileSync(themeCssPath, 'utf8');
  const deck = loadDeck();
  const slides = deck.map(renderSlide);
  const html = buildHtml(slides, themeCss);
  fs.writeFileSync(outputPath, html, 'utf8');
  console.log(`Rendered deck to ${outputPath}`);
}

main();
