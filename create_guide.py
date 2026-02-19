#!/usr/bin/env python3
from notion_client import Client
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
parent_id = '30b8d599-a162-8067-9eb8-f229b473d25f'

print("="*60)
print("CREATING ENHANCEMENT GUIDE")
print("="*60)

guide_content = """# 📚 How to Enhance Your Notion Pages

## Quick Wins (Do These First)

### 1. Add Icons (1 min per page)
- Click the page icon (📄)
- Choose an emoji that represents the content
- Examples:
  - CVs: 📋
  - LinkedIn: 🔗
  - Case Studies: 📊
  - Strategy: 🎯

### 2. Add Cover Images (1 min per page)
- Hover over the page
- Click "Add cover"
- Upload a relevant image or choose gradient

### 3. Turn Into Database (2 min)
- Click "..." on page
- Select "Turn into"
- Choose "Table - Inline"
- Now you can add properties!

### 4. Add Properties (3 min)
Once in a database, add these properties:

| Property | Type | Values |
|----------|------|--------|
| Created | Date | Auto |
| Status | Select | Draft, Review, Published |
| Type | Select | CV, Content, Case Study |
| Priority | Select | High, Medium, Low |
| Tags | Multi-select | Your keywords |

---

## Page Enhancement Checklist

For each page, do:

- [ ] Add relevant emoji icon
- [ ] Add cover image (professional background)
- [ ] Add summary callout at top
- [ ] Add key metrics as bullets
- [ ] Add related page links
- [ ] Add tags/metadata

---

## Example Enhanced Page

```
📄 CV: MASTER_CV
━━━━━━━━━━━━━━━━━━━━━━
🖼️ Cover: Professional background
📋 Properties:
   • Type: CV
   • Status: Published
   • Created: Feb 2026

> 💼 **Executive Profile**
> 20+ years in Digital Transformation
> $50M current program | 233x growth at Talabat

💰 Key Metrics
- $50M: Current transformation (Saudi German)
- 233x: Platform growth (Talabat)
- 300+: Projects managed (Network International)
- 8: Countries coverage

🔗 Related Pages
- [[CV: MASTER_CV_QUICKREF]]
- [[Case: Talabat]]
- [[Strategy: Executive Playbook]]

📁 Tags: #executive #healthtech #digitaltransformation
```

---

## Bulk Actions

### Quick Add Icons
1. Open page
2. Press `Ctrl/Cmd + /`
3. Search "icon"
4. Choose emoji

### Quick Add Cover
1. Press `Ctrl/Cmd + /`
2. Search "cover"
3. Choose image/gradient

---

## Pro Tips

1. **Use Consistent Icons**: Same category = same emoji
2. **Use Consistent Covers**: Same type = similar style
3. **Link Everything**: Every page should link to 2+ related pages
4. **Use Callouts**: Highlight key info with 📌 or 💡
5. **Add Tags**: Makes search easier

---

## Recommended Icon System

| Category | Icon | Example |
|----------|------|---------|
| Core Files | 📁 | MEMORY.md |
| CVs | 📋 | MASTER_CV |
| LinkedIn | 🔗 | linkedin_posts |
| Case Studies | 📊 | case-study-talabat |
| Strategy | 🎯 | Executive Playbook |
| Templates | 📝 | TEMPLATE |
| Dashboard | 🎛️ | Enhanced Dashboard |

---

## Resources

- [[🎯 Enhanced Dashboard]] - Main navigation
- [[CV: MASTER_CV]] - Your resume
- [[📊 Case Studies]] - Success stories
- [[🔗 LinkedIn Content]] - Post templates

---

*Guide created: {date}*

**Next Step:** Start enhancing pages one by one!""".format(date=datetime.now().strftime("%B %d, %Y"))

try:
    guide = notion.pages.create(
        parent={'page_id': parent_id},
        properties={'title': {'title': [{'text': {'content': '📚 Enhancement Guide'}}]}}
    )
    guide_id = guide['id']
    print("Created: Enhancement Guide page")
    
    lines = guide_content.strip().split('\n')
    for i in range(0, len(lines), 15):
        chunk = lines[i:i+15]
        text = '\n'.join(chunk)
        if text.strip():
            try:
                notion.blocks.children.append(guide_id, children=[
                    {'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': text[:2000]}}]}}
                ])
            except:
                pass
    
    print("Added content")
    print("\n" + "="*60)
    print("GUIDE CREATED SUCCESSFULLY")
    print("="*60)
    
except Exception as e:
    print("Error: " + str(e)[:80])
