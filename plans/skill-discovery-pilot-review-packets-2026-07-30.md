# Skill Discovery Pilot Review Packets

## Plan Metadata

- Status: complete
- Owner: NASR
- Planned at: commit `076603c` on `2026-07-30`
- Depends on: none

> **Executor contract:** Read the full plan before editing. Stay inside scope, run each verification gate, and report evidence. If a stop condition is met or reality conflicts with the plan, stop and report the mismatch instead of improvising.

> **Drift check:** `git diff --stat 076603c..HEAD -- skills/skill-discovery-pilot config/skill-discovery-pilot.json`
> If an in-scope path changed, compare current source with the evidence anchors below. Refresh or supersede the plan before execution when the intended change or verification no longer matches.

## Objective

- Target outcome: Extend the weekly discovery pilot with inert Reader/Extractor evidence, five-case representative evaluation plans, and local PR-ready review packets for `REVIEW` candidates.
- User-visible success condition: A fixture and bounded live run produce useful review packets while repository content remains quarantined and no branch, pull request, installation, or active-skill change occurs.
- Why this matters: The current workflow identifies candidates but leaves the highest-value analysis and promotion preparation manual.

## Evidence And Current State

- Source anchors: `skills/skill-discovery-pilot/scripts/discover.py:269` - evaluation currently stores README text in quarantine and produces only candidate-level scores.
- Source anchors: `skills/skill-discovery-pilot/scripts/discover.py:318` - the report currently exposes headings but no structured pattern, evaluation matrix, or review packet.
- Source anchors: `skills/skill-discovery-pilot/references/policy.md:41` - promotion requires isolated review, representative tests, and explicit approval.
- Existing convention to follow: `skills/skill-discovery-pilot/tests/test_discover.py:87` - human reports must not echo suspicious commands.
- Reproduction or baseline: `python3 -m unittest skills/skill-discovery-pilot/tests/test_discover.py` passes 9 tests.
- Raw evidence to preserve: existing fixture decisions and the latest report format.

## Scope

- In scope: deterministic extraction from already fetched README text; bounded review packet generation; representative evaluation templates; focused tests; skill/policy/checklist documentation.
- Files likely touched: `skills/skill-discovery-pilot/**`, `config/skill-discovery-pilot.json`, this plan, and the current daily note.
- Do not touch: active skills outside the pilot, cron, gateway/runtime state, credentials, GitHub repositories, or external systems.
- Non-goals: cloning or executing candidate code; generating/installing a candidate skill; opening a branch or pull request; assigning reviewers; automatic promotion.

## Authority And Safety

- Permission profile: local-write
- Approval boundary: Ahmed approved the local pilot extension. Any candidate source inspection beyond inert text, generated candidate implementation, external PR, merge, installation, or promotion remains separately approval-gated.
- Rollback path: revert only the files listed in scope; generated run artifacts are isolated beneath `data/skill-discovery-pilot/`.
- External/public/credential/paid/runtime action involved: no

## Owner And Helpers

- Owning session/agent: NASR `/root`
- Helpers, if explicitly permitted: none
- Independent assignment and expected evidence for each helper: none
- Maximum concurrency: 1

## Ordered Implementation Steps

### Step 1: Add inert Reader/Extractor evidence

- Files: `skills/skill-discovery-pilot/scripts/discover.py`
- Change: hash each source snapshot and write bounded, explicitly untrusted reader and reusable-pattern JSON artifacts without interpreting source text as instructions.
- Preserve: metadata/text-only network behavior, quarantine isolation, command redaction, candidate decision policy.
- Verify command/check: focused unit tests for hashes, safe labels, and absence of repository execution paths.
- Expected result: every candidate has traceable reader evidence; only `REVIEW` candidates advance to review-packet preparation.

### Step 2: Generate representative evaluation and draft-PR packets

- Files: `skills/skill-discovery-pilot/scripts/discover.py`, `config/skill-discovery-pilot.json`
- Change: create five deterministic acceptance cases and a local `draft-pr.md` marked not ready to open, with unresolved approval gates.
- Preserve: no GitHub write API, no `git`/`gh`/subprocess path, no active-skill output.
- Verify command/check: tests prove packet count, required scenarios, explicit stop gate, and non-generation for rejected candidates.
- Expected result: each `REVIEW` candidate has a safe local review packet and the run report links to it.

### Step 3: Update the governing documentation and evaluations

- Files: `skills/skill-discovery-pilot/SKILL.md`, `skills/skill-discovery-pilot/references/policy.md`, `skills/skill-discovery-pilot/eval/checklist.md`, `skills/skill-discovery-pilot/evals/evals.json`
- Change: document the new stages, trust labels, deterministic gates, five-case evaluation standard, and external PR prohibition.
- Preserve: explicit human approval before promotion.
- Verify command/check: inspect the skill against the updated checklist.
- Expected result: instructions and implementation describe the same workflow and stop conditions.

## Test Plan

- Existing tests to run: `python3 -m unittest skills/skill-discovery-pilot/tests/test_discover.py`
- New or changed tests: Reader/Extractor safety, five-case matrix, draft-PR stop label, rejected-candidate exclusion, end-to-end fixture artifacts.
- Original reproduction after implementation: run `discover.py` with `tests/fixture.json`.
- Actual artifact or behavior to inspect: one generated `REVIEW` packet, its evaluation matrix, the report, and `results.json`.

## Stop Conditions

- An evidence anchor or in-scope file has materially drifted.
- A required dependency or approval is missing.
- A verification gate fails twice after bounded repair.
- The smallest credible fix requires out-of-scope files or a new external/runtime/destructive action.

## Done Criteria

- [x] Every ordered step completed or explicitly skipped with evidence.
- [x] Focused tests and original reproduction pass.
- [x] Actual user-visible or operational outcome inspected.
- [x] Changed files remain inside scope.
- [x] Accepted review findings repaired and reverified.
- [x] Remaining risk and rollback evidence recorded.

## Review Handoff

- Diff base and target: `076603c` to working tree
- Reviewer focus: untrusted-text containment, absence of execution/external-write paths, usefulness of evaluation cases, and clarity of approval gates.
- Known trade-offs: deterministic extraction is safer but less semantically rich than an isolated model-based reader.
- Deliberately deferred work: source-tree/dependency inspection and actual candidate-skill generation.

## Closeout

- Files/artifacts changed: pilot script, tests, config, skill instructions, policy, checklist, eval prompts, this plan, and isolated run artifacts under `data/skill-discovery-pilot/`.
- Commands/checks and results: Python compile passed; 14/14 focused tests passed; fixture run passed with five candidates; bounded live run passed with five candidates; artifact assertions passed; plan validator and `git diff --check` passed.
- Deviations from plan: Added a prompt-injection rejection category during the adversarial pass because the existing suspicious-content policy did not cover instruction override attacks explicitly.
- Evidence of success: live run `20260730T110637Z` created Reader evidence for all five candidates, local Extractor/evaluation/draft-PR packets for the three `REVIEW` candidates, and no packets for the two `WATCH` candidates.
- Residual risk: Reader/Extractor output is deterministic and inert but does not inspect source trees or dependencies. The generated evaluations remain `planned_not_executed`; implementation, PR creation, and promotion stay approval-gated.
