from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

W, H = 1080, 1350
BG = '#F5F8FC'
CARD = '#FFFFFF'
TEXT = '#0F172A'
MUTED = '#475569'
ACCENT = '#0A66C2'
ACCENT_DARK = '#084B91'
ACCENT_LIGHT = '#DCEBFA'
LINE = '#D8E2EE'

ROOT = Path('/root/.openclaw/workspace')
SRC = ROOT / 'profile-photo.jpg'
OUT = ROOT / 'artifacts' / 'ahmed-linkedin-carousel-cover-v3.png'
OUT.parent.mkdir(parents=True, exist_ok=True)

font_regular = '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'
font_bold = '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'

f_tag = ImageFont.truetype(font_bold, 20)
f_title = ImageFont.truetype(font_bold, 70)
f_sub = ImageFont.truetype(font_regular, 28)
f_footer_name = ImageFont.truetype(font_bold, 26)
f_footer_role = ImageFont.truetype(font_regular, 18)
f_swipe = ImageFont.truetype(font_bold, 24)
f_chip = ImageFont.truetype(font_bold, 18)

img = Image.new('RGB', (W, H), BG)
draw = ImageDraw.Draw(img)

# faint blue wash at top right
wash = Image.new('RGBA', (W, H), (0,0,0,0))
wd = ImageDraw.Draw(wash)
for r, a in [(560, 22), (430, 28), (300, 36)]:
    wd.ellipse((720-r//2, -60-r//2, 720+r//2, -60+r//2), fill=(10,102,194,a))
img = Image.alpha_composite(img.convert('RGBA'), wash).convert('RGB')
draw = ImageDraw.Draw(img)

# main card
draw.rounded_rectangle((42, 42, 1038, 1308), radius=38, fill=CARD)

# left accent rail
draw.rounded_rectangle((74, 84, 98, 330), radius=12, fill=ACCENT)

# header tag
draw.rounded_rectangle((122, 92, 306, 132), radius=20, fill=ACCENT_LIGHT)
draw.text((142, 104), 'LinkedIn Carousel', font=f_tag, fill=ACCENT)

# title
x0, y0, max_w = 122, 180, 480
segments = [
    ('AI is becoming ', False),
    ('the operating layer ', True),
    ('for modern companies', False),
]
cur_x, cur_y = x0, y0
line_gap = 14
last_h = 0
for text, bold in segments:
    font = f_title
    words = text.split(' ')
    for i, word in enumerate(words):
        if word == '':
            continue
        token = word + (' ' if i < len(words)-1 else '')
        bbox = draw.textbbox((0,0), token, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        last_h = th
        if cur_x + tw > x0 + max_w:
            cur_x = x0
            cur_y += th + line_gap
        draw.text((cur_x, cur_y), token, font=font, fill=ACCENT_DARK if bold else TEXT)
        cur_x += tw

title_bottom = cur_y + last_h

sub = 'Leaders who learn to work with AI now will build an unfair advantage in execution and scale.'
small = f_sub
sx, sy, smw = 122, title_bottom + 54, 455
cx, cy = sx, sy
for word in sub.split(' '):
    token = word + ' '
    bbox = draw.textbbox((0,0), token, font=small)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    if cx + tw > sx + smw:
        cx = sx
        cy += th + 10
    draw.text((cx, cy), token, font=small, fill=MUTED)
    cx += tw

sub_bottom = cy + (draw.textbbox((0,0), 'Ag', font=small)[3] - draw.textbbox((0,0), 'Ag', font=small)[1])

# topic chips
chips = ['AI Strategy', 'Leadership', 'Execution', 'Scale']
chip_y = sub_bottom + 44
chip_x = 122
for chip in chips:
    bbox = draw.textbbox((0,0), chip, font=f_chip)
    w = bbox[2] - bbox[0] + 28
    draw.rounded_rectangle((chip_x, chip_y, chip_x + w, chip_y + 38), radius=19, fill='#EEF4FB')
    draw.text((chip_x + 14, chip_y + 10), chip, font=f_chip, fill=ACCENT)
    chip_x += w + 12

# swipe CTA
cta_y = chip_y + 96
cta_box = (122, cta_y, 380, cta_y + 56)
draw.rounded_rectangle(cta_box, radius=24, fill=ACCENT)
draw.text((146, cta_y + 16), 'Swipe for insights →', font=f_swipe, fill='white')

# subtle rule above footer
for x in range(122, 956, 7):
    draw.line((x, 1146, min(x+4, 956), 1146), fill=LINE, width=2)

# footer text
draw.text((122, 1186), 'Ahmed Nasr', font=f_footer_name, fill=TEXT)
draw.text((122, 1221), 'Technology Executive • AI Automation', font=f_footer_role, fill=MUTED)

# portrait panel
panel = (610, 118, 972, 1218)
draw.rounded_rectangle(panel, radius=34, fill='#EAF1F8')

src = Image.open(SRC).convert('RGB')
# crop for a more confident chest-up framing
sw, sh = src.size
portrait = src.crop((310, 55, 1100, 1210)).resize((362, 1100), Image.Resampling.LANCZOS)
portrait = ImageOps.colorize(ImageOps.grayscale(portrait), black='#1C2430', white='#F7FBFF')
portrait = Image.blend(portrait, Image.new('RGB', portrait.size, '#D7E7F6'), 0.12)

# soften and increase contrast slightly
portrait = ImageOps.autocontrast(portrait, cutoff=1)
portrait = portrait.filter(ImageFilter.SMOOTH_MORE)

mask = Image.new('L', portrait.size, 0)
md = ImageDraw.Draw(mask)
md.rounded_rectangle((0,0,362,1100), radius=34, fill=255)
img.paste(portrait, (610, 118), mask)
draw = ImageDraw.Draw(img)

# bottom blue panel inside portrait area for balance
overlay = Image.new('RGBA', (362, 240), (0,0,0,0))
od = ImageDraw.Draw(overlay)
for i in range(240):
    a = int(210 * (i / 239))
    od.line((0, i, 362, i), fill=(10, 102, 194, a))
img = img.convert('RGBA')
img.alpha_composite(overlay, (610, 978))
img = img.convert('RGB')
draw = ImageDraw.Draw(img)

# mini badge on portrait
badge = (640, 1032, 925, 1092)
draw.rounded_rectangle(badge, radius=24, fill='white')
draw.text((662, 1050), 'Executive AI perspective', font=f_chip, fill=ACCENT_DARK)

# page indicator
for i in range(5):
    fill = ACCENT if i == 0 else '#BFD3E8'
    draw.ellipse((820 + i*28, 1228, 834 + i*28, 1242), fill=fill)

img.save(OUT, quality=95)
print(OUT)
