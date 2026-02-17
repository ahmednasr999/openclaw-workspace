#!/usr/bin/env python3
"""
Gmail SMTP Sender - Uses App Password
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import csv

# Load credentials
with open('/root/.config/gmail-smtp.json', 'r') as f:
    creds = json.load(f)

GMAIL_USER = creds['email']
APP_PASSWORD = creds['app_password']
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

def send_email(to_email, subject, body):
    """Send email via Gmail SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(GMAIL_USER, APP_PASSWORD)
        server.sendmail(GMAIL_USER, to_email, msg.as_string())
        server.quit()
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

# Load contacts
contacts = []
with open('/root/.openclaw/workspace/healthtech-directory/outreach/decision-makers.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        contacts.append(row)

print(f"Loaded {len(contacts)} contacts")
print()

# Email template
def create_email(contact):
    first_name = contact['decision_maker'].split()[0]
    company = contact['company']
    
    subject = f"Executive PMO Leadership - {company}"
    
    body = f"""Hi {first_name},

I noticed {company} is leading digital transformation in the GCC healthcare sector.

I'm a Senior Technology Executive with 20+ years experience:
• SGH (Egypt): Led $50M transformation, reduced reporting by 97%
• Talabat (GCC): Scaled operations 233x in 18 months
• Network (8 countries): PMO for 300+ projects

I'm exploring senior leadership opportunities in HealthTech, particularly PMO, Digital Transformation, or CDO roles.

Would you have 15 minutes for a brief call this week?

Best regards,
Ahmed Nasr
Senior Technology Executive | PMO & AI Transformation"""
    
    return subject, body

# Send to first 3 as test
print("=" * 60)
print("Sending Test Emails (first 3)")
print("=" * 60)
print()

for i, contact in enumerate(contacts[:3]):
    email = contact['email'].strip()
    first_name = contact['decision_maker'].split()[0]
    company = contact['company']
    
    subject, body = create_email(contact)
    
    print(f"[{i+1}] Sending to {first_name} at {company}...")
    print(f"    → {email}")
    
    if send_email(email, subject, body):
        print(f"    ✅ Sent!")
    else:
        print(f"    ❌ Failed!")
    
    print()

print("=" * 60)
print("Done!")
print("=" * 60)
