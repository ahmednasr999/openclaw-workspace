#!/usr/bin/env python3
"""
Replace the plain-text Priority Matrix with a native Google Docs table.
"""
import json, urllib.request, urllib.parse, os

DOC_ID = "1vnMHyow-d_i-YaxhM48KFTPMqi4ryn83GoS2c48EO7Q"

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

def api_call(url, data, token, method='POST'):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }, method=method)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def get_doc(token):
    req = urllib.request.Request(
        f'https://docs.googleapis.com/v1/documents/{DOC_ID}',
        headers={'Authorization': f'Bearer {token}'}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

NAVY = {"red": 0.15, "green": 0.3, "blue": 0.53}
WHITE_RGB = {"red": 1.0, "green": 1.0, "blue": 1.0}
LIGHT_BG = {"red": 0.94, "green": 0.95, "blue": 0.97}
RED_RGB = {"red": 0.75, "green": 0.15, "blue": 0.15}
GREEN_RGB = {"red": 0.0, "green": 0.4, "blue": 0.2}
ORANGE_RGB = {"red": 0.83, "green": 0.5, "blue": 0.0}
DARK = {"red": 0.13, "green": 0.13, "blue": 0.13}

MATRIX = [
    ("1", "🔴", "AR Aging by Payer Category", "SAR 18M", "Available Now", "Medium Effort"),
    ("2", "🔴", "OPD Slot Utilization", "SAR 8.4M", "Available Now", "Quick Win"),
    ("3", "🔴", "Cross-Hospital Procurement Variance", "SAR 5.2M", "Available Now", "Medium Effort"),
    ("4", "🔴", "Delayed Discharge / Bed Turnover", "SAR 4.3M", "Available Now", "Medium Effort"),
    ("5", "🔴", "Patient No-Show Patterns", "SAR 10.7M", "Available Now", "Quick Win"),
    ("6", "🟡", "Medication Substitution", "SAR 2.5-3.8M", "Needs Collection", "Medium Effort"),
    ("7", "🟡", "ED LWBS Rate", "SAR 2.1M", "Available Now", "Quick Win"),
    ("8", "🟡", "Overtime vs. Volume", "SAR 3.6M", "Available Now", "Medium Effort"),
    ("9", "🟡", "Radiology Report TAT", "SAR 1.8M", "Available Now", "Quick Win"),
    ("10", "🟢", "Send-Out Test Migration", "SAR 1.4M", "Needs Collection", "Major Initiative"),
    ("11", "🟢", "Near-Miss Reporting Culture", "Risk Mitigation", "Needs Collection", "Major Initiative"),
    ("12", "🟢", "Digital Reputation vs Quality", "Brand Value", "Needs Integration", "Medium Effort"),
]

def find_matrix_range(doc):
    """Find the start and end indices of the plain-text priority matrix section."""
    body = doc['body']['content']
    
    # Find "Rank | Insight" header line and the legend line
    start_idx = None
    end_idx = None
    
    full_text = ""
    for elem in body:
        if 'paragraph' in elem:
            for run in elem['paragraph'].get('elements', []):
                tc = run.get('textRun', {}).get('content', '')
                full_text += tc
    
    # Find the header line
    header_pos = full_text.find("Rank | Insight")
    if header_pos == -1:
        print("ERROR: Could not find 'Rank | Insight' header")
        return None, None
    
    # Find the legend line (end marker)
    legend_pos = full_text.find("🔴 = Start Immediately")
    if legend_pos == -1:
        print("ERROR: Could not find legend line")
        return None, None
    
    # Find end of legend line
    legend_end = full_text.find("\n", legend_pos)
    if legend_end == -1:
        legend_end = legend_pos + 80
    
    # +1 because doc indices are 1-based
    # We need to account for the body start offset
    # Actually, let's iterate through elements to find exact indices
    
    start_idx = None
    end_idx = None
    
    for elem in body:
        if 'paragraph' in elem:
            for run in elem['paragraph'].get('elements', []):
                tc = run.get('textRun', {}).get('content', '')
                si = run.get('startIndex', 0)
                ei = run.get('endIndex', 0)
                if "Rank | Insight" in tc and start_idx is None:
                    start_idx = si
                if "= Start Immediately" in tc or "= Start Immediately" in tc:
                    end_idx = ei
    
    return start_idx, end_idx

def main():
    token = get_access_token()
    doc = get_doc(token)
    
    start_idx, end_idx = find_matrix_range(doc)
    if start_idx is None:
        print("Could not locate matrix text. Aborting.")
        return
    
    print(f"Found matrix text: index {start_idx} to {end_idx}")
    
    # Step 1: Delete the old plain-text matrix
    requests = []
    requests.append({
        "deleteContentRange": {
            "range": {"startIndex": start_idx, "endIndex": end_idx}
        }
    })
    
    api_call(f'https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate',
             {"requests": requests}, token)
    print("Deleted old plain-text matrix")
    
    # Step 2: Insert table at that position
    rows = len(MATRIX) + 1  # +1 for header
    cols = 6  # Rank, Priority, Insight, Revenue Impact, Data Readiness, Complexity
    
    requests2 = []
    requests2.append({
        "insertTable": {
            "rows": rows,
            "columns": cols,
            "location": {"index": start_idx}
        }
    })
    
    api_call(f'https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate',
             {"requests": requests2}, token)
    print(f"Inserted {rows}x{cols} table")
    
    # Step 3: Read doc again to get table cell indices
    doc = get_doc(token)
    
    # Find the table element
    table = None
    for elem in doc['body']['content']:
        if 'table' in elem:
            if elem.get('startIndex', 0) >= start_idx - 5:
                table = elem['table']
                table_start = elem['startIndex']
                break
    
    if table is None:
        print("ERROR: Could not find inserted table")
        return
    
    print(f"Found table at index {table_start}")
    
    # Build cell content + styling requests
    headers = ["#", "Priority", "Insight", "Revenue Impact", "Data Readiness", "Complexity"]
    
    all_data = [headers] + [[r, p, i, rev, d, c] for r, p, i, rev, d, c in MATRIX]
    
    requests3 = []
    styles3 = []
    
    for row_idx, row_data in enumerate(all_data):
        table_row = table['tableRows'][row_idx]
        for col_idx, cell_text in enumerate(row_data):
            cell = table_row['tableCells'][col_idx]
            # Get the paragraph inside the cell
            cell_content = cell['content']
            if cell_content:
                para = cell_content[0]
                if 'paragraph' in para:
                    elements = para['paragraph']['elements']
                    if elements:
                        insert_idx = elements[0]['startIndex']
                        
                        # Insert text
                        requests3.append({
                            "insertText": {
                                "location": {"index": insert_idx},
                                "text": cell_text
                            }
                        })
    
    # Apply text insertions (must be done in reverse order to maintain indices)
    # Actually, let's do row by row, bottom to top, right to left
    requests3_sorted = []
    for row_idx in range(len(all_data) - 1, -1, -1):
        table_row = table['tableRows'][row_idx]
        for col_idx in range(len(all_data[row_idx]) - 1, -1, -1):
            cell = table_row['tableCells'][col_idx]
            cell_content = cell['content']
            if cell_content:
                para = cell_content[0]
                if 'paragraph' in para:
                    elements = para['paragraph']['elements']
                    if elements:
                        insert_idx = elements[0]['startIndex']
                        cell_text = all_data[row_idx][col_idx]
                        
                        requests3_sorted.append({
                            "insertText": {
                                "location": {"index": insert_idx},
                                "text": cell_text
                            }
                        })
    
    api_call(f'https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate',
             {"requests": requests3_sorted}, token)
    print("Inserted cell text")
    
    # Step 4: Read doc again for styling
    doc = get_doc(token)
    
    # Find table again
    table = None
    for elem in doc['body']['content']:
        if 'table' in elem:
            if elem.get('startIndex', 0) >= start_idx - 5:
                table = elem['table']
                break
    
    if table is None:
        print("ERROR: Could not find table for styling")
        return
    
    styles = []
    
    # Style header row
    header_row = table['tableRows'][0]
    for col_idx in range(cols):
        cell = header_row['tableCells'][col_idx]
        cell_content = cell['content']
        if cell_content and 'paragraph' in cell_content[0]:
            elements = cell_content[0]['paragraph']['elements']
            if elements:
                si = elements[0]['startIndex']
                ei = elements[-1]['endIndex'] - 1  # exclude newline
                
                # Bold white text
                styles.append({"updateTextStyle": {
                    "range": {"startIndex": si, "endIndex": ei},
                    "textStyle": {"bold": True, "fontSize": {"magnitude": 10, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": WHITE_RGB}}},
                    "fields": "bold,fontSize,foregroundColor"
                }})
        
        # Navy background for header cells
        styles.append({"updateTableCellStyle": {
            "tableRange": {
                "tableCellLocation": {"tableStartLocation": {"index": table['tableRows'][0]['tableCells'][0]['content'][0]['paragraph']['elements'][0]['startIndex'] - 4}, "rowIndex": 0, "columnIndex": col_idx},
                "rowSpan": 1, "columnSpan": 1
            },
            "tableCellStyle": {"backgroundColor": {"color": {"rgbColor": NAVY}}},
            "fields": "backgroundColor"
        }})
    
    # Style data rows
    for row_idx in range(1, len(all_data)):
        row = table['tableRows'][row_idx]
        for col_idx in range(cols):
            cell = row['tableCells'][col_idx]
            cell_content = cell['content']
            if cell_content and 'paragraph' in cell_content[0]:
                elements = cell_content[0]['paragraph']['elements']
                if elements:
                    si = elements[0]['startIndex']
                    ei = elements[-1]['endIndex'] - 1
                    
                    # Default text style
                    text_color = DARK
                    bold = False
                    
                    if col_idx == 2:  # Insight name
                        bold = True
                    elif col_idx == 3:  # Revenue
                        text_color = RED_RGB
                        bold = True
                    elif col_idx == 4:  # Data readiness
                        cell_text = all_data[row_idx][col_idx]
                        text_color = GREEN_RGB if cell_text == "Available Now" else ORANGE_RGB
                    
                    styles.append({"updateTextStyle": {
                        "range": {"startIndex": si, "endIndex": ei},
                        "textStyle": {"bold": bold, "fontSize": {"magnitude": 9, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": text_color}}},
                        "fields": "bold,fontSize,foregroundColor"
                    }})
        
        # Alternate row background
        if row_idx % 2 == 0:
            for col_idx in range(cols):
                styles.append({"updateTableCellStyle": {
                    "tableRange": {
                        "tableCellLocation": {"tableStartLocation": {"index": table['tableRows'][0]['tableCells'][0]['content'][0]['paragraph']['elements'][0]['startIndex'] - 4}, "rowIndex": row_idx, "columnIndex": col_idx},
                        "rowSpan": 1, "columnSpan": 1
                    },
                    "tableCellStyle": {"backgroundColor": {"color": {"rgbColor": LIGHT_BG}}},
                    "fields": "backgroundColor"
                }})
    
    # Apply styles in batches
    batch_size = 60
    for i in range(0, len(styles), batch_size):
        batch = styles[i:i+batch_size]
        api_call(f'https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate',
                 {"requests": batch}, token)
        print(f"  Style batch {i//batch_size + 1}: {len(batch)} applied")
    
    print(f"\n✅ Priority Matrix table added: https://docs.google.com/document/d/{DOC_ID}/edit")

if __name__ == '__main__':
    main()
