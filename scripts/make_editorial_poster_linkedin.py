from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

W, H = 1080, 1350
BG = '#F4F7FB'
CARD = '#FFFFFF'
TEXT = '#0F172A'
MUTED = '#475569'
ACCENT = '#0A66C2'
ACCENT_LIGHT = '#DCEBFA'
LINE = '#E2E8F0'

ROOT = Path('/root/.openclaw/workspace')
SRC = ROOT / 'profile-photo.jpg'
OUT = ROOT / 'artifacts' / 'ahmed-linkedin-poster-v2.png'
OUT.parent.mkdir(parents=True, exist_ok=True)

quote = (
    'AI is not a side project. It is becoming the operating layer for how modern '
    'companies decide, execute, and scale.'
)
quote2 = 'The leaders who learn to work with it now will build an unfair advantage.'

font_regular = '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'
font_bold = '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'
font_black = font_bold

f_kicker = ImageFont.truetype(font_bold, 22)
f_name = ImageFont.truetype(font_bold, 28)
f_role = ImageFont.truetype(font_regular, 18)
f_quote = ImageFont.truetype(font_regular, 46)
f_quote_bold = ImageFont.truetype(font_black, 46)
f_footer = ImageFont.truetype(font_regular, 17)
f_tag = ImageFont.truetype(font_bold, 16)

img = Image.new('RGB', (W, H), BG)
draw = ImageDraw.Draw(img)

# subtle top gradient feel using bands
for i in range(300):
    alpha = int(35 * (1 - i / 300))
    overlay = Image.new('RGBA', (W, 1), (10, 102, 194, alpha))
    img.paste(Image.alpha_composite(Image.new('RGBA', (W, 1), (244, 247, 251, 255)), overlay).convert('RGB'), (0, i))

draw.rounded_rectangle((56, 44, 1024, 1306), radius=36, fill=CARD)

# accent strip
accent = Image.new('RGBA', (W, H), (0,0,0,0))
ad = ImageDraw.Draw(accent)
ad.rounded_rectangle((56, 44, 1024, 1306), radius=36, outline=None, fill=(0,0,0,0))
ad.rounded_rectangle((56, 44, 1024, 170), radius=36, fill=ACCENT)
ad.rectangle((56, 120, 1024, 170), fill=ACCENT)
img = Image.alpha_composite(img.convert('RGBA'), accent).convert('RGB')
draw = ImageDraw.Draw(img)

# header
ax, ay = 92, 86
draw.rounded_rectangle((ax, ay, ax+160, ay+34), radius=17, fill='white')
draw.text((ax+16, ay+8), 'LINKEDIN POST', font=f_tag, fill=ACCENT)

draw.text((92, 210), 'Ahmed Nasr', font=f_name, fill=TEXT)
draw.text((92, 246), 'Technology Executive • AI Automation', font=f_role, fill=MUTED)

# divider
for x in range(92, 610, 6):
    draw.line((x, 289, min(x+3, 610), 289), fill=LINE, width=2)

# quote block
x0, y0, max_w = 92, 335, 470
segments = [
    ('“AI is not a side project. ', False),
    ('It is becoming the operating layer', True),
    (' for how modern companies decide, execute, and scale. ', False),
    ('The leaders who learn to work with it now will build an unfair advantage.”', True),
]
cur_x, cur_y = x0, y0
line_gap = 12
for text, is_bold in segments:
    font = f_quote_bold if is_bold else f_quote
    words = text.split(' ')
    for i, word in enumerate(words):
        token = word + (' ' if i < len(words)-1 else '')
        bbox = draw.textbbox((0,0), token, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        if cur_x + tw > x0 + max_w:
            cur_x = x0
            cur_y += th + line_gap
        draw.text((cur_x, cur_y), token, font=font, fill=TEXT)
        cur_x += tw

# insight box
ibox = (92, 1000, 586, 1185)
draw.rounded_rectangle(ibox, radius=26, fill=ACCENT_LIGHT)
draw.text((118, 1038), 'Why this matters', font=f_kicker, fill=ACCENT)
insight = (
    'Executives who treat AI as a workflow layer, not a side initiative, '\
    'will move faster on decisions, execution, and scale.'
)
small = ImageFont.truetype(font_regular, 28)
ix, iy, mw = 118, 1082, 420
cx, cy = ix, iy
for word in insight.split(' '):
    token = word + ' '
    bbox = draw.textbbox((0,0), token, font=small)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    if cx + tw > ix + mw:
        cx = ix
        cy += th + 8
    draw.text((cx, cy), token, font=small, fill=TEXT)
    cx += tw

# portrait panel on right
panel = (646, 210, 968, 1190)
draw.rounded_rectangle(panel, radius=28, fill='#E8EEF5')

src = Image.open(SRC).convert('RGB')
sw, sh = src.size
crop = src.crop((360, 80, 1120, 1180)).resize((322, 980), Image.Resampling.LANCZOS)
# professional blue-gray treatment
crop = ImageOps.colorize(ImageOps.grayscale(crop), black='#0F172A', white='#EEF4FB')
# brighten face gently
crop = Image.blend(crop, Image.new('RGB', crop.size, '#DCEBFA'), 0.10)

# rounded mask
mask = Image.new('L', crop.size, 0)
ImageDraw.Draw(mask).rounded_rectangle((0,0,crop.size[0], crop.size[1]), radius=28, fill=255)
img.paste(crop, (646, 210), mask)

draw = ImageDraw.Draw(img)

# subtle footer accent and linkedin mark
for x in range(92, 968, 8):
    draw.line((x, 1248, min(x+4, 968), 1248), fill=LINE, width=2)

for i in range(3):
    draw.rounded_rectangle((904 + i*18, 88, 916 + i*18, 100), radius=6, fill='white')

img.save(OUT, quality=95)
print(OUT)
