# LinkedIn Gulf Jobs Scraper

Use this skill to search LinkedIn jobs in GCC countries without login.

## Trigger
- "linkedin jobs", "gulf jobs", "dubai jobs", "saudi jobs", "riyadh jobs"

## How It Works
Uses web_fetch to access LinkedIn job search results without authentication.

## Usage

### Search Commands
Tell me what to search using this format:

```
Search LinkedIn jobs for [keyword] in [city], [country]
```

### Examples
- "Search LinkedIn jobs for Digital Transformation in Riyadh, Saudi Arabia"
- "Find VP Digital Transformation jobs in Dubai, UAE"
- "Search Chief Technology Officer jobs in Qatar"

### What You Get
- Job titles
- Companies
- Locations
- Links to full descriptions

### GCC Locations Supported
- UAE: Dubai, Abu Dhabi, Sharjah
- Saudi Arabia: Riyadh, Jeddah, Dammam
- Qatar: Doha
- Bahrain: Manama
- Kuwait: Kuwait City
- Oman: Muscat

### Seniority Levels
- VP / Vice President
- Director / Head
- Chief / C-Suite
- Senior Manager
- Principal

## Technical Note
This uses the public LinkedIn job search (no login required). 
Full job descriptions may require login, but job titles, companies, 
and locations are accessible.
