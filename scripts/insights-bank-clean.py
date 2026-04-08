#!/usr/bin/env python3
"""
TopMed Insights Bank - Clean version.
Insight Ideas with template structure, no fabricated data.
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

NAVY = {"red": 0.15, "green": 0.3, "blue": 0.53}
DARK = {"red": 0.13, "green": 0.13, "blue": 0.13}
GRAY = {"red": 0.5, "green": 0.5, "blue": 0.5}
GREEN = {"red": 0.0, "green": 0.4, "blue": 0.2}
LIGHT_GRAY = {"red": 0.8, "green": 0.8, "blue": 0.8}
RED = {"red": 0.75, "green": 0.15, "blue": 0.15}
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
        s = self.text(f"{t}\n")
        self.styles.append({"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": s + len(t)}, "paragraphStyle": {"namedStyleType": "HEADING_1"}, "fields": "namedStyleType"}})
        self.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(t)}, "textStyle": {"bold": True, "fontSize": {"magnitude": 18, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": NAVY}}}, "fields": "bold,fontSize,foregroundColor"}})
        self.text("\n")

    def h2(self, t):
        s = self.text(f"{t}\n")
        self.styles.append({"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": s + len(t)}, "paragraphStyle": {"namedStyleType": "HEADING_2"}, "fields": "namedStyleType"}})
        self.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(t)}, "textStyle": {"bold": True, "fontSize": {"magnitude": 14, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": NAVY}}}, "fields": "bold,fontSize,foregroundColor"}})
        self.text("\n")

    def h3(self, t):
        s = self.text(f"{t}\n")
        self.styles.append({"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": s + len(t)}, "paragraphStyle": {"namedStyleType": "HEADING_3"}, "fields": "namedStyleType"}})
        self.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(t)}, "textStyle": {"bold": True, "fontSize": {"magnitude": 12, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": BLUE}}}, "fields": "bold,fontSize,foregroundColor"}})

    def field(self, label, value, label_color=NAVY):
        full = f"{label}: {value}\n"
        s = self.text(full)
        self.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(label) + 1}, "textStyle": {"bold": True, "foregroundColor": {"color": {"rgbColor": label_color}}}, "fields": "bold,foregroundColor"}})

    def placeholder_field(self, label, label_color=NAVY):
        """Field with placeholder for real data"""
        full = f"{label}: [To be determined from data]\n"
        s = self.text(full)
        self.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(label) + 1}, "textStyle": {"bold": True, "foregroundColor": {"color": {"rgbColor": label_color}}}, "fields": "bold,foregroundColor"}})
        placeholder_start = s + len(label) + 2
        placeholder_end = s + len(full) - 1
        self.styles.append({"updateTextStyle": {"range": {"startIndex": placeholder_start, "endIndex": placeholder_end}, "textStyle": {"italic": True, "foregroundColor": {"color": {"rgbColor": GRAY}}}, "fields": "italic,foregroundColor"}})

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

# ─── DEPARTMENTS ───

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
            ("ED Door-to-Doctor Time Variance Across Shifts", "Compare average door-to-doctor time across morning, afternoon, and night shifts. Identify shifts with the longest wait times and investigate staffing, patient volume, and triage efficiency as contributing factors."),
            ("ED Patient Boarding and Disposition Delays", "Measure the time from ED physician decision (admit/discharge) to actual patient movement. Identify bottlenecks in bed assignment, transport, and handoff processes that delay disposition."),
            ("Left Without Being Seen (LWBS) Rate and Revenue Impact", "Track the percentage of registered ED patients who leave before being seen by a physician. Analyze by time of day, day of week, and acuity level. Estimate the revenue loss from these walkouts."),
            ("Triage Accuracy and Acuity-Based Resource Allocation", "Evaluate whether triage classifications (ESI levels) are accurate by comparing initial acuity assignment to actual clinical outcomes. Assess if resource allocation matches acuity distribution."),
            ("ED-to-Inpatient Conversion Rate by Specialty", "Calculate the percentage of ED visits resulting in hospital admission, broken down by referring specialty. Identify specialties with unusually high or low conversion rates for further investigation."),
        ],
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
            ("Length of Stay Optimization by Clinical Specialty", "Compare actual ALOS by specialty against Saudi MOH benchmarks and internal targets. Identify specialties with consistently above-benchmark stays and investigate clinical, administrative, or discharge-related causes."),
            ("Bed Occupancy Imbalance Across Hospital Wards", "Analyze bed utilization rates across all wards and floors. Identify wards with chronic over-occupancy (causing diversions) or under-occupancy (indicating demand mismatch). Assess whether bed allocation aligns with specialty demand."),
            ("30-Day Readmission Rates and Root Causes", "Track patients readmitted within 30 days of discharge by diagnosis, specialty, and original treating physician. Identify patterns that may indicate premature discharge, inadequate discharge planning, or gaps in follow-up care."),
            ("Delayed Discharge and Bed Turnover Impact", "Measure the time gap between physician discharge order and actual patient departure. Identify the major delay factors (pharmacy reconciliation, insurance clearance, transport, patient/family readiness) and quantify their impact on bed availability."),
            ("Same-Day Surgical Cancellation Rate and Revenue Loss", "Track surgeries cancelled on the day of the scheduled procedure. Categorize by reason (patient-related, clinical, administrative, equipment). Calculate the financial impact of unused OR time and wasted preparation resources."),
        ],
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
            ("High-Cost Medication Substitution Opportunities", "Identify branded medications in the top 50 by spend that have therapeutically equivalent generics or biosimilars available in the Saudi market. Compare costs and assess the savings potential from substitution without compromising clinical outcomes."),
            ("Pharmacy Stock-Out and Expiry Rate Analysis", "Track medication stock-out frequency and expired medication write-offs. Identify items with recurring stock-outs (indicating under-ordering) and items with high expiry rates (indicating over-ordering or low demand forecasting accuracy)."),
            ("Medication Dispensing Turnaround Time", "Measure the time from physician medication order to actual patient administration. Identify bottlenecks in the dispensing workflow (order verification, preparation, transport, nursing administration) and their clinical impact."),
            ("Formulary Adherence Rate by Prescriber", "Track the percentage of prescriptions that comply with the hospital formulary, broken down by prescribing physician and specialty. Identify physicians with low adherence and investigate whether non-formulary prescriptions are clinically justified or habitual."),
            ("Outpatient Pharmacy Revenue Optimization", "Compare revenue and margin contributions of outpatient vs. inpatient pharmacy operations. Identify high-margin outpatient medications, assess prescription capture rate from discharged patients, and evaluate competitive pricing against external pharmacies."),
        ],
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
            ("Patient Satisfaction Score Trends by Department", "Analyze patient satisfaction survey results over time, broken down by department, hospital, and specific service dimensions (communication, wait time, cleanliness, pain management). Identify departments with declining trends and correlate with operational changes."),
            ("Wait Time Impact on Patient Retention", "Correlate average waiting times (registration, consultation, diagnostics, pharmacy) with patient complaint rates and return visit rates. Determine the wait time threshold beyond which patient retention significantly drops."),
            ("Patient No-Show Patterns and Financial Impact", "Analyze appointment no-show rates by specialty, day of week, time of day, and booking lead time. Identify the highest no-show specialties and time slots. Calculate the revenue impact and assess the effectiveness of current reminder systems."),
            ("Patient Retention and Follow-Up Compliance", "Track the percentage of patients who return for recommended follow-up visits within the prescribed timeframe. Identify specialties and patient segments with the lowest follow-up rates and investigate barriers to return."),
            ("Digital Reputation vs. Internal Quality Gap", "Compare external patient ratings (Google, social media, health platforms) with internal quality metrics and satisfaction surveys. Identify disconnects where internal metrics show improvement but external perception lags, or vice versa."),
        ],
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
            ("Medical Consumable Cost Per Patient Trend", "Track the cost of medical consumables per patient encounter (OPD visit, IPD day, surgical case) over time. Identify whether cost increases are driven by volume growth, price inflation, usage pattern changes, or a combination."),
            ("Cross-Hospital Procurement Price Variance", "Compare unit prices for identical items across all hospitals in the network. Identify items with the widest price variance and investigate whether differences are driven by contract terms, order volumes, local suppliers, or lack of centralized negotiation."),
            ("Vendor Contract Renewal Optimization", "Review vendor contract expiry dates, renewal terms, and historical price trends. Identify contracts approaching renewal that should be competitively rebid and contracts where bulk consolidation across hospitals would yield better pricing."),
            ("Inventory Carrying Cost vs. Consumption Efficiency", "Calculate the total cost of holding medical inventory (storage, insurance, capital lock-up, expiry waste) as a percentage of annual consumption value. Identify items with excessive safety stock relative to actual usage patterns."),
        ],
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
            ("Hospital-Acquired Infection Rate Trends", "Track hospital-acquired infection (HAI) rates by type (surgical site, catheter-associated, ventilator-associated) across all hospitals. Compare against WHO benchmarks and identify facilities or units with rising trends for targeted intervention."),
            ("Incident Reporting Culture and Near-Miss Trends", "Analyze near-miss and adverse event reporting rates across hospitals. Higher reporting rates typically indicate a stronger safety culture, not more incidents. Identify hospitals with low reporting and investigate whether just-culture practices are consistently applied."),
            ("Clinical Protocol Adherence Across Network", "Measure compliance with standardized clinical protocols (hand hygiene, medication administration, surgical safety checklist) across all hospitals. Identify protocols with the lowest adherence and hospitals with inconsistent compliance for focused training."),
            ("Nurse-to-Patient Ratio Impact on Safety Events", "Correlate nurse-to-patient staffing ratios with patient safety event rates (falls, medication errors, pressure injuries). Determine whether specific shifts, units, or hospitals have staffing levels below the threshold associated with increased safety events."),
        ],
        "kpis": [
            ("Hospital-Acquired Infection Rate", "< 2 per 1,000 patient days (WHO target)"),
            ("Incident Reporting Rate", "> 8 per 1,000 patient days (High-reliability benchmark)"),
            ("Nurse-to-Patient Ratio", "1:4 Med/Surg, 1:2 ICU, 1:1 Critical (Saudi MOH)"),
            ("Clinical Protocol Adherence", "> 95% (CBAHI standard)"),
        ],
        "data_sources": "Incident Reporting System, Infection Control Database, CBAHI Compliance Tracker",
    },
    {
        "icon": "🩻", "name": "Radiology", "tag": "EXPANSION TO EXISTING AREA",
        "questions": [
            "What is the radiology report turnaround time, and does it vary by modality?",
            "Are repeat/rejected imaging studies increasing costs?",
        ],
        "insights": [
            ("Radiology Report Turnaround Time by Modality", "Measure report TAT for each imaging modality (X-ray, Ultrasound, CT, MRI) and compare against targets. Break down by ordering source (ED stat, inpatient urgent, outpatient routine) and time period (weekday vs. weekend, day vs. night) to identify bottlenecks."),
            ("Radiology Repeat Study Rate and Quality Impact", "Track the percentage of imaging studies that are repeated or rejected due to technical quality issues (patient positioning, motion artifacts, incorrect parameters). Calculate the cost of repeated studies and identify technologists or equipment with above-average repeat rates."),
        ],
        "kpis": [
            ("Radiology Report TAT", "< 4 hours routine; < 1 hour ED stat (ACR guideline)"),
            ("Repeat/Reject Rate", "< 5% (Radiology quality benchmark)"),
        ],
        "data_sources": "PACS, RIS (Radiology Information System), HIS Radiology Module",
    },
    {
        "icon": "🔬", "name": "Laboratory", "tag": "EXPANSION TO EXISTING AREA",
        "questions": [
            "Are critical value notification times meeting clinical standards?",
            "Is send-out testing volume growing when in-house capacity exists?",
        ],
        "insights": [
            ("Critical Lab Value Notification Compliance", "Track the time from critical lab result generation to physician notification. Measure compliance against the 30-minute standard (CAP/Joint Commission). Identify test types and shifts with the longest notification delays."),
            ("In-House vs. Send-Out Test Migration Opportunity", "Compare send-out test volumes and costs against in-house capabilities. Identify high-volume send-out tests that could be migrated in-house based on equipment availability, volume thresholds, and cost-per-test analysis."),
        ],
        "kpis": [
            ("Lab Stat TAT", "< 60 minutes (CAP recommendation)"),
            ("Send-Out Test Ratio", "< 5% of total test volume (Lab efficiency benchmark)"),
            ("Critical Value Notification", "< 30 minutes (CAP/Joint Commission)"),
        ],
        "data_sources": "LIS (Laboratory Information System), Send-Out Tracking, Equipment Utilization Logs",
    },
    {
        "icon": "🩺", "name": "OPD (Outpatient Department)", "tag": "EXPANSION TO EXISTING AREA",
        "questions": [
            "Are new patient acquisition rates growing or stagnating by specialty?",
            "What is the doctor productivity rate (patients per clinical hour)?",
        ],
        "insights": [
            ("New Patient Acquisition Rate by Specialty", "Track the monthly volume of new patients (first-time visitors) by specialty. Identify specialties with declining new patient volumes and investigate whether the cause is competition, physician availability, appointment access, or marketing effectiveness."),
            ("Doctor Productivity and Clinic Slot Utilization", "Calculate the number of patients seen per clinical hour by physician and specialty. Measure overall clinic slot utilization (booked slots vs. available slots). Identify physicians and specialties with low utilization and assess whether the gap is due to scheduling, no-shows, or blocked slots."),
        ],
        "kpis": [
            ("OPD Slot Utilization", "> 85% (Operational best practice)"),
            ("New Patient Acquisition Rate", "> 5% YoY growth by specialty"),
            ("Clinic Start Time Adherence", "> 90% on-time start"),
        ],
        "data_sources": "HIS (Appointment Module), Clinic Scheduling System, Patient Registration System",
    },
    {
        "icon": "💰", "name": "Revenue Cycle", "tag": "EXPANSION TO EXISTING AREA",
        "questions": [
            "What is the average days in accounts receivable (AR) by payer?",
            "Are self-pay collection rates declining?",
            "Is payer mix shifting in a way that impacts overall margin?",
        ],
        "insights": [
            ("Accounts Receivable Aging by Payer Category", "Analyze AR aging buckets (0-30, 31-60, 61-90, 90+ days) by payer category (government, insurance, self-pay). Identify payers with the longest payment cycles and the highest proportion of aged receivables. Assess whether contract terms, claim rejection rates, or follow-up processes are driving delays."),
            ("Self-Pay Collection Rate Decline", "Track self-pay collection rates at point-of-service and post-discharge over time. Identify whether declining rates are due to changes in payment policy enforcement, patient demographics, pricing transparency, or availability of payment plans."),
            ("Payer Mix Shift and Margin Impact Analysis", "Monitor changes in the proportion of patients by payer category over time. Assess whether shifts in payer mix (e.g., increasing government, decreasing private insurance) are impacting overall revenue per patient and hospital margins."),
        ],
        "kpis": [
            ("Days in Accounts Receivable", "< 45 days (Industry target); Saudi avg: 60-80 days"),
            ("Claim First-Pass Acceptance", "> 95% (Revenue cycle best practice)"),
            ("Self-Pay Collection Rate", "> 85% at point of service"),
        ],
        "data_sources": "Billing System, Claims Management Platform, Payer Portal, AR Aging Reports",
    },
    {
        "icon": "⚙️", "name": "Operational Efficiency", "tag": "EXPANSION TO EXISTING AREA",
        "questions": [
            "Is overtime spending proportional to patient volume increases?",
            "Are energy and facility costs per patient bed-day within benchmark?",
        ],
        "insights": [
            ("Overtime Cost vs. Patient Volume Correlation", "Compare overtime spending trends against patient volume trends. Determine whether overtime growth is proportional to volume growth (demand-driven) or disproportionate (indicating structural staffing issues, inefficient scheduling, or informal approval processes)."),
            ("Facility Cost Per Occupied Bed-Day", "Calculate total facility costs (energy, maintenance, housekeeping, security) per occupied bed-day. Compare across hospitals in the network and track trends over time. Identify facilities with above-average costs for targeted efficiency improvements."),
        ],
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
        "description": "Track the referral-to-completion pathway from OPD physician order to completed radiology study. Identify drop-off points (order not placed, appointment not scheduled, patient no-show for imaging) by specialty and scheduling lead time.",
    },
    {
        "title": "ED Admission to IPD Bed Assignment Wait Time",
        "depts": "Emergency Department + Inpatient Department",
        "question": "How long do admitted ED patients wait for an inpatient bed, and what is the clinical and operational impact of ED boarding?",
        "description": "Measure the time from ED admission decision to actual inpatient bed placement. Analyze the cascading impact on ED capacity, nursing workload, and patient outcomes when boarding times are prolonged.",
    },
    {
        "title": "Pharmacy Cost Per Inpatient Day by Department",
        "depts": "Pharmacy + Inpatient Department",
        "question": "Which departments have the highest pharmacy cost per patient day, and are there outlier prescribing patterns driving cost inflation?",
        "description": "Calculate pharmacy spend per inpatient day by clinical department. Compare costs across hospitals for the same departments to distinguish case-mix-driven variation from prescribing pattern variation.",
    },
    {
        "title": "End-to-End Revenue Cycle: Visit to Collection",
        "depts": "OPD + Revenue Cycle + Insurance",
        "question": "What is the average time from patient visit to final payment collection, and where are the bottlenecks in the revenue realization chain?",
        "description": "Map the complete revenue cycle from patient encounter to cash collection. Identify time spent in each stage (coding, claim submission, payer adjudication, denial management, payment posting) and quantify the working capital impact of delays.",
    },
    {
        "title": "Surgical Pathway: OPD Consultation to OR Utilization",
        "depts": "OPD + Operating Room + IPD",
        "question": "What is the conversion rate from surgical consultation to completed surgery, and what are the drop-off points in the surgical patient pathway?",
        "description": "Track patients from initial surgical consultation through pre-operative workup, insurance authorization, scheduling, and surgery day. Identify where patients drop out of the surgical pathway and assess the revenue impact of each drop-off point.",
    },
    {
        "title": "Laboratory TAT Impact on ED Disposition Time",
        "depts": "Laboratory + Emergency Department",
        "question": "How does laboratory result turnaround time affect ED patient disposition decisions, and what is the operational cost of delayed lab results?",
        "description": "Correlate lab result delivery times with total ED length of stay for patients requiring lab work. Measure the incremental impact of lab delays on ED throughput, boarding, and overall department capacity.",
    },
]


def main():
    token = get_access_token()
    doc = api_call('https://docs.googleapis.com/v1/documents',
                   {"title": "TopMed Insights Bank - Additional Insight Ideas (March 2026)"},
                   token)
    doc_id = doc['documentId']
    print(f"Created doc: {doc_id}")

    b = DocBuilder()

    # ─── TITLE ───
    b.centered("TopMed Insights Bank", lambda s, e: [
        b.styles.append({"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": e}, "paragraphStyle": {"namedStyleType": "HEADING_1"}, "fields": "namedStyleType"}}),
        b.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": e}, "textStyle": {"bold": True, "fontSize": {"magnitude": 24, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": NAVY}}}, "fields": "bold,fontSize,foregroundColor"}}),
    ])
    b.centered("Additional Insight Ideas", lambda s, e: [
        b.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": e}, "textStyle": {"italic": True, "fontSize": {"magnitude": 14, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": GRAY}}}, "fields": "italic,fontSize,foregroundColor"}}),
    ])
    b.text("\n")
    b.centered("Prepared by: Ahmed Nasr, Delivery PMO | March 2026 | Confidential", lambda s, e: [
        b.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": e}, "textStyle": {"italic": True, "fontSize": {"magnitude": 10, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": GRAY}}}, "fields": "italic,fontSize,foregroundColor"}}),
    ])
    b.text("\n")
    b.divider()

    # ─── DEPARTMENTS ───
    for dept in DEPARTMENTS:
        b.h1(f"{dept['icon']}  {dept['name']}")
        tag = dept['tag']
        s = b.text(f"[{tag}]\n")
        tag_color = GREEN if "NEW" in tag else BLUE
        b.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": s + len(tag) + 2}, "textStyle": {"bold": True, "italic": True, "foregroundColor": {"color": {"rgbColor": tag_color}}}, "fields": "bold,italic,foregroundColor"}})
        b.text("\n")

        # Analytical Questions
        b.h2("Analytical Questions")
        for i, q in enumerate(dept['questions'], 1):
            b.numbered(i, q)
        b.text("\n")

        # Insight Ideas with Details
        b.h2("Insight Ideas")
        for title, description in dept['insights']:
            b.h3(f"▸  {title}")
            b.text(f"{description}\n\n")

        # Insight Brief Template
        b.h2("Insight Brief Template")
        b.italic_gray("Use this template to document each insight once data is available")
        b.text("\n")
        b.placeholder_field("Insight Title")
        b.placeholder_field("Relevant Department")
        b.placeholder_field("Confidence Level (High / Medium / Preliminary)")
        b.placeholder_field("Observation (What Data Tell Us)")
        b.placeholder_field("Supporting Evidence")
        b.placeholder_field("Root Cause Analysis")
        b.placeholder_field("Business Impact (Financial)", RED)
        b.placeholder_field("Recommended Actions", GREEN)
        b.placeholder_field("Strategic Importance", BLUE)
        b.text("\n")

        # KPI Benchmarks
        b.h2("KPI Benchmarks (Industry Standards)")
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

    # ─── CROSS-DEPARTMENT ───
    b.h1("🔗  Cross-Department Insight Ideas")
    b.italic_gray("These insights span multiple departments. They are typically the highest-value opportunities because no single department owns them.")
    b.text("\n\n")

    for cd in CROSS_DEPT:
        b.h2(f"🔗  {cd['title']}")
        b.field("Departments", cd['depts'])
        b.field("Analytical Question", cd['question'])
        b.text(f"\n{cd['description']}\n\n")
        b.thin_divider()

    # Footer
    b.divider()
    b.centered("End of Additional Insight Ideas | TopMed Insights Bank | March 2026", lambda s, e: [
        b.styles.append({"updateTextStyle": {"range": {"startIndex": s, "endIndex": e}, "textStyle": {"italic": True, "foregroundColor": {"color": {"rgbColor": GRAY}}}, "fields": "italic,foregroundColor"}}),
    ])

    # ─── SEND ───
    all_reqs = b.get_all()
    print(f"Total requests: {len(all_reqs)}")

    batch_size = 80
    for i in range(0, len(all_reqs), batch_size):
        batch = all_reqs[i:i+batch_size]
        api_call(f'https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate',
                 {"requests": batch}, token)
        print(f"  Batch {i//batch_size + 1}: {len(batch)} applied")

    print(f"\n✅ Document ready: https://docs.google.com/document/d/{doc_id}/edit")

if __name__ == '__main__':
    main()
