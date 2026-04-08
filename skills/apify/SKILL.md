# Apify Skill

Use Apify to scrape websites, access LinkedIn, X/Twitter via pre-built Actors.

## Trigger
- "apify", "scrape", "run actor", "web scrape", "linkedin", "x scraper"

## Setup
API key: stored at `~/.openclaw/credentials/apify.txt`

## Quick Test
```bash
curl -s "https://api.apify.com/v2/users/me?token=$(cat ~/.openclaw/credentials/apify.txt)"
```

## Common Actors for Job Search

| Actor | Use Case |
|-------|----------|
| linkedin/linkedin-jobs-scraper | LinkedIn job listings |
| linkedin/linkedin-profile-scraper | LinkedIn profiles |
| apify/x-twitter-scraper | X/Twitter data |
| apify/youtube-scraper | YouTube search |
| apify/google-jobs-scraper | Google Jobs |

## Usage Examples

### Run LinkedIn Job Scraper
```bash
curl -s -X POST "https://api.apify.com/v2/acts/linkedin~linkedin-jobs-scraper/runs" \
  -H "Authorization: Token $(cat ~/.openclaw/credentials/apify.txt)" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "VP Engineering", "location": "United Arab Emirates"}'
```

### Search Actors
```bash
curl -s "https://api.apify.com/v2/acts?token=$(cat ~/.openclaw/credentials/apify.txt)&search=linkedin"
```

### Get Actor Info
```bash
curl -s "https://api.apify.com/v2/acts/linkedin~linkedin-jobs-scraper?token=$(cat ~/.openclaw/credentials/apify.txt)"
```

## Important Notes
- FREE plan: $5/month compute credits
- Data retention: 7 days
- 25 concurrent actor runs max
- Most public actors work on free tier
- Actors bypass bot detection automatically
