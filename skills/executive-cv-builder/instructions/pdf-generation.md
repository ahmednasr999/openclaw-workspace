# Step 5 — PDF Generation

Use WeasyPrint (most consistent results, 19-25KB target size):

```bash
# Generate HTML version first
cat > /tmp/cv-ahmed-nasr.html << 'HTML'
[CV content formatted as clean HTML with inline CSS]
HTML

# Convert to PDF via WeasyPrint (preferred method)
weasyprint /tmp/cv-ahmed-nasr.html "/root/.openclaw/workspace/cvs/Ahmed Nasr - [Role] - [Company].pdf"

# Fallback only if WeasyPrint fails:
# npx playwright pdf /tmp/cv-ahmed-nasr.html "/root/.openclaw/workspace/cvs/Ahmed Nasr - [Role] - [Company].pdf"
```

PDF formatting requirements:
- Font: Clean sans-serif (Arial or Helvetica)
- Margins: 0.75 inch all sides
- Section headers: bold, slightly larger
- Bullets: left-aligned, consistent indentation
- No tables, text boxes, or graphics (ATS killer)
- Single or two-column header only (name + contact)
- Target file size: 15-30KB. If > 50KB, something is wrong (embedded fonts/images). If < 10KB, styling likely missing.
