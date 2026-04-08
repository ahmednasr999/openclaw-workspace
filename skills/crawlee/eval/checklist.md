# Crawlee Skill - Quality Checklist

## Pass/Fail Checks

- [ ] **Returns data**: Scraper returns non-empty results for valid URLs
- [ ] **Correct format**: Output matches requested format (json/text/markdown)
- [ ] **Selector works**: CSS selectors extract the right elements
- [ ] **Depth control**: Multi-page crawl respects --depth and --max limits
- [ ] **Error handling**: Gracefully handles 404s, timeouts, invalid URLs
- [ ] **Clean output**: No script/style tags in extracted text content
