---
name: scanner-test
description: "One-time test run of the LinkedIn job scanner to verify it works."
---

# Scanner Test Run

## Steps

### Step 1: Run scanner
```bash
cd /root/.openclaw/workspace
python3 scripts/linkedin-gulf-jobs.py --test 2>&1 | tail -20
```
If --test flag not supported:
```bash
python3 scripts/linkedin-gulf-jobs.py 2>&1 | tail -30
```

### Step 2: Verify output
Check that scanner:
- Connected successfully
- Found job listings
- Parsed results correctly
- Wrote to output file

### Step 3: Report
```
Scanner Test - [DATE]
Status: [PASS/FAIL]
Jobs found: [X]
Errors: [list or "none"]
```

## Error Handling
- If script not found: Report "Scanner script missing"
- If connection fails: Report the specific error

## Quality Gates
- Must actually run the script, not just check if it exists

## Output Rules
- No em dashes. Hyphens only.
