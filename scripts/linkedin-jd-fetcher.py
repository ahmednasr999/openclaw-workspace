#!/usr/bin/env python3
"""
LinkedIn JD Fetcher
Usage: python3 linkedin-jd-fetcher.py <linkedin_job_url>
Output: JSON with title, company, location, jd
Requires: config/linkedin-cookies.json with li_at cookie
"""

import sys
import json
import asyncio
from pathlib import Path

COOKIES_FILE = Path(__file__).parent.parent / "config" / "linkedin-cookies.json"

EXTRACT_JS = """
() => {
    const getText = (selector) => {
        const el = document.querySelector(selector);
        return (el && el.innerText && el.innerText.length > 50) ? el.innerText.trim() : null;
    };
    const title = getText('h1');
    const company = getText('.job-details-jobs-unified-top-card__company-name') ||
                    getText('.topcard__org-name-link');
    const location = getText('.job-details-jobs-unified-top-card__bullet') ||
                     getText('.topcard__flavor--bullet');
    const jdSelectors = [
        '.jobs-description__content',
        '.jobs-description-content__text',
        '.show-more-less-html__markup',
        '.description__text',
        '#job-details',
    ];
    let jd = null;
    for (const sel of jdSelectors) {
        const el = document.querySelector(sel);
        if (el && el.innerText && el.innerText.length > 200) {
            jd = el.innerText.trim();
            break;
        }
    }
    // Fallback: grab main content
    if (!jd) {
        const main = document.querySelector('main');
        if (main) jd = main.innerText.trim().substring(0, 8000);
    }
    return { title, company, location, jd };
}
"""

async def fetch_jd(url: str) -> dict:
    from playwright.async_api import async_playwright

    if not COOKIES_FILE.exists():
        return {"error": "No LinkedIn cookies found. Run linkedin-cookie-setup.py first.", "jd": None}

    with open(COOKIES_FILE) as f:
        cookies = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        await context.add_cookies(cookies)

        page = await browser.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # Accept cookie consent if shown
            try:
                btn = page.get_by_role("button", name="Accept")
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    await page.wait_for_timeout(1500)
            except Exception:
                pass

            # Click "Show more" to expand truncated JD
            try:
                show_more = page.locator(
                    "button.show-more-less-html__button, "
                    "button[aria-label*='Show more'], "
                    "button.jobs-description__footer-button"
                ).first
                if await show_more.is_visible(timeout=2000):
                    await show_more.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                pass

            result = await page.evaluate(EXTRACT_JS)
            await browser.close()
            return result

        except Exception as e:
            await browser.close()
            return {"error": str(e), "jd": None}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: linkedin-jd-fetcher.py <url>"}))
        sys.exit(1)

    url = sys.argv[1]
    result = asyncio.run(fetch_jd(url))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
