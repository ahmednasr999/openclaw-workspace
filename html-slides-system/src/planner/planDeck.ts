import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import type { DeckBrief, PlannedSlide, PlannerInput, SlideOutline, SourceSection } from './plannerTypes.js';
import { sampleInput } from './sampleInput.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, '../..');
const planningDir = path.join(root, 'planning', 'latest');

function priorityScore(priority?: SourceSection['priority']): number {
  if (priority === 'high') return 3;
  if (priority === 'medium') return 2;
  return 1;
}

function topSections(input: PlannerInput): SourceSection[] {
  const reservedSlides = 3;
  const availableContentSlots = Math.max(1, input.desiredSlideCount - reservedSlides);
  return [...input.sections]
    .sort((a, b) => priorityScore(b.priority) - priorityScore(a.priority))
    .slice(0, Math.min(availableContentSlots, input.sections.length));
}

function buildBrief(input: PlannerInput, selected: SourceSection[]): DeckBrief {
  return {
    deckTitle: input.deckTitle,
    objective: input.objective,
    audience: input.audience,
    tone: input.tone,
    desiredSlideCount: input.desiredSlideCount,
    narrativeArc: ['Context', 'Why now', 'Thesis', 'Capabilities', 'Implementation', 'Risks', 'Decision'],
    strongestSections: selected.map((section) => section.title),
    gaps: ['Quantified impact data not yet provided', 'No external benchmark data yet attached'],
    assumptions: ['Audience is already familiar with transformation pain', 'Deck should stay concise and executive-level']
  };
}

function buildSlide(section: SourceSection, index: number): PlannedSlide {
  const patternMap = ['thesis', 'comparison', 'kpi-hero', 'table', 'timeline'];
  const pattern = patternMap[index % patternMap.length];
  const payloadByPattern: Record<string, Record<string, unknown>> = {
    thesis: {
      eyebrow: section.title,
      title: section.title,
      thesis: section.summary,
      supportingPoints: section.bullets ?? []
    },
    comparison: {
      eyebrow: section.title,
      title: section.title,
      leftTitle: 'Current state',
      leftBody: (section.bullets ?? [section.summary]).slice(0, 2).join(', '),
      rightTitle: 'Target state',
      rightBody: section.summary,
      preferredSide: 'right'
    },
    'kpi-hero': {
      eyebrow: section.title,
      title: section.title,
      metric: priorityScore(section.priority) === 3 ? 'High' : 'Medium',
      metricLabel: 'Strategic priority',
      supportingText: section.summary,
      footnote: (section.bullets ?? []).join(' • ')
    },
    table: {
      eyebrow: section.title,
      title: section.title,
      columns: ['Dimension', 'Detail'],
      rows: (section.bullets ?? [section.summary]).map((bullet, bulletIndex) => [`Point ${bulletIndex + 1}`, bullet]),
      highlightColumn: 1,
      footnote: section.summary
    },
    timeline: {
      eyebrow: section.title,
      title: section.title,
      phases: (section.bullets ?? [section.summary]).map((bullet, bulletIndex) => ({
        label: `Step ${bulletIndex + 1}`,
        title: bullet,
        detail: section.summary
      })),
      currentLabel: 'Step 1'
    }
  };

  return {
    id: `slide-${index + 1}`,
    pattern,
    title: section.title,
    purpose: `Explain ${section.title.toLowerCase()}`,
    keyMessage: section.summary,
    sourceSectionIds: [section.id],
    layoutDirection: pattern === 'comparison' ? 'Two-column contrast' : pattern === 'timeline' ? 'Phased sequence' : 'Single-focus editorial',
    visualSuggestion: pattern === 'kpi-hero' ? 'Large metric card' : pattern === 'table' ? 'Simple comparison table' : 'Minimal executive graphic support',
    confidence: priorityScore(section.priority) === 3 ? 0.9 : 0.75,
    payload: payloadByPattern[pattern]
  };
}

function buildOutline(input: PlannerInput, selected: SourceSection[]): SlideOutline {
  const contentSlides = selected.map(buildSlide);

  const cover: PlannedSlide = {
    id: 'slide-cover',
    pattern: 'cover',
    title: input.deckTitle,
    purpose: 'Open the deck',
    keyMessage: input.objective,
    sourceSectionIds: selected.slice(0, 2).map((section) => section.id),
    layoutDirection: 'Hero cover',
    visualSuggestion: 'Executive editorial cover visual',
    confidence: 0.95,
    payload: {
      eyebrow: input.audience,
      title: input.deckTitle,
      subtitle: input.objective,
      heroText: `${input.tone}. ${input.audience}.`
    }
  };

  const agenda: PlannedSlide = {
    id: 'slide-agenda',
    pattern: 'agenda',
    title: 'Agenda',
    purpose: 'Show the narrative arc',
    keyMessage: 'This is the executive story flow.',
    sourceSectionIds: selected.map((section) => section.id),
    layoutDirection: 'Single card list',
    visualSuggestion: 'Ordered list of section titles',
    confidence: 0.95,
    payload: {
      eyebrow: 'Outline',
      title: 'Agenda',
      subtitle: 'The executive story in sequence',
      items: selected.map((section) => section.title)
    }
  };

  const closing: PlannedSlide = {
    id: 'slide-closing',
    pattern: 'closing',
    title: 'Decision',
    purpose: 'Close with the executive ask',
    keyMessage: 'Commit to a scoped pilot and measure execution confidence gains.',
    sourceSectionIds: selected.slice(-2).map((section) => section.id),
    layoutDirection: 'Centered close',
    visualSuggestion: 'High-contrast close with CTA',
    confidence: 0.9,
    payload: {
      eyebrow: 'Decision',
      title: 'Move from AI theater to execution value',
      closingStatement: 'Start with one operating workflow, prove value fast, then scale only what improves decision velocity.',
      supportingText: 'The win is not more content. It is tighter execution, cleaner signals, and faster leadership action.',
      cta: 'Approve a 30-day pilot'
    }
  };

  return {
    deckTitle: input.deckTitle,
    generatedAt: new Date().toISOString(),
    slides: [cover, agenda, ...contentSlides, closing].slice(0, input.desiredSlideCount)
  };
}

function writeMarkdownBrief(brief: DeckBrief): string {
  return `# Deck Brief\n\n- **Title:** ${brief.deckTitle}\n- **Objective:** ${brief.objective}\n- **Audience:** ${brief.audience}\n- **Tone:** ${brief.tone}\n- **Desired slide count:** ${brief.desiredSlideCount}\n\n## Narrative arc\n${brief.narrativeArc.map((item) => `- ${item}`).join('\n')}\n\n## Strongest sections\n${brief.strongestSections.map((item) => `- ${item}`).join('\n')}\n\n## Gaps\n${brief.gaps.map((item) => `- ${item}`).join('\n')}\n\n## Assumptions\n${brief.assumptions.map((item) => `- ${item}`).join('\n')}\n`;
}

function writeContentMap(outline: SlideOutline): string {
  const lines = outline.slides.map((slide) => `- **${slide.id}** ${slide.title} -> ${slide.sourceSectionIds.join(', ')}`);
  return `# Content Map\n\n${lines.join('\n')}\n`;
}

function main() {
  fs.mkdirSync(planningDir, { recursive: true });
  const selected = topSections(sampleInput);
  const brief = buildBrief(sampleInput, selected);
  const outline = buildOutline(sampleInput, selected);

  fs.writeFileSync(path.join(planningDir, 'deck_brief.md'), writeMarkdownBrief(brief), 'utf8');
  fs.writeFileSync(path.join(planningDir, 'slide_outline.json'), JSON.stringify(outline, null, 2), 'utf8');
  fs.writeFileSync(path.join(planningDir, 'content_map.md'), writeContentMap(outline), 'utf8');

  console.log(`Planned deck artifacts in ${planningDir}`);
}

main();
