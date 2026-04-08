#!/usr/bin/env python3
"""
X/Tweet Reader via oEmbed API
Reads public tweet content without any auth.
Usage: python3 x-tweet-reader.py <tweet-url>
       python3 x-tweet-reader.py https://x.com/user/status/123456789
"""

import sys
import json
import urllib.request
import urllib.parse
import re


def extract_tweet_info(oembed_data):
    """Parse oEmbed response into clean structured data."""
    return {
        "author_name": oembed_data.get("author_name", ""),
        "author_url": oembed_data.get("author_url", ""),
        "html": oembed_data.get("html", ""),
        "url": oembed_data.get("url", ""),
        "provider": oembed_data.get("provider_name", ""),
        # Extract plain text from the HTML blockquote
        "text": re.sub(r"<[^>]+>", "", oembed_data.get("html", "")).strip(),
        # Extract date if present (April 1, 2026 style)
        "date": re.search(r'[A-Z][a-z]+ \d+, \d{4}', oembed_data.get("html", "") or "").group(0) if re.search(r'[A-Z][a-z]+ \d+, \d{4}', oembed_data.get("html", "") or "") else "",
    }


def read_tweet(tweet_url, dnt="true"):
    """
    Read a public tweet via Twitter's oEmbed API.
    
    Args:
        tweet_url: Full URL to the tweet (https://x.com/user/status/ID or https://twitter.com/user/status/ID)
        dnt: Do Not Track (prevents tracking)
    
    Returns:
        dict with author_name, author_url, text, date, raw oEmbed
    """
    # Normalize URL (x.com or twitter.com both work)
    encoded_url = urllib.parse.quote(tweet_url, safe="")
    api_url = f"https://publish.twitter.com/oembed?url={encoded_url}&dnt={dnt}"
    
    req = urllib.request.Request(
        api_url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; OpenClaw/1.0; +https://openclaw.ai)",
            "Accept": "application/json",
        }
    )
    
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    
    return extract_tweet_info(data)


def main():
    if len(sys.argv) < 2:
        print("Usage: x-tweet-reader.py <tweet-url>")
        print("Example: x-tweet-reader.py https://x.com/saboo_shubham_/status/2039413107400089964")
        sys.exit(1)
    
    tweet_url = sys.argv[1]
    
    # Fix URL if user passed twitter.com instead of x.com
    tweet_url = tweet_url.replace("twitter.com", "x.com")
    
    try:
        info = read_tweet(tweet_url)
        print(f"Author: {info['author_name']} ({info['author_url']})")
        if info['date']:
            print(f"Date: {info['date']}")
        print(f"\nTweet text:\n{info['text']}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
