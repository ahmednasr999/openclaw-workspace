#!/usr/bin/env python3
"""
LinkedIn Cookie Setup
Saves a single li_at cookie value into the cookies file.
Usage: python3 linkedin-cookie-setup.py <li_at_value>
"""

import sys
import json
from pathlib import Path

COOKIES_FILE = Path(__file__).parent.parent / "config" / "linkedin-cookies.json"

def setup_cookie(li_at_value: str):
    cookies = [
        {
            "name": "li_at",
            "value": li_at_value,
            "domain": ".linkedin.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
            "sameSite": "None"
        }
    ]
    COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(COOKIES_FILE, "w") as f:
        json.dump(cookies, f, indent=2)
    print(f"Cookie saved to {COOKIES_FILE}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 linkedin-cookie-setup.py <li_at_value>")
        sys.exit(1)
    setup_cookie(sys.argv[1])
