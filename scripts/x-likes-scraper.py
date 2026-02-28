#!/usr/bin/env python3
"""
X/Twitter Likes Scraper
Uses session cookies from Chrome browser relay to fetch Ahmed's liked tweets.
Output: memory/x-likes.md
"""

import json
import re
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# Session cookies from Chrome browser relay (extracted Feb 28, 2026)
COOKIES = {
    "guest_id": "v1%3A177225248325700526",
    "ct0": "62bc5ed98a09bf15e3b114155f74a1415619f9b782286c64a4438ceacbfa0ddd5667d771c0934b030f6221160d191b3d29f0745503025245c0c2641076b50707294895b274f805138957641684f11110",
    "twid": "u%3D220061234",
    "lang": "en",
    "personalization_id": "\"v1_Q0q5QKZDJt3MQpjF3iib1w==\"",
}

# Build cookie header
COOKIE_HEADER = "; ".join([f"{k}={v}" for k, v in COOKIES.items()])

# X GraphQL endpoint for likes
USER_ID = "220061234"  # extracted from twid cookie

HEADERS = {
    "authority": "x.com",
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
    "content-type": "application/json",
    "cookie": COOKIE_HEADER,
    "referer": "https://x.com/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "x-csrf-token": "62bc5ed98a09bf15e3b114155f74a1415619f9b782286c64a4438ceacbfa0ddd5667d771c0934b030f6221160d191b3d29f0745503025245c0c2641076b50707294895b274f805138957641684f11110",
    "x-twitter-active-user": "yes",
    "x-twitter-auth-type": "OAuth2Session",
    "x-twitter-client-language": "en",
}

def fetch_likes():
    variables = {
        "userId": USER_ID,
        "count": 20,
        "includePromotedContent": False,
        "withSuperFollowsUserFields": True,
        "withDownvotePerspective": False,
        "withReactionsMetadata": False,
        "withReactionsPerspective": False,
        "withSuperFollowsTweetFields": True,
        "withClientEventToken": False,
        "withBirdwatchNotes": False,
        "withVoice": True,
        "withV2Timeline": True,
    }
    features = {
        "responsive_web_graphql_exclude_directive_enabled": True,
        "verified_phone_label_enabled": False,
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "tweetypie_unmention_optimization_enabled": True,
        "responsive_web_edit_tweet_api_enabled": True,
        "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
        "view_counts_everywhere_api_enabled": True,
        "longform_notetweets_consumption_enabled": True,
        "tweet_awards_web_tipping_enabled": False,
        "freedom_of_speech_not_reach_fetch_enabled": True,
        "standardized_nudges_misinfo": True,
        "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": False,
        "longform_notetweets_rich_text_read_enabled": True,
        "longform_notetweets_inline_media_enabled": False,
        "responsive_web_enhance_cards_enabled": False,
    }

    params = urllib.parse.urlencode({
        "variables": json.dumps(variables),
        "features": json.dumps(features),
    })

    url = f"https://x.com/i/api/graphql/QK8AVO3RpcnbLPKXLAiVog/Likes?{params}"

    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data
    except urllib.error.HTTPError as e:
        return {"error": str(e), "code": e.code}
    except Exception as e:
        return {"error": str(e)}

def extract_tweets(data):
    tweets = []
    try:
        entries = data["data"]["user"]["result"]["timeline_v2"]["timeline"]["instructions"]
        for instruction in entries:
            if instruction.get("type") == "TimelineAddEntries":
                for entry in instruction.get("entries", []):
                    try:
                        tweet_result = entry["content"]["itemContent"]["tweet_results"]["result"]
                        legacy = tweet_result.get("legacy", {})
                        user = tweet_result.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {})
                        tweets.append({
                            "text": legacy.get("full_text", ""),
                            "author": user.get("name", ""),
                            "username": user.get("screen_name", ""),
                            "created_at": legacy.get("created_at", ""),
                            "likes": legacy.get("favorite_count", 0),
                            "retweets": legacy.get("retweet_count", 0),
                        })
                    except (KeyError, TypeError):
                        continue
    except (KeyError, TypeError):
        pass
    return tweets

def save_to_memory(tweets):
    output_path = "/root/.openclaw/workspace/memory/x-likes.md"
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    lines = [
        f"# X Likes — Ahmed Nasr (@AhmedNasr999)",
        f"*Last updated: {now}*",
        f"*{len(tweets)} tweets fetched*",
        "",
        "---",
        "",
    ]
    
    for i, t in enumerate(tweets, 1):
        lines.append(f"## {i}. @{t['username']} ({t['author']})")
        lines.append(f"*{t['created_at']}*")
        lines.append("")
        lines.append(t['text'])
        lines.append("")
        lines.append(f"❤️ {t['likes']} | 🔄 {t['retweets']}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    
    return output_path

if __name__ == "__main__":
    print("Fetching X likes...")
    data = fetch_likes()
    
    if "error" in data:
        print(f"Error: {data}")
    else:
        tweets = extract_tweets(data)
        if tweets:
            path = save_to_memory(tweets)
            print(f"✅ Saved {len(tweets)} liked tweets to {path}")
            for t in tweets[:3]:
                print(f"  - @{t['username']}: {t['text'][:80]}...")
        else:
            print("No tweets extracted. Raw response:")
            print(json.dumps(data, indent=2)[:1000])
