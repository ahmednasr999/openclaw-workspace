#!/usr/bin/env python3
"""Validate slides brand-onboarding token generation against fixtures."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import slides_brand_onboarding as brand  # noqa: E402


FIXTURES = Path(__file__).resolve().parent.parent / 'examples' / 'brand-onboarding-fixtures.json'
BRAND_HTML = Path(__file__).resolve().parent.parent / 'examples' / 'brand-site.html'


def main() -> int:
    fixtures = json.loads(FIXTURES.read_text(encoding='utf-8'))
    failures: list[str] = []

    for fixture in fixtures:
        name = fixture['name']
        signals = fixture['input']
        expected = fixture['expect']
        tokens = brand.build_tokens(signals)
        typography = brand.build_typography(signals)
        print(f"\n## {name}")
        print(json.dumps({
            'tokens': tokens,
            'typography': typography,
        }, indent=2, ensure_ascii=False))
        for key, expected_value in expected.items():
            actual_value = tokens.get(key)
            if actual_value != expected_value:
                failures.append(f"{name}: token {key} expected {expected_value} but got {actual_value}")
        if brand.contrast_ratio(tokens['bg'], tokens['text-primary']) < 4.5:
            failures.append(f"{name}: text-primary contrast below threshold")
        if brand.contrast_ratio(tokens['bg'], tokens['text-secondary']) < 4.5:
            failures.append(f"{name}: text-secondary contrast below threshold")

    live_signals = brand.extract_signals_from_url(BRAND_HTML.resolve().as_uri())
    live_tokens = brand.build_tokens(live_signals)
    print("\n## live_url_fixture")
    print(json.dumps({
        'signals': live_signals,
        'tokens': live_tokens,
    }, indent=2, ensure_ascii=False))

    if live_tokens.get('bg') != 'F7F0E8':
        failures.append(f"live_url_fixture: expected bg F7F0E8 but got {live_tokens.get('bg')}")
    if live_tokens.get('surface') != 'FBF7F2':
        failures.append(f"live_url_fixture: expected surface FBF7F2 but got {live_tokens.get('surface')}")
    if live_tokens.get('accent') != 'C86432':
        failures.append(f"live_url_fixture: expected accent C86432 but got {live_tokens.get('accent')}")
    if brand.build_typography(live_signals).get('display') != 'Fraunces':
        failures.append('live_url_fixture: expected display font Fraunces')

    browser_signals = brand.extract_signals_with_browser(BRAND_HTML.resolve().as_uri())
    browser_tokens = brand.build_tokens({
        **browser_signals,
        'bodyBackground': brand.coerce_browser_signal(browser_signals.get('bodyBackground')),
        'cardBackground': brand.coerce_browser_signal(browser_signals.get('cardBackground')),
        'primaryText': brand.coerce_browser_signal(browser_signals.get('primaryText')),
        'secondaryText': brand.coerce_browser_signal(browser_signals.get('secondaryText')),
        'borderColor': brand.coerce_browser_signal(browser_signals.get('borderColor')),
        'accentColor': brand.coerce_browser_signal(browser_signals.get('accentColor')),
        'titleFont': brand.extract_font_family(browser_signals.get('titleFont')) or browser_signals.get('titleFont'),
        'bodyFont': brand.extract_font_family(browser_signals.get('bodyFont')) or browser_signals.get('bodyFont'),
        'monoFont': brand.extract_font_family(browser_signals.get('monoFont')) or browser_signals.get('monoFont'),
    })
    print("\n## browser_fixture")
    print(json.dumps({
        'signals': browser_signals,
        'tokens': browser_tokens,
    }, indent=2, ensure_ascii=False))
    if browser_tokens.get('bg') != 'F7F0E8':
        failures.append(f"browser_fixture: expected bg F7F0E8 but got {browser_tokens.get('bg')}")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"\nBrand onboarding validation failed with {len(failures)} issue(s).")
        return 1

    print("\nBrand onboarding validation passed.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
