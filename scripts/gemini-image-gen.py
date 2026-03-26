#!/usr/bin/env python3
"""
Gemini Image Generator for LinkedIn Posts
==========================================
Free AI image generation via Composio Gemini integration.
Generates professional visuals for LinkedIn content pipeline.

Usage:
  python3 gemini-image-gen.py --prompt "Your image description"
  python3 gemini-image-gen.py --prompt "..." --aspect 16:9 --output /tmp/my-image.png
  python3 gemini-image-gen.py --topic "digital transformation" --template linkedin
  python3 gemini-image-gen.py --notion-page <page-id>  # Auto-generate from Notion post content
"""
import argparse, json, os, ssl, sys, urllib.request
from datetime import datetime, timezone, timedelta

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
OUTPUT_DIR = f"{WORKSPACE}/media/post-visuals"
GATEWAY_URL = "http://127.0.0.1:18789"
os.makedirs(OUTPUT_DIR, exist_ok=True)
CAIRO = timezone(timedelta(hours=2))
ctx = ssl.create_default_context()

# ── LinkedIn Visual Prompt Templates ─────────────────────────────────────────
TEMPLATES = {
    "linkedin": (
        "Professional LinkedIn post banner image. Dark navy blue gradient background. "
        "Clean minimalist corporate design. {subject_desc} "
        "No text overlay. Modern, premium feel suitable for executive content. "
        "High quality, photorealistic lighting."
    ),
    "abstract": (
        "Abstract professional banner. Dark background with subtle gradient. "
        "Geometric shapes and flowing lines representing {subject_desc}. "
        "Minimalist, modern, no text. Corporate premium aesthetic."
    ),
    "tech": (
        "Technology-themed professional banner. Dark blue-black gradient. "
        "Digital network nodes, data visualization elements, circuit patterns. "
        "{subject_desc}. No text overlay. Futuristic corporate design."
    ),
    "leadership": (
        "Executive leadership themed banner. Dark sophisticated background. "
        "Abstract elements suggesting strategy and vision - chess pieces, "
        "pathways, horizon light. {subject_desc}. No text. Premium corporate."
    ),
    "healthcare": (
        "Healthcare technology themed banner. Dark blue-teal gradient. "
        "Abstract medical/health elements - DNA helixes, heartbeat lines, "
        "hospital silhouettes, data streams. {subject_desc}. No text. "
        "Professional, modern, suitable for GCC healthcare executive content."
    ),
}

# ── Notion Integration ───────────────────────────────────────────────────────
def load_notion_token():
    with open(f"{WORKSPACE}/config/notion.json") as f:
        return json.load(f)["token"]

def get_notion_page_content(page_id):
    """Fetch post title and content from Notion page."""
    token = load_notion_token()
    # Get page properties
    url = f"https://api.notion.com/v1/pages/{page_id}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
    })
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        page = json.loads(r.read())
    
    title = ""
    props = page.get("properties", {})
    for key in ["Title", "Name", "title"]:
        if key in props:
            title_arr = props[key].get("title", [])
            title = "".join(t.get("plain_text", "") for t in title_arr)
            break
    
    # Get page blocks for hook/draft content
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=20"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
    })
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        blocks = json.loads(r.read())
    
    text_parts = []
    for block in blocks.get("results", []):
        btype = block.get("type", "")
        if btype in ("paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item"):
            rich_text = block.get(btype, {}).get("rich_text", [])
            text_parts.append("".join(t.get("plain_text", "") for t in rich_text))
    
    return title, "\n".join(text_parts[:5])  # First 5 blocks

def generate_prompt_from_content(title, content, template="linkedin"):
    """Use LLM to create an image prompt from post content."""
    tmpl = TEMPLATES.get(template, TEMPLATES["linkedin"])
    
    # Build a subject description from the title
    subject = title if title else "professional business concepts"
    prompt = tmpl.format(subject_desc=f"Visual elements representing: {subject}")
    return prompt

# ── Gemini Prompt Builder ─────────────────────────────────────────────────────
GEMINI_TOPIC_TEMPLATES = {
    "Healthcare": "Healthcare technology banner. Dark blue-teal gradient. Abstract medical elements - DNA helixes, data streams, hospital silhouettes. {topic_hint}. No text overlay. Professional executive content.",
    "HealthTech": "Digital health technology banner. Dark gradient. Abstract health data visualization, connected medical devices, futuristic clinical interface. {topic_hint}. No text. Modern premium.",
    "AI": "Artificial intelligence themed banner. Dark navy gradient. Neural network nodes, data flow, abstract AI brain visualization. {topic_hint}. No text overlay. Corporate premium aesthetic.",
    "Digital Transformation": "Digital transformation banner. Dark gradient. Abstract geometric network, data flowing through connected nodes, modern enterprise visualization. {topic_hint}. No text. Executive quality.",
    "PMO": "Project management and strategy banner. Dark sophisticated background. Abstract Gantt-like lines, milestone markers, strategic pathway visualization. {topic_hint}. No text. Premium corporate.",
    "Strategy": "Business strategy banner. Dark background with subtle gradient. Abstract chess-like elements, strategic pathways, decision tree visualization. {topic_hint}. No text. Executive quality.",
    "FinTech": "Financial technology banner. Dark blue-purple gradient. Abstract fintech elements - transaction flows, digital currency, secure connections. {topic_hint}. No text. Premium corporate.",
}

def build_gemini_prompt(topic, headline=""):
    """Build a topic-aware Gemini prompt for LinkedIn visuals."""
    topic_hint = f"themes of: {headline[:80]}" if headline else f"themes of: {topic}"
    tmpl = GEMINI_TOPIC_TEMPLATES.get(topic,
        "Professional LinkedIn post banner. Dark navy gradient. Clean minimalist corporate design. Abstract elements representing {topic_hint}. No text overlay. Modern premium executive content."
    )
    return tmpl.format(topic_hint=topic_hint)

# ── Gemini Image Generation (via Composio) ───────────────────────────────────
def get_composio_params(prompt, aspect_ratio="16:9", model="gemini-2.5-flash-image", output_path=None):
    """Build Composio tool call parameters for GEMINI_GENERATE_IMAGE.
    
    Returns params dict for use with COMPOSIO_MULTI_EXECUTE_TOOL,
    and the intended output path.
    """
    if output_path is None:
        now = datetime.now(CAIRO)
        output_path = f"{OUTPUT_DIR}/gemini-{now.strftime('%Y-%m-%d-%H%M%S')}.png"
    
    params = {
        "tool_slug": "GEMINI_GENERATE_IMAGE",
        "arguments": {
            "prompt": prompt,
            "model": model,
            "aspect_ratio": aspect_ratio,
        }
    }
    
    print(f"📸 Generating image...")
    print(f"   Prompt: {prompt[:100]}...")
    print(f"   Model: {model}")
    print(f"   Aspect: {aspect_ratio}")
    print(f"   Output: {output_path}")
    print(f"\n🔧 Composio parameters:")
    print(json.dumps(params, indent=2))
    
    return params, output_path

def download_image(url, output_path):
    """Download generated image from S3 URL."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
        data = r.read()
    with open(output_path, "wb") as f:
        f.write(data)
    size_kb = len(data) / 1024
    print(f"   ✅ Downloaded: {output_path} ({size_kb:.0f}KB)")
    return output_path

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate LinkedIn post images via Gemini (free)")
    parser.add_argument("--prompt", help="Direct image generation prompt")
    parser.add_argument("--topic", help="Topic to generate a visual for (uses template)")
    parser.add_argument("--template", default="linkedin", choices=list(TEMPLATES.keys()),
                        help="Visual template style")
    parser.add_argument("--notion-page", help="Notion page ID to auto-generate visual from")
    parser.add_argument("--aspect", default="16:9", help="Aspect ratio (default: 16:9)")
    parser.add_argument("--model", default="gemini-2.5-flash-image", 
                        choices=["gemini-2.5-flash-image", "gemini-3-pro-image-preview"],
                        help="Gemini model")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--download-url", help="Download from S3 URL (after Composio generation)")
    args = parser.parse_args()
    
    # If downloading from a previous generation
    if args.download_url:
        out = args.output or f"{OUTPUT_DIR}/gemini-{datetime.now(CAIRO).strftime('%Y-%m-%d-%H%M%S')}.png"
        download_image(args.download_url, out)
        return
    
    # Build the prompt
    if args.prompt:
        prompt = args.prompt
    elif args.topic:
        tmpl = TEMPLATES.get(args.template, TEMPLATES["linkedin"])
        prompt = tmpl.format(subject_desc=f"Visual elements representing: {args.topic}")
    elif args.notion_page:
        title, content = get_notion_page_content(args.notion_page)
        prompt = generate_prompt_from_content(title, content, args.template)
        print(f"📄 From Notion: {title}")
    else:
        parser.error("Provide --prompt, --topic, or --notion-page")
        return
    
    params, output_path = get_composio_params(
        prompt=prompt,
        aspect_ratio=args.aspect,
        model=args.model,
        output_path=args.output,
    )
    
    print(f"\n💡 To generate, run via NASR:")
    print(f'   "Generate image with these Composio params and download to {output_path}"')

if __name__ == "__main__":
    main()
