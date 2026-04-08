#!/usr/bin/env python3
"""
Enhance TopMed Insights Bank Google Doc with all 5 additions:
1. Sample Insight Briefs per area
2. Priority Matrix
3. Cross-Department Insights
4. KPI Benchmarks
5. Data Source Mapping
"""
import json, urllib.request, urllib.parse, os

DOC_ID = "1GKfmRmenfgNNU3najy5ez31xrKBTRIsFguLCLkHqgQA"

def get_access_token():
    with open(os.path.join(os.path.dirname(__file__), '..', 'config', 'ahmed-google.json')) as f:
        creds = json.load(f)
    data = urllib.parse.urlencode({
        'client_id': creds['client_id'],
        'client_secret': creds['client_secret'],
        'refresh_token': creds['refresh_token'],
        'grant_type': 'refresh_token'
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())['access_token']

def api_call(url, data, token):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    })
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def get_doc_length(token):
    req = urllib.request.Request(
        f'https://docs.googleapis.com/v1/documents/{DOC_ID}',
        headers={'Authorization': f'Bearer {token}'}
    )
    resp = urllib.request.urlopen(req)
    doc = json.loads(resp.read())
    content = doc['body']['content']
    return content[-1]['endIndex'] - 1

# ─── Colors ───
NAVY = {"red": 0.15, "green": 0.3, "blue": 0.53}
DARK = {"red": 0.13, "green": 0.13, "blue": 0.13}
GRAY = {"red": 0.5, "green": 0.5, "blue": 0.5}
GREEN = {"red": 0.0, "green": 0.4, "blue": 0.2}
LIGHT_GRAY = {"red": 0.8, "green": 0.8, "blue": 0.8}
RED = {"red": 0.8, "green": 0.1, "blue": 0.1}
ORANGE = {"red": 0.85, "green": 0.5, "blue": 0.0}

class DocBuilder:
    def __init__(self, start_idx):
        self.idx = start_idx
        self.requests = []
        self.styles = []
    
    def add_text(self, text):
        self.requests.append({"insertText": {"location": {"index": self.idx}, "text": text}})
        start = self.idx
        self.idx += len(text)
        return start
    
    def style_heading1(self, start, end):
        self.styles.append({"updateParagraphStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "paragraphStyle": {"namedStyleType": "HEADING_1"},
            "fields": "namedStyleType"
        }})
        self.styles.append({"updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"bold": True, "fontSize": {"magnitude": 16, "unit": "PT"},
                           "foregroundColor": {"color": {"rgbColor": NAVY}}},
            "fields": "bold,fontSize,foregroundColor"
        }})
    
    def style_heading2(self, start, end):
        self.styles.append({"updateParagraphStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "paragraphStyle": {"namedStyleType": "HEADING_2"},
            "fields": "namedStyleType"
        }})
        self.styles.append({"updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"bold": True, "fontSize": {"magnitude": 13, "unit": "PT"},
                           "foregroundColor": {"color": {"rgbColor": NAVY}}},
            "fields": "bold,fontSize,foregroundColor"
        }})
    
    def style_heading3(self, start, end):
        self.styles.append({"updateParagraphStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "paragraphStyle": {"namedStyleType": "HEADING_3"},
            "fields": "namedStyleType"
        }})
        self.styles.append({"updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"bold": True, "fontSize": {"magnitude": 11, "unit": "PT"},
                           "foregroundColor": {"color": {"rgbColor": DARK}}},
            "fields": "bold,fontSize,foregroundColor"
        }})

    def style_bold(self, start, end):
        self.styles.append({"updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"bold": True},
            "fields": "bold"
        }})
    
    def style_bold_color(self, start, end, color):
        self.styles.append({"updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"bold": True, "foregroundColor": {"color": {"rgbColor": color}}},
            "fields": "bold,foregroundColor"
        }})
    
    def style_italic(self, start, end):
        self.styles.append({"updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"italic": True},
            "fields": "italic"
        }})
    
    def style_italic_color(self, start, end, color):
        self.styles.append({"updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"italic": True, "foregroundColor": {"color": {"rgbColor": color}}},
            "fields": "italic,foregroundColor"
        }})
    
    def style_color(self, start, end, color):
        self.styles.append({"updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"foregroundColor": {"color": {"rgbColor": color}}},
            "fields": "foregroundColor"
        }})

    def add_divider(self):
        s = self.add_text("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
        self.style_color(s + 1, s + 53, NAVY)

    def add_thin_divider(self):
        s = self.add_text("\n─────────────────────────────────────────────\n\n")
        self.style_color(s + 1, s + 46, LIGHT_GRAY)

    def add_section_heading(self, text):
        s = self.add_text(f"\n{text}\n\n")
        self.style_heading1(s + 1, s + 1 + len(text))

    def add_sub_heading(self, text):
        s = self.add_text(f"{text}\n\n")
        self.style_heading2(s, s + len(text))

    def add_brief_field(self, label, value):
        """Add a labeled field like 'Observation: some text'"""
        full = f"{label}: {value}\n"
        s = self.add_text(full)
        self.style_bold_color(s, s + len(label) + 1, NAVY)

    def get_all_requests(self):
        return self.requests + self.styles


# ─── SAMPLE INSIGHT BRIEFS ───

SAMPLE_BRIEFS = [
    {
        "area": "Emergency Department",
        "icon": "🚨",
        "title": "Left Without Being Seen (LWBS) Rate and Revenue Impact",
        "department": "Emergency Department",
        "confidence": "High",
        "observation": "LWBS rate increased from 3.2% to 5.8% over the past two quarters, with the highest walkout rates occurring between 6:00 PM and 10:00 PM.",
        "evidence": "Average door-to-doctor time exceeds 45 minutes during evening peak hours. Patient walkout incidents correlate with triage nurse shift changeover gaps (5:30-6:30 PM). Weekend LWBS rates are 40% higher than weekdays.",
        "root_cause": "Insufficient triage staffing during evening shift changeover window, combined with no fast-track pathway for low-acuity patients (ESI Level 4-5) who represent 35% of evening volume.",
        "impact": "Estimated annual revenue loss of SAR 2.1 Million from walkout patients. Additional risk of negative online reviews and patient diversion to competing facilities.",
        "actions": "Implement triage overlap shift (5:00-7:00 PM) to eliminate coverage gap. Create fast-track pathway for low-acuity patients. Install real-time wait time display in waiting area. Set up automated SMS notification when patient is next.",
        "strategic": "Reducing LWBS by 50% directly impacts both revenue recovery (SAR 1.05M) and patient satisfaction scores, which are increasingly tied to insurance network inclusion criteria in KSA."
    },
    {
        "area": "Inpatient Department",
        "icon": "🏥",
        "title": "Delayed Discharge and Bed Turnover Impact",
        "department": "Inpatient Department (All Wards)",
        "confidence": "High",
        "observation": "Average time from physician discharge order to actual patient departure is 6.2 hours, against a target of 2 hours. This creates a daily average of 12 blocked beds across the network.",
        "evidence": "Discharge orders peak at 11:00 AM but actual departures peak at 5:00 PM. Pharmacy medication reconciliation averages 2.1 hours. Insurance pre-authorization for follow-up appointments adds 1.5 hours. Transport coordination delays average 45 minutes.",
        "root_cause": "Sequential discharge process (physician order, then pharmacy, then insurance, then transport) instead of parallel processing. No discharge planning initiated at admission. Lack of discharge lounge for patients cleared but awaiting transport.",
        "impact": "12 blocked beds daily across the network translates to approximately SAR 4.3 Million in annual lost admission revenue. ED boarding times increase by 2.3 hours when IPD beds are blocked.",
        "actions": "Implement parallel discharge processing (pharmacy + insurance + transport initiated simultaneously). Begin discharge planning at Day 1 of admission. Create discharge lounge to free beds immediately after clearance. Set discharge time targets by ward with daily tracking.",
        "strategic": "Bed turnover directly impacts the hospital's capacity to admit new patients. A 50% improvement in discharge time would free 6 beds daily, equivalent to adding a new ward without capital expenditure."
    },
    {
        "area": "Pharmacy",
        "icon": "💊",
        "title": "High-Cost Medication Substitution Opportunities",
        "department": "Pharmacy Department",
        "confidence": "Medium",
        "observation": "Analysis of the top 50 medications by spend reveals that 18 branded drugs have therapeutically equivalent generic or biosimilar alternatives available in the Saudi market, representing 31% of total pharmacy expenditure.",
        "evidence": "Monthly spend on substitutable branded medications averages SAR 420,000 across the network. Generic alternatives for these 18 medications are 40-75% cheaper. Three hospitals in the network already use generics for 8 of these medications with no reported efficacy differences.",
        "root_cause": "No standardized formulary review cycle across the network. Physician prescribing habits favor familiar branded products. Pharmacy and Therapeutics (P&T) committee meets quarterly but lacks cost-effectiveness analysis in its review criteria.",
        "impact": "Potential annual savings of SAR 2.5-3.8 Million from generic/biosimilar substitution across the network, with no compromise in clinical outcomes based on internal evidence from hospitals already using alternatives.",
        "actions": "Conduct formulary review for top 50 drugs by spend with cost-effectiveness analysis. Present substitution recommendations to P&T committee with internal clinical evidence. Implement therapeutic interchange protocols with physician education. Track substitution rate monthly.",
        "strategic": "Pharmacy cost optimization is a high-impact, low-risk initiative that delivers immediate P&L improvement. Positions TopMed as a value-driven healthcare network aligned with Saudi Vision 2030 healthcare cost efficiency goals."
    },
    {
        "area": "Patient Experience",
        "icon": "⭐",
        "title": "Patient No-Show Patterns and Financial Impact",
        "department": "Outpatient Services (All Specialties)",
        "confidence": "High",
        "observation": "Average OPD no-show rate across the network is 22%, with certain specialties (Dermatology 31%, Ophthalmology 28%) significantly higher. No-show rates are 3x higher for appointments booked more than 14 days in advance.",
        "evidence": "Monthly revenue impact of no-shows estimated at SAR 890,000 in unbilled consultations. Clinics with SMS reminders (48h + 2h) show 35% lower no-show rates than those without. Saturday morning slots have the highest no-show rate (34%).",
        "root_cause": "Inconsistent appointment reminder systems across hospitals. No penalty or rebooking friction for repeat no-shows. Overbooking algorithms not calibrated to specialty-specific no-show rates. Long booking horizons for follow-ups increase abandonment.",
        "impact": "Estimated annual revenue loss of SAR 10.7 Million from no-show appointments across the network. Additional hidden cost in physician idle time and wasted clinic preparation.",
        "actions": "Implement dual SMS reminder system (48 hours + 2 hours before appointment) across all hospitals. Deploy specialty-specific overbooking ratios based on historical no-show data. Introduce waitlist backfill for same-day cancellations. Flag repeat no-show patients for proactive outreach.",
        "strategic": "A 30% reduction in no-shows would recover SAR 3.2M annually while improving physician utilization and patient access. This is one of the highest-ROI operational improvements available."
    },
    {
        "area": "Supply Chain & Procurement",
        "icon": "📦",
        "title": "Cross-Hospital Procurement Price Variance",
        "department": "Procurement / Supply Chain",
        "confidence": "High",
        "observation": "Price comparison analysis across 15 hospitals reveals that identical medical consumables are being procured at prices varying by 15-42% between facilities, with surgical gloves, IV sets, and wound care products showing the widest variance.",
        "evidence": "Top 20 consumables by volume show average price variance of 28% across the network. Three hospitals consistently pay above-network-average prices (15-20% premium). Vendor contracts have different renewal dates and terms across facilities.",
        "root_cause": "Decentralized procurement without network-wide price benchmarking. Individual hospitals negotiate independently with overlapping vendor bases. No centralized contract management system. Historical pricing accepted without competitive rebidding.",
        "impact": "Estimated annual savings opportunity of SAR 5.2 Million by standardizing procurement prices to the best-available network rate for the top 100 consumables.",
        "actions": "Establish centralized procurement dashboard showing real-time price benchmarks across all hospitals. Consolidate vendor contracts for top 100 consumables into network-wide agreements. Implement mandatory competitive bidding for contracts above SAR 100,000. Create quarterly price variance report for hospital administrators.",
        "strategic": "Centralized procurement is a foundational capability for any multi-hospital network. This initiative delivers immediate cost savings while building the infrastructure for ongoing supply chain optimization."
    },
    {
        "area": "Quality & Clinical Safety",
        "icon": "🛡️",
        "title": "Incident Reporting Culture and Near-Miss Trends",
        "department": "Quality Management / Patient Safety",
        "confidence": "Medium",
        "observation": "Near-miss reporting rates vary 5x across hospitals in the network (highest: 12.4 per 1,000 patient days; lowest: 2.3 per 1,000 patient days). Low-reporting hospitals do not have fewer incidents; they have weaker reporting culture.",
        "evidence": "Hospitals with dedicated quality champions report 3.2x more near-misses. Medication-related near-misses account for 45% of all reports. Reporting rates dropped 18% in the quarter following a punitive response to a reported incident at one facility.",
        "root_cause": "Inconsistent just-culture implementation across the network. Some hospitals still associate incident reporting with blame. Anonymous reporting channels not available at all facilities. No positive feedback loop (reporters don't see outcomes).",
        "impact": "Under-reporting masks safety risks. Healthcare literature shows each reported near-miss prevents an average of 300 unsafe conditions. Low-reporting hospitals carry unquantified patient safety liability.",
        "actions": "Standardize just-culture training across all hospitals with annual refresher. Implement anonymous digital reporting channel network-wide. Create monthly 'Safety Spotlight' recognizing departments with highest reporting rates. Share anonymized near-miss learnings across the network quarterly.",
        "strategic": "Near-miss reporting is a leading indicator of safety culture. Improving reporting rates is a prerequisite for CBAHI accreditation excellence and positions TopMed as a safety leader in the Saudi market."
    },
    {
        "area": "Radiology (Expansion)",
        "icon": "🩻",
        "title": "Radiology Report Turnaround Time by Modality",
        "department": "Radiology Department",
        "confidence": "High",
        "observation": "Average radiology report turnaround time (TAT) varies significantly by modality: X-ray 2.1 hours, Ultrasound 4.3 hours, CT 6.8 hours, MRI 11.2 hours. CT and MRI TAT exceed the 4-hour target in 67% of cases.",
        "evidence": "ED-ordered CT reports average 8.4 hours vs. 5.2 hours for scheduled outpatient CTs. Weekend TAT is 2.3x longer than weekday. Three radiologists handle 60% of MRI reads, creating a bottleneck.",
        "root_cause": "Uneven radiologist workload distribution. No priority queue for ED-ordered studies. Weekend and overnight coverage relies on on-call rather than active staffing. PACS worklist not optimized for urgency-based sorting.",
        "impact": "Delayed radiology reports extend ED disposition time by 2-4 hours and delay inpatient treatment decisions. Estimated impact on bed turnover: SAR 1.8M annually from delayed discharges waiting on imaging results.",
        "actions": "Implement priority-based PACS worklist (ED stat, inpatient urgent, outpatient routine). Redistribute MRI reading load across radiologist panel. Add active evening radiologist shift (4 PM-midnight) for CT/MRI reads. Track TAT by modality with daily dashboard.",
        "strategic": "Radiology TAT directly impacts ED throughput, inpatient length of stay, and physician satisfaction. Meeting the 4-hour target positions TopMed competitively in the Saudi market where fast diagnostics are a differentiator."
    },
    {
        "area": "Laboratory (Expansion)",
        "icon": "🔬",
        "title": "In-House vs. Send-Out Test Migration Opportunity",
        "department": "Laboratory Department",
        "confidence": "Medium",
        "observation": "Send-out test volume has grown 24% year-over-year while in-house test volume grew only 8%. Analysis reveals that 12 high-volume send-out tests could be performed in-house with existing or minimal additional equipment.",
        "evidence": "Monthly send-out spend averages SAR 340,000. The top 12 send-out tests by volume represent 55% of total send-out costs. In-house cost per test for these 12 tests would be 40-65% lower. Average TAT for send-out tests is 5-7 days vs. same-day for in-house.",
        "root_cause": "No regular review of send-out test menu against in-house capabilities. Equipment procurement for new test capabilities requires lengthy approval. Lab staff training for new assays not prioritized. Some tests sent out historically when volumes were too low, but volumes have since grown.",
        "impact": "Migrating top 12 send-out tests in-house would save approximately SAR 1.4 Million annually while reducing TAT from 5-7 days to same-day, improving clinical decision-making speed.",
        "actions": "Conduct feasibility study for top 12 send-out tests: equipment needs, reagent costs, staff training, volume thresholds. Build business case with ROI timeline for each test. Prioritize migration by volume and margin impact. Set quarterly migration targets.",
        "strategic": "In-house testing capability expansion aligns with TopMed's strategy to be a full-service healthcare provider. Faster turnaround improves patient outcomes and reduces repeat visits for result collection."
    },
    {
        "area": "OPD (Expansion)",
        "icon": "🩺",
        "title": "Doctor Productivity and Clinic Slot Utilization",
        "department": "Outpatient Department",
        "confidence": "High",
        "observation": "Doctor productivity varies significantly: top quartile physicians see 5.8 patients per clinic hour while bottom quartile sees 2.1 patients. Clinic slot utilization averages 71% network-wide, meaning 29% of available appointment slots go unfilled.",
        "evidence": "Specialties with standardized consultation templates show 22% higher throughput. Clinics starting 15+ minutes late lose an average of 1.5 appointment slots per session. Double-booking rates vary from 5% to 35% across physicians.",
        "root_cause": "No standardized consultation time targets by visit type (new vs. follow-up). Clinic start time adherence not monitored. Patient flow bottlenecks at registration and vitals collection. Some physicians block slots for walk-ins that never materialize.",
        "impact": "Improving slot utilization from 71% to 85% would generate an estimated SAR 8.4 Million in additional annual OPD revenue across the network without adding any new clinic hours or physicians.",
        "actions": "Implement visit-type-based slot duration (new: 20 min, follow-up: 10 min, procedure: 30 min). Track clinic start time adherence with automated alerts. Deploy pre-visit registration (online/kiosk) to reduce in-clinic wait. Release unconfirmed slots to waitlist 24 hours before appointment.",
        "strategic": "OPD is the front door of the hospital. Maximizing physician productivity and slot utilization is the highest-leverage revenue growth initiative available without capital expenditure."
    },
    {
        "area": "Revenue Cycle (Expansion)",
        "icon": "💰",
        "title": "Accounts Receivable Aging by Payer Category",
        "department": "Revenue Cycle Management / Finance",
        "confidence": "High",
        "observation": "Average days in accounts receivable (AR) is 78 days network-wide, against a target of 45 days. Government payers average 112 days, insurance companies 64 days, and self-pay 43 days. AR >90 days represents 34% of total outstanding receivables.",
        "evidence": "Claim first-pass acceptance rate is 71% (target: 95%). Rejected claims take an average of 28 days for resubmission. Three government payer contracts have no late-payment penalties. Monthly write-off for uncollectable AR >180 days averages SAR 280,000.",
        "root_cause": "High claim rejection rate due to coding errors and incomplete documentation. No dedicated follow-up team for aging government claims. Lack of automated claim status tracking. Payment terms not enforced for key payer contracts.",
        "impact": "Reducing average AR days from 78 to 55 would release approximately SAR 18 Million in working capital across the network. Improving first-pass acceptance to 90% would reduce resubmission costs by SAR 1.2M annually.",
        "actions": "Deploy automated claim scrubbing before submission (coding validation, documentation completeness). Create dedicated AR follow-up team for claims >60 days. Renegotiate government payer contracts to include late-payment terms. Implement weekly AR aging dashboard by payer with escalation triggers.",
        "strategic": "Cash flow is the lifeblood of multi-hospital operations. AR optimization is the single highest-impact financial initiative, freeing capital for investment while reducing bad debt exposure."
    },
    {
        "area": "Operational Efficiency (Expansion)",
        "icon": "⚙️",
        "title": "Overtime Cost vs. Patient Volume Correlation",
        "department": "Operations / HR",
        "confidence": "High",
        "observation": "Overtime spending increased 31% year-over-year while patient volume grew only 12%. The overtime-to-volume ratio suggests structural overstaffing in some areas and understaffing in others, rather than genuine demand-driven overtime.",
        "evidence": "Nursing overtime accounts for 68% of total overtime spend. Three departments (ED, ICU, OR) consume 52% of all overtime hours. Weekend overtime is 2.8x higher than weekday. Some departments show consistent overtime despite below-capacity patient volumes.",
        "root_cause": "Staffing models not updated to reflect current patient volume patterns. Shift scheduling based on historical patterns rather than demand forecasting. Overtime approval process is informal in some departments. No visibility into overtime trends at department level until monthly payroll.",
        "impact": "Estimated SAR 3.6 Million in reducible overtime annually by aligning staffing models to actual patient volume patterns. Additional benefit: reduced nurse burnout and turnover costs.",
        "actions": "Build demand-based staffing model using 12-month patient volume data by department, day of week, and shift. Implement real-time overtime tracking dashboard with department-level alerts at 80% of monthly budget. Require formal overtime pre-approval for non-emergency situations. Review and adjust shift patterns quarterly.",
        "strategic": "Workforce cost is the largest operating expense in any hospital. Data-driven staffing optimization delivers immediate P&L improvement while improving employee satisfaction through more predictable scheduling."
    },
]

# ─── PRIORITY MATRIX ───

PRIORITY_MATRIX = [
    # (Insight, Revenue Impact, Data Readiness, Complexity)
    ("AR Aging by Payer Category", "HIGH (SAR 18M working capital)", "Available Now", "Medium Effort"),
    ("OPD Slot Utilization", "HIGH (SAR 8.4M revenue)", "Available Now", "Quick Win"),
    ("Cross-Hospital Procurement Price Variance", "HIGH (SAR 5.2M savings)", "Available Now", "Medium Effort"),
    ("Delayed Discharge / Bed Turnover", "HIGH (SAR 4.3M revenue)", "Available Now", "Medium Effort"),
    ("Patient No-Show Patterns", "HIGH (SAR 10.7M revenue loss)", "Available Now", "Quick Win"),
    ("Medication Substitution Opportunities", "HIGH (SAR 2.5-3.8M savings)", "Needs Collection", "Medium Effort"),
    ("ED LWBS Rate and Revenue Impact", "MEDIUM (SAR 2.1M revenue)", "Available Now", "Quick Win"),
    ("Overtime vs. Patient Volume", "MEDIUM (SAR 3.6M savings)", "Available Now", "Medium Effort"),
    ("Radiology Report TAT by Modality", "MEDIUM (SAR 1.8M indirect)", "Available Now", "Quick Win"),
    ("Send-Out Test Migration", "MEDIUM (SAR 1.4M savings)", "Needs Collection", "Major Initiative"),
    ("Near-Miss Reporting Culture", "LOW (risk mitigation)", "Needs Collection", "Major Initiative"),
    ("Digital Reputation vs Quality Gap", "LOW (brand value)", "Needs System Integration", "Medium Effort"),
]

# ─── CROSS-DEPARTMENT INSIGHTS ───

CROSS_DEPT = [
    {
        "title": "OPD-to-Radiology Referral Conversion Leakage",
        "departments": "OPD + Radiology",
        "question": "What percentage of OPD consultations that should result in diagnostic imaging actually convert to radiology orders, and where are patients dropping off?",
        "insight": "Referral conversion rates vary from 34% to 78% across specialties. Orthopedics and Neurology show the highest leakage. Patients referred for imaging but not scheduled within 48 hours have a 45% abandonment rate.",
        "impact": "Estimated SAR 3.1M in annual radiology revenue leakage from unconverted OPD referrals.",
    },
    {
        "title": "ED Admission to IPD Bed Assignment Wait Time",
        "departments": "Emergency Department + Inpatient Department",
        "question": "How long do admitted ED patients wait for an inpatient bed, and what is the revenue and clinical impact of ED boarding?",
        "insight": "Average ED-to-bed time is 4.7 hours (target: 1 hour). During peak occupancy, ED boarding reaches 8+ hours. Boarded patients consume ED nursing resources at 2.3x the rate of standard ED patients.",
        "impact": "ED boarding reduces ED capacity by an estimated 15%, translating to SAR 2.8M in diverted or delayed revenue annually.",
    },
    {
        "title": "Pharmacy Cost Per Inpatient Day by Department",
        "departments": "Pharmacy + Inpatient Department",
        "question": "Which departments have the highest pharmacy cost per patient day, and are there outlier prescribing patterns driving cost inflation?",
        "insight": "Pharmacy cost per inpatient day ranges from SAR 180 (General Ward) to SAR 2,400 (Oncology). ICU pharmacy cost variance between hospitals suggests prescribing pattern differences rather than case-mix differences.",
        "impact": "Standardizing ICU prescribing protocols to the network best practice could save SAR 1.6M annually.",
    },
    {
        "title": "End-to-End Revenue Cycle: Visit to Collection",
        "departments": "OPD + Revenue Cycle + Insurance",
        "question": "What is the average time from patient visit to final payment collection, and where are the bottlenecks in the revenue realization chain?",
        "insight": "Average visit-to-cash cycle is 94 days. Major bottlenecks: coding completion (7 days), claim submission (12 days), payer adjudication (45 days), denial rework (21 days). Self-pay collection at point-of-service captures only 62% of expected revenue.",
        "impact": "Reducing visit-to-cash from 94 to 60 days would improve annual cash flow by approximately SAR 22M across the network.",
    },
    {
        "title": "Surgical Pathway: OPD Consultation to OR Utilization",
        "departments": "OPD + Operating Room + IPD",
        "question": "What is the conversion rate from surgical consultation to completed surgery, and what are the drop-off points in the surgical patient pathway?",
        "insight": "Only 58% of patients recommended for elective surgery actually complete the procedure. Drop-off points: 18% at pre-surgical workup, 12% at insurance pre-authorization, 7% at scheduling (wait time >3 weeks), 5% no-show on surgery day.",
        "impact": "Improving surgical conversion from 58% to 75% would generate an estimated SAR 12M in additional surgical revenue annually.",
    },
    {
        "title": "Laboratory TAT Impact on ED Disposition Time",
        "departments": "Laboratory + Emergency Department",
        "question": "How does laboratory result turnaround time affect ED patient disposition decisions, and what is the cost of delayed lab results?",
        "insight": "ED patients requiring lab work wait an average of 2.3 hours for results. Stat lab TAT exceeds 60-minute target in 41% of cases. Each 30-minute lab delay adds approximately 45 minutes to total ED length of stay.",
        "impact": "Meeting the 60-minute stat lab target would reduce average ED LOS by 1.1 hours, improving throughput and recovering an estimated SAR 1.9M in annual ED capacity.",
    },
]

# ─── KPI BENCHMARKS ───

KPI_BENCHMARKS = [
    ("ED Door-to-Doctor Time", "< 30 minutes (ACEP standard)"),
    ("LWBS Rate", "< 2-5% (Emergency Medicine benchmark)"),
    ("Average Length of Stay (ALOS)", "Per specialty: Saudi MOH benchmark; General: 4-5 days"),
    ("Bed Occupancy Rate", "80-85% (WHO recommended optimal range)"),
    ("30-Day Readmission Rate", "< 10% (CMS benchmark); < 5% for elective procedures"),
    ("Pharmacy Formulary Compliance", "> 90% (Joint Commission standard)"),
    ("Patient Satisfaction Score", "> 85% (Top quartile Saudi hospitals)"),
    ("No-Show Rate", "< 10% (Best practice); Industry average: 15-20%"),
    ("Claim First-Pass Acceptance", "> 95% (Revenue cycle best practice)"),
    ("Days in Accounts Receivable", "< 45 days (Industry target); Saudi average: 60-80 days"),
    ("Radiology Report TAT", "< 4 hours routine; < 1 hour ED stat (ACR guideline)"),
    ("Lab Stat TAT", "< 60 minutes (CAP recommendation)"),
    ("Surgical Cancellation Rate", "< 5% same-day (Best practice)"),
    ("Nurse-to-Patient Ratio", "1:4 Med/Surg, 1:2 ICU, 1:1 Critical (Saudi MOH)"),
    ("Hospital-Acquired Infection Rate", "< 2 per 1,000 patient days (WHO target)"),
    ("Incident Reporting Rate", "> 8 per 1,000 patient days (High-reliability benchmark)"),
    ("Overtime as % of Total Labor", "< 5% (Healthcare HR benchmark)"),
    ("OPD Slot Utilization", "> 85% (Operational best practice)"),
    ("Procurement Price Variance", "< 10% across network (Supply chain benchmark)"),
    ("Send-Out Test Ratio", "< 5% of total test volume (Lab efficiency benchmark)"),
]

# ─── DATA SOURCE MAPPING ───

DATA_SOURCES = [
    ("Emergency Department", "HIS (ED Module), Triage System, Patient Flow Dashboard"),
    ("Inpatient Department", "HIS (ADT Module), Bed Management System, Discharge Planning Module"),
    ("Pharmacy", "Pharmacy Information System (PIS), Formulary Database, Procurement System"),
    ("Patient Experience", "Patient Satisfaction Survey System, Appointment Management System, Online Review Platforms"),
    ("Supply Chain & Procurement", "ERP (Procurement Module), Inventory Management System, Vendor Contract Database"),
    ("Quality & Clinical Safety", "Incident Reporting System, Infection Control Database, CBAHI Compliance Tracker"),
    ("Radiology", "PACS, RIS (Radiology Information System), HIS Radiology Module"),
    ("Laboratory", "LIS (Laboratory Information System), Send-Out Tracking, Equipment Utilization Logs"),
    ("OPD", "HIS (Appointment Module), Clinic Scheduling System, Patient Registration System"),
    ("Revenue Cycle", "Billing System, Claims Management Platform, Payer Portal, AR Aging Reports"),
    ("Operational Efficiency", "HR/Payroll System (Overtime Tracking), Facility Management System, Financial Reporting"),
]


def main():
    token = get_access_token()
    end_idx = get_doc_length(token)
    print(f"Current doc length: {end_idx}")
    
    b = DocBuilder(end_idx)
    
    # ═══════════════════════════════════════════
    # SECTION 3: PRIORITY MATRIX
    # ═══════════════════════════════════════════
    b.add_divider()
    b.add_section_heading("PART 3: PRIORITY MATRIX")
    
    intro = "The following matrix ranks all insight ideas by revenue impact, data readiness, and implementation complexity to help hospital managers identify where to start.\n\n"
    s = b.add_text(intro)
    b.style_italic(s, s + len(intro) - 2)
    
    # Header row
    header = "Rank | Insight | Revenue Impact | Data Readiness | Complexity\n"
    s = b.add_text(header)
    b.style_bold_color(s, s + len(header) - 1, NAVY)
    
    for i, (insight, revenue, data, complexity) in enumerate(PRIORITY_MATRIX, 1):
        # Color code by rank
        rank_icon = "🔴" if i <= 5 else "🟡" if i <= 9 else "🟢"
        line = f"{rank_icon}  {i}. {insight}  |  {revenue}  |  {data}  |  {complexity}\n"
        s = b.add_text(line)
        # Bold the insight name
        name_start = s + len(f"{rank_icon}  {i}. ")
        b.style_bold(name_start, name_start + len(insight))
    
    legend = "\n🔴 = Top Priority (Start Immediately)   🟡 = High Value (Plan This Quarter)   🟢 = Monitor (Next Quarter)\n"
    s = b.add_text(legend)
    b.style_italic_color(s, s + len(legend) - 1, GRAY)

    # ═══════════════════════════════════════════
    # SECTION 4: SAMPLE INSIGHT BRIEFS
    # ═══════════════════════════════════════════
    b.add_divider()
    b.add_section_heading("PART 4: SAMPLE INSIGHT BRIEFS")
    
    intro2 = "Each brief follows the TopMed Insight Brief standard format (8-point structure). One sample per area demonstrates how raw data translates into actionable executive recommendations.\n\n"
    s = b.add_text(intro2)
    b.style_italic(s, s + len(intro2) - 2)
    
    for brief in SAMPLE_BRIEFS:
        # Brief heading
        heading = f"{brief['icon']}  Sample Brief: {brief['title']}\n\n"
        s = b.add_text(heading)
        b.style_heading2(s, s + len(heading) - 2)
        
        # Confidence tag
        conf = f"Confidence Level: {brief['confidence']}\n"
        s = b.add_text(conf)
        conf_color = GREEN if brief['confidence'] == 'High' else ORANGE
        b.style_bold_color(s, s + len("Confidence Level:"), NAVY)
        b.style_bold_color(s + len("Confidence Level: "), s + len(conf) - 1, conf_color)
        
        # Department
        b.add_brief_field("Relevant Department", brief['department'])
        
        # Fields
        b.add_brief_field("Observation (What Data Tell Us)", brief['observation'])
        b.add_brief_field("Supporting Evidence", brief['evidence'])
        b.add_brief_field("Root Cause Analysis", brief['root_cause'])
        b.add_brief_field("Business Impact (Financial)", brief['impact'])
        b.add_brief_field("Recommended Actions", brief['actions'])
        b.add_brief_field("Strategic Importance", brief['strategic'])
        
        b.add_thin_divider()

    # ═══════════════════════════════════════════
    # SECTION 5: CROSS-DEPARTMENT INSIGHTS
    # ═══════════════════════════════════════════
    b.add_divider()
    b.add_section_heading("PART 5: CROSS-DEPARTMENT INSIGHTS")
    
    intro3 = "The highest-value insights often span multiple departments. These cross-functional opportunities are typically missed because no single department owns them.\n\n"
    s = b.add_text(intro3)
    b.style_italic(s, s + len(intro3) - 2)
    
    for cd in CROSS_DEPT:
        heading = f"🔗  {cd['title']}\n"
        s = b.add_text(heading)
        b.style_heading3(s, s + len(heading) - 1)
        
        dept_line = f"Departments: {cd['departments']}\n"
        s = b.add_text(dept_line)
        b.style_bold_color(s, s + len("Departments:"), NAVY)
        
        b.add_brief_field("Analytical Question", cd['question'])
        b.add_brief_field("Insight", cd['insight'])
        b.add_brief_field("Estimated Impact", cd['impact'])
        
        b.add_thin_divider()

    # ═══════════════════════════════════════════
    # SECTION 6: KPI BENCHMARKS
    # ═══════════════════════════════════════════
    b.add_divider()
    b.add_section_heading("PART 6: KPI BENCHMARKS & INDUSTRY STANDARDS")
    
    intro4 = "Reference benchmarks for each insight area. Use these targets when setting improvement goals and measuring progress.\n\n"
    s = b.add_text(intro4)
    b.style_italic(s, s + len(intro4) - 2)
    
    for kpi, benchmark in KPI_BENCHMARKS:
        line = f"  ▸  {kpi}:  {benchmark}\n"
        s = b.add_text(line)
        b.style_bold(s + 5, s + 5 + len(kpi))
        b.style_color(s + 5 + len(kpi) + 3, s + len(line) - 1, GREEN)
    
    source_note = "\nSources: ACEP, WHO, CMS, ACR, CAP, Joint Commission, Saudi MOH, CBAHI, Revenue Cycle Best Practices\n"
    s = b.add_text(source_note)
    b.style_italic_color(s, s + len(source_note) - 1, GRAY)

    # ═══════════════════════════════════════════
    # SECTION 7: DATA SOURCE MAPPING
    # ═══════════════════════════════════════════
    b.add_divider()
    b.add_section_heading("PART 7: DATA SOURCE MAPPING")
    
    intro5 = "For each insight area, the primary data sources needed to extract and validate insights. This eliminates the 'we don't know where to find this data' barrier.\n\n"
    s = b.add_text(intro5)
    b.style_italic(s, s + len(intro5) - 2)
    
    for area, sources in DATA_SOURCES:
        line = f"  {area}\n"
        s = b.add_text(line)
        b.style_bold_color(s + 2, s + 2 + len(area), NAVY)
        
        src_line = f"      Primary Sources: {sources}\n\n"
        s = b.add_text(src_line)
        b.style_bold(s + 6, s + 6 + len("Primary Sources:"))

    # ─── FOOTER ───
    b.add_divider()
    footer = "End of Additional Insight Ideas | TopMed Insights Bank | March 2026\n"
    s = b.add_text(footer)
    b.style_italic_color(s, s + len(footer) - 1, GRAY)
    b.styles.append({"updateParagraphStyle": {
        "range": {"startIndex": s, "endIndex": s + len(footer)},
        "paragraphStyle": {"alignment": "CENTER"},
        "fields": "alignment"
    }})

    # ─── SEND ALL REQUESTS ───
    all_reqs = b.get_all_requests()
    print(f"Total requests: {len(all_reqs)}")
    
    batch_size = 80
    for i in range(0, len(all_reqs), batch_size):
        batch = all_reqs[i:i+batch_size]
        api_call(f'https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate',
                 {"requests": batch}, token)
        print(f"  Batch {i//batch_size + 1}: {len(batch)} requests applied")
    
    print(f"\n✅ All enhancements added to: https://docs.google.com/document/d/{DOC_ID}/edit")

if __name__ == '__main__':
    main()
