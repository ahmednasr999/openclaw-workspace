#!/usr/bin/env python3
"""
Content Factory Visual Template Generator v3.0 — PREMIUM
=========================================================
Designer-quality LinkedIn post images. Film grain, radial gradients,
glassmorphism badges, glow effects, refined typography.

4 templates: Newsjacking, Brandjacking, Namejacking, Hot Take
"""
import argparse, json, math, os, random, ssl, sys, textwrap, urllib.request
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
import numpy as np

WORKSPACE = "/root/.openclaw/workspace"
NOTION_TOKEN = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
RSS_DB = "32e8d599-a162-8180-9e3a-fbfc17a84e49"
OUTPUT_DIR = f"{WORKSPACE}/media/post-visuals"
PROFILE_PHOTO = f"{WORKSPACE}/profile-photo.jpg"
os.makedirs(OUTPUT_DIR, exist_ok=True)
CAIRO = timezone(timedelta(hours=2))
ctx = ssl.create_default_context()

W, H = 1200, 628
MARGIN_L = 72
MARGIN_R = 72
TEXT_WIDTH = W - MARGIN_L - MARGIN_R
BRAND_BAR_H = 52
CONTENT_BOTTOM = H - BRAND_BAR_H

# ── Fonts ────────────────────────────────────────────────────────────────────
def load_font(style="regular", size=32):
    paths = {
        "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "light": "/usr/share/fonts/truetype/lato/Lato-Medium.ttf",
        "italic": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        "bold_italic": "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
    }
    try:
        return ImageFont.truetype(paths.get(style, paths["regular"]), size)
    except:
        return ImageFont.load_default()

# ── Premium Color Palettes ───────────────────────────────────────────────────
PALETTES = {
    "Newsjacking": {
        "bg_center": (22, 32, 56),      # Warm center
        "bg_edge": (8, 10, 20),          # Near-black edges
        "accent": (50, 140, 255),        # Electric blue
        "accent_glow": (40, 100, 220),   # Glow color
        "text": (242, 242, 247),         # Off-white
        "text_muted": (120, 140, 170),
        "badge_label": "BREAKING INSIGHT",
    },
    "Brandjacking": {
        "bg_center": (28, 22, 48),
        "bg_edge": (8, 6, 16),
        "accent": (158, 120, 255),       # Mauve purple
        "accent_glow": (120, 80, 200),
        "text": (242, 242, 247),
        "text_muted": (140, 130, 170),
        "badge_label": "BRAND INSIGHT",
    },
    "Namejacking": {
        "bg_center": (32, 30, 28),
        "bg_edge": (10, 10, 9),
        "accent": (220, 175, 30),        # Rich gold/amber
        "accent_glow": (180, 140, 20),
        "text": (242, 242, 247),
        "text_muted": (155, 150, 135),
        "badge_label": "INSIGHT",
    },
    "Hot Take": {
        "bg_center": (52, 14, 14),
        "bg_edge": (12, 4, 6),
        "accent": (235, 65, 65),         # Vibrant red
        "accent_glow": (200, 40, 40),
        "text": (242, 242, 247),
        "text_muted": (180, 130, 130),
        "badge_label": "HOT TAKE",
    },
}

TOPIC_COLORS = {
    "AI": (90, 160, 250), "Digital Transformation": (50, 200, 150),
    "PMO": (240, 185, 40), "Healthcare": (240, 110, 110),
    "HealthTech": (235, 110, 175), "FinTech": (120, 135, 240),
    "Strategy": (160, 135, 245),
}

# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM EFFECTS
# ══════════════════════════════════════════════════════════════════════════════

def create_radial_gradient(w, h, center_color, edge_color, cx_ratio=0.42, cy_ratio=0.38):
    """Create premium radial gradient with off-center focal point."""
    small_w, small_h = w // 8, h // 8
    small = Image.new("RGB", (small_w, small_h))
    pixels = small.load()
    cx, cy = int(small_w * cx_ratio), int(small_h * cy_ratio)
    max_dist = math.sqrt(small_w**2 + small_h**2) * 0.65
    
    for y in range(small_h):
        for x in range(small_w):
            dist = math.sqrt((x - cx)**2 + (y - cy)**2)
            ratio = min(dist / max_dist, 1.0)
            ratio = ratio ** 1.6  # Smoother falloff
            r = int(center_color[0] + (edge_color[0] - center_color[0]) * ratio)
            g = int(center_color[1] + (edge_color[1] - center_color[1]) * ratio)
            b = int(center_color[2] + (edge_color[2] - center_color[2]) * ratio)
            pixels[x, y] = (r, g, b)
    
    return small.resize((w, h), Image.LANCZOS)

def add_film_grain(img, intensity=8, opacity=0.035):
    """Add subtle film grain for tactile premium feel."""
    arr = np.array(img).astype(np.float32)
    noise = np.random.normal(0, intensity, arr.shape).astype(np.float32)
    result = np.clip(arr + noise * (opacity * 255 / intensity), 0, 255).astype(np.uint8)
    return Image.fromarray(result)

def add_vignette(img, strength=0.3):
    """Add corner vignette to focus attention on center."""
    arr = np.array(img).astype(np.float32)
    h, w = arr.shape[:2]
    
    # Create vignette mask
    Y, X = np.ogrid[:h, :w]
    cy, cx = h / 2, w / 2
    # Normalized distance from center (elliptical)
    dist = np.sqrt(((X - cx) / (w * 0.6))**2 + ((Y - cy) / (h * 0.55))**2)
    mask = np.clip(dist - 0.5, 0, 1) * strength
    mask = np.stack([mask] * 3, axis=-1)
    
    result = np.clip(arr * (1 - mask), 0, 255).astype(np.uint8)
    return Image.fromarray(result)

def add_glow(img, x, y, w_glow, h_glow, color, opacity=0.12, blur_radius=40):
    """Add soft glow behind an area."""
    glow_layer = Image.new("RGB", img.size, (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.ellipse([x - w_glow//2, y - h_glow//2, x + w_glow//2, y + h_glow//2], fill=color)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(blur_radius))
    
    # Blend
    arr_img = np.array(img).astype(np.float32)
    arr_glow = np.array(glow_layer).astype(np.float32)
    result = np.clip(arr_img + arr_glow * opacity, 0, 255).astype(np.uint8)
    return Image.fromarray(result)

def add_subtle_shape(img, palette):
    """Add a large, faint geometric circle in background for depth."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # Large circle, partially off-screen bottom-right
    cx, cy, r = int(W * 0.8), int(H * 0.75), int(H * 0.6)
    # Very faint version of accent color
    ac = palette["accent"]
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(ac[0], ac[1], ac[2], 8))
    
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    return img.convert("RGB")

# ── Text Helpers ─────────────────────────────────────────────────────────────
def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current: lines.append(current)
            current = word
    if current: lines.append(current)
    return lines

def draw_text_with_shadow(draw, xy, text, fill, font, shadow_offset=3, shadow_blur=None, shadow_opacity=0.25):
    """Draw text with subtle drop shadow for depth."""
    x, y = xy
    # Shadow (darker version)
    shadow_color = (0, 0, 0)
    # We can't blur per-character easily, so just offset
    draw.text((x + 1, y + shadow_offset), text, fill=(*shadow_color, int(255 * shadow_opacity)), font=font)
    # Main text
    draw.text((x, y), text, fill=fill, font=font)

# ── Glassmorphism Badge ──────────────────────────────────────────────────────
def draw_glass_badge(img, draw, x, y, text, font, text_color, accent_color, height=26):
    """Draw a glassmorphism-style badge with frosted look."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    bw = tw + 22
    
    # Semi-transparent background
    badge_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    badge_draw = ImageDraw.Draw(badge_layer)
    
    # Background with accent tint
    bg_color = (accent_color[0], accent_color[1], accent_color[2], 45)
    # Rounded rect
    r = 5
    x1, y1, x2, y2 = x, y, x + bw, y + height
    badge_draw.rectangle([x1+r, y1, x2-r, y2], fill=bg_color)
    badge_draw.rectangle([x1, y1+r, x2, y2-r], fill=bg_color)
    badge_draw.pieslice([x1, y1, x1+2*r, y1+2*r], 180, 270, fill=bg_color)
    badge_draw.pieslice([x2-2*r, y1, x2, y1+2*r], 270, 360, fill=bg_color)
    badge_draw.pieslice([x1, y2-2*r, x1+2*r, y2], 90, 180, fill=bg_color)
    badge_draw.pieslice([x2-2*r, y2-2*r, x2, y2], 0, 90, fill=bg_color)
    
    # 1px border (subtle white, top-left emphasis for light effect)
    border_color = (255, 255, 255, 30)
    badge_draw.rectangle([x1+r, y1, x2-r, y1+1], fill=(255, 255, 255, 45))  # Top highlight
    badge_draw.rectangle([x1, y1+r, x1+1, y2-r], fill=(255, 255, 255, 25))  # Left highlight
    
    if img.mode != "RGBA":
        img_rgba = img.convert("RGBA")
    else:
        img_rgba = img
    img_rgba = Image.alpha_composite(img_rgba, badge_layer)
    img.paste(img_rgba.convert("RGB"))
    draw = ImageDraw.Draw(img)
    
    # Text
    draw.text((x + 11, y + (height - (bbox[3]-bbox[1])) // 2), text, fill=text_color, font=font)
    return draw, x + bw

# ── Hairline Divider ─────────────────────────────────────────────────────────
def draw_hairline(img, y, color, fade=True):
    """Draw a 1px hairline that fades at edges."""
    arr = np.array(img).astype(np.float32)
    for x in range(W):
        if fade:
            # Fade at edges
            if x < 100:
                alpha = x / 100.0
            elif x > W - 100:
                alpha = (W - x) / 100.0
            else:
                alpha = 1.0
            alpha *= 0.12  # Very subtle
        else:
            alpha = 0.1
        
        for c in range(3):
            arr[y, x, c] = min(255, arr[y, x, c] + color[c] * alpha)
    
    return Image.fromarray(arr.astype(np.uint8))

# ── Profile Photo ────────────────────────────────────────────────────────────
_profile_cache = None
def get_profile_photo(size=36):
    global _profile_cache
    if _profile_cache and _profile_cache.size[0] == size:
        return _profile_cache
    if not os.path.exists(PROFILE_PHOTO):
        return None
    
    photo = Image.open(PROFILE_PHOTO).convert("RGBA")
    photo = photo.resize((size, size), Image.LANCZOS)
    
    # Circular mask
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size-1, size-1], fill=255)
    
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(photo, (0, 0), mask)
    
    # Add subtle ring
    ring_draw = ImageDraw.Draw(output)
    ring_draw.ellipse([0, 0, size-1, size-1], outline=(255, 255, 255, 50), width=1)
    
    _profile_cache = output
    return output

# ── Brand Bar v3 (Premium) ───────────────────────────────────────────────────
def draw_brand_bar(img, palette):
    """Premium slim brand bar with photo, name, accent hairline."""
    bar_y = H - BRAND_BAR_H
    
    # Draw dark overlay
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, bar_y, W, H], fill=(6, 6, 10))
    
    # Accent hairline at top of bar
    img = draw_hairline(img, bar_y, palette["accent"], fade=False)
    draw = ImageDraw.Draw(img)
    
    # Profile photo
    photo = get_profile_photo(34)
    photo_x = MARGIN_L
    photo_y = bar_y + (BRAND_BAR_H - 34) // 2
    if photo:
        img.paste(photo, (photo_x, photo_y), photo)
        text_x = photo_x + 44
    else:
        text_x = MARGIN_L
    
    # Name (semibold) + title (light, tracked out)
    name_font = load_font("bold", 16)
    title_font = load_font("light", 11)
    
    draw.text((text_x, bar_y + 11), "Ahmed Nasr", fill=(240, 240, 245), font=name_font)
    draw.text((text_x, bar_y + 30), "TECHNOLOGY EXECUTIVE  \u00b7  AI & DIGITAL TRANSFORMATION", 
              fill=(120, 120, 135), font=title_font)
    
    return img, draw

# ── Source text helper ───────────────────────────────────────────────────────
def clean_source(source):
    """Clean source for display."""
    if source.startswith("X: @"):
        return source[4:], "via @"
    elif source.startswith("X: "):
        return source[3:], "via "
    elif source.startswith("LinkedIn: "):
        return source[10:], ""
    return source, "Source: "

# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE GENERATORS v3
# ══════════════════════════════════════════════════════════════════════════════

def generate_newsjacking(title, topic, source=""):
    palette = PALETTES["Newsjacking"]
    
    # 1. Radial gradient background
    img = create_radial_gradient(W, H, palette["bg_center"], palette["bg_edge"])
    
    # 2. Subtle geometric shape
    img = add_subtle_shape(img, palette)
    
    # 3. Glow behind text area
    img = add_glow(img, W // 2 - 50, H // 2 - 40, 600, 250, palette["accent_glow"], opacity=0.06)
    
    draw = ImageDraw.Draw(img)
    
    # 4. Top accent line (gradient feel - brighter center)
    for x in range(W):
        center_dist = abs(x - W//2) / (W//2)
        alpha = max(0, 1 - center_dist * 0.6)
        c = palette["accent"]
        r, g, b = int(c[0]*alpha), int(c[1]*alpha), int(c[2]*alpha)
        draw.line([(x, 0), (x, 2)], fill=(r, g, b))
    
    # 5. Glassmorphism badges
    badge_font = load_font("bold", 11)
    topic_font = load_font("light", 10)
    draw, badge_end = draw_glass_badge(img, draw, MARGIN_L, 34, palette["badge_label"], 
                                       badge_font, (240, 240, 255), palette["accent"])
    
    # Topic badge
    tc = TOPIC_COLORS.get(topic, (150, 150, 150))
    draw, _ = draw_glass_badge(img, draw, badge_end + 10, 34, topic.upper(), 
                               topic_font, tc, tc)
    badge_bottom = 72
    
    # 6. Headline - vertically centered
    headline_font = load_font("bold", 44)
    lines = wrap_text(title, headline_font, TEXT_WIDTH, draw)[:4]
    bbox = draw.textbbox((0, 0), lines[0], font=headline_font)
    line_h = int((bbox[3] - bbox[1]) * 1.30)
    
    src_name, src_prefix = clean_source(source) if source else ("", "")
    src_height = 32 if source else 0
    total_h = line_h * len(lines) + src_height
    
    zone_top = badge_bottom + 8
    zone_bottom = CONTENT_BOTTOM - 16
    start_y = zone_top + (zone_bottom - zone_top - total_h) // 2
    
    y = start_y
    for line in lines:
        draw_text_with_shadow(draw, (MARGIN_L, y), line, palette["text"], headline_font, shadow_offset=2)
        y += line_h
    
    # Source (tracked out, muted)
    if source:
        src_font = load_font("italic", 13)
        draw.text((MARGIN_L, y + 14), f"{src_prefix}{src_name}".upper(), 
                  fill=palette["text_muted"], font=src_font)
    
    # 7. Brand bar
    img, draw = draw_brand_bar(img, palette)
    
    # 8. Film grain + vignette
    img = add_film_grain(img, intensity=10, opacity=0.03)
    img = add_vignette(img, strength=0.25)
    
    return img

def generate_brandjacking(title, topic, source=""):
    palette = PALETTES["Brandjacking"]
    
    img = create_radial_gradient(W, H, palette["bg_center"], palette["bg_edge"], cx_ratio=0.35, cy_ratio=0.35)
    img = add_subtle_shape(img, palette)
    img = add_glow(img, W // 3, H // 2 - 30, 500, 200, palette["accent_glow"], opacity=0.07)
    
    draw = ImageDraw.Draw(img)
    
    # Left accent stripe (thin, glowing)
    for y_px in range(H):
        fade = 1.0 - abs(y_px - H//2) / (H * 0.6)
        fade = max(0, min(1, fade))
        c = palette["accent"]
        draw.line([(0, y_px), (3, y_px)], fill=(int(c[0]*fade), int(c[1]*fade), int(c[2]*fade)))
    
    # Badges
    badge_font = load_font("bold", 11)
    topic_font = load_font("light", 10)
    draw, badge_end = draw_glass_badge(img, draw, MARGIN_L, 34, palette["badge_label"],
                                       badge_font, (240, 235, 255), palette["accent"])
    tc = TOPIC_COLORS.get(topic, (150, 150, 150))
    draw, _ = draw_glass_badge(img, draw, badge_end + 10, 34, topic.upper(), topic_font, tc, tc)
    badge_bottom = 72
    
    # Small elegant quote mark (at reduced opacity)
    quote_font = load_font("bold", 48)
    draw.text((MARGIN_L - 4, badge_bottom + 2), "\u201C", 
              fill=(palette["accent"][0], palette["accent"][1], palette["accent"][2], 90), font=quote_font)
    
    # Headline centered
    headline_font = load_font("bold", 42)
    lines = wrap_text(title, headline_font, TEXT_WIDTH - 10, draw)[:4]
    bbox = draw.textbbox((0, 0), lines[0], font=headline_font)
    line_h = int((bbox[3] - bbox[1]) * 1.30)
    
    src_name, src_prefix = clean_source(source) if source else ("", "")
    src_height = 32 if source else 0
    total_h = line_h * len(lines) + src_height
    
    zone_top = badge_bottom + 30
    zone_bottom = CONTENT_BOTTOM - 16
    start_y = zone_top + (zone_bottom - zone_top - total_h) // 2
    
    y = start_y
    for line in lines:
        draw_text_with_shadow(draw, (MARGIN_L, y), line, palette["text"], headline_font, shadow_offset=2)
        y += line_h
    
    if source:
        src_font = load_font("italic", 13)
        draw.text((MARGIN_L, y + 14), f"{src_prefix}{src_name}".upper(),
                  fill=palette["text_muted"], font=src_font)
    
    img, draw = draw_brand_bar(img, palette)
    img = add_film_grain(img, intensity=10, opacity=0.03)
    img = add_vignette(img, strength=0.25)
    return img

def generate_namejacking(title, topic, source=""):
    palette = PALETTES["Namejacking"]
    
    img = create_radial_gradient(W, H, palette["bg_center"], palette["bg_edge"], cx_ratio=0.45, cy_ratio=0.40)
    img = add_subtle_shape(img, palette)
    img = add_glow(img, W // 2, H // 2, 500, 200, palette["accent_glow"], opacity=0.05)
    
    draw = ImageDraw.Draw(img)
    
    # Top gold accent (gradient fade at edges)
    for x in range(W):
        center_dist = abs(x - W//2) / (W//2)
        alpha = max(0, 1 - center_dist * 0.4)
        c = palette["accent"]
        draw.line([(x, 0), (x, 1)], fill=(int(c[0]*alpha), int(c[1]*alpha), int(c[2]*alpha)))
    
    # Badges
    badge_font = load_font("bold", 11)
    topic_font = load_font("light", 10)
    draw, badge_end = draw_glass_badge(img, draw, MARGIN_L, 34, palette["badge_label"],
                                       badge_font, palette["accent"], palette["accent"])
    tc = TOPIC_COLORS.get(topic, (150, 150, 150))
    draw, _ = draw_glass_badge(img, draw, badge_end + 10, 34, topic.upper(), topic_font, tc, tc)
    badge_bottom = 72
    
    # Left gold accent bar (thin vertical line, fading)
    bar_top = badge_bottom + 10
    bar_bottom = CONTENT_BOTTOM - 20
    for y_px in range(bar_top, bar_bottom):
        mid = (bar_top + bar_bottom) / 2
        dist = abs(y_px - mid) / ((bar_bottom - bar_top) / 2)
        alpha = max(0, 1 - dist * 0.5)
        c = palette["accent"]
        draw.line([(MARGIN_L - 18, y_px), (MARGIN_L - 15, y_px)], 
                  fill=(int(c[0]*alpha), int(c[1]*alpha), int(c[2]*alpha)))
    
    # Headline centered
    headline_font = load_font("bold", 40)
    lines = wrap_text(title, headline_font, TEXT_WIDTH - 20, draw)[:4]
    bbox = draw.textbbox((0, 0), lines[0], font=headline_font)
    line_h = int((bbox[3] - bbox[1]) * 1.32)
    
    src_name, _ = clean_source(source) if source else ("", "")
    attr_height = 42 if src_name else 0
    total_h = line_h * len(lines) + attr_height
    
    zone_top = badge_bottom + 10
    zone_bottom = CONTENT_BOTTOM - 16
    start_y = zone_top + (zone_bottom - zone_top - total_h) // 2
    
    y = start_y
    for line in lines:
        draw_text_with_shadow(draw, (MARGIN_L, y), line, palette["text"], headline_font, shadow_offset=2)
        y += line_h
    
    # Attribution - gold, larger, with em dash
    if src_name:
        attr_font = load_font("italic", 17)
        draw.text((MARGIN_L, y + 16), f"\u2014 {src_name}", fill=palette["accent"], font=attr_font)
    
    img, draw = draw_brand_bar(img, palette)
    img = add_film_grain(img, intensity=10, opacity=0.03)
    img = add_vignette(img, strength=0.22)
    return img

def generate_hot_take(title, topic, source=""):
    palette = PALETTES["Hot Take"]
    
    img = create_radial_gradient(W, H, palette["bg_center"], palette["bg_edge"], cx_ratio=0.3, cy_ratio=0.3)
    img = add_subtle_shape(img, palette)
    img = add_glow(img, W // 3, H // 2 - 50, 400, 200, palette["accent_glow"], opacity=0.08)
    
    draw = ImageDraw.Draw(img)
    
    # Top red accent (thicker, gradient)
    for x in range(W):
        center_dist = abs(x - W//3) / (W * 0.7)
        alpha = max(0, 1 - center_dist * 0.5)
        c = palette["accent"]
        draw.line([(x, 0), (x, 3)], fill=(int(c[0]*alpha), int(c[1]*alpha), int(c[2]*alpha)))
    
    # Badges
    badge_font = load_font("bold", 11)
    topic_font = load_font("light", 10)
    draw, badge_end = draw_glass_badge(img, draw, MARGIN_L, 34, palette["badge_label"],
                                       badge_font, (255, 240, 240), palette["accent"])
    tc = TOPIC_COLORS.get(topic, (150, 150, 150))
    draw, _ = draw_glass_badge(img, draw, badge_end + 10, 34, topic.upper(), topic_font, tc, tc)
    badge_bottom = 72
    
    # Headline - first line in accent red
    headline_font = load_font("bold", 46)
    lines = wrap_text(title, headline_font, TEXT_WIDTH, draw)[:4]
    bbox = draw.textbbox((0, 0), lines[0], font=headline_font)
    line_h = int((bbox[3] - bbox[1]) * 1.28)
    
    src_name, src_prefix = clean_source(source) if source else ("", "")
    src_height = 45 if source else 0
    total_h = line_h * len(lines) + src_height
    
    zone_top = badge_bottom + 8
    zone_bottom = CONTENT_BOTTOM - 16
    start_y = zone_top + (zone_bottom - zone_top - total_h) // 2
    
    y = start_y
    for i, line in enumerate(lines):
        color = palette["accent"] if i == 0 else palette["text"]
        draw_text_with_shadow(draw, (MARGIN_L, y), line, color, headline_font, shadow_offset=2)
        y += line_h
    
    # Accent separator (glowing thin line)
    sep_y = y + 8
    for x in range(MARGIN_L, MARGIN_L + 55):
        fade = 1.0 - (x - MARGIN_L) / 55.0 * 0.5
        c = palette["accent"]
        draw.line([(x, sep_y), (x, sep_y + 2)], fill=(int(c[0]*fade), int(c[1]*fade), int(c[2]*fade)))
    
    if source:
        src_font = load_font("italic", 13)
        draw.text((MARGIN_L, sep_y + 12), f"{src_prefix}{src_name}".upper(),
                  fill=palette["text_muted"], font=src_font)
    
    img, draw = draw_brand_bar(img, palette)
    img = add_film_grain(img, intensity=10, opacity=0.035)
    img = add_vignette(img, strength=0.28)
    return img

# ── Router + CLI ─────────────────────────────────────────────────────────────
GENERATORS = {
    "Newsjacking": generate_newsjacking,
    "Brandjacking": generate_brandjacking,
    "Namejacking": generate_namejacking,
    "Hot Take": generate_hot_take,
}

def generate_visual(title, post_format, topic, source="", output_path=None):
    generator = GENERATORS.get(post_format, generate_newsjacking)
    img = generator(title, topic, source)
    if not output_path:
        safe = "".join(c for c in title[:40] if c.isalnum() or c in " -_").strip().replace(" ", "-")
        ts = datetime.now(CAIRO).strftime("%Y%m%d-%H%M")
        output_path = f"{OUTPUT_DIR}/{ts}-{post_format.lower().replace(' ','-')}-{safe}.png"
    img.save(output_path, "PNG", quality=95)
    return output_path

def notion_req(method, path, body=None):
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read())

def batch_generate():
    pages = notion_req("POST", f"/databases/{RSS_DB}/query", {
        "filter": {"property": "Priority", "select": {"equals": "High"}}, "page_size": 50
    })
    results = pages.get("results", [])
    print(f"Found {len(results)} Gold items")
    generated = 0
    for page in results:
        props = page.get("properties", {})
        title = "".join([t.get("plain_text", "") for t in props.get("Name", {}).get("title", [])])
        formats = [f.get("name", "") for f in props.get("Post Format", {}).get("multi_select", [])]
        categories = [c.get("name", "") for c in props.get("Category", {}).get("multi_select", [])]
        source = "".join([t.get("plain_text", "") for t in props.get("Source", {}).get("rich_text", [])])
        if not title or not formats: continue
        path = generate_visual(title, formats[0], categories[0] if categories else "AI", source)
        print(f"  Generated: {os.path.basename(path)} [{formats[0]}]")
        generated += 1
    print(f"\nDone: {generated} visuals in {OUTPUT_DIR}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Content Factory Visual Generator v3 Premium")
    parser.add_argument("--title"); parser.add_argument("--format", choices=list(GENERATORS.keys()), default="Newsjacking")
    parser.add_argument("--topic", default="AI"); parser.add_argument("--source", default="")
    parser.add_argument("--output"); parser.add_argument("--batch", action="store_true")
    args = parser.parse_args()
    if args.batch: batch_generate()
    elif args.title: print(f"Generated: {generate_visual(args.title, args.format, args.topic, args.source, args.output)}")
    else: parser.print_help()
