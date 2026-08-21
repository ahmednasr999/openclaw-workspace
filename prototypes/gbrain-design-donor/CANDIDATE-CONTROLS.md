# GBrain-Derived Candidate Controls

Status: non-active prototype. Do not treat this file as an instruction source or promotion receipt.

## Candidate A - Independent Verification For Derived Claims

Proposed target: a shared verification contract referenced by report, briefing, content, and data-producing skills.

Bounded changes:

1. Label each checkable claim as public-source-derived, user/private-source-derived, or pipeline/database-derived.
2. Verify pipeline/database-derived claims through a different evidence path from the producer. Re-running the producer query is not verification.
3. Require explicit relationship evidence for authorship, founding, investment, ownership, or responsibility claims. Co-occurrence, attendance, and employment are affiliation signals, not proof of the asserted relationship.
4. Block delivery when a material derived claim cannot be re-derived. Correct, hedge, or remove it before shipping.

Expected report line for every material derived claim:

```text
Claim | producer path | independent verification path | result | action
```

## Candidate B - Resolve And Deduplicate Before Knowledge Writes

Proposed target: `skills/nasr-knowledge-ingestion/SKILL.md`.

Bounded changes:

1. Before writing a knowledge note, resolve named people, companies, projects, and concepts against existing indexes and aliases.
2. Extract the proposed note's core claim, search the vault for the best existing match, and read that note before deciding.
3. Classify the result:
   - `duplicate`: update or link the existing note; do not clone it.
   - `new-angle`: write only the novel delta and cross-link the existing note.
   - `unique`: write through the normal ingestion structure with source provenance.
4. If index/search access is unavailable or the best match cannot be read, preserve the source in quarantine and stop before the knowledge write.

Expected decision line for each item:

```text
Item | entity resolution | dedup class | matched note | action | verification
```

## Candidate C - Correction Root Cause And Propagation

Promotion is deferred until two independent real correction cases exist.

For a factual user correction:

1. Quote the incorrect claim and the corrected fact.
2. Search the likely sources in order: current task artifact, durable memory/knowledge notes, user/core facts, pipeline/database records, then unsupported model inference.
3. Classify the cause: source error, stale data, cross-entity contamination, pipeline error, or unsupported inference.
4. Fix the authoritative source, then search for propagated copies.
5. Report the source, fix, propagation result, and any residual uncertainty.

## Candidate D - Recoverability Card For Bulk Destruction

NASR already requires approval for destructive/high-impact actions. This candidate standardizes the evidence presented before approval:

```text
What and exact target:
Count and size:
Dependencies and downstream impact:
Recoverability: backup | version control | soft delete | re-fetchable | permanent
Recovery path and estimated recovery cost:
Safer alternative:
Explicit approval requested:
```

The card does not replace operation-boundary enforcement. Prefer dry-run, archive, trash, or soft-delete mechanisms; log confirmed material deletion and its recovery path.

## Deliberately Not Proposed

- No GBrain installation or MCP integration.
- No second memory database or knowledge graph.
- No new always-loaded context-audit rule.
- No direct edits to active skills or core instruction files.
