# Evidence Model

## Purpose

The bank is an evidence system, not a collection of polished claims. It must preserve the difference between what happened, what Ahmed personally did, what the wider organization achieved, and what lesson can reasonably be drawn.

## Canonical top-level structure

```json
{
  "schema_version": "1.0",
  "subject": "Ahmed Nasr",
  "last_updated": "YYYY-MM-DD",
  "source_of_truth": ["memory/master-cv-data.md"],
  "records": []
}
```

## Record fields

| Field | Meaning |
|---|---|
| `id` | Stable kebab-case ID, normally `exp-YYYY-organization-topic` |
| `title` | Plain-language story name |
| `organization`, `role`, `period` | Exact approved career identifiers |
| `status` | `verified`, `partial`, or `candidate` |
| `domains` | Sector or operating environment |
| `competencies` | Capabilities demonstrated by supported actions |
| `source_evidence` | Evidence objects with stable IDs, file/claim source, locator, and supporting claim |
| `situation` | Supported context, without invented stakes |
| `responsibility` | Ahmed's supported remit |
| `actions` | Specific first-person-capable actions |
| `outcomes` | Result statements with attribution and source references |
| `scope_metrics` | Numbers or scope facts with source references and verification state |
| `story_angles` | Interpretive angles for interviews or content, not historical facts |
| `questions_to_complete` | Missing details that would materially improve the story |
| `disclosure` | Privacy and external-reuse constraints |

## Source evidence object

```json
{
  "id": "src-network-pmo-1",
  "source": "memory/master-cv-data.md",
  "locator": "Professional Experience > Network International",
  "claim": "Built and led enterprise PMO from ground up managing 300+ concurrent projects across 8 countries."
}
```

The `claim` may be a concise faithful extract. Do not rewrite it into a stronger causal statement.

## Outcome object

```json
{
  "statement": "The platform scaled from 30,000 to 7 million daily orders during Ahmed's product leadership tenure.",
  "attribution": "shared",
  "source_refs": ["src-talabat-1"]
}
```

Use `direct` only when the source supports Ahmed delivering the result. Company scale, market growth, or broad program success is usually `shared` unless the evidence establishes sole ownership.

## Metric object

```json
{
  "label": "Concurrent projects",
  "value": "300+",
  "verified": true,
  "source_refs": ["src-network-pmo-1"]
}
```

Keep the original unit and qualifier. Do not turn `300+` into an exact count or infer percentages from two rounded values.

## Record status

- `verified`: every core claim needed for reuse is supported by an approved source or explicit user confirmation.
- `partial`: the role or project is real, but the record lacks material action, result, obstacle, or decision evidence.
- `candidate`: a potentially useful claim exists only in a draft, archive, or secondary note.

Candidate records may guide questions but cannot be used as external facts.

## Disclosure model

```json
{
  "classification": "private",
  "external_reuse_requires_approval": true,
  "constraints": ["Do not disclose confidential current-employer details."]
}
```

Supported classifications are `private`, `confidential`, and `public-approved`. The default is `private`.

## Claim transformation rules

| Source says | Safe transformation | Unsafe transformation |
|---|---|---|
| "contributing to platform scaling" | "contributed during the scale-up" | "scaled the company" |
| "$50M transformation budget" | "managed a $50M transformation budget" | "delivered $50M ROI" |
| "300+ concurrent projects" | "governed a 300+ project portfolio" | "delivered every project on time" |
| "170 users" | "rollout covered 170 users" | "achieved 100% adoption" |
| "designed architecture" | "designed the architecture" | "launched and grew the product" |

## Promotion rule

To promote a candidate fact into verified evidence, require one of:

1. Ahmed explicitly confirms it.
2. It appears in the canonical master CV or approved pending updates.
3. A primary artifact supplied by Ahmed supports it and Ahmed has not contradicted it.

Record the confirming source. Do not overwrite conflicting evidence silently.

