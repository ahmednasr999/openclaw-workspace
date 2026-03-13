# Browser Automation Helper

Before any browser interaction (click/type), always:

1. **Snapshot first** - Always take a snapshot to see current page state
2. **Check element** - Verify the element ref exists in snapshot
3. **Wait if needed** - If not found, sleep 2s and snapshot again (max 2 retries)
4. **Then interact** - Only then click/type
5. **Verify success** - Take another snapshot to confirm action worked

## Retry Pattern

For complex forms (like job applications):

```bash
# Try up to 3 times with backoff
for attempt in 1 2 3; do
  camofox_snapshot ...
  if element exists; then
    camofox_type ...
    break
  fi
  sleep $((attempt * 2))
done
```

## Better Selectors

When refs don't work, use specific selectors:

```bash
# Use CSS selector instead of ref
camofox_click --selector "button[type=submit]" --tabId "xxx"
camofox_type --selector "#expected-salary" --text "55000" --tabId "xxx"

# Common selectors
camofox_click --selector "[aria-label='Submit']" ...
camofox_click --selector "button.submit-btn" ...
camofox_click --selector "input[name='salary']" ...
```

## File Upload via CDP

For uploading CVs/files that normal automation can't handle:

```javascript
// Upload file via CDP
const input = document.querySelector('input[type="file"]');
const file = new File(['CV content'], 'resume.pdf', {type: 'application/pdf'});
const dataTransfer = new DataTransfer();
dataTransfer.items.add(file);
input.files = dataTransfer.files;
input.dispatchEvent(new Event('change', {bubbles: true}));
```

## JavaScript Injection

For complex React forms that don't respond to normal clicks:

```javascript
// Execute in browser console via camofox
// Click hidden/submit button
document.querySelector('button[type="submit"]').click();

// Fill field directly
document.querySelector('#salary-input').value = '55000';

// Trigger change event
element.dispatchEvent(new Event('change', {bubbles: true}));
```

## Screenshot on Failure

After any failed action, automatically capture screenshot:

```bash
# After failure
camofox_screenshot --tabId "$TAB_ID"
# Saves to default location, helps debug
```

## Common Fixes

- **Timeout on type**: Click the field first, then type
- **Element not found**: Scroll to it, wait, try again
- **Form not loaded**: Wait for "Loading..." to disappear

## Direct Playwright (Fallback)

When Camoufox fails, use Playwright directly:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://careers.contango.ae/...")
    page.fill('input[name="firstName"]', "Ahmed")
    page.click('button[type="submit"]')
```

Install: `pip install playwright && playwright install chromium`
