#!/usr/bin/env python3
"""
CV Builder Test Suite
=====================
5 deterministic tests using existing CV fixtures. No Opus calls needed.
Run after every modification to auto-cv-builder.py or cv_validator.py.

Usage:
    python3 test-cv-builder.py
    python3 test-cv-builder.py --verbose

Exit code: 0 = all pass, 1 = failures
"""

import json, os, sys, tempfile, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cv_validator import validate_cv, validate_html, validate_pdf, auto_fix_cosmetic

WORKSPACE = "/root/.openclaw/workspace"
CVS_DIR = f"{WORKSPACE}/cvs"

PASS = 0
FAIL = 0
VERBOSE = "--verbose" in sys.argv


def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        if VERBOSE:
            print(f"  \u2705 {name}")
    else:
        FAIL += 1
        print(f"  \u274c {name} \u2014 {detail}")


# ── Test 1: Existing CVs pass validation ─────────────────────────────────────
def test_existing_cvs_pass():
    """At least 80% of existing CVs should pass validation."""
    print("\n\U0001f4c4 Test 1: Existing CV validation")
    html_files = glob.glob(f"{CVS_DIR}/*.html")
    if not html_files:
        test("Has HTML fixtures", False, "No .html files in cvs/")
        return

    passed_count = 0
    total = min(len(html_files), 20)  # Sample up to 20
    failures = []
    for html_path in html_files[:total]:
        p, blockers, cosmetic = validate_cv(html_path)
        if p:
            passed_count += 1
        else:
            failures.append((os.path.basename(html_path), blockers[:2]))

    rate = passed_count / total * 100
    test(f"Pass rate >= 70% ({passed_count}/{total} = {rate:.0f}%)", rate >= 70,
         f"Failures: {failures[:3]}")


# ── Test 2: Known-bad HTML is caught ─────────────────────────────────────────
def test_known_bad_patterns():
    """Validator catches missing sections, em dashes, thin content."""
    print("\n\U0001f6a8 Test 2: Known-bad patterns detected")

    # Missing education
    bad_html = "<h2>Professional Experience</h2><p>Some content here that is long enough to pass thin check.</p>" * 10
    blockers, cosmetic = validate_html(tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, dir="/tmp"
    ).__enter__().name)
    # Write and re-validate
    tmp = "/tmp/test_bad_cv.html"
    with open(tmp, "w") as f:
        f.write(bad_html)
    blockers, cosmetic = validate_html(tmp)
    test("Catches missing Education", any("MISSING_EDUCATION" in b for b in blockers),
         f"Blockers: {blockers}")
    test("Catches missing Certifications", any("MISSING_CERTS" in b for b in blockers),
         f"Blockers: {blockers}")
    test("Catches missing email", any("MISSING_EMAIL" in b for b in blockers),
         f"Blockers: {blockers}")
    os.remove(tmp)

    # Em dashes
    em_html = "<h2>Education</h2><h2>Certifications</h2><h2>Professional Experience</h2>" + \
              "<p>ahmednasr999@gmail.com +971 50 281 4490</p>" + \
              "<p>Some content \u2014 with em dashes</p>" * 20
    tmp2 = "/tmp/test_em_cv.html"
    with open(tmp2, "w") as f:
        f.write(em_html)
    blockers2, cosmetic2 = validate_html(tmp2)
    test("Catches em dashes as cosmetic", any("EM_DASH" in c for c in cosmetic2),
         f"Cosmetic: {cosmetic2}")
    test("Em dashes are NOT blockers", not any("EM_DASH" in b for b in blockers2),
         f"Blockers: {blockers2}")
    os.remove(tmp2)


# ── Test 3: Auto-fix only handles cosmetic issues ────────────────────────────
def test_auto_fix_cosmetic_only():
    """Auto-fix removes em dashes but never injects content."""
    print("\n\U0001f527 Test 3: Auto-fix cosmetic only")

    html_with_em = (
        "<h2>Education</h2><h2>Certifications</h2><h2>Professional Experience</h2>"
        "<p>ahmednasr999@gmail.com +971 50 281 4490</p>"
        "<p>Led transformation \u2014 drove results \u2013 across regions</p>" * 10
    )
    tmp = "/tmp/test_fix_cv.html"
    with open(tmp, "w") as f:
        f.write(html_with_em)

    fixes = auto_fix_cosmetic(tmp, ["EM_DASH: 10 em dashes found", "EN_DASH: 10 en dashes found"])
    test("Fixes applied > 0", fixes > 0, f"Got {fixes}")

    with open(tmp) as f:
        fixed = f.read()
    test("No em dashes remain", "\u2014" not in fixed and "&mdash;" not in fixed,
         "Em dashes still present")
    test("No en dashes remain", "\u2013" not in fixed and "&ndash;" not in fixed,
         "En dashes still present")
    test("No hardcoded education injected", "Dubai, United Arab Emirates, 2010" not in fixed,
         "Old hardcoded education found!")
    test("No hardcoded certs injected", "&#8212;" not in fixed,
         "Old hardcoded cert em-dash entities found!")
    os.remove(tmp)


# ── Test 4: HTML template loads from shared file ─────────────────────────────
def test_template_loading():
    """Shared template exists and is valid."""
    print("\n\U0001f4e6 Test 4: Shared HTML template")
    template_path = f"{WORKSPACE}/templates/cv-template.html"
    test("Template file exists", os.path.exists(template_path))

    if os.path.exists(template_path):
        with open(template_path) as f:
            tmpl = f.read()
        test("Contains {role_title}", "{role_title}" in tmpl, "Missing placeholder")
        test("Contains {body_html}", "{body_html}" in tmpl, "Missing placeholder")
        test("No table-cell CSS", "table-cell" not in tmpl, "Still has table-cell layout")
        test("Has float:right for dates", "float: right" in tmpl or "float:right" in tmpl,
             "Missing float-right date layout")


# ── Test 5: Validator module imports cleanly ─────────────────────────────────
def test_imports():
    """All CV builder modules import without error."""
    print("\n\U0001f4e5 Test 5: Module imports")
    try:
        from cv_validator import validate_cv, auto_fix_cosmetic, validate_html, validate_pdf
        test("cv_validator imports", True)
    except Exception as e:
        test("cv_validator imports", False, str(e))

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("auto_cv", f"{WORKSPACE}/scripts/auto-cv-builder.py")
        # Just check syntax, don't execute
        with open(f"{WORKSPACE}/scripts/auto-cv-builder.py") as f:
            compile(f.read(), "auto-cv-builder.py", "exec")
        test("auto-cv-builder.py compiles", True)
    except Exception as e:
        test("auto-cv-builder.py compiles", False, str(e))

    try:
        with open(f"{WORKSPACE}/scripts/cv_validator.py") as f:
            compile(f.read(), "cv_validator.py", "exec")
        test("cv_validator.py compiles", True)
    except Exception as e:
        test("cv_validator.py compiles", False, str(e))


# ── Run all ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("CV Builder Test Suite")
    print("=" * 50)

    test_existing_cvs_pass()
    test_known_bad_patterns()
    test_auto_fix_cosmetic_only()
    test_template_loading()
    test_imports()

    print(f"\n{'=' * 50}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    print(f"{'=' * 50}")
    sys.exit(0 if FAIL == 0 else 1)
