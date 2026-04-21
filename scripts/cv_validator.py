#!/usr/bin/env python3
"""
CV Validator — Single source of truth for CV quality checks.
Used by both auto-cv-builder.py (Path B) and executive-cv-builder skill (Path A).

Usage:
    from cv_validator import validate_cv, auto_fix_cosmetic
    passed, blockers, cosmetic = validate_cv(html_path, pdf_path=None)
    if cosmetic:
        fixes = auto_fix_cosmetic(html_path, cosmetic)

CLI:
    python3 cv_validator.py /path/to/cv.html [/path/to/cv.pdf]
"""

import os
import re
import subprocess
import sys


def validate_html(html_path):
    """Validate CV HTML content. Returns (blockers: list, cosmetic: list)."""
    blockers = []
    cosmetic = []

    try:
        with open(html_path) as f:
            html = f.read()
    except Exception as e:
        return [f"Cannot read HTML: {e}"], []

    html_lower = html.lower()

    # ── BLOCKERS (fail the CV, require re-generation) ──

    # 1. Education section must exist (supports both <h2> and <div class="section-title">)
    edu_patterns = [
        "<h2>education</h2>", "<h2>education &",
        "section-title\">education<", "section-title\">education &"
    ]
    if not any(p in html_lower for p in edu_patterns):
        blockers.append("MISSING_EDUCATION: Education section not found")

    # 2. Certifications section must exist (supports both <h2> and <div class="section-title">)
    cert_patterns = [
        "certifications</h2>", "professional certifications</h2>",
        "section-title\">certifications<", "section-title\">professional certifications<"
    ]
    if not any(p in html_lower for p in cert_patterns):
        blockers.append("MISSING_CERTS: Certifications section not found")

    # 3. Contact info
    if "ahmednasr999@gmail.com" not in html:
        blockers.append("MISSING_EMAIL: ahmednasr999@gmail.com not found")
    if "+971 50 281 4490" not in html and "+97150281" not in html.replace(" ", ""):
        blockers.append("MISSING_PHONE: Phone number not found")

    # 4. Minimum content (thin CV = likely incomplete generation)
    if len(html) < 3000:
        blockers.append(f"THIN_CONTENT: HTML only {len(html)} chars, likely incomplete")

    # 5. Professional Experience section must exist
    _has_exp = (
        "<h2>professional experience</h2>" in html_lower
        or "<h2>experience</h2>" in html_lower
        or "professional experience" in html_lower  # covers section-title divs
    )
    if not _has_exp:
        blockers.append("MISSING_EXPERIENCE: Professional Experience section not found")

    # 6. Header violation: role/company should NOT be in header area
    # Check first 500 chars for "CV", "Resume", "Curriculum Vitae"
    # Strip <title>...</title> before checking header area to avoid false positives
    _header_raw = re.sub(r'<title[^>]*>.*?</title>', '', html[:500], flags=re.IGNORECASE|re.DOTALL)
    header_area = _header_raw.lower()
    for bad in ["curriculum vitae", " cv<", " cv ", ">cv<", "resume"]:
        if bad in header_area:
            blockers.append(f"HEADER_VIOLATION: Found '{bad.strip()}' in header area")
            break

    # 7. Reverse chronological order check
    # Match dates in job header rows only (job-date, job-date-cell, or date-cell class)
    date_pattern = re.compile(
        r'class=["\']job[-_]?date(?:[-_]cell)?["\'][^>]*>([^<]+)<',
        re.IGNORECASE,
    )
    dates_found = date_pattern.findall(html)
    if not dates_found:
        # Fallback: look for date patterns after job-title spans (common in older CVs)
        date_pattern2 = re.compile(
            r'(?:20\d{2}\s*[-\u2013\u2014]\s*(?:Present|20\d{2}|19\d{2}))',
            re.IGNORECASE,
        )
        # Only check first occurrence per .job block
        job_blocks = re.split(r'class=["\']job["\']', html, flags=re.IGNORECASE)
        for block in job_blocks[1:]:  # skip pre-first-job content
            m = date_pattern2.search(block[:300])  # date should be in first 300 chars of block
            if m:
                dates_found.append(m.group(0))
    if dates_found:
        year_pattern = re.compile(r"(\d{4})")
        years = []
        for d in dates_found:
            m = year_pattern.search(d)
            if m:
                yr = int(m.group(1))
                if "present" in d.lower():
                    yr = 9999
                years.append((yr, d.strip()))
        for i in range(len(years) - 1):
            if years[i][0] < years[i + 1][0]:
                blockers.append(
                    f"WRONG_ORDER: '{years[i][1]}' appears before '{years[i + 1][1]}' (not reverse chronological)"
                )
                break

    # ── COSMETIC (auto-fixable, don't block) ──

    # Em dashes
    em_count = html.count("—") + html.count("&mdash;")
    if em_count > 0:
        cosmetic.append(f"EM_DASH: {em_count} em dashes found")

    # En dashes
    en_count = html.count("–") + html.count("&ndash;")
    if en_count > 0:
        cosmetic.append(f"EN_DASH: {en_count} en dashes found")

    # Broken entities
    for bad, fix in [("ATandT", "AT&amp;T"), ("AT and T", "AT&amp;T")]:
        if bad in html:
            cosmetic.append(f"ENTITY: '{bad}' should be '{fix}'")

    return blockers, cosmetic


def validate_pdf(pdf_path):
    """Validate PDF file. Returns (blockers: list, cosmetic: list)."""
    blockers = []
    cosmetic = []

    if not os.path.exists(pdf_path):
        return [f"PDF_MISSING: {pdf_path} does not exist"], []

    size = os.path.getsize(pdf_path)

    # Size checks
    if size < 5000:
        blockers.append(f"PDF_TINY: {size}B, likely empty or broken")
    elif size < 15000:
        cosmetic.append(f"PDF_SMALL: {size}B, below expected 15KB minimum")

    if size > 100000:
        cosmetic.append(f"PDF_LARGE: {size}B, may have embedded fonts/images")

    # Text extraction check
    try:
        r = subprocess.run(
            ["pdftotext", pdf_path, "-"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        text = r.stdout

        chars = len(text.strip())
        if chars < 2000:
            blockers.append(f"PDF_NO_TEXT: Only {chars} extractable chars (ATS cannot read)")

        # Em dash in extracted text
        em_in_pdf = text.count("—") + text.count("–")
        if em_in_pdf > 0:
            cosmetic.append(f"PDF_EM_DASH: {em_in_pdf} em/en dashes in extracted text")

        # Header violation in extracted text
        first_lines = "\n".join(text.split("\n")[:5]).lower()
        for bad in ["curriculum vitae", " cv ", "resume"]:
            if bad in first_lines:
                blockers.append(f"PDF_HEADER: Found '{bad.strip()}' in first lines of extracted text")
                break

        # Contact info in extracted text
        if "ahmednasr999" not in text.lower():
            blockers.append("PDF_NO_CONTACT: Email not found in extracted text")

    except subprocess.TimeoutExpired:
        cosmetic.append("PDF_EXTRACT_TIMEOUT: pdftotext timed out")
    except FileNotFoundError:
        cosmetic.append("PDF_NO_PDFTOTEXT: pdftotext not installed, skipping extraction checks")
    except Exception as e:
        cosmetic.append(f"PDF_EXTRACT_ERROR: {e}")

    return blockers, cosmetic


def validate_cv(html_path, pdf_path=None):
    """
    Full CV validation. Returns (passed: bool, blockers: list, cosmetic: list).
    
    If pdf_path is provided, runs both HTML and PDF checks.
    """
    blockers, cosmetic = validate_html(html_path)

    if pdf_path:
        pdf_blockers, pdf_cosmetic = validate_pdf(pdf_path)
        blockers.extend(pdf_blockers)
        cosmetic.extend(pdf_cosmetic)

    passed = len(blockers) == 0
    return passed, blockers, cosmetic


def auto_fix_cosmetic(html_path, cosmetic_issues):
    """
    Fix cosmetic-only issues. Returns count of fixes applied.
    NEVER fixes blockers. NEVER injects content (no hardcoded education/certs).
    """
    try:
        with open(html_path) as f:
            html = f.read()
    except Exception:
        return 0

    fixes = 0

    if any("EM_DASH" in i for i in cosmetic_issues):
        html = html.replace("—", "-").replace("&mdash;", "-")
        fixes += 1

    if any("EN_DASH" in i for i in cosmetic_issues):
        html = html.replace("–", "-").replace("&ndash;", "-")
        fixes += 1

    if any("ENTITY" in i for i in cosmetic_issues):
        html = html.replace("ATandT", "AT&amp;T").replace("AT and T", "AT&amp;T")
        fixes += 1

    if fixes > 0:
        with open(html_path, "w") as f:
            f.write(html)

    return fixes


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 cv_validator.py <html_path> [pdf_path]")
        sys.exit(1)

    html_p = sys.argv[1]
    pdf_p = sys.argv[2] if len(sys.argv) > 2 else None

    passed, blockers, cosmetic = validate_cv(html_p, pdf_p)

    if blockers:
        print(f"BLOCKERS ({len(blockers)}):")
        for b in blockers:
            print(f"  ❌ {b}")
    if cosmetic:
        print(f"COSMETIC ({len(cosmetic)}):")
        for c in cosmetic:
            print(f"  ⚠️  {c}")

    if passed:
        print("\n✅ PASSED")
        sys.exit(0)
    else:
        print(f"\n❌ FAILED ({len(blockers)} blocker(s))")
        sys.exit(1)
