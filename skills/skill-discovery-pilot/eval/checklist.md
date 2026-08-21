# Skill Discovery Pilot Checklist

1. [ ] Candidate count is bounded to 5-10.
   - PASS if the runner rejects other configured limits and never evaluates more than 10 repositories.

2. [ ] Untrusted repositories remain inert.
   - PASS if the runner performs metadata/text fetches only and contains no clone, install, shell execution, or subprocess path for candidate content.

3. [ ] Every decision is evidence-backed.
   - PASS if each candidate records provenance, safety categories/count, relevance score, duplication score, and decision reasons.

4. [ ] High-risk content fails closed.
   - PASS if multiple suspicious categories or any prompt-injection category produce `REJECT_SAFETY` without echoing suspicious instructions into the report.

5. [ ] Promotion remains human-controlled.
   - PASS if output contains no install/merge action and explicitly requires a separate approved task.

6. [ ] The run is reproducible.
   - PASS if fixture mode produces stable decisions and focused tests pass without network access.

7. [ ] Reader/Extractor output remains quarantined and traceable.
   - PASS if every candidate has a source SHA-256 and Reader artifact, only `REVIEW` candidates get Extractor artifacts, unsafe labels are withheld, and no candidate content reaches an execution path.

8. [ ] Representative evaluation is specific and bounded.
   - PASS if every `REVIEW` packet contains exactly five planned cases—normal, incomplete-input, hostile-instruction, overlap, and partial-failure behavior—with observable pass criteria.

9. [ ] Draft-PR preparation cannot be mistaken for an external PR.
   - PASS if the packet is local, begins `LOCAL DRAFT — DO NOT OPEN`, remains `NOT_READY_FOR_PR`, lists unresolved gates, and no branch, GitHub-write, or PR-opening code exists.
