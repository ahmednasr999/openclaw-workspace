#!/usr/bin/env python3
"""
Job Email Monitor - Checks Gmail via SMTP
Finds recruiter/talent/hiring emails
"""
import smtplib
import imaplib
import email
import json
from email.header import decode_header
from datetime import datetime, timedelta

# Load credentials
with open('/root/.config/gmail-smtp.json', 'r') as f:
    creds = json.load(f)

GMAIL_USER = creds['email']
APP_PASSWORD = creds['app_password']

def search_job_emails():
    """Search for job-related emails"""
    
    # IMAP connection for searching
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, APP_PASSWORD)
        
        # Search for recruiter/job emails from last 24 hours
        date_24h = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
        
        # Search queries
        queries = [
            f'SINCE {date_24h} FROM "linkedin.com" (SUBJECT interview OR SUBJECT opportunity OR SUBJECT role)',
            f'SINCE {date_24h} (FROM recruiter OR FROM talent OR FROM hiring OR FROM careers)',
            f'SINCE {date_24h} SUBJECT "job opportunity"',
            f'SINCE {date_24h} SUBJECT "career opportunity"',
        ]
        
        results = []
        
        for query in queries:
            try:
                status, messages = mail.search(None, query)
                if messages[0]:
                    email_ids = messages[0].split()
                    for eid in email_ids[-10:]:  # Last 10 per query
                        res, msg = mail.fetch(eid, "(RFC822)")
                        for response in msg:
                            if isinstance(response, tuple):
                                msg_content = email.message_from_bytes(response[1])
                                subject = decode_header(msg_content["Subject"])[0][0]
                                from_ = msg_content["From"]
                                date = msg_content["Date"]
                                
                                results.append({
                                    "subject": subject[:100],
                                    "from": from_[:80],
                                    "date": date[:30],
                                    "has_linkedin": "linkedin.com" in from_.lower()
                                })
            except Exception as e:
                continue
        
        mail.logout()
        
        return results
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def send_summary(results):
    """Send summary to user via SMTP"""
    
    if not results:
        message = """Subject: Job Search Monitor - No New Opportunities

No new recruiter/talent emails found in the last 24 hours.

Continue:
- Check LinkedIn manually
- Review job boards
- Follow up on pending applications

- Your AI Assistant
"""
    else:
        # Deduplicate
        unique = {}
        for r in results:
            key = r['subject'][:50]
            if key not in unique:
                unique[key] = r
        
        message = f"""Subject: Job Search Monitor - {len(unique)} New Opportunities Found

Found {len(unique)} new job-related emails:

"""
        
        for i, r in enumerate(list(unique.values())[:10], 1):
            message += f"""
{i}. {r['subject']}
   From: {r['from']}
   Date: {r['date']}
"""
        
        message += """

Action Items:
- Review each email
- Respond to relevant opportunities
- Apply to new roles

- Your AI Assistant
"""
    
    # Send via SMTP
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, APP_PASSWORD)
        server.sendmail(GMAIL_USER, GMAIL_USER, message)
        server.quit()
        return True
    except Exception as e:
        print(f"Send error: {e}")
        return False

if __name__ == "__main__":
    print("Checking for job emails...")
    
    results = search_job_emails()
    
    print(f"Found {len(results)} potential opportunities")
    
    if results:
        send_summary(results)
        print("Summary sent to your email!")
    else:
        print("No new emails found")
