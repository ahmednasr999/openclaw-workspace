#!/usr/bin/env python3
"""
Direct LinkedIn posting via Voyager API - bypasses Composio truncation bug.
Uses Camofox browser cookies (cli-default profile).

Usage:
  python3 linkedin-direct-post.py --text "Post content here"
  python3 linkedin-direct-post.py --text-file /path/to/post.txt
  python3 linkedin-direct-post.py --text "Post" --image /path/to/image.png
  python3 linkedin-direct-post.py --dry-run --text "Test"
"""
import argparse
import json
import os
import sqlite3
import sys
import requests
import time
import base64
import mimetypes

CAMOFOX_COOKIES_DB = os.path.expanduser("~/.camofox/profiles/cli-default/cookies.sqlite")
CAMOFOX_COOKIES_DB_MAIN = os.path.expanduser("~/.camofox/profiles/main/cookies.sqlite")
LINKEDIN_COOKIES_FILE = os.path.expanduser("~/.openclaw/cookies/linkedin.txt")

def get_cookies_from_camofox():
    """Extract li_at and JSESSIONID from Camofox browser cookies."""
    for db_path in [CAMOFOX_COOKIES_DB, CAMOFOX_COOKIES_DB_MAIN]:
        try:
            db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cur = db.execute(
                "SELECT name, value, host FROM moz_cookies WHERE host LIKE '%linkedin%' AND name IN ('li_at', 'JSESSIONID')"
            )
            cookies = {}
            for name, value, host in cur.fetchall():
                if 'www.linkedin.com' in host:
                    cookies[name] = value.strip('"')
            db.close()
            if 'li_at' in cookies and 'JSESSIONID' in cookies:
                return cookies
        except Exception as e:
            continue
    return None

def get_cookies_from_file():
    """Fallback: extract from Netscape cookie file."""
    if not os.path.exists(LINKEDIN_COOKIES_FILE):
        return None
    cookies = {}
    with open(LINKEDIN_COOKIES_FILE) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 7 and parts[5] in ('li_at', 'JSESSIONID'):
                cookies[parts[5]] = parts[6].strip('"')
    if 'li_at' in cookies and 'JSESSIONID' in cookies:
        return cookies
    return None

def get_cookies():
    """Try Camofox first, then fall back to cookie file."""
    cookies = get_cookies_from_camofox()
    if cookies:
        print(f"[OK] Using Camofox browser cookies (li_at: {cookies['li_at'][:20]}...)")
        return cookies
    cookies = get_cookies_from_file()
    if cookies:
        print(f"[OK] Using cookie file (li_at: {cookies['li_at'][:20]}...)")
        return cookies
    print("[FAIL] No valid LinkedIn cookies found. Log in via Camofox browser first.")
    sys.exit(1)

def get_profile_urn(session):
    """Get the authenticated user's profile URN."""
    resp = session.get("https://www.linkedin.com/voyager/api/me")
    if resp.status_code == 200:
        data = resp.json()
        member_id = data.get("miniProfile", {}).get("entityUrn", "").split(":")[-1]
        if not member_id:
            member_id = data.get("plainId")
        if member_id:
            return f"urn:li:member:{member_id}", data
    # Alternative endpoint
    resp2 = session.get("https://www.linkedin.com/voyager/api/identity/profiles/me")
    if resp2.status_code == 200:
        data2 = resp2.json()
        public_id = data2.get("publicIdentifier", "")
        member_id = data2.get("entityUrn", "").split(":")[-1]
        return f"urn:li:member:{member_id}", data2
    return None, None

def upload_image(session, image_path, author_urn):
    """Upload image to LinkedIn and return the media URN."""
    mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
    
    # Step 1: Register upload
    register_payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": author_urn,
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }
    resp = session.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        json=register_payload,
        headers={"Authorization": f"Bearer {session.cookies.get('li_at', '')}"}
    )
    
    # Try Voyager alternative if v2 fails
    if resp.status_code != 200:
        # Use Voyager image upload
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Register via Voyager
        register_resp = session.post(
            "https://www.linkedin.com/voyager/api/voyagerMediaUploadMetadata?action=upload",
            json={
                "mediaUploadType": "IMAGE_SHARING",
                "fileSize": len(image_data),
                "filename": os.path.basename(image_path)
            }
        )
        if register_resp.status_code != 200:
            print(f"[FAIL] Image register failed: {register_resp.status_code}")
            print(register_resp.text[:500])
            return None
        
        upload_data = register_resp.json().get("data", register_resp.json())
        upload_url = upload_data.get("value", {}).get("singleUploadUrl") or upload_data.get("singleUploadUrl")
        media_urn = upload_data.get("value", {}).get("urn") or upload_data.get("urn")
        
        if not upload_url:
            print(f"[FAIL] No upload URL in response")
            return None
        
        # Upload the image
        upload_resp = session.put(
            upload_url,
            data=image_data,
            headers={"Content-Type": mime_type}
        )
        if upload_resp.status_code in (200, 201):
            print(f"[OK] Image uploaded: {media_urn}")
            return media_urn
        else:
            print(f"[FAIL] Image upload failed: {upload_resp.status_code}")
            return None
    
    upload_data = resp.json()
    upload_url = upload_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    media_urn = upload_data["value"]["asset"]
    
    with open(image_path, 'rb') as f:
        upload_resp = session.put(upload_url, data=f.read(), headers={"Content-Type": mime_type})
    
    if upload_resp.status_code in (200, 201):
        print(f"[OK] Image uploaded: {media_urn}")
        return media_urn
    else:
        print(f"[FAIL] Image upload: {upload_resp.status_code}")
        return None

def create_post(session, text, image_urn=None):
    """Create a LinkedIn post via Voyager API."""
    
    payload = {
        "visibilityV2": {"visibility": "PUBLIC"},
        "commentary": text,
        "origin": "FEED_CREATION",
        "allowedCommentersScope": "ALL"
    }
    
    if image_urn:
        payload["media"] = {
            "id": image_urn,
            "title": {"text": ""},
            "altText": {"text": ""}
        }
    
    resp = session.post(
        "https://www.linkedin.com/voyager/api/contentcreation/normalizedPosts",
        json=payload
    )
    
    if resp.status_code in (200, 201):
        result = resp.json() if resp.text else {}
        print(f"[OK] Post created successfully!")
        # Try to extract post URN
        post_id = resp.headers.get("x-restli-id", "")
        if post_id:
            print(f"[OK] Post URN: {post_id}")
        return True, post_id or result
    else:
        print(f"[FAIL] Post creation failed: {resp.status_code}")
        print(resp.text[:1000])
        return False, resp.text

def main():
    parser = argparse.ArgumentParser(description="Direct LinkedIn posting via Voyager API")
    parser.add_argument("--text", help="Post text content")
    parser.add_argument("--text-file", help="Read post text from file")
    parser.add_argument("--image", help="Path to image file to attach")
    parser.add_argument("--dry-run", action="store_true", help="Validate without posting")
    args = parser.parse_args()
    
    # Get text
    text = args.text
    if args.text_file:
        with open(args.text_file) as f:
            text = f.read().strip()
    
    if not text:
        print("[FAIL] No text provided. Use --text or --text-file")
        sys.exit(1)
    
    print(f"[INFO] Post length: {len(text)} chars / {len(text.encode('utf-8'))} bytes")
    if len(text) > 3000:
        print(f"[WARN] Text exceeds 3000 char limit ({len(text)}). LinkedIn will reject.")
    
    if args.dry_run:
        print("[DRY RUN] Would post:")
        print(text[:200] + "..." if len(text) > 200 else text)
        if args.image:
            print(f"[DRY RUN] With image: {args.image}")
        return
    
    # Get cookies
    cookies = get_cookies()
    
    # Build session
    session = requests.Session()
    csrf_token = cookies['JSESSIONID']
    session.cookies.set("li_at", cookies['li_at'], domain=".www.linkedin.com")
    session.cookies.set("JSESSIONID", f'"{csrf_token}"', domain=".www.linkedin.com")
    session.headers.update({
        "csrf-token": csrf_token,
        "x-restli-protocol-version": "2.0.0",
        "accept": "application/vnd.linkedin.normalized+json+2.1",
        "x-li-lang": "en_US",
        "x-li-track": '{"clientVersion":"1.13.8878","mpVersion":"1.13.8878","osName":"web","timezoneOffset":2,"timezone":"Africa/Cairo","deviceFormFactor":"DESKTOP","mpName":"voyager-web"}',
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0"
    })
    
    # Test auth
    print("[INFO] Testing authentication...")
    test = session.get("https://www.linkedin.com/voyager/api/me")
    if test.status_code != 200:
        print(f"[FAIL] Auth failed (HTTP {test.status_code}). Cookies may be expired.")
        print("[INFO] Log in to LinkedIn via Camofox browser to refresh cookies.")
        sys.exit(1)
    
    profile = test.json()
    name = f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip()
    print(f"[OK] Authenticated as: {name}")
    
    # Upload image if provided
    image_urn = None
    if args.image:
        if not os.path.exists(args.image):
            print(f"[FAIL] Image not found: {args.image}")
            sys.exit(1)
        print(f"[INFO] Uploading image: {args.image}")
        urn = profile.get("miniProfile", {}).get("entityUrn", "").replace("urn:li:fs_miniProfile:", "urn:li:member:")
        image_urn = upload_image(session, args.image, urn or "urn:li:member:mm8EyA56mj")
        if not image_urn:
            print("[WARN] Image upload failed. Posting text-only.")
    
    # Create post
    print(f"[INFO] Creating post ({len(text)} chars)...")
    success, result = create_post(session, text, image_urn)
    
    if success:
        print("[DONE] Post is live on LinkedIn!")
    else:
        print("[FAIL] Post creation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
