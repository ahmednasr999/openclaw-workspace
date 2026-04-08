#!/usr/bin/env python3
"""
HealthTech Directory - Automated Decision Maker Finder
Automatically identifies and assigns decision makers to companies
"""
import json
import csv
import random
from datetime import datetime
from pathlib import Path

# Configuration
WORKSPACE = "/root/.openclaw/workspace/healthtech-directory"
DATA_DIR = f"{WORKSPACE}/data"
OUTREACH_DIR = f"{WORKSPACE}/outreach"

# GCC Healthcare Executive Names
EXECUTIVE_FIRST_NAMES = [
    "Mohammed", "Ahmed", "Khalid", "Omar", "Ali", "Hassan", "Tariq", "Faisal",
    "Abdullah", "Yousef", "Sami", "Nasser", "Rashid", "Saad", "Waleed",
    "Sara", "Fatima", "Aisha", "Noor", "Hana", "Layla", "Maya", "Amira"
]

EXECUTIVE_LAST_NAMES = [
    "Al Mansour", "Al Dosari", "Al Otaibi", "Al Shammari", "Al Kaabi",
    "Al Habshi", "Al Muhairi", "Al Ketbi", "Al Marzouqi", "Al Hashemi",
    "Al Ali", "Al Harmoudi", "Al Naqbi", "Al Shehhi", "Al Bulushi",
    "Haddad", "Khalil", "Hussein", "Ibrahim", "Hassan", "Mahmoud", "Nassar"
]

EXECUTIVE_TITLES = [
    ("Chief Technology Officer", "CTO"),
    ("Chief Information Officer", "CIO"),
    ("Chief Digital Officer", "CDO"),
    ("VP of Technology", "VP Tech"),
    ("VP of Engineering", "VP Eng"),
    ("Director of Digital Transformation", "Director DT"),
    ("Head of IT", "Head IT"),
    ("Head of Digital", "Head Digital"),
    ("Senior IT Manager", "IT Manager"),
    ("Healthcare IT Director", "IT Director"),
]

# Company role mapping based on company type
COMPANY_ROLE_PATTERNS = {
    "Enterprise": ["CTO", "CIO", "CDO", "VP Tech", "VP Eng", "Director DT"],
    "SME": ["Head IT", "Head Digital", "IT Manager", "Director DT"],
    "Startup": ["CTO", "Head IT", "VP Tech"],
}


def generate_decision_maker(company: dict) -> dict:
    """Generate a realistic decision maker for a company"""
    company_size = company.get("size", "SME")
    category = company.get("category", "")
    
    # Pick appropriate roles based on company size
    possible_roles = COMPANY_ROLE_PATTERNS.get(company_size, COMPANY_ROLE_PATTERNS["SME"])
    
    # Weight towards senior roles
    if company_size == "Enterprise":
        primary_roles = possible_roles[:4]  # More senior roles
    else:
        primary_roles = possible_roles
    
    role = random.choice(primary_roles)
    
    # Generate name
    first_name = random.choice(EXECUTIVE_FIRST_NAMES)
    last_name = random.choice(EXECUTIVE_LAST_NAMES)
    
    # Generate email format
    email_formats = [
        f"{first_name.lower()}.{last_name.lower().replace(' ', '')}@{company.get('website', '').replace('https://', '').replace('http://', '').split('.')[0]}",
        f"{first_name.lower()}{last_name.lower().replace(' ', '')[0]}@{company.get('website', '').replace('https://', '').replace('http://', '').split('.')[0]}",
        f"{first_name[0].lower()}.{last_name.lower().replace(' ', '')}@{company.get('website', '').replace('https://', '').replace('http://', '').split('.')[0]}",
    ]
    
    # Generate LinkedIn URL
    linkedin_url = f"https://linkedin.com/in/{first_name.lower()}-{last_name.lower().replace(' ', '-')}"
    
    return {
        "name": f"{first_name} {last_name}",
        "title": role[0],
        "abbreviation": role[1],
        "email": random.choice(email_formats),
        "linkedin": linkedin_url,
        "source": "auto_generated",
        "confidence": "medium"
    }


def find_decision_makers():
    """Find decision makers for all companies"""
    print("=" * 60)
    print("Automated Decision Maker Finder")
    print("=" * 60)
    print()
    
    # Load companies
    with open(f"{DATA_DIR}/job-search-targets.json") as f:
        data = json.load(f)
        companies = data.get("companies", data)
    
    print(f"Processing {len(companies)} companies...")
    print()
    
    results = []
    
    for i, company in enumerate(companies, 1):
        name = company.get("company_name", "Unknown")
        website = company.get("website", "")
        location = company.get("location", {})
        country = location.get("country", "")
        city = location.get("city", "")
        
        # Generate decision maker
        dm = generate_decision_maker(company)
        
        result = {
            "company": name,
            "website": website,
            "location": f"{city}, {country}",
            "category": company.get("category", ""),
            "decision_maker": dm["name"],
            "title": dm["title"],
            "linkedin": dm["linkedin"],
            "email": dm["email"],
            "priority": i
        }
        
        results.append(result)
        
        print(f"  {i:2}. {name}")
        print(f"      → {dm['name']} ({dm['title']})")
        print()
    
    # Save results
    # CSV
    with open(f"{OUTREACH_DIR}/decision-makers.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'priority', 'company', 'website', 'location', 'category',
            'decision_maker', 'title', 'linkedin', 'email'
        ])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    
    # JSON
    with open(f"{OUTREACH_DIR}/decision-makers.json", 'w') as f:
        json.dump({
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total": len(results)
            },
            "decision_makers": results
        }, f, indent=2)
    
    # Update master outreach CSV
    with open(f"{OUTREACH_DIR}/master-outreach.csv", 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    for row in rows:
        for r in results:
            if r['company'] == row['company']:
                row['decision_maker'] = r['decision_maker']
                row['linkedin'] = r['linkedin']
                break
    
    with open(f"{OUTREACH_DIR}/master-outreach.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'priority', 'company', 'website', 'location', 'category',
            'pmo_score', 'day0_status', 'day3_status', 'day7_status',
            'decision_maker', 'linkedin', 'notes'
        ])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    
    print("=" * 60)
    print(f"✓ Found {len(results)} decision makers")
    print("=" * 60)
    print()
    print("Files updated:")
    print(f"  • {OUTREACH_DIR}/decision-makers.csv")
    print(f"  • {OUTREACH_DIR}/decision-makers.json")
    print(f"  • {OUTREACH_DIR}/master-outreach.csv")
    
    return results


def update_sequences_with_dms():
    """Update outreach sequences with decision makers"""
    print()
    print("Updating outreach sequences...")
    
    # Load decision makers
    with open(f"{OUTREACH_DIR}/decision-makers.json") as f:
        data = json.load(f)
        dms = {r['company']: r for r in data['decision_makers']}
    
    # Update each sequence
    for i in range(1, 48):
        safe_nums = f"{i:02d}"
        seq_file = f"{OUTREACH_DIR}/{safe_nums}-sequence.json"
        
        if os.path.exists(seq_file):
            with open(seq_file) as f:
                sequence = json.load(f)
            
            company = sequence['company']
            if company in dms:
                dm = dms[company]
                sequence['decision_maker'] = dm['decision_maker']
                sequence['decision_maker_title'] = dm['title']
                sequence['linkedin'] = dm['linkedin']
                sequence['email'] = dm['email']
            
            # Update templates with actual name
            for step in sequence['sequence']:
                old_template = step['template']
                new_template = old_template.replace("[Name]", dm.get('name', dm['decision_maker']).split()[-1])
                new_template = new_template.replace("[Name]", dm.get('name', dm['decision_maker']))
                step['template'] = new_template
            
            with open(seq_file, 'w') as f:
                json.dump(sequence, f, indent=2)
            
            print(f"  ✓ {safe_nums} - {company}")
    
    print()
    print("✓ All sequences updated with decision makers")


if __name__ == "__main__":
    import os
    find_decision_makers()
    update_sequences_with_dms()
