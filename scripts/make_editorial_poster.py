from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops
import numpy as np

W, H = 1080, 1350
BG = '#DA7257'
CARD = '#FCFBFA'
TEXT = '#121212'
MUTED = '#555555'
BLUE = '#1D9BF0'

ROOT = Path('/root/.openclaw/workspace')
SRC = ROOT / 'profile-photo.jpg'
PORTRAIT_SRC = Path('/root/.openclaw/media/tool-image-generation/ahmed-bw-editorial-portrait---49ca640a-164e-4ec2-8519-759d600b4bb7.png')
OUT = ROOT / 'artifacts' / 'ahmed-editorial-poster-v1.png'
OUT.parent.mkdir(parents=True, exist_ok=True)

quote = (
    'AI is not a side project. It is becoming the operating layer for how modern '
    'companies decide, execute, and scale. The leaders who learn to work with it now '
    'will build an unfair advantage.'
)

font_regular = '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'
font_bold = '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'
font_avatar = ImageFont.truetype(font_regular, 16)
font_name = ImageFont.truetype(font_bold, 28)
font_sub = ImageFont.truetype(font_regular, 18)
font_quote = ImageFont.truetype(font_regular, 34)
font_quote_bold = ImageFont.truetype(font_bold, 34)
font_pill = ImageFont.truetype(font_bold, 22)
font_check = ImageFont.truetype(font_bold, 22)

img = Image.new('RGBA', (W, H), BG)
draw = ImageDraw.Draw(img)

# shadow + card
shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
shadow_draw = ImageDraw.Draw(shadow)
card_box = (85, 58, 995, 480)
shadow_draw.rounded_rectangle((card_box[0]+6, card_box[1]+10, card_box[2]+6, card_box[3]+10), 28, fill=(0, 0, 0, 38))
shadow = shadow.filter(ImageFilter.GaussianBlur(14))
img.alpha_composite(shadow)
draw.rounded_rectangle(card_box, 28, fill=CARD, outline=(0,0,0,18), width=1)

# source image
src = Image.open(SRC).convert('RGB')
sw, sh = src.size

# avatar crop
avatar = src.crop((sw*0.2, sh*0.12, sw*0.56, sh*0.48)).resize((86, 86), Image.Resampling.LANCZOS)
mask = Image.new('L', (86, 86), 0)
ImageDraw.Draw(mask).ellipse((0,0,85,85), fill=255)
img.paste(avatar, (115, 105), mask)

draw.text((225, 112), 'Ahmed Nasr', font=font_name, fill=TEXT)
# blue check
cx, cy = 492, 126
ImageDraw.Draw(img).ellipse((cx-11, cy-11, cx+11, cy+11), fill=BLUE)
draw.text((486, 113), '✓', font=font_check, fill='white')
draw.text((225, 150), 'Technology Executive • AI Automation', font=font_sub, fill=MUTED)

# quote block with selective bold
x0, y0, max_w = 114, 212, 835
segments = [
    ('“AI is not a side project. ', False),
    ('It is becoming the operating layer', True),
    (' for how modern companies decide, execute, and scale. The leaders who learn to work with it now will build an unfair advantage.”', False),
]
line_spacing = 10
cur_x, cur_y = x0, y0
for text, is_bold in segments:
    font = font_quote_bold if is_bold else font_quote
    words = text.split(' ')
    for i, word in enumerate(words):
        token = word + (' ' if i < len(words)-1 else '')
        bbox = draw.textbbox((0,0), token, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        if cur_x + tw > x0 + max_w:
            cur_x = x0
            cur_y += th + line_spacing
        draw.text((cur_x, cur_y), token, font=font, fill=TEXT)
        cur_x += tw

# Use a cleaner generated headshot as portrait source, then stylize ourselves
portrait_src = Image.open(PORTRAIT_SRC).convert('RGB') if PORTRAIT_SRC.exists() else src.copy()
psw, psh = portrait_src.size
portrait = portrait_src.crop((70, 80, psw-70, psh-10)).resize((640, 855), Image.Resampling.LANCZOS)

# Mask based on bright background + manual shoulder support
pgray = ImageOps.grayscale(portrait)
mask_auto = pgray.point(lambda p: 0 if p > 242 else 255).filter(ImageFilter.GaussianBlur(3))
mask_support = Image.new('L', (640, 855), 0)
md = ImageDraw.Draw(mask_support)
md.ellipse((120, 20, 520, 470), fill=255)
md.rounded_rectangle((120, 315, 520, 855), radius=90, fill=255)
md.ellipse((45, 430, 300, 850), fill=255)
md.ellipse((340, 430, 595, 850), fill=255)
mask_crop = ImageChops.lighter(mask_auto, mask_support).filter(ImageFilter.GaussianBlur(6))

# Stylize with preserved facial detail
base = ImageOps.grayscale(portrait)
base = ImageOps.autocontrast(base, cutoff=1)
base = base.filter(ImageFilter.SMOOTH_MORE)
poster = ImageOps.posterize(base.convert('RGB'), 3).convert('L')
poster = ImageOps.autocontrast(poster)
poster = poster.point(lambda p: 245 if p > 210 else (220 if p > 175 else (170 if p > 130 else (95 if p > 85 else 25))))

edges = base.filter(ImageFilter.FIND_EDGES)
edges = ImageOps.autocontrast(edges)
edges = edges.point(lambda p: 255 if p > 68 else 0).filter(ImageFilter.GaussianBlur(0.5))

# softer halftone texture
arr = np.array(base.resize((160, 214), Image.Resampling.BICUBIC))
dot = Image.new('L', (160*6, 214*6), 255)
draw_dot = ImageDraw.Draw(dot)
for yy in range(arr.shape[0]):
    for xx in range(arr.shape[1]):
        v = arr[yy, xx]
        r = max(0, int((255 - v) / 255 * 2.0))
        if r > 0:
            cx = xx*6 + 3
            cy = yy*6 + 3
            draw_dot.ellipse((cx-r, cy-r, cx+r, cy+r), fill=0)
dot = dot.resize((640, 855), Image.Resampling.BICUBIC)
dot = dot.filter(ImageFilter.GaussianBlur(0.8)).point(lambda p: 255 if p > 235 else 226)

stylized = ImageChops.multiply(poster, dot)
stylized = ImageChops.darker(stylized, ImageOps.invert(edges).point(lambda p: min(255, int(p*0.97))))
stylized = ImageOps.autocontrast(stylized, cutoff=0.5)
rgba = Image.merge('RGBA', (stylized, stylized, stylized, mask_crop))

# very light outline only
edge_alpha = mask_crop.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1.6)).point(lambda p: 28 if p > 26 else 0)
stroke = Image.new('RGBA', rgba.size, (0,0,0,0))
stroke.putalpha(edge_alpha)
img.alpha_composite(stroke, (220, 500))
img.alpha_composite(rgba, (220, 500))

img.convert('RGB').save(OUT, quality=95)
print(OUT)
