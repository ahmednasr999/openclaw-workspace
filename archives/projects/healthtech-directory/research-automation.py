#!/usr/bin/env python3
"""
HealthTech Directory - Company Research Automation
Research all 47 job target companies systematically
"""
import json
import csv
from datetime import datetime
from pathlib import Path

# Configuration
WORKSPACE = "/root/.openclaw/workspace/healthtech-directory"
DATA_DIR = f"{WORKSPACE}/data"
OUTPUT_DIR = f"{WORKSPACE}/research"


def load_targets():
    """Load job search targets"""
    with open(f"{DATA_DIR}/job-search-targets.json") as f:
        data = json.load(f)
        return data.get("companies", data)


def create_research_template(company: dict) -> str:
    """Create research template for a company"""
    name = company.get("company_name", "Unknown")
    location = company.get("location", {})
    country = location.get("country", "")
    city = location.get("city", "")
    website = company.get("website", "")
    category = company.get("category", "")
    pmo_score = company.get("pmo_maturity", {}).get("score", 0)
    
    template = f"""# Research: {name}

**Company:** {name}
**Location:** {city}, {country}
**Category:** {category}
**Website:** {website}
**PMO Maturity:** {pmo_score}/100

---

## Research Checklist

### 1. Website Research
- [ ] Visit: {website}
- [ ] Check "About Us" page
- [ ] Find leadership team
- [ ] Look for digital transformation initiatives
- [ ] Check careers page

### 2. LinkedIn Research
- [ ] Search company on LinkedIn
- [ ] Identify key decision makers (CTO, CIO, CDO)
- [ ] Check recent posts
- [ ] Look for hiring trends

### 3. Financial/News Research
- [ ] Search for recent news
- [ ] Check for funding announcements
- [ ] Look for expansion news

---

## Key Decision Makers

| Role | Name | LinkedIn | Priority |
|------|------|----------|----------|
| CTO | | | ⭐⭐⭐ |
| CIO | | | ⭐⭐⭐ |
| CDO | | | ⭐⭐⭐ |
| VP Engineering | | | ⭐⭐ |
| HR Director | | | ⭐⭐ |

---

## Outreach Notes

**Why this company is a good fit:**

**Personalized angle:**

**Template message:**

---

## Next Steps

- [ ] Complete research
- [ ] Find decision maker
- [ ] Send outreach
- [ ] Follow up

---

*Template created: {datetime.now().isoformat()}*
"""
    return template


def generate_all_research():
    """Generate research templates for all companies"""
    companies = load_targets()
    
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    print(f"Generating research templates for {len(companies)} companies...")
    
    for i, company in enumerate(companies, 1):
        name = company.get("company_name", f"Company_{i}")
        safe_name = name.replace(" ", "-").replace("/", "-")
        filename = f"research-{i:02d}-{safe_name}.md"
        
        template = create_research_template(company)
        
        with open(f"{OUTPUT_DIR}/{filename}", 'w') as f:
            f.write(template)
        
        print(f"  ✓ {i:2}. {filename}")
    
    print(f"\n✓ Created {len(companies)} research templates in {OUTPUT_DIR}/")


def create_master_tracker():
    """Create master tracking spreadsheet"""
    companies = load_targets()
    
    with open(f"{OUTPUT_DIR}/master-tracker.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'priority', 'company_name', 'website', 'country', 'city', 
            'category', 'size', 'pmo_score', 'research_status',
            'decision_maker', 'decision_maker_linkedin', 'outreach_sent',
            'follow_up_date', 'notes'
        ])
        writer.writeheader()
        
        for i, c in enumerate(companies, 1):
            writer.writerow({
                'priority': i,
                'company_name': c.get('company_name', ''),
                'website': c.get('website', ''),
                'country': c.get('location', {}).get('country', ''),
                'city': c.get('location', {}).get('city', ''),
                'category': c.get('category', ''),
                'size': c.get('size', ''),
                'pmo_score': c.get('pmo_maturity', {}).get('score', ''),
                'research_status': 'Pending',
                'decision_maker': '',
                'decision_maker_linkedin': '',
                'outreach_sent': '',
                'follow_up_date': '',
                'notes': ''
            })
    
    print(f"✓ Created master tracker: {OUTPUT_DIR}/master-tracker.csv")


def main():
    """Main function"""
    print("=" * 60)
    print("HealthTech Directory - Research Automation")
    print("=" * 60)
    print()
    
    # Generate all research templates
    generate_all_research()
    
    # Create master tracker
    create_master_tracker()
    
    print()
    print("=" * 60)
    print("Research Automation Complete")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review research templates in research/")
    print("2. Open master-tracker.csv to track progress")
    print("3. Research top 10 companies")
    print("4. Send personalized outreach")


if __name__ == "__main__":
    main()
