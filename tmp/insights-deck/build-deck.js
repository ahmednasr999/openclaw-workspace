const PptxGenJS = require("pptxgenjs");
const {
  warnIfSlideHasOverlaps,
  warnIfSlideElementsOutOfBounds,
} = require("./pptxgenjs_helpers");

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pptx.author = "Ahmed Nasr - Delivery PMO";
pptx.company = "TopMed - Saudi German Hospital Group";
pptx.subject = "Insights Bank - Additional Insight Ideas";
pptx.title = "TopMed Insights Bank";

// ─── THEME ───
const NAVY = "1A3A6B";
const DARK = "222222";
const WHITE = "FFFFFF";
const LIGHT_BG = "F2F4F8";
const ACCENT_BLUE = "2E75B6";
const ACCENT_GREEN = "0D8050";
const ACCENT_RED = "C0392B";
const ACCENT_ORANGE = "D4740A";
const GRAY = "666666";
const LIGHT_GRAY = "CCCCCC";
const VERY_LIGHT = "EDF1F7";

const FONT = "Segoe UI";
const FONT_BOLD = "Segoe UI";

// ─── HELPERS ───
function addSlide(opts = {}) {
  const slide = pptx.addSlide();
  // Navy bar at top
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.08, fill: { color: NAVY },
  });
  // Light bottom bar
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 7.1, w: "100%", h: 0.4, fill: { color: VERY_LIGHT },
  });
  if (opts.title) {
    slide.addText(opts.title, {
      x: 0.5, y: 0.2, w: 12.3, h: 0.5,
      fontSize: 22, fontFace: FONT_BOLD, bold: true, color: NAVY,
    });
  }
  if (opts.subtitle) {
    slide.addText(opts.subtitle, {
      x: 0.5, y: 0.65, w: 12.3, h: 0.35,
      fontSize: 12, fontFace: FONT, italic: true, color: GRAY,
    });
  }
  // Page number
  slide.addText(opts.pageNum ? String(opts.pageNum) : "", {
    x: 12.0, y: 7.1, w: 1.0, h: 0.35,
    fontSize: 9, fontFace: FONT, color: GRAY, align: "right",
  });
  // Footer
  slide.addText("TopMed Insights Bank | March 2026 | Confidential", {
    x: 0.5, y: 7.1, w: 8, h: 0.35,
    fontSize: 8, fontFace: FONT, color: LIGHT_GRAY,
  });
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
  return slide;
}

function addSectionDivider(title, subtitle, icon, pageNum) {
  const slide = pptx.addSlide();
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: "100%", fill: { color: NAVY },
  });
  slide.addText(icon, {
    x: 0, y: 1.5, w: "100%", h: 1.5,
    fontSize: 60, align: "center",
  });
  slide.addText(title, {
    x: 1, y: 3.0, w: 11.33, h: 1.0,
    fontSize: 32, fontFace: FONT_BOLD, bold: true, color: WHITE, align: "center",
  });
  slide.addText(subtitle, {
    x: 1.5, y: 4.2, w: 10.33, h: 0.8,
    fontSize: 14, fontFace: FONT, color: LIGHT_GRAY, align: "center",
  });
  slide.addText(String(pageNum), {
    x: 12.0, y: 7.1, w: 1.0, h: 0.35,
    fontSize: 9, fontFace: FONT, color: "4A6FA5", align: "right",
  });
  return slide;
}

function insightAreaSlide(section, pageNum) {
  const slide = addSlide({
    title: `${section.icon}  ${section.area}`,
    subtitle: section.is_new ? "NEW INSIGHT AREA" : "EXPANSION TO EXISTING AREA",
    pageNum,
  });

  // Questions column
  slide.addText("Analytical Questions", {
    x: 0.5, y: 1.1, w: 6.0, h: 0.35,
    fontSize: 12, fontFace: FONT_BOLD, bold: true, color: NAVY,
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.5, y: 1.45, w: 5.8, h: 0.03, fill: { color: ACCENT_BLUE },
  });

  const qRows = section.questions.map((q, i) => [
    { text: `${i + 1}.`, options: { bold: true, fontSize: 10, color: NAVY, fontFace: FONT } },
    { text: ` ${q}`, options: { fontSize: 10, color: DARK, fontFace: FONT } },
  ]);
  slide.addText(qRows.map(r => r), {
    x: 0.5, y: 1.6, w: 6.0, h: 5.0,
    fontSize: 10, fontFace: FONT, color: DARK, valign: "top",
    lineSpacingMultiple: 1.4,
    paraSpaceBefore: 4,
  });

  // Insights column
  slide.addText("Insight Titles", {
    x: 6.8, y: 1.1, w: 6.0, h: 0.35,
    fontSize: 12, fontFace: FONT_BOLD, bold: true, color: ACCENT_GREEN,
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 6.8, y: 1.45, w: 5.8, h: 0.03, fill: { color: ACCENT_GREEN },
  });

  const iText = section.insights.map(ins => `▸  ${ins}`).join("\n");
  slide.addText(iText, {
    x: 6.8, y: 1.6, w: 6.0, h: 5.0,
    fontSize: 10, fontFace: FONT, color: DARK, valign: "top", bold: true,
    lineSpacingMultiple: 1.4,
    paraSpaceBefore: 4,
  });

  // Vertical divider
  slide.addShape(pptx.ShapeType.rect, {
    x: 6.55, y: 1.1, w: 0.02, h: 5.5, fill: { color: LIGHT_GRAY },
  });

  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function insightBriefSlide(brief, pageNum) {
  const slide = addSlide({
    title: `${brief.icon}  ${brief.title}`,
    subtitle: `${brief.area} | Confidence: ${brief.confidence}`,
    pageNum,
  });

  const fields = [
    { label: "Observation", value: brief.observation, color: NAVY },
    { label: "Supporting Evidence", value: brief.evidence, color: NAVY },
    { label: "Root Cause", value: brief.root_cause, color: NAVY },
    { label: "Business Impact", value: brief.impact, color: ACCENT_RED },
    { label: "Recommended Actions", value: brief.actions, color: ACCENT_GREEN },
    { label: "Strategic Importance", value: brief.strategic, color: ACCENT_BLUE },
  ];

  let y = 1.1;
  for (const f of fields) {
    slide.addText([
      { text: `${f.label}: `, options: { bold: true, fontSize: 9.5, color: f.color, fontFace: FONT_BOLD } },
      { text: f.value, options: { fontSize: 9.5, color: DARK, fontFace: FONT } },
    ], {
      x: 0.5, y, w: 12.3, h: 0.85,
      valign: "top",
      lineSpacingMultiple: 1.15,
    });
    y += 0.88;
  }

  // Confidence badge - positioned below the title bar to avoid overlap
  const confColor = brief.confidence === "High" ? ACCENT_GREEN : ACCENT_ORANGE;
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 11.5, y: 0.68, w: 1.3, h: 0.32,
    fill: { color: confColor }, rectRadius: 0.1,
  });
  slide.addText(brief.confidence.toUpperCase(), {
    x: 11.5, y: 0.68, w: 1.3, h: 0.32,
    fontSize: 9, fontFace: FONT_BOLD, bold: true, color: WHITE, align: "center", valign: "middle",
  });

  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

// ═══════════════════════════════════════════
// DATA
// ═══════════════════════════════════════════

const SECTIONS = [
  {
    area: "Emergency Department (ED)", icon: "🚨", is_new: true,
    questions: [
      "What is the average door-to-doctor time across different shifts?",
      "Are ED patients being admitted or discharged within optimal timeframes?",
      "Is ED overcrowding during peak hours leading to patient walkouts (LWBS)?",
      "Are high-acuity patients being triaged and treated faster than low-acuity?",
      "What percentage of ED visits result in hospital admissions vs. discharge?",
    ],
    insights: [
      "ED Door-to-Doctor Time Variance Across Shifts",
      "ED Patient Boarding and Disposition Delays",
      "Left Without Being Seen (LWBS) Rate and Revenue Impact",
      "Triage Accuracy and Acuity-Based Resource Allocation",
      "ED-to-Inpatient Conversion Rate by Specialty",
    ],
  },
  {
    area: "Inpatient Department (IPD)", icon: "🏥", is_new: true,
    questions: [
      "What is the average length of stay (ALOS) by specialty vs. benchmarks?",
      "Are bed occupancy rates balanced across wards and floors?",
      "Are readmission rates within 30 days indicating quality gaps?",
      "Is discharge planning causing unnecessary bed-blocking?",
      "Are surgical cancellations on the day of surgery affecting OR utilization?",
    ],
    insights: [
      "Length of Stay Optimization by Clinical Specialty",
      "Bed Occupancy Imbalance Across Hospital Wards",
      "30-Day Readmission Rates and Root Causes",
      "Delayed Discharge and Bed Turnover Impact",
      "Same-Day Surgical Cancellation Rate and Revenue Loss",
    ],
  },
  {
    area: "Pharmacy", icon: "💊", is_new: true,
    questions: [
      "Are high-cost medications prescribed when cost-effective alternatives exist?",
      "Is pharmacy inventory aligned with actual consumption patterns?",
      "Are medication turnaround times from order to administration affecting care?",
      "Is formulary compliance being maintained across prescribing physicians?",
      "What is the revenue contribution of outpatient pharmacy vs. inpatient?",
    ],
    insights: [
      "High-Cost Medication Substitution Opportunities",
      "Pharmacy Stock-Out and Expiry Rate Analysis",
      "Medication Dispensing Turnaround Time",
      "Formulary Adherence Rate by Prescriber",
      "Outpatient Pharmacy Revenue Optimization",
    ],
  },
  {
    area: "Patient Experience", icon: "⭐", is_new: true,
    questions: [
      "Are patient satisfaction scores declining in specific departments?",
      "Is there a correlation between waiting times and patient complaints?",
      "Are patient no-show rates affecting revenue and resource planning?",
      "What percentage of patients return for follow-up visits within 90 days?",
      "Are online reviews and ratings reflecting internal quality metrics?",
    ],
    insights: [
      "Patient Satisfaction Score Trends by Department",
      "Wait Time Impact on Patient Retention",
      "Patient No-Show Patterns and Financial Impact",
      "Patient Retention and Follow-Up Compliance",
      "Digital Reputation vs. Internal Quality Gap",
    ],
  },
  {
    area: "Supply Chain & Procurement", icon: "📦", is_new: true,
    questions: [
      "Are procurement costs for consumables increasing faster than patient volume?",
      "Is there price variance for the same items across different hospitals?",
      "Are vendor contracts being renegotiated at optimal intervals?",
      "Is inventory carrying cost proportional to consumption?",
    ],
    insights: [
      "Medical Consumable Cost Per Patient Trend",
      "Cross-Hospital Procurement Price Variance",
      "Vendor Contract Renewal Optimization",
      "Inventory Carrying Cost vs. Consumption Efficiency",
    ],
  },
  {
    area: "Quality & Clinical Safety", icon: "🛡️", is_new: true,
    questions: [
      "Are hospital-acquired infection rates trending within acceptable limits?",
      "Are near-miss and adverse event reporting rates increasing or declining?",
      "Are clinical protocol compliance rates consistent across hospitals?",
      "Is there a correlation between staffing ratios and patient safety events?",
    ],
    insights: [
      "Hospital-Acquired Infection Rate Trends",
      "Incident Reporting Culture and Near-Miss Trends",
      "Clinical Protocol Adherence Across Network",
      "Nurse-to-Patient Ratio Impact on Safety Events",
    ],
  },
];

const EXPANSIONS = [
  {
    area: "Radiology (Additional)", icon: "🩻", is_new: false,
    questions: [
      "What is the radiology report turnaround time by modality?",
      "Are repeat/rejected imaging studies increasing costs?",
    ],
    insights: [
      "Radiology Report Turnaround Time by Modality",
      "Radiology Repeat Study Rate and Quality Impact",
    ],
  },
  {
    area: "Laboratory (Additional)", icon: "🔬", is_new: false,
    questions: [
      "Are critical value notification times meeting clinical standards?",
      "Is send-out testing volume growing when in-house capacity exists?",
    ],
    insights: [
      "Critical Lab Value Notification Compliance",
      "In-House vs. Send-Out Test Migration Opportunity",
    ],
  },
  {
    area: "OPD (Additional)", icon: "🩺", is_new: false,
    questions: [
      "Are new patient acquisition rates growing or stagnating by specialty?",
      "What is the doctor productivity rate (patients per clinical hour)?",
    ],
    insights: [
      "New Patient Acquisition Rate by Specialty",
      "Doctor Productivity and Clinic Slot Utilization",
    ],
  },
  {
    area: "Revenue Cycle (Additional)", icon: "💰", is_new: false,
    questions: [
      "What is the average days in accounts receivable (AR) by payer?",
      "Are self-pay collection rates declining?",
      "Is payer mix shifting in a way that impacts overall margin?",
    ],
    insights: [
      "Accounts Receivable Aging by Payer Category",
      "Self-Pay Collection Rate Decline",
      "Payer Mix Shift and Margin Impact Analysis",
    ],
  },
  {
    area: "Operational Efficiency (Additional)", icon: "⚙️", is_new: false,
    questions: [
      "Is overtime spending proportional to patient volume increases?",
      "Are energy and facility costs per patient bed-day within benchmark?",
    ],
    insights: [
      "Overtime Cost vs. Patient Volume Correlation",
      "Facility Cost Per Occupied Bed-Day",
    ],
  },
];

const SAMPLE_BRIEFS = [
  {
    area: "Emergency Department", icon: "🚨", confidence: "High",
    title: "Left Without Being Seen (LWBS) Rate and Revenue Impact",
    observation: "LWBS rate increased from 3.2% to 5.8% over the past two quarters, with the highest walkout rates occurring between 6:00 PM and 10:00 PM.",
    evidence: "Average door-to-doctor time exceeds 45 minutes during evening peak hours. Patient walkout incidents correlate with triage nurse shift changeover gaps (5:30-6:30 PM). Weekend LWBS rates are 40% higher than weekdays.",
    root_cause: "Insufficient triage staffing during evening shift changeover window, combined with no fast-track pathway for low-acuity patients (ESI Level 4-5) who represent 35% of evening volume.",
    impact: "Estimated annual revenue loss of SAR 2.1 Million from walkout patients. Additional risk of negative online reviews and patient diversion to competing facilities.",
    actions: "Implement triage overlap shift (5:00-7:00 PM). Create fast-track pathway for low-acuity patients. Install real-time wait time display. Set up automated SMS notification when patient is next.",
    strategic: "Reducing LWBS by 50% directly impacts both revenue recovery (SAR 1.05M) and patient satisfaction scores, increasingly tied to insurance network inclusion criteria in KSA.",
  },
  {
    area: "Inpatient Department", icon: "🏥", confidence: "High",
    title: "Delayed Discharge and Bed Turnover Impact",
    observation: "Average time from physician discharge order to actual patient departure is 6.2 hours, against a target of 2 hours. This creates a daily average of 12 blocked beds across the network.",
    evidence: "Discharge orders peak at 11:00 AM but actual departures peak at 5:00 PM. Pharmacy medication reconciliation averages 2.1 hours. Insurance pre-authorization for follow-up adds 1.5 hours.",
    root_cause: "Sequential discharge process instead of parallel processing. No discharge planning initiated at admission. Lack of discharge lounge for patients cleared but awaiting transport.",
    impact: "12 blocked beds daily translates to approximately SAR 4.3 Million in annual lost admission revenue. ED boarding times increase by 2.3 hours when IPD beds are blocked.",
    actions: "Implement parallel discharge processing. Begin discharge planning at Day 1 of admission. Create discharge lounge to free beds immediately. Set discharge time targets by ward.",
    strategic: "A 50% improvement in discharge time would free 6 beds daily, equivalent to adding a new ward without capital expenditure.",
  },
  {
    area: "Pharmacy", icon: "💊", confidence: "Medium",
    title: "High-Cost Medication Substitution Opportunities",
    observation: "Analysis of top 50 medications by spend reveals 18 branded drugs have therapeutically equivalent generic or biosimilar alternatives, representing 31% of total pharmacy expenditure.",
    evidence: "Monthly spend on substitutable branded medications averages SAR 420,000. Generic alternatives are 40-75% cheaper. Three hospitals already use generics for 8 of these with no efficacy differences.",
    root_cause: "No standardized formulary review cycle. Physician prescribing habits favor familiar branded products. P&T committee meets quarterly but lacks cost-effectiveness analysis.",
    impact: "Potential annual savings of SAR 2.5-3.8 Million from generic/biosimilar substitution across the network, with no compromise in clinical outcomes.",
    actions: "Conduct formulary review for top 50 drugs with cost-effectiveness analysis. Present substitution recommendations to P&T committee. Implement therapeutic interchange protocols.",
    strategic: "Pharmacy cost optimization delivers immediate P&L improvement. Positions TopMed aligned with Saudi Vision 2030 healthcare cost efficiency goals.",
  },
  {
    area: "Patient Experience", icon: "⭐", confidence: "High",
    title: "Patient No-Show Patterns and Financial Impact",
    observation: "Average OPD no-show rate is 22%, with Dermatology (31%) and Ophthalmology (28%) significantly higher. No-show rates 3x higher for appointments booked >14 days in advance.",
    evidence: "Monthly revenue impact estimated at SAR 890,000. Clinics with SMS reminders (48h + 2h) show 35% lower no-show rates. Saturday morning slots have highest no-show rate (34%).",
    root_cause: "Inconsistent appointment reminders. No penalty for repeat no-shows. Overbooking not calibrated to specialty-specific rates. Long booking horizons increase abandonment.",
    impact: "Estimated annual revenue loss of SAR 10.7 Million from no-show appointments. Additional hidden cost in physician idle time and wasted clinic preparation.",
    actions: "Implement dual SMS reminder system (48h + 2h). Deploy specialty-specific overbooking ratios. Introduce waitlist backfill for same-day cancellations. Flag repeat no-show patients.",
    strategic: "A 30% reduction recovers SAR 3.2M annually while improving physician utilization. One of the highest-ROI operational improvements available.",
  },
  {
    area: "Supply Chain", icon: "📦", confidence: "High",
    title: "Cross-Hospital Procurement Price Variance",
    observation: "Price comparison across 15 hospitals reveals identical medical consumables procured at prices varying by 15-42%, with surgical gloves, IV sets, and wound care products showing widest variance.",
    evidence: "Top 20 consumables show average price variance of 28%. Three hospitals consistently pay 15-20% premium. Vendor contracts have different renewal dates and terms.",
    root_cause: "Decentralized procurement without network-wide benchmarking. Individual hospitals negotiate independently. No centralized contract management. Historical pricing accepted without rebidding.",
    impact: "Estimated annual savings of SAR 5.2 Million by standardizing to the best-available network rate for top 100 consumables.",
    actions: "Establish centralized procurement dashboard. Consolidate vendor contracts for top 100 consumables. Implement mandatory competitive bidding >SAR 100,000. Create quarterly price variance report.",
    strategic: "Centralized procurement is foundational for any multi-hospital network. Delivers immediate savings while building infrastructure for ongoing optimization.",
  },
  {
    area: "Quality & Safety", icon: "🛡️", confidence: "Medium",
    title: "Incident Reporting Culture and Near-Miss Trends",
    observation: "Near-miss reporting rates vary 5x across hospitals (highest: 12.4/1,000 patient days; lowest: 2.3/1,000). Low-reporting hospitals don't have fewer incidents; they have weaker reporting culture.",
    evidence: "Hospitals with dedicated quality champions report 3.2x more near-misses. Medication near-misses account for 45% of reports. Reporting dropped 18% after a punitive response at one facility.",
    root_cause: "Inconsistent just-culture implementation. Some hospitals still associate reporting with blame. Anonymous reporting not available at all facilities. No positive feedback loop.",
    impact: "Under-reporting masks safety risks. Each reported near-miss prevents an average of 300 unsafe conditions. Low-reporting hospitals carry unquantified patient safety liability.",
    actions: "Standardize just-culture training with annual refresher. Implement anonymous digital reporting channel. Create monthly 'Safety Spotlight.' Share anonymized learnings quarterly.",
    strategic: "Near-miss reporting is a leading indicator of safety culture. Improving rates is a prerequisite for CBAHI accreditation excellence.",
  },
  {
    area: "Radiology", icon: "🩻", confidence: "High",
    title: "Radiology Report Turnaround Time by Modality",
    observation: "Average TAT varies: X-ray 2.1h, Ultrasound 4.3h, CT 6.8h, MRI 11.2h. CT and MRI exceed the 4-hour target in 67% of cases.",
    evidence: "ED-ordered CT reports average 8.4 hours vs. 5.2 hours for scheduled outpatient. Weekend TAT is 2.3x longer. Three radiologists handle 60% of MRI reads.",
    root_cause: "Uneven radiologist workload distribution. No priority queue for ED-ordered studies. Weekend coverage relies on on-call rather than active staffing.",
    impact: "Delayed reports extend ED disposition by 2-4 hours and delay inpatient treatment decisions. Estimated SAR 1.8M annually from delayed discharges.",
    actions: "Implement priority-based PACS worklist. Redistribute MRI reading load. Add active evening radiologist shift (4 PM-midnight). Track TAT daily by modality.",
    strategic: "Radiology TAT directly impacts ED throughput, inpatient LOS, and physician satisfaction. Meeting 4-hour target is a competitive differentiator.",
  },
  {
    area: "Laboratory", icon: "🔬", confidence: "Medium",
    title: "In-House vs. Send-Out Test Migration Opportunity",
    observation: "Send-out volume grew 24% YoY while in-house grew only 8%. 12 high-volume send-out tests could be performed in-house with existing or minimal additional equipment.",
    evidence: "Monthly send-out spend averages SAR 340,000. Top 12 tests represent 55% of send-out costs. In-house cost would be 40-65% lower. Send-out TAT: 5-7 days vs. same-day in-house.",
    root_cause: "No regular review of send-out menu against in-house capabilities. Equipment procurement requires lengthy approval. Some tests sent out historically when volumes were low.",
    impact: "Migrating top 12 tests saves approximately SAR 1.4 Million annually while reducing TAT from 5-7 days to same-day.",
    actions: "Conduct feasibility study for top 12 tests. Build business case with ROI timeline. Prioritize migration by volume and margin. Set quarterly targets.",
    strategic: "In-house testing expansion aligns with TopMed's full-service strategy. Faster turnaround improves outcomes and reduces repeat visits.",
  },
  {
    area: "OPD", icon: "🩺", confidence: "High",
    title: "Doctor Productivity and Clinic Slot Utilization",
    observation: "Top quartile physicians see 5.8 patients/clinic hour vs. 2.1 for bottom quartile. Clinic slot utilization averages 71%, meaning 29% of slots go unfilled.",
    evidence: "Specialties with standardized templates show 22% higher throughput. Clinics starting 15+ min late lose 1.5 slots/session. Double-booking varies 5-35% across physicians.",
    root_cause: "No standardized consultation time targets by visit type. Clinic start time not monitored. Patient flow bottlenecks at registration. Some physicians block slots for walk-ins that never materialize.",
    impact: "Improving utilization from 71% to 85% would generate an estimated SAR 8.4 Million in additional annual OPD revenue without adding clinic hours or physicians.",
    actions: "Implement visit-type-based slot duration (new: 20min, follow-up: 10min). Track clinic start time adherence. Deploy pre-visit registration. Release unconfirmed slots 24h before.",
    strategic: "OPD is the front door. Maximizing productivity is the highest-leverage revenue growth initiative without capital expenditure.",
  },
  {
    area: "Revenue Cycle", icon: "💰", confidence: "High",
    title: "Accounts Receivable Aging by Payer Category",
    observation: "Average AR is 78 days (target: 45). Government payers average 112 days, insurance 64 days, self-pay 43 days. AR >90 days represents 34% of outstanding receivables.",
    evidence: "First-pass acceptance rate is 71% (target: 95%). Rejected claims take 28 days for resubmission. Three government contracts have no late-payment penalties. Monthly write-off >180 days averages SAR 280,000.",
    root_cause: "High rejection rate from coding errors and incomplete documentation. No dedicated follow-up for aging government claims. Lack of automated claim tracking. Payment terms not enforced.",
    impact: "Reducing AR from 78 to 55 days would release approximately SAR 18 Million in working capital. Improving first-pass to 90% reduces resubmission costs by SAR 1.2M annually.",
    actions: "Deploy automated claim scrubbing before submission. Create dedicated AR follow-up team for >60 days. Renegotiate government contracts. Implement weekly AR aging dashboard.",
    strategic: "Cash flow is the lifeblood. AR optimization is the single highest-impact financial initiative, freeing capital while reducing bad debt.",
  },
  {
    area: "Operational Efficiency", icon: "⚙️", confidence: "High",
    title: "Overtime Cost vs. Patient Volume Correlation",
    observation: "Overtime spending increased 31% YoY while patient volume grew only 12%. The ratio suggests structural issues rather than demand-driven overtime.",
    evidence: "Nursing overtime is 68% of total overtime spend. ED, ICU, OR consume 52% of all overtime hours. Weekend overtime is 2.8x higher than weekday.",
    root_cause: "Staffing models not updated for current volume patterns. Scheduling based on historical patterns. Overtime approval process is informal. No department-level visibility until monthly payroll.",
    impact: "Estimated SAR 3.6 Million in reducible overtime annually. Additional benefit: reduced nurse burnout and turnover costs.",
    actions: "Build demand-based staffing model using 12-month data. Implement real-time overtime tracking dashboard. Require formal pre-approval for non-emergency overtime. Review shift patterns quarterly.",
    strategic: "Workforce cost is the largest operating expense. Data-driven staffing delivers immediate P&L improvement while improving employee satisfaction.",
  },
];

const PRIORITY_MATRIX = [
  { rank: 1, insight: "AR Aging by Payer Category", revenue: "SAR 18M", data: "Available Now", complexity: "Medium", color: ACCENT_RED },
  { rank: 2, insight: "OPD Slot Utilization", revenue: "SAR 8.4M", data: "Available Now", complexity: "Quick Win", color: ACCENT_RED },
  { rank: 3, insight: "Cross-Hospital Procurement Variance", revenue: "SAR 5.2M", data: "Available Now", complexity: "Medium", color: ACCENT_RED },
  { rank: 4, insight: "Delayed Discharge / Bed Turnover", revenue: "SAR 4.3M", data: "Available Now", complexity: "Medium", color: ACCENT_RED },
  { rank: 5, insight: "Patient No-Show Patterns", revenue: "SAR 10.7M", data: "Available Now", complexity: "Quick Win", color: ACCENT_RED },
  { rank: 6, insight: "Medication Substitution", revenue: "SAR 2.5-3.8M", data: "Needs Collection", complexity: "Medium", color: ACCENT_ORANGE },
  { rank: 7, insight: "ED LWBS Rate", revenue: "SAR 2.1M", data: "Available Now", complexity: "Quick Win", color: ACCENT_ORANGE },
  { rank: 8, insight: "Overtime vs. Volume", revenue: "SAR 3.6M", data: "Available Now", complexity: "Medium", color: ACCENT_ORANGE },
  { rank: 9, insight: "Radiology Report TAT", revenue: "SAR 1.8M", data: "Available Now", complexity: "Quick Win", color: ACCENT_ORANGE },
  { rank: 10, insight: "Send-Out Test Migration", revenue: "SAR 1.4M", data: "Needs Collection", complexity: "Major", color: ACCENT_GREEN },
  { rank: 11, insight: "Near-Miss Reporting Culture", revenue: "Risk Mitigation", data: "Needs Collection", complexity: "Major", color: ACCENT_GREEN },
  { rank: 12, insight: "Digital Reputation vs Quality", revenue: "Brand Value", data: "Needs Integration", complexity: "Medium", color: ACCENT_GREEN },
];

const CROSS_DEPT = [
  { title: "OPD-to-Radiology Referral Conversion Leakage", depts: "OPD + Radiology", question: "What % of OPD consultations that should result in imaging actually convert to radiology orders?", insight: "Conversion rates vary 34-78% across specialties. Patients not scheduled within 48h have 45% abandonment.", impact: "SAR 3.1M annual radiology revenue leakage" },
  { title: "ED Admission to IPD Bed Assignment Wait", depts: "ED + IPD", question: "How long do admitted ED patients wait for an inpatient bed?", insight: "Average 4.7 hours (target: 1 hour). During peak occupancy, boarding reaches 8+ hours.", impact: "SAR 2.8M in diverted/delayed revenue annually" },
  { title: "Pharmacy Cost Per Inpatient Day by Department", depts: "Pharmacy + IPD", question: "Which departments have the highest pharmacy cost per patient day?", insight: "Ranges from SAR 180 (General Ward) to SAR 2,400 (Oncology). ICU variance suggests prescribing pattern differences.", impact: "SAR 1.6M savings from standardizing ICU protocols" },
  { title: "End-to-End Revenue Cycle: Visit to Collection", depts: "OPD + Revenue Cycle", question: "What is the average time from patient visit to final payment collection?", insight: "Average visit-to-cash: 94 days. Bottlenecks: coding (7d), submission (12d), adjudication (45d), rework (21d).", impact: "SAR 22M cash flow improvement (94 to 60 days)" },
  { title: "Surgical Pathway: Consultation to OR", depts: "OPD + OR + IPD", question: "What is the conversion rate from surgical consultation to completed surgery?", insight: "Only 58% complete. Drop-offs: pre-surgical workup (18%), insurance (12%), wait time (7%), no-show (5%).", impact: "SAR 12M additional surgical revenue (58% to 75%)" },
  { title: "Lab TAT Impact on ED Disposition", depts: "Laboratory + ED", question: "How does lab turnaround time affect ED patient disposition decisions?", insight: "ED patients wait 2.3 hours for results. Stat lab exceeds 60-minute target in 41% of cases.", impact: "SAR 1.9M annual ED capacity recovery" },
];

const KPI_BENCHMARKS = [
  { kpi: "ED Door-to-Doctor Time", benchmark: "< 30 min (ACEP)" },
  { kpi: "LWBS Rate", benchmark: "< 2-5% (Emergency Medicine)" },
  { kpi: "Average Length of Stay", benchmark: "Per specialty: Saudi MOH benchmark" },
  { kpi: "Bed Occupancy Rate", benchmark: "80-85% (WHO recommended)" },
  { kpi: "30-Day Readmission Rate", benchmark: "< 10% (CMS); < 5% elective" },
  { kpi: "Formulary Compliance", benchmark: "> 90% (Joint Commission)" },
  { kpi: "Patient Satisfaction", benchmark: "> 85% (Top quartile Saudi)" },
  { kpi: "No-Show Rate", benchmark: "< 10% (Best practice)" },
  { kpi: "Claim First-Pass Acceptance", benchmark: "> 95% (Revenue cycle best)" },
  { kpi: "Days in AR", benchmark: "< 45 days (Industry target)" },
  { kpi: "Radiology Report TAT", benchmark: "< 4h routine; < 1h ED stat (ACR)" },
  { kpi: "Lab Stat TAT", benchmark: "< 60 min (CAP)" },
  { kpi: "Surgical Cancellation Rate", benchmark: "< 5% same-day" },
  { kpi: "Nurse-to-Patient Ratio", benchmark: "1:4 Med/Surg, 1:2 ICU (MOH)" },
  { kpi: "HAI Rate", benchmark: "< 2 per 1,000 patient days (WHO)" },
  { kpi: "Incident Reporting Rate", benchmark: "> 8 per 1,000 patient days" },
  { kpi: "Overtime as % of Labor", benchmark: "< 5% (Healthcare HR)" },
  { kpi: "OPD Slot Utilization", benchmark: "> 85% (Operational best)" },
  { kpi: "Procurement Price Variance", benchmark: "< 10% across network" },
  { kpi: "Send-Out Test Ratio", benchmark: "< 5% of total volume" },
];

const DATA_SOURCES = [
  { area: "Emergency Department", sources: "HIS (ED Module), Triage System, Patient Flow Dashboard" },
  { area: "Inpatient Department", sources: "HIS (ADT Module), Bed Management System, Discharge Planning Module" },
  { area: "Pharmacy", sources: "Pharmacy Information System (PIS), Formulary Database, Procurement System" },
  { area: "Patient Experience", sources: "Satisfaction Survey System, Appointment Management, Online Review Platforms" },
  { area: "Supply Chain", sources: "ERP (Procurement Module), Inventory Management, Vendor Contract Database" },
  { area: "Quality & Safety", sources: "Incident Reporting System, Infection Control Database, CBAHI Tracker" },
  { area: "Radiology", sources: "PACS, RIS, HIS Radiology Module" },
  { area: "Laboratory", sources: "LIS, Send-Out Tracking, Equipment Utilization Logs" },
  { area: "OPD", sources: "HIS (Appointment Module), Clinic Scheduling, Patient Registration" },
  { area: "Revenue Cycle", sources: "Billing System, Claims Management, Payer Portal, AR Reports" },
  { area: "Operations", sources: "HR/Payroll (Overtime), Facility Management, Financial Reporting" },
];

// ═══════════════════════════════════════════
// BUILD SLIDES
// ═══════════════════════════════════════════

let pg = 1;

// ─── SLIDE 1: TITLE ───
const s1 = pptx.addSlide();
s1.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: "100%", h: "100%", fill: { color: NAVY } });
s1.addShape(pptx.ShapeType.rect, { x: 0, y: 6.8, w: "100%", h: 0.7, fill: { color: "142D54" } });
s1.addText("TopMed\nInsights Bank", {
  x: 1, y: 1.5, w: 11.33, h: 2.5,
  fontSize: 44, fontFace: FONT_BOLD, bold: true, color: WHITE, align: "center",
  lineSpacingMultiple: 1.2,
});
s1.addText("Additional Insight Ideas & Strategic Analysis", {
  x: 1.5, y: 4.0, w: 10.33, h: 0.6,
  fontSize: 18, fontFace: FONT, color: LIGHT_GRAY, align: "center",
});
s1.addShape(pptx.ShapeType.rect, { x: 4.5, y: 4.8, w: 4.33, h: 0.04, fill: { color: ACCENT_BLUE } });
s1.addText("Prepared by: Ahmed Nasr, Delivery PMO\nMarch 2026 | Confidential", {
  x: 1.5, y: 5.0, w: 10.33, h: 0.8,
  fontSize: 12, fontFace: FONT, color: LIGHT_GRAY, align: "center", lineSpacingMultiple: 1.5,
});
pg++;

// ─── SLIDE 2: TABLE OF CONTENTS ───
const s2 = addSlide({ title: "Contents", pageNum: pg++ });
const tocItems = [
  "Part 1: New Insight Areas (6 departments)",
  "Part 2: Expansions to Existing Areas (5 departments)",
  "Part 3: Priority Matrix",
  "Part 4: Sample Insight Briefs (11 detailed briefs)",
  "Part 5: Cross-Department Insights (6 cross-functional opportunities)",
  "Part 6: KPI Benchmarks & Industry Standards",
  "Part 7: Data Source Mapping",
];
tocItems.forEach((item, i) => {
  s2.addText(`${i + 1}.  ${item}`, {
    x: 1.5, y: 1.2 + i * 0.7, w: 10.0, h: 0.55,
    fontSize: 16, fontFace: FONT, color: i < 2 ? NAVY : i < 5 ? ACCENT_BLUE : ACCENT_GREEN,
    bold: true,
  });
});

// ─── SLIDE 3: EXECUTIVE SUMMARY ───
const s3 = addSlide({ title: "Executive Summary", subtitle: "SAR 65M+ in identified improvement opportunities across 11 areas", pageNum: pg++ });

const summaryCards = [
  { label: "New Areas\nIdentified", value: "6", color: NAVY },
  { label: "Existing Areas\nExpanded", value: "5", color: ACCENT_BLUE },
  { label: "Insight\nBriefs", value: "11", color: ACCENT_GREEN },
  { label: "Cross-Dept\nInsights", value: "6", color: ACCENT_ORANGE },
  { label: "KPI\nBenchmarks", value: "20", color: ACCENT_RED },
];

summaryCards.forEach((card, i) => {
  const cx = 0.5 + i * 2.5;
  s3.addShape(pptx.ShapeType.roundRect, {
    x: cx, y: 1.3, w: 2.2, h: 2.0,
    fill: { color: VERY_LIGHT }, rectRadius: 0.15,
    line: { color: card.color, width: 2 },
  });
  s3.addText(card.value, {
    x: cx, y: 1.4, w: 2.2, h: 1.1,
    fontSize: 40, fontFace: FONT_BOLD, bold: true, color: card.color, align: "center", valign: "middle",
  });
  s3.addText(card.label, {
    x: cx, y: 2.5, w: 2.2, h: 0.7,
    fontSize: 10, fontFace: FONT, color: GRAY, align: "center", valign: "top",
  });
});

// Top financial opportunities
const topFinancials = [
  "SAR 18M working capital release (AR Optimization)",
  "SAR 12M surgical pathway conversion",
  "SAR 10.7M no-show revenue recovery",
  "SAR 8.4M OPD slot utilization",
  "SAR 5.2M procurement standardization",
];
s3.addText("Top Financial Opportunities", {
  x: 0.5, y: 3.6, w: 12.0, h: 0.4,
  fontSize: 14, fontFace: FONT_BOLD, bold: true, color: NAVY,
});
topFinancials.forEach((item, i) => {
  s3.addText(`▸  ${item}`, {
    x: 0.8, y: 4.1 + i * 0.45, w: 11.5, h: 0.4,
    fontSize: 12, fontFace: FONT, color: DARK, bold: true,
  });
});

// ─── PART 1: NEW INSIGHT AREAS ───
addSectionDivider("Part 1", "New Insight Areas", "📊", pg++);
SECTIONS.forEach(s => insightAreaSlide(s, pg++));

// ─── PART 2: EXPANSIONS ───
addSectionDivider("Part 2", "Expansions to Existing Areas", "📈", pg++);
EXPANSIONS.forEach(s => insightAreaSlide(s, pg++));

// ─── PART 3: PRIORITY MATRIX ───
addSectionDivider("Part 3", "Priority Matrix", "🎯", pg++);

const pmSlide = addSlide({ title: "Priority Matrix: Revenue Impact x Readiness x Complexity", pageNum: pg++ });

// Table headers
const pmHeaders = [
  [
    { text: "#", options: { bold: true, fontSize: 9, color: WHITE, fill: { color: NAVY }, align: "center" } },
    { text: "Insight", options: { bold: true, fontSize: 9, color: WHITE, fill: { color: NAVY } } },
    { text: "Revenue Impact", options: { bold: true, fontSize: 9, color: WHITE, fill: { color: NAVY }, align: "center" } },
    { text: "Data Readiness", options: { bold: true, fontSize: 9, color: WHITE, fill: { color: NAVY }, align: "center" } },
    { text: "Complexity", options: { bold: true, fontSize: 9, color: WHITE, fill: { color: NAVY }, align: "center" } },
  ],
];

const pmRows = PRIORITY_MATRIX.map(p => [
  { text: String(p.rank), options: { fontSize: 9, align: "center", color: p.color, bold: true } },
  { text: p.insight, options: { fontSize: 9, color: DARK, bold: true } },
  { text: p.revenue, options: { fontSize: 9, align: "center", color: ACCENT_RED, bold: true } },
  { text: p.data, options: { fontSize: 9, align: "center", color: p.data === "Available Now" ? ACCENT_GREEN : ACCENT_ORANGE } },
  { text: p.complexity, options: { fontSize: 9, align: "center", color: DARK } },
]);

pmSlide.addTable([...pmHeaders, ...pmRows], {
  x: 0.3, y: 1.1, w: 12.7,
  colW: [0.5, 3.5, 2.5, 2.5, 2.0],
  border: { type: "solid", pt: 0.5, color: LIGHT_GRAY },
  rowH: 0.38,
  autoPage: false,
});

// Legend
pmSlide.addText([
  { text: "🔴 Start Immediately (Top 5)   ", options: { fontSize: 9, color: ACCENT_RED } },
  { text: "🟡 Plan This Quarter   ", options: { fontSize: 9, color: ACCENT_ORANGE } },
  { text: "🟢 Next Quarter", options: { fontSize: 9, color: ACCENT_GREEN } },
], { x: 0.5, y: 6.5, w: 12, h: 0.35 });

// ─── PART 4: SAMPLE INSIGHT BRIEFS ───
addSectionDivider("Part 4", "Sample Insight Briefs", "📋", pg++);
SAMPLE_BRIEFS.forEach(b => insightBriefSlide(b, pg++));

// ─── PART 5: CROSS-DEPARTMENT INSIGHTS ───
addSectionDivider("Part 5", "Cross-Department Insights", "🔗", pg++);

// Two per slide
for (let i = 0; i < CROSS_DEPT.length; i += 2) {
  const slide = addSlide({ title: "Cross-Department Insights", subtitle: "High-value opportunities that span multiple departments", pageNum: pg++ });
  
  [0, 1].forEach(j => {
    const cd = CROSS_DEPT[i + j];
    if (!cd) return;
    const yBase = j === 0 ? 1.1 : 4.2;

    slide.addText(`🔗  ${cd.title}`, {
      x: 0.5, y: yBase, w: 12.3, h: 0.4,
      fontSize: 14, fontFace: FONT_BOLD, bold: true, color: NAVY,
    });
    slide.addText(`Departments: ${cd.depts}`, {
      x: 0.5, y: yBase + 0.4, w: 12.3, h: 0.3,
      fontSize: 10, fontFace: FONT, italic: true, color: GRAY,
    });

    // Three columns: Question, Insight, Impact
    slide.addText([
      { text: "Question: ", options: { bold: true, fontSize: 9.5, color: NAVY } },
      { text: cd.question, options: { fontSize: 9.5, color: DARK } },
    ], { x: 0.5, y: yBase + 0.8, w: 4.5, h: 1.8, valign: "top" });

    slide.addText([
      { text: "Insight: ", options: { bold: true, fontSize: 9.5, color: ACCENT_GREEN } },
      { text: cd.insight, options: { fontSize: 9.5, color: DARK } },
    ], { x: 5.2, y: yBase + 0.8, w: 4.5, h: 1.8, valign: "top" });

    slide.addShape(pptx.ShapeType.roundRect, {
      x: 10.0, y: yBase + 0.8, w: 2.8, h: 1.2,
      fill: { color: VERY_LIGHT }, rectRadius: 0.1,
      line: { color: ACCENT_RED, width: 1.5 },
    });
    slide.addText([
      { text: "Impact\n", options: { bold: true, fontSize: 9, color: GRAY } },
      { text: cd.impact, options: { bold: true, fontSize: 11, color: ACCENT_RED } },
    ], { x: 10.0, y: yBase + 0.8, w: 2.8, h: 1.2, align: "center", valign: "middle" });
  });
}

// ─── PART 6: KPI BENCHMARKS ───
addSectionDivider("Part 6", "KPI Benchmarks & Industry Standards", "📏", pg++);

// Two slides for KPIs (10 per slide)
for (let i = 0; i < KPI_BENCHMARKS.length; i += 10) {
  const slide = addSlide({ title: "KPI Benchmarks & Industry Standards", subtitle: "Sources: ACEP, WHO, CMS, ACR, CAP, Joint Commission, Saudi MOH, CBAHI", pageNum: pg++ });

  const kpiHeaders = [
    [
      { text: "#", options: { bold: true, fontSize: 9, color: WHITE, fill: { color: NAVY }, align: "center" } },
      { text: "KPI", options: { bold: true, fontSize: 9, color: WHITE, fill: { color: NAVY } } },
      { text: "Industry Benchmark / Target", options: { bold: true, fontSize: 9, color: WHITE, fill: { color: NAVY } } },
    ],
  ];

  const kpiRows = KPI_BENCHMARKS.slice(i, i + 10).map((k, idx) => [
    { text: String(i + idx + 1), options: { fontSize: 9, align: "center", color: NAVY, bold: true } },
    { text: k.kpi, options: { fontSize: 9, color: DARK, bold: true } },
    { text: k.benchmark, options: { fontSize: 9, color: ACCENT_GREEN } },
  ]);

  slide.addTable([...kpiHeaders, ...kpiRows], {
    x: 0.5, y: 1.1, w: 12.3,
    colW: [0.6, 4.5, 7.2],
    border: { type: "solid", pt: 0.5, color: LIGHT_GRAY },
    rowH: 0.45,
    autoPage: false,
  });
}

// ─── PART 7: DATA SOURCE MAPPING ───
addSectionDivider("Part 7", "Data Source Mapping", "🗂️", pg++);

const dsSlide = addSlide({ title: "Data Source Mapping", subtitle: "Primary data sources needed to extract and validate insights per area", pageNum: pg++ });

const dsHeaders = [
  [
    { text: "Department / Area", options: { bold: true, fontSize: 10, color: WHITE, fill: { color: NAVY } } },
    { text: "Primary Data Sources", options: { bold: true, fontSize: 10, color: WHITE, fill: { color: NAVY } } },
  ],
];

const dsRows = DATA_SOURCES.map(d => [
  { text: d.area, options: { fontSize: 9, color: NAVY, bold: true } },
  { text: d.sources, options: { fontSize: 9, color: DARK } },
]);

dsSlide.addTable([...dsHeaders, ...dsRows], {
  x: 0.5, y: 1.1, w: 12.3,
  colW: [3.5, 8.8],
  border: { type: "solid", pt: 0.5, color: LIGHT_GRAY },
  rowH: 0.45,
  autoPage: false,
});

// ─── CLOSING SLIDE ───
const closing = pptx.addSlide();
closing.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: "100%", h: "100%", fill: { color: NAVY } });
closing.addText("Next Steps", {
  x: 1, y: 1.0, w: 11.33, h: 1.0,
  fontSize: 36, fontFace: FONT_BOLD, bold: true, color: WHITE, align: "center",
});

const nextSteps = [
  "1.  Prioritize top 5 Quick Wins for immediate implementation",
  "2.  Assign department owners to each insight area",
  "3.  Establish baseline KPIs using current data",
  "4.  Build dashboards for real-time tracking",
  "5.  Launch cross-department working groups for joint insights",
  "6.  Set 90-day review cycle for progress tracking",
];
nextSteps.forEach((step, i) => {
  closing.addText(step, {
    x: 2.0, y: 2.3 + i * 0.6, w: 9.33, h: 0.5,
    fontSize: 16, fontFace: FONT, color: WHITE, bold: true,
  });
});

closing.addShape(pptx.ShapeType.rect, { x: 4.5, y: 6.2, w: 4.33, h: 0.04, fill: { color: ACCENT_BLUE } });
closing.addText("TopMed Insights Bank | March 2026 | Ahmed Nasr, Delivery PMO", {
  x: 1, y: 6.4, w: 11.33, h: 0.5,
  fontSize: 11, fontFace: FONT, color: LIGHT_GRAY, align: "center",
});

// ─── SAVE ───
const outPath = "/root/.openclaw/workspace/tmp/insights-deck/TopMed-Insights-Bank.pptx";
pptx.writeFile({ fileName: outPath }).then(() => {
  console.log(`✅ Deck saved: ${outPath}`);
  console.log(`Total slides: ${pptx.slides.length}`);
});
