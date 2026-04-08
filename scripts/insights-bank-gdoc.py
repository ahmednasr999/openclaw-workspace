#!/usr/bin/env python3
"""
Generate premium-formatted TopMed Insights Bank Google Doc.
Uses native Google Docs API: headings, bold, tables, colors.
"""
import json, sys, urllib.request, urllib.parse, os

def get_access_token():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ahmed-google.json')
    with open(config_path) as f:
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

def api_call(url, data, token, method='POST'):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }, method=method)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

# ─── CONTENT STRUCTURE ───

SECTIONS = [
    {
        "area": "Emergency Department (ED) Insights Opportunities",
        "icon": "🚨",
        "is_new": True,
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
        ]
    },
    {
        "area": "Inpatient Department (IPD) Insights Opportunities",
        "icon": "🏥",
        "is_new": True,
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
        ]
    },
    {
        "area": "Pharmacy Insights Opportunities",
        "icon": "💊",
        "is_new": True,
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
        ]
    },
    {
        "area": "Patient Experience Insights Opportunities",
        "icon": "⭐",
        "is_new": True,
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
        ]
    },
    {
        "area": "Supply Chain & Procurement Insights Opportunities",
        "icon": "📦",
        "is_new": True,
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
        ]
    },
    {
        "area": "Quality & Clinical Safety Insights Opportunities",
        "icon": "🛡️",
        "is_new": True,
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
        ]
    },
]

# Expansions to existing areas
EXPANSIONS = [
    {
        "area": "Radiology Insights Opportunities (Additional)",
        "icon": "📡",
        "questions": [
            "What is the radiology report turnaround time, and does it vary by modality?",
            "Are repeat/rejected imaging studies increasing costs?",
        ],
        "insights": [
            "Radiology Report Turnaround Time by Modality",
            "Radiology Repeat Study Rate and Quality Impact",
        ]
    },
    {
        "area": "Laboratory Insights Opportunities (Additional)",
        "icon": "🔬",
        "questions": [
            "Are critical value notification times meeting clinical standards?",
            "Is send-out testing volume growing when in-house capacity exists?",
        ],
        "insights": [
            "Critical Lab Value Notification Compliance",
            "In-House vs. Send-Out Test Migration Opportunity",
        ]
    },
    {
        "area": "OPD Insights Opportunities (Additional)",
        "icon": "🩺",
        "questions": [
            "Are new patient acquisition rates growing or stagnating by specialty?",
            "What is the doctor productivity rate (patients per clinical hour)?",
        ],
        "insights": [
            "New Patient Acquisition Rate by Specialty",
            "Doctor Productivity and Clinic Slot Utilization",
        ]
    },
    {
        "area": "Revenue Cycle Insights Opportunities (Additional)",
        "icon": "💰",
        "questions": [
            "What is the average days in accounts receivable (AR) by payer?",
            "Are self-pay collection rates declining?",
            "Is payer mix shifting in a way that impacts overall margin?",
        ],
        "insights": [
            "Accounts Receivable Aging by Payer Category",
            "Self-Pay Collection Rate Decline",
            "Payer Mix Shift and Margin Impact Analysis",
        ]
    },
    {
        "area": "Operational Efficiency Insights Opportunities (Additional)",
        "icon": "⚙️",
        "questions": [
            "Is overtime spending proportional to patient volume increases?",
            "Are energy and facility costs per patient bed-day within benchmark?",
        ],
        "insights": [
            "Overtime Cost vs. Patient Volume Correlation",
            "Facility Cost Per Occupied Bed-Day",
        ]
    },
]

def build_requests():
    """Build all Google Docs API batchUpdate requests."""
    requests = []
    idx = 1  # Current document index (1-based after empty doc creation)
    styles = []  # Collect styling requests to apply after all text is inserted
    
    # ─── TITLE ───
    title = "TopMed Insights Bank\nAdditional Insight Ideas\n"
    requests.append({"insertText": {"location": {"index": idx}, "text": title}})
    styles.append({"updateParagraphStyle": {
        "range": {"startIndex": idx, "endIndex": idx + len("TopMed Insights Bank")},
        "paragraphStyle": {"namedStyleType": "HEADING_1", "alignment": "CENTER"},
        "fields": "namedStyleType,alignment"
    }})
    styles.append({"updateTextStyle": {
        "range": {"startIndex": idx, "endIndex": idx + len("TopMed Insights Bank")},
        "textStyle": {"bold": True, "fontSize": {"magnitude": 22, "unit": "PT"},
                       "foregroundColor": {"color": {"rgbColor": {"red": 0.15, "green": 0.3, "blue": 0.53}}}},
        "fields": "bold,fontSize,foregroundColor"
    }})
    sub_start = idx + len("TopMed Insights Bank\n")
    sub_text = "Additional Insight Ideas"
    styles.append({"updateParagraphStyle": {
        "range": {"startIndex": sub_start, "endIndex": sub_start + len(sub_text)},
        "paragraphStyle": {"namedStyleType": "HEADING_2", "alignment": "CENTER"},
        "fields": "namedStyleType,alignment"
    }})
    styles.append({"updateTextStyle": {
        "range": {"startIndex": sub_start, "endIndex": sub_start + len(sub_text)},
        "textStyle": {"italic": True, "fontSize": {"magnitude": 14, "unit": "PT"},
                       "foregroundColor": {"color": {"rgbColor": {"red": 0.4, "green": 0.4, "blue": 0.4}}}},
        "fields": "italic,fontSize,foregroundColor"
    }})
    idx += len(title)
    
    # ─── METADATA LINE ───
    meta = "Prepared by: PMO Office | March 2026 | Confidential\n\n"
    requests.append({"insertText": {"location": {"index": idx}, "text": meta}})
    meta_text = "Prepared by: PMO Office | March 2026 | Confidential"
    styles.append({"updateTextStyle": {
        "range": {"startIndex": idx, "endIndex": idx + len(meta_text)},
        "textStyle": {"italic": True, "fontSize": {"magnitude": 10, "unit": "PT"},
                       "foregroundColor": {"color": {"rgbColor": {"red": 0.5, "green": 0.5, "blue": 0.5}}}},
        "fields": "italic,fontSize,foregroundColor"
    }})
    styles.append({"updateParagraphStyle": {
        "range": {"startIndex": idx, "endIndex": idx + len(meta_text)},
        "paragraphStyle": {"alignment": "CENTER"},
        "fields": "alignment"
    }})
    idx += len(meta)

    # ─── DIVIDER ───
    divider = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    requests.append({"insertText": {"location": {"index": idx}, "text": divider}})
    styles.append({"updateTextStyle": {
        "range": {"startIndex": idx, "endIndex": idx + len(divider) - 2},
        "textStyle": {"foregroundColor": {"color": {"rgbColor": {"red": 0.15, "green": 0.3, "blue": 0.53}}}},
        "fields": "foregroundColor"
    }})
    idx += len(divider)

    # ─── PART 1 HEADER ───
    part1 = "PART 1: NEW INSIGHT AREAS\n\n"
    requests.append({"insertText": {"location": {"index": idx}, "text": part1}})
    styles.append({"updateParagraphStyle": {
        "range": {"startIndex": idx, "endIndex": idx + len("PART 1: NEW INSIGHT AREAS")},
        "paragraphStyle": {"namedStyleType": "HEADING_1"},
        "fields": "namedStyleType"
    }})
    styles.append({"updateTextStyle": {
        "range": {"startIndex": idx, "endIndex": idx + len("PART 1: NEW INSIGHT AREAS")},
        "textStyle": {"bold": True, "fontSize": {"magnitude": 16, "unit": "PT"},
                       "foregroundColor": {"color": {"rgbColor": {"red": 0.15, "green": 0.3, "blue": 0.53}}}},
        "fields": "bold,fontSize,foregroundColor"
    }})
    idx += len(part1)

    # ─── NEW AREAS ───
    for section in SECTIONS:
        idx = add_section(requests, styles, idx, section)
    
    # ─── PART 2 HEADER ───
    part2 = "\nPART 2: EXPANSIONS TO EXISTING AREAS\n\n"
    requests.append({"insertText": {"location": {"index": idx}, "text": part2}})
    p2_start = idx + 1  # skip the \n
    p2_text = "PART 2: EXPANSIONS TO EXISTING AREAS"
    styles.append({"updateParagraphStyle": {
        "range": {"startIndex": p2_start, "endIndex": p2_start + len(p2_text)},
        "paragraphStyle": {"namedStyleType": "HEADING_1"},
        "fields": "namedStyleType"
    }})
    styles.append({"updateTextStyle": {
        "range": {"startIndex": p2_start, "endIndex": p2_start + len(p2_text)},
        "textStyle": {"bold": True, "fontSize": {"magnitude": 16, "unit": "PT"},
                       "foregroundColor": {"color": {"rgbColor": {"red": 0.15, "green": 0.3, "blue": 0.53}}}},
        "fields": "bold,fontSize,foregroundColor"
    }})
    idx += len(part2)

    # ─── EXPANSIONS ───
    for section in EXPANSIONS:
        idx = add_section(requests, styles, idx, section)
    
    return requests + styles

def add_section(requests, styles, idx, section):
    """Add a single insight area section."""
    # Section heading
    heading = f"{section['icon']}  {section['area']}\n\n"
    requests.append({"insertText": {"location": {"index": idx}, "text": heading}})
    h_end = idx + len(heading) - 2
    styles.append({"updateParagraphStyle": {
        "range": {"startIndex": idx, "endIndex": h_end},
        "paragraphStyle": {"namedStyleType": "HEADING_2"},
        "fields": "namedStyleType"
    }})
    styles.append({"updateTextStyle": {
        "range": {"startIndex": idx, "endIndex": h_end},
        "textStyle": {"bold": True, "fontSize": {"magnitude": 14, "unit": "PT"},
                       "foregroundColor": {"color": {"rgbColor": {"red": 0.17, "green": 0.33, "blue": 0.53}}}},
        "fields": "bold,fontSize,foregroundColor"
    }})
    idx += len(heading)
    
    # Questions sub-header
    q_header = "Analytical Questions:\n"
    requests.append({"insertText": {"location": {"index": idx}, "text": q_header}})
    styles.append({"updateTextStyle": {
        "range": {"startIndex": idx, "endIndex": idx + len("Analytical Questions:")},
        "textStyle": {"bold": True, "italic": True, "fontSize": {"magnitude": 11, "unit": "PT"}},
        "fields": "bold,italic,fontSize"
    }})
    idx += len(q_header)
    
    # Questions
    for i, q in enumerate(section["questions"], 1):
        q_line = f"  {i}.  {q}\n"
        requests.append({"insertText": {"location": {"index": idx}, "text": q_line}})
        # Bold the number
        num_text = f"  {i}."
        styles.append({"updateTextStyle": {
            "range": {"startIndex": idx, "endIndex": idx + len(num_text)},
            "textStyle": {"bold": True},
            "fields": "bold"
        }})
        idx += len(q_line)
    
    # Spacing
    requests.append({"insertText": {"location": {"index": idx}, "text": "\n"}})
    idx += 1

    # Insights sub-header
    i_header = "Insight Titles:\n"
    requests.append({"insertText": {"location": {"index": idx}, "text": i_header}})
    styles.append({"updateTextStyle": {
        "range": {"startIndex": idx, "endIndex": idx + len("Insight Titles:")},
        "textStyle": {"bold": True, "italic": True, "fontSize": {"magnitude": 11, "unit": "PT"},
                       "foregroundColor": {"color": {"rgbColor": {"red": 0.0, "green": 0.4, "blue": 0.2}}}},
        "fields": "bold,italic,fontSize,foregroundColor"
    }})
    idx += len(i_header)
    
    # Insight titles
    for ins in section["insights"]:
        i_line = f"  ▸  {ins}\n"
        requests.append({"insertText": {"location": {"index": idx}, "text": i_line}})
        # Style the insight title
        styles.append({"updateTextStyle": {
            "range": {"startIndex": idx + 5, "endIndex": idx + len(i_line) - 1},
            "textStyle": {"bold": True, "foregroundColor": {"color": {"rgbColor": {"red": 0.13, "green": 0.13, "blue": 0.13}}}},
            "fields": "bold,foregroundColor"
        }})
        idx += len(i_line)
    
    # Section divider
    div = "\n─────────────────────────────────────────────\n\n"
    requests.append({"insertText": {"location": {"index": idx}, "text": div}})
    styles.append({"updateTextStyle": {
        "range": {"startIndex": idx, "endIndex": idx + len(div) - 2},
        "textStyle": {"foregroundColor": {"color": {"rgbColor": {"red": 0.8, "green": 0.8, "blue": 0.8}}}},
        "fields": "foregroundColor"
    }})
    idx += len(div)
    
    return idx

def main():
    token = get_access_token()
    
    # Create the document
    doc = api_call('https://docs.googleapis.com/v1/documents',
                   {"title": "TopMed Insights Bank - Additional Insight Ideas (March 2026)"},
                   token)
    doc_id = doc['documentId']
    print(f"Created doc: {doc_id}")
    
    # Build all requests
    reqs = build_requests()
    
    # Send in batches (API limit is ~100 requests per batch)
    batch_size = 80
    for i in range(0, len(reqs), batch_size):
        batch = reqs[i:i+batch_size]
        api_call(f'https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate',
                 {"requests": batch}, token)
        print(f"  Batch {i//batch_size + 1}: {len(batch)} requests applied")
    
    url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print(f"\n✅ Document ready: {url}")
    return url

if __name__ == '__main__':
    main()
