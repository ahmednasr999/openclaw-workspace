#!/usr/bin/env python3
"""
LinkedIn JD Fetcher (Camofox Edition)
Usage: python3 linkedin-jd-fetcher.py <linkedin_job_url>
Output: JSON with title, company, location, jd
Uses camofox-browser for anti-detection browsing.
Fallback: raw Playwright if camofox server is down.
"""

import sys
import json
import subprocess
import time
from pathlib import Path

COOKIES_FILE = Path(__file__).parent.parent / "config" / "linkedin-cookies.json"
CAMOFOX_PORT = 9377

EXTRACT_JS = """
(() => {
    const getText = (selector) => {
        const el = document.querySelector(selector);
        return (el && el.innerText && el.innerText.length > 50) ? el.innerText.trim() : null;
    };
    const title = document.querySelector('h1') ? document.querySelector('h1').innerText.trim() : null;
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
    if (!jd) {
        const main = document.querySelector('main');
        if (main) jd = main.innerText.trim().substring(0, 8000);
    }
    return JSON.stringify({ title, company, location, jd });
})()
"""


def run_camofox(args: list, timeout: int = 30) -> tuple:
    """Run a camofox-browser CLI command. Returns (stdout, stderr, returncode)."""
    cmd = ["camofox-browser", "--format", "json"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", 1


def camofox_health() -> bool:
    """Check if camofox server is running."""
    out, _, rc = run_camofox(["health"], timeout=5)
    return rc == 0 and "true" in out


def fetch_jd_camofox(url: str) -> dict:
    """Fetch JD using camofox-browser CLI (anti-detection)."""

    # Open the URL
    out, err, rc = run_camofox(["open", url], timeout=30)
    if rc != 0:
        return {"error": f"camofox open failed: {err}", "jd": None}

    try:
        tab_data = json.loads(out)
        tab_id = tab_data.get("tabId", "")
    except (json.JSONDecodeError, AttributeError):
        # Try to extract tabId from text output
        tab_id = ""
        for line in out.split("\n"):
            if "tabId" in line:
                tab_id = line.split(":")[-1].strip().strip('"')
                break

    if not tab_id:
        return {"error": "No tabId returned from camofox open", "jd": None}

    try:
        # Import cookies
        if COOKIES_FILE.exists():
            run_camofox(["cookie", "import", str(COOKIES_FILE), tab_id], timeout=10)
            # Navigate again with cookies
            run_camofox(["navigate", url, tab_id], timeout=30)

        # Wait for page to settle
        time.sleep(3)

        # Accept cookie consent if present
        run_camofox(["click", "button:has-text('Accept')", tab_id], timeout=5)
        time.sleep(1)

        # Click "Show more" to expand JD
        for selector in [
            "button.show-more-less-html__button",
            "button[aria-label*='Show more']",
            "button.jobs-description__footer-button",
        ]:
            run_camofox(["click", selector, tab_id], timeout=3)
            time.sleep(0.5)

        # Extract JD content
        out, err, rc = run_camofox(["eval", EXTRACT_JS, tab_id], timeout=15)

        if rc == 0 and out:
            try:
                # Parse the JSON response from camofox eval
                eval_result = json.loads(out)
                # The eval result might be nested in a "result" key
                result_str = eval_result.get("result", out) if isinstance(eval_result, dict) else out
                if isinstance(result_str, str):
                    result = json.loads(result_str)
                else:
                    result = result_str
                return result
            except (json.JSONDecodeError, TypeError):
                pass

        # Fallback: use get-text
        out, _, rc = run_camofox(["get-text", tab_id], timeout=15)
        if rc == 0 and out and len(out) > 200:
            return {"title": None, "company": None, "location": None, "jd": out[:8000]}

        return {"error": "Could not extract JD content", "jd": None}

    finally:
        # Always close the tab
        run_camofox(["close", tab_id], timeout=5)


def fetch_jd_playwright(url: str) -> dict:
    """Fallback: fetch JD using raw Playwright (original method)."""
    import asyncio

    async def _fetch():
        from playwright.async_api import async_playwright

        if not COOKIES_FILE.exists():
            return {"error": "No LinkedIn cookies found.", "jd": None}

        with open(COOKIES_FILE) as f:
            cookies = json.load(f)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
            )
            await context.add_cookies(cookies)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)

                try:
                    btn = page.get_by_role("button", name="Accept")
                    if await btn.is_visible(timeout=2000):
                        await btn.click()
                        await page.wait_for_timeout(1500)
                except Exception:
                    pass

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

                pw_extract = """
                () => {
                    const getText = (sel) => { const el = document.querySelector(sel); return (el && el.innerText && el.innerText.length > 50) ? el.innerText.trim() : null; };
                    const title = document.querySelector('h1') ? document.querySelector('h1').innerText.trim() : null;
                    const company = getText('.job-details-jobs-unified-top-card__company-name') || getText('.topcard__org-name-link');
                    const location = getText('.job-details-jobs-unified-top-card__bullet') || getText('.topcard__flavor--bullet');
                    const sels = ['.jobs-description__content','.jobs-description-content__text','.show-more-less-html__markup','.description__text','#job-details'];
                    let jd = null;
                    for (const s of sels) { const el = document.querySelector(s); if (el && el.innerText && el.innerText.length > 200) { jd = el.innerText.trim(); break; } }
                    if (!jd) { const main = document.querySelector('main'); if (main) jd = main.innerText.trim().substring(0, 8000); }
                    return { title, company, location, jd };
                }
                """
                result = await page.evaluate(pw_extract)
                return result

            except Exception as e:
                return {"error": str(e), "jd": None}
            finally:
                await browser.close()

    return asyncio.run(_fetch())


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: linkedin-jd-fetcher.py <url>"}))
        sys.exit(1)

    url = sys.argv[1]

    # Try camofox first, fall back to Playwright
    if camofox_health():
        result = fetch_jd_camofox(url)
        result["engine"] = "camofox"
    else:
        result = fetch_jd_playwright(url)
        result["engine"] = "playwright-fallback"

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
