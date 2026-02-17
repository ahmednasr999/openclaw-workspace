#!/usr/bin/env python3
"""
HealthTech Directory - Gmail Draft Manager
Manage Gmail drafts with approval workflow
"""
import json
import csv
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace/healthtech-directory"
OUTREACH_DIR = f"{WORKSPACE}/outreach"
DRAFTS_FILE = f"{OUTREACH_DIR}/drafts-status.json"

# Gmail configuration (add your credentials)
GMAIL_CONFIG = {
    "drafts_folder": "HealthTech Outreach",
}


def create_drafts_html():
    """Create an HTML page for reviewing drafts"""
    
    with open(DRAFTS_FILE) as f:
        data = json.load(f)
    
    drafts = data['drafts']
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>HealthTech Outreach - Draft Review</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ background: #f0f0f0; padding: 15px 25px; border-radius: 8px; }}
        .draft {{ background: white; border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 15px; }}
        .draft.pending {{ border-left: 4px solid #ffc107; }}
        .draft.approved {{ border-left: 4px solid #28a745; }}
        .draft.sent {{ border-left: 4px solid #17a2b8; }}
        .company {{ font-size: 18px; font-weight: bold; color: #333; }}
        .contact {{ color: #666; margin: 5px 0; }}
        .email {{ color: #007bff; }}
        .subject {{ background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0; font-family: monospace; }}
        .body {{ white-space: pre-wrap; font-family: Arial, sans-serif; line-height: 1.6; }}
        .status {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
        .status.pending {{ background: #ffc107; color: #000; }}
        .status.approved {{ background: #28a745; color: #fff; }}
        .status.sent {{ background: #17a2b8; color: #fff; }}
        .actions {{ margin-top: 15px; }}
        .btn {{ padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }}
        .btn.approve {{ background: #28a745; color: white; }}
        .btn.edit {{ background: #007bff; color: white; }}
        .btn.send {{ background: #17a2b8; color: white; }}
        .nav {{ margin-bottom: 20px; }}
        .nav a {{ margin-right: 20px; color: #007bff; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="#pending">Pending Review</a>
        <a href="#approved">Approved</a>
        <a href="#sent">Sent</a>
    </div>
    
    <div class="header">
        <h1>📧 HealthTech Outreach - Draft Manager</h1>
        <p>Review and approve emails before sending</p>
    </div>
    
    <div class="stats">
        <div class="stat">Total: {data['metadata']['total']}</div>
        <div class="stat">Pending: {data['metadata']['pending_review']}</div>
        <div class="stat">Approved: {data['metadata']['approved']}</div>
        <div class="stat">Sent: {data['metadata']['sent']}</div>
    </div>
    
    <h2 id="pending">⏳ Pending Review ({len([d for d in drafts if d['status'] == 'pending_review'])})</h2>
"""
    
    # Pending drafts
    for draft in drafts:
        if draft['status'] == 'pending_review':
            html += f"""
    <div class="draft pending" id="draft-{draft['id']}">
        <span class="status pending">PENDING REVIEW</span>
        <div class="company">{draft['company']}</div>
        <div class="contact">{draft['contact']} → <span class="email">{draft['email']}</span></div>
        <div class="subject">Subject: {draft['subject']}</div>
        <div class="body">{draft['body']}</div>
        <div class="actions">
            <button class="btn approve" onclick="approve({draft['id']})">✅ Approve</button>
            <button class="btn edit" onclick="edit({draft['id']})">✏️ Edit in Gmail</button>
        </div>
    </div>
"""
    
    html += """
    <h2 id="approved">✅ Approved ({len([d for d in drafts if d['status'] == 'approved'])})</h2>
"""
    
    # Approved drafts
    for draft in drafts:
        if draft['status'] == 'approved':
            html += f"""
    <div class="draft approved" id="draft-{draft['id']}">
        <span class="status approved">APPROVED - READY TO SEND</span>
        <div class="company">{draft['company']}</div>
        <div class="contact">{draft['contact']} → <span class="email">{draft['email']}</span></div>
        <div class="subject">Subject: {draft['subject']}</div>
        <div class="body">{draft['body']}</div>
        <div class="actions">
            <button class="btn send" onclick="send({draft['id']})">📤 Send</button>
            <button class="btn edit" onclick="edit({draft['id']})">✏️ Edit</button>
        </div>
    </div>
"""
    
    html += """
    <h2 id="sent">📤 Sent ({len([d for d in drafts if d['status'] == 'sent'])})</h2>
"""
    
    # Sent drafts
    for draft in drafts:
        if draft['status'] == 'sent':
            html += f"""
    <div class="draft sent" id="draft-{draft['id']}">
        <span class="status sent">SENT</span>
        <div class="company">{draft['company']}</div>
        <div class="contact">{draft['contact']} → <span class="email">{draft['email']}</span></div>
    </div>
"""
    
    html += """
    <script>
        function approve(id) {
            fetch('/approve/' + id, { method: 'POST' })
                .then(r => r.json())
                .then(d => location.reload());
        }
        
        function send(id) {
            if(confirm('Send this email?')) {
                fetch('/send/' + id, { method: 'POST' })
                    .then(r => r.json())
                    .then(d => location.reload());
            }
        }
        
        function edit(id) {
            window.open('https://mail.google.com/mail/u/0/#drafts', '_blank');
        }
    </script>
</body>
</html>
"""
    
    with open(f"{WORKSPACE}/drafts-review.html", 'w') as f:
        f.write(html)
    
    print(f"✓ Created: drafts-review.html")
    return html


def main():
    """Main function"""
    print("=" * 60)
    print("Gmail Draft Manager")
    print("=" * 60)
    print()
    
    # Create drafts if not exists
    if not Path(DRAFTS_FILE).exists():
        print("Creating drafts...")
        import gmail_drafts
        gmail_drafts.create_gmail_drafts()
    
    # Create HTML review page
    create_drafts_html()
    
    print()
    print("Files ready:")
    print(f"  • {DRAFTS_FILE}")
    print(f"  • {WORKSPACE}/drafts-review.html")
    print()
    print("Next steps:")
    print("  1. Review drafts in browser")
    print("  2. Edit in Gmail if needed")
    print("  3. Approve when ready")
    print("  4. Confirm on Telegram to send")


if __name__ == "__main__":
    main()
