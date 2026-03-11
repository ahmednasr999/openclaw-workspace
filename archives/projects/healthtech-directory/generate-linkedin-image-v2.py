#!/usr/bin/env python3
"""
LinkedIn Post Image Generator v2 - Improved Design
Creates a professional quote-style image for social media
"""
from PIL import Image, ImageDraw
import textwrap

# Configuration - LinkedIn optimal size
WIDTH = 1200
HEIGHT = 628
BACKGROUND_COLOR = (26, 32, 44)  # Dark slate
ACCENT_COLOR = (99, 102, 241)  # Indigo
TEXT_COLOR = (248, 250, 252)  # Nearly white
MUTED_COLOR = (203, 213, 225)  # Muted

def draw_text_centered(draw, text, y, font, color, max_width=None):
    """Draw centered text"""
    if max_width:
        lines = textwrap.wrap(text, width=max_width)
    else:
        lines = [text]
    
    for line in lines:
        text_width = draw.textlength(line, font=font)
        draw.text(((WIDTH - text_width) / 2, y), line, font=font, fill=color)
        y += font.getbbox(line)[3] - font.getbbox(line)[1] + 10
    
    return y

def create_v2_image():
    """Create improved LinkedIn image"""
    
    # Create image
    img = Image.new('RGB', (WIDTH, HEIGHT), color=BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Use basic fonts
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
        heading_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
        body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        title_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Top accent line
    draw.rectangle([(0, 0), (WIDTH, 6)], fill=ACCENT_COLOR)
    
    # Main hook - centered quote
    hook = "The $50M mistake"
    hook2 = "I almost made"
    
    y = 80
    y = draw_text_centered(draw, hook, y, title_font, MUTED_COLOR)
    y = draw_text_centered(draw, hook2, y, title_font, MUTED_COLOR)
    
    # Quote marks
    y += 20
    draw.text(((WIDTH / 2) - 60, y), '"', font=heading_font, fill=ACCENT_COLOR)
    draw.text(((WIDTH / 2) + 40, y), '"', font=heading_font, fill=ACCENT_COLOR)
    
    # Divider
    y += 60
    divider_w = 150
    draw.rectangle([((WIDTH - divider_w) / 2, y), ((WIDTH + divider_w) / 2, y + 4)], fill=ACCENT_COLOR)
    
    # Lessons section
    y += 60
    lessons_title = "What I learned:"
    draw_text_centered(draw, lessons_title, y, body_font, ACCENT_COLOR)
    
    y += 50
    
    # Lesson boxes
    lessons = [
        ("OUTCOMES > OUTPUTS", "Measure results, not deliverables"),
        ("DATA > OPINIONS", "Evidence beats gut feelings"),
        ("INFLUENCE > AUTHORITY", "Soft power wins"),
    ]
    
    box_height = 70
    box_width = 550
    start_x = (WIDTH - (3 * box_width + 40)) / 2
    
    for i, (title, subtitle) in enumerate(lessons):
        x = start_x + i * (box_width + 20)
        box_y = y
        
        # Draw box
        draw.rectangle([(x, box_y), (x + box_width, box_y + box_height)], 
                       outline=ACCENT_COLOR, width=2)
        
        # Draw text
        title_w = draw.textlength(title, small_font)
        draw.text(((x + box_width - title_w) / 2, box_y + 12), title, font=small_font, fill=TEXT_COLOR)
        
        subtitle_w = draw.textlength(subtitle, small_font)
        draw.text(((x + box_width - subtitle_w) / 2, box_y + 42), subtitle, font=small_font, fill=MUTED_COLOR)
    
    y += box_height + 50
    
    # Results section
    results_title = "The outcome?"
    y = draw_text_centered(draw, results_title, y, body_font, MUTED_COLOR)
    
    y += 15
    draw.rectangle([((WIDTH - 400) / 2, y), ((WIDTH + 400) / 2, y + 2)], fill=MUTED_COLOR)
    
    y += 20
    
    # Results in one line
    results = ["↓ 23% Readmissions", "↑ 89% Adoption", "Under budget ✓"]
    result_x = WIDTH / 2 - 250
    
    for i, result in enumerate(results):
        x = result_x + i * 180
        draw.text((x, y), result, font=body_font, fill=ACCENT_COLOR)
    
    # Hashtags at bottom
    y = HEIGHT - 50
    hashtags = "#HealthTech  #PMO  #DigitalTransformation  #Leadership"
    text_w = draw.textlength(hashtags, small_font)
    draw.text(((WIDTH - text_w) / 2, y), hashtags, font=small_font, fill=(100, 116, 139))
    
    # Save
    output_path = "/root/.openclaw/workspace/healthtech-directory/linkedin-post-image-v2.png"
    img.save(output_path, quality=95, optimize=True)
    
    print(f"✅ Image saved: {output_path}")
    print(f"   Size: {WIDTH}x{HEIGHT}")
    
    return output_path

if __name__ == "__main__":
    create_v2_image()
