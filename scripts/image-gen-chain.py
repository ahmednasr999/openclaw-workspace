#!/usr/bin/env python3
"""
Multi-Fallback Image Generation Chain
======================================
Tries multiple free image sources in priority order.
Used by the agent (via Composio) and auto-poster cron.

Priority Chain (topic-aware routing, 7 sources):
  AI/Tech topics:    Gemini Flash → FLUX.1 → Pinterest-Style → SD XL → Gemini Pro → Stock → PIL
  Business/PMO:      Pinterest-Style → Stock → Gemini Flash → FLUX.1 → Gemini Pro → SD XL → PIL
  Default:           Gemini Flash → Pinterest-Style → FLUX.1 → Stock → SD XL → Gemini Pro → PIL

Pinterest-Style (Ruben Hassid method): finds topic infographic + handwritten style ref,
  uses Gemini to merge content + style → scrappy, non-branded, highly shareable images.

Usage:
  # From agent (Composio context):
  from image_gen_chain import ImageGenChain
  chain = ImageGenChain(composio_fn=run_composio_tool)
  result = chain.generate(topic="AI in healthcare", headline="Why hospitals need AI now")

  # CLI:
  python3 image-gen-chain.py --topic "digital transformation" --headline "The future is now"
  python3 image-gen-chain.py --notion-page <page-id>
"""
import argparse, json, os, ssl, sys, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
OUTPUT_DIR = f"{WORKSPACE}/media/post-visuals"
os.makedirs(OUTPUT_DIR, exist_ok=True)
CAIRO = timezone(timedelta(hours=2))
ctx = ssl.create_default_context()

# ── Topic-Aware Gemini Prompts ───────────────────────────────────────────────
GEMINI_PROMPTS = {
    "Healthcare": "Healthcare technology banner. Dark blue-teal gradient. Abstract medical elements - DNA helixes, data streams, hospital silhouettes. {hint}. No text overlay. Professional executive content.",
    "HealthTech": "Digital health technology banner. Dark gradient. Abstract health data visualization, connected medical devices, futuristic clinical interface. {hint}. No text. Modern premium.",
    "AI": "Artificial intelligence themed banner. Dark navy gradient. Neural network nodes, data flow, abstract AI brain visualization. {hint}. No text overlay. Corporate premium aesthetic.",
    "Digital Transformation": "Digital transformation banner. Dark gradient. Abstract geometric network, data flowing through connected nodes, modern enterprise visualization. {hint}. No text. Executive quality.",
    "PMO": "Project management and strategy banner. Dark sophisticated background. Abstract Gantt-like lines, milestone markers, strategic pathway visualization. {hint}. No text. Premium corporate.",
    "Strategy": "Business strategy banner. Dark background with subtle gradient. Abstract chess-like elements, strategic pathways, decision tree visualization. {hint}. No text. Executive quality.",
    "FinTech": "Financial technology banner. Dark blue-purple gradient. Abstract fintech elements - transaction flows, digital currency, secure connections. {hint}. No text. Premium corporate.",
    "Leadership": "Executive leadership banner. Dark elegant gradient. Abstract elements of vision - telescope, compass, ascending paths, light on horizon. {hint}. No text. Premium quality.",
    "Innovation": "Innovation and disruption banner. Dark background. Abstract lightbulb fragments, neural sparks, breaking boundaries visual metaphor. {hint}. No text. Modern corporate.",
    "Data": "Data analytics banner. Dark blue-black gradient. Abstract data visualization - flowing charts, scatter plots, heat maps as art. {hint}. No text. Executive quality.",
}

DEFAULT_PROMPT = (
    "Professional LinkedIn post banner. Dark navy gradient. Clean minimalist corporate design. "
    "Abstract elements representing {hint}. No text overlay. Modern premium executive content."
)

# ── Topic-to-Source Routing ──────────────────────────────────────────────────
# Which image source to try FIRST based on post topic
AI_TECH_TOPICS = {"AI", "Digital Transformation", "HealthTech", "FinTech", "Data", "Innovation"}
BUSINESS_TOPICS = {"PMO", "Strategy", "Leadership", "Healthcare"}

# ── Stock Image Search Queries ───────────────────────────────────────────────
STOCK_QUERIES = {
    "Healthcare": "professional healthcare technology dark blue banner minimal",
    "HealthTech": "digital health innovation dark gradient professional",
    "AI": "artificial intelligence neural network dark blue professional banner",
    "Digital Transformation": "digital transformation technology dark gradient corporate",
    "PMO": "project management strategy dark professional banner",
    "Strategy": "business strategy leadership dark professional",
    "FinTech": "fintech digital banking dark professional",
    "Leadership": "executive leadership vision dark professional",
}


def apply_text_overlay(image_path, headline, author="Ahmed Nasr",
                       tags="#DigitalTransformation  #GenAI  #PMO"):
    """Apply headline + author + hashtag overlay on an image (for non-PIL sources).
    
    Skips PIL templates since they already have text baked in.
    Saves over the same path.
    """
    from PIL import Image, ImageDraw, ImageFont
    
    TARGET_W, TARGET_H = 1200, 628
    
    # Find bold font
    for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
               "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"]:
        if os.path.exists(fp):
            bold_path = fp
            break
    else:
        bold_path = None
    
    for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
               "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]:
        if os.path.exists(fp):
            reg_path = fp
            break
    else:
        reg_path = bold_path
    
    img = Image.open(image_path).convert("RGBA")
    img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)
    
    # Dark overlay for readability
    overlay = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 140))
    img = Image.alpha_composite(img, overlay)
    
    draw = ImageDraw.Draw(img)
    title_font = ImageFont.truetype(bold_path, 48) if bold_path else ImageFont.load_default()
    author_font = ImageFont.truetype(bold_path, 28) if bold_path else ImageFont.load_default()
    tag_font = ImageFont.truetype(reg_path or bold_path, 20) if (reg_path or bold_path) else ImageFont.load_default()
    
    # Auto-wrap headline to ~30 chars per line
    words = headline.split()
    lines, current = [], ""
    for w in words:
        test = f"{current} {w}".strip()
        if len(test) > 32 and current:
            lines.append(current)
            current = w
        else:
            current = test
    if current:
        lines.append(current)
    if len(lines) > 3:
        lines = lines[:3]
        lines[-1] = lines[-1][:27] + "..."
    
    total_h = sum(draw.textbbox((0, 0), l, font=title_font)[3] - draw.textbbox((0, 0), l, font=title_font)[1] for l in lines) + 15 * (len(lines) - 1)
    y = (TARGET_H - total_h) // 2 - 40
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        tw = bbox[2] - bbox[0]
        x = (TARGET_W - tw) // 2
        draw.text((x + 2, y + 2), line, fill=(0, 0, 0, 200), font=title_font)
        draw.text((x, y), line, fill=(255, 255, 255, 255), font=title_font)
        y += (bbox[3] - bbox[1]) + 15
    
    # Divider
    div_y = y + 20
    draw.line([(TARGET_W // 2 - 100, div_y), (TARGET_W // 2 + 100, div_y)], fill=(100, 180, 255, 200), width=3)
    
    # Author
    bbox = draw.textbbox((0, 0), author, font=author_font)
    ax = (TARGET_W - (bbox[2] - bbox[0])) // 2
    draw.text((ax, div_y + 20), author, fill=(200, 220, 255, 255), font=author_font)
    
    # Tags
    bbox = draw.textbbox((0, 0), tags, font=tag_font)
    tx = (TARGET_W - (bbox[2] - bbox[0])) // 2
    draw.text((tx, TARGET_H - 50), tags, fill=(180, 180, 200, 180), font=tag_font)
    
    final = img.convert("RGB")
    final.save(image_path, "PNG", quality=95)
    return image_path


class ImageGenChain:
    """Multi-fallback image generation with Composio tools."""

    def __init__(self, composio_fn=None):
        """
        Args:
            composio_fn: Function to call Composio tools. Signature: fn(tool_slug, arguments) -> (result, error)
                         If None, outputs parameters for manual execution.
        """
        self.composio_fn = composio_fn
        self.attempts = []

    def generate(self, topic="AI", headline="", aspect_ratio="16:9", output_path=None):
        """Try each source in topic-aware priority order until one succeeds.
        
        Routing:
          AI/Tech topics → Gemini Flash → Gemini Pro → Stock Search → PIL
          Business/PMO   → Stock Search → Gemini Flash → Gemini Pro → PIL
          Default        → Gemini Flash → Stock Search → Gemini Pro → PIL
        
        Returns:
            dict with keys: success, path, source, attempts, s3url (if from Composio)
        """
        if output_path is None:
            now = datetime.now(CAIRO)
            output_path = f"{OUTPUT_DIR}/gen-{now.strftime('%Y-%m-%d-%H%M%S')}.png"

        hint = f"themes of: {headline[:80]}" if headline else f"themes of: {topic}"
        prompt = GEMINI_PROMPTS.get(topic, DEFAULT_PROMPT).format(hint=hint)

        # Build ordered chain based on topic
        # Sources: Gemini (Composio), FLUX/SDXL (HuggingFace), Stock, PIL
        if topic in AI_TECH_TOPICS:
            chain = [
                ("gemini_flash", lambda: self._try_gemini(prompt, "gemini-2.5-flash-image", aspect_ratio, output_path)),
                ("hf_flux", lambda: self._try_huggingface(prompt, "flux-schnell", output_path)),
                ("pinterest_style", lambda: self._try_pinterest_style_transfer(topic, headline, output_path)),
                ("hf_sdxl", lambda: self._try_huggingface(prompt, "sdxl", output_path)),
                ("gemini_pro", lambda: self._try_gemini(prompt, "gemini-3-pro-image-preview", aspect_ratio, output_path)),
                ("stock_search", lambda: self._try_image_search(topic, headline, output_path)),
                ("pil_template", lambda: self._try_pil_template(topic, headline, output_path)),
            ]
            print(f"  📋 Route: AI/Tech → Flash → FLUX → Pinterest-Style → SDXL → Pro → Stock → PIL")
        elif topic in BUSINESS_TOPICS:
            chain = [
                ("pinterest_style", lambda: self._try_pinterest_style_transfer(topic, headline, output_path)),
                ("stock_search", lambda: self._try_image_search(topic, headline, output_path)),
                ("gemini_flash", lambda: self._try_gemini(prompt, "gemini-2.5-flash-image", aspect_ratio, output_path)),
                ("hf_flux", lambda: self._try_huggingface(prompt, "flux-schnell", output_path)),
                ("gemini_pro", lambda: self._try_gemini(prompt, "gemini-3-pro-image-preview", aspect_ratio, output_path)),
                ("hf_sdxl", lambda: self._try_huggingface(prompt, "sdxl", output_path)),
                ("pil_template", lambda: self._try_pil_template(topic, headline, output_path)),
            ]
            print(f"  📋 Route: Business → Pinterest-Style → Stock → Flash → FLUX → Pro → SDXL → PIL")
        else:
            chain = [
                ("gemini_flash", lambda: self._try_gemini(prompt, "gemini-2.5-flash-image", aspect_ratio, output_path)),
                ("pinterest_style", lambda: self._try_pinterest_style_transfer(topic, headline, output_path)),
                ("hf_flux", lambda: self._try_huggingface(prompt, "flux-schnell", output_path)),
                ("stock_search", lambda: self._try_image_search(topic, headline, output_path)),
                ("hf_sdxl", lambda: self._try_huggingface(prompt, "sdxl", output_path)),
                ("gemini_pro", lambda: self._try_gemini(prompt, "gemini-3-pro-image-preview", aspect_ratio, output_path)),
                ("pil_template", lambda: self._try_pil_template(topic, headline, output_path)),
            ]
            print(f"  📋 Route: Default → Flash → Pinterest-Style → FLUX → Stock → SDXL → Pro → PIL")

        for name, try_fn in chain:
            result = try_fn()
            if result["success"]:
                return result

        # ── All failed ──
        return {
            "success": False,
            "path": None,
            "source": "none",
            "attempts": self.attempts,
            "error": "All image generation methods failed",
        }

    def generate_with_overlay(self, topic="AI", headline="", author="Ahmed Nasr",
                              tags="", aspect_ratio="16:9", output_path=None):
        """Generate image then apply headline + author text overlay.
        
        PIL templates already have text, so overlay is skipped for those.
        """
        result = self.generate(topic=topic, headline=headline,
                               aspect_ratio=aspect_ratio, output_path=output_path)
        
        if result["success"] and result.get("source") != "pil_template":
            try:
                overlay_tags = tags or f"#{topic.replace(' ', '')}  #GenAI  #PMO"
                apply_text_overlay(result["path"], headline or topic, author, overlay_tags)
                result["overlay_applied"] = True
                print(f"  🎨 Text overlay applied to {result['source']}")
            except Exception as e:
                result["overlay_applied"] = False
                print(f"  ⚠️ Overlay failed ({e}) — raw image still usable")
        elif result["success"]:
            result["overlay_applied"] = False  # PIL already has text
        
        return result

    def _try_gemini(self, prompt, model, aspect_ratio, output_path):
        """Try Gemini image generation via Composio."""
        source = f"gemini:{model.split('-')[1]}"
        print(f"  🔄 Trying {model}...")

        if not self.composio_fn:
            self.attempts.append({"source": source, "status": "skipped", "reason": "no composio_fn"})
            return {"success": False}

        try:
            args = {"prompt": prompt, "model": model, "aspect_ratio": aspect_ratio}
            # gemini-2.0-flash-exp doesn't support aspect_ratio
            if "2.0-flash-exp" in model:
                del args["aspect_ratio"]

            result, error = self.composio_fn("GEMINI_GENERATE_IMAGE", args)

            if error:
                self.attempts.append({"source": source, "status": "error", "reason": str(error)[:200]})
                print(f"  ❌ {source}: {str(error)[:100]}")
                return {"success": False}

            # Extract S3 URL
            data = (result or {}).get("data", {})
            s3url = None
            img = data.get("image", {})
            if isinstance(img, dict):
                s3url = img.get("s3url")
            if not s3url:
                for item in data.get("content", []) or []:
                    if isinstance(item, dict):
                        t = item.get("text", "")
                        if isinstance(t, str) and t.startswith("http"):
                            s3url = t
                            break

            if not s3url:
                self.attempts.append({"source": source, "status": "no_url", "reason": "No s3url in response"})
                print(f"  ❌ {source}: No image URL returned")
                return {"success": False}

            # Download
            img_data = self._download(s3url)
            if img_data:
                with open(output_path, "wb") as f:
                    f.write(img_data)
                self.attempts.append({"source": source, "status": "success", "size_kb": len(img_data) // 1024})
                print(f"  ✅ {source}: {len(img_data) // 1024}KB -> {output_path}")
                return {
                    "success": True,
                    "path": output_path,
                    "source": source,
                    "s3url": s3url,
                    "size_kb": len(img_data) // 1024,
                    "attempts": self.attempts,
                }
            else:
                self.attempts.append({"source": source, "status": "download_failed"})
                return {"success": False}

        except Exception as e:
            self.attempts.append({"source": source, "status": "exception", "reason": str(e)[:200]})
            print(f"  ❌ {source}: {e}")
            return {"success": False}

    def _try_huggingface(self, prompt, model_key, output_path):
        """Try HuggingFace Inference API for image generation.
        
        model_key: 'flux-schnell' or 'sdxl'
        """
        model_map = {
            "flux-schnell": "black-forest-labs/FLUX.1-schnell",
            "sdxl": "stabilityai/stable-diffusion-xl-base-1.0",
        }
        model_id = model_map.get(model_key, model_key)
        source = f"huggingface:{model_key}"
        print(f"  🔄 Trying HuggingFace {model_key}...")

        try:
            # Import our HF client
            hf_client_path = f"{WORKSPACE}/scripts/huggingface-client.py"
            if not os.path.exists(hf_client_path):
                self.attempts.append({"source": source, "status": "skipped", "reason": "client not found"})
                return {"success": False}

            import importlib.util
            spec = importlib.util.spec_from_file_location("hf_client", hf_client_path)
            hf = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(hf)

            result = hf.generate_image(prompt, model=model_id, output_path=output_path, timeout=45)

            if result["success"]:
                self.attempts.append({
                    "source": source, "status": "success",
                    "size_kb": result["size_kb"],
                })
                print(f"  ✅ {source}: {output_path} ({result['size_kb']}KB)")
                return {
                    "success": True,
                    "path": output_path,
                    "source": source,
                    "attempts": self.attempts,
                }
            else:
                self.attempts.append({"source": source, "status": "failed", "reason": result.get("error", "")[:200]})
                print(f"  ❌ {source}: {result.get('error', 'unknown')[:80]}")
                return {"success": False}

        except Exception as e:
            self.attempts.append({"source": source, "status": "exception", "reason": str(e)[:200]})
            print(f"  ❌ {source}: {e}")
            return {"success": False}

    def _try_image_search(self, topic, headline, output_path):
        """Try finding a relevant stock image via Composio Image Search."""
        source = "composio_search"
        print(f"  🔄 Trying image search...")

        if not self.composio_fn:
            self.attempts.append({"source": source, "status": "skipped"})
            return {"success": False}

        try:
            query = STOCK_QUERIES.get(topic, f"{topic} professional dark banner corporate")
            if headline:
                query = f"{headline[:40]} professional dark banner"

            result, error = self.composio_fn("COMPOSIO_SEARCH_IMAGE", {"query": query, "num": 5})
            if error:
                self.attempts.append({"source": source, "status": "error", "reason": str(error)[:200]})
                return {"success": False}

            # Extract first usable image URL
            data = (result or {}).get("data", {})
            images = data.get("images_results", data.get("results", []))
            
            for img in images[:5]:
                url = img.get("original") or img.get("thumbnail")
                if not url:
                    continue
                img_data = self._download(url)
                if img_data and len(img_data) > 10000:  # Min 10KB
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    self.attempts.append({"source": source, "status": "success", "url": url[:100]})
                    print(f"  ✅ {source}: Found image {len(img_data) // 1024}KB")
                    return {
                        "success": True,
                        "path": output_path,
                        "source": source,
                        "size_kb": len(img_data) // 1024,
                        "attempts": self.attempts,
                    }

            self.attempts.append({"source": source, "status": "no_results"})
            print(f"  ❌ {source}: No usable images found")
            return {"success": False}

        except Exception as e:
            self.attempts.append({"source": source, "status": "exception", "reason": str(e)[:200]})
            return {"success": False}

    def _try_pinterest_style_transfer(self, topic, headline, output_path):
        """Ruben Hassid's style-transfer workflow:
        1. Find a content infographic from Pinterest (via web search)
        2. Find a 'handwritten style' infographic for visual style reference
        3. Gemini: extract content from #1, remake in style of #2
        
        Produces scrappy, non-branded images that don't look like AI ads.
        """
        source = "pinterest_style_transfer"
        print(f"  🔄 Trying Pinterest style-transfer (Ruben method)...")

        if not self.composio_fn:
            self.attempts.append({"source": source, "status": "skipped", "reason": "no composio_fn"})
            return {"success": False}

        try:
            # Step 1: Search for a content infographic on the topic
            content_query = f"{topic} infographic data visualization site:pinterest.com OR site:i.pinimg.com"
            content_result, err = self.composio_fn("COMPOSIO_SEARCH_IMAGE", {
                "query": f"{topic} graph cheat sheet infographic professional",
                "num": 5
            })
            if err:
                self.attempts.append({"source": source, "status": "error", "reason": f"search failed: {err[:100]}"})
                return {"success": False}

            content_images = (content_result or {}).get("data", {}).get("images_results", [])
            content_url = None
            for img in content_images[:5]:
                url = img.get("original") or img.get("thumbnail")
                if url and ("png" in url.lower() or "jpg" in url.lower() or "jpeg" in url.lower()):
                    content_url = url
                    break
            
            if not content_url and content_images:
                content_url = content_images[0].get("original") or content_images[0].get("thumbnail")

            if not content_url:
                self.attempts.append({"source": source, "status": "no_content_image"})
                return {"success": False}

            # Step 2: Search for handwritten/organic style reference
            style_result, err2 = self.composio_fn("COMPOSIO_SEARCH_IMAGE", {
                "query": "handwritten style infographic organic sketch notes cheat sheet",
                "num": 5
            })
            if err2:
                self.attempts.append({"source": source, "status": "error", "reason": f"style search failed: {err2[:100]}"})
                return {"success": False}

            style_images = (style_result or {}).get("data", {}).get("images_results", [])
            style_url = None
            for img in style_images[:5]:
                url = img.get("original") or img.get("thumbnail")
                if url:
                    style_url = url
                    break

            if not style_url:
                self.attempts.append({"source": source, "status": "no_style_image"})
                return {"success": False}

            # Step 3: Download both images
            content_data = self._download(content_url)
            style_data = self._download(style_url)

            if not content_data or not style_data:
                self.attempts.append({"source": source, "status": "download_failed"})
                return {"success": False}

            # Save temp files
            import tempfile, base64
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as cf:
                cf.write(content_data)
                content_path = cf.name
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as sf:
                sf.write(style_data)
                style_path = sf.name

            # Step 4: Gemini style-transfer via Composio
            # Encode images as base64 for Gemini
            content_b64 = base64.b64encode(content_data).decode()
            style_b64 = base64.b64encode(style_data).decode()

            prompt = (
                f"I'm giving you two images. "
                f"Image 1 (content): Extract all information, data points, labels, and structure from this infographic about {topic}. "
                f"Image 2 (style): This is the visual style I want - handwritten, organic, sketch-like. "
                f"Now create a NEW infographic that: "
                f"1. Contains the key information relevant to: '{headline or topic}' "
                f"2. Uses the handwritten/organic visual style from Image 2 "
                f"3. Looks scrappy and human-made, NOT like a corporate ad "
                f"4. Is optimized for LinkedIn (1080x1350 portrait or 1200x628 landscape) "
                f"5. Has no text overlay needed - the design IS the content "
                f"Make it something a professional would bookmark and share with colleagues."
            )

            result, error = self.composio_fn("GEMINI_GENERATE_IMAGE", {
                "prompt": prompt,
                "model": "gemini-2.5-flash-image",
                "aspect_ratio": "4:5",  # 1080x1350 portrait for LinkedIn
            })

            # Clean up temp files
            import os as _os
            for p in [content_path, style_path]:
                try: _os.unlink(p)
                except: pass

            if error:
                self.attempts.append({"source": source, "status": "gemini_error", "reason": str(error)[:200]})
                print(f"  ❌ {source}: Gemini failed - {str(error)[:80]}")
                return {"success": False}

            # Extract image URL from result
            data = (result or {}).get("data", {})
            s3url = None
            img = data.get("image", {})
            if isinstance(img, dict):
                s3url = img.get("s3url")
            if not s3url:
                for item in data.get("content", []) or []:
                    if isinstance(item, dict):
                        t = item.get("text", "")
                        if isinstance(t, str) and t.startswith("http"):
                            s3url = t
                            break

            if not s3url:
                self.attempts.append({"source": source, "status": "no_url"})
                return {"success": False}

            img_bytes = self._download(s3url)
            if img_bytes:
                with open(output_path, "wb") as f:
                    f.write(img_bytes)
                self.attempts.append({"source": source, "status": "success", "size_kb": len(img_bytes) // 1024})
                print(f"  ✅ {source}: Style-transfer complete {len(img_bytes) // 1024}KB -> {output_path}")
                return {
                    "success": True,
                    "path": output_path,
                    "source": source,
                    "s3url": s3url,
                    "size_kb": len(img_bytes) // 1024,
                    "attempts": self.attempts,
                }

            self.attempts.append({"source": source, "status": "download_failed"})
            return {"success": False}

        except Exception as e:
            self.attempts.append({"source": source, "status": "exception", "reason": str(e)[:200]})
            print(f"  ❌ {source}: {e}")
            return {"success": False}

    def _try_pil_template(self, topic, headline, output_path):
        """Generate a PIL branded template (always works locally)."""
        source = "pil_template"
        print(f"  🔄 Trying PIL branded template...")

        try:
            import importlib.util
            vspec = importlib.util.spec_from_file_location(
                "visuals", f"{WORKSPACE}/scripts/content-factory-visuals.py")
            visuals = importlib.util.module_from_spec(vspec)
            vspec.loader.exec_module(visuals)

            # Detect format
            import re
            combined = f"{topic} {headline}".lower()
            hot_take_signals = ["don't", "won't", "stop", "wrong", "myth", "unpopular"]
            brands = ["google", "microsoft", "openai", "salesforce", "amazon", "meta"]

            if sum(1 for s in hot_take_signals if s in combined) >= 2:
                post_format = "Hot Take"
            elif any(b in combined for b in brands):
                post_format = "Brandjacking"
            else:
                post_format = "Newsjacking"

            if len(headline) > 100:
                headline = headline[:97] + "..."

            visual_path = visuals.generate_visual(
                headline or topic, post_format, topic, "Ahmed Nasr",
                output_path
            )
            
            size = os.path.getsize(visual_path) // 1024
            self.attempts.append({"source": source, "status": "success", "size_kb": size})
            print(f"  ✅ {source}: {post_format}/{topic} -> {visual_path} ({size}KB)")
            return {
                "success": True,
                "path": visual_path,
                "source": source,
                "size_kb": size,
                "attempts": self.attempts,
            }

        except Exception as e:
            self.attempts.append({"source": source, "status": "exception", "reason": str(e)[:200]})
            print(f"  ❌ {source}: {e}")
            return {"success": False}

    def _download(self, url, timeout=30):
        """Download from URL, return bytes or None."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
                return r.read()
        except Exception:
            return None


# ── Notion Integration ───────────────────────────────────────────────────────
def get_notion_post_info(page_id):
    """Pull title and content from Notion page for prompt generation."""
    token = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
    
    url = f"https://api.notion.com/v1/pages/{page_id}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"
    })
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        page = json.loads(r.read())
    
    props = page.get("properties", {})
    title = ""
    for key in ["Title", "Name", "title"]:
        if key in props:
            title = "".join(t.get("plain_text", "") for t in props[key].get("title", []))
            break
    
    topic_prop = props.get("Topic", {}).get("select", {})
    topic = topic_prop.get("name", "AI") if topic_prop else "AI"
    
    return title, topic


# ── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Multi-fallback image generation chain")
    parser.add_argument("--topic", default="AI", help="Post topic (AI, Healthcare, PMO, etc.)")
    parser.add_argument("--headline", default="", help="Post headline for prompt")
    parser.add_argument("--notion-page", help="Notion page ID to auto-detect topic/headline")
    parser.add_argument("--aspect", default="16:9", help="Aspect ratio")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--pil-only", action="store_true", help="Skip Composio, use PIL only")
    args = parser.parse_args()

    if args.notion_page:
        title, topic = get_notion_post_info(args.notion_page)
        args.headline = title
        args.topic = topic
        print(f"📄 From Notion: '{title}' / topic={topic}")

    chain = ImageGenChain(composio_fn=None)  # CLI mode = no Composio (params only)
    
    if args.pil_only:
        result = chain._try_pil_template(args.topic, args.headline, 
                                          args.output or f"{OUTPUT_DIR}/pil-{datetime.now(CAIRO).strftime('%Y-%m-%d-%H%M%S')}.png")
    else:
        result = chain.generate(
            topic=args.topic,
            headline=args.headline,
            aspect_ratio=args.aspect,
            output_path=args.output,
        )

    print(f"\n{'✅' if result['success'] else '❌'} Result: source={result.get('source')}, "
          f"path={result.get('path')}, size={result.get('size_kb', 0)}KB")
    print(f"Attempts: {json.dumps(result.get('attempts', []), indent=2)}")


if __name__ == "__main__":
    main()
