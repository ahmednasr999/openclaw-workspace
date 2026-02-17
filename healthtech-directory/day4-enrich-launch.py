# HealthTech Directory - Day 4: Enrichment + Launch
**Image enrichment, PMO assessment, and MVP launch**

---

## Part A: Image Enrichment (Claude Vision)

### Script

```python
#!/usr/bin/env python3
"""
Enrich company data with Claude Vision
"""
import json
import os
import asyncio
from pathlib import Path
from anthropic import Anthropic
from datetime import datetime

# Configuration
INPUT_FILE = "gcc-healthtech-clean.json"
OUTPUT_FILE = "gcc-healthtech-enriched.json"
LOGO_DIR = "./logos"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Initialize Claude
client = Anthropic(api_key=ANTHROPIC_API_KEY)


def get_logo_url(company_name: str, website: str) -> str:
    """Get company logo URL using Claude Vision"""
    prompt = f"""
    Find the official logo URL for {company_name}.
    Website: {website}
    
    Return ONLY the logo URL (direct image link) or "NOT_FOUND".
    Example: "https://example.com/logo.png"
    """
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        
        logo_url = response.content[0].text.strip()
        
        if logo_url == "NOT_FOUND":
            return None
        
        return logo_url
        
    except Exception as e:
        print(f"Error getting logo for {company_name}: {e}")
        return None


def enrich_company(company: dict) -> dict:
    """Enrich a single company"""
    enriched = company.copy()
    
    # Skip if no website
    if not company.get("website"):
        enriched["enrichment"] = {
            "status": "skipped",
            "reason": "no_website"
        }
        return enriched
    
    # Get logo
    logo_url = get_logo_url(
        company["company_name"],
        company["website"]
    )
    
    enriched["logo_url"] = logo_url
    enriched["enrichment"] = {
        "logo_url": logo_url,
        "enriched_at": datetime.now().isoformat(),
        "status": "success" if logo_url else "failed"
    }
    
    return enriched


def enrich_all(input_file: str, output_file: str, limit: int = None):
    """Enrich all companies"""
    # Load
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    companies = data.get("companies", data if isinstance(data, list) else [])
    
    if limit:
        companies = companies[:limit]
    
    print(f"Enriching {len(companies)} companies...")
    
    # Enrich
    enriched = []
    for company in companies:
        result = enrich_company(company)
        enriched.append(result)
        print(f"  ✓ {company['company_name']}"[:50])
    
    # Save
    output = {
        "metadata": {
            "enriched_at": datetime.now().isoformat(),
            "total_companies": len(enriched),
            "with_logo": sum(1 for c in enriched if c.get("logo_url"))
        },
        "companies": enriched
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved {len(enriched)} enriched companies to {output_file}")


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    enrich_all(INPUT_FILE, OUTPUT_FILE, limit)
```

---

## Part B: PMO Maturity Assessment

```python
#!/usr/bin/env python3
"""
Assess PMO maturity based on website signals
"""
import json
import aiohttp
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PMOAssessment:
    company_name: str
    website: str
    score: int = 0
    level: str = "Low"
    signals: List[str] = None
    details: Dict = None
    
    def __post_init__(self):
        if self.signals is None:
            self.signals = []
        if self.details is None:
            self.details = {}


class PMOMaturityAssessor:
    """Assess PMO maturity based on website content"""
    
    # PMO maturity indicators
    HIGH_INDICATORS = [
        "project management office",
        "pmo",
        "program management",
        "portfolio management",
        "transformation office",
        "digital transformation",
        "change management",
        "strategic initiatives"
    ]
    
    MEDIUM_INDICATORS = [
        "project manager",
        "project management",
        "delivery manager",
        "program manager",
        "operations manager",
        "digital initiatives"
    ]
    
    LOW_INDICATORS = [
        "healthcare services",
        "patient care",
        "medical services"
    ]
    
    def __init__(self):
        self.session = None
    
    async def init_session(self):
        self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        if self.session:
            await self.session.close()
    
    async def fetch_website(self, url: str) -> str:
        """Fetch website content"""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                return await response.text()
        except:
            return ""
    
    def assess(self, html: str) -> PMOAssessment:
        """Assess PMO maturity from HTML"""
        html_lower = html.lower()
        
        signals = []
        score = 0
        level = "Low"
        
        # Check high indicators
        for indicator in self.HIGH_INDICATORS:
            if indicator in html_lower:
                signals.append(indicator)
                score += 25  # High value signals
        
        # Check medium indicators
        for indicator in self.MEDIUM_INDICATORS:
            if indicator in html_lower:
                signals.append(indicator)
                score += 10  # Medium value signals
        
        # Cap score at 100
        score = min(score, 100)
        
        # Determine level
        if score >= 75:
            level = "High"
        elif score >= 25:
            level = "Medium"
        else:
            level = "Low"
        
        return PMOAssessment(
            company_name="",
            website="",
            score=score,
            level=level,
            signals=signals,
            details={
                "high_signals": [s for s in signals if s in self.HIGH_INDICATORS],
                "medium_signals": [s for s in signals if s in self.MEDIUM_INDICATORS]
            }
        )
    
    async def assess_company(self, company: dict) -> dict:
        """Assess PMO maturity for a company"""
        website = company.get("website", "")
        
        if not website:
            return {
                **company,
                "pmo_maturity": {
                    "score": 0,
                    "level": "Unknown",
                    "signals": [],
                    "reason": "no_website"
                }
            }
        
        html = await self.fetch_website(website)
        assessment = self.assess(html)
        
        return {
            **company,
            "pmo_maturity": {
                "score": assessment.score,
                "level": assessment.level,
                "signals": assessment.signals,
                "details": assessment.details,
                "assessed_at": datetime.now().isoformat()
            }
        }
    
    async def assess_all(self, companies: list) -> list:
        """Assess all companies"""
        await self.init_session()
        
        results = []
        for company in companies:
            result = await self.assess_company(company)
            results.append(result)
            print(f"  ✓ {company.get('company_name', 'Unknown')[:50]}")
        
        await self.close_session()
        return results


def save_assessment(companies: list, output_file: str):
    """Save assessment results"""
    output = {
        "metadata": {
            "assessed_at": datetime.now().isoformat(),
            "total_companies": len(companies)
        },
        "companies": companies
    }
    
    # Calculate stats
    high = sum(1 for c in companies if c.get("pmo_maturity", {}).get("level") == "High")
    medium = sum(1 for c in companies if c.get("pmo_maturity", {}).get("level") == "Medium")
    low = sum(1 for c in companies if c.get("pmo_maturity", {}).get("level") == "Low")
    
    output["metadata"]["stats"] = {
        "high_maturity": high,
        "medium_maturity": medium,
        "low_maturity": low,
        "unknown": len(companies) - high - medium - low
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved assessment to {output_file}")


async def main():
    """Main function"""
    # Load companies
    with open("gcc-healthtech-clean.json", 'r') as f:
        companies = json.load(f)
        if isinstance(companies, dict) and "companies" in companies:
            companies = companies["companies"]
    
    print(f"Assessing PMO maturity for {len(companies)} companies...")
    
    # Assess
    assessor = PMOMaturityAssessor()
    assessed = await assessor.assess_all(companies)
    
    # Save
    save_assessment(assessed, "gcc-healthtech-pmo-scored.json")
    
    # Print stats
    high = sum(1 for c in assessed if c.get("pmo_maturity", {}).get("level") == "High")
    medium = sum(1 for c in assessed if c.get("pmo_maturity", {}).get("level") == "Medium")
    low = sum(1 for c in assessed if c.get("pmo_maturity", {}).get("level") == "Low")
    
    print(f"\n=== PMO Maturity Assessment ===")
    print(f"High (ANCO clients): {high}")
    print(f"Medium: {medium}")
    print(f"Low (quick wins): {low}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## Part C: MVP Launch (Simple Search Interface)

### index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GCC HealthTech Directory</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #1a1a1a; margin-bottom: 20px; }
        .filters { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .filters input, .filters select { padding: 10px; border: 1px solid #ddd; border-radius: 4px; margin-right: 10px; }
        .filters input { flex: 1; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .card h3 { color: #0066cc; margin-bottom: 10px; }
        .card .category { background: #e3f2fd; color: #1565c0; padding: 4px 8px; border-radius: 4px; font-size: 12px; display: inline-block; margin-bottom: 10px; }
        .card .location { color: #666; font-size: 14px; margin-bottom: 10px; }
        .card .pmo { font-size: 12px; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-right: 5px; }
        .card .pmo.high { background: #c8e6c9; color: #2e7d32; }
        .card .pmo.medium { background: #fff9c4; color: #f9a825; }
        .card .pmo.low { background: #ffcdd2; color: #c62828; }
        .card .website { margin-top: 10px; }
        .card .website a { color: #0066cc; text-decoration: none; }
        .stats { margin-bottom: 20px; color: #666; }
    </style>
</head>
<body>
    <h1>GCC HealthTech Directory</h1>
    <div class="stats" id="stats"></div>
    
    <div class="filters">
        <input type="text" id="search" placeholder="Search companies...">
        <select id="category">
            <option value="">All Categories</option>
            <option value="Hospital">Hospitals</option>
            <option value="HealthTech">HealthTech</option>
            <option value="MedTech">MedTech</option>
            <option value="Clinic">Clinics</option>
        </select>
        <select id="country">
            <option value="">All Countries</option>
            <option value="UAE">UAE</option>
            <option value="KSA">KSA</option>
            <option value="Egypt">Egypt</option>
        </select>
        <select id="pmo">
            <option value="">All PMO Levels</option>
            <option value="High">High (ANCO Clients)</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low (Quick Wins)</option>
        </select>
    </div>
    
    <div class="grid" id="results"></div>
    
    <script>
        let companies = [];
        
        // Load data
        fetch('data.json')
            .then(r => r.json())
            .then(data => {
                companies = data.companies || data;
                renderStats(companies);
                render(companies);
            });
        
        // Search
        document.getElementById('search').addEventListener('input', filter);
        document.getElementById('category').addEventListener('change', filter);
        document.getElementById('country').addEventListener('change', filter);
        document.getElementById('pmo').addEventListener('change', filter);
        
        function filter() {
            const search = document.getElementById('search').value.toLowerCase();
            const category = document.getElementById('category').value;
            const country = document.getElementById('country').value;
            const pmo = document.getElementById('pmo').value;
            
            const filtered = companies.filter(c => {
                const matchSearch = !search || c.company_name.toLowerCase().includes(search);
                const matchCategory = !category || c.category === category;
                const matchCountry = !country || c.location?.country === country;
                const matchPMO = !pmo || (c.pmo_maturity?.level === pmo);
                return matchSearch && matchCategory && matchCountry && matchPMO;
            });
            
            renderStats(filtered);
            render(filtered);
        }
        
        function renderStats(list) {
            const high = list.filter(c => c.pmo_maturity?.level === 'High').length;
            const medium = list.filter(c => c.pmo_maturity?.level === 'Medium').length;
            const low = list.filter(c => c.pmo_maturity?.level === 'Low').length;
            
            document.getElementById('stats').textContent = 
                `Showing ${list.length} companies | High PMO: ${high} | Medium: ${medium} | Low: ${low}`;
        }
        
        function render(list) {
            document.getElementById('results').innerHTML = list.map(c => `
                <div class="card">
                    <h3>${c.company_name}</h3>
                    <span class="category">${c.category}</span>
                    <span class="pmo ${c.pmo_maturity?.level?.toLowerCase() || 'medium'}">PMO: ${c.pmo_maturity?.level || 'Unknown'}</span>
                    <div class="location">📍 ${c.location?.city || ''}, ${c.location?.country || ''}</div>
                    <div class="website">
                        <a href="${c.website || '#'}" target="_blank">${c.website || 'No website'}</a>
                    </div>
                </div>
            `).join('');
        }
    </script>
</body>
</html>
```

---

## Part D: Data Export

```python
#!/usr/bin/env python3
"""
Export directory for different use cases
"""
import json


def export_for_job_search(companies: list, output: str):
    """Export companies relevant for job search"""
    # Filter: High PMO maturity + Hiring PMO roles
    relevant = [
        c for c in companies
        if c.get("pmo_maturity", {}).get("level") == "High"
        and c.get("hiring", {}).get("pmo_roles") == True
    ]
    
    with open(output, 'w') as f:
        json.dump({
            "exported_at": datetime.now().isoformat(),
            "total": len(relevant),
            "companies": relevant
        }, f, indent=2)
    
    print(f"Exported {len(relevant)} companies for job search to {output}")


def export_for_anco(companies: list, output: str):
    """Export companies relevant for ANCO consulting"""
    # Filter: Low PMO maturity + Enterprise size
    prospects = [
        c for c in companies
        if c.get("pmo_maturity", {}).get("level") == "Low"
        and c.get("size") == "Enterprise"
        and c.get("employees", 0) > 100
    ]
    
    with open(output, 'w') as f:
        json.dump({
            "exported_at": datetime.now().isoformat(),
            "total": len(prospects),
            "companies": prospects
        }, f, indent=2)
    
    print(f"Exported {len(prospects)} ANCO prospects to {output}")


def export_csv(companies: list, output: str):
    """Export to CSV for CRM import"""
    import csv
    
    fieldnames = [
        "company_name", "website", "linkedin", "category",
        "country", "city", "size", "pmo_maturity", "pmo_score"
    ]
    
    with open(output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for c in companies:
            row = {
                "company_name": c.get("company_name", ""),
                "website": c.get("website", ""),
                "linkedin": c.get("linkedin", ""),
                "category": c.get("category", ""),
                "country": c.get("location", {}).get("country", ""),
                "city": c.get("location", {}).get("city", ""),
                "size": c.get("size", ""),
                "pmo_maturity": c.get("pmo_maturity", {}).get("level", ""),
                "pmo_score": c.get("pmo_maturity", {}).get("score", 0)
            }
            writer.writerow(row)
    
    print(f"Exported {len(companies)} companies to CSV: {output}")


if __name__ == "__main__":
    with open("gcc-healthtech-enriched.json", 'r') as f:
        data = json.load(f)
        companies = data.get("companies", data)
    
    export_for_job_search(companies, "job-search-targets.json")
    export_for_anco(companies, "anco-prospects.json")
    export_csv(companies, "directory-export.csv")
```

---

## Day 4 Deliverables

| File | Description | Use |
|------|-------------|-----|
| `gcc-healthtech-enriched.json` | Full enriched data | Master |
| `job-search-targets.json` | High PMO + hiring | Job search |
| `anco-prospects.json` | Low PMO + Enterprise | ANCO sales |
| `directory-export.csv` | CSV for CRM | Import to CRM |
| `index.html` | Search interface | MVP launch |
| `data.json` | Company data | Search interface |

---

## Launch Checklist

- [ ] Run enrichment script
- [ ] Export job search targets
- [ ] Export ANCO prospects
- [ ] Create CSV for CRM
- [ ] Build search interface
- [ ] Deploy to Cloudflare Pages
- [ ] Test search functionality

---

*Day 4: Enrichment and Launch*
