# HealthTech Directory - Day 3: Verification
**Verify websites and filter junk with Crawl4AI**

---

## Installation

```bash
# Clone Crawl4AI
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai

# Install dependencies
pip install -e .

# Verify installation
python -c "import crawl4ai; print('Crawl4AI installed')"
```

---

## Verification Script

```python
#!/usr/bin/env python3
"""
Verify HealthTech company websites using Crawl4AI
"""
import json
import asyncio
import aiohttp
from crawl4ai import Crawler, CrawlResult
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configuration
INPUT_FILE = "gcc-healthtech-scored.json"
OUTPUT_FILE = "gcc-healthtech-verified.json"
CONCURRENCY = 10  # Parallel requests
TIMEOUT = 30  # Seconds per request


class CompanyVerifier:
    def __init__(self):
        self.crawler = Crawler()
        self.session = None
        self.stats = {
            "total": 0,
            "verified": 0,
            "failed": 0,
            "skipped": 0,
            "spam": 0
        }
    
    async def init_session(self):
        """Initialize aiohttp session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TIMEOUT)
        )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def verify_website(self, company: dict) -> dict:
        """Verify a single company website"""
        website = company.get("website")
        
        if not website:
            self.stats["skipped"] += 1
            return {
                **company,
                "verification": {
                    "status": "skipped",
                    "reason": "no_website",
                    "checked_at": datetime.now().isoformat()
                }
            }
        
        # Clean URL
        if not website.startswith(("http://", "https://")):
            website = "https://" + website
            company["website"] = website
        
        try:
            # Use Crawl4AI to verify
            result = await self.crawler.arun(
                url=website,
                extraction_strategy=None,  # Just verify, don't extract
                bypass_cache=True
            )
            
            if result.success:
                # Check for spam indicators
                spam_score = self.check_spam(result.html)
                
                if spam_score >= 3:
                    self.stats["spam"] += 1
                    status = "failed"
                    reason = "spam_detected"
                else:
                    self.stats["verified"] += 1
                    status = "verified"
                    reason = "website_loads"
                
                # Extract basic info for enrichment
                title = self.extract_title(result.html)
                description = self.extract_description(result.html)
                
            else:
                self.stats["failed"] += 1
                status = "failed"
                reason = "website_unavailable"
                title = None
                description = None
            
            return {
                **company,
                "verification": {
                    "status": status,
                    "reason": reason,
                    "spam_score": spam_score if status == "verified" else None,
                    "title": title,
                    "description": description,
                    "checked_at": datetime.now().isoformat(),
                    "load_time_ms": result.metadata.get("downloaded_at", {}).get("time_ms", 0) if result.metadata else None
                }
            }
            
        except Exception as e:
            self.stats["failed"] += 1
            return {
                **company,
                "verification": {
                    "status": "failed",
                    "reason": str(e),
                    "checked_at": datetime.now().isoformat()
                }
            }
    
    def check_spam(self, html: str) -> int:
        """Check for spam indicators in HTML"""
        spam_score = 0
        html_lower = html.lower()
        
        spam_indicators = [
            "buy now",
            "click here",
            "free money",
            "make money fast",
            "work from home",
            "weight loss",
            "casino",
            "adult content",
            "redirecting",
            "parking page"
        ]
        
        for indicator in spam_indicators:
            if indicator in html_lower:
                spam_score += 1
        
        # Check for excessive ads
        if "advertisement" in html_lower:
            spam_score += 1
        
        # Check for broken HTML
        if "<html" not in html_lower:
            spam_score += 1
        
        return spam_score
    
    def extract_title(self, html: str) -> Optional[str]:
        """Extract page title"""
        import re
        match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def extract_description(self, html: str) -> Optional[str]:
        """Extract meta description"""
        import re
        match = re.search(
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
            html, re.IGNORECASE
        )
        return match.group(1).strip() if match else None
    
    async def verify_all(self, companies: list) -> list:
        """Verify all companies"""
        await self.init_session()
        
        results = await asyncio.gather(
            *[self.verify_website(c) for c in companies],
            return_exceptions=True
        )
        
        await self.close_session()
        
        # Process results (handle exceptions)
        verified = []
        for result in results:
            if isinstance(result, Exception):
                self.stats["failed"] += 1
            else:
                verified.append(result)
        
        return verified


def load_companies(filename: str) -> list:
    """Load companies from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both "companies" array and direct array
    if isinstance(data, dict) and "companies" in data:
        return data["companies"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unknown JSON format in {filename}")


def save_companies(filename: str, companies: list):
    """Save companies to JSON file"""
    output = {
        "metadata": {
            "verified_at": datetime.now().isoformat(),
            "total_companies": len(companies),
            "stats": {}
        },
        "companies": companies
    }
    
    # Calculate stats
    verified = [c for c in companies if c.get("verification", {}).get("status") == "verified"]
    failed = [c for c in companies if c.get("verification", {}).get("status") == "failed"]
    skipped = [c for c in companies if c.get("verification", {}).get("status") == "skipped"]
    spam = [c for c in companies if c.get("verification", {}).get("spam_score", 0) >= 3]
    
    output["metadata"]["stats"] = {
        "verified": len(verified),
        "failed": len(failed),
        "skipped": len(skipped),
        "spam_detected": len(spam),
        "verification_rate": f"{len(verified)/len(companies)*100:.1f}%" if companies else "0%"
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(companies)} companies to {filename}")


async def main():
    print("=== HealthTech Directory - Day 3: Verification ===")
    print()
    
    # Load companies
    print(f"Loading companies from {INPUT_FILE}...")
    companies = load_companies(INPUT_FILE)
    print(f"Loaded {len(companies)} companies")
    print()
    
    # Verify
    verifier = CompanyVerifier()
    print("Verifying websites...")
    verified_companies = await verifier.verify_all(companies)
    print()
    
    # Save
    save_companies(OUTPUT_FILE, verified_companies)
    print()
    
    # Print stats
    print("=== Verification Stats ===")
    print(f"Total: {verifier.stats['total']}")
    print(f"Verified: {verifier.stats['verified']}")
    print(f"Failed: {verifier.stats['failed']}")
    print(f"Skipped: {verifier.stats['skipped']}")
    print(f"Spam detected: {verifier.stats['spam']}")
    print()
    
    print(f"Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Usage

```bash
# Make executable
chmod +x verify.py

# Run verification
python verify.py
```

---

## Verification Results

| Status | Count | Action |
|--------|-------|--------|
| **Verified** | ✓ | Keep for enrichment |
| **Failed** | ✗ | Remove or manual review |
| **Skipped** | ○ | No website, check manually |
| **Spam** | ⚠️ | Remove immediately |

---

## Filter Criteria

```python
# Keep only verified companies
keep = [c for c in companies if c["verification"]["status"] == "verified"]

# Also remove spam
clean = [c for c in keep if c["verification"]["spam_score"] < 3]

# Minimum quality threshold
quality = [c for c in clean if c["data_quality"] in ["High", "Medium"]]
```

---

## Day 3 Deliverables

| File | Description | Target |
|------|-------------|--------|
| `gcc-healthtech-verified.json` | All verification results | 1,500+ verified |
| `gcc-healthtech-clean.json` | Only verified, non-spam | 1,000+ |

---

## Tips

1. **Rate limiting**: Crawl4AI respects robots.txt
2. **Caching**: Subsequent runs are faster
3. **Errors**: Some sites may block bots
4. **Quality**: Focus on quality over quantity

---

*Day 3 verification script for Crawl4AI*
