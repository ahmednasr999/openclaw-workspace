#!/usr/bin/env python3
"""
LinkedIn Auto-Poster Test Suite
================================
Deterministic tests for bold conversion, scoring weights, content extraction.
No network calls needed.

Usage:
    python3 test-linkedin-poster.py
    python3 test-linkedin-poster.py --verbose
"""

import sys, os, json, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
        print(f"  \u274c {name} - {detail}")


# Import functions from the poster script
# We can't import main() (it has side effects), but we can import helpers
WORKSPACE = "/root/.openclaw/workspace"
POSTER = f"{WORKSPACE}/scripts/linkedin-auto-poster.py"


def load_poster_functions():
    """Load specific functions from the poster script without executing main."""
    import importlib.util
    # Read the file and extract just the function definitions we need
    with open(POSTER) as f:
        code = f.read()

    # Create a restricted namespace
    ns = {"__builtins__": __builtins__, "re": re, "json": json, "os": os, "sys": sys}

    # Extract and exec just the functions we need
    # Bold conversion
    bold_funcs = re.search(
        r'(def to_unicode_bold\(.*?\n(?:.*?\n)*?def convert_bold_markdown\(.*?\n(?:.*?\n)*?    return.*?\n)',
        code,
    )
    if bold_funcs:
        exec(bold_funcs.group(0), ns)

    return ns


# ── Test 1: Bold conversion A-Z, a-z, 0-9 ───────────────────────────────────
def test_bold_conversion():
    """Unicode bold produces correct Mathematical Bold characters."""
    print("\n\U0001f4dd Test 1: Bold conversion")

    ns = load_poster_functions()
    to_bold = ns.get("to_unicode_bold")
    convert = ns.get("convert_bold_markdown")

    if not to_bold or not convert:
        test("Functions loaded", False, "Could not extract bold functions")
        return

    # A-Z
    bold_A = to_bold("A")
    test("A -> Mathematical Bold A", bold_A == "\U0001D5D4", f"Got {repr(bold_A)}")

    bold_Z = to_bold("Z")
    test("Z -> Mathematical Bold Z", bold_Z == "\U0001D5ED", f"Got {repr(bold_Z)}")

    # a-z
    bold_a = to_bold("a")
    test("a -> Mathematical Bold a", bold_a == "\U0001D5EE", f"Got {repr(bold_a)}")

    bold_z = to_bold("z")
    test("z -> Mathematical Bold z", bold_z == "\U0001D607", f"Got {repr(bold_z)}")

    # 0-9
    bold_0 = to_bold("0")
    test("0 -> Mathematical Bold 0", bold_0 == "\U0001D7EC", f"Got {repr(bold_0)}")

    bold_9 = to_bold("9")
    test("9 -> Mathematical Bold 9", bold_9 == "\U0001D7F5", f"Got {repr(bold_9)}")

    # Non-alphanumeric passes through
    test("Space unchanged", to_bold(" ") == " ")
    test("Emoji unchanged", to_bold("\U0001f680") == "\U0001f680")


# ── Test 2: Markdown bold conversion ─────────────────────────────────────────
def test_markdown_bold():
    """**text** patterns are properly converted."""
    print("\n\u2733\ufe0f Test 2: Markdown bold patterns")

    ns = load_poster_functions()
    convert = ns.get("convert_bold_markdown")
    to_bold = ns.get("to_unicode_bold")

    if not convert:
        test("Function loaded", False)
        return

    # Basic conversion
    result = convert("**Hello** world")
    expected_hello = to_bold("Hello")
    test("**Hello** converts", result.startswith(expected_hello), f"Got: {repr(result[:20])}")
    test("' world' preserved", result.endswith(" world"), f"Got: {repr(result[-10:])}")

    # Multiple bolds in one line
    result2 = convert("**A** and **B**")
    test("Multiple bolds", to_bold("A") in result2 and to_bold("B") in result2)

    # No bold markers = no change
    result3 = convert("Plain text here")
    test("No markers = no change", result3 == "Plain text here")

    # Empty bold
    result4 = convert("**** empty")
    test("Empty bold pattern handled", True)  # Should not crash

    # Nested asterisks (edge case)
    result5 = convert("**bold with * star**")
    test("Nested asterisk", to_bold("b") in result5)


# ── Test 3: Scoring weights and mandatory gates ──────────────────────────────
def test_scoring_weights():
    """Verify weighted scoring config is correct."""
    print("\n\u2696\ufe0f Test 3: Scoring weights")

    with open(POSTER) as f:
        code = f.read()

    # Extract SCORED_QUESTIONS
    sq_match = re.search(r'SCORED_QUESTIONS\s*=\s*\[(.*?)\]', code, re.DOTALL)
    if not sq_match:
        test("SCORED_QUESTIONS found", False)
        return
    test("SCORED_QUESTIONS found", True)

    # Parse the tuples
    tuples = re.findall(r'\("(\w+)".*?,\s*(\d+),\s*(True|False)\)', sq_match.group(1))
    test("10 questions defined", len(tuples) == 10, f"Found {len(tuples)}")

    # Check weights sum to 13 (1+1+1+2+1+1+1+2+2+1)
    weights = [int(t[1]) for t in tuples]
    test(f"Max score = {sum(weights)}", sum(weights) == 13, f"Got {sum(weights)}")

    # Check mandatory gates
    mandatory = [t[0] for t in tuples if t[2] == "True"]
    test("SCROLL_STOPPER is mandatory", "SCROLL_STOPPER" in mandatory)
    test("CTA is mandatory", "CTA" in mandatory)
    test("Exactly 2 mandatory gates", len(mandatory) == 2, f"Got {len(mandatory)}: {mandatory}")

    # High-weight questions
    high = [t[0] for t in tuples if int(t[1]) == 2]
    test("METRIC is high-weight", "METRIC" in high)
    test("NOT_PRESS_RELEASE is high-weight", "NOT_PRESS_RELEASE" in high)
    test("CONTEXT_RICH is high-weight", "CONTEXT_RICH" in high)


# ── Test 4: Watchdog uses persistent path ────────────────────────────────────
def test_watchdog_path():
    """Watchdog flag is NOT in /tmp/ (survives reboots)."""
    print("\n\U0001f6a8 Test 4: Persistent watchdog")

    with open(POSTER) as f:
        code = f.read()

    tmp_watchdog = code.count("/tmp/linkedin-post-pending.flag")
    test("No /tmp/ watchdog references", tmp_watchdog == 0, f"Found {tmp_watchdog} references")

    persistent_watchdog = "linkedin-watchdog.json" in code
    test("Persistent watchdog path exists", persistent_watchdog)


# ── Test 5: No local .md fallback ────────────────────────────────────────────
def test_no_md_fallback():
    """Local .md bold fallback has been removed."""
    print("\n\U0001f4c4 Test 5: Single source of truth")

    with open(POSTER) as f:
        code = f.read()

    md_fallback = "local_md_candidates" in code or "Bold markers found in local .md" in code
    test("No .md fallback code", not md_fallback, "Local .md fallback still present")

    notion_source = "Notion annotations are the single source of truth" in code
    test("Notion is single source comment", notion_source)


# ── Test 6: Script compiles ──────────────────────────────────────────────────
def test_compiles():
    """Script has no syntax errors."""
    print("\n\U0001f4e5 Test 6: Compilation")

    try:
        with open(POSTER) as f:
            compile(f.read(), POSTER, "exec")
        test("linkedin-auto-poster.py compiles", True)
    except SyntaxError as e:
        test("linkedin-auto-poster.py compiles", False, str(e))


# ── Run all ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("LinkedIn Auto-Poster Test Suite")
    print("=" * 50)

    test_bold_conversion()
    test_markdown_bold()
    test_scoring_weights()
    test_watchdog_path()
    test_no_md_fallback()
    test_compiles()

    print(f"\n{'=' * 50}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    print(f"{'=' * 50}")
    sys.exit(0 if FAIL == 0 else 1)
