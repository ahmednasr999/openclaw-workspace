#!/usr/bin/env python3
"""
Automated Email Finder - Uses Multiple Free Methods
"""
import json
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Target companies with PMO hiring potential
COMPANIES = [
    {"name": "Cerner Gulf", "domain": "cerner.com", "linkedin": "cerner"},
    {"name": "Philips Healthcare UAE", "domain": "philips.com", "linkedin": "philips-healthcare"},
    {"name": "GE Healthcare UAE", "domain": "gehealthcare.com", "linkedin": "ge-healthcare"},
    {"name": "Siemens Healthineers UAE", "domain": "siemens-healthineers.com", "linkedin": "siemens-healthineers"},
    {"name": "Medtronic UAE", "domain": "medtronic.com", "linkedin": "medtronic"},
    {"name": "Bayzat", "domain": "bayzat.com", "linkedin": "bayzat"},
    {"name": "Sihaty", "domain": "sihaty.com", "linkedin": "sihaty"},
    {"name": "Vezeeta", "domain": "vezeeta.com", "linkedin": "vezeeta"},
    {"name": "OKADOC", "domain": "okadoc.com", "linkedin": "okadoc"},
    {"name": "Health at Hand", "domain": "healthatfand.com", "linkedin": "healthatfand"},
    {"name": "Yodawy", "domain": "yodawy.com", "linkedin": "yodawy"},
    {"name": "Dr. Sulaiman Al Habib", "domain": "habibmedical.com", "linkedin": "dr-sulaiman-al-habib-medical-group"},
    {"name": "King Faisal Specialist Hospital", "domain": "kfsh.edu", "linkedin": "king-faisal-specialist-hospital"},
    {"name": "Saudi German Hospital", "domain": "sgh.com", "linkedin": "saudi-german-hospital"},
    {"name": "Telemedica Qatar", "domain": "telemedica.qa", "linkedin": "telemedica"},
    {"name": "Sidra Medicine", "domain": "sidra.org", "linkedin": "sidra-medicine"},
]

def generate_email_patterns(first_name, last_name, domain):
    """Generate possible email patterns"""
    patterns = [
        f"{first_name}.{last_name}@{domain}",
        f"{first_name[0]}{last_name}@{domain}",
        f"{firstname}{last_name}@{domain}",
        f"{first_name}_{last_name}@{domain}",
        f"{first_name}{last_name}@{domain}",
        f"{last_name}.{first_name}@{domain}",
        f"{last_name}{first_name}@{domain}",
        f"{first_name}@{domain}",
    ]
    return patterns

def find_common_pmo_contacts(domain):
    """Generate likely PMO/Operations contact emails"""
    common_pmo_emails = [
        f"pmo@{domain}",
        f"operations@{domain}",
        f"delivery@{domain}",
        f"implementation@{domain}",
        f"pm@{domain}",
        f"program.manager@{domain}",
        f"head.operations@{domain}",
        f"vp.operations@{domain}",
        f"director.pmo@{domain}",
        f"coo@{domain}",
        f"cto@{domain}",
        f"cio@{domain}",
        f"it@{domain}",
        f"hr@{domain}",
        f"recruiting@{domain}",
        f"careers@{domain}",
        f"talent@{domain}",
        f"people@{domain}",
        f"hello@{domain}",
        f"info@{domain}",
        f"contact@{domain}",
    ]
    return common_pmo_emails

def create_personalized_email(company_name, recipient_name=None):
    """Create personalized outreach email"""
    subject = f"Executive PMO Leadership - {company_name}"
    
    body = f"""Hi,

I noticed {company_name} is a leader in HealthTech innovation in the GCC region.

I'm a Senior Technology Executive with 20+ years experience:
• SGH (Egypt): Led $50M transformation, reduced reporting by 97%
• Talabat (GCC): Scaled operations 233x in 18 months
• Network (8 countries): PMO for 300+ projects

I'm exploring senior leadership opportunities in HealthTech, particularly:
- Chief Operating Officer (COO)
- Chief Digital Officer (CDO)  
- VP/Head of PMO
- Director of Digital Transformation

Would you have 15 minutes for a brief call this week?

Best regards,
Ahmed Nasr
Senior Technology Executive | PMO & AI Transformation
"""
    
    return subject, body

def send_email_via_smtp(to_email, subject, body, credentials_file='/root/.config/gmail-smtp.json'):
    """Send email via Gmail SMTP"""
    import json
    
    with open(credentials_file, 'r') as f:
        creds = json.load(f)
    
    try:
        msg = MIMEMultipart()
        msg['From'] = creds['email']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(creds['email'], creds['app_password'])
        server.sendmail(creds['email'], to_email, msg.as_string())
        server.quit()
        return True, "Sent"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 70)
    print("  Automated Email Sender - Real Company Contacts")
    print("=" * 70)
    print()
    
    all_contacts = []
    
    # Generate all possible contacts
    for company in COMPANIES:
        domain = company['domain']
        name = company['name']
        
        print(f"📍 {name}")
        
        # Common PMO emails
        pmo_emails = find_common_pmo_contacts(domain)
        
        # Add to contacts list
        for email in pmo_emails:
            all_contacts.append({
                'company': name,
                'email': email,
                'type': 'pmo'
            })
            print(f"   → {email}")
        
        print()
    
    print(f"Total contacts generated: {len(all_contacts)}")
    print()
    
    # Save contacts
    with open('auto-contacts.json', 'w') as f:
        json.dump(all_contacts, f, indent=2)
    
    # Send test emails to first 3 unique domains
    print("=" * 70)
    print("  Sending Test Emails")
    print("=" * 70)
    print()
    
    sent = []
    failed = []
    tested_domains = set()
    
    for i, contact in enumerate(all_contacts):
        domain = contact['email'].split('@')[1]
        
        # Only test 1 email per domain
        if domain in tested_domains:
            continue
        tested_domains.add(domain)
        
        if len(sent) >= 3:
            break
        
        company = contact['company']
        email = contact['email']
        
        subject, body = create_personalized_email(company)
        
        print(f"[{len(sent)+1}] {company} → {email}")
        success, msg = send_email_via_smtp(email, subject, body)
        
        if success:
            sent.append({'company': company, 'email': email})
            print(f"   ✅ Sent!")
        else:
            failed.append({'company': company, 'email': email, 'error': msg})
            print(f"   ❌ Failed: {msg}")
        
        print()
    
    print("=" * 70)
    print("  Results")
    print("=" * 70)
    print()
    print(f"✅ Sent: {len(sent)}")
    print(f"❌ Failed: {len(failed)}")
    print()
    
    if failed:
        print("Failed emails:")
        for f in failed:
            print(f"  • {f['company']}: {f['email']} - {f['error']}")
        print()
    
    # Continue sending to remaining contacts
    print("Continuing with all contacts...")
    print()
    
    success_count = 0
    fail_count = 0
    
    for i, contact in enumerate(all_contacts):
        # Skip already tested
        domain = contact['email'].split('@')[1]
        if domain in tested_domains:
            continue
        
        company = contact['company']
        email = contact['email']
        
        subject, body = create_personalized_email(company)
        
        print(f"[{i+1}/{len(all_contacts)}] {company} → {email}", end=" ")
        
        success, msg = send_email_via_smtp(email, subject, body)
        
        if success:
            success_count += 1
            print("✅")
        else:
            fail_count += 1
            print("❌")
        
        # Rate limiting - wait between emails
        if (i + 1) % 5 == 0:
            print(f"\nProgress: {success_count + fail_count}/{len(all_contacts)}")
            print("Taking a short break to avoid rate limiting...\n")
            import time
            time.sleep(3)
    
    print()
    print("=" * 70)
    print("  FINAL RESULTS")
    print("=" * 70)
    print()
    print(f"Total Sent: {success_count}")
    print(f"Total Failed: {fail_count}")
    print(f"Success Rate: {success_count/(success_count+fail_count)*100:.1f}%")
    print()
    print(f"Contacts saved to: auto-contacts.json")

if __name__ == "__main__":
    main()
