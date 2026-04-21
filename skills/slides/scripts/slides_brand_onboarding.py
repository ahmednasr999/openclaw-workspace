#!/usr/bin/env python3
"""Generate and optionally apply a proposed slides style guide from extracted brand signals.

This is a proposal workflow. It converts a small set of extracted brand inputs into
semantic tokens for slides-style-guide.md.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

DEFAULT_BG = "F5F1EA"
DEFAULT_SURFACE = "FFFDFC"
DEFAULT_SURFACE_2 = "ECE6DE"
DEFAULT_TEXT_PRIMARY = "171411"
DEFAULT_TEXT_SECONDARY = "4B443D"
DEFAULT_TEXT_SOFT = "7A6F66"
DEFAULT_RULE = "D8CEC2"
DEFAULT_RULE_STRONG = "B9AB9B"
DEFAULT_ACCENT = "C86432"
DEFAULT_ACCENT_SOFT = "F3E1D8"
DEFAULT_WARNING = "B85C38"
DEFAULT_SUCCESS = "4B7A5A"
DEFAULT_DATA_LINK = "2E6FD0"

STYLE_GUIDE_PATH = Path(__file__).resolve().parent.parent / "references" / "slides-style-guide.md"


class _StyleGuideHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_style = False
        self.styles: list[str] = []
        self.body_attrs: dict[str, str] = {}
        self.stylesheet_hrefs: list[str] = []
        self.meta_theme_color: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k.lower(): v for k, v in attrs if v is not None}
        if tag.lower() == "style":
            self.in_style = True
        elif tag.lower() == "body":
            self.body_attrs = attr_map
        elif tag.lower() == "link":
            rel = (attr_map.get("rel") or "").lower()
            href = attr_map.get("href")
            if "stylesheet" in rel and href:
                self.stylesheet_hrefs.append(href)
        elif tag.lower() == "meta":
            name = (attr_map.get("name") or attr_map.get("property") or "").lower()
            content = attr_map.get("content")
            if name == "theme-color" and content:
                self.meta_theme_color = content

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "style":
            self.in_style = False

    def handle_data(self, data: str) -> None:
        if self.in_style and data.strip():
            self.styles.append(data)


def normalize_hex(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    cleaned = value.strip().lstrip("#").upper()
    if len(cleaned) == 3:
        cleaned = "".join(ch * 2 for ch in cleaned)
    if not re.fullmatch(r"[0-9A-F]{6}", cleaned):
        return fallback
    return cleaned


def extract_css_property(css: str, selectors: list[str], property_name: str) -> str | None:
    selector_pattern = "|".join(re.escape(selector) for selector in selectors)
    pattern = rf"(?:{selector_pattern})\s*\{{([^}}]+)\}}"
    for match in re.finditer(pattern, css, flags=re.IGNORECASE | re.DOTALL):
        block = match.group(1)
        prop_match = re.search(rf"{re.escape(property_name)}\s*:\s*([^;]+)", block, flags=re.IGNORECASE)
        if prop_match:
            return prop_match.group(1).strip()
    return None


def extract_css_variable(css: str, names: list[str]) -> str | None:
    for name in names:
        match = re.search(rf"{re.escape(name)}\s*:\s*([^;]+)", css, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def resolve_css_var_value(value: str | None, css: str, max_depth: int = 4) -> str | None:
    if not value:
        return None
    current = value.strip()
    for _ in range(max_depth):
        match = re.search(r"var\((--[A-Za-z0-9_-]+)(?:\s*,[^)]*)?\)", current)
        if not match:
            return current
        replacement = extract_css_variable(css, [match.group(1)])
        if not replacement:
            return current
        current = re.sub(r"var\((--[A-Za-z0-9_-]+)(?:\s*,[^)]*)?\)", replacement.strip(), current, count=1)
    return current


def extract_first_color(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"#([0-9a-fA-F]{3,6})\b", value)
    if not match:
        return None
    return normalize_hex(match.group(0), None)  # type: ignore[arg-type]


def extract_font_family(value: str | None) -> str | None:
    if not value:
        return None
    first = value.split(",")[0].strip().strip('"\'')
    return first or None


def fetch_url_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 SlidesBrandOnboarding/1.0"})
    with urlopen(req, timeout=20) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def extract_signals_with_browser(url: str) -> dict[str, Any]:
    script = """
const { chromium } = require('playwright');

(async () => {
  const url = process.argv[2];
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
  const result = await page.evaluate(() => {
    const body = document.body;
    const root = document.documentElement;
    const getStyle = (el) => window.getComputedStyle(el);
    const bodyStyle = getStyle(body);
    const rootStyle = getStyle(root);
    const firstHeading = document.querySelector('h1, h2');
    const headingStyle = firstHeading ? getStyle(firstHeading) : null;
    const accentEl = document.querySelector('a, button, .btn, .button');
    const accentStyle = accentEl ? getStyle(accentEl) : null;
    const cardEl = document.querySelector('.card, .panel, main section, section, article, main');
    const cardStyle = cardEl ? getStyle(cardEl) : null;
    const codeEl = document.querySelector('code, pre');
    const codeStyle = codeEl ? getStyle(codeEl) : null;

    return {
      bodyBackground: bodyStyle.backgroundColor || rootStyle.backgroundColor,
      cardBackground: cardStyle ? cardStyle.backgroundColor : '',
      primaryText: bodyStyle.color || rootStyle.color,
      secondaryText: rootStyle.getPropertyValue('--color-text-soft') || rootStyle.getPropertyValue('--color-muted') || '',
      borderColor: cardStyle ? cardStyle.borderColor : (rootStyle.getPropertyValue('--color-border') || ''),
      accentColor: accentStyle ? (accentStyle.color || accentStyle.backgroundColor) : (rootStyle.getPropertyValue('--color-accent') || rootStyle.getPropertyValue('--accent') || ''),
      titleFont: headingStyle ? headingStyle.fontFamily : rootStyle.getPropertyValue('--font-display') || '',
      bodyFont: bodyStyle.fontFamily || rootStyle.fontFamily,
      monoFont: codeStyle ? codeStyle.fontFamily : rootStyle.getPropertyValue('--font-mono') || '',
    };
  });
  console.log(JSON.stringify(result));
  await browser.close();
})().catch(err => {
  console.error(err.stack || String(err));
  process.exit(1);
});
"""

    with tempfile.TemporaryDirectory(prefix="slides-brand-browser-") as tmp:
        script_path = Path(tmp) / "extract_brand.js"
        script_path.write_text(script, encoding="utf-8")
        env = os.environ.copy()
        if not env.get("NODE_PATH"):
            try:
                proc = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, check=True)
                env["NODE_PATH"] = proc.stdout.strip()
            except subprocess.SubprocessError:
                pass
        proc = subprocess.run([
            "node",
            str(script_path),
            url,
        ], capture_output=True, text=True, env=env, check=True)
        result = json.loads(proc.stdout)
        result["extractionMethod"] = "browser-computed-style"
        return result


def extract_signals_from_url(url: str) -> dict[str, Any]:
    html = fetch_url_html(url)
    parser = _StyleGuideHTMLParser()
    parser.feed(html)
    css_blocks = list(parser.styles)
    for href in parser.stylesheet_hrefs[:6]:
        abs_href = urljoin(url, href)
        try:
            css_blocks.append(fetch_url_html(abs_href))
        except (OSError, URLError):
            continue
    css = "\n".join(css_blocks)
    body_style = parser.body_attrs.get("style", "")

    body_background = (
        extract_first_color(body_style)
        or normalize_hex(parser.meta_theme_color, None)  # type: ignore[arg-type]
        or extract_first_color(extract_css_property(css, ["body", ":root"], "background"))
        or extract_first_color(extract_css_property(css, ["body", ":root"], "background-color"))
        or extract_first_color(extract_css_variable(css, ["--color-bg", "--color-background", "--background", "--surface-bg"]))
    )
    primary_text = (
        extract_first_color(body_style)
        or extract_first_color(extract_css_property(css, ["body", ":root"], "color"))
        or extract_first_color(extract_css_variable(css, ["--color-text", "--text", "--color-ink", "--ink"]))
    )
    title_font = (
        extract_font_family(resolve_css_var_value(extract_css_property(css, ["h1"], "font-family"), css))
        or extract_font_family(resolve_css_var_value(extract_css_property(css, ["h2"], "font-family"), css))
        or extract_font_family(resolve_css_var_value(extract_css_variable(css, ["--font-display", "--font-heading", "--font-serif"]), css))
        or extract_font_family(resolve_css_var_value(extract_css_property(css, ["body", ":root"], "font-family"), css))
    )
    body_font = (
        extract_font_family(resolve_css_var_value(extract_css_property(css, ["body", ":root"], "font-family"), css))
        or extract_font_family(resolve_css_var_value(extract_css_variable(css, ["--font-body", "--font-sans", "--font-text"]), css))
    )
    mono_font = (
        extract_font_family(resolve_css_var_value(extract_css_property(css, ["code", "pre"], "font-family"), css))
        or extract_font_family(resolve_css_var_value(extract_css_variable(css, ["--font-mono", "--mono-font"]), css))
    )

    accent = None
    for selector in ["a", "button", ".btn", ".button", ":root"]:
        accent = extract_first_color(extract_css_property(css, [selector], "color")) or extract_first_color(extract_css_property(css, [selector], "background")) or extract_first_color(extract_css_property(css, [selector], "background-color"))
        if accent:
            break
    accent = accent or extract_first_color(extract_css_variable(css, ["--color-accent", "--accent", "--color-brand", "--brand", "--color-primary", "--primary"]))

    border = extract_first_color(extract_css_property(css, [":root", "body", ".card", ".panel"], "border-color")) or extract_first_color(extract_css_variable(css, ["--color-border", "--border", "--rule"]))
    card_bg = (
        extract_first_color(extract_css_property(css, [".card", ".panel", "main", "section"], "background"))
        or extract_first_color(extract_css_property(css, [".card", ".panel", "main", "section"], "background-color"))
        or extract_first_color(extract_css_variable(css, ["--color-surface", "--surface", "--card-bg", "--panel-bg"]))
    )
    secondary_text = extract_first_color(extract_css_property(css, ["small", ".muted", ".secondary", "p"], "color")) or extract_first_color(extract_css_variable(css, ["--color-text-soft", "--color-muted", "--text-soft", "--muted"]))

    return {
        "url": url,
        "bodyBackground": body_background,
        "cardBackground": card_bg,
        "primaryText": primary_text,
        "secondaryText": secondary_text,
        "borderColor": border,
        "accentColor": accent,
        "titleFont": title_font,
        "bodyFont": body_font,
        "monoFont": mono_font,
        "extractionMethod": "live-url-css-scan",
    }


def coerce_browser_signal(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith("rgb"):
        channels = [int(part) for part in re.findall(r"\d+", value)[:3]]
        if len(channels) == 3:
            return rgb_to_hex(tuple(channels))
    return extract_first_color(value) or extract_font_family(value) or value.strip()


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def hex_to_rgb(hex_value: str) -> tuple[int, int, int]:
    hex_value = normalize_hex(hex_value, "000000")
    return tuple(int(hex_value[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "".join(f"{clamp(int(round(channel)), 0, 255):02X}" for channel in rgb)


def mix(hex_a: str, hex_b: str, ratio: float) -> str:
    a = hex_to_rgb(hex_a)
    b = hex_to_rgb(hex_b)
    ratio = clamp(ratio, 0.0, 1.0)
    mixed = tuple(a[i] * (1 - ratio) + b[i] * ratio for i in range(3))
    return rgb_to_hex(mixed)


def relative_luminance(hex_value: str) -> float:
    def channel(c: int) -> float:
        c = c / 255.0
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    r, g, b = hex_to_rgb(hex_value)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    lum_a = relative_luminance(hex_a)
    lum_b = relative_luminance(hex_b)
    lighter = max(lum_a, lum_b)
    darker = min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def enforce_bg(hex_value: str) -> str:
    normalized = normalize_hex(hex_value, DEFAULT_BG)
    if normalized == "FFFFFF":
        return "FAF7F2"
    return normalized


def enforce_surface(bg: str, surface: str) -> str:
    surface = normalize_hex(surface, DEFAULT_SURFACE)
    if surface == "FFFFFF" and bg == "FAF7F2":
        return "FFFDFC"
    if surface == bg:
        return mix(bg, "FFFFFF", 0.35)
    return surface


def ensure_text_contrast(bg: str, text: str, fallback_dark: str) -> str:
    text = normalize_hex(text, fallback_dark)
    if contrast_ratio(bg, text) >= 4.5:
        return text
    dark_candidate = normalize_hex(fallback_dark, DEFAULT_TEXT_PRIMARY)
    if contrast_ratio(bg, dark_candidate) >= 4.5:
        return dark_candidate
    return mix(bg, "000000", 0.92)


def ensure_secondary_contrast(bg: str, text_primary: str, secondary: str) -> str:
    secondary = normalize_hex(secondary, DEFAULT_TEXT_SECONDARY)
    if contrast_ratio(bg, secondary) >= 4.5:
        return secondary
    return mix(text_primary, bg, 0.35)


def build_tokens(signals: dict[str, Any]) -> dict[str, str]:
    bg = enforce_bg(signals.get("bodyBackground") or signals.get("background"))
    surface = enforce_surface(bg, normalize_hex(signals.get("cardBackground"), DEFAULT_SURFACE))
    surface_2 = enforce_surface(bg, mix(surface, bg, 0.45))
    text_primary = ensure_text_contrast(bg, signals.get("primaryText"), DEFAULT_TEXT_PRIMARY)
    text_secondary = ensure_secondary_contrast(bg, text_primary, signals.get("secondaryText"))
    text_soft = mix(text_secondary, bg, 0.28)
    rule = normalize_hex(signals.get("borderColor"), mix(text_primary, bg, 0.78))
    rule_strong = mix(text_primary, bg, 0.62)
    accent = normalize_hex(signals.get("accentColor"), DEFAULT_ACCENT)
    accent_soft = mix(accent, bg, 0.78)
    warning = mix(accent, "8B1E2D", 0.25)
    success = DEFAULT_SUCCESS
    data_link = DEFAULT_DATA_LINK if accent == DEFAULT_ACCENT else mix(accent, "2563EB", 0.55)
    return {
        "bg": bg,
        "surface": surface,
        "surface-2": surface_2,
        "text-primary": text_primary,
        "text-secondary": text_secondary,
        "text-soft": text_soft,
        "rule": rule,
        "rule-strong": rule_strong,
        "accent": accent,
        "accent-soft": accent_soft,
        "warning": warning,
        "success": success,
        "data-link": data_link,
    }


def build_typography(signals: dict[str, Any]) -> dict[str, str]:
    body = signals.get("bodyFont") or "Aptos"
    title = signals.get("titleFont") or body
    mono = signals.get("monoFont") or "Aptos Mono"
    return {
        "display": title,
        "title": title,
        "section": title,
        "body": body,
        "caption": body,
        "meta": body,
        "data": mono,
        "eyebrow": body,
    }


def format_diff(tokens: dict[str, str], typography: dict[str, str]) -> str:
    lines = [
        "# Proposed Slides Brand Tokens",
        "",
        "## Colors",
        "",
    ]
    for key, value in tokens.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Typography", ""])
    for key, value in typography.items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def apply_style_guide(tokens: dict[str, str]) -> None:
    text = STYLE_GUIDE_PATH.read_text(encoding="utf-8")
    for token, value in tokens.items():
        pattern = rf"(\| `{re.escape(token)}` \| [^|]+ \| `)([0-9A-F]{{6}})(` \|)"
        text, count = re.subn(pattern, rf"\g<1>{value}\g<3>", text)
        if count == 0:
            raise SystemExit(f"Could not update token row for {token} in {STYLE_GUIDE_PATH}")
    STYLE_GUIDE_PATH.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or apply slides brand tokens from extracted signals.")
    parser.add_argument("input_json", nargs="?", help="Path to JSON file containing extracted brand signals.")
    parser.add_argument("--url", help="Live website URL to scan for rough brand signals.")
    parser.add_argument("--browser", action="store_true", help="Use browser-computed styles for stronger website extraction")
    parser.add_argument("--apply", action="store_true", help="Write proposed color tokens into slides-style-guide.md")
    parser.add_argument("--output", help="Optional path for writing the proposal markdown.")
    args = parser.parse_args()

    if not args.input_json and not args.url:
        raise SystemExit("Provide either input_json or --url")

    if args.url:
        try:
            if args.browser:
                signals = extract_signals_with_browser(args.url)
                for key in ["bodyBackground", "cardBackground", "primaryText", "secondaryText", "borderColor", "accentColor"]:
                    signals[key] = coerce_browser_signal(signals.get(key))
                for key in ["titleFont", "bodyFont", "monoFont"]:
                    signals[key] = extract_font_family(signals.get(key)) or signals.get(key)
            else:
                signals = extract_signals_from_url(args.url)
        except (OSError, URLError, subprocess.SubprocessError) as exc:
            raise SystemExit(f"URL extraction failed: {exc}")
    else:
        input_path = Path(args.input_json).expanduser().resolve()
        signals = json.loads(input_path.read_text(encoding="utf-8"))

    tokens = build_tokens(signals)
    typography = build_typography(signals)
    proposal = format_diff(tokens, typography)

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(proposal, encoding="utf-8")

    if args.apply:
        apply_style_guide(tokens)

    print(json.dumps({
        "tokens": tokens,
        "typography": typography,
        "signals": signals,
        "contrast": {
            "text-primary_on_bg": round(contrast_ratio(tokens["bg"], tokens["text-primary"]), 2),
            "text-secondary_on_bg": round(contrast_ratio(tokens["bg"], tokens["text-secondary"]), 2),
        },
        "proposalPath": str(Path(args.output).expanduser().resolve()) if args.output else None,
        "applied": args.apply,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
