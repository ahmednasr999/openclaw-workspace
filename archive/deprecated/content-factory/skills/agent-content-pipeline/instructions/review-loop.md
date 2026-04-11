# The Review Loop

## Flow Diagram

```
drafts/ → reviewed/ → revised/ → approved/ → posted/
              ↑          │
              └──────────┘
               more feedback
```

## Step-by-Step Process

1. You write draft to `drafts/`
2. Human runs `content review <file>`:
   - **With feedback** → file moves to `reviewed/`, you get notified
   - **No feedback** → human is asked "Approve?" → moves to `approved/`
3. If feedback: you revise and move to `revised/`
4. Human reviews from `revised/`:
   - More feedback → back to `reviewed/`
   - Approve → moves to `approved/`
5. Posting happens manually via `content post`

## After Receiving Feedback

When you get review feedback:

1. Read the file from `reviewed/`
2. Apply the feedback
3. Move the file to `revised/`
4. Confirm what you changed
5. (Optional) Add a note: `content thread <file> --from agent`
