---
description: "Known Gmail API limitations and workarounds for automation"
type: reference
topics: [system-ops]
updated: 2026-03-14
---

# Gmail Automation - Known Limitations & Safeguards

## ⚠️ KNOWN ISSUES

### IMAP Sync Discrepancy
- **Issue:** IMAP queries may show different count than actual Gmail
- **Cause:** Cached state vs real-time Gmail
- **Impact:** Verification may be unreliable

### Symptoms
- Query returns 0 but Gmail shows emails
- Counts don't match after deletions
- Stale folder views

## 🛡️ SAFEGUARDS REQUIRED

### 1. Pre-Operation Check
- Always query current state BEFORE operation
- Note exact count and IDs

### 2. Post-Operation Verification  
- Re-query AFTER operation
- Compare counts
- Report discrepancy if found

### 3. User Verification Checkpoint
- After any "complete" claim, ask user to verify in Gmail
- Don't proceed until user confirms actual state

### 4. Batch Verification
- For bulk operations: verify after each batch
- Don't assume success - confirm it

### 5. Confidence Reporting
- ✅ "VERIFIED clean" = I checked + user confirmed
- ⚠️ "Query shows clean" = IMAP says 0, but may be stale
- ❌ "Unknown" = Can't verify

## 📋 VERIFICATION PROTOCOL

```
BEFORE deletion:
  1. Query folder
  2. Note count + IDs
  3. Report to user

AFTER deletion:
  1. Re-query folder  
  2. Compare counts
  3. If discrepancy found: flag it
  4. Ask user to verify in Gmail
  5. Only mark "VERIFIED" after user confirmation
```

## 🔧 FIXES TO INVESTIGATE

1. Himalaya version update
2. IMAP IDLE support for real-time sync
3. Force refresh between queries
4. Alternative verification method (Gmail API directly)

## 📝 DOCUMENTATION

Updated: 2026-02-17
Issue discovered during spam cleanup - user saw email my query didn't show
