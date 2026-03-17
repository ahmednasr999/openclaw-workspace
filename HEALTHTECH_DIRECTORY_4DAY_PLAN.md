# HEALTHTECH DIRECTORY - 4-DAY BUILD
**GCC HealthTech Company Directory**
**Purpose:** Job search targets + ANCO consulting leads + Revenue

---

## EXECUTIVE SUMMARY

| Metric | Target |
|--------|--------|
| Companies | 5,000 |
| Verified | 3,000+ |
| Contactable | 1,000+ |
| Cost | ~$250 |
| Timeline | 4 days |

---

## TOOLS NEEDED

| Tool | Purpose | Cost |
|------|---------|------|
| **Outscraper** | Scrape company data | ~$50 |
| **Claude Code** | Clean + structure data | Free (existing) |
| **Crawl4AI** | Verify websites | Free (self-hosted) |
| **Claude Vision** | Image enrichment | API cost |
| **Cloudflare Pages** | Host directory | Free |
| **Notion** | CRM + pipeline | Free |

---

## DAY 1: SCRAPE

### Target: 5,000 GCC HealthTech Companies

#### Sources to Scrape
1. LinkedIn company search (HealthTech, GCC)
2. CB Insights / Crunchbase
3. Local directories (UAE, KSA, Egypt)
4. Industry associations

#### Outscraper Configuration
```bash
# Install Outscraper
npm install -g outscraper

# Scrape GCC HealthTech companies
outscraper scrape companies \
  --domain "linkedin.com" \
  --query "HealthTech UAE" \
  --limit 5000 \
  --output gcc-healthtech-raw.json
```

#### Alternative: Manual Sources
| Source | URL | Records |
|--------|-----|---------|
| Sadafco Directory | directory.healthtech.ae | ~500 |
| Dubai Health Authority | dha.gov.ae | ~300 |
| Saudi Health Council | sha.gov.sa | ~400 |
| Egypt Health Ministry | mohp.gov.eg | ~300 |
| Total | | ~5,000 |

#### Day 1 Deliverables
- [ ] `gcc-healthtech-raw.json` (5,000 companies)
- [ ] Company name, website, location
- [ ] Initial deduplication check

---

## DAY 2: CLEAN + STRUCTURE

### Target: 3,000 clean, deduplicated records

#### Claude Code Prompts

##### Pass 1: Deduplication
```
Clean this HealthTech company list:
1. Remove exact duplicates
2. Normalize company names (e.g., "LLC" vs "Limited")
3. Flag near-duplicates for review
4. Output: gcc-healthtech-deduped.json
```

##### Pass 2: Structure
```
Structure each record with:
{
  "company_name": "string",
  "website": "url",
  "linkedin": "url", 
  "location": {
    "country": "UAE/KSA/Egypt/GCC",
    "city": "Dubai/Riyah/Cairo",
    "address": "string"
  },
  "category": "Hospital|Clinic|HealthTech|MedTech|Payer|Provider",
  "size": "Startup|SME|Enterprise",
  "funding": "Bootstrapped|Seed|Series A|Series B|PE",
  "contact": {
    "linkedin_url": "url",
    "email_format": "string"
  },
  "hiring": {
    "pmo_roles": boolean,
    "tech_roles": boolean,
    "url": "url"
  },
  "data_quality": "High|Medium|Low"
}
```

##### Pass 3: Quality Scoring
```
Add quality score (1-10) based on:
- Website exists (2 points)
- LinkedIn present (2 points)
- Email format guessable (2 points)
- Hiring page exists (2 points)
- Location specific (2 points)

Output: gcc-healthtech-scored.json
```

#### Day 2 Deliverables
- [ ] `gcc-healthtech-deduped.json` (3,000+ companies)
- [ ] Quality scores for each record
- [ ] Structured data with all fields

---

## DAY 3: VERIFY + FILTER

### Target: 1,500 verified companies with live websites

#### Crawl4AI Configuration

```bash
# Install Crawl4AI
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
pip install -e .

# Verify websites
python verify.py \
  --input gcc-healthtech-scored.json \
  --output gcc-healthtech-verified.json \
  --workers 10
```

#### Verification Logic
```python
def verify_company(record):
    checks = []
    
    # Check 1: Website exists and loads
    website_ok = check_website(record['website'])
    checks.append(('website', website_ok))
    
    # Check 2: LinkedIn exists
    linkedin_ok = check_linkedin(record['linkedin'])
    checks.append(('linkedin', linkedin_ok))
    
    # Check 3: No obvious spam
    spam_score = check_spam(record)
    checks.append(('spam', spam_score < 3))
    
    # Check 4: Hiring page exists
    hiring_ok = check_hiring_page(record['website'])
    checks.append(('hiring', hiring_ok))
    
    # Overall quality
    passed = sum([c[1] for c in checks]) >= 3
    
    return {
        'record': record,
        'checks': dict(checks),
        'passed': passed,
        'verified_at': datetime.now().isoformat()
    }
```

#### Filtering Criteria
```yaml
KEEP:
  - Website: exists AND loads < 5s
  - LinkedIn: exists AND has >10 employees
  - No spam indicators
  - Hiring page: optional but preferred

REVIEW:
  - Website loads 5-10s
  - LinkedIn exists but <10 employees
  - Ambiguous category

DISCARD:
  - Website: doesn't exist OR loads >10s
  - LinkedIn: doesn't exist
  - Spam indicators present
  - Duplicate of already-verified company
```

#### Day 3 Deliverables
- [ ] `gcc-healthtech-verified.json` (1,500+ companies)
- [ ] Verification status for each record
- [ ] Spam scores

---

## DAY 4: ENRICH + LAUNCH

### Target: 1,000 enriched records + MVP launch

#### A. Image Enrichment (Claude Vision)

```python
# Get company logo using Claude Vision
import anthropic

client = anthropic.Anthropic()

def get_logo_info(company_name, website):
    prompt = f"""
    Find the logo URL for {company_name} ({website}).
    Return ONLY the logo URL or "NOT_FOUND".
    """
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text.strip()
```

#### B. Enrichment Pipeline

```python
def enrich_record(record):
    enriched = record.copy()
    
    # 1. Logo
    logo_url = get_logo_info(record['company_name'], record['website'])
    enriched['logo_url'] = logo_url
    
    # 2. Employee count from LinkedIn
    enriched['employees'] = get_linkedin_employees(record['linkedin'])
    
    # 3. Recent news
    enriched['recent_news'] = get_news_summary(record['company_name'])
    
    # 4. PMO maturity
    enriched['pmo_maturity'] = assess_pmo_maturity(record)
    
    # 5. Contact enrichment
    enriched['contact_enriched'] = enrich_contacts(record)
    
    return enriched
```

#### C. PMO Maturity Assessment

```python
def assess_pmo_maturity(record):
    """
    Assess PMO maturity based on website signals:
    - Project management software mentioned
    - Digital transformation language
    - Case studies / success stories
    - Team page with PMO roles
    """
    signals = []
    
    # Check for PMO indicators on website
    if 'project management' in website_text: signals.append('pm_software')
    if 'digital transformation' in website_text: signals.append('digital_focus')
    if 'case studies' in website_text: signals.append('evidence_based')
    if 'pmp' in team_page: signals.append('certified_team')
    
    maturity = {
        'signals': signals,
        'score': len(signals) * 25,  # 0-100
        'level': 'High' if len(signals) >= 3 else 'Medium' if len(signals) >= 1 else 'Low'
    }
    
    return maturity
```

#### D. MVP Launch (Notion + Cloudflare Pages)

##### Option 1: Notion Database
```markdown
1. Create Notion database
2. Import gcc-healthtech-enriched.json
3. Share read-only link
4. Use as CRM
```

##### Option 2: Simple Search Interface (Cloudflare Pages)

```html
<!-- index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>GCC HealthTech Directory</title>
    <style>
        .company-card { border: 1px solid #ddd; padding: 16px; margin: 8px; }
        .logo { max-width: 60px; }
    </style>
</head>
<body>
    <h1>GCC HealthTech Directory</h1>
    <input type="text" id="search" placeholder="Search...">
    <div id="results"></div>
    <script src="data.json"></script>
    <script>
        // Simple search interface
        document.getElementById('search').addEventListener('input', (e) => {
            const results = companies.filter(c => 
                c.company_name.toLowerCase().includes(e.target.value.toLowerCase())
            );
            render(results);
        });
    </script>
</body>
</html>
```

#### E. Deployment

```bash
# Deploy to Cloudflare Pages
wrangler pages deploy ./dist --project-name=gcc-healthtech-directory
```

#### Day 4 Deliverables
- [ ] `gcc-healthtech-enriched.json` (1,000+ companies)
- [ ] Logo URLs for each company
- [ ] PMO maturity assessment
- [ ] Contact enrichment
- [ ] Live MVP: gcc-healthtech.directory

---

## DATA SCHEMA

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "company_name": {"type": "string"},
    "website": {"type": "string", "format": "uri"},
    "linkedin": {"type": "string", "format": "uri"},
    "location": {
      "type": "object",
      "properties": {
        "country": {"type": "string", "enum": ["UAE", "KSA", "Egypt", "Kuwait", "Qatar", "Bahrain", "Oman"]},
        "city": {"type": "string"},
        "address": {"type": "string"}
      }
    },
    "category": {"type": "string", "enum": ["Hospital", "Clinic", "HealthTech", "MedTech", "Payer", "Provider", "Other"]},
    "size": {"type": "string", "enum": ["Startup", "SME", "Enterprise"]},
    "funding": {"type": "string", "enum": ["Bootstrapped", "Seed", "Series A", "Series B", "PE", "Public"]},
    "logo_url": {"type": "string", "format": "uri"},
    "employees": {"type": "integer"},
    "hiring": {
      "type": "object",
      "properties": {
        "pmo_roles": {"type": "boolean"},
        "tech_roles": {"type": "boolean"},
        "url": {"type": "string", "format": "uri"}
      }
    },
    "pmo_maturity": {
      "type": "object",
      "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "level": {"type": "string", "enum": ["High", "Medium", "Low"]},
        "signals": {"type": "array", "items": {"type": "string"}}
      }
    },
    "contact_enriched": {"type": "boolean"},
    "data_quality": {"type": "string", "enum": ["High", "Medium", "Low"]},
    "verified_at": {"type": "string", "format": "date-time"}
  }
}
```

---

## COST BREAKDOWN

| Item | Cost | Notes |
|------|------|-------|
| Outscraper (1 month) | $50 | Can cancel after |
| Claude Vision API | $20 | ~1,000 images |
| Hosting (Cloudflare Pages) | $0 | Free tier |
| Notion | $0 | Free tier |
| **Total** | **~$70** | Less than $250 |

---

## USAGE: JOB SEARCH

### Search Queries

```json
{
  "filter": {
    "country": "UAE",
    "category": "Hospital",
    "pmo_maturity.level": "High",
    "hiring.pmo_roles": true
  }
}
```

This gives: UAE hospitals with high PMO maturity actively hiring PMO roles.

### Output
```
• 50 target companies
• 200+ contactable individuals
• Ready for LinkedIn outreach
```

---

## USAGE: ANCO CONSULTING

### Search Queries

```json
{
  "filter": {
    "pmo_maturity.level": "Low",
    "size": "Enterprise",
    "employees": {"$gt": 500}
  }
}
```

This gives: Large enterprises with low PMO maturity = ANCO clients.

### Output
```
• 100 potential ANCO clients
• Sales enablement ready
• Personalized outreach possible
```

---

## NEXT STEPS

### Day 1 Actions
- [ ] Sign up for Outscraper
- [ ] Scrape 5,000 companies
- [ ] Save raw data

### Day 2 Actions  
- [ ] Clean with Claude Code
- [ ] Structure data
- [ ] Quality score

### Day 3 Actions
- [ ] Verify with Crawl4AI
- [ ] Filter spam
- [ ] Verify 1,500+ websites

### Day 4 Actions
- [ ] Enrich with Claude Vision
- [ ] PMO maturity assessment
- [ ] Launch MVP

---

## METRICS

| Metric | Day 1 | Day 2 | Day 3 | Day 4 |
|--------|-------|-------|-------|-------|
| Raw records | 5,000 | 5,000 | 5,000 | 5,000 |
| Deduplicated | - | 3,000 | 3,000 | 3,000 |
| Verified | - | - | 1,500 | 1,500 |
| Enriched | - | - | - | 1,000 |
| Contactable | - | - | - | 500 |

---

## SUCCESS CRITERIA

| Metric | Target |
|--------|--------|
| Companies scraped | 5,000 |
| Unique companies | 3,000+ |
| Verified websites | 1,500+ |
| Companies with hiring data | 500+ |
| Companies with PMO maturity Low | 100+ |
| Cost | <$250 |

---

*Plan created: 2026-02-17*
