const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');
const layoutHelpers = require('../../assets/pptxgenjs_helpers/layout');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'OpenClaw';
pptx.company = 'OpenClaw';
pptx.subject = 'Executive Summary Starter';
pptx.title = 'Executive Summary Starter';
pptx.lang = 'en-US';
pptx.theme = {
  headFontFace: 'Aptos Display',
  bodyFontFace: 'Aptos',
  lang: 'en-US',
};

const OUT = path.join(__dirname, 'exports', 'executive-summary-starter.pptx');
const TOKENS = {
  bgWarm: 'F5F1EA',
  bgWhite: 'FFFFFF',
  surface: 'FCFAF7',
  surfaceAlt: 'F3EEE8',
  textPrimary: '171411',
  textSecondary: '4B443D',
  textSoft: '7A6F66',
  rule: 'D8CEC2',
  ruleStrong: 'B9AB9B',
  accent: 'C86432',
  accentSoft: 'F3E1D8',
  green: '4B7A5A',
  blue: '2E6FD0',
};

function finalize(slide, number, cover = false) {
  if (typeof layoutHelpers.warnIfSlideHasOverlaps === 'function') layoutHelpers.warnIfSlideHasOverlaps(slide, pptx);
  if (typeof layoutHelpers.warnIfSlideElementsOutOfBounds === 'function') layoutHelpers.warnIfSlideElementsOutOfBounds(slide, pptx);
  if (!cover) {
    slide.addText(String(number), {
      x: 12.45, y: 6.82, w: 0.45, h: 0.24,
      fontFace: 'Aptos', fontSize: 10, bold: true,
      color: '666666', align: 'center', margin: 0,
    });
  }
}

function eyebrow(slide, text, x = 0.7, y = 0.45, w = 3.5) {
  slide.addText(text, {
    x, y, w, h: 0.22,
    fontFace: 'Aptos', fontSize: 9, bold: true,
    color: TOKENS.textSoft, charSpace: 1.2, margin: 0,
  });
}

function risk(slide, text) {
  slide.addText(text, {
    x: 0.7, y: 6.25, w: 10.8, h: 0.25,
    fontFace: 'Aptos', fontSize: 8.5, color: TOKENS.textSoft, margin: 0,
  });
}

function panel(slide, x, y, w, h, fill = TOKENS.surface, line = TOKENS.rule) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.08,
    line: { color: line, pt: 1 },
    fill: { color: fill },
  });
}

function cover() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWarm };
  eyebrow(slide, 'executive summary · transformation office');
  slide.addText('Transformation Office Executive Summary', {
    x: 0.7, y: 1.0, w: 6.6, h: 1.4,
    fontFace: 'Aptos Display', fontSize: 30, bold: true,
    color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('A focused operating model to reduce delivery friction, improve automation coverage, and speed executive decision making.', {
    x: 0.7, y: 2.55, w: 5.9, h: 1.0,
    fontFace: 'Aptos', fontSize: 15, color: TOKENS.textSecondary, margin: 0,
  });
  slide.addText('Decision needed: approve one pilot and assign one accountable owner.', {
    x: 0.72, y: 4.18, w: 5.6, h: 0.35,
    fontFace: 'Aptos', fontSize: 10.5, color: TOKENS.textSoft, margin: 0,
  });
  panel(slide, 7.2, 1.0, 5.0, 4.7, TOKENS.accentSoft, TOKENS.accent);
  slide.addText('hero field\ntransformation office', {
    x: 7.45, y: 2.2, w: 4.5, h: 1.1,
    fontFace: 'Aptos', fontSize: 15, color: TOKENS.textSoft,
    align: 'center', valign: 'mid', margin: 0.08,
  });
  finalize(slide, 1, true);
}

function agenda() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  eyebrow(slide, 'agenda');
  slide.addText('Agenda', {
    x: 0.7, y: 0.9, w: 4.0, h: 0.45,
    fontFace: 'Aptos Display', fontSize: 24, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('Six slides to move from problem statement to decision-ready next step.', {
    x: 0.7, y: 1.5, w: 5.6, h: 0.4,
    fontFace: 'Aptos', fontSize: 11, color: TOKENS.textSecondary, margin: 0,
  });
  const items = ['Problem', 'Recommendations', 'KPI target', 'Decision framing', 'Timeline', 'Next step'];
  let y = 2.2;
  items.forEach((item, idx) => {
    slide.addText(String(idx + 1).padStart(2, '0'), {
      x: 0.9, y, w: 0.55, h: 0.25,
      fontFace: 'Aptos', fontSize: 14, bold: true, color: TOKENS.accent, margin: 0,
    });
    slide.addText(item, {
      x: 1.55, y: y - 0.02, w: 4.8, h: 0.3,
      fontFace: 'Aptos', fontSize: 15, color: TOKENS.textPrimary, margin: 0,
    });
    y += 0.66;
  });
  panel(slide, 7.2, 1.45, 5.0, 4.0, TOKENS.surfaceAlt);
  slide.addText('structure should scan in\n2 to 3 seconds', {
    x: 7.5, y: 2.3, w: 4.3, h: 0.9,
    fontFace: 'Aptos Display', fontSize: 18, bold: true, color: TOKENS.textPrimary,
    align: 'center', margin: 0,
  });
  risk(slide, 'Risk note: agenda should stay crisp, not become a dashboard of equal-weight boxes.');
  finalize(slide, 2);
}

function problem() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  eyebrow(slide, 'thesis-summary · problem');
  slide.addText('Problem', {
    x: 0.7, y: 0.9, w: 4.4, h: 0.45,
    fontFace: 'Aptos Display', fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('The operating model is fragmented across business units, slowing execution and multiplying tool sprawl.', {
    x: 0.7, y: 1.6, w: 5.4, h: 1.3,
    fontFace: 'Aptos Display', fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('Leaders are seeing duplicated tooling, uneven adoption, and handoff delays that should already be standardized.', {
    x: 0.72, y: 3.35, w: 5.2, h: 0.8,
    fontFace: 'Aptos', fontSize: 12, color: TOKENS.textSecondary, margin: 0,
  });
  panel(slide, 7.0, 1.45, 5.15, 3.95, TOKENS.surfaceAlt);
  slide.addText('support field\nfragmentation evidence', {
    x: 7.3, y: 2.2, w: 4.5, h: 1.0,
    fontFace: 'Aptos', fontSize: 14, color: TOKENS.textSoft,
    align: 'center', valign: 'mid', margin: 0.08,
  });
  risk(slide, 'Risk note: summary slides fail when supporting points visually compete with the thesis.');
  finalize(slide, 3);
}

function recommendations() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  eyebrow(slide, 'thesis-summary · recommendation');
  slide.addText('Recommendation', {
    x: 0.7, y: 0.9, w: 4.6, h: 0.45,
    fontFace: 'Aptos Display', fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('Launch a phased automation program led by one transformation office, starting with one pilot before scaling.', {
    x: 0.7, y: 1.6, w: 5.5, h: 1.35,
    fontFace: 'Aptos Display', fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('The goal is controlled proof, tighter governance, and one repeatable operating model instead of scattered point fixes.', {
    x: 0.72, y: 3.35, w: 5.1, h: 0.8,
    fontFace: 'Aptos', fontSize: 12, color: TOKENS.textSecondary, margin: 0,
  });
  panel(slide, 7.0, 1.45, 5.15, 3.95, TOKENS.surfaceAlt);
  slide.addText('support field\npilot scope and governance', {
    x: 7.3, y: 2.2, w: 4.5, h: 1.0,
    fontFace: 'Aptos', fontSize: 14, color: TOKENS.textSoft,
    align: 'center', valign: 'mid', margin: 0.08,
  });
  finalize(slide, 4);
}

function metric() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  eyebrow(slide, 'metric');
  slide.addText('KPI target', {
    x: 0.7, y: 0.9, w: 4.0, h: 0.45,
    fontFace: 'Aptos Display', fontSize: 22, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('72% automation coverage', {
    x: 0.7, y: 1.8, w: 5.8, h: 1.2,
    fontFace: 'Aptos Display', fontSize: 30, bold: true, color: TOKENS.accent, margin: 0,
  });
  slide.addText('Target this in year one while reducing handoff delays by 35 percent.', {
    x: 0.72, y: 3.25, w: 5.6, h: 0.75,
    fontFace: 'Aptos', fontSize: 14, color: TOKENS.textSecondary, margin: 0,
  });
  panel(slide, 7.05, 1.35, 5.2, 3.9, TOKENS.surfaceAlt);
  slide.addText('metric support field\neditable chart optional', {
    x: 7.35, y: 2.2, w: 4.55, h: 1.0,
    fontFace: 'Aptos', fontSize: 14, color: TOKENS.textSoft,
    align: 'center', valign: 'mid', margin: 0.08,
  });
  risk(slide, 'Risk note: do not bury the KPI inside a generic four-card dashboard.');
  finalize(slide, 5);
}

function comparison() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  eyebrow(slide, 'comparison');
  slide.addText('Decision framing', {
    x: 0.7, y: 0.9, w: 5.2, h: 0.45,
    fontFace: 'Aptos Display', fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('Recommended lane should dominate because symmetry would be false neutrality here.', {
    x: 0.7, y: 1.52, w: 5.2, h: 0.44,
    fontFace: 'Aptos', fontSize: 11.5, color: TOKENS.textSecondary, margin: 0,
  });
  panel(slide, 0.7, 2.2, 3.9, 2.7, TOKENS.surface);
  panel(slide, 4.95, 2.2, 4.6, 2.8, TOKENS.accentSoft, TOKENS.accent);
  slide.addText('Current / baseline', {
    x: 1.0, y: 2.52, w: 2.6, h: 0.3,
    fontFace: 'Aptos', fontSize: 17, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('Duplicated ownership and fragmented tooling', {
    x: 1.0, y: 3.05, w: 3.0, h: 0.95,
    fontFace: 'Aptos', fontSize: 12, color: TOKENS.textSoft, margin: 0,
  });
  slide.addText('Recommended', {
    x: 5.25, y: 2.5, w: 3.0, h: 0.3,
    fontFace: 'Aptos', fontSize: 18, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('One transformation office, one pilot, one accountable owner', {
    x: 5.25, y: 3.02, w: 3.6, h: 0.95,
    fontFace: 'Aptos', fontSize: 13, color: TOKENS.textSecondary, margin: 0,
  });
  slide.addText('preferred', {
    x: 8.2, y: 2.2, w: 0.9, h: 0.22,
    fontFace: 'Aptos', fontSize: 9, bold: true, color: TOKENS.accent, align: 'center', margin: 0,
  });
  risk(slide, 'Risk note: if one option is clearly preferred, equal-width columns are the wrong default.');
  finalize(slide, 6);
}

function timeline() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  eyebrow(slide, 'process-timeline');
  slide.addText('Phased rollout', {
    x: 0.7, y: 0.9, w: 5.0, h: 0.45,
    fontFace: 'Aptos Display', fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('The rollout should read as a sequence with one clear current focus.', {
    x: 0.7, y: 1.52, w: 6.0, h: 0.44,
    fontFace: 'Aptos', fontSize: 12, color: TOKENS.textSecondary, margin: 0,
  });
  const labels = ['Pilot in Q1', 'Scale in Q2', 'Standardize in Q3', 'Embed in Q4'];
  const xs = [1.0, 3.35, 5.7, 8.05];
  slide.addShape(pptx.ShapeType.line, { x: 1.2, y: 3.55, w: 7.7, h: 0, line: { color: TOKENS.rule, pt: 1.2 } });
  xs.forEach((x, idx) => {
    slide.addShape(pptx.ShapeType.ellipse, { x, y: 3.28, w: 0.32, h: 0.32, line: { color: idx === 1 ? TOKENS.accent : TOKENS.rule, pt: 1 }, fill: { color: idx === 1 ? TOKENS.accent : TOKENS.surface } });
    slide.addText(labels[idx], {
      x: x - 0.32, y: 2.62, w: 1.65, h: 0.45,
      fontFace: 'Aptos', fontSize: 11, bold: true,
      color: idx === 1 ? TOKENS.accent : TOKENS.textPrimary,
      align: 'center', margin: 0,
    });
  });
  slide.addText('Now', {
    x: 3.55, y: 3.95, w: 0.65, h: 0.22,
    fontFace: 'Aptos', fontSize: 10, bold: true, color: TOKENS.accent,
    align: 'center', margin: 0,
  });
  slide.addText('Scale in Q2', {
    x: 3.1, y: 4.2, w: 2.1, h: 0.6,
    fontFace: 'Aptos', fontSize: 12, color: TOKENS.textSecondary,
    align: 'center', margin: 0,
  });
  risk(slide, 'Risk note: too many milestones on one spine will collapse the sequence into clutter.');
  finalize(slide, 7);
}

function closing() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWarm };
  eyebrow(slide, 'closing');
  slide.addText('Approve one pilot and assign one accountable owner.', {
    x: 0.9, y: 1.55, w: 10.4, h: 1.55,
    fontFace: 'Aptos Display', fontSize: 28, bold: true,
    color: TOKENS.textPrimary, margin: 0, align: 'center',
  });
  slide.addText('That is the smallest complete move that turns strategy into operating proof.', {
    x: 2.0, y: 3.45, w: 8.2, h: 0.9,
    fontFace: 'Aptos', fontSize: 14, color: TOKENS.textSecondary,
    margin: 0, align: 'center',
  });
  panel(slide, 4.45, 4.9, 4.1, 0.6, TOKENS.accentSoft, TOKENS.accent);
  slide.addText('next move: approve the pilot', {
    x: 4.72, y: 5.08, w: 3.55, h: 0.22,
    fontFace: 'Aptos', fontSize: 11, bold: true, color: TOKENS.accent,
    align: 'center', margin: 0,
  });
  slide.addText('closing-takeaway', {
    x: 5.05, y: 5.68, w: 2.9, h: 0.2,
    fontFace: 'Aptos', fontSize: 9, color: TOKENS.textSoft,
    align: 'center', margin: 0,
  });
  finalize(slide, 8);
}

cover();
agenda();
problem();
recommendations();
metric();
comparison();
timeline();
closing();

fs.mkdirSync(path.dirname(OUT), { recursive: true });
pptx.writeFile({ fileName: OUT });
