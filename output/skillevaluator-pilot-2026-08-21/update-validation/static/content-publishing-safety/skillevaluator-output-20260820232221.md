# SkillEvaluator Validation Report

**Status:** ✅ PASSED
**Profile:** external
**Policy digest:** `sha256:1caeb0bf9c2e044705f32fcdbd773fea4d835d895b4e0ab20d1aaa5e28acd660`
**Generated:** August 20, 2026 at 11:22 PM UTC

## Summary

| Metric | Value |
|--------|-------|
| Validator Results | 6 |
| ✅ Passed | 6 |
| ❌ Failed | 0 |
| ⚠️ Incomplete | 0 |
| Total Issues | 12 (4 medium) |

## Quality Score

| Skill | Score | Grade | Type | Correctness | Discoverability | Reliability | Efficiency |
|-------|-------|-------|------|-------------|-----------------|-------------|------------|
| content-publishing-safety | 89.8 | B | guide-only | 85.0 | 95.0 | 85.0 | 100.0 |

## Results

### ✅ Schema & Repository Governance
*Validate SKILL.md frontmatter and repository structure*

- [OK] **manifest_exists**: Found skill manifest: SKILL.md
- [OK] **frontmatter_valid**: Valid frontmatter for skill 'content-publishing-safety'
- [OK] **folder_hierarchy**: Valid general skill structure: skills/content-publishing-safety/
- [OK] **naming_convention**: Folder name 'content-publishing-safety' follows kebab-case convention
- [OK] **line_count**: SKILL.md within line limit (58/500)
- [OK] **body_heading**: Body contains a top-level heading
- [OK] **optional_files**: Found optional supporting files: references
- [OK] **name_consistency**: Directory name matches frontmatter: 'content-publishing-safety'
- [OK] **author_format**: Valid author format: Ahmed Nasr <ahmednasr999@gmail.com>

**Non-blocking findings: 4**

| Severity | Issue | Location |
|----------|-------|----------|
| [MED] MEDIUM | Missing recommended section: '## Instructions' | <code>/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md</code> |
| [MED] MEDIUM | Missing recommended section: '## Examples' | <code>/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md</code> |
| [LOW] LOW | Unexpected 'checklists' in skill root | <code>/root/.openclaw/workspace/skills/content-publishing-safety/checklists</code> |
| [LOW] LOW | Unexpected 'examples' in skill root | <code>/root/.openclaw/workspace/skills/content-publishing-safety/examples</code> |

<details>
<summary>View Details</summary>

**1. Missing recommended section: '## Instructions'**
- File: `/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md`
- Check: `body_recommended_section`
- Fix: Consider adding a '## Instructions' or '## Usage' section. Per agentskills.io the body format is unrestricted, so this is a convention nudge — it also gives the quality scorer a stable anchor for instruction-quality heuristics.

**2. Missing recommended section: '## Examples'**
- File: `/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md`
- Check: `body_recommended_section`
- Fix: Consider adding a '## Examples' section. If examples are already inline under instructions, this can be skipped.

**3. Unexpected 'checklists' in skill root**
- File: `/root/.openclaw/workspace/skills/content-publishing-safety/checklists`
- Check: `unexpected_file`
- Fix: Consider moving to one of: agents/, assets/, config/, evals/, references/, scripts/, tests/, tools/. To allow additional directories, set $SKILLEVALUATOR_SCHEMA_ALLOWED_DIRS.

**4. Unexpected 'examples' in skill root**
- File: `/root/.openclaw/workspace/skills/content-publishing-safety/examples`
- Check: `unexpected_file`
- Fix: Consider moving to one of: agents/, assets/, config/, evals/, references/, scripts/, tests/, tools/. To allow additional directories, set $SKILLEVALUATOR_SCHEMA_ALLOWED_DIRS.

</details>


### ✅ PII Scan
*Detect PII and local identifiers*

- [OK] **pii_scan_start**: Scanning 9 files for PII
- [OK] **pii_detection**: No PII detected in 9 files (emails, SSNs, phone numbers, paths)

### ✅ License Compliance
*Validate license compliance for Skills, Rules, and Workflows*

- No license detected in any tier

### ✅ Unicode Smuggling Detection
*Detect invisible Unicode characters and ASCII smuggling*

- [OK] **unicode_scan**: No invisible Unicode characters detected in 9 file(s)

### ✅ B QUALITY
*Skill quality scoring across Correctness (35%), Discoverability (25%), Reliability (25%), and Efficiency (15%)*

**Overall: 89.8/100 (Grade: B)** | Skill Type: guide-only

| Dimension | Score | Weight |
|-----------|-------|--------|
| Correctness | 85.0 | 35% |
| Discoverability | 95.0 | 25% |
| Reliability | 85.0 | 25% |
| Efficiency | 100.0 | 15% |

- [OK] **quality_score**: Score: 89.8/100 (Grade: B)

**Non-blocking findings: 7**

| Severity | Issue | Location |
|----------|-------|----------|
| [LOW] LOW | No examples provided | <code>/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md</code> |
| [MED] MEDIUM | SKILL_SPEC recommended field missing: 'version' | <code>/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md</code> |
| [MED] MEDIUM | SKILL_SPEC recommended field missing: 'metadata.tags' | <code>/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md</code> |
| [LOW] LOW | No '## Purpose' section | <code>/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md</code> |
| [LOW] LOW | No prerequisites/requirements documented | <code>/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md</code> |
| [LOW] LOW | No limitations documented | <code>/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md</code> |
| [LOW] LOW | No troubleshooting section documented | <code>/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md</code> |

<details>
<summary>View Details</summary>

**1. No examples provided**
- File: `/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md`
- Check: `quality_correctness`
- Fix: Add example usage with code blocks

**2. SKILL_SPEC recommended field missing: 'version'**
- File: `/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md`
- Check: `quality_correctness`
- Fix: Add 'version' to frontmatter — Semantic version (e.g., "1.0.0")

**3. SKILL_SPEC recommended field missing: 'metadata.tags'**
- File: `/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md`
- Check: `quality_correctness`
- Fix: Add 'tags' under metadata: — Categorization tags (under metadata:, list of 1-5 items)

**4. No '## Purpose' section**
- File: `/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md`
- Check: `quality_discoverability`
- Fix: Add purpose section to clarify use cases

**5. No prerequisites/requirements documented**
- File: `/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md`
- Check: `quality_reliability`
- Fix: Document dependencies, API keys, or setup needed

**6. No limitations documented**
- File: `/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md`
- Check: `quality_reliability`
- Fix: Add '## Limitations' section with known issues/constraints

**7. No troubleshooting section documented**
- File: `/root/.openclaw/workspace/skills/content-publishing-safety/SKILL.md`
- Check: `quality_reliability`
- Fix: Add '## Troubleshooting' with Error/Cause/Solution patterns

</details>


### ✅ SCRIPT_LINT
*AST-based code quality checks for skill scripts*

- [OK] **lint**: No scripts/ directory found

---
*Generated by SkillEvaluator*