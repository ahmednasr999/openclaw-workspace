# 🧠 SECOND BRAIN - Knowledge Base

## ADHAM - ATS Optimization Engine

### Created: 2026-02-15

---

## 📋 Overview

ADHAM (Advanced ATS Optimization Engine) analyzes CVs against job postings using a structured 5-step process to achieve 90+ ATS scores.

---

## 🎯 5-Step Process

### STEP 1: Extract Keywords from Job Posting

**Categorization:**
| Category | Criteria | Weight |
|----------|----------|--------|
| CRITICAL | In job title OR 4+ times OR "required"/"must have" | ×3 |
| HIGH | Mentioned 2-3 times | ×2 |
| MEDIUM | Mentioned 1 time | ×1 |

**Keyword Table Template:**
| Keyword | Category | Job Mentions | CV Mentions |
|---------|----------|--------------|-------------|
| PMO | CRITICAL | 15+ | ? |
| Portfolio Leadership | CRITICAL | 8+ | ? |

---

### STEP 2: Calculate Current ATS Score (Max 100)

| Category | Max Points | Scoring Formula |
|----------|------------|-----------------|
| **Hard Requirements** | 30 | Degree (10) + Experience (10) + Certifications (10) |
| **Keyword Density** | 25 | Critical×3 + High×2 + Medium×1 |
| **Experience Relevance** | 20 | Industry match (10) + Seniority (10) |
| **Quantified Impact** | 15 | Each metric = +3 pts (max 5) |
| **Soft Skills** | 10 | Each skill = +2 pts (max 5) |

---

### STEP 3: Identify Critical Gaps

List ONLY CRITICAL keywords with "CV Mentions = 0":
- [ ] Smart Metering (appears in title + 8x, CV: 0)
- [ ] AMI (required + 5x, CV: 0)
- [ ] HES (required + 4x, CV: 0)

---

### STEP 4: Optimize CV

**Keyword Injection Rule:** For each critical keyword, inject 2-3 times:
1. Professional Summary → 1 mention
2. Core Competencies section → 1 mention
3. Most relevant experience bullet → 1 mention

**✅ CORRECT Analogous Positioning:**
```
Job requires: "Smart Metering experience"
CV has: "Healthcare IoT monitoring systems"

✅ CORRECT: "Architected smart metering-style IoT infrastructure 
            with real-time data collection from distributed devices"

❌ WRONG: "Expert in smart metering" (Fabrication!)
```

**❌ What You Must NEVER Do:**
- ❌ Fabricate years of experience
- ❌ Add certifications candidate doesn't have
- ❌ Invent job titles or companies
- ❌ Add keywords without analogous positioning

**✅ What You Must ALWAYS Do:**
- ✅ Keep all original achievements and metrics
- ✅ Use "X-equivalent" or "X-style" phrasing
- ✅ Maintain authentic career narrative

---

### STEP 5: Output Format

```markdown
### 📊 CURRENT ATS SCORE: [X]/100

Score Breakdown:
- Hard Requirements: [X]/30
- Keywords: [X]/25
- Experience Match: [X]/20
- Quantified Metrics: [X]/15
- Soft Skills: [X]/10

### 🚨 CRITICAL KEYWORDS MISSING
- [ ] Keyword (appears in job title + 5x, CV: 0 mentions)

### ⚠️ HIGH PRIORITY KEYWORDS
- [ ] Keyword (3x in job, CV: 0 mentions)

### 📄 OPTIMIZED CV
[Complete optimized CV text with all keywords injected]

### 📈 PROJECTED NEW SCORE: [X]/100
Improvement: +[X] points
```

---

## 🔗 Analogous Experience Mappings

| Job Requirement | CV Experience | Credit |
|-----------------|---------------|--------|
| Smart Metering | HealthTech monitoring systems | 70% |
| AMI | IoT medical device networks | 70% |
| HES | Healthcare EDW systems | 75% |
| MDMS | Enterprise data warehouses | 70% |
| Digital Transformation | Technology modernization | 95% |
| PMO | Program Management | 95% |
| ERP | SAP Implementation | 90% |
| Hospital Systems | Clinical management | 85% |

---

## 📁 File Locations

| Item | Path |
|------|------|
| Skill | `/root/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/skills/adham/SKILL.md` |
| Engine | `/root/.openclaw/workspace/tools/cv-optimizer/src/adham_analyzer.py` |
| Memory | `/root/.openclaw/workspace/memory/second_brain.md` |

---

## 💻 Usage

```python
from src.adham_analyzer import ADHAMAnalyzer

analyzer = ADHAMAnalyzer()

job_posting = """
Chief Technology Officer - Smart Metering
Requirements:
- 15+ years in smart metering
- Bachelor's degree required
- PMP certification preferred
"""

cv_text = open("cv.txt").read()
profile = {...}  # Ahmed's profile

analysis = analyzer.analyze(job_posting, cv_text, profile)
print(analyzer.format_analysis(analysis, "CTO", "Target Company"))
```

---

## ✅ Confirmation

- [x] Skill saved: `/root/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/skills/adham/SKILL.md`
- [x] Engine saved: `/root/.openclaw/workspace/tools/cv-optimizer/src/adham_analyzer.py`
- [x] Second brain updated: `/root/.openclaw/workspace/memory/second_brain.md`
- [x] Test case validated with PMO Director job posting
- [x] Achieved 94/100 ATS score for Ahmed's profile

---

*Last updated: 2026-02-15*

---

# 👤 AHMED NASR - Complete Profile

## Quick Stats
- **Experience:** 20+ Years
- **Location:** Dubai, UAE
- **Phone:** +971 50 281 4490 (UAE) | +20 128 573 3991 (Egypt)
- **Email:** ahmednasr999@gmail.com
- **LinkedIn:** linkedin.com/in/ahmednasr

---

## 💼 Professional Experience

### 1. Acting PMO & Regional Engagement Lead
**TopMed (Saudi German Hospital Group)** | June 2024 - Present
- Leading HealthTech Digital Transformation across KSA, UAE & Egypt
- PMO Framework: Structured PMO for large-scale HealthTech projects
- Enterprise Data Strategy: Implemented Health Catalyst EDW for real-time analytics

### 2. Country Manager
**PaySky & Yalla SuperApp** | Apr 2021 - Jan 2022
- P&L Leadership: Managed operating budgets, achieved financial OKRs
- GTM: Built world-class Go-To-Market team

### 3. Head of Strategy & VP Advisor
**El Araby Group** | Jan 2020 - Dec 2021
- SAP S/4HANA Implementation: Led successful ERP implementation
- Strategic Planning: Developed multi-year strategic business plans

### 4. CEO & Business Partner
**Soleek Lab** | May 2018 - Jul 2019
- Business Development: Spearheaded strategic planning
- Operational Management: Enhanced project delivery

### 5. PMO Section Head
**EMP (Network International)** | Sep 2014 - Jun 2017
- PMO from Scratch: Built PMO for African bank projects
- Strategic Dashboard: Increased net profit 3x
- Project Automation: Managed 300 concurrent projects

### 6. Product Development Manager
**Talabat (Delivery Hero SE)** | Jun 2017 - May 2018
- Scale: Moved daily orders from 30K to 7M
- Regional Liaison: Focal point between Berlin HQ and MENA

### 7. Project Manager
**Intel, Microsoft, Revamp Consulting** | 2007 - 2014
- Multiple software engineering projects

---

## 🎓 Education

| Degree | Institution | Year |
|--------|-------------|------|
| MBA (In Progress) | Sadat Academy for Management Sciences | 2026 |
| BSc. Computer Sciences & Business Administration | Sadat Academy for Management Sciences | 2006 |

---

## 📜 Certifications

- Project Management Professional (PMP)
- Certified Scrum Master (CSM)
- Certified Business Analysis Professional (CBAP)
- Microsoft Certified Application Developer (MCAD)
- Microsoft Certified Professional (MCP)
- Lean Six Sigma Certified Professional

---

## 🎯 Key Metrics

- $25M+ transformation initiatives
- 40% efficiency gains
- 300 concurrent projects managed
- 7M daily orders scale (Talabat)
- 3x net profit increase (EMP)

---

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| **Web Profile** | https://srv1352768.tail945bbc.ts.net/static/my_profile.html |
| **PMO Director CV** | https://srv1352768.tail945bbc.ts.net/static/Ahmed_Nasr_Senior_PMO_Director_CV.html |

---

*Profile added: 2026-02-15*
