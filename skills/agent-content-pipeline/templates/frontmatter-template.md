# Frontmatter Template

Use this YAML frontmatter at the top of every content file.

## LinkedIn

```yaml
---
platform: linkedin
title: Optional Title
status: draft
---

Your LinkedIn post content here.
```

## X (Twitter)

```yaml
---
platform: x
title: Optional Title
status: draft
---

Your tweet or thread content here.
```

## Reddit (experimental)

```yaml
---
platform: reddit
title: Your Post Title
status: draft
subreddit: programming
---

Your Reddit post body here.
```

## Notes

- `status` must always start as `draft`
- `subreddit` is **required** for Reddit posts
- `title` is optional for LinkedIn and X (first line used if missing)
- File naming: `YYYY-MM-DD-<platform>-<slug>.md`
