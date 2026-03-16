#!/usr/bin/env python3
"""
LinkedIn Job Scout v2 - Playwright-based
Searches all keyword/location combos, extracts job IDs, deduplicates
Output: /tmp/scout-results.json
"""

import asyncio
import json
import re
import sys
from pathlib import Path
from datetime import datetime

COOKIES_FILE = Path(__file__).parent.parent / "config" / "linkedin-cookies.json"
OUTPUT_FILE = Path("/tmp/scout-results.json")

KEYWORDS = [
    "PMO Director",
    "VP Digital Transformation",
    "VP Technology",
    "CTO",
    "Head of AI",
    "Director Digital Transformation",
    "Chief Digital Officer",
    "Head of Product",
    "Senior Director Technology",
    "VP HealthTech",
]

LOCATIONS = [
    "United Arab Emirates",
    "Saudi Arabia",
    "Qatar",
    "Bahrain",
    "Kuwait",
    "Oman",
]


async def search_jobs(context, keyword, location):
    """Search one keyword/location combo, return list of {title, company, id, location}"""
    page = await context.new_page()
    kw = keyword.replace(" ", "%20")
    loc = location.replace(" ", "%20")
    url = f"https://www.linkedin.com/jobs/search/?keywords={kw}&location={loc}&f_TPR=r604800"

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)

        jobs = await page.evaluate('''() => {
            const cards = document.querySelectorAll('.job-card-container, .jobs-search-results__list-item, li.ember-view');
            return Array.from(cards).slice(0, 15).map(card => {
                const title = card.querySelector('.job-card-list__title, .artdeco-entity-lockup__title');
                const company = card.querySelector('.job-card-container__primary-description, .artdeco-entity-lockup__subtitle');
                const loc = card.querySelector('.job-card-container__metadata-item, .artdeco-entity-lockup__caption');
                const link = card.querySelector('a[href*="jobs/view"]');
                const href = link ? link.href : '';
                const idMatch = href.match(/jobs\\/view\\/(\\d+)/);
                return {
                    title: title ? title.innerText.trim() : '',
                    company: company ? company.innerText.trim() : '',
                    location: loc ? loc.innerText.trim() : '',
                    id: idMatch ? idMatch[1] : '',
                };
            }).filter(j => j.title && j.id);
        }''')

        await page.close()
        return jobs
    except Exception as e:
        await page.close()
        return []


async def main():
    if not COOKIES_FILE.exists():
        print("ERROR: No LinkedIn cookies found")
        sys.exit(1)

    with open(COOKIES_FILE) as f:
        cookies = json.load(f)

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        await context.add_cookies(cookies)

        all_jobs = {}
        total = len(KEYWORDS) * len(LOCATIONS)
        done = 0

        for kw in KEYWORDS:
            for loc in LOCATIONS:
                done += 1
                sys.stdout.write(f"\r[{done}/{total}] {kw} | {loc}                    ")
                sys.stdout.flush()

                jobs = await search_jobs(context, kw, loc)
                for j in jobs:
                    if j["id"] not in all_jobs:
                        all_jobs[j["id"]] = {
                            **j,
                            "search_keyword": kw,
                            "search_location": loc,
                            "url": f"https://www.linkedin.com/jobs/view/{j['id']}",
                        }

                # Small delay between searches to be conservative
                await asyncio.sleep(1)

        await browser.close()

    print(f"\n\nFound {len(all_jobs)} unique jobs across {total} searches")

    # Save results
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "searches": total,
        "unique_jobs": len(all_jobs),
        "jobs": list(all_jobs.values()),
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    for j in sorted(all_jobs.values(), key=lambda x: x["title"]):
        print(f"  {j['title']} | {j['company']} | {j['location']} | {j['id']}")

    print(f"\nResults saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
