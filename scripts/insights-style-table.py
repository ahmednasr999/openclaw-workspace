#!/usr/bin/env python3
"""Style the Priority Matrix table with colors, bold, backgrounds."""
import json, urllib.request, urllib.parse, os

DOC_ID = "1vnMHyow-d_i-YaxhM48KFTPMqi4ryn83GoS2c48EO7Q"
TABLE_START = 1164  # from inspection

NAVY = {"red": 0.15, "green": 0.3, "blue": 0.53}
WHITE_RGB = {"red": 1.0, "green": 1.0, "blue": 1.0}
LIGHT_BG = {"red": 0.94, "green": 0.95, "blue": 0.97}
RED_RGB = {"red": 0.75, "green": 0.15, "blue": 0.15}
GREEN_RGB = {"red": 0.0, "green": 0.4, "blue": 0.2}
ORANGE_RGB = {"red": 0.83, "green": 0.5, "blue": 0.0}
DARK = {"red": 0.13, "green": 0.13, "blue": 0.13}

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

def get_doc(token):
    req = urllib.request.Request(
        f'https://docs.googleapis.com/v1/documents/{DOC_ID}',
        headers={'Authorization': f'Bearer {token}'}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

MATRIX_DATA = [
    ["#", "Priority", "Insight", "Revenue Impact", "Data Readiness", "Complexity"],
    ["1", "🔴", "AR Aging by Payer Category", "SAR 18M", "Available Now", "Medium Effort"],
    ["2", "🔴", "OPD Slot Utilization", "SAR 8.4M", "Available Now", "Quick Win"],
    ["3", "🔴", "Cross-Hospital Procurement Variance", "SAR 5.2M", "Available Now", "Medium Effort"],
    ["4", "🔴", "Delayed Discharge / Bed Turnover", "SAR 4.3M", "Available Now", "Medium Effort"],
    ["5", "🔴", "Patient No-Show Patterns", "SAR 10.7M", "Available Now", "Quick Win"],
    ["6", "🟡", "Medication Substitution", "SAR 2.5-3.8M", "Needs Collection", "Medium Effort"],
    ["7", "🟡", "ED LWBS Rate", "SAR 2.1M", "Available Now", "Quick Win"],
    ["8", "🟡", "Overtime vs. Volume", "SAR 3.6M", "Available Now", "Medium Effort"],
    ["9", "🟡", "Radiology Report TAT", "SAR 1.8M", "Available Now", "Quick Win"],
    ["10", "🟢", "Send-Out Test Migration", "SAR 1.4M", "Needs Collection", "Major Initiative"],
    ["11", "🟢", "Near-Miss Reporting Culture", "Risk Mitigation", "Needs Collection", "Major Initiative"],
    ["12", "🟢", "Digital Reputation vs Quality", "Brand Value", "Needs Integration", "Medium Effort"],
]

def main():
    token = get_access_token()
    doc = get_doc(token)
    
    # Find table
    table = None
    for elem in doc['body']['content']:
        if 'table' in elem and elem.get('startIndex', 0) == TABLE_START:
            table = elem['table']
            break
    
    if not table:
        print("Table not found!")
        return
    
    styles = []
    
    # ─── Header row: navy background, white bold text ───
    for col_idx in range(6):
        # Background
        styles.append({"updateTableCellStyle": {
            "tableRange": {
                "tableCellLocation": {
                    "tableStartLocation": {"index": TABLE_START},
                    "rowIndex": 0,
                    "columnIndex": col_idx
                },
                "rowSpan": 1,
                "columnSpan": 1
            },
            "tableCellStyle": {"backgroundColor": {"color": {"rgbColor": NAVY}}},
            "fields": "backgroundColor"
        }})
        
        # Text style
        cell = table['tableRows'][0]['tableCells'][col_idx]
        para = cell['content'][0]['paragraph']
        si = para['elements'][0]['startIndex']
        ei = para['elements'][-1]['endIndex'] - 1
        styles.append({"updateTextStyle": {
            "range": {"startIndex": si, "endIndex": ei},
            "textStyle": {"bold": True, "fontSize": {"magnitude": 10, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": WHITE_RGB}}},
            "fields": "bold,fontSize,foregroundColor"
        }})
    
    # ─── Data rows ───
    for row_idx in range(1, 13):
        row = table['tableRows'][row_idx]
        row_data = MATRIX_DATA[row_idx]
        
        # Alternate row background
        if row_idx % 2 == 0:
            for col_idx in range(6):
                styles.append({"updateTableCellStyle": {
                    "tableRange": {
                        "tableCellLocation": {
                            "tableStartLocation": {"index": TABLE_START},
                            "rowIndex": row_idx,
                            "columnIndex": col_idx
                        },
                        "rowSpan": 1,
                        "columnSpan": 1
                    },
                    "tableCellStyle": {"backgroundColor": {"color": {"rgbColor": LIGHT_BG}}},
                    "fields": "backgroundColor"
                }})
        
        for col_idx in range(6):
            cell = row['tableCells'][col_idx]
            para = cell['content'][0]['paragraph']
            si = para['elements'][0]['startIndex']
            ei = para['elements'][-1]['endIndex'] - 1
            
            if si >= ei:
                continue
            
            bold = False
            color = DARK
            size = 9
            
            if col_idx == 0:  # Rank
                bold = True
                color = NAVY
            elif col_idx == 2:  # Insight
                bold = True
                color = DARK
            elif col_idx == 3:  # Revenue
                bold = True
                color = RED_RGB
            elif col_idx == 4:  # Data readiness
                text = row_data[col_idx]
                color = GREEN_RGB if text == "Available Now" else ORANGE_RGB
            elif col_idx == 5:  # Complexity
                text = row_data[col_idx]
                if text == "Quick Win":
                    color = GREEN_RGB
                elif text == "Major Initiative":
                    color = RED_RGB
                else:
                    color = ORANGE_RGB
            
            styles.append({"updateTextStyle": {
                "range": {"startIndex": si, "endIndex": ei},
                "textStyle": {"bold": bold, "fontSize": {"magnitude": size, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": color}}},
                "fields": "bold,fontSize,foregroundColor"
            }})
    
    # ─── Table borders ───
    # Set thin borders on entire table
    for row_idx in range(13):
        for col_idx in range(6):
            styles.append({"updateTableCellStyle": {
                "tableRange": {
                    "tableCellLocation": {
                        "tableStartLocation": {"index": TABLE_START},
                        "rowIndex": row_idx,
                        "columnIndex": col_idx
                    },
                    "rowSpan": 1,
                    "columnSpan": 1
                },
                "tableCellStyle": {
                    "borderTop": {"color": {"color": {"rgbColor": {"red": 0.85, "green": 0.85, "blue": 0.85}}}, "width": {"magnitude": 0.5, "unit": "PT"}, "dashStyle": "SOLID"},
                    "borderBottom": {"color": {"color": {"rgbColor": {"red": 0.85, "green": 0.85, "blue": 0.85}}}, "width": {"magnitude": 0.5, "unit": "PT"}, "dashStyle": "SOLID"},
                    "borderLeft": {"color": {"color": {"rgbColor": {"red": 0.85, "green": 0.85, "blue": 0.85}}}, "width": {"magnitude": 0.5, "unit": "PT"}, "dashStyle": "SOLID"},
                    "borderRight": {"color": {"color": {"rgbColor": {"red": 0.85, "green": 0.85, "blue": 0.85}}}, "width": {"magnitude": 0.5, "unit": "PT"}, "dashStyle": "SOLID"},
                    "paddingTop": {"magnitude": 3, "unit": "PT"},
                    "paddingBottom": {"magnitude": 3, "unit": "PT"},
                    "paddingLeft": {"magnitude": 5, "unit": "PT"},
                    "paddingRight": {"magnitude": 5, "unit": "PT"},
                },
                "fields": "borderTop,borderBottom,borderLeft,borderRight,paddingTop,paddingBottom,paddingLeft,paddingRight"
            }})
    
    print(f"Total style requests: {len(styles)}")
    
    batch_size = 50
    for i in range(0, len(styles), batch_size):
        batch = styles[i:i+batch_size]
        api_call(f'https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate',
                 {"requests": batch}, token)
        print(f"  Batch {i//batch_size + 1}: {len(batch)} applied")
    
    print(f"\n✅ Table styled: https://docs.google.com/document/d/{DOC_ID}/edit")

if __name__ == '__main__':
    main()
