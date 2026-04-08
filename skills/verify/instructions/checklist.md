# Verification Checklist - Detailed

## 1. Completeness
**Question:** Did the agent do what was asked? All of it?

**Check for:**
- [ ] All requirements from the original task are addressed
- [ ] No TODO, FIXME, or placeholder comments left behind
- [ ] No "I'll do this later" promises in the output
- [ ] If task said "create X and Y", both X and Y exist
- [ ] Edge cases mentioned in the task are handled

**Evidence command:**
```bash
grep -rn "TODO\|FIXME\|HACK\|XXX\|placeholder\|coming soon" <changed_files>
```

**FAIL if:** Core requirements are missing. A TODO in a non-critical spot is PARTIAL.

---

## 2. Correctness
**Question:** Does it actually work?

**Check for:**
- [ ] Python scripts parse without syntax errors: `python3 -c "import ast; ast.parse(open('file.py').read())"`
- [ ] Shell scripts pass syntax check: `bash -n script.sh`
- [ ] File paths referenced in code actually exist: `ls <path>`
- [ ] JSON/YAML files are valid: `python3 -m json.tool file.json` or `python3 -c "import yaml; yaml.safe_load(open('file.yaml'))"`
- [ ] If a script is runnable, try `--help` or `--dry-run`

**FAIL if:** Code has syntax errors or references non-existent files.

---

## 3. Safety
**Question:** Could this cause damage?

**Check for:**
- [ ] No hardcoded credentials, API keys, or tokens (grep for patterns)
- [ ] No `rm -rf` without safeguards
- [ ] No unguarded file overwrites (should check before clobbering)
- [ ] Cron schedules are reasonable (not every second/minute without good reason)
- [ ] No unbounded loops that could run forever
- [ ] Network calls have timeouts
- [ ] No world-readable permission on sensitive files

**Evidence command:**
```bash
grep -rn "password\|secret\|api_key\|token\|Bearer\|sk-\|hf_\|ntn_" <changed_files>
grep -rn "rm -rf\|rm -r\|shutil.rmtree" <changed_files>
```

**FAIL if:** Any credential exposure or destructive operation without confirmation. Safety failures override all other checks.

---

## 4. Integration
**Question:** Does it play nice with the existing system?

**Check for:**
- [ ] Imports reference installed packages: `python3 -c "import <module>"`
- [ ] No conflicting cron schedules (check existing crons)
- [ ] File writes go to expected directories
- [ ] Follows existing naming conventions (check nearby files)
- [ ] Doesn't silently override existing functionality

**FAIL if:** Would break an existing workflow or depends on missing packages.

---

## 5. Documentation
**Question:** Would future-me understand this?

**Check for:**
- [ ] New scripts have a docstring or header comment explaining purpose
- [ ] If a new tool/workflow was created, TOOLS.md or AGENTS.md was updated
- [ ] If a skill was created/modified, SKILL.md accurately describes it
- [ ] If cron job was created, schedule and purpose are documented

**FAIL if:** A significant new system was created with zero documentation. Minor scripts without docs = PARTIAL.

---

## 6. Edge Cases
**Question:** What breaks this?

**Check for:**
- [ ] Empty input handling (empty files, missing args, null values)
- [ ] Network failure handling (API calls have try/except or timeout)
- [ ] File not found handling (checked before open)
- [ ] Large input handling (no unbounded memory consumption)
- [ ] Concurrent execution safety (if applicable - cron jobs, shared files)

**FAIL if:** The first unexpected input would crash the script. Robust error handling with poor coverage = PARTIAL.
