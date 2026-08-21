# GBrain Design-Donor Assessment

Date: 2026-08-13  
Decision: use selected controls as design donors; do not install GBrain into NASR.

## Executive Decision

GBrain is credible enough to study and too overlapping to adopt as a second platform. Two ideas justify promotion candidates after replay:

1. **Producer is not verifier** for database- or memory-derived claims.
2. **Resolve and deduplicate before knowledge writes**, including reading the best existing match rather than trusting a similarity score.

The correction pipeline and recoverability card are useful hardening patterns, but NASR already owns adjacent correction, approval, backup, and destructive-action controls. The context-audit skill is useful as a report-only technique, not as another installed skill.

No active skill, core instruction, cron, gateway setting, credential, production database, or personal knowledge file was changed.

## Provenance And Isolation

- Repository: [garrytan/gbrain](https://github.com/garrytan/gbrain)
- Evaluated release: `v0.45.8.0`
- Evaluated commit: [`4dc77c39790d65f40a1560c888e4324ea5d9c5b3`](https://github.com/garrytan/gbrain/commit/4dc77c39790d65f40a1560c888e4324ea5d9c5b3)
- License: MIT
- Checkout: temporary directory under `/tmp`; not added to NASR or OpenClaw.
- Dependencies: locked with `bun.lock`; installed only in the temporary checkout with install scripts disabled.
- Credentials: test commands ran through a clean environment containing only `PATH` and temporary-directory settings.
- Data: only synthetic upstream fixtures and temporary PGLite databases were used.

## Safety Review

The repository contains defensive examples of prompt injection, two remote-install shell examples, and one example warning against credential transmission. These are not evidence of malicious behavior, but the remote-install patterns are exactly why no installer or post-install hook was executed. The dependency install used `--ignore-scripts`.

No tracked symlinks were found. The repository's privacy check passed. This is a bounded source review, not a security certification.

One tooling mismatch remains: GBrain declares Bun `>=1.3.10`; the host currently has `1.3.9`. The focused checks below passed, but a full product certification would require a matching isolated Bun runtime and the full upstream suite.

## Verification Results

| Check | Result |
|---|---|
| Destructive guard unit test | 24 passed, 0 failed |
| Structural routing evaluation | 282 passed, 0 missed, 100% top-1 accuracy |
| Brain-first skill guard | passed |
| Skill-reference checker | 169 files scanned, 0 warnings |
| Privacy checker | passed |
| Full upstream test suite | deliberately not run; out of scope for a design-donor pilot |

The strongest implementation evidence is the destructive guard: it measures impact, rejects ordinary non-interactive confirmation when data exists, supports dry-run preview, and provides a 72-hour soft-delete/restore window. The associated narrative data-loss skill is candid that it is only a routing convention; that distinction matters.

## Component Decisions

| Component | Decision | NASR overlap | Distinct value | Promotion target |
|---|---|---|---|---|
| `correction-pipeline` | Adapt after evidence | Corrections are already logged and governed learning already prevents premature promotion | Root-cause classification, fix the actual contamination source, search for propagation, and report the repair | Existing self-improvement/correction workflow, after two real independent correction cases |
| `data-loss-gate` | Retain as a card pattern | Destructive/high-impact actions already require approval; platform safeguards already inspect targets and avoid broad deletion | A standard blast-radius/recoverability card and preference for reversible soft-delete | A reusable destructive-change template, not another always-loaded rule |
| `fact-check` | Promote to candidate | NASR verifies outputs and prefers primary/live sources | Producer and verifier must use different evidence paths; unsupported data-derived claims block delivery; affiliation is not authorship | Shared verification contract referenced by report/content/data-producing skills |
| `brain-ingest-gate` | Promote to candidate | External knowledge already lands in a sandbox and core promotion is reviewed | Resolve named entities first, read the best existing match, classify duplicate/new angle/unique, and fail closed when search is unavailable | `skills/nasr-knowledge-ingestion/SKILL.md` after replay |
| `context-audit` | Use report-only; do not install | NASR already compresses core files and has an active context-engineering track | Deterministic measurement, contradiction-first review, and risk-ranked recommendations | No active target; rerun as an audit technique when the stack materially grows |

## Why Wholesale Adoption Fails The Test

- It would duplicate Lossless Claw, the Memory Wiki, Markdown memory, governed learning, and existing agent skills.
- Four of the five reviewed skills are policy/routing conventions rather than operation-boundary enforcement.
- The repository has a large dependency and maintenance surface for controls NASR can adopt more narrowly.
- A second memory system would introduce competing sources of truth, duplicate indexing, and correction drift.

## Candidate Promotion Boundary

The two high-value candidates are staged under `prototypes/gbrain-design-donor/`. They are not active behavior. Before either is promoted:

1. Run the representative tasks against the current baseline and the candidate at least twice.
2. Require zero regression on critical privacy, approval, and correctness cases.
3. Record negative evidence rather than weakening the suite.
4. Ask Ahmed to approve the exact candidate text and target path.
5. Implement the approved change separately and verify a real artifact.

## Upstream Evidence

- Correction source tracing and propagation: [correction-pipeline](https://github.com/garrytan/gbrain/blob/4dc77c39790d65f40a1560c888e4324ea5d9c5b3/skills/correction-pipeline/SKILL.md)
- Recoverability card and routing-convention limitation: [data-loss-gate](https://github.com/garrytan/gbrain/blob/4dc77c39790d65f40a1560c888e4324ea5d9c5b3/skills/data-loss-gate/SKILL.md)
- Independent re-derivation and typed-edge attribution: [fact-check](https://github.com/garrytan/gbrain/blob/4dc77c39790d65f40a1560c888e4324ea5d9c5b3/skills/fact-check/SKILL.md)
- Pre-write entity resolution and semantic dedup: [brain-ingest-gate](https://github.com/garrytan/gbrain/blob/4dc77c39790d65f40a1560c888e4324ea5d9c5b3/skills/brain-ingest-gate/SKILL.md)
- Report-only token hygiene: [context-audit](https://github.com/garrytan/gbrain/blob/4dc77c39790d65f40a1560c888e4324ea5d9c5b3/skills/context-audit/SKILL.md)
- Mechanical destructive guard: [destructive-guard.ts](https://github.com/garrytan/gbrain/blob/4dc77c39790d65f40a1560c888e4324ea5d9c5b3/src/core/destructive-guard.ts)
