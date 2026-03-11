#!/usr/bin/env python3
"""
LinkedIn Post Image Generator - Quote Style
Creates an engaging image for social media
"""
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

# Configuration
WIDTH = 1200
HEIGHT = 628  # LinkedIn recommended
BACKGROUND_COLOR = (15, 23, 42)  # Dark blue/slate
ACCENT_COLOR = (56, 189, 248)  # Light blue
TEXT_COLOR = (255, 255, 255)  # White
SECONDARY_COLOR = (148, 163, 184)  # Muted

def create_linkedin_image():
    """Create a professional LinkedIn image"""
    
    # Create image
    img = Image.new('RGB', (WIDTH, HEIGHT), color=BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Try to use default font, fallback to basic
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw accent bar at top
    draw.rectangle([(0, 0), (WIDTH, 8)], fill=ACCENT_COLOR)
    
    # Main hook text
    hook_text = '"The $50M mistake I almost made"'
    
    # Wrap text
    hook_lines = textwrap.wrap(hook_text, width=25)
    
    # Draw hook
    y_position = 120
    for line in hook_lines:
        text_width = draw.textlength(line, font=title_font)
        draw.text(((WIDTH - text_width) / 2, y_position), line, font=title_font, fill=SECONDARY_COLOR)
        y_position += 75
    
    # Draw separator
    y_position += 30
    separator_width = 200
    draw.rectangle([(WIDTH - separator_width) / 2, y_position, (WIDTH + separator_width) / 2, y_position + 4], fill=ACCENT_COLOR)
    
    # Key lessons
    lessons = [
        ("🎯", "Outcomes trump outputs"),
        ("📊", "Data beats opinions"),
        ("🤝", "Influence > authority"),
        ("⚡", "Speed of learning"),
    ]
    
    y_position += 60
    
    for emoji, lesson in lessons:
        # Draw emoji
        draw.text((100, y_position), emoji, font=body_font, fill=(255, 255, 255))
        
        # Draw lesson text
        draw.text((180, y_position + 5), lesson, font=body_font, fill=TEXT_COLOR)
        y_position += 70
    
    # Draw result box
    y_position += 30
    box_y = y_position
    draw.rectangle([(80, box_y), (WIDTH - 80, box_y + 120)], outline=ACCENT_COLOR, width=3)
    
    results = [
        ("↓ 23% Patient readmission", ACCENT_COLOR),
        ("↑ 89% Staff adoption", ACCENT_COLOR),
        ("Under budget ✓", ACCENT_COLOR),
    ]
    
    x_positions = [300, 600, 900]
    for i, (result, color) in enumerate(results):
        text_width = draw.textlength(result, font=small_font)
        draw.text((x_positions[i] - text_width / 2, box_y + 50), result, font=small_font, fill=color)
    
    # Footer
    y_position = HEIGHT - 60
    footer_text = "#HealthTech #PMO #DigitalTransformation #Leadership"
    text_width = draw.textlength(footer_text, font=small_font)
    draw.text(((WIDTH - text_width) / 2, y_position), footer_text, font=small_font, fill=SECONDARY_COLOR)
    
    # Save
    output_path = "/root/.openclaw/workspace/healthtech-directory/linkedin-post-image.png"
    img.save(output_path, quality=95, optimize=True)
    
    print(f"✅ Image saved: {output_path}")
    print(f"   Size: {WIDTH}x{HEIGHT}")
    
    return output_path

if __name__ == "__main__":
    create_linkedin_image()
