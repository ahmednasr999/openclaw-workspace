# UI Audit Checklist

Use this for existing frontend redesign or quality review.

## Hierarchy
- Is there one clear primary action per screen?
- Can a user understand the page purpose within 3 seconds?
- Are headings sized by importance, not randomly large?
- Are metrics/data labels clear and comparable?

## Layout and spacing
- Is the page constrained on wide screens?
- Are sections visually distinct without random background jumps?
- Are side-by-side elements aligned optically, not just mathematically?
- Are card groups aligned and not awkwardly equal-height when content differs?
- Does mobile collapse to a clean single-column flow?

## Color and surface
- Is there one main accent color?
- Are neutral tones consistent?
- Are cards, borders, and shadows used intentionally?
- Is the contrast strong enough for reading?

## States
- Loading states match the final layout shape.
- Empty states explain what happened and what to do next.
- Error states are inline and recoverable.
- Buttons have hover, active, focus, disabled states.
- Forms have labels, helper/error text, and accessible focus.

## Responsiveness
- No horizontal scroll at common mobile widths.
- Images/media maintain aspect ratio.
- Touch targets are large enough.
- Sticky/fixed elements do not cover content.

## Content realism
- No Lorem Ipsum.
- No generic names unless obviously sample data.
- No overused AI copy clichés.
- Metrics and examples match the domain.

## Performance
- Avoid repaint-heavy background filters in scrolling areas.
- Animate transform/opacity only.
- Avoid unnecessary animation libraries.
- Use optimized image formats and explicit dimensions when possible.
