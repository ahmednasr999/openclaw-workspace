#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 2160, 3840
OUT = Path("output/linkedin/return-on-tokens-rot-daily-style-2026-06-10.png")
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def make_background() -> Image.Image:
    img = Image.new("RGB", (W, H), (6, 13, 24))
    pix = img.load()
    for y in range(H):
        t = y / (H - 1)
        base = (lerp(8, 2, t), lerp(20, 9, t), lerp(36, 23, t))
        for x in range(W):
            dx1 = (x - W * 0.2) / W
            dy1 = (y - H * 0.18) / H
            glow1 = max(0.0, 1.0 - math.sqrt(dx1 * dx1 + dy1 * dy1) * 3.0)
            dx2 = (x - W * 0.82) / W
            dy2 = (y - H * 0.58) / H
            glow2 = max(0.0, 1.0 - math.sqrt(dx2 * dx2 + dy2 * dy2) * 2.7)
            r = min(255, base[0] + int(18 * glow1) + int(20 * glow2))
            g = min(255, base[1] + int(22 * glow1) + int(12 * glow2))
            b = min(255, base[2] + int(40 * glow1) + int(4 * glow2))
            pix[x, y] = (r, g, b)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    grid = (78, 157, 174, 24)
    for x in range(120, W, 180):
        d.line([(x, 0), (x, H)], fill=grid, width=1)
    for y in range(160, H, 180):
        d.line([(0, y), (W, y)], fill=grid, width=1)
    for i in range(13):
        x0 = 120 + i * 155
        d.line([(x0, 2580 + i * 12), (W - 220, 2100 + i * 28)], fill=(196, 158, 75, 24), width=2)
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def rounded(draw: ImageDraw.ImageDraw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def glow_rect(base: Image.Image, box, radius: int, color, blur: int = 36):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(box, radius=radius, fill=color)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)


def center_text(d: ImageDraw.ImageDraw, xy, text, fnt, fill, anchor="mm"):
    d.text(xy, text, font=fnt, fill=fill, anchor=anchor)


def draw_wrapped(d, text, xy, fnt, fill, max_width, line_gap=10, anchor="la"):
    words = text.split()
    lines = []
    line = ""
    for word in words:
        candidate = (line + " " + word).strip()
        if d.textbbox((0, 0), candidate, font=fnt)[2] <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    x, y = xy
    ascent = d.textbbox((0, 0), "Ag", font=fnt)[3]
    for i, line in enumerate(lines):
        d.text((x, y + i * (ascent + line_gap)), line, font=fnt, fill=fill, anchor=anchor)
    return y + len(lines) * (ascent + line_gap)


def draw_token_stack(d, cx, cy, accent):
    for i in range(5):
        y = cy + i * 42
        shade = (accent[0], accent[1], accent[2], 150 - i * 12)
        d.ellipse((cx - 138, y - 38, cx + 138, y + 38), outline=shade, width=5)
        d.arc((cx - 138, y - 38, cx + 138, y + 38), 0, 180, fill=(255, 255, 255, 56), width=2)


def draw_arrow(d, start, end, color):
    d.line([start, end], fill=color, width=8)
    ex, ey = end
    sx, sy = start
    ang = math.atan2(ey - sy, ex - sx)
    left = (ex - math.cos(ang - 0.58) * 42, ey - math.sin(ang - 0.58) * 42)
    right = (ex - math.cos(ang + 0.58) * 42, ey - math.sin(ang + 0.58) * 42)
    d.polygon([end, left, right], fill=color)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img = make_background()
    d = ImageDraw.Draw(img)

    white = (244, 249, 252, 255)
    muted = (164, 181, 196, 255)
    cyan = (72, 203, 223, 255)
    gold = (212, 171, 82, 255)
    line = (99, 198, 219, 64)
    glass = (14, 30, 48, 178)

    d.text((180, 230), "AI GOVERNANCE METRIC", font=font(42, True), fill=gold)
    d.line((180, 304, 515, 304), fill=(212, 171, 82, 180), width=4)

    d.text((180, 470), "RETURN ON", font=font(190, True), fill=white)
    d.text((180, 680), "TOKENS", font=font(232, True), fill=gold)
    draw_wrapped(d, "Measure AI value by business outcomes, not token volume.", (186, 980), font(58), muted, 1550, line_gap=14)

    panel = (170, 1275, W - 170, 2510)
    glow_rect(img, panel, 48, (72, 203, 223, 28), 48)
    glow_rect(img, (520, 1460, 1640, 2360), 440, (212, 171, 82, 18), 90)
    rounded(d, panel, 54, glass, outline=line, width=3)

    d.text((260, 1385), "TOKENS IN", font=font(38, True), fill=cyan)
    d.text((260, 1458), "Prompting\nModel calls\nRetries", font=font(42), fill=muted, spacing=18)
    draw_token_stack(d, 430, 1735, cyan)

    d.text((W - 760, 1385), "VALUE OUT", font=font(38, True), fill=gold)
    d.text((W - 760, 1458), "Time saved\nCost avoided\nBetter decisions", font=font(42), fill=muted, spacing=18)
    chart_base = 1968
    for i, h in enumerate([220, 170, 280, 205]):
        x = W - 585 + i * 82
        d.rounded_rectangle((x, chart_base - h, x + 46, chart_base), radius=16, fill=(212, 171, 82, 150))
        d.rounded_rectangle((x, chart_base - h, x + 46, chart_base - h + 38), radius=16, fill=(255, 234, 164, 110))

    draw_arrow(d, (635, 1800), (855, 1800), (72, 203, 223, 165))
    draw_arrow(d, (1305, 1800), (1525, 1800), (212, 171, 82, 170))

    ring_box = (805, 1485, 1355, 2035)
    d.ellipse(ring_box, outline=(72, 203, 223, 90), width=10)
    d.arc(ring_box, -80, 260, fill=gold, width=20)
    center_text(d, (1080, 1738), "ROT", font(128, True), white)
    center_text(d, (1080, 1855), "VALUE PER TOKEN", font(32, True), muted)

    formula_box = (360, 2180, W - 360, 2388)
    rounded(d, formula_box, 32, (4, 12, 22, 166), outline=(212, 171, 82, 108), width=2)
    center_text(d, (W // 2, 2264), "ROT = Net Business Value / Token Cost", font(60, True), white)
    center_text(d, (W // 2, 2338), "accepted outcomes divided by total AI consumption", font(35), muted)

    pillars = [("GOVERN", "usage"), ("MEASURE", "outcomes"), ("ATTRIBUTE", "cost"), ("OPTIMIZE", "execution")]
    top = 2650
    gap = 34
    card_w = (W - 2 * 170 - 3 * gap) // 4
    for i, (label, sub) in enumerate(pillars):
        x0 = 170 + i * (card_w + gap)
        box = (x0, top, x0 + card_w, top + 430)
        rounded(d, box, 34, (13, 28, 44, 176), outline=(105, 199, 215, 58), width=2)
        center_text(d, (x0 + card_w // 2, top + 112), f"0{i+1}", font(42, True), gold)
        center_text(d, (x0 + card_w // 2, top + 222), label, font(48, True), white)
        center_text(d, (x0 + card_w // 2, top + 298), sub, font(38), muted)
        d.line((x0 + 64, top + 355, x0 + card_w - 64, top + 355), fill=(212, 171, 82, 100), width=3)

    d.line((170, 3370, W - 170, 3370), fill=(255, 255, 255, 60), width=2)
    d.text((170, 3472), "Ahmed Nasr", font=font(54, True), fill=white)
    d.text((170, 3548), "PMO • AI Automation • Digital Transformation", font=font(38), fill=muted)
    d.text((W - 170, 3510), "EXECUTION INTELLIGENCE", font=font(34, True), fill=gold, anchor="ra")

    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((-700, -900, W + 700, H + 900), fill=255)
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 110))
    vignette.putalpha(Image.eval(mask, lambda p: 110 - int(p * 0.43)))
    img.alpha_composite(vignette)

    img.convert("RGB").save(OUT, quality=96)
    print(OUT)


if __name__ == "__main__":
    main()
