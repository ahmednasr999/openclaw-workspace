# FileKind v1 - Implementation Backlog

## Recommendation

Ship `FileKind` as a lean routing contract first, not as a full intelligence subsystem.

Goal: improve attachment and file routing safety without dragging OpenClaw into premature ML-heavy ingestion architecture.

## Scope boundary

### In scope for v1
- Canonical `FileKind` contract
- Rule-based file classification from existing signals
- Special-case handling
- Simple routing decisions for core lanes
- Honest fallback labels
- `rawLabel` vs `finalLabel` separation
- Default `balanced` confidence mode only

### Out of scope for v1
- Direct Magika integration
- Large type taxonomy
- Per-type threshold tuning
- Recursive deep archive/container inspection
- Full ML classification pipeline
- Multiple active confidence modes in production

---

## Epic 1 - FileKind contract

### Ticket 1.1 - Define canonical FileKind schema
Create a single canonical schema used everywhere file classification is needed.

Required fields for v1:
- `label`
- `group`
- `mimeType`
- `isText`
- `confidence`
- `trusted`
- `specialCase`
- `routingDecision`
- `rawLabel`
- `finalLabel`
- `evidence[]`

Acceptance criteria:
- Schema is documented in code and docs
- Schema supports both path-based and in-memory files
- `rawLabel` and `finalLabel` are distinct fields
- `specialCase` can bypass normal classification

### Ticket 1.2 - Define canonical label set for v1
Keep the taxonomy intentionally small.

Recommended labels:
- `pdf`
- `image`
- `audio`
- `video`
- `code`
- `archive`
- `data`
- `email`
- `generic_text`
- `generic_binary`
- `unknown`

Acceptance criteria:
- Label list is stable and documented
- Every routing decision maps from this set
- Unknown or ambiguous files fall back safely

### Ticket 1.3 - Define evidence model
Store how the system decided.

Recommended evidence sources:
- extension
- mime_header
- magic_bytes
- parser
- filesystem
- fallback

Acceptance criteria:
- Evidence supports multiple sources per file
- Evidence can explain why a downgrade/fallback happened
- Evidence is human-readable in logs/debug output

---

## Epic 2 - Rule-based classification

### Ticket 2.1 - Build special-case detector
These should short-circuit classification:
- empty
- directory
- symlink
- missing
- unreadable
- oversized
- encrypted

Acceptance criteria:
- Special cases are detected before downstream parsing
- `specialCase` is populated
- Routing can reject or quarantine when needed

### Ticket 2.2 - Build rule-based classifier
Use current cheap signals first:
- extension
- MIME hint
- magic bytes or parser signature where available

Acceptance criteria:
- Produces a valid `FileKind`
- Does not require ML
- Falls back to `generic_text`, `generic_binary`, or `unknown` when uncertain

### Ticket 2.3 - Separate raw and final classification
Do not expose raw detection as final truth.

Examples:
- raw says `yaml`, final becomes `generic_text` if confidence is weak
- raw says `pdf`, final becomes `generic_binary` if content conflicts hard

Acceptance criteria:
- Downgrades are explicit
- `overwriteReason` or equivalent is recorded
- Logs/debugging can show both raw and final outputs

---

## Epic 3 - Routing integration

### Ticket 3.1 - Map FileKind to routing decisions
Initial routing decisions:
- `pdf` -> pdf lane
- `image` -> image lane
- `audio` -> audio lane
- `video` -> video lane
- `code` -> code/text lane
- `archive` -> archive lane
- `data` -> structured-data lane
- `email` -> email lane
- `generic_text` -> text lane
- `generic_binary` / `unknown` -> review or quarantine

Acceptance criteria:
- Routing is deterministic
- Unknown/binary handling is safe by default
- Existing tool selection can consume the routing decision

### Ticket 3.2 - Stop trusting extension alone
Where file tools are selected today using filename/extension heuristics, route through `FileKind` first.

Acceptance criteria:
- At least the main attachment/file ingestion path uses `FileKind`
- Disguised extension cases do not silently route to the wrong parser

### Ticket 3.3 - Improve agent/tool context
Pass file context in a structured way.

Example:
- not just "here is a file"
- but "classified as code, trusted, likely Python, route: code lane"

Acceptance criteria:
- Downstream agents/tools receive a compact structured file summary
- Tool choice mistakes decrease in ambiguous cases

---

## Epic 4 - Confidence behavior

### Ticket 4.1 - Add confidence semantics
Even in rule-based v1, keep confidence and trust explicit.

Acceptance criteria:
- `confidence` is always present
- `trusted` is derived from current mode and evidence strength
- Low-confidence outputs fall back honestly

### Ticket 4.2 - Define confidence modes without fully activating them
Define the product surface now:
- `safe`
- `balanced`
- `best_effort`

But only activate `balanced` in v1.

Acceptance criteria:
- Enum/types exist
- `balanced` is default
- Other modes are reserved and documented, not necessarily wired everywhere yet

---

## Epic 5 - Later evaluation

### Ticket 5.1 - Evaluate Magika only after v1 routing works
Do not introduce Magika until the routing contract proves useful and ambiguity remains a real problem.

Questions for later:
- Are rule-based signals insufficient on real attachment traffic?
- Are ambiguous text/code/document cases frequent enough to justify ML?
- Is attachment routing a meaningful bottleneck?

Acceptance criteria:
- Evaluation is driven by observed pain, not repo hype
- Any Magika adoption plugs into `FileKind`, not around it

---

## Suggested order

### Phase 1
- Ticket 1.1
- Ticket 1.2
- Ticket 2.1
- Ticket 2.2

### Phase 2
- Ticket 1.3
- Ticket 2.3
- Ticket 3.1
- Ticket 3.2

### Phase 3
- Ticket 3.3
- Ticket 4.1
- Ticket 4.2

### Phase 4
- Ticket 5.1

---

## Strategic note

The key design principle is:

**Treat file classification as a routing contract, not as a prediction toy.**

The most important behavior to preserve:
- honest uncertainty
- safe fallbacks
- clean routing
- explainable decisions

Not model cleverness.
