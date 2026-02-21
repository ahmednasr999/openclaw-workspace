#!/usr/bin/env python3
"""
Company Career Page Scraper - Find PMO/Operations Roles
Run locally to find real contacts and job openings
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import time

# Companies to check
COMPANIES = [
    {"name": "Bayzat", "url": "https://bayzat.com/careers", "domain": "bayzat.com"},
    {"name": "Sihaty", "url": "https://sihaty.com/careers", "domain": "sihaty.com"},
    {"name": "Vezeeta", "url": "https://vezeeta.com/careers", "domain": "vezeeta.com"},
    {"name": "Cerner Gulf", "url": "https://cerner.com/careers", "domain": "cerner.com"},
    {"name": "Philips Healthcare", "url": "https://www.philips.com/a-w/careers.html", "domain": "philips.com"},
    {"name": "GE Healthcare", "url": "https://www.gehealthcare.com/careers", "domain": "gehealthcare.com"},
    {"name": "Medtronic", "url": "https://www.medtronic.com/us-en/company/careers.html", "domain": "medtronic.com"},
    {"name": "OKADOC", "url": "https://okadoc.com/careers", "domain": "okadoc.com"},
    {"name": "Health at Hand", "url": "https://healthatfand.com/careers", "domain": "healthatfand.com"},
    {"name": "Yodawy", "url": "https://yodawy.com/careers", "domain": "yodawy.com"},
]

# Job titles to look for
PMO_KEYWORDS = [
    'pmO', 'project manager', 'program manager', 'operations', 
    'delivery', 'implementation', 'head of', 'director of',
    'chief', 'VP', 'vice president', 'senior manager'
]

def scrape_careers(url, domain):
    """Scrape careers page for PMO roles"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {"url": url, "status": "failed", "error": f"HTTP {response.status_code}"}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for job listings
        jobs = []
        
        # Search for job-related links/text
        for link in soup.find_all(['a', 'button', 'div']):
            text = link.get_text().lower() if link.get_text() else ''
            
            # Check if this looks like a job link
            if any(kw in text for kw in ['job', 'career', 'position', 'role', 'apply']):
                href = link.get('href', '')
                if href and '/jobs/' in href or '/careers/' in href or '/jobs' in href:
                    jobs.append({
                        'text': text.strip()[:100],
                        'url': href if href.startswith('http') else f"https://{domain}{href}"
                    })
        
        # Also search for PMO-specific roles
        pmo_jobs = []
        for link in soup.find_all(['a', 'div', 'li', 'article']):
            text = link.get_text().lower() if link.get_text() else ''
            
            if any(kw in text for kw in PMO_KEYWORDS):
                href = link.get('href', '')
                if href:
                    pmo_jobs.append({
                        'role': text.strip()[:100],
                        'url': href if href.startswith('http') else f"https://{domain}{href}"
                    })
        
        return {
            "url": url,
            "status": "success",
            "job_links": jobs[:10],
            "pmo_roles": pmo_jobs[:10]
        }
        
    except Exception as e:
        return {"url": url, "status": "error", "error": str(e)}

def scrape_linkedin_search(domain):
    """Generate LinkedIn search URLs for the company"""
    company_name = domain.split('.')[0].title()
    
    searches = [
        f"https://www.linkedin.com/search/results/people/?keywords={company_name}%20PMO",
        f"https://www.linkedin.com/search/results/people/?keywords={company_name}%20Operations",
        f"https://www.linkedin.com/search/results/people/?keywords={company_name}%20Project%20Manager",
    ]
    
    return searches

def main():
    print("=" * 70)
    print("  Company Career Page Scraper - PMO Roles")
    print("=" * 70)
    print()
    
    results = []
    
    for company in COMPANIES:
        print(f"Checking: {company['name']}...")
        
        result = {
            "company": company['name'],
            "url": company['url']
        }
        
        # Scrape careers page
        career_data = scrape_careers(company['url'], company['domain'])
        result.update(career_data)
        
        # Generate LinkedIn searches
        result['linkedin_searches'] = scrape_linkedin_search(company['domain'])
        
        results.append(result)
        
        # Print summary
        if career_data.get('status') == 'success':
            pmo_count = len(career_data.get('pmo_roles', []))
            job_count = len(career_data.get('job_links', []))
            print(f"  ✅ Found {job_count} job links, {pmo_count} PMO-related")
        else:
            print(f"  ❌ {career_data.get('error', 'Unknown error')}")
        
        time.sleep(1)  # Rate limiting
    
    # Save results
    with open('career-scrape-results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print()
    print("=" * 70)
    print("  Results")
    print("=" * 70)
    print()
    
    for r in results:
        print(f"📍 {r['company']}")
        print(f"   {r['url']}")
        
        if r.get('pmo_roles'):
            print("   PMO Roles Found:")
            for job in r['pmo_roles'][:3]:
                print(f"   • {job['role']}")
        
        if r.get('linkedin_searches'):
            print("   LinkedIn Searches:")
            for search in r['linkedin_searches'][:1]:
                print(f"   🔗 {search[:60]}...")
        
        print()
    
    print()
    print(f"Full results saved to: career-scrape-results.json")
    print()
    print("Next Steps:")
    print("1. Open LinkedIn search URLs")
    print("2. Find PMO/Operations leads")
    print("3. Send connection requests with personalized notes")

if __name__ == "__main__":
    main()
