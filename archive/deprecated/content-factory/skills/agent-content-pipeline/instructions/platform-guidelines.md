# Platform Guidelines

## LinkedIn

- Professional but human
- Idiomatic language (Dutch for NL audiences, don't be stiff)
- 1-3 paragraphs ideal
- End with question or CTA
- 3-5 hashtags at end

## X (Twitter)

- 280 chars per tweet (unless paid account)
- Punchy, direct
- 1-2 hashtags max
- Use threads sparingly
- If Firefox auth fails, you can paste `auth_token` and `ct0` manually

### Manual Cookie Steps for X

1. Open x.com and log in
2. Open DevTools → Application/Storage → Cookies → https://x.com
3. Copy `auth_token` and `ct0`

## Reddit (experimental)

- Treat as experimental; API and subreddit rules can change
- Requires `subreddit:` in frontmatter
- Title comes from frontmatter `title:` (or first line if missing)
- Match each subreddit's rules and tone
