# Skill Discovery Pilot Checklist

1. [ ] Candidate count is bounded to 5-10.
   - PASS if the runner rejects other configured limits and never evaluates more than 10 repositories.

2. [ ] Untrusted repositories remain inert.
   - PASS if the runner performs metadata/text fetches only and contains no clone, install, shell execution, or subprocess path for candidate content.

3. [ ] Every decision is evidence-backed.
   - PASS if each candidate records provenance, safety categories/count, relevance score, duplication score, and decision reasons.

4. [ ] High-risk content fails closed.
   - PASS if multiple suspicious categories produce `REJECT_SAFETY` without echoing suspicious commands into the report.

5. [ ] Promotion remains human-controlled.
   - PASS if output contains no install/merge action and explicitly requires a separate approved task.

6. [ ] The run is reproducible.
   - PASS if fixture mode produces stable decisions and focused tests pass without network access.
