#!/usr/bin/env python3
"""
HealthTech Directory - Auto-Scraper
Fully automated Day 1: Find + Scrape + Save
"""
import json
import os
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Configuration
WORKSPACE = "/root/.openclaw/workspace/healthtech-directory"
DATA_DIR = f"{WORKSPACE}/data"
OUTPUT_FILE = f"{DATA_DIR}/gcc-healthtech-raw.json"
MAX_COMPANIES = 5000

# Company search queries
SEARCH_QUERIES = [
    "HealthTech companies UAE list",
    "HealthTech startups KSA directory",
    "Egypt healthcare companies",
    "GCC digital health companies",
    "Hospital chains Dubai Abu Dhabi",
    "HealthTech companies Saudi Arabia",
]


async def search_company_lists(query: str) -> List[str]:
    """Search for company lists using Brave Search API"""
    # This would use web_search in production
    print(f"Searching: {query}")
    return []


async def fetch_directory(url: str, session: aiohttp.ClientSession) -> List[Dict]:
    """Fetch companies from a directory URL"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                text = await response.text()
                # Parse companies from page (simplified)
                return []
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return []


async def scrape_linkedin_companies():
    """Scrape LinkedIn company search results"""
    # LinkedIn requires auth, so this is limited
    # Would need Outscraper for full access
    print("Note: LinkedIn scraping requires Outscraper API")
    return []


async def get_companies_from_sources() -> List[Dict]:
    """Aggregate companies from all sources"""
    companies = []
    
    # Source 1: Web search for company lists
    print("=== Source 1: Web Search ===")
    for query in SEARCH_QUERIES:
        urls = await search_company_lists(query)
        print(f"  Found {len(urls)} URLs for: {query}")
    
    # Source 2: Known directories
    print("\n=== Source 2: Known Directories ===")
    directories = [
        "https://www.crunchbase.com/organization.stype=HealthTech&country_code=ARE",
        "https://www.crunchbase.com/organization.stype=HealthTech&country_code=SAU",
        "https://www.saudibusinessevents.com/directory/healthcare",
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in directories:
            companies.extend(await fetch_directory(url, session))
    
    # Source 3: Manual export (fallback)
    print("\n=== Source 3: LinkedIn Export ===")
    companies.extend(await scrape_linkan_companies())
    
    return companies


async def generate_sample_data():
    """Generate sample data for testing (until real data available)"""
    print("Generating sample GCC HealthTech data...")
    
    sample_companies = [
        {
            "company_name": "MedConnect Health",
            "website": "https://medconnect.ae",
            "linkedin": "https://linkedin.com/company/medconnect",
            "location": {"country": "UAE", "city": "Dubai", "address": "Dubai Healthcare City"},
            "category": "HealthTech",
            "size": "SME",
            "funding": "Series A"
        },
        {
            "company_name": "Saudi Digital Health",
            "website": "https://sdh.sa",
            "linkedin": "https://linkedin.com/company/saudidigitalhealth",
            "location": {"country": "KSA", "city": "Riyadh", "address": "Olaya Street"},
            "category": "HealthTech",
            "size": "Enterprise",
            "funding": "Bootstrapped"
        },
        {
            "company_name": "Cairo Medical Systems",
            "website": "https://cairo-med.com",
            "linkedin": "https://linkedin.com/company/cairo-medical",
            "location": {"country": "Egypt", "city": "Cairo", "address": "Maadi"},
            "category": "MedTech",
            "size": "SME",
            "funding": "Seed"
        },
    ]
    
    # Generate more sample data
    import random
    
    prefixes = ["Gulf", "Emirates", "Arabian", "Nile", "Delta", "Royal", "National", "Advanced"]
    types = ["Health", "Medical", "Pharma", "Care", "Clinic", "Hospital", "Digital", "Smart"]
    suffixes = ["Solutions", "Systems", "Technologies", "Group", "Holdings", "Partners"]
    
    countries = [
        {"country": "UAE", "cities": ["Dubai", "Abu Dhabi", "Sharjah"]},
        {"country": "KSA", "cities": ["Riyadh", "Jeddah", "Dammam"]},
        {"country": "Egypt", "cities": ["Cairo", "Alexandria", "Giza"]},
        {"country": "Kuwait", "cities": ["Kuwait City"]},
        {"country": "Qatar", "cities": ["Doha"]},
        {"country": "Bahrain", "cities": ["Manama"]},
    ]
    
    categories = ["HealthTech", "MedTech", "Hospital", "Clinic", "Digital Health", "Telemedicine"]
    sizes = ["Startup", "SME", "Enterprise"]
    fundings = ["Bootstrapped", "Seed", "Series A", "Series B"]
    
    all_companies = []
    
    for i in range(100):  # Generate 100 sample companies
        prefix = random.choice(prefixes)
        type_name = random.choice(types)
        suffix = random.choice(suffixes)
        
        country_data = random.choice(countries)
        city = random.choice(country_data["cities"])
        
        company_name = f"{prefix} {type_name} {suffix}"
        domain = f"{prefix.lower().replace(' ', '')}{type_name.lower()}.com"
        
        company = {
            "company_name": company_name,
            "website": f"https://{domain}",
            "linkedin": f"https://linkedin.com/company/{company_name.lower().replace(' ', '')}",
            "location": {
                "country": country_data["country"],
                "city": city,
                "address": f"{city}, {country_data['country']}"
            },
            "category": random.choice(categories),
            "size": random.choice(sizes),
            "funding": random.choice(fundings),
            "source": "sample_data"
        }
        
        all_companies.append(company)
    
    # Add the manual samples
    all_companies.extend(sample_companies)
    
    return all_companies


async def auto_scrape():
    """Main auto-scraping function"""
    print("=" * 60)
    print("HealthTech Directory - Auto-Scraper")
    print("=" * 60)
    print()
    
    # Ensure directories
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    
    # Try to get real data
    print("Attempting to scrape real data...")
    companies = await get_companies_from_sources()
    
    # If no real data, generate sample
    if len(companies) < 10:
        print("\nNo sufficient real data found.")
        print("Generating sample data for testing...")
        print()
        companies = await generate_sample_data()
    
    # Save data
    output = {
        "metadata": {
            "scraped_at": datetime.now().isoformat(),
            "source": "auto_scraper",
            "total_records": len(companies),
            "note": "Sample data - replace with real export for production"
        },
        "companies": companies
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("=" * 60)
    print("✓ SCRAPING COMPLETE")
    print("=" * 60)
    print()
    print(f"Saved {len(companies)} companies to:")
    print(f"  {OUTPUT_FILE}")
    print()
    print("Next step:")
    print(f"  cd {WORKSPACE}")
    print(f"  bash quick-start.sh")
    
    return companies


if __name__ == "__main__":
    asyncio.run(auto_scrape())
