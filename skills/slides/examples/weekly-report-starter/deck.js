const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');
const layoutHelpers = require('../../assets/pptxgenjs_helpers/layout');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'OpenClaw';
pptx.company = 'OpenClaw';
pptx.subject = 'Weekly Report Starter';
pptx.title = 'Weekly Report Starter';
pptx.lang = 'en-US';
pptx.theme = {
  headFontFace: 'Aptos Display',
  bodyFontFace: 'Aptos',
  lang: 'en-US',
};

const OUT = path.join(__dirname, 'exports', 'weekly-report-starter.pptx');
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
  warning: 'B85C38',
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

function eyebrow(slide, text, x = 0.7, y = 0.45, w = 3.8) {
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
  eyebrow(slide, 'weekly report · operating review');
  slide.addText('Weekly Operating Review', {
    x: 0.7, y: 1.0, w: 6.2, h: 1.3,
    fontFace: 'Aptos Display', fontSize: 30, bold: true,
    color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('Status, KPI movement, risks, and next actions for the week ending Friday.', {
    x: 0.7, y: 2.45, w: 5.9, h: 0.9,
    fontFace: 'Aptos', fontSize: 15, color: TOKENS.textSecondary, margin: 0,
  });
  slide.addText('Decision focus: where leadership needs to unblock delivery this week.', {
    x: 0.72, y: 4.08, w: 5.7, h: 0.35,
    fontFace: 'Aptos', fontSize: 10.5, color: TOKENS.textSoft, margin: 0,
  });
  panel(slide, 7.2, 1.0, 5.0, 4.6, TOKENS.accentSoft, TOKENS.accent);
  slide.addText('hero field\nweekly report', {
    x: 7.45, y: 2.15, w: 4.5, h: 1.1,
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
  slide.addText('Five slides to get from status scan to action.', {
    x: 0.7, y: 1.5, w: 5.5, h: 0.4,
    fontFace: 'Aptos', fontSize: 11, color: TOKENS.textSecondary, margin: 0,
  });
  const items = ['Status summary', 'KPI movement', 'Risk framing', 'Timeline', 'Next steps'];
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
  slide.addText('scan first\nthen discuss', {
    x: 7.5, y: 2.4, w: 4.2, h: 0.8,
    fontFace: 'Aptos Display', fontSize: 18, bold: true, color: TOKENS.textPrimary,
    align: 'center', margin: 0,
  });
  finalize(slide, 2);
}

function statusSummary() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  eyebrow(slide, 'thesis-summary · status');
  slide.addText('Status summary', {
    x: 0.7, y: 0.9, w: 4.4, h: 0.45,
    fontFace: 'Aptos Display', fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('Delivery is on track overall, but one cross-functional dependency is now the main source of schedule risk.', {
    x: 0.7, y: 1.55, w: 5.6, h: 1.25,
    fontFace: 'Aptos Display', fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('Execution is steady inside teams. The current issue is alignment between functions, not lack of activity.', {
    x: 0.72, y: 3.25, w: 5.2, h: 0.8,
    fontFace: 'Aptos', fontSize: 12, color: TOKENS.textSecondary, margin: 0,
  });
  panel(slide, 7.0, 1.45, 5.1, 3.9, TOKENS.surfaceAlt);
  slide.addText('support field\nstatus evidence', {
    x: 7.25, y: 2.2, w: 4.5, h: 1.0,
    fontFace: 'Aptos', fontSize: 14, color: TOKENS.textSoft,
    align: 'center', valign: 'mid', margin: 0.08,
  });
  finalize(slide, 3);
}

function metric() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  eyebrow(slide, 'metric');
  slide.addText('KPI movement', {
    x: 0.7, y: 0.9, w: 4.0, h: 0.45,
    fontFace: 'Aptos Display', fontSize: 22, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('94% milestone completion', {
    x: 0.7, y: 1.8, w: 5.6, h: 1.2,
    fontFace: 'Aptos Display', fontSize: 30, bold: true, color: TOKENS.accent, margin: 0,
  });
  slide.addText('Up 6 points week over week, but at risk if the current dependency remains unresolved beyond Tuesday.', {
    x: 0.72, y: 3.25, w: 5.7, h: 0.85,
    fontFace: 'Aptos', fontSize: 14, color: TOKENS.textSecondary, margin: 0,
  });
  panel(slide, 7.0, 1.35, 5.2, 3.95, TOKENS.surfaceAlt);
  slide.addText('metric support field\nchart or variance note', {
    x: 7.35, y: 2.2, w: 4.5, h: 1.0,
    fontFace: 'Aptos', fontSize: 14, color: TOKENS.textSoft,
    align: 'center', valign: 'mid', margin: 0.08,
  });
  finalize(slide, 4);
}

function comparison() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  eyebrow(slide, 'comparison · risk framing');
  slide.addText('Risk framing', {
    x: 0.7, y: 0.9, w: 5.0, h: 0.45,
    fontFace: 'Aptos Display', fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('The core choice is between absorbing short-term friction or accepting a larger downstream slip.', {
    x: 0.7, y: 1.5, w: 5.3, h: 0.5,
    fontFace: 'Aptos', fontSize: 11.5, color: TOKENS.textSecondary, margin: 0,
  });
  panel(slide, 0.7, 2.2, 3.9, 2.7, TOKENS.surface);
  panel(slide, 4.95, 2.2, 4.6, 2.8, TOKENS.accentSoft, TOKENS.accent);
  slide.addText('Wait for alignment', {
    x: 1.0, y: 2.52, w: 2.6, h: 0.3,
    fontFace: 'Aptos', fontSize: 17, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('Less friction now, higher risk of compounding delay later.', {
    x: 1.0, y: 3.05, w: 3.0, h: 0.95,
    fontFace: 'Aptos', fontSize: 12, color: TOKENS.textSoft, margin: 0,
  });
  slide.addText('Escalate now', {
    x: 5.25, y: 2.5, w: 3.0, h: 0.3,
    fontFace: 'Aptos', fontSize: 18, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('Short-term discomfort, cleaner recovery path, lower overall schedule risk.', {
    x: 5.25, y: 3.0, w: 3.65, h: 1.0,
    fontFace: 'Aptos', fontSize: 13, color: TOKENS.textSecondary, margin: 0,
  });
  slide.addText('preferred', {
    x: 8.2, y: 2.2, w: 0.9, h: 0.22,
    fontFace: 'Aptos', fontSize: 9, bold: true, color: TOKENS.accent, align: 'center', margin: 0,
  });
  risk(slide, 'Risk note: if there is a recommended action, do not hide it behind false balance.');
  finalize(slide, 5);
}

function timeline() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWhite };
  eyebrow(slide, 'process-timeline');
  slide.addText('Recovery timeline', {
    x: 0.7, y: 0.9, w: 5.2, h: 0.45,
    fontFace: 'Aptos Display', fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  });
  slide.addText('The schedule can recover within the week if the dependency is escalated immediately.', {
    x: 0.7, y: 1.5, w: 6.0, h: 0.45,
    fontFace: 'Aptos', fontSize: 12, color: TOKENS.textSecondary, margin: 0,
  });
  const labels = ['Escalate Mon', 'Resolve Tue', 'Recover Wed', 'Stabilize Thu'];
  const xs = [1.0, 3.35, 5.7, 8.05];
  slide.addShape(pptx.ShapeType.line, { x: 1.2, y: 3.55, w: 7.7, h: 0, line: { color: TOKENS.rule, pt: 1.2 } });
  xs.forEach((x, idx) => {
    slide.addShape(pptx.ShapeType.ellipse, { x, y: 3.28, w: 0.32, h: 0.32, line: { color: idx === 1 ? TOKENS.accent : TOKENS.rule, pt: 1 }, fill: { color: idx === 1 ? TOKENS.accent : TOKENS.surface } });
    slide.addText(labels[idx], {
      x: x - 0.35, y: 2.62, w: 1.72, h: 0.45,
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
  slide.addText('Resolve Tue', {
    x: 3.05, y: 4.2, w: 2.25, h: 0.6,
    fontFace: 'Aptos', fontSize: 12, color: TOKENS.textSecondary,
    align: 'center', margin: 0,
  });
  finalize(slide, 6);
}

function closing() {
  const slide = pptx.addSlide();
  slide.background = { color: TOKENS.bgWarm };
  eyebrow(slide, 'closing');
  slide.addText('Escalate the dependency now and review recovery on Wednesday.', {
    x: 0.9, y: 1.55, w: 10.4, h: 1.55,
    fontFace: 'Aptos Display', fontSize: 28, bold: true,
    color: TOKENS.textPrimary, margin: 0, align: 'center',
  });
  slide.addText('That is the smallest move with the highest leverage for this week’s operating report.', {
    x: 2.0, y: 3.45, w: 8.2, h: 0.9,
    fontFace: 'Aptos', fontSize: 14, color: TOKENS.textSecondary,
    margin: 0, align: 'center',
  });
  panel(slide, 4.3, 4.9, 4.4, 0.6, TOKENS.accentSoft, TOKENS.accent);
  slide.addText('next move: escalate today', {
    x: 4.58, y: 5.08, w: 3.85, h: 0.22,
    fontFace: 'Aptos', fontSize: 11, bold: true, color: TOKENS.accent,
    align: 'center', margin: 0,
  });
  slide.addText('weekly-report-starter', {
    x: 4.75, y: 5.68, w: 3.5, h: 0.2,
    fontFace: 'Aptos', fontSize: 9, color: TOKENS.textSoft,
    align: 'center', margin: 0,
  });
  finalize(slide, 7);
}

cover();
agenda();
statusSummary();
metric();
comparison();
timeline();
closing();

fs.mkdirSync(path.dirname(OUT), { recursive: true });
pptx.writeFile({ fileName: OUT });
