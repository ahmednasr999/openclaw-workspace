# SkillEvaluator Validation Report

**Status:** ❌ FAILED
**Profile:** external
**Policy digest:** `sha256:1caeb0bf9c2e044705f32fcdbd773fea4d835d895b4e0ab20d1aaa5e28acd660`
**Generated:** August 20, 2026 at 10:39 PM UTC

## Summary

| Metric | Value |
|--------|-------|
| Validator Results | 6 |
| ✅ Passed | 5 |
| ❌ Failed | 1 |
| ⚠️ Incomplete | 0 |
| Total Issues | 15 (1 high, 5 medium) |

## Quality Score

| Skill | Score | Grade | Type | Correctness | Discoverability | Reliability | Efficiency |
|-------|-------|-------|------|-------------|-----------------|-------------|------------|
| gateway-runtime-safety | 88.0 | B | guide-only | 80.0 | 95.0 | 85.0 | 100.0 |

## Results

### ❌ Schema & Repository Governance
*Validate SKILL.md frontmatter and repository structure*

**1 errors, 5 warnings**

| Severity | Issue | Location |
|----------|-------|----------|
| [MED] MEDIUM | Missing recommended section: '## Instructions' | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md</code> |
| [MED] MEDIUM | Missing recommended section: '## Examples' | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md</code> |
| [LOW] LOW | Unexpected 'checklists' in skill root | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/checklists</code> |
| [LOW] LOW | Unexpected 'SKILL.md.bak-20260525-approved-escalation' in skill root | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md.bak-20260525-approved-escalation</code> |
| [LOW] LOW | Unexpected 'examples' in skill root | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/examples</code> |
| [HIGH] HIGH | Author not specified in metadata | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md</code> |

<details>
<summary>View Details</summary>

**1. Missing recommended section: '## Instructions'**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md`
- Check: `body_recommended_section`
- Fix: Consider adding a '## Instructions' or '## Usage' section. Per agentskills.io the body format is unrestricted, so this is a convention nudge — it also gives the quality scorer a stable anchor for instruction-quality heuristics.

**2. Missing recommended section: '## Examples'**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md`
- Check: `body_recommended_section`
- Fix: Consider adding a '## Examples' section. If examples are already inline under instructions, this can be skipped.

**3. Unexpected 'checklists' in skill root**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/checklists`
- Check: `unexpected_file`
- Fix: Consider moving to one of: agents/, assets/, config/, evals/, references/, scripts/, tests/, tools/. To allow additional directories, set $SKILLEVALUATOR_SCHEMA_ALLOWED_DIRS.

**4. Unexpected 'SKILL.md.bak-20260525-approved-escalation' in skill root**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md.bak-20260525-approved-escalation`
- Check: `unexpected_file`
- Fix: Consider moving to one of: agents/, assets/, config/, evals/, references/, scripts/, tests/, tools/. To allow additional directories, set $SKILLEVALUATOR_SCHEMA_ALLOWED_DIRS.

**5. Unexpected 'examples' in skill root**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/examples`
- Check: `unexpected_file`
- Fix: Consider moving to one of: agents/, assets/, config/, evals/, references/, scripts/, tests/, tools/. To allow additional directories, set $SKILLEVALUATOR_SCHEMA_ALLOWED_DIRS.

**6. Author not specified in metadata**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md`
- Check: `author_missing`
- Fix: Add 'metadata.author' field with format 'Name <email@example.com>'

</details>


### ✅ PII Scan
*Detect PII and local identifiers*

- [OK] **pii_scan_start**: Scanning 11 files for PII
- [OK] **pii_detection**: No PII detected in 11 files (emails, SSNs, phone numbers, paths)

### ✅ License Compliance
*Validate license compliance for Skills, Rules, and Workflows*

- No license detected in any tier

### ✅ Unicode Smuggling Detection
*Detect invisible Unicode characters and ASCII smuggling*

- [OK] **unicode_scan**: No invisible Unicode characters detected in 11 file(s)

### ✅ B QUALITY
*Skill quality scoring across Correctness (35%), Discoverability (25%), Reliability (25%), and Efficiency (15%)*

**Overall: 88.0/100 (Grade: B)** | Skill Type: guide-only

| Dimension | Score | Weight |
|-----------|-------|--------|
| Correctness | 80.0 | 35% |
| Discoverability | 95.0 | 25% |
| Reliability | 85.0 | 25% |
| Efficiency | 100.0 | 15% |

- [OK] **quality_score**: Score: 88.0/100 (Grade: B)

**Non-blocking findings: 8**

| Severity | Issue | Location |
|----------|-------|----------|
| [LOW] LOW | No examples provided | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md</code> |
| [MED] MEDIUM | SKILL_SPEC recommended field missing: 'version' | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md</code> |
| [MED] MEDIUM | SKILL_SPEC recommended field missing: 'metadata.author' | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md</code> |
| [MED] MEDIUM | SKILL_SPEC recommended field missing: 'metadata.tags' | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md</code> |
| [LOW] LOW | No '## Purpose' section | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md</code> |
| [LOW] LOW | No prerequisites/requirements documented | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md</code> |
| [LOW] LOW | No limitations documented | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md</code> |
| [LOW] LOW | No troubleshooting section documented | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md</code> |

<details>
<summary>View Details</summary>

**1. No examples provided**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md`
- Check: `quality_correctness`
- Fix: Add example usage with code blocks

**2. SKILL_SPEC recommended field missing: 'version'**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md`
- Check: `quality_correctness`
- Fix: Add 'version' to frontmatter — Semantic version (e.g., "1.0.0")

**3. SKILL_SPEC recommended field missing: 'metadata.author'**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md`
- Check: `quality_correctness`
- Fix: Add 'author' under metadata: — Author name or team (under metadata:)

**4. SKILL_SPEC recommended field missing: 'metadata.tags'**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md`
- Check: `quality_correctness`
- Fix: Add 'tags' under metadata: — Categorization tags (under metadata:, list of 1-5 items)

**5. No '## Purpose' section**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md`
- Check: `quality_discoverability`
- Fix: Add purpose section to clarify use cases

**6. No prerequisites/requirements documented**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md`
- Check: `quality_reliability`
- Fix: Document dependencies, API keys, or setup needed

**7. No limitations documented**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md`
- Check: `quality_reliability`
- Fix: Add '## Limitations' section with known issues/constraints

**8. No troubleshooting section documented**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/gateway-runtime-safety/SKILL.md`
- Check: `quality_reliability`
- Fix: Add '## Troubleshooting' with Error/Cause/Solution patterns

</details>


### ✅ SCRIPT_LINT
*AST-based code quality checks for skill scripts*

- [OK] **lint**: No scripts/ directory found

---
*Generated by SkillEvaluator*