# SkillEvaluator Validation Report

**Status:** ❌ FAILED
**Profile:** external
**Policy digest:** `sha256:1caeb0bf9c2e044705f32fcdbd773fea4d835d895b4e0ab20d1aaa5e28acd660`
**Generated:** August 20, 2026 at 10:39 PM UTC

## Summary

| Metric | Value |
|--------|-------|
| Validator Results | 6 |
| ✅ Passed | 3 |
| ❌ Failed | 3 |
| ⚠️ Incomplete | 0 |
| Total Issues | 20 (3 high, 6 medium) |

## Quality Score

| Skill | Score | Grade | Type | Correctness | Discoverability | Reliability | Efficiency |
|-------|-------|-------|------|-------------|-----------------|-------------|------------|
| executive-cv-builder | 81.2 | B | resource-based | 85.0 | 70.0 | 85.0 | 85.0 |

## Results

### ❌ Schema & Repository Governance
*Validate SKILL.md frontmatter and repository structure*

**1 errors, 6 warnings**

| Severity | Issue | Location |
|----------|-------|----------|
| [MED] MEDIUM | Missing recommended section: '## Instructions' | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md</code> |
| [MED] MEDIUM | Missing recommended section: '## Examples' | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md</code> |
| [LOW] LOW | Unexpected 'instructions' in skill root | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/instructions</code> |
| [LOW] LOW | Unexpected 'templates' in skill root | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/templates</code> |
| [LOW] LOW | Unexpected 'eval' in skill root | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/eval</code> |
| [LOW] LOW | Unexpected 'examples' in skill root | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/examples</code> |
| [HIGH] HIGH | Author not specified in metadata | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md</code> |

<details>
<summary>View Details</summary>

**1. Missing recommended section: '## Instructions'**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md`
- Check: `body_recommended_section`
- Fix: Consider adding a '## Instructions' or '## Usage' section. Per agentskills.io the body format is unrestricted, so this is a convention nudge — it also gives the quality scorer a stable anchor for instruction-quality heuristics.

**2. Missing recommended section: '## Examples'**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md`
- Check: `body_recommended_section`
- Fix: Consider adding a '## Examples' section. If examples are already inline under instructions, this can be skipped.

**3. Unexpected 'instructions' in skill root**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/instructions`
- Check: `unexpected_file`
- Fix: Consider moving to one of: agents/, assets/, config/, evals/, references/, scripts/, tests/, tools/. To allow additional directories, set $SKILLEVALUATOR_SCHEMA_ALLOWED_DIRS.

**4. Unexpected 'templates' in skill root**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/templates`
- Check: `unexpected_file`
- Fix: Consider moving to one of: agents/, assets/, config/, evals/, references/, scripts/, tests/, tools/. To allow additional directories, set $SKILLEVALUATOR_SCHEMA_ALLOWED_DIRS.

**5. Unexpected 'eval' in skill root**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/eval`
- Check: `unexpected_file`
- Fix: Consider moving to one of: agents/, assets/, config/, evals/, references/, scripts/, tests/, tools/. To allow additional directories, set $SKILLEVALUATOR_SCHEMA_ALLOWED_DIRS.

**6. Unexpected 'examples' in skill root**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/examples`
- Check: `unexpected_file`
- Fix: Consider moving to one of: agents/, assets/, config/, evals/, references/, scripts/, tests/, tools/. To allow additional directories, set $SKILLEVALUATOR_SCHEMA_ALLOWED_DIRS.

**7. Author not specified in metadata**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md`
- Check: `author_missing`
- Fix: Add 'metadata.author' field with format 'Name <email@example.com>'

</details>


### ❌ PII Scan
*Detect PII and local identifiers*

**1 errors, 0 warnings**

| Severity | Issue | Location |
|----------|-------|----------|
| [HIGH] HIGH | Non-placeholder email address: ahmednasr999@gmail.com | <code>eval/post-gen-checks.md:26</code> |

<details>
<summary>View Details</summary>

**1. Non-placeholder email address: ahmednasr999@gmail.com**
- File: `eval/post-gen-checks.md:26`
- Check: `emails`
- Content: `CONTACT=$(echo "$TEXT" | grep -c 'ahmednasr999@gmail.com'...`
- Fix: Remove the address or use a placeholder like user@example.com

</details>


### ✅ License Compliance
*Validate license compliance for Skills, Rules, and Workflows*

- No license detected in any tier

### ✅ Unicode Smuggling Detection
*Detect invisible Unicode characters and ASCII smuggling*

- [OK] **unicode_scan**: No invisible Unicode characters detected in 14 file(s)

### ❌ B QUALITY
*Skill quality scoring across Correctness (35%), Discoverability (25%), Reliability (25%), and Efficiency (15%)*

**Overall: 81.2/100 (Grade: B)** | Skill Type: resource-based

| Dimension | Score | Weight |
|-----------|-------|--------|
| Correctness | 85.0 | 35% |
| Discoverability | 70.0 | 25% |
| Reliability | 85.0 | 25% |
| Efficiency | 85.0 | 15% |

**1 errors, 10 warnings**

| Severity | Issue | Location |
|----------|-------|----------|
| [MED] MEDIUM | SKILL_SPEC recommended field missing: 'version' | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md</code> |
| [MED] MEDIUM | SKILL_SPEC recommended field missing: 'metadata.author' | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md</code> |
| [MED] MEDIUM | SKILL_SPEC recommended field missing: 'metadata.tags' | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md</code> |
| [LOW] LOW | Description very long (793 chars, recommend 50-150) | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md</code> |
| [MED] MEDIUM | Description uses first/second person | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md</code> |
| [LOW] LOW | Skill uses exclusivity language that conflicts with composability | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md</code> |
| [LOW] LOW | No '## Purpose' section | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md</code> |
| [LOW] LOW | No prerequisites/requirements documented | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md</code> |
| [LOW] LOW | No limitations documented | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md</code> |
| [LOW] LOW | No troubleshooting section documented | <code>/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md</code> |
| ... | *1 more issues* | |

<details>
<summary>View Details</summary>

**1. SKILL_SPEC recommended field missing: 'version'**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md`
- Check: `quality_correctness`
- Fix: Add 'version' to frontmatter — Semantic version (e.g., "1.0.0")

**2. SKILL_SPEC recommended field missing: 'metadata.author'**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md`
- Check: `quality_correctness`
- Fix: Add 'author' under metadata: — Author name or team (under metadata:)

**3. SKILL_SPEC recommended field missing: 'metadata.tags'**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md`
- Check: `quality_correctness`
- Fix: Add 'tags' under metadata: — Categorization tags (under metadata:, list of 1-5 items)

**4. Description very long (793 chars, recommend 50-150)**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md`
- Check: `quality_discoverability`
- Fix: Keep descriptions concise for progressive disclosure

**5. Description uses first/second person**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md`
- Check: `quality_discoverability`
- Fix: Use third person: 'Processes files' not 'I can process'

**6. Skill uses exclusivity language that conflicts with composability**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md`
- Check: `quality_discoverability`
- Fix: Skills should work alongside others (composability principle)

**7. No '## Purpose' section**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md`
- Check: `quality_discoverability`
- Fix: Add purpose section to clarify use cases

**8. No prerequisites/requirements documented**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md`
- Check: `quality_reliability`
- Fix: Document dependencies, API keys, or setup needed

**9. No limitations documented**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md`
- Check: `quality_reliability`
- Fix: Add '## Limitations' section with known issues/constraints

**10. No troubleshooting section documented**
- File: `/root/.openclaw/workspace/output/skillevaluator-pilot-2026-08-21/skills/executive-cv-builder/SKILL.md`
- Check: `quality_reliability`
- Fix: Add '## Troubleshooting' with Error/Cause/Solution patterns

*... and 1 more issues*

</details>


### ✅ SCRIPT_LINT
*AST-based code quality checks for skill scripts*

- [OK] **lint**: No scripts/ directory found

---
*Generated by SkillEvaluator*