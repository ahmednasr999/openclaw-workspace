#!/usr/bin/env python3
"""
LinkedIn Post with Image via Composio API.
Handles the full flow: register upload -> upload bytes -> create post with image.

Usage (from cron/agent):
  python3 linkedin-composio-post.py --text "Post text" --image-url "https://..." [--dry-run]
  python3 linkedin-composio-post.py --text "Post text" --image-file /path/to/image.png [--dry-run]

Output: JSON with post_url on success, error on failure.
"""
import argparse
import json
import os
import sys
import subprocess
import requests
import time

PERSON_URN = "urn:li:person:mm8EyA56mj"
WORKSPACE = os.environ.get("WORKSPACE", "/root/.openclaw/workspace")


def composio_tool(tool_slug, arguments):
    """Execute a Composio tool via the CLI helper."""
    # Use the run_composio_tool pattern from the workbench
    cmd = [
        "python3", "-c",
        f"""
import json, os, sys
sys.path.insert(0, '/home/user')
# Direct API call to Composio
import requests as req

# Read session info
COMPOSIO_API_KEY = os.environ.get('COMPOSIO_API_KEY', '')
COMPOSIO_BASE_URL = os.environ.get('COMPOSIO_BASE_URL', 'https://backend.composio.dev')

# This is a placeholder - the actual posting should go through the agent
print(json.dumps({{"error": "Use agent for Composio calls"}}))
"""
    ]
    # For now, return None - this script is meant to be called by the agent
    return None


def download_image(url=None, filepath=None):
    """Download image from URL or read from local file."""
    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            data = f.read()
        import mimetypes
        ct = mimetypes.guess_type(filepath)[0] or "image/png"
        return data, ct
    
    if url:
        # Try local file first (GitHub raw URLs may be in repo)
        if "raw.githubusercontent.com" in url:
            # Map to local workspace path
            parts = url.split("/master/")
            if len(parts) == 2:
                local_path = os.path.join(WORKSPACE, parts[1])
                if os.path.exists(local_path):
                    print(f"Using local file: {local_path}")
                    with open(local_path, 'rb') as f:
                        data = f.read()
                    ct = "image/png" if local_path.endswith(".png") else "image/jpeg"
                    return data, ct
        
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        ct = r.headers.get("Content-Type", "image/png")
        return r.content, ct
    
    raise ValueError("No image URL or file path provided")


def main():
    parser = argparse.ArgumentParser(description="LinkedIn Post with Image via Composio")
    parser.add_argument("--text", required=True, help="Post text content")
    parser.add_argument("--image-url", help="Image URL to download and attach")
    parser.add_argument("--image-file", help="Local image file path")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually post")
    parser.add_argument("--output", default="/tmp/linkedin-composio-result.json", help="Output JSON path")
    args = parser.parse_args()

    print(f"=== LinkedIn Composio Post ===")
    print(f"Text length: {len(args.text)} chars")
    print(f"Image URL: {args.image_url or 'none'}")
    print(f"Image file: {args.image_file or 'none'}")
    
    has_image = bool(args.image_url or args.image_file)
    
    if has_image:
        try:
            image_bytes, content_type = download_image(url=args.image_url, filepath=args.image_file)
            print(f"Image ready: {len(image_bytes)} bytes, type: {content_type}")
        except Exception as e:
            # NEVER post without image if image was expected
            result = {"success": False, "error": f"Image download failed: {e}", "action": "IMAGE_HOLD"}
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"IMAGE_HOLD: {e}")
            sys.exit(1)
        
        # Save image for agent to upload
        ext = "png" if "png" in content_type else "jpg"
        tmp_path = f"/tmp/linkedin-post-image.{ext}"
        with open(tmp_path, 'wb') as f:
            f.write(image_bytes)
        print(f"Image saved: {tmp_path}")
    
    if args.dry_run:
        print("[DRY RUN] Would post to LinkedIn")
        result = {"success": True, "dry_run": True, "text_length": len(args.text), "has_image": has_image}
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        return
    
    # The actual Composio API calls must go through the agent (COMPOSIO_MULTI_EXECUTE_TOOL)
    # This script prepares the payload and the agent handles execution
    payload = {
        "action": "post_to_linkedin_with_image",
        "person_urn": PERSON_URN,
        "text": args.text,
        "has_image": has_image,
        "image_path": f"/tmp/linkedin-post-image.{ext}" if has_image else None,
        "image_content_type": content_type if has_image else None,
        "steps": [
            "1. Call LINKEDIN_REGISTER_IMAGE_UPLOAD with owner_urn",
            "2. PUT image bytes to returned upload_url",
            "3. Call LINKEDIN_CREATE_LINKED_IN_POST with asset_urn in images[]",
        ] if has_image else [
            "1. Call LINKEDIN_CREATE_LINKED_IN_POST with text only"
        ]
    }
    
    with open(args.output, 'w') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    
    print(f"Payload ready at: {args.output}")
    print("READY_FOR_AGENT")


if __name__ == "__main__":
    main()
