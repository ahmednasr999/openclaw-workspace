#!/usr/bin/env python3
"""
ScrapeCreators API Client
Lightweight wrapper for social media scraping.
Docs: https://docs.scrapecreators.com

Setup:
  1. Sign up at https://scrapecreators.com (100 free credits, no card)
  2. Get your API key from the dashboard
  3. Save it: echo 'SCRAPECREATORS_API_KEY=your-key' >> ~/.env
"""

import os
import json
import sys
import requests

API_BASE = "https://api.scrapecreators.com/v1"

def get_api_key():
    """Load API key from env or .env file."""
    key = os.environ.get("SCRAPECREATORS_API_KEY")
    if key:
        return key
    env_file = os.path.expanduser("~/.env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if line.startswith("SCRAPECREATORS_API_KEY="):
                    return line.strip().split("=", 1)[1].strip('"').strip("'")
    raise ValueError("SCRAPECREATORS_API_KEY not found. Set it in ~/.env or environment.")

def call(endpoint, params=None):
    """Generic API call. Returns parsed JSON."""
    api_key = get_api_key()
    headers = {"x-api-key": api_key}
    url = f"{API_BASE}/{endpoint}"
    resp = requests.get(url, headers=headers, params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()

# --- YouTube ---

def youtube_transcript(video_id_or_url):
    """Get YouTube video transcript. 1 credit. NOTE: Endpoint may be unstable."""
    return call("youtube/transcript", {"url": video_id_or_url})

def youtube_video_details(video_id_or_url):
    """Get YouTube video details. 1 credit."""
    return call("youtube/video", {"url": video_id_or_url})

def youtube_search(query, num_results=10):
    """Search YouTube. 1 credit."""
    return call("youtube/search", {"query": query, "numResults": num_results})

def youtube_channel_videos(channel_id, num_results=10):
    """Get channel videos. 1 credit."""
    return call("youtube/channelVideos", {"channelId": channel_id, "numResults": num_results})

# --- Twitter/X ---

def twitter_tweet(url_or_id):
    """Get tweet details. 1 credit. Pass full URL or tweet ID."""
    if url_or_id.startswith("http"):
        return call("twitter/tweet", {"url": url_or_id})
    return call("twitter/tweet", {"url": f"https://x.com/i/status/{url_or_id}"})

def twitter_transcript(tweet_id):
    """Get transcript from a Twitter video. 1 credit."""
    return call("twitter/transcript", {"tweetId": tweet_id})

def twitter_profile(username):
    """Get Twitter profile. 1 credit."""
    return call("twitter/profile", {"handle": username})

def twitter_user_tweets(user_id, num_results=10):
    """Get user tweets. 1 credit."""
    return call("twitter/userTweets", {"userId": user_id, "numResults": num_results})

# --- LinkedIn ---

def linkedin_profile(url):
    """Get LinkedIn profile. 1 credit."""
    return call("linkedin/profile", {"url": url})

def linkedin_company(url):
    """Get LinkedIn company page. 1 credit."""
    return call("linkedin/companyPage", {"url": url})

def linkedin_company_posts(url, num_results=10):
    """Get company posts. 1 credit."""
    return call("linkedin/companyPosts", {"url": url, "numResults": num_results})

def linkedin_post(url):
    """Get LinkedIn post details. 1 credit."""
    return call("linkedin/post", {"url": url})

# --- Instagram ---

def instagram_profile(username):
    """Get Instagram profile. 1 credit."""
    return call("instagram/profile", {"handle": username})

def instagram_transcript(url):
    """Get transcript from Instagram reel/video. 1 credit."""
    return call("instagram/transcript", {"url": url})

# --- TikTok ---

def tiktok_profile(username):
    """Get TikTok profile. 1 credit."""
    return call("tiktok/profile", {"handle": username})

def tiktok_transcript(url):
    """Get TikTok video transcript. 1 credit."""
    return call("tiktok/transcript", {"url": url})

# --- Reddit ---

def reddit_search(query, num_results=10):
    """Search Reddit. 1 credit."""
    return call("reddit/search", {"query": query, "numResults": num_results})

def reddit_post_comments(url, num_results=20):
    """Get post comments. 1 credit."""
    return call("reddit/postComments", {"url": url, "numResults": num_results})

# --- Facebook ---

def facebook_transcript(url):
    """Get Facebook video transcript. 1 credit."""
    return call("facebook/transcript", {"url": url})

# --- CLI ---

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: scrapecreators.py <platform> <action> [args...]")
        print()
        print("Examples:")
        print("  scrapecreators.py youtube transcript dQw4w9WgXcQ")
        print("  scrapecreators.py twitter tweet 2034672484059095263")
        print("  scrapecreators.py linkedin profile https://linkedin.com/in/someone")
        print("  scrapecreators.py tiktok transcript https://tiktok.com/@user/video/123")
        sys.exit(1)

    platform = sys.argv[1].lower()
    action = sys.argv[2].lower()
    args = sys.argv[3:]

    funcs = {
        ("youtube", "transcript"): lambda: youtube_transcript(args[0]),
        ("youtube", "video"): lambda: youtube_video_details(args[0]),
        ("youtube", "search"): lambda: youtube_search(" ".join(args)),
        ("twitter", "tweet"): lambda: twitter_tweet(args[0]),
        ("twitter", "transcript"): lambda: twitter_transcript(args[0]),
        ("twitter", "profile"): lambda: twitter_profile(args[0]),
        ("linkedin", "profile"): lambda: linkedin_profile(args[0]),
        ("linkedin", "company"): lambda: linkedin_company(args[0]),
        ("linkedin", "post"): lambda: linkedin_post(args[0]),
        ("instagram", "profile"): lambda: instagram_profile(args[0]),
        ("instagram", "transcript"): lambda: instagram_transcript(args[0]),
        ("tiktok", "profile"): lambda: tiktok_profile(args[0]),
        ("tiktok", "transcript"): lambda: tiktok_transcript(args[0]),
        ("reddit", "search"): lambda: reddit_search(" ".join(args)),
        ("facebook", "transcript"): lambda: facebook_transcript(args[0]),
    }

    key = (platform, action)
    if key not in funcs:
        print(f"Unknown command: {platform} {action}")
        sys.exit(1)

    result = funcs[key]()
    print(json.dumps(result, indent=2, ensure_ascii=False))
