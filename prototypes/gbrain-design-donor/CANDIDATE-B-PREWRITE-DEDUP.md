# Candidate B: Pre-write Entity Resolution and Deduplication

Status: non-active proposal artifact. This file is evidence for governed replay; it does not change NASR behavior.

Exact proposed target: `skills/nasr-knowledge-ingestion/SKILL.md`, immediately before `## Output pattern`.

Exact bounded edit (one new section):

## Pre-write identity and dedup gate

1. Resolve named people, companies, projects, and concepts against existing indexes and aliases before writing.
2. Extract the proposed note's core claim, search for the strongest existing match, and open that match before deciding.
3. Classify the item as `duplicate`, `new-angle`, or `unique`:
   - `duplicate`: update or link the existing note; do not clone it.
   - `new-angle`: write only the novel delta and cross-link the existing note.
   - `unique`: use the normal provenance-backed ingestion structure.
4. If search/index access is unavailable or the strongest match cannot be opened, preserve the source in quarantine and stop before the knowledge write.

Promotion boundary: replay acceptance is not approval. The active skill must remain unchanged until Ahmed approves this exact target and section in a separate promotion step.
