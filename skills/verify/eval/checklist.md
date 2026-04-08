# Verification Skill - Eval Checklist

## Pass/Fail Criteria (for evaluating the verification agent itself)

- [ ] **Evidence-based:** Every check cites a specific command output or file inspection, not just "looks good"
- [ ] **No self-grading:** The verification was done by a different agent than the one that did the work
- [ ] **Complete coverage:** All 6 checks were evaluated (none skipped)
- [ ] **Verdict matches evidence:** If 3+ checks failed, verdict must be FAIL (not PARTIAL)
- [ ] **Safety override:** If safety check failed, overall verdict must be FAIL regardless of other checks
- [ ] **Report written:** Verdict was logged to memory/verification-logs/
