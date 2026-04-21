const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');
const layoutHelpers = require('../../assets/pptxgenjs_helpers/layout');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'OpenClaw';
pptx.company = 'OpenClaw';
pptx.subject = 'Little Might branded showcase';
pptx.title = 'Little Might Branded Showcase';
pptx.lang = 'en-US';
pptx.theme = {
  headFontFace: 'Instrument Serif',
  bodyFontFace: 'Inter',
  lang: 'en-US',
};

const OUT = path.join(__dirname, 'exports', 'littlemight-branded-showcase.pptx');
const TOKENS = {
  bgWarm: 'F5F4ED',
  bgWhite: 'FFFDFC',
  surface: 'FFFDFC',
  surfaceAlt: 'FAF9F5',
  textPrimary: '0B0D0B',
  textSecondary: '65655C',
  textSoft: '8D8D85',
  rule: 'C2C1BB',
  accent: 'F7591F',
  accentSoft: 'F5D2C0',
  blue: '845E8F',
  green: '4B7A5A',
};

function addPageBadge(slide, n) {
  slide.addText(String(n), {
    x: 12.45, y: 6.82, w: 0.45, h: 0.24,
    fontFace: 'Inter', fontSize: 10, bold: true,
    color: '666666', align: 'center', margin: 0,
  });
}

function addEyebrow(slide, text, x, y, w) {
  slide.addText(text, {
    x, y, w, h: 0.22,
    fontFace: 'Inter', fontSize: 9, bold: true,
    color: TOKENS.textSoft, charSpace: 1.2, margin: 0,
  });
}

function addRiskNote(slide, text) {
  slide.addText(text, {
    x: 0.7, y: 6.25, w: 10.8, h: 0.25,
    fontFace: 'Inter', fontSize: 8.5, color: TOKENS.textSoft, margin: 0,
  });
}

function addVisualPlaceholder(slide, label, x, y, w, h, fill = TOKENS.surface) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.08,
    line: { color: TOKENS.rule, pt: 1 },
    fill: { color: fill },
  });
  slide.addText(label, {
    x: x + 0.24, y: y + 0.32, w: w - 0.48, h: h - 0.64,
    fontFace: 'Inter', fontSize: 14, color: TOKENS.textSoft,
    align: 'center', valign: 'mid', margin: 0.08,
  });
}

function finalize(slide, number, cover = false) {
  if (typeof layoutHelpers.warnIfSlideHasOverlaps === 'function') layoutHelpers.warnIfSlideHasOverlaps(slide, pptx);
  if (typeof layoutHelpers.warnIfSlideElementsOutOfBounds === 'function') layoutHelpers.warnIfSlideElementsOutOfBounds(slide, pptx);
  if (!cover) addPageBadge(slide, number);
}

function coverSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWarm };
  addEyebrow(slide, 'little might showcase · cover', 0.7, 0.55, 3.2);
  slide.addText('Little Might Branded Showcase', {
    x: 0.7, y: 1.1, w: 6.1, h: 1.4,
    fontFace: 'Instrument Serif', fontSize: 31, bold: true,
    color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('A concrete starter deck for the redesigned slides skill, showing how planning patterns map into editable PPTX composition.', {
    x: 0.7, y: 2.7, w: 5.9, h: 1.2,
    fontFace: 'Inter', fontSize: 16, color: TOKENS.textSecondary,
    margin: 0,
  });
  slide.addText('Goal: make the default output feel designed before a human touches it.', {
    x: 0.72, y: 4.2, w: 5.5, h: 0.45,
    fontFace: 'Inter', fontSize: 11, color: TOKENS.textSoft, margin: 0,
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 7.6, y: 1.0, w: 4.7, h: 4.7,
    rectRadius: 0.09,
    line: { color: TOKENS.accent, pt: 1.1 },
    fill: { color: TOKENS.accentSoft },
  });
  slide.addText('Little Might favors\nwarm restraint over loud polish.', {
    x: 7.92, y: 1.75, w: 3.75, h: 1.0,
    fontFace: 'Instrument Serif', fontSize: 20, bold: true,
    color: TOKENS.textPrimary, align: 'center', margin: 0,
  });
  slide.addText('Paper-toned backgrounds, serif-led hierarchy, and selective orange emphasis.', {
    x: 7.92, y: 3.0, w: 3.75, h: 1.1,
    fontFace: 'Inter', fontSize: 12, color: TOKENS.textSecondary,
    align: 'center', valign: 'mid', margin: 0.08,
  });
  slide.addText('editorial reference field', {
    x: 9.0, y: 5.0, w: 1.7, h: 0.2,
    fontFace: 'Inter', fontSize: 8.5, bold: true, color: TOKENS.textSoft,
    align: 'center', margin: 0,
  });
  finalize(slide, 1, true);
}

function sectionDividerSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWarm };
  addEyebrow(slide, 'little might showcase · section-divider', 0.8, 0.75, 3.6);
  slide.addText('02', {
    x: 0.78, y: 1.35, w: 1.6, h: 1.15,
    fontFace: 'Instrument Serif', fontSize: 34, bold: true,
    color: TOKENS.accent, margin: 0,
  });
  slide.addText('Pattern logic', {
    x: 0.78, y: 2.9, w: 6.0, h: 0.8,
    fontFace: 'Instrument Serif', fontSize: 26, bold: true,
    color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('A section divider should feel like a chapter page, not a normal content slide with a bigger title.', {
    x: 0.82, y: 4.0, w: 4.9, h: 0.8,
    fontFace: 'Inter', fontSize: 13, color: TOKENS.textSecondary, margin: 0,
  });
  slide.addShape(pptx.ShapeType.line, {
    x: 7.2, y: 1.4, w: 4.1, h: 0,
    line: { color: TOKENS.rule, pt: 1.1 },
  });
  slide.addText('Reset the eye.\nChange the rhythm.\nSignal a new block.', {
    x: 7.25, y: 2.0, w: 3.9, h: 1.6,
    fontFace: 'Instrument Serif', fontSize: 19, bold: true,
    color: TOKENS.textPrimary, margin: 0,
  });
  addRiskNote(slide, 'Risk note: if the divider looks like a normal slide, it is not creating rhythm or reset.');
  finalize(slide, 2);
}

function agendaSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  addEyebrow(slide, 'little might showcase · agenda', 0.7, 0.45, 3.2);
  slide.addText('Agenda', {
    x: 0.7, y: 0.9, w: 3.8, h: 0.45,
    fontFace: 'Instrument Serif', fontSize: 24, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('Six examples showing how pattern-aware planning should shape the default deck stub.', {
    x: 0.7, y: 1.5, w: 5.7, h: 0.45,
    fontFace: 'Inter', fontSize: 11, color: TOKENS.textSecondary, margin: 0,
  });
  const items = ['Cover', 'Agenda', 'Metric', 'Comparison', 'Process timeline', 'Closing'];
  let y = 2.2;
  items.forEach((item, idx) => {
    slide.addText(String(idx + 1).padStart(2, '0'), {
      x: 0.9, y, w: 0.55, h: 0.25,
      fontFace: 'Inter', fontSize: 14, bold: true, color: TOKENS.accent, margin: 0,
    });
    slide.addText(item, {
      x: 1.55, y: y - 0.02, w: 4.6, h: 0.3,
      fontFace: 'Inter', fontSize: 15, color: TOKENS.textPrimary, margin: 0,
    });
    y += 0.66;
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 7.2, y: 1.45, w: 5.05, h: 4.05,
    rectRadius: 0.08,
    line: { color: TOKENS.rule, pt: 1 },
    fill: { color: TOKENS.surfaceAlt },
  });
  slide.addText('Navigation should feel like\na calm editorial index.', {
    x: 7.55, y: 2.0, w: 4.25, h: 0.9,
    fontFace: 'Instrument Serif', fontSize: 19, bold: true,
    color: TOKENS.textPrimary, align: 'center', margin: 0,
  });
  slide.addText('Keep the scan path obvious, keep the accent restrained, and avoid turning agenda slides into dashboards.', {
    x: 7.55, y: 3.15, w: 4.2, h: 1.15,
    fontFace: 'Inter', fontSize: 11.5, color: TOKENS.textSecondary,
    align: 'center', valign: 'mid', margin: 0.08,
  });
  addRiskNote(slide, 'Risk note: agenda should stay crisp, not turn into a dashboard of equal-weight cards.');
  finalize(slide, 2);
}

function thesisSummarySlide() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  addEyebrow(slide, 'little might showcase · thesis-summary', 0.7, 0.45, 3.9);
  slide.addText('Thesis summary', {
    x: 0.7, y: 0.9, w: 4.6, h: 0.45,
    fontFace: 'Instrument Serif', fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('The redesign should move slide quality from prompt luck to a constrained editorial system.', {
    x: 0.7, y: 1.55, w: 5.5, h: 1.15,
    fontFace: 'Inter', fontSize: 18, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addShape(pptx.ShapeType.roundRect, { x: 7.0, y: 1.35, w: 5.2, h: 3.9, rectRadius: 0.08, line: { color: TOKENS.rule, pt: 1 }, fill: { color: TOKENS.surfaceAlt } });
  slide.addText('Why it works', {
    x: 7.28, y: 1.72, w: 1.9, h: 0.22,
    fontFace: 'Inter', fontSize: 9.5, bold: true, color: TOKENS.textSoft, margin: 0,
  });
  const supports = [
    'Patterns tell the model what this slide is doing.',
    'Tokens keep style coherent across layouts.',
    'Anti-patterns prevent generic template drift.',
  ];
  let y = 2.15;
  supports.forEach((text, idx) => {
    slide.addText(String(idx + 1).padStart(2, '0'), {
      x: 7.28, y: y + 0.02, w: 0.42, h: 0.18,
      fontFace: 'Inter', fontSize: 9.5, bold: true, color: TOKENS.accent, margin: 0,
    });
    slide.addText(text, {
      x: 7.78, y, w: 3.85, h: 0.48,
      fontFace: 'Inter', fontSize: 12, color: TOKENS.textSecondary, margin: 0,
    });
    y += 0.88;
  });
  addRiskNote(slide, 'Risk note: summary slides fail when every supporting point is given the same weight as the thesis.');
  finalize(slide, 4);
}

function metricSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  addEyebrow(slide, 'little might showcase · metric', 0.7, 0.45, 3.2);
  slide.addText('Key KPI', {
    x: 0.7, y: 0.9, w: 4.0, h: 0.45,
    fontFace: 'Instrument Serif', fontSize: 22, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('72% automation coverage', {
    x: 0.7, y: 1.8, w: 5.8, h: 1.2,
    fontFace: 'Instrument Serif', fontSize: 30, bold: true, color: TOKENS.accent, margin: 0,
  });
  slide.addText('Up from 31% baseline in nine months, enough to justify scaling the operating model into two additional functions.', {
    x: 0.72, y: 3.3, w: 5.7, h: 0.9,
    fontFace: 'Inter', fontSize: 14, color: TOKENS.textSecondary, margin: 0,
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 7.05, y: 1.35, w: 5.2, h: 3.95,
    rectRadius: 0.08,
    line: { color: TOKENS.rule, pt: 1 },
    fill: { color: TOKENS.surfaceAlt },
  });
  slide.addText('supporting proof', {
    x: 7.35, y: 1.72, w: 1.8, h: 0.2,
    fontFace: 'Inter', fontSize: 9.5, bold: true, color: TOKENS.textSoft, margin: 0,
  });
  slide.addText('18% YoY growth', {
    x: 7.35, y: 2.25, w: 2.6, h: 0.4,
    fontFace: 'Instrument Serif', fontSize: 20, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('paired with a 4-point margin lift and a cleaner operating model argument.', {
    x: 7.35, y: 2.95, w: 4.2, h: 0.95,
    fontFace: 'Inter', fontSize: 12, color: TOKENS.textSecondary, margin: 0,
  });
  slide.addShape(pptx.ShapeType.line, { x: 7.35, y: 4.22, w: 3.8, h: 0, line: { color: TOKENS.rule, pt: 1 } });
  slide.addText('chart is optional when the number is already the story', {
    x: 7.35, y: 4.42, w: 3.9, h: 0.28,
    fontFace: 'Inter', fontSize: 9.5, color: TOKENS.textSoft, margin: 0,
  });
  addRiskNote(slide, 'Risk note: do not bury the number inside four KPI cards or a default analytics layout.');
  finalize(slide, 3);
}

function comparisonSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  addEyebrow(slide, 'little might showcase · comparison', 0.7, 0.45, 3.5);
  slide.addText('Decision framing', {
    x: 0.7, y: 0.9, w: 5.2, h: 0.45,
    fontFace: 'Instrument Serif', fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('Recommended lane should dominate when symmetry is not truthful.', {
    x: 0.7, y: 1.52, w: 4.9, h: 0.44,
    fontFace: 'Inter', fontSize: 11.5, color: TOKENS.textSecondary, margin: 0,
  });
  slide.addShape(pptx.ShapeType.roundRect, { x: 0.7, y: 2.2, w: 3.9, h: 2.7, rectRadius: 0.06, line: { color: TOKENS.rule, pt: 1 }, fill: { color: TOKENS.surface } });
  slide.addShape(pptx.ShapeType.roundRect, { x: 4.95, y: 2.2, w: 4.6, h: 2.8, rectRadius: 0.06, line: { color: TOKENS.accent, pt: 1.2 }, fill: { color: TOKENS.accentSoft } });
  slide.addText('Status quo', { x: 1.0, y: 2.52, w: 2.3, h: 0.3, fontFace: 'Inter', fontSize: 17, bold: true, color: TOKENS.textPrimary, margin: 0 });
  slide.addText('Recommended lane', { x: 5.25, y: 2.55, w: 3.1, h: 0.3, fontFace: 'Inter', fontSize: 18, bold: true, color: TOKENS.textPrimary, margin: 0 });
  slide.addText('Preferred option gets more area, stronger stroke, and cleaner evidence hierarchy.', { x: 5.22, y: 3.15, w: 3.8, h: 1.0, fontFace: 'Inter', fontSize: 13, color: TOKENS.textSecondary, margin: 0 });
  slide.addText('preferred because\nit reduces ambiguity\nand scales more cleanly.', {
    x: 9.9, y: 2.35, w: 2.2, h: 1.1,
    fontFace: 'Inter', fontSize: 10.5, color: TOKENS.textSecondary,
    align: 'center', valign: 'mid', margin: 0.08,
  });
  slide.addShape(pptx.ShapeType.line, { x: 10.15, y: 3.85, w: 1.7, h: 0, line: { color: TOKENS.rule, pt: 1 } });
  slide.addText('decision note', {
    x: 10.15, y: 4.05, w: 1.7, h: 0.18,
    fontFace: 'Inter', fontSize: 8.5, bold: true, color: TOKENS.textSoft,
    align: 'center', margin: 0,
  });
  addRiskNote(slide, 'Risk note: if one option is clearly preferred, equal-weight columns become fake neutrality.');
  finalize(slide, 4);
}

function twoColumnExplainerSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  addEyebrow(slide, 'little might showcase · 2-column-explainer', 0.7, 0.45, 4.3);
  slide.addText('Two-column explainer', {
    x: 0.7, y: 0.9, w: 5.0, h: 0.45,
    fontFace: 'Instrument Serif', fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('One side should explain. The other side should support. If both sides shout equally, this should probably be a comparison slide instead.', {
    x: 0.7, y: 1.55, w: 5.15, h: 1.25,
    fontFace: 'Inter', fontSize: 16, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('Use asymmetry so the explanatory block dominates and the support panel behaves like evidence, not a twin.', {
    x: 0.72, y: 3.05, w: 4.95, h: 0.75,
    fontFace: 'Inter', fontSize: 11.5, color: TOKENS.textSecondary, margin: 0,
  });
  slide.addShape(pptx.ShapeType.roundRect, { x: 6.95, y: 1.4, w: 5.15, h: 4.0, rectRadius: 0.08, line: { color: TOKENS.rule, pt: 1 }, fill: { color: TOKENS.surfaceAlt } });
  slide.addText('support block', {
    x: 7.25, y: 1.85, w: 3.8, h: 0.3,
    fontFace: 'Inter', fontSize: 9.5, bold: true, color: TOKENS.textSoft, margin: 0,
  });
  slide.addText('The support side should clarify the thesis, not compete with it.', {
    x: 7.25, y: 2.35, w: 4.05, h: 0.7,
    fontFace: 'Instrument Serif', fontSize: 18, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('Use this area for one quote, one mini diagram, or one implementation note, not a second equally loud argument.', {
    x: 7.25, y: 3.25, w: 4.15, h: 1.0,
    fontFace: 'Inter', fontSize: 11.5, color: TOKENS.textSecondary, margin: 0,
  });
  addRiskNote(slide, 'Risk note: if both columns look equally heavy, the hierarchy is wrong for this pattern.');
  finalize(slide, 7);
}

function timelineSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  addEyebrow(slide, 'little might showcase · process-timeline', 0.7, 0.45, 4.0);
  slide.addText('Phased rollout', {
    x: 0.7, y: 0.9, w: 5.0, h: 0.45,
    fontFace: 'Instrument Serif', fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('The process spine should be obvious on first glance, with one phase carrying the main emphasis.', {
    x: 0.7, y: 1.52, w: 6.2, h: 0.55,
    fontFace: 'Inter', fontSize: 12, color: TOKENS.textSecondary, margin: 0,
  });
  const xs = [1.0, 3.35, 5.7, 8.05];
  slide.addShape(pptx.ShapeType.line, { x: 1.2, y: 3.55, w: 7.7, h: 0, line: { color: TOKENS.rule, pt: 1.2 } });
  xs.forEach((x, idx) => {
    slide.addShape(pptx.ShapeType.ellipse, { x, y: 3.28, w: 0.32, h: 0.32, line: { color: idx === 1 ? TOKENS.accent : TOKENS.rule, pt: 1 }, fill: { color: idx === 1 ? TOKENS.accent : TOKENS.surface } });
    slide.addText(`Phase ${idx + 1}`, { x: x - 0.08, y: 2.66, w: 1.0, h: 0.22, fontFace: 'Inter', fontSize: 11, bold: true, color: idx === 1 ? TOKENS.accent : TOKENS.textPrimary, margin: 0 });
  });
  slide.addText('Current priority phase', { x: 3.0, y: 4.0, w: 2.3, h: 0.5, fontFace: 'Inter', fontSize: 12, color: TOKENS.textSecondary, margin: 0, align: 'center' });
  slide.addShape(pptx.ShapeType.roundRect, { x: 9.55, y: 2.05, w: 2.75, h: 2.95, rectRadius: 0.08, line: { color: TOKENS.rule, pt: 1 }, fill: { color: TOKENS.surfaceAlt } });
  slide.addText('milestone note', {
    x: 9.85, y: 2.35, w: 2.1, h: 0.22,
    fontFace: 'Inter', fontSize: 8.8, bold: true, color: TOKENS.textSoft, align: 'center', margin: 0,
  });
  slide.addText('Keep the side note short so the process spine remains the focal structure.', {
    x: 9.82, y: 2.95, w: 2.0, h: 1.0,
    fontFace: 'Inter', fontSize: 10.3, color: TOKENS.textSecondary, align: 'center', valign: 'mid', margin: 0.08,
  });
  addRiskNote(slide, 'Risk note: too many milestones in one row will collapse the sequence into noise.');
  finalize(slide, 5);
}

function closingSlide() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWarm };
  addEyebrow(slide, 'little might showcase · closing', 0.7, 0.55, 3.1);
  slide.addText('Make the default output feel designed before a human touches it.', {
    x: 0.9, y: 1.6, w: 10.4, h: 1.55,
    fontFace: 'Instrument Serif', fontSize: 28, bold: true,
    color: TOKENS.textPrimary, margin: 0, align: 'center',
  });
  slide.addText('The redesign matters when planning intent, pattern logic, and editable output all line up in the first generated draft.', {
    x: 2.0, y: 3.45, w: 8.2, h: 0.95,
    fontFace: 'Inter', fontSize: 14, color: TOKENS.textSecondary,
    margin: 0, align: 'center',
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 4.35, y: 4.82, w: 4.3, h: 0.68,
    rectRadius: 0.08,
    line: { color: TOKENS.accent, pt: 1.2 },
    fill: { color: TOKENS.accentSoft },
  });
  slide.addText('next move: build more examples', {
    x: 4.55, y: 5.03, w: 3.9, h: 0.22,
    fontFace: 'Inter', fontSize: 11, bold: true, color: TOKENS.accent,
    align: 'center', margin: 0,
  });
  slide.addText('A stronger default draft makes the human polish pass strategic instead of corrective.', {
    x: 2.55, y: 5.75, w: 7.1, h: 0.35,
    fontFace: 'Inter', fontSize: 10.2, color: TOKENS.textSoft, align: 'center', margin: 0,
  });
  addRiskNote(slide, 'Risk note: do not let the final slide turn into a weak administrative summary.');
  finalize(slide, 6);
}

coverSlide();
sectionDividerSlide();
agendaSlide();
thesisSummarySlide();
metricSlide();
comparisonSlide();
twoColumnExplainerSlide();
timelineSlide();
closingSlide();

fs.mkdirSync(path.dirname(OUT), { recursive: true });
pptx.writeFile({ fileName: OUT });
