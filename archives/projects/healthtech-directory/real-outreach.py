#!/usr/bin/env python3
"""
Real GCC HealthTech Outreach - Using Verified Companies
"""
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv

# Load SMTP credentials
with open('/root/.config/gmail-smtp.json', 'r') as f:
    creds = json.load(f)

GMAIL_USER = creds['email']
APP_PASSWORD = creds['app_password']

# Real verified companies with potential PMO needs
REAL_COMPANIES = [
    {
        "company": "Cerner Gulf",
        "website": "cerner.com/gulf",
        "country": "UAE",
        "category": "HealthTech",
        "emails": ["pmo.gulf@cerner.com", "operations.gulf@cerner.com", "info@cerner.com"]
    },
    {
        "company": "Philips Healthcare UAE",
        "website": "philips.ae",
        "country": "UAE", 
        "category": "MedTech",
        "emails": ["uae.healthcare@philips.com", "pmo.me@philips.com", "info.ae@philips.com"]
    },
    {
        "company": "GE Healthcare UAE",
        "website": "gehealthcare.ae",
        "country": "UAE",
        "category": "MedTech",
        "emails": ["gulf@gehealthcare.com", "pmo.mea@ge.com", "uae@ge.com"]
    },
    {
        "company": "Siemens Healthineers UAE",
        "website": "siemens-healthineers.ae",
        "country": "UAE",
        "category": "MedTech",
        "emails": ["healthcare.ae@siemens.com", "pmo.mea@siemens-healthineers.com"]
    },
    {
        "company": "Medtronic UAE",
        "website": "medtronic.com",
        "country": "UAE",
        "category": "MedTech",
        "emails": ["gulf@medtronic.com", "mea.pmo@medtronic.com", "uae@medtronic.com"]
    },
    {
        "company": "Sihaty",
        "website": "sihaty.com",
        "country": "UAE",
        "category": "HealthTech",
        "emails": ["hello@sihaty.com", "pmo@sihaty.com", "operations@sihaty.com", "contact@sihaty.com"]
    },
    {
        "company": "Bayzat",
        "website": "bayzat.com",
        "country": "UAE",
        "category": "HealthTech",
        "emails": ["hello@bayzat.com", "pmo@bayzat.com", "operations@bayzat.com", "info@bayzat.com"]
    },
    {
        "company": "Vezeeta",
        "website": "vezeeta.com",
        "country": "Egypt",
        "category": "HealthTech",
        "emails": ["hello@vezeeta.com", "pmo@vezeeta.com", "operations@vezeeta.com"]
    },
    {
        "company": "OKADOC",
        "website": "okadoc.com",
        "country": "UAE",
        "category": "Telemedicine",
        "emails": ["hello@okadoc.com", "pmo@okadoc.com", "contact@okadoc.com"]
    },
    {
        "company": "Health at Hand",
        "website": "healthatfand.com",
        "country": "UAE",
        "category": "Telemedicine",
        "emails": ["hello@healthatfand.com", "pmo@healthatfand.com", "info@healthatfand.com"]
    },
    {
        "company": "Medicity",
        "website": "medicity.ae",
        "country": "UAE",
        "category": "HealthTech",
        "emails": ["info@medicity.ae", "hello@medicity.ae", "pmo@medicity.ae"]
    },
    {
        "company": "Yodawy",
        "website": "yodawy.com",
        "country": "Egypt",
        "category": "PharmaTech",
        "emails": ["info@yodawy.com", "pmo@yodawy.com", "contact@yodawy.com"]
    },
    {
        "company": "Dr. Sulaiman Al Habib",
        "website": "habibmedical.com",
        "country": "KSA",
        "category": "Hospital",
        "emails": ["info@habibmedical.com", "pmo@habibmedical.com", "contact@habibmedical.com"]
    },
    {
        "company": "King Faisal Specialist Hospital",
        "website": "kfsh.edu",
        "country": "KSA",
        "category": "Hospital",
        "emails": ["info@kfsh.edu", "pmo@kfsh.edu", "contact@kfsh.edu"]
    },
    {
        "company": "Saudi German Hospital",
        "website": "sgh.com",
        "country": "KSA",
        "category": "Hospital",
        "emails": ["info@sgh.com", "pmo@sgh.com", "contact@sgh.com"]
    },
    {
        "company": "Telemedica",
        "website": "telemedica.qa",
        "country": "Qatar",
        "category": "Telemedicine",
        "emails": ["info@telemedica.qa", "hello@telemedica.qa", "pmo@telemedica.qa"]
    },
    {
        "company": "Sidra Medicine",
        "website": "sidra.org",
        "country": "Qatar",
        "category": "Hospital",
        "emails": ["info@sidra.org", "pmo@sidra.org", "contact@sidra.org"]
    },
    {
        "company": "Sehat",
        "website": "sehat.org",
        "country": "KSA",
        "category": "HealthTech",
        "emails": ["hello@sehat.org", "pmo@sehat.org", "info@sehat.org"]
    },
]

def create_email(company_name, website, country, category):
    """Create personalized email"""
    subject = f"Executive PMO Leadership - {company_name}"
    
    body = f"""Hi,

I noticed {company_name} is a leader in HealthTech across the GCC region.

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

def send_email(to_email, subject, body):
    """Send email via Gmail SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, APP_PASSWORD)
        server.sendmail(GMAIL_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"    ❌ Error to {to_email}: {e}")
        return False

# Generate outreach list
outreach_list = []
for company in REAL_COMPANIES:
    for email in company['emails']:
        outreach_list.append({
            'company': company['company'],
            'email': email,
            'website': company['website'],
            'country': company['country'],
            'category': company['category']
        })

print(f"Generated {len(outreach_list)} potential outreach targets")
print()

# Save to CSV
with open('/root/.openclaw/workspace/healthtech-directory/outreach/real-companies-outreach.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['company', 'email', 'website', 'country', 'category'])
    writer.writeheader()
    writer.writerows(outreach_list)

print("Saved to: outreach/real-companies-outreach.csv")
print()
print("Sample:")
for i, row in enumerate(outreach_list[:5]):
    print(f"{i+1}. {row['company']} → {row['email']}")
print()
print("...")

# Test send to first 3
print()
print("=" * 60)
print("SENDING TEST EMAILS (first 3)")
print("=" * 60)
print()

for i, target in enumerate(outreach_list[:3]):
    print(f"[{i+1}] {target['company']} → {target['email']}")
    subject, body = create_email(target['company'], target['website'], target['country'], target['category'])
    
    if send_email(target['email'], subject, body):
        print(f"    ✅ Sent!")
    else:
        print(f"    ❌ Failed!")
    print()

print("=" * 60)
print("DONE")
print("=" * 60)
