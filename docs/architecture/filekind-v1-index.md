# FileKind v1 - Index

## Purpose

This index is the single entry point for the FileKind v1 proposal.

Use it when you want to understand, plan, or implement the FileKind routing contract for OpenClaw without re-reading the full chat history.

---

## Reading order

### 1. Implementation brief
Start here for the strategic frame, scope boundary, and recommended implementation order.

- `docs/architecture/filekind-v1-implementation-brief.md`

### 2. Backlog
Use this for work breakdown, epics, tickets, and sequencing.

- `docs/architecture/filekind-v1-backlog.md`

### 3. Schema draft
Use this when turning the proposal into real code.

- `docs/architecture/filekind-v1.schema.ts`

---

## Recommended use

### If deciding whether to build this at all
Read:
1. implementation brief

### If planning the work
Read:
1. implementation brief
2. backlog

### If coding
Read:
1. implementation brief
2. schema draft
3. backlog

---

## Core decision

The proposal is intentionally narrow:

- build a **lean FileKind routing contract first**
- improve attachment and file routing safety
- preserve uncertainty honestly
- avoid direct Magika integration unless reality later proves it necessary

---

## Strategic principle

**Treat file classification as a routing contract, not as a prediction toy.**

That means:
- safe fallbacks over fake specificity
- `rawLabel` separate from `finalLabel`
- small canonical label set
- simple deterministic routing
- ML only later if rule-based routing proves insufficient

---

## Current artifact set

- Brief: `docs/architecture/filekind-v1-implementation-brief.md`
- Backlog: `docs/architecture/filekind-v1-backlog.md`
- Schema: `docs/architecture/filekind-v1.schema.ts`
- Index: `docs/architecture/filekind-v1-index.md`

---

## Status

This is a design package only.
No production code integration is implied by these documents.
