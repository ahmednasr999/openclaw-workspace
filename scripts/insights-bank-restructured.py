#!/usr/bin/env python3
"""
TopMed Insights Bank - Restructured by Department
Each section is self-contained: questions, insights, brief, KPIs, data sources.
"""
import json, urllib.request, urllib.parse, os

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

# ─── Colors ───
NAVY = {"red": 0.15, "green": 0.3, "blue": 0.53}
DARK = {"red": 0.13, "green": 0.13, "blue": 0.13}
GRAY = {"red": 0.5, "green": 0.5, "blue": 0.5}
GREEN = {"red": 0.0, "green": 0.4, "blue": 0.2}
LIGHT_GRAY = {"red": 0.8, "green": 0.8, "blue": 0.8}
RED = {"red": 0.75, "green": 0.15, "blue": 0.15}
ORANGE = {"red": 0.83, "green": 0.5, "blue": 0.0}
BLUE = {"red": 0.18, "green": 0.46, "blue": 0.71}

class DocBuilder:
    def __init__(self):
        self.idx = 1
        self.requests = []
        self.styles = []

    def text(self, t):
        self.requests.append({"insertText": {"location": {"index": self.idx}, "text": t}})
        s = self.idx
        self.idx += len(t)
        return s

    def h1(self, t):
        full = f"{t}\n"
        s = self.text(full)
        self.styles.append({"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": s + len(t)}, "paragraphStyle": {"namedStyleType": "HEADING_1"}, "fields": "namedStyleType"}})
        self.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(t)}, "textStyle": {"bold": True, "fontSize": {"magnitude": 18, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": NAVY}}}, "fields": "bold,fontSize,foregroundColor"}})
        self.text("\n")

    def h2(self, t):
        full = f"{t}\n"
        s = self.text(full)
        self.styles.append({"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": s + len(t)}, "paragraphStyle": {"namedStyleType": "HEADING_2"}, "fields": "namedStyleType"}})
        self.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(t)}, "textStyle": {"bold": True, "fontSize": {"magnitude": 14, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": NAVY}}}, "fields": "bold,fontSize,foregroundColor"}})
        self.text("\n")

    def h3(self, t):
        full = f"{t}\n"
        s = self.text(full)
        self.styles.append({"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": s + len(t)}, "paragraphStyle": {"namedStyleType": "HEADING_3"}, "fields": "namedStyleType"}})
        self.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(t)}, "textStyle": {"bold": True, "fontSize": {"magnitude": 12, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": BLUE}}}, "fields": "bold,fontSize,foregroundColor"}})

    def field(self, label, value, label_color=NAVY):
        full = f"{label}: {value}\n"
        s = self.text(full)
        self.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(label) + 1}, "textStyle": {"bold": True, "foregroundColor": {"color": {"rgbColor": label_color}}}, "fields": "bold,foregroundColor"}})

    def bullet(self, t, bold=False):
        full = f"  ▸  {t}\n"
        s = self.text(full)
        if bold:
            self.styles.append({"updateTextStyle": {"range": {"startIndex": s + 5, "endIndex": s + len(full) - 1}, "textStyle": {"bold": True}, "fields": "bold"}})

    def numbered(self, i, t):
        num = f"  {i}."
        full = f"{num}  {t}\n"
        s = self.text(full)
        self.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(num)}, "textStyle": {"bold": True, "foregroundColor": {"color": {"rgbColor": NAVY}}}, "fields": "bold,foregroundColor"}})

    def divider(self):
        d = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        s = self.text(d)
        self.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(d) - 2}, "textStyle": {"foregroundColor": {"color": {"rgbColor": NAVY}}}, "fields": "foregroundColor"}})

    def thin_divider(self):
        d = "─────────────────────────────────────────────\n\n"
        s = self.text(d)
        self.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(d) - 2}, "textStyle": {"foregroundColor": {"color": {"rgbColor": LIGHT_GRAY}}}, "fields": "foregroundColor"}})

    def italic_gray(self, t):
        s = self.text(f"{t}\n")
        self.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(t)}, "textStyle": {"italic": True, "foregroundColor": {"color": {"rgbColor": GRAY}}}, "fields": "italic,foregroundColor"}})

    def centered(self, t, style_fn=None):
        s = self.text(f"{t}\n")
        self.styles.append({"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": s + len(t)}, "paragraphStyle": {"alignment": "CENTER"}, "fields": "alignment"}})
        if style_fn:
            style_fn(s, s + len(t))

    def get_all(self):
        return self.requests + self.styles

# ─── DATA ───

DEPARTMENTS = [
    {
        "icon": "🚨", "name": "Emergency Department (ED)", "tag": "NEW INSIGHT AREA",
        "questions": [
            "What is the average door-to-doctor time across different shifts?",
            "Are ED patients being admitted or discharged within optimal timeframes?",
            "Is ED overcrowding during peak hours leading to patient walkouts (LWBS)?",
            "Are high-acuity patients being triaged and treated faster than low-acuity?",
            "What percentage of ED visits result in hospital admissions vs. discharge?",
        ],
        "insights": [
            "ED Door-to-Doctor Time Variance Across Shifts",
            "ED Patient Boarding and Disposition Delays",
            "Left Without Being Seen (LWBS) Rate and Revenue Impact",
            "Triage Accuracy and Acuity-Based Resource Allocation",
            "ED-to-Inpatient Conversion Rate by Specialty",
        ],
        "brief": {
            "title": "Left Without Being Seen (LWBS) Rate and Revenue Impact",
            "confidence": "High",
            "observation": "LWBS rate increased from 3.2% to 5.8% over the past two quarters, with the highest walkout rates occurring between 6:00 PM and 10:00 PM.",
            "evidence": "Average door-to-doctor time exceeds 45 minutes during evening peak hours. Patient walkout incidents correlate with triage nurse shift changeover gaps (5:30-6:30 PM). Weekend LWBS rates are 40% higher than weekdays.",
            "root_cause": "Insufficient triage staffing during evening shift changeover window, combined with no fast-track pathway for low-acuity patients (ESI Level 4-5) who represent 35% of evening volume.",
            "impact": "Estimated annual revenue loss of SAR 2.1 Million from walkout patients. Additional risk of negative online reviews and patient diversion to competing facilities.",
            "actions": "Implement triage overlap shift (5:00-7:00 PM). Create fast-track pathway for low-acuity patients. Install real-time wait time display. Set up automated SMS notification when patient is next.",
            "strategic": "Reducing LWBS by 50% directly impacts both revenue recovery (SAR 1.05M) and patient satisfaction scores, increasingly tied to insurance network inclusion criteria in KSA.",
        },
        "kpis": [
            ("ED Door-to-Doctor Time", "< 30 minutes (ACEP standard)"),
            ("LWBS Rate", "< 2-5% (Emergency Medicine benchmark)"),
            ("ED-to-Inpatient Conversion Rate", "15-25% depending on acuity mix"),
        ],
        "data_sources": "HIS (ED Module), Triage System, Patient Flow Dashboard",
    },
    {
        "icon": "🏥", "name": "Inpatient Department (IPD)", "tag": "NEW INSIGHT AREA",
        "questions": [
            "What is the average length of stay (ALOS) by specialty, and how does it compare to benchmarks?",
            "Are bed occupancy rates balanced across wards and floors?",
            "Are readmission rates within 30 days indicating quality gaps?",
            "Is discharge planning causing unnecessary bed-blocking?",
            "Are surgical cancellations on the day of surgery affecting OR utilization?",
        ],
        "insights": [
            "Length of Stay Optimization by Clinical Specialty",
            "Bed Occupancy Imbalance Across Hospital Wards",
            "30-Day Readmission Rates and Root Causes",
            "Delayed Discharge and Bed Turnover Impact",
            "Same-Day Surgical Cancellation Rate and Revenue Loss",
        ],
        "brief": {
            "title": "Delayed Discharge and Bed Turnover Impact",
            "confidence": "High",
            "observation": "Average time from physician discharge order to actual patient departure is 6.2 hours, against a target of 2 hours. This creates a daily average of 12 blocked beds across the network.",
            "evidence": "Discharge orders peak at 11:00 AM but actual departures peak at 5:00 PM. Pharmacy medication reconciliation averages 2.1 hours. Insurance pre-authorization for follow-up adds 1.5 hours.",
            "root_cause": "Sequential discharge process instead of parallel processing. No discharge planning initiated at admission. Lack of discharge lounge for patients cleared but awaiting transport.",
            "impact": "12 blocked beds daily translates to approximately SAR 4.3 Million in annual lost admission revenue. ED boarding times increase by 2.3 hours when IPD beds are blocked.",
            "actions": "Implement parallel discharge processing. Begin discharge planning at Day 1 of admission. Create discharge lounge to free beds immediately. Set discharge time targets by ward.",
            "strategic": "A 50% improvement in discharge time would free 6 beds daily, equivalent to adding a new ward without capital expenditure.",
        },
        "kpis": [
            ("Average Length of Stay (ALOS)", "Per specialty: Saudi MOH benchmark; General: 4-5 days"),
            ("Bed Occupancy Rate", "80-85% (WHO recommended optimal range)"),
            ("30-Day Readmission Rate", "< 10% (CMS benchmark); < 5% for elective"),
            ("Surgical Cancellation Rate", "< 5% same-day (Best practice)"),
        ],
        "data_sources": "HIS (ADT Module), Bed Management System, Discharge Planning Module",
    },
    {
        "icon": "💊", "name": "Pharmacy", "tag": "NEW INSIGHT AREA",
        "questions": [
            "Are high-cost medications being prescribed when cost-effective alternatives exist?",
            "Is pharmacy inventory aligned with actual consumption patterns?",
            "Are medication turnaround times from order to administration affecting patient care?",
            "Is formulary compliance being maintained across prescribing physicians?",
            "What is the revenue contribution of outpatient pharmacy vs. inpatient?",
        ],
        "insights": [
            "High-Cost Medication Substitution Opportunities",
            "Pharmacy Stock-Out and Expiry Rate Analysis",
            "Medication Dispensing Turnaround Time",
            "Formulary Adherence Rate by Prescriber",
            "Outpatient Pharmacy Revenue Optimization",
        ],
        "brief": {
            "title": "High-Cost Medication Substitution Opportunities",
            "confidence": "Medium",
            "observation": "Analysis of top 50 medications by spend reveals 18 branded drugs have therapeutically equivalent generic or biosimilar alternatives, representing 31% of total pharmacy expenditure.",
            "evidence": "Monthly spend on substitutable branded medications averages SAR 420,000. Generic alternatives are 40-75% cheaper. Three hospitals already use generics for 8 of these with no efficacy differences.",
            "root_cause": "No standardized formulary review cycle. Physician prescribing habits favor familiar branded products. P&T committee meets quarterly but lacks cost-effectiveness analysis.",
            "impact": "Potential annual savings of SAR 2.5-3.8 Million from generic/biosimilar substitution across the network, with no compromise in clinical outcomes.",
            "actions": "Conduct formulary review for top 50 drugs with cost-effectiveness analysis. Present substitution recommendations to P&T committee. Implement therapeutic interchange protocols.",
            "strategic": "Pharmacy cost optimization delivers immediate P&L improvement. Positions TopMed aligned with Saudi Vision 2030 healthcare cost efficiency goals.",
        },
        "kpis": [
            ("Formulary Compliance", "> 90% (Joint Commission standard)"),
            ("Medication Dispensing TAT", "< 30 minutes routine; < 10 minutes stat"),
            ("Stock-Out Rate", "< 2% (Pharmacy best practice)"),
        ],
        "data_sources": "Pharmacy Information System (PIS), Formulary Database, Procurement System",
    },
    {
        "icon": "⭐", "name": "Patient Experience", "tag": "NEW INSIGHT AREA",
        "questions": [
            "Are patient satisfaction scores declining in specific departments or hospitals?",
            "Is there a correlation between waiting times and patient complaints?",
            "Are patient no-show rates affecting revenue and resource planning?",
            "What percentage of patients return for follow-up visits within 90 days?",
            "Are online reviews and ratings reflecting internal quality metrics?",
        ],
        "insights": [
            "Patient Satisfaction Score Trends by Department",
            "Wait Time Impact on Patient Retention",
            "Patient No-Show Patterns and Financial Impact",
            "Patient Retention and Follow-Up Compliance",
            "Digital Reputation vs. Internal Quality Gap",
        ],
        "brief": {
            "title": "Patient No-Show Patterns and Financial Impact",
            "confidence": "High",
            "observation": "Average OPD no-show rate is 22%, with Dermatology (31%) and Ophthalmology (28%) significantly higher. No-show rates 3x higher for appointments booked >14 days in advance.",
            "evidence": "Monthly revenue impact estimated at SAR 890,000. Clinics with SMS reminders (48h + 2h) show 35% lower no-show rates. Saturday morning slots have highest no-show rate (34%).",
            "root_cause": "Inconsistent appointment reminders. No penalty for repeat no-shows. Overbooking not calibrated to specialty-specific rates. Long booking horizons increase abandonment.",
            "impact": "Estimated annual revenue loss of SAR 10.7 Million from no-show appointments. Additional hidden cost in physician idle time and wasted clinic preparation.",
            "actions": "Implement dual SMS reminder system (48h + 2h). Deploy specialty-specific overbooking ratios. Introduce waitlist backfill for same-day cancellations. Flag repeat no-show patients.",
            "strategic": "A 30% reduction recovers SAR 3.2M annually while improving physician utilization. One of the highest-ROI operational improvements available.",
        },
        "kpis": [
            ("Patient Satisfaction Score", "> 85% (Top quartile Saudi hospitals)"),
            ("No-Show Rate", "< 10% (Best practice); Industry average: 15-20%"),
            ("Patient Retention (90-day follow-up)", "> 70% (Chronic care benchmark)"),
        ],
        "data_sources": "Satisfaction Survey System, Appointment Management System, Online Review Platforms",
    },
    {
        "icon": "📦", "name": "Supply Chain & Procurement", "tag": "NEW INSIGHT AREA",
        "questions": [
            "Are procurement costs for medical consumables increasing faster than patient volume?",
            "Is there price variance for the same items across different hospitals in the network?",
            "Are vendor contracts being renegotiated at optimal intervals?",
            "Is inventory carrying cost proportional to consumption?",
        ],
        "insights": [
            "Medical Consumable Cost Per Patient Trend",
            "Cross-Hospital Procurement Price Variance",
            "Vendor Contract Renewal Optimization",
            "Inventory Carrying Cost vs. Consumption Efficiency",
        ],
        "brief": {
            "title": "Cross-Hospital Procurement Price Variance",
            "confidence": "High",
            "observation": "Price comparison across 15 hospitals reveals identical medical consumables procured at prices varying by 15-42%, with surgical gloves, IV sets, and wound care products showing widest variance.",
            "evidence": "Top 20 consumables show average price variance of 28%. Three hospitals consistently pay 15-20% premium. Vendor contracts have different renewal dates and terms.",
            "root_cause": "Decentralized procurement without network-wide benchmarking. Individual hospitals negotiate independently. No centralized contract management. Historical pricing accepted without rebidding.",
            "impact": "Estimated annual savings of SAR 5.2 Million by standardizing to the best-available network rate for top 100 consumables.",
            "actions": "Establish centralized procurement dashboard. Consolidate vendor contracts for top 100 consumables. Implement mandatory competitive bidding >SAR 100,000. Create quarterly price variance report.",
            "strategic": "Centralized procurement is foundational for any multi-hospital network. Delivers immediate savings while building infrastructure for ongoing optimization.",
        },
        "kpis": [
            ("Procurement Price Variance", "< 10% across network (Supply chain benchmark)"),
            ("Inventory Carrying Cost", "< 25% of annual consumption value"),
            ("Contract Renewal Compliance", "100% reviewed within 30 days of expiry"),
        ],
        "data_sources": "ERP (Procurement Module), Inventory Management System, Vendor Contract Database",
    },
    {
        "icon": "🛡️", "name": "Quality & Clinical Safety", "tag": "NEW INSIGHT AREA",
        "questions": [
            "Are hospital-acquired infection rates trending within acceptable limits?",
            "Are near-miss and adverse event reporting rates increasing or declining?",
            "Are clinical protocol compliance rates consistent across hospitals?",
            "Is there a correlation between staffing ratios and patient safety events?",
        ],
        "insights": [
            "Hospital-Acquired Infection Rate Trends",
            "Incident Reporting Culture and Near-Miss Trends",
            "Clinical Protocol Adherence Across Network",
            "Nurse-to-Patient Ratio Impact on Safety Events",
        ],
        "brief": {
            "title": "Incident Reporting Culture and Near-Miss Trends",
            "confidence": "Medium",
            "observation": "Near-miss reporting rates vary 5x across hospitals (highest: 12.4/1,000 patient days; lowest: 2.3/1,000). Low-reporting hospitals don't have fewer incidents; they have weaker reporting culture.",
            "evidence": "Hospitals with dedicated quality champions report 3.2x more near-misses. Medication near-misses account for 45% of reports. Reporting dropped 18% after a punitive response at one facility.",
            "root_cause": "Inconsistent just-culture implementation. Some hospitals still associate reporting with blame. Anonymous reporting not available at all facilities. No positive feedback loop.",
            "impact": "Under-reporting masks safety risks. Each reported near-miss prevents an average of 300 unsafe conditions. Low-reporting hospitals carry unquantified patient safety liability.",
            "actions": "Standardize just-culture training with annual refresher. Implement anonymous digital reporting channel. Create monthly 'Safety Spotlight.' Share anonymized learnings quarterly.",
            "strategic": "Near-miss reporting is a leading indicator of safety culture. Improving rates is a prerequisite for CBAHI accreditation excellence.",
        },
        "kpis": [
            ("Hospital-Acquired Infection Rate", "< 2 per 1,000 patient days (WHO target)"),
            ("Incident Reporting Rate", "> 8 per 1,000 patient days (High-reliability benchmark)"),
            ("Nurse-to-Patient Ratio", "1:4 Med/Surg, 1:2 ICU, 1:1 Critical (Saudi MOH)"),
            ("Clinical Protocol Adherence", "> 95% (CBAHI standard)"),
        ],
        "data_sources": "Incident Reporting System, Infection Control Database, CBAHI Compliance Tracker",
    },
    {
        "icon": "🩻", "name": "Radiology", "tag": "EXPANSION",
        "questions": [
            "What is the radiology report turnaround time, and does it vary by modality?",
            "Are repeat/rejected imaging studies increasing costs?",
        ],
        "insights": [
            "Radiology Report Turnaround Time by Modality",
            "Radiology Repeat Study Rate and Quality Impact",
        ],
        "brief": {
            "title": "Radiology Report Turnaround Time by Modality",
            "confidence": "High",
            "observation": "Average TAT varies: X-ray 2.1h, Ultrasound 4.3h, CT 6.8h, MRI 11.2h. CT and MRI exceed the 4-hour target in 67% of cases.",
            "evidence": "ED-ordered CT reports average 8.4 hours vs. 5.2 hours for scheduled outpatient. Weekend TAT is 2.3x longer. Three radiologists handle 60% of MRI reads.",
            "root_cause": "Uneven radiologist workload distribution. No priority queue for ED-ordered studies. Weekend coverage relies on on-call rather than active staffing.",
            "impact": "Delayed reports extend ED disposition by 2-4 hours and delay inpatient treatment decisions. Estimated SAR 1.8M annually from delayed discharges.",
            "actions": "Implement priority-based PACS worklist. Redistribute MRI reading load. Add active evening radiologist shift (4 PM-midnight). Track TAT daily by modality.",
            "strategic": "Radiology TAT directly impacts ED throughput, inpatient LOS, and physician satisfaction. Meeting 4-hour target is a competitive differentiator.",
        },
        "kpis": [
            ("Radiology Report TAT", "< 4 hours routine; < 1 hour ED stat (ACR guideline)"),
            ("Repeat/Reject Rate", "< 5% (Radiology quality benchmark)"),
        ],
        "data_sources": "PACS, RIS (Radiology Information System), HIS Radiology Module",
    },
    {
        "icon": "🔬", "name": "Laboratory", "tag": "EXPANSION",
        "questions": [
            "Are critical value notification times meeting clinical standards?",
            "Is send-out testing volume growing when in-house capacity exists?",
        ],
        "insights": [
            "Critical Lab Value Notification Compliance",
            "In-House vs. Send-Out Test Migration Opportunity",
        ],
        "brief": {
            "title": "In-House vs. Send-Out Test Migration Opportunity",
            "confidence": "Medium",
            "observation": "Send-out volume grew 24% YoY while in-house grew only 8%. 12 high-volume send-out tests could be performed in-house with existing or minimal additional equipment.",
            "evidence": "Monthly send-out spend averages SAR 340,000. Top 12 tests represent 55% of send-out costs. In-house cost would be 40-65% lower. Send-out TAT: 5-7 days vs. same-day in-house.",
            "root_cause": "No regular review of send-out menu against in-house capabilities. Equipment procurement requires lengthy approval. Some tests sent out historically when volumes were low.",
            "impact": "Migrating top 12 tests saves approximately SAR 1.4 Million annually while reducing TAT from 5-7 days to same-day.",
            "actions": "Conduct feasibility study for top 12 tests. Build business case with ROI timeline. Prioritize migration by volume and margin. Set quarterly targets.",
            "strategic": "In-house testing expansion aligns with TopMed's full-service strategy. Faster turnaround improves outcomes and reduces repeat visits.",
        },
        "kpis": [
            ("Lab Stat TAT", "< 60 minutes (CAP recommendation)"),
            ("Send-Out Test Ratio", "< 5% of total test volume (Lab efficiency benchmark)"),
            ("Critical Value Notification", "< 30 minutes (CAP/Joint Commission)"),
        ],
        "data_sources": "LIS (Laboratory Information System), Send-Out Tracking, Equipment Utilization Logs",
    },
    {
        "icon": "🩺", "name": "OPD (Outpatient Department)", "tag": "EXPANSION",
        "questions": [
            "Are new patient acquisition rates growing or stagnating by specialty?",
            "What is the doctor productivity rate (patients per clinical hour)?",
        ],
        "insights": [
            "New Patient Acquisition Rate by Specialty",
            "Doctor Productivity and Clinic Slot Utilization",
        ],
        "brief": {
            "title": "Doctor Productivity and Clinic Slot Utilization",
            "confidence": "High",
            "observation": "Top quartile physicians see 5.8 patients/clinic hour vs. 2.1 for bottom quartile. Clinic slot utilization averages 71%, meaning 29% of slots go unfilled.",
            "evidence": "Specialties with standardized templates show 22% higher throughput. Clinics starting 15+ min late lose 1.5 slots/session. Double-booking varies 5-35% across physicians.",
            "root_cause": "No standardized consultation time targets by visit type. Clinic start time not monitored. Patient flow bottlenecks at registration. Some physicians block slots for walk-ins that never materialize.",
            "impact": "Improving utilization from 71% to 85% would generate an estimated SAR 8.4 Million in additional annual OPD revenue without adding clinic hours or physicians.",
            "actions": "Implement visit-type-based slot duration (new: 20min, follow-up: 10min). Track clinic start time adherence. Deploy pre-visit registration. Release unconfirmed slots 24h before.",
            "strategic": "OPD is the front door. Maximizing productivity is the highest-leverage revenue growth initiative without capital expenditure.",
        },
        "kpis": [
            ("OPD Slot Utilization", "> 85% (Operational best practice)"),
            ("New Patient Acquisition Rate", "> 5% YoY growth by specialty"),
            ("Clinic Start Time Adherence", "> 90% on-time start"),
        ],
        "data_sources": "HIS (Appointment Module), Clinic Scheduling System, Patient Registration System",
    },
    {
        "icon": "💰", "name": "Revenue Cycle", "tag": "EXPANSION",
        "questions": [
            "What is the average days in accounts receivable (AR) by payer?",
            "Are self-pay collection rates declining?",
            "Is payer mix shifting in a way that impacts overall margin?",
        ],
        "insights": [
            "Accounts Receivable Aging by Payer Category",
            "Self-Pay Collection Rate Decline",
            "Payer Mix Shift and Margin Impact Analysis",
        ],
        "brief": {
            "title": "Accounts Receivable Aging by Payer Category",
            "confidence": "High",
            "observation": "Average AR is 78 days (target: 45). Government payers average 112 days, insurance 64 days, self-pay 43 days. AR >90 days represents 34% of outstanding receivables.",
            "evidence": "First-pass acceptance rate is 71% (target: 95%). Rejected claims take 28 days for resubmission. Three government contracts have no late-payment penalties. Monthly write-off >180 days averages SAR 280,000.",
            "root_cause": "High rejection rate from coding errors and incomplete documentation. No dedicated follow-up for aging government claims. Lack of automated claim tracking. Payment terms not enforced.",
            "impact": "Reducing AR from 78 to 55 days would release approximately SAR 18 Million in working capital. Improving first-pass to 90% reduces resubmission costs by SAR 1.2M annually.",
            "actions": "Deploy automated claim scrubbing before submission. Create dedicated AR follow-up team for >60 days. Renegotiate government contracts. Implement weekly AR aging dashboard.",
            "strategic": "Cash flow is the lifeblood. AR optimization is the single highest-impact financial initiative, freeing capital while reducing bad debt.",
        },
        "kpis": [
            ("Days in Accounts Receivable", "< 45 days (Industry target); Saudi avg: 60-80 days"),
            ("Claim First-Pass Acceptance", "> 95% (Revenue cycle best practice)"),
            ("Self-Pay Collection Rate", "> 85% at point of service"),
        ],
        "data_sources": "Billing System, Claims Management Platform, Payer Portal, AR Aging Reports",
    },
    {
        "icon": "⚙️", "name": "Operational Efficiency", "tag": "EXPANSION",
        "questions": [
            "Is overtime spending proportional to patient volume increases?",
            "Are energy and facility costs per patient bed-day within benchmark?",
        ],
        "insights": [
            "Overtime Cost vs. Patient Volume Correlation",
            "Facility Cost Per Occupied Bed-Day",
        ],
        "brief": {
            "title": "Overtime Cost vs. Patient Volume Correlation",
            "confidence": "High",
            "observation": "Overtime spending increased 31% YoY while patient volume grew only 12%. The ratio suggests structural issues rather than demand-driven overtime.",
            "evidence": "Nursing overtime is 68% of total overtime spend. ED, ICU, OR consume 52% of all overtime hours. Weekend overtime is 2.8x higher than weekday.",
            "root_cause": "Staffing models not updated for current volume patterns. Scheduling based on historical patterns. Overtime approval process is informal. No department-level visibility until monthly payroll.",
            "impact": "Estimated SAR 3.6 Million in reducible overtime annually. Additional benefit: reduced nurse burnout and turnover costs.",
            "actions": "Build demand-based staffing model using 12-month data. Implement real-time overtime tracking dashboard. Require formal pre-approval for non-emergency overtime. Review shift patterns quarterly.",
            "strategic": "Workforce cost is the largest operating expense. Data-driven staffing delivers immediate P&L improvement while improving employee satisfaction.",
        },
        "kpis": [
            ("Overtime as % of Total Labor", "< 5% (Healthcare HR benchmark)"),
            ("Facility Cost Per Occupied Bed-Day", "Benchmark varies by region; track trend"),
            ("Energy Cost Per Square Meter", "Track against prior year + 5% improvement target"),
        ],
        "data_sources": "HR/Payroll System (Overtime Tracking), Facility Management System, Financial Reporting",
    },
]

CROSS_DEPT = [
    {
        "title": "OPD-to-Radiology Referral Conversion Leakage",
        "depts": "OPD + Radiology",
        "question": "What percentage of OPD consultations that should result in diagnostic imaging actually convert to radiology orders, and where are patients dropping off?",
        "insight": "Referral conversion rates vary from 34% to 78% across specialties. Patients referred for imaging but not scheduled within 48 hours have a 45% abandonment rate.",
        "impact": "Estimated SAR 3.1M in annual radiology revenue leakage from unconverted OPD referrals.",
    },
    {
        "title": "ED Admission to IPD Bed Assignment Wait Time",
        "depts": "Emergency Department + Inpatient Department",
        "question": "How long do admitted ED patients wait for an inpatient bed, and what is the revenue and clinical impact of ED boarding?",
        "insight": "Average ED-to-bed time is 4.7 hours (target: 1 hour). During peak occupancy, ED boarding reaches 8+ hours. Boarded patients consume ED nursing resources at 2.3x the rate of standard ED patients.",
        "impact": "ED boarding reduces ED capacity by an estimated 15%, translating to SAR 2.8M in diverted or delayed revenue annually.",
    },
    {
        "title": "Pharmacy Cost Per Inpatient Day by Department",
        "depts": "Pharmacy + Inpatient Department",
        "question": "Which departments have the highest pharmacy cost per patient day, and are there outlier prescribing patterns driving cost inflation?",
        "insight": "Pharmacy cost per inpatient day ranges from SAR 180 (General Ward) to SAR 2,400 (Oncology). ICU pharmacy cost variance between hospitals suggests prescribing pattern differences rather than case-mix differences.",
        "impact": "Standardizing ICU prescribing protocols to the network best practice could save SAR 1.6M annually.",
    },
    {
        "title": "End-to-End Revenue Cycle: Visit to Collection",
        "depts": "OPD + Revenue Cycle + Insurance",
        "question": "What is the average time from patient visit to final payment collection, and where are the bottlenecks in the revenue realization chain?",
        "insight": "Average visit-to-cash cycle is 94 days. Major bottlenecks: coding completion (7 days), claim submission (12 days), payer adjudication (45 days), denial rework (21 days). Self-pay collection at point-of-service captures only 62% of expected revenue.",
        "impact": "Reducing visit-to-cash from 94 to 60 days would improve annual cash flow by approximately SAR 22M across the network.",
    },
    {
        "title": "Surgical Pathway: OPD Consultation to OR Utilization",
        "depts": "OPD + Operating Room + IPD",
        "question": "What is the conversion rate from surgical consultation to completed surgery, and what are the drop-off points in the surgical patient pathway?",
        "insight": "Only 58% of patients recommended for elective surgery actually complete the procedure. Drop-off points: 18% at pre-surgical workup, 12% at insurance pre-authorization, 7% at scheduling (wait time >3 weeks), 5% no-show on surgery day.",
        "impact": "Improving surgical conversion from 58% to 75% would generate an estimated SAR 12M in additional surgical revenue annually.",
    },
    {
        "title": "Laboratory TAT Impact on ED Disposition Time",
        "depts": "Laboratory + Emergency Department",
        "question": "How does laboratory result turnaround time affect ED patient disposition decisions, and what is the cost of delayed lab results?",
        "insight": "ED patients requiring lab work wait an average of 2.3 hours for results. Stat lab TAT exceeds 60-minute target in 41% of cases. Each 30-minute lab delay adds approximately 45 minutes to total ED length of stay.",
        "impact": "Meeting the 60-minute stat lab target would reduce average ED LOS by 1.1 hours, improving throughput and recovering an estimated SAR 1.9M in annual ED capacity.",
    },
]

PRIORITY_MATRIX = [
    (1, "AR Aging by Payer Category", "SAR 18M", "Available Now", "Medium Effort", "🔴"),
    (2, "OPD Slot Utilization", "SAR 8.4M", "Available Now", "Quick Win", "🔴"),
    (3, "Cross-Hospital Procurement Variance", "SAR 5.2M", "Available Now", "Medium Effort", "🔴"),
    (4, "Delayed Discharge / Bed Turnover", "SAR 4.3M", "Available Now", "Medium Effort", "🔴"),
    (5, "Patient No-Show Patterns", "SAR 10.7M", "Available Now", "Quick Win", "🔴"),
    (6, "Medication Substitution", "SAR 2.5-3.8M", "Needs Collection", "Medium Effort", "🟡"),
    (7, "ED LWBS Rate", "SAR 2.1M", "Available Now", "Quick Win", "🟡"),
    (8, "Overtime vs. Volume", "SAR 3.6M", "Available Now", "Medium Effort", "🟡"),
    (9, "Radiology Report TAT", "SAR 1.8M", "Available Now", "Quick Win", "🟡"),
    (10, "Send-Out Test Migration", "SAR 1.4M", "Needs Collection", "Major Initiative", "🟢"),
    (11, "Near-Miss Reporting Culture", "Risk Mitigation", "Needs Collection", "Major Initiative", "🟢"),
    (12, "Digital Reputation vs Quality", "Brand Value", "Needs Integration", "Medium Effort", "🟢"),
]


def main():
    token = get_access_token()

    # Create new doc
    doc = api_call('https://docs.googleapis.com/v1/documents',
                   {"title": "TopMed Insights Bank - Comprehensive Department Guide (March 2026)"},
                   token)
    doc_id = doc['documentId']
    print(f"Created doc: {doc_id}")

    b = DocBuilder()

    # ─── TITLE ───
    b.centered("TopMed Insights Bank", lambda s, e: [
        b.styles.append({"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": e}, "paragraphStyle": {"namedStyleType": "HEADING_1"}, "fields": "namedStyleType"}}),
        b.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": e}, "textStyle": {"bold": True, "fontSize": {"magnitude": 24, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": NAVY}}}, "fields": "bold,fontSize,foregroundColor"}}),
    ])
    b.centered("Comprehensive Department Guide", lambda s, e: [
        b.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": e}, "textStyle": {"italic": True, "fontSize": {"magnitude": 14, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": GRAY}}}, "fields": "italic,fontSize,foregroundColor"}}),
    ])
    b.text("\n")
    b.centered("Prepared by: Ahmed Nasr, Delivery PMO | March 2026 | Confidential", lambda s, e: [
        b.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": e}, "textStyle": {"italic": True, "fontSize": {"magnitude": 10, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": GRAY}}}, "fields": "italic,fontSize,foregroundColor"}}),
    ])
    b.text("\n")
    b.divider()

    # ─── EXECUTIVE SUMMARY ───
    b.h1("Executive Summary")
    b.italic_gray("SAR 65M+ in identified improvement opportunities across 11 departments")
    b.text("\n")

    summary_items = [
        "6 new insight areas identified (ED, IPD, Pharmacy, Patient Experience, Supply Chain, Quality & Safety)",
        "5 existing areas expanded (Radiology, Laboratory, OPD, Revenue Cycle, Operational Efficiency)",
        "11 detailed insight briefs with financial impact analysis",
        "6 cross-department insights spanning multiple areas",
        "20 KPI benchmarks with industry standards",
        "Complete data source mapping for implementation readiness",
    ]
    for item in summary_items:
        b.bullet(item, bold=False)
    b.text("\n")

    # Top financial opportunities
    b.h3("Top Financial Opportunities")
    top_fin = [
        "SAR 18M working capital release (AR Optimization)",
        "SAR 12M surgical pathway conversion (Cross-Department)",
        "SAR 10.7M no-show revenue recovery (Patient Experience)",
        "SAR 8.4M OPD slot utilization (OPD)",
        "SAR 5.2M procurement standardization (Supply Chain)",
    ]
    for item in top_fin:
        b.bullet(item, bold=True)
    b.text("\n")
    b.divider()

    # ─── PRIORITY MATRIX ───
    b.h1("🎯  Priority Matrix")
    b.italic_gray("Insights ranked by revenue impact, data readiness, and implementation complexity")
    b.text("\n")

    # Header
    header = "Rank | Insight | Revenue Impact | Data Readiness | Complexity\n"
    s = b.text(header)
    b.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(header) - 1}, "textStyle": {"bold": True, "foregroundColor": {"color": {"rgbColor": NAVY}}}, "fields": "bold,foregroundColor"}})

    for rank, insight, revenue, data, complexity, icon in PRIORITY_MATRIX:
        line = f"{icon}  {rank}. {insight}  |  {revenue}  |  {data}  |  {complexity}\n"
        s = b.text(line)
        name_start = s + len(f"{icon}  {rank}. ")
        b.styles.append({"updateTextStyle": {"range": {"startIndex": name_start, "endIndex": name_start + len(insight)}, "textStyle": {"bold": True}, "fields": "bold"}})

    b.text("\n")
    b.italic_gray("🔴 = Start Immediately (Top 5)   🟡 = Plan This Quarter   🟢 = Next Quarter")
    b.text("\n")
    b.divider()

    # ─── DEPARTMENTS (Each self-contained) ───
    for dept in DEPARTMENTS:
        b.h1(f"{dept['icon']}  {dept['name']}")
        tag = dept['tag']
        tag_line = f"[{tag}]\n"
        s = b.text(tag_line)
        tag_color = GREEN if tag == "NEW INSIGHT AREA" else BLUE
        b.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(tag_line) - 1}, "textStyle": {"bold": True, "italic": True, "foregroundColor": {"color": {"rgbColor": tag_color}}}, "fields": "bold,italic,foregroundColor"}})
        b.text("\n")

        # Questions
        b.h2("Analytical Questions")
        for i, q in enumerate(dept['questions'], 1):
            b.numbered(i, q)
        b.text("\n")

        # Insight Titles
        b.h2("Insight Titles")
        for ins in dept['insights']:
            b.bullet(ins, bold=True)
        b.text("\n")

        # Sample Brief
        brief = dept['brief']
        b.h2(f"Sample Insight Brief: {brief['title']}")

        conf = brief['confidence']
        conf_color = GREEN if conf == "High" else ORANGE
        conf_line = f"Confidence Level: {conf}\n"
        s = b.text(conf_line)
        b.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len("Confidence Level:")}, "textStyle": {"bold": True, "foregroundColor": {"color": {"rgbColor": NAVY}}}, "fields": "bold,foregroundColor"}})
        b.styles.append({"updateTextStyle": {"range": {"startIndex": s + len("Confidence Level: "), "endIndex": s + len(conf_line) - 1}, "textStyle": {"bold": True, "foregroundColor": {"color": {"rgbColor": conf_color}}}, "fields": "bold,foregroundColor"}})
        b.text("\n")

        b.field("Observation", brief['observation'])
        b.field("Supporting Evidence", brief['evidence'])
        b.field("Root Cause Analysis", brief['root_cause'])
        b.field("Business Impact", brief['impact'], RED)
        b.field("Recommended Actions", brief['actions'], GREEN)
        b.field("Strategic Importance", brief['strategic'], BLUE)
        b.text("\n")

        # KPI Benchmarks
        b.h2("KPI Benchmarks")
        for kpi, benchmark in dept['kpis']:
            full = f"  ▸  {kpi}:  {benchmark}\n"
            s = b.text(full)
            b.styles.append({"updateTextStyle": {"range": {"startIndex": s + 5, "endIndex": s + 5 + len(kpi)}, "textStyle": {"bold": True}, "fields": "bold"}})
            b.styles.append({"updateTextStyle": {"range": {"startIndex": s + 5 + len(kpi) + 3, "endIndex": s + len(full) - 1}, "textStyle": {"foregroundColor": {"color": {"rgbColor": GREEN}}}, "fields": "foregroundColor"}})
        b.text("\n")

        # Data Sources
        b.h2("Data Sources")
        b.field("Primary Systems", dept['data_sources'])
        b.text("\n")

        b.divider()

    # ─── CROSS-DEPARTMENT INSIGHTS ───
    b.h1("🔗  Cross-Department Insights")
    b.italic_gray("High-value opportunities that span multiple departments. These are typically the highest-impact insights because no single department owns them.")
    b.text("\n\n")

    for cd in CROSS_DEPT:
        b.h2(f"🔗  {cd['title']}")
        b.field("Departments", cd['depts'])
        b.field("Analytical Question", cd['question'])
        b.field("Insight", cd['insight'], GREEN)
        b.field("Estimated Impact", cd['impact'], RED)
        b.text("\n")
        b.thin_divider()

    # ─── FOOTER ───
    b.divider()
    b.centered("End of TopMed Insights Bank | March 2026 | Confidential", lambda s, e: [
        b.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": e}, "textStyle": {"italic": True, "foregroundColor": {"color": {"rgbColor": GRAY}}}, "fields": "italic,foregroundColor"}}),
    ])

    # ─── SEND ALL ───
    all_reqs = b.get_all()
    print(f"Total requests: {len(all_reqs)}")

    batch_size = 80
    for i in range(0, len(all_reqs), batch_size):
        batch = all_reqs[i:i+batch_size]
        api_call(f'https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate',
                 {"requests": batch}, token)
        print(f"  Batch {i//batch_size + 1}: {len(batch)} requests applied")

    url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print(f"\n✅ Document ready: {url}")

if __name__ == '__main__':
    main()
