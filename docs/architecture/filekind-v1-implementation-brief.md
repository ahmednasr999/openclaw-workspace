# FileKind v1 - Implementation Brief

## Purpose

Introduce a lean `FileKind` routing contract for OpenClaw so file and attachment handling becomes safer, more explainable, and less dependent on filename extensions.

This is **not** a proposal to build a full ingestion intelligence subsystem.
It is a focused v1 that improves routing discipline first.

---

## Why now

Current risk pattern:
- tools often infer file handling from extension or shallow heuristics
- renamed or disguised files can route to the wrong parser
- ambiguous files lack a stable contract for downstream decisions
- agents/tools receive weak file context

Desired outcome:
- classify files into a small canonical set
- route them consistently
- preserve uncertainty honestly
- support future deeper detection later, without redesign

---

## Strategic decision

**Borrow the contract, not the Magika dependency, first.**

Magika is useful as a design reference for:
- canonical file classification
- confidence-aware routing
- explicit fallbacks
- raw vs final output separation

But v1 should stay rule-based and simple.

---

## Scope for v1

### In scope
- canonical `FileKind` schema
- small canonical label set
- rule-based classification from existing signals
- special-case detection
- routing decisions for core lanes
- honest fallbacks
- `rawLabel` vs `finalLabel`
- default `balanced` confidence mode only

### Out of scope
- Magika integration
- large file taxonomy
- ML-driven classification pipeline
- deep recursive archive/container inspection
- per-type threshold tuning
- multiple production confidence modes

---

## Core design rules

1. **File classification is a routing contract, not a prediction toy**
2. **Keep `rawLabel` and `finalLabel` separate**
3. **Prefer safe fallback over fake specificity**
4. **Special cases bypass classification**
5. **Do not trust extension alone**
6. **Keep v1 small enough to ship**

---

## Canonical label set for v1

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

This is intentionally small.
It should cover the vast majority of routing decisions without overfitting the taxonomy.

---

## Required schema fields

Minimum useful fields:
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

Reference draft:
- `docs/architecture/filekind-v1.schema.ts`

---

## Special cases

These must short-circuit classification:
- empty
- directory
- symlink
- missing
- unreadable
- oversized
- encrypted

If any of these apply, routing should prioritize safety and avoid pretending a normal file classification exists.

---

## Routing behavior

Initial routing map:
- `pdf` -> pdf lane
- `image` -> image lane
- `audio` -> audio lane
- `video` -> video lane
- `code` -> code/text lane
- `archive` -> archive lane
- `data` -> structured-data lane
- `email` -> email lane
- `generic_text` -> text lane
- `generic_binary` -> review/quarantine lane
- `unknown` -> review/quarantine lane

The goal is deterministic routing, not perfect file typing.

---

## Classification approach for v1

Use existing cheap signals only:
- extension
- MIME hints
- magic bytes if available
- parser signature if available
- filesystem state

Do not add ML in v1.

If the evidence is weak or conflicting:
- downgrade to `generic_text`
- downgrade to `generic_binary`
- or return `unknown`

---

## Confidence handling

Define the product surface now:
- `safe`
- `balanced`
- `best_effort`

But only activate `balanced` in v1.

This preserves future extension without multiplying behavior during first implementation.

---

## Recommended implementation order

### Phase 1
1. Define canonical `FileKind` schema
2. Define canonical label set
3. Build special-case detector
4. Build rule-based classifier

### Phase 2
5. Add evidence model
6. Add raw vs final downgrade behavior
7. Add routing decision map
8. Replace extension-only routing on the main attachment path

### Phase 3
9. Improve agent/tool file context
10. Add confidence semantics
11. Reserve additional confidence modes

### Phase 4
12. Re-evaluate whether Magika or similar is needed

---

## Acceptance test for v1

v1 is successful if OpenClaw can do all of the following reliably:
- tell a PDF from an image from code from an archive from generic text/binary
- detect special cases safely
- route files without trusting the extension alone
- explain why a file was routed a certain way
- downgrade uncertain cases honestly
- expose structured file context to downstream tools/agents

If it cannot do those things, adding Magika early would only hide weak product design behind a stronger detector.

---

## Decision for future work

Only consider direct Magika integration later if:
- attachment ambiguity remains a real operational bottleneck
- rule-based classification proves insufficient on real traffic
- there is clear value in higher-fidelity content detection

If those conditions are not met, the contract alone may be enough.

---

## Related files

- Backlog: `docs/architecture/filekind-v1-backlog.md`
- Schema draft: `docs/architecture/filekind-v1.schema.ts`

---

## One-line takeaway

**Ship FileKind v1 as a lean, uncertainty-aware routing contract first. Add intelligence later only if reality forces it.**
