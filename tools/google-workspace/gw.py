#!/usr/bin/env python3
"""
Google Workspace CLI - Pure Python 3 stdlib wrapper for Gmail, Calendar, Drive, Sheets, Docs, Slides
Uses OAuth refresh tokens directly (no external dependencies)
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

CREDENTIALS_FILE = "/root/.openclaw/workspace/config/ahmed-google.json"
TOKEN_CACHE_FILE = "/root/.openclaw/workspace/tools/google-workspace/.token_cache.json"

TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API = "https://gmail.googleapis.com/gmail/v1"
CALENDAR_API = "https://www.googleapis.com/calendar/v3"
DRIVE_API = "https://www.googleapis.com/drive/v3"
SHEETS_API = "https://sheets.googleapis.com/v4"
DOCS_API = "https://docs.googleapis.com/v1"


def load_credentials():
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: Credentials file not found: {CREDENTIALS_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(CREDENTIALS_FILE, "r") as f:
        return json.load(f)


def load_token_cache():
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, "r") as f:
                cache = json.load(f)
            if cache.get("expires_at", 0) > time.time() + 60:
                return cache.get("access_token")
        except Exception:
            pass
    return None


def save_token_cache(access_token, expires_in):
    cache = {"access_token": access_token, "expires_at": time.time() + expires_in}
    os.makedirs(os.path.dirname(TOKEN_CACHE_FILE), exist_ok=True)
    with open(TOKEN_CACHE_FILE, "w") as f:
        json.dump(cache, f)


def refresh_access_token(credentials):
    params = urllib.parse.urlencode({
        "client_id": credentials["client_id"],
        "client_secret": credentials["client_secret"],
        "refresh_token": credentials["refresh_token"],
        "grant_type": "refresh_token"
    })
    data = params.encode("utf-8")
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req) as response:
            token_data = json.load(response)
            access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            save_token_cache(access_token, expires_in)
            return access_token
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"Error refreshing token: {e.code} - {error_body}", file=sys.stderr)
        sys.exit(1)


def get_access_token():
    credentials = load_credentials()
    cached_token = load_token_cache()
    if cached_token:
        return cached_token
    return refresh_access_token(credentials)


def api_call(method, url, body=None, headers=None, retry_on_401=True):
    access_token = get_access_token()
    req_headers = {"Authorization": f"Bearer {access_token}"}
    if headers:
        req_headers.update(headers)
    data = None
    if body is not None:
        if isinstance(body, str):
            data = body.encode("utf-8")
        else:
            data = json.dumps(body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=req_headers)
    try:
        with urllib.request.urlopen(req) as response:
            content = response.read().decode("utf-8")
            if content:
                return json.loads(content)
            return {}
    except urllib.error.HTTPError as e:
        if e.code == 401 and retry_on_401:
            if os.path.exists(TOKEN_CACHE_FILE):
                os.remove(TOKEN_CACHE_FILE)
            new_token = get_access_token()
            req.headers["Authorization"] = f"Bearer {new_token}"
            with urllib.request.urlopen(req) as response:
                content = response.read().decode("utf-8")
                if content:
                    return json.loads(content)
                return {}
        else:
            try:
                error_body = json.loads(e.read().decode("utf-8"))
                msg = error_body.get("error", {})
                if isinstance(msg, dict):
                    msg = msg.get("message", str(e))
                print(f"API Error: {msg}", file=sys.stderr)
            except Exception:
                print(f"API Error: {e.code} - {e.reason}", file=sys.stderr)
            sys.exit(1)


def fmt_json(data):
    return json.dumps(data, indent=2)


# ===== GMAIL =====

def gmail_search(query, max_results=10, output_json=False):
    url = f"{GMAIL_API}/users/me/messages?q={urllib.parse.quote(query)}&maxResults={max_results}"
    result = api_call("GET", url)
    messages = result.get("messages", [])
    if not messages:
        print("No messages found")
        return
    if output_json:
        details = []
        for msg in messages:
            msg_url = f"{GMAIL_API}/users/me/messages/{msg['id']}?format=full"
            details.append(api_call("GET", msg_url))
        print(fmt_json(details))
        return
    for msg in messages:
        msg_url = f"{GMAIL_API}/users/me/messages/{msg['id']}?format=full"
        msg_data = api_call("GET", msg_url)
        hdrs = msg_data.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in hdrs if h["name"].lower() == "subject"), "(No Subject)")
        from_addr = next((h["value"] for h in hdrs if h["name"].lower() == "from"), "")
        date = next((h["value"] for h in hdrs if h["name"].lower() == "date"), "")
        snippet = msg_data.get("snippet", "")
        print(f"ID: {msg['id']}")
        print(f"From: {from_addr}")
        print(f"Date: {date}")
        print(f"Subject: {subject}")
        print(f"Snippet: {snippet}")
        print("-" * 50)


def gmail_read(message_id, output_json=False):
    url = f"{GMAIL_API}/users/me/messages/{message_id}?format=full"
    result = api_call("GET", url)
    if output_json:
        print(fmt_json(result))
        return
    hdrs = result.get("payload", {}).get("headers", [])
    for h in ["From", "To", "Subject", "Date", "Cc", "Bcc"]:
        value = next((hdr["value"] for hdr in hdrs if hdr["name"].lower() == h.lower()), None)
        if value:
            print(f"{h}: {value}")
    print("\nBody:")
    body = result.get("payload", {}).get("body", {})
    if body.get("data"):
        print(base64.urlsafe_b64decode(body["data"]).decode("utf-8"))
    else:
        parts = result.get("payload", {}).get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                print(base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8"))
                break


def gmail_send(to, subject, body, output_json=False):
    message = MIMEMultipart()
    message["to"] = to
    message["subject"] = subject
    message.attach(MIMEText(body, "plain"))
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    result = api_call("POST", f"{GMAIL_API}/users/me/messages/send", {"raw": raw})
    if output_json:
        print(fmt_json(result))
    else:
        print(f"Email sent. ID: {result.get('id')}")


def gmail_reply(message_id, body, output_json=False):
    url = f"{GMAIL_API}/users/me/messages/{message_id}"
    original = api_call("GET", url)
    thread_id = original.get("threadId")
    hdrs = original.get("payload", {}).get("headers", [])
    to = next((h["value"] for h in hdrs if h["name"].lower() == "reply-to"),
               next((h["value"] for h in hdrs if h["name"].lower() == "from"), ""))
    subject = next((h["value"] for h in hdrs if h["name"].lower() == "subject"), "")
    if not subject.startswith("Re:"):
        subject = f"Re: {subject}"
    message = MIMEMultipart()
    message["to"] = to
    message["subject"] = subject
    message["In-Reply-To"] = message_id
    message["References"] = message_id
    message.attach(MIMEText(body, "plain"))
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    result = api_call("POST", f"{GMAIL_API}/users/me/messages/send", {"raw": raw, "threadId": thread_id})
    if output_json:
        print(fmt_json(result))
    else:
        print(f"Reply sent. ID: {result.get('id')}")


def gmail_label_cmd(message_id, add_label=None, remove_label=None, output_json=False):
    body = {"addLabelIds": [], "removeLabelIds": []}
    if add_label:
        body["addLabelIds"].append(add_label)
    if remove_label:
        body["removeLabelIds"].append(remove_label)
    result = api_call("POST", f"{GMAIL_API}/users/me/messages/{message_id}/modify", body)
    if output_json:
        print(fmt_json(result))
    else:
        print(f"Labels updated for message {message_id}")


def gmail_labels(output_json=False):
    result = api_call("GET", f"{GMAIL_API}/users/me/labels")
    if output_json:
        print(fmt_json(result))
        return
    for label in result.get("labels", []):
        print(f"{label['name']} (ID: {label['id']})")


def gmail_draft(to, subject, body, output_json=False):
    message = MIMEMultipart()
    message["to"] = to
    message["subject"] = subject
    message.attach(MIMEText(body, "plain"))
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    result = api_call("POST", f"{GMAIL_API}/users/me/drafts", {"message": {"raw": raw}})
    if output_json:
        print(fmt_json(result))
    else:
        print(f"Draft created. ID: {result.get('id')}")


# ===== CALENDAR =====

def calendar_list(start_date=None, end_date=None, output_json=False):
    params = {}
    if start_date:
        params["timeMin"] = f"{start_date}T00:00:00Z"
    if end_date:
        params["timeMax"] = f"{end_date}T23:59:59Z"
    url = f"{CALENDAR_API}/calendars/primary/events?{urllib.parse.urlencode(params)}"
    result = api_call("GET", url)
    if output_json:
        print(fmt_json(result))
        return
    events = result.get("items", [])
    if not events:
        print("No events found")
        return
    for event in events:
        start = event.get("start", {})
        end = event.get("end", {})
        print(f"ID: {event['id']}")
        print(f"Summary: {event.get('summary', '(No title)')}")
        print(f"Start: {start.get('dateTime', start.get('date', ''))}")
        print(f"End: {end.get('dateTime', end.get('date', ''))}")
        if event.get("location"):
            print(f"Location: {event['location']}")
        print("-" * 50)


def calendar_create(summary, start, end, output_json=False):
    body = {
        "summary": summary,
        "start": {"dateTime": start, "timeZone": "UTC"},
        "end": {"dateTime": end, "timeZone": "UTC"}
    }
    result = api_call("POST", f"{CALENDAR_API}/calendars/primary/events", body)
    if output_json:
        print(fmt_json(result))
    else:
        print(f"Event created. ID: {result.get('id')}")


def calendar_update(event_id, summary=None, start=None, end=None, output_json=False):
    body = {}
    if summary:
        body["summary"] = summary
    if start:
        body["start"] = {"dateTime": start, "timeZone": "UTC"}
    if end:
        body["end"] = {"dateTime": end, "timeZone": "UTC"}
    result = api_call("PATCH", f"{CALENDAR_API}/calendars/primary/events/{event_id}", body)
    if output_json:
        print(fmt_json(result))
    else:
        print(f"Event updated. ID: {result.get('id')}")


# ===== DRIVE =====

def drive_search(query, max_results=10, output_json=False):
    url = f"{DRIVE_API}/files?q={urllib.parse.quote(query)}&pageSize={max_results}&fields=files(id,name,mimeType,modifiedTime)"
    result = api_call("GET", url)
    if output_json:
        print(fmt_json(result))
        return
    files = result.get("files", [])
    if not files:
        print("No files found")
        return
    for f in files:
        print(f"ID: {f['id']}")
        print(f"Name: {f['name']}")
        print(f"Type: {f['mimeType']}")
        print(f"Modified: {f.get('modifiedTime', 'N/A')}")
        print("-" * 50)


def drive_list(folder_id=None, output_json=False):
    folder_query = f"\'{folder_id or 'root'}\' in parents and trashed=false"
    url = f"{DRIVE_API}/files?q={urllib.parse.quote(folder_query)}&fields=files(id,name,mimeType,modifiedTime)"
    result = api_call("GET", url)
    if output_json:
        print(fmt_json(result))
        return
    files = result.get("files", [])
    if not files:
        print("Folder is empty")
        return
    for f in files:
        icon = "D" if f["mimeType"] == "application/vnd.google-apps.folder" else "F"
        print(f"[{icon}] {f['name']} (ID: {f['id']})")


def drive_download(file_id, output_path, output_json=False):
    meta = api_call("GET", f"{DRIVE_API}/files/{file_id}?fields=name,mimeType")
    if meta["mimeType"].startswith("application/vnd.google-apps."):
        export_mime = {
            "application/vnd.google-apps.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.google-apps.presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        }.get(meta["mimeType"], "text/plain")
        url = f"{DRIVE_API}/files/{file_id}/export?mimeType={urllib.parse.quote(export_mime)}"
    else:
        url = f"{DRIVE_API}/files/{file_id}?alt=media"
    access_token = get_access_token()
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {access_token}")
    with urllib.request.urlopen(req) as response:
        with open(output_path, "wb") as f:
            f.write(response.read())
    if output_json:
        print(fmt_json({"status": "downloaded", "path": output_path}))
    else:
        print(f"Downloaded: {meta['name']} -> {output_path}")


def drive_upload(file_path, folder_id=None, output_json=False):
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    file_name = os.path.basename(file_path)
    access_token = get_access_token()
    boundary = "-------314159265358979323846"
    metadata = {"name": file_name}
    if folder_id:
        metadata["parents"] = [folder_id]
    with open(file_path, "rb") as f:
        file_content = f.read()
    body = (
        f"\r\n--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
        + json.dumps(metadata)
        + f"\r\n--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + file_content + f"\r\n--{boundary}--".encode("utf-8")
    url = f"https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name"
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type", f"multipart/related; boundary={boundary}")
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))
    if output_json:
        print(fmt_json(result))
    else:
        print(f"Uploaded: {file_name} (ID: {result.get('id')}")


def drive_mkdir(name, parent_id=None, output_json=False):
    body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        body["parents"] = [parent_id]
    result = api_call("POST", f"{DRIVE_API}/files", body)
    if output_json:
        print(fmt_json(result))
    else:
        print(f"Folder created: {name} (ID: {result.get('id')})")


def drive_info(file_id, output_json=False):
    url = f"{DRIVE_API}/files/{file_id}?fields=id,name,mimeType,createdTime,modifiedTime,size"
    result = api_call("GET", url)
    if output_json:
        print(fmt_json(result))
        return
    print(f"ID: {result.get('id')}")
    print(f"Name: {result.get('name')}")
    print(f"Type: {result.get('mimeType')}")
    print(f"Created: {result.get('createdTime')}")
    print(f"Modified: {result.get('modifiedTime')}")
    print(f"Size: {result.get('size', 'N/A')} bytes")


# ===== SHEETS =====

def sheets_get(sheet_id, range_spec, output_json=False):
    url = f"{SHEETS_API}/spreadsheets/{sheet_id}/values/{urllib.parse.quote(range_spec)}"
    result = api_call("GET", url)
    if output_json:
        print(fmt_json(result))
        return
    values = result.get("values", [])
    if not values:
        print("No data found")
        return
    for row in values:
        print("\t".join(str(v) for v in row))


def sheets_update(sheet_id, range_spec, values, output_json=False):
    url = f"{SHEETS_API}/spreadsheets/{sheet_id}/values/{urllib.parse.quote(range_spec)}?valueInputOption=USER_ENTERED"
    body = {"values": json.loads(values)}
    result = api_call("PUT", url, body)
    if output_json:
        print(fmt_json(result))
    else:
        print(f"Updated {result.get('updatedCells')} cells")


def sheets_append(sheet_id, range_spec, values, output_json=False):
    url = f"{SHEETS_API}/spreadsheets/{sheet_id}/values/{urllib.parse.quote(range_spec)}:append?valueInputOption=USER_ENTERED"
    body = {"values": json.loads(values)}
    result = api_call("POST", url, body)
    if output_json:
        print(fmt_json(result))
    else:
        updated = result.get("updates", {}).get("updatedRows", "some")
        print(f"Appended {updated} rows")


def sheets_clear(sheet_id, range_spec, output_json=False):
    url = f"{SHEETS_API}/spreadsheets/{sheet_id}/values/{urllib.parse.quote(range_spec)}:clear"
    result = api_call("POST", url, {})
    if output_json:
        print(fmt_json(result))
    else:
        print(f"Cleared range: {range_spec}")


def sheets_create(title, output_json=False):
    result = api_call("POST", f"{SHEETS_API}/spreadsheets", {"properties": {"title": title}})
    if output_json:
        print(fmt_json(result))
    else:
        print(f"Created spreadsheet: {title} (ID: {result.get('spreadsheetId')})")


def sheets_metadata(sheet_id, output_json=False):
    result = api_call("GET", f"{SHEETS_API}/spreadsheets/{sheet_id}")
    if output_json:
        print(fmt_json(result))
        return
    props = result.get("properties", {})
    print(f"Title: {props.get('title')}")
    print(f"ID: {result.get('spreadsheetId')}")
    print("Sheets:")
    for sheet in result.get("sheets", []):
        sp = sheet.get("properties", {})
        print(f"  - {sp.get('title')} (ID: {sp.get('sheetId')}, Index: {sp.get('index')})")


# ===== DOCS =====

def docs_read(doc_id, output_json=False):
    result = api_call("GET", f"{DOCS_API}/documents/{doc_id}")
    if output_json:
        print(fmt_json(result))
        return
    print(f"Title: {result.get('title', 'Untitled')}")
    print("\nContent:")
    for elem in result.get("body", {}).get("content", []):
        if "paragraph" in elem:
            text = ""
            for te in elem["paragraph"].get("elements", []):
                if "textRun" in te:
                    text += te["textRun"].get("content", "")
            if text.strip():
                print(text.rstrip())


def docs_create(title, body_content="", output_json=False):
    result = api_call("POST", f"{DOCS_API}/documents", {"title": title})
    doc_id = result.get("documentId")
    if body_content and doc_id:
        api_call("POST", f"{DOCS_API}/documents/{doc_id}:batchUpdate", {
            "requests": [{"insertText": {"location": {"index": 1}, "text": body_content}}]
        })
    if output_json:
        print(fmt_json(result))
    else:
        print(f"Created document: {title} (ID: {doc_id})")


def docs_export(doc_id, fmt="txt", output_path=None, output_json=False):
    export_mime = {"txt": "text/plain", "pdf": "application/pdf", "html": "text/html", "rtf": "application/rtf"}.get(fmt, "text/plain")
    access_token = get_access_token()
    url = f"https://www.googleapis.com/drive/v3/files/{doc_id}/export?mimeType={urllib.parse.quote(export_mime)}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {access_token}")
    with urllib.request.urlopen(req) as response:
        content = response.read()
    if output_path:
        with open(output_path, "wb") as f:
            f.write(content)
        if output_json:
            print(fmt_json({"status": "exported", "path": output_path}))
        else:
            print(f"Exported to: {output_path}")
    else:
        print(content.decode("utf-8", errors="ignore"))


# ===== SLIDES =====

def slides_create(title, output_json=False):
    print("Slides scope not yet authorized. Run: python3 gw.py auth --add-scope slides", file=sys.stderr)
    sys.exit(1)


def slides_list(presentation_id, output_json=False):
    print("Slides scope not yet authorized. Run: python3 gw.py auth --add-scope slides", file=sys.stderr)
    sys.exit(1)


# ===== MAIN =====

def main():
    parser = argparse.ArgumentParser(description="Google Workspace CLI")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    subparsers = parser.add_subparsers(dest="service")

    # Gmail
    gp = subparsers.add_parser("gmail")
    gs = gp.add_subparsers(dest="action")

    sp = gs.add_parser("search")
    sp.add_argument("query")
    sp.add_argument("--max", type=int, default=10)

    rp = gs.add_parser("read")
    rp.add_argument("messageId")

    sendp = gs.add_parser("send")
    sendp.add_argument("--to", required=True)
    sendp.add_argument("--subject", required=True)
    sendp.add_argument("--body")
    sendp.add_argument("--body-file")

    replyp = gs.add_parser("reply")
    replyp.add_argument("--message-id", required=True)
    replyp.add_argument("--body", required=True)

    lp = gs.add_parser("label")
    lp.add_argument("messageId")
    lp.add_argument("--add")
    lp.add_argument("--remove")

    gs.add_parser("labels")

    dp = gs.add_parser("draft")
    dp.add_argument("--to", required=True)
    dp.add_argument("--subject", required=True)
    dp.add_argument("--body", required=True)

    # Calendar
    cp = subparsers.add_parser("calendar")
    cs = cp.add_subparsers(dest="action")

    clp = cs.add_parser("list")
    clp.add_argument("--from", dest="start")
    clp.add_argument("--to", dest="end")

    ccp = cs.add_parser("create")
    ccp.add_argument("--summary", required=True)
    ccp.add_argument("--start", required=True)
    ccp.add_argument("--end", required=True)

    cup = cs.add_parser("update")
    cup.add_argument("eventId")
    cup.add_argument("--summary")
    cup.add_argument("--start")
    cup.add_argument("--end")

    # Drive
    drp = subparsers.add_parser("drive")
    drs = drp.add_subparsers(dest="action")

    drsp = drs.add_parser("search")
    drsp.add_argument("query")
    drsp.add_argument("--max", type=int, default=10)

    drlp = drs.add_parser("list")
    drlp.add_argument("folderId", nargs="?")

    drdp = drs.add_parser("download")
    drdp.add_argument("fileId")
    drdp.add_argument("--out", required=True)

    drup = drs.add_parser("upload")
    drup.add_argument("file")
    drup.add_argument("--folder")

    drmp = drs.add_parser("mkdir")
    drmp.add_argument("name")
    drmp.add_argument("--parent")

    drip = drs.add_parser("info")
    drip.add_argument("fileId")

    # Sheets
    shp = subparsers.add_parser("sheets")
    shs = shp.add_subparsers(dest="action")

    shgp = shs.add_parser("get")
    shgp.add_argument("sheetId")
    shgp.add_argument("range")

    shup = shs.add_parser("update")
    shup.add_argument("sheetId")
    shup.add_argument("range")
    shup.add_argument("--values", required=True)

    shap = shs.add_parser("append")
    shap.add_argument("sheetId")
    shap.add_argument("range")
    shap.add_argument("--values", required=True)

    shclp = shs.add_parser("clear")
    shclp.add_argument("sheetId")
    shclp.add_argument("range")

    shcrp = shs.add_parser("create")
    shcrp.add_argument("title")

    shmp = shs.add_parser("metadata")
    shmp.add_argument("sheetId")

    # Docs
    docp = subparsers.add_parser("docs")
    docs = docp.add_subparsers(dest="action")

    docrp = docs.add_parser("read")
    docrp.add_argument("docId")

    doccp = docs.add_parser("create")
    doccp.add_argument("title")
    doccp.add_argument("--body")

    docep = docs.add_parser("export")
    docep.add_argument("docId")
    docep.add_argument("--format", default="txt")
    docep.add_argument("--out")

    # Slides
    slp = subparsers.add_parser("slides")
    sls = slp.add_subparsers(dest="action")

    slcp = sls.add_parser("create")
    slcp.add_argument("title")

    sllp = sls.add_parser("list")
    sllp.add_argument("presentationId")

    args = parser.parse_args()

    if not args.service:
        parser.print_help()
        sys.exit(1)

    output_json = args.json

    try:
        if args.service == "gmail":
            if args.action == "search":
                gmail_search(args.query, args.max, output_json)
            elif args.action == "read":
                gmail_read(args.messageId, output_json)
            elif args.action == "send":
                body = args.body or ""
                if args.body_file:
                    with open(args.body_file) as f:
                        body = f.read()
                gmail_send(args.to, args.subject, body, output_json)
            elif args.action == "reply":
                gmail_reply(args.message_id, args.body, output_json)
            elif args.action == "label":
                gmail_label_cmd(args.messageId, args.add, args.remove, output_json)
            elif args.action == "labels":
                gmail_labels(output_json)
            elif args.action == "draft":
                gmail_draft(args.to, args.subject, args.body, output_json)
            else:
                gp.print_help()

        elif args.service == "calendar":
            if args.action == "list":
                calendar_list(args.start, args.end, output_json)
            elif args.action == "create":
                calendar_create(args.summary, args.start, args.end, output_json)
            elif args.action == "update":
                calendar_update(args.eventId, args.summary, args.start, args.end, output_json)
            else:
                cp.print_help()

        elif args.service == "drive":
            if args.action == "search":
                drive_search(args.query, args.max, output_json)
            elif args.action == "list":
                drive_list(args.folderId, output_json)
            elif args.action == "download":
                drive_download(args.fileId, args.out, output_json)
            elif args.action == "upload":
                drive_upload(args.file, args.folder, output_json)
            elif args.action == "mkdir":
                drive_mkdir(args.name, args.parent, output_json)
            elif args.action == "info":
                drive_info(args.fileId, output_json)
            else:
                drp.print_help()

        elif args.service == "sheets":
            if args.action == "get":
                sheets_get(args.sheetId, args.range, output_json)
            elif args.action == "update":
                sheets_update(args.sheetId, args.range, args.values, output_json)
            elif args.action == "append":
                sheets_append(args.sheetId, args.range, args.values, output_json)
            elif args.action == "clear":
                sheets_clear(args.sheetId, args.range, output_json)
            elif args.action == "create":
                sheets_create(args.title, output_json)
            elif args.action == "metadata":
                sheets_metadata(args.sheetId, output_json)
            else:
                shp.print_help()

        elif args.service == "docs":
            if args.action == "read":
                docs_read(args.docId, output_json)
            elif args.action == "create":
                docs_create(args.title, args.body or "", output_json)
            elif args.action == "export":
                docs_export(args.docId, args.format, args.out, output_json)
            else:
                docp.print_help()

        elif args.service == "slides":
            if args.action == "create":
                slides_create(args.title, output_json)
            elif args.action == "list":
                slides_list(args.presentationId, output_json)
            else:
                slp.print_help()

        else:
            parser.print_help()

    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
