# Post-Generation Quality Gate (automated, mandatory)

Run these checks before sending to Ahmed. If any fail, regenerate:

```bash
PDF_PATH="/root/.openclaw/workspace/cvs/Ahmed Nasr - [Role] - [Company].pdf"

# 1. File size check (15-50KB expected)
SIZE=$(stat -c%s "$PDF_PATH")
echo "Size: ${SIZE}B"

# 2. Text extraction check (must be extractable for ATS)
TEXT=$(pdftotext "$PDF_PATH" - 2>/dev/null)
CHARS=$(echo "$TEXT" | wc -c)
echo "Extractable chars: $CHARS"

# 3. Em dash check (hard zero tolerance)
EMDASH=$(echo "$TEXT" | grep -cP '—' || echo 0)
echo "Em dashes found: $EMDASH"

# 4. Header check (no role/company in body text header)
HEADER_VIOLATION=$(echo "$TEXT" | head -5 | grep -ciE '(CV|Resume|Curriculum)' || echo 0)
echo "Header violations: $HEADER_VIOLATION"

# 5. Contact info present
CONTACT=$(echo "$TEXT" | grep -c 'ahmednasr999@gmail.com' || echo 0)
echo "Contact info: $CONTACT"
```

All checks must pass: size 15-50KB, chars > 2000, em dashes = 0, header violations = 0, contact = 1.
