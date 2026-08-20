## Learned Improvements

### 2026-04-04 — Weekly Skill Tune-Up

**Context:** No direct errors this week (2026-03-28 to 2026-04-04), but systemic improvements needed based on adjacent failures:

1. **Ontology update resilience (from 3/30 silent failure):** Step 5.5 ontology commands use JSON-in-string format for --props. If shell escaping breaks, the command silently creates an empty entity. Add: after each `ontology.py create`, parse the returned id and validate it's non-empty before proceeding to the next step. If any create returns empty, fail loudly.

2. **Model gate enforcement:** Step 1 should explicitly log which model is active before starting CV work. If it is not `openai/gpt-5.6-sol`, STOP and announce. Do not proceed on another model or report partial results.

3. **Master CV data freshness (general):** Before loading `memory/master-cv-data.md`, check `memory/cv-pending-updates.md` for any PENDING entries older than 7 days. If found, apply them or flag for Ahmed review. Stale pending updates cause CV data to drift.

**Action:** Added these as implicit pre-flight checks. The quality gates already cover post-gen validation, but these pre-gen checks prevent waste earlier in the pipeline.

### 2026-04-11 — Weekly Skill Tune-Up

**Reviewed signals:**
- 2026-03-16, never cut CV quality or tailoring depth without explicit approval
- 2026-03-18, never recommend or score from title-only without the full JD
- 2026-03-24, every generated CV needs visual review, not just automated validation

**Improvements to keep active:**
1. **Make the quality tradeoff explicit before batch work.** If more than 3 CVs are requested, the skill should force a decision between fully tailored output and faster template-assisted output before any drafting starts.
2. **Promote full-JD proof to a visible gate.** Step 0 already requires the complete JD, but delivery should also state where that JD came from so title-only shortcuts cannot creep back in.
3. **Add a human-eye final check to the written workflow.** Step 5 currently points to automated gates; the skill should also require a rendered visual review of page 1 and page 2 before delivery, especially for header/footer artifacts and spacing drift.
4. **Create an explicit `eval/checklist.md`.** This skill has strong eval files, but not one compact final checklist. Adding one would reduce missed steps during hurried runs.

### 2026-04-18 — Weekly Skill Tune-Up

**Audit note:** No fresh CV-builder-tagged lessons were logged in the last 7 days, so this stayed in the weekly audit as a default high-value skill and was reviewed for instruction drift.

**Improvements to add next:**
1. **Keep model wording aligned with the current workspace rule.** `eval/quality-gates.md` must require `openai/gpt-5.6-sol` with high reasoning.
2. **Promote JD provenance into the delivery contract.** The final response should explicitly state where the full JD came from, pasted text, fetched page, or handoff file, so title-only drift cannot slip back in.
3. **Make ontology writes blocking and verified.** Step 5.5 should require checking that every `ontology.py create` call returns a real id before the skill can claim completion.
4. **Add one compact final checklist file.** The missing `eval/checklist.md` is still the biggest structural gap. It should cover model, full-JD proof, ATS floor, rendered visual QA, post-generation text extraction, and ontology update confirmation.

### 2026-04-18 - Weekly Skill Tune-Up (cron refresh)

**Audit basis:** No direct executive-cv-builder-tagged lessons were found in `memory/lessons-learned.md`, so this stayed in scope as a default high-value skill and the refresh focused on structural drift in the current instructions.

**Improvements to add next:**
1. **Keep the model gate as a current-policy check.** `eval/quality-gates.md` must match the active GPT-5.6 Sol policy.
2. **Make the missing checklist a real blocker.** Add `eval/checklist.md` and require it before Step 5.5. Keep it binary: full JD proven, ATS floor met, rendered page 1 and page 2 visually reviewed, `pdftotext` clean, ontology ids captured, delivery filename correct.
3. **Gate ontology and git actions behind proof, not hope.** Step 5.5 and Step 8 should require explicit confirmation that ontology create calls returned ids and the PDF exists at the delivery path before any commit or push instruction runs.
4. **Expose JD provenance in the delivery format.** The final handoff should state whether the JD came from pasted text, fetched URL, or handoff file so title-only drift is impossible to hide.

### 2026-04-25 - Weekly Skill Tune-Up

**Audit basis:** No fresh executive-CV-specific failure dominated the last 7 days, but the weekly check kept this skill in scope as a default high-value workflow. The requested `eval/checklist.md` is still missing, so the main risk is instruction drift across multiple eval files during rushed CV delivery.

**Reviewed lessons:**
- 2026-04-21, do not mislabel vendor/marketing emails as interview activity. This matters for CV/application triage because the skill should only build application materials from verified hiring signals.
- 2026-04-15, important recruiter follow-ups can fall through narrow email rules. CV requests triggered by recruiter follow-up should preserve the full thread and JD/source proof before tailoring.
- 2026-04-17, avoid ambiguous “half-done” wording. CV closeout should state completed artifacts, checks run, and any blocker plainly.

**Improvement recommendation:**
1. **Add a recruiter-signal verification gate before CV work.** Confirm the request is tied to a real JD, recruiter/hiring team message, or application handoff, not vendor marketing or a weak title-only signal.
2. **Create the missing compact checklist.** `eval/checklist.md` should be added next with binary gates for full JD/source proof, ATS floor, rendered PDF review, text extraction, ontology IDs, filename, and delivery wording.
3. **Make CV closeout artifact-based.** Final delivery should list the generated PDF path, ATS score, JD provenance, visual QA result, ontology update status, and whether any follow-up is genuinely blocked.
4. **Keep stale model language out of gates.** Any model check should refer to the current workspace-approved top-tier model policy, not outdated hard-coded model names.
### 2026-05-09 - Weekly Skill Tune-Up

**Audit basis:** No lessons were logged in the last 7 days, so this stayed in scope as a default high-value skill. eval/checklist.md is still missing, while eval/quality-gates.md needed alignment with the current workspace model policy.

**Reviewed lessons:**
- No direct CV, resume, or ATS lessons were found in `memory/lessons-learned.md`.
- Adjacent recruiting lessons from 2026-04-25 reinforce source verification before treating an alert as actionable.
- Repeated closeout lessons reinforce artifact-based completion language instead of vague status.

**Improvement recommendation:**
1. **Create the missing compact checklist.** Add `eval/checklist.md` with binary gates for full JD/source proof, recruiter or application signal verification, ATS floor, rendered PDF review, clean `pdftotext`, ontology IDs, filename, and delivery wording.
2. **Keep model wording current.** `eval/quality-gates.md` must use the current GPT-5.6 Sol requirement.
3. **Make closeout artifact-based.** Delivery should list the PDF path, ATS score, JD provenance, visual QA result, ontology status, and any real blocker.

### 2026-05-16 - Weekly Skill Tune-Up

**Audit basis:** Recent lessons from 2026-05-15 did not identify a CV-specific failure, so this stayed in scope as a default high-value skill. The requested `eval/checklist.md` still does not exist, and the existing eval files still carry stale model-specific wording.

**Reviewed lessons:**
- 2026-05-15, fix low-risk JobZoom warnings instead of reporting preventable noise. For CV work, local validation warnings should be inspected and fixed before delivery when safe.
- 2026-05-15, avoid empty private closeouts after Telegram sends. CV delivery should be one useful artifact-based closeout, not a second bookkeeping reply.
- 2026-04-25, source verification matters before treating job or recruiter signals as actionable.

**Improvement recommendation:**
1. **Make the compact checklist the next structural fix.** Add `eval/checklist.md` with binary gates for JD provenance, real recruiter/application signal, ATS floor, visual PDF review, clean `pdftotext`, ontology IDs, filename, and delivery wording.
2. **Treat local validation warnings as actionable.** If PDF checks, ontology writes, or pipeline updates produce low-risk warnings, inspect and fix the local cause before reporting completion.
3. **Keep delivery to one useful closeout.** After sending or attaching the CV, the visible response should include PDF path, ATS score, JD source, checks run, and any real blocker. Do not add a separate empty or generic final receipt.
4. **Keep stale model hard-coding out.** Eval files must use the current GPT-5.6 Sol model policy.

### 2026-05-23 - Weekly Skill Tune-Up

**Audit basis:** One recent CV-adjacent lesson from 2026-05-16 directly applies: JobZoom CV packs were resent for roles already marked applied. No `eval/checklist.md` exists yet, so the recommendation stays in this skill file rather than creating a new checklist during this bounded cron.

**Reviewed lessons:**
- 2026-05-16, check `applied_jobs` and `jobs.applied` before sending or regenerating JobZoom CV packs.
- 2026-05-15, fix low-risk JobZoom warnings instead of reporting preventable noise.
- 2026-05-15, avoid empty private closeouts after Telegram sends.

**Improvement recommendation:**
1. **Add an applied-ledger preflight before CV delivery.** For any JobZoom or pipeline-generated CV pack, verify each target role against `applied_jobs` and `jobs.applied` before sending, regenerating, or treating it as an active opportunity.
2. **Separate artifact generation from delivery eligibility.** A valid PDF is not enough to deliver. The role must still be actionable, not already applied, and tied to a verified JD or recruiter/application signal.
3. **Make duplicate-send prevention visible in closeout.** Delivery should state whether applied-ledger checks were run, how many roles were blocked as already applied, and which PDFs were actually sent.
4. **Keep the compact checklist as the next structural fix.** `eval/checklist.md` should include the applied-ledger gate along with JD provenance, ATS floor, rendered PDF review, clean text extraction, ontology ids, filename, and delivery wording.

### 2026-05-30 - Weekly Skill Tune-Up

**Audit basis:** Recent lessons from 2026-05-23 to 2026-05-30 were mostly OpenClaw runtime and cron-sandbox issues, not direct CV-builder failures. The strongest CV-relevant carryover is still the 2026-05-16 applied-ledger miss, and this skill still has no `eval/checklist.md`.

**Reviewed lessons:**
- 2026-05-16, check `applied_jobs` and `jobs.applied` before sending or regenerating JobZoom CV packs.
- 2026-05-27, cron/internal maintenance should use approval-safe commands and narrow checks before more complex helpers.
- 2026-05-28, interrupted work needs current-state inspection before retrying completed steps.

**Improvement recommendation:**
1. **Make duplicate-delivery prevention explicit in Step 0.** Before any JobZoom or pipeline CV pack is generated, resent, or delivered, verify the target role is not already marked applied in both available ledgers.
2. **Resume from inspected state after interruptions.** If CV generation, PDF validation, ontology writes, or Telegram delivery were interrupted, inspect existing artifacts and ledger state before rerunning the workflow.
3. **Keep validation commands simple in cron contexts.** For scheduled CV maintenance, prefer direct file existence, ledger, and PDF checks before shell pipelines that may be rejected by the cron sandbox.
4. **Create `eval/checklist.md` as the next structural fix.** It should include JD provenance, real hiring signal, applied-ledger clear, ATS floor, rendered PDF QA, clean text extraction, ontology ids, filename, delivery status, and interruption-resume checks.

### 2026-06-06 - Weekly Skill Tune-Up

**Audit basis:** Recent lessons from 2026-06-02 to 2026-06-05 were CV/application adjacent: LinkedIn Easy Apply can show the wrong selected CV after a nominal upload, external ATS flows require real missing artifacts and explicit account approval, and confirmed submissions must be locked in the dedupe ledger. `eval/checklist.md` is still missing.

**Reviewed lessons:**
- 2026-06-02, LinkedIn Upload Success Needs Visible Exact-CV Proof.
- 2026-06-03, External ATS Submissions Need Real Required Artifacts And Account Approval.
- 2026-06-04, Job Application Success Needs Dedupe Ledger Verification.

**Improvement recommendation:**
1. **Tie CV completion to selected-file proof.** When a generated CV is used in LinkedIn or ATS submission, require visible proof that the exact tailored PDF is selected before marking the CV/application package complete.
2. **Keep missing artifacts as blockers.** Do not substitute certificates, diplomas, credentials, or unrelated documents to satisfy ATS upload requirements. Record the missing item and ask Ahmed for the real artifact or approval path.
3. **Verify permanent dedupe after submission.** After any confirmed submission using a generated CV, verify both the application status/report and the permanent applied-job ledger so future scans cannot resurface the same role.
4. **Create `eval/checklist.md` next.** Include exact selected-CV proof, missing-artifact gate, account-approval gate, applied-ledger lock, JD provenance, ATS floor, rendered PDF QA, clean text extraction, ontology ids, filename, and delivery status.


### 2026-06-13 - Weekly Skill Tune-Up

**Audit basis:** Recent lessons from 2026-06-02 to 2026-06-04 remain directly relevant to CV/application completion: LinkedIn uploads can report success while the wrong CV remains selected, external ATS portals must not receive substitute artifacts, and confirmed submissions still need permanent dedupe proof. The requested `eval/checklist.md` is still missing.

**Reviewed lessons:**
- 2026-06-02, LinkedIn Upload Success Needs Visible Exact-CV Proof.
- 2026-06-03, External ATS Submissions Need Real Required Artifacts And Account Approval.
- 2026-06-04, Job Application Success Needs Dedupe Ledger Verification.

**Improvement recommendation:**
1. **Make exact-CV selection a blocking delivery gate.** A generated PDF is not complete for LinkedIn or ATS use until the visible portal UI shows the exact tailored filename selected, not an old CV or an empty upload control.
2. **Record missing artifacts as real blockers.** If a portal asks for diplomas, certificates, credentials, account creation, MFA, passkey, or reCAPTCHA, stop and ask Ahmed instead of substituting another document or treating the CV pack as submission-ready.
3. **Close the loop in the permanent ledgers.** After a CV-backed submission, verify the application report and permanent applied-job ledger before saying the role is done.
4. **Prioritize the compact checklist.** `eval/checklist.md` should now be treated as the next structural fix, covering JD provenance, ATS floor, exact selected-CV proof, missing-artifact gate, approval-sensitive account steps, visual PDF QA, text extraction, ontology ids, delivery status, and dedupe ledger lock.


### 2026-06-20 - Weekly Skill Tune-Up

**Audit basis:** Recent June lessons are CV/application-adjacent rather than pure writing failures. The active risks are false completion signals after LinkedIn or ATS submission attempts, rejection emails being treated as actionable, and duplicate retry rows inflating application counts. The compact `eval/checklist.md` is still missing, so this recommendation remains in the skill file.

**Reviewed lessons:**
- 2026-06-17, Bulk LinkedIn Application Counts Need Submitted Proof States.
- 2026-06-19, Email Rejections Should Not Be Auto-Actionable.
- 2026-06-19, LinkedIn Bulk Campaigns Need Unique-ID Counts And Runner Fallbacks.

**Improvement recommendation:**
1. **Gate CV/application completion on proof states.** Count a CV-backed application as complete only when the portal shows an explicit submitted state for the unique job id, the exact tailored CV was selected, and the permanent ledger has the same unique id.
2. **Do not regenerate or escalate from plain rejections.** Rejection/status emails should not trigger a CV rebuild, follow-up, or actionable alert unless they ask Ahmed to schedule, reply, provide documents, or complete a specific step.
3. **Deduplicate retries before reporting totals.** If LinkedIn or JobZoom retries create duplicate rows, collapse by unique LinkedIn/job id before saying how many applications were submitted.
4. **Use runner fallback without weakening gates.** If the visible CDP path is unavailable and a browser-CLI runner is used, keep the same proof requirements: exact CV selected, no unknown/sensitive fields guessed, visible submitted proof, and ledger lock.

### 2026-06-27 - Weekly Skill Tune-Up

**Audit basis:** No direct executive-CV-builder failure appeared in the last 7 days, so this remained in scope as a default high-value workflow. Recent application and briefing lessons reinforce that CV work should only start from real source evidence and should not treat automation output as proof without manual verification.

**Reviewed lessons:**
- 2026-06-21, Job Hunter Notion Fallback Needs Type Guards.
- 2026-06-22, Email Briefings Need Body-Proof Urgency.
- 2026-06-24, JobZoom And CMO Loops Need Manual Proof Before Automation.

**Improvement recommendation:**
1. **Require typed source records before tailoring.** When a JD or application handoff comes from Notion, JobZoom, email, or another parser, validate the expected fields and types before using it for ATS scoring or CV generation.
2. **Keep body-proof as the trigger gate.** Do not rebuild, tailor, or escalate a CV from a noisy email category, title-only alert, or inferred opportunity. Require body/source evidence that proves a real role, recruiter request, assessment, or document need.
3. **Add manual proof before automating CV loops.** Before turning a CV/application pattern into a validator or cron, run clean manual passes that prove source evidence, artifact generation, exact selected-CV proof, ledger update, and clear stop state.
4. **Keep `eval/checklist.md` as the structural gap.** The compact checklist should include typed-source validation, body-proof trigger, ATS floor, exact selected-CV proof, rendered PDF QA, text extraction, ontology ids, dedupe ledger lock, and artifact-based closeout.


### 2026-07-04 - Weekly Skill Tune-Up

**Audit basis:** No direct executive-CV-builder failure appeared in the last 7 days, so this stayed in scope as a default high-value workflow. Recent application lessons still affect CV package completion: exact-CV proof, visible authenticated submission paths, and real ATS artifacts are the strongest carryover risks. `eval/checklist.md` is still missing.

**Reviewed lessons:**
- 2026-06-02, LinkedIn Upload Success Needs Visible Exact-CV Proof.
- 2026-06-03, LinkedIn Easy Apply Can Recover Through A Different Visible Authenticated Profile.
- 2026-06-03, External ATS Submissions Need Real Required Artifacts And Account Approval.

**Improvement recommendation:**
1. **Treat exact selected-CV proof as a completion gate.** A generated CV package is not submission-ready until the visible portal UI shows the exact tailored PDF selected, or the workflow records a blocker instead of continuing.
2. **Keep visible authenticated lane recovery separate from CV quality.** If a LinkedIn or ATS lane changes profile, runner, or browser context, re-check the selected filename, target role, and account identity before using the CV.
3. **Do not substitute missing artifacts.** Diplomas, certificates, IDs, credentials, account creation, MFA, passkey, or reCAPTCHA remain blockers unless Ahmed provides the artifact or explicit approval path.
4. **Create `eval/checklist.md` next.** It should include JD/source proof, ATS floor, exact selected-CV proof, missing-artifact gate, rendered PDF QA, text extraction, ontology ids, dedupe ledger lock, and artifact-based closeout.
