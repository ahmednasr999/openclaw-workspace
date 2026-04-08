# Verification Agent Skill

> Independent quality gate for sub-agent work. The sub-agent cannot grade itself.

## When to Use
This skill is invoked by the CEO agent AFTER a sub-agent completes work. It is NOT self-invoked by the working agent.

**Trigger conditions (ANY = verify):**
- Sub-agent touched 3+ files
- Sub-agent created a new script (.py, .sh, .js)
- Sub-agent modified a cron job or SKILL.md
- Sub-agent changed MEMORY.md, SOUL.md, TOOLS.md, or AGENTS.md
- Task was tagged critical or high-priority

**Skip conditions (ALL must be true to skip):**
- Simple file reads or appends only
- Content writing (posts, drafts) - has own review flow
- Config changes under 5 lines
- Research-only tasks with no deliverable

## Workflow

### Step 1: Gather Evidence
Run these commands to collect what changed:
```bash
# Get the diff (last N commits from sub-agent, or working tree changes)
cd /root/.openclaw/workspace
git diff HEAD~1 --stat
git diff HEAD~1
```

If the sub-agent didn't commit, check working tree:
```bash
git status --short
git diff
```

List all changed files and note their types (script, config, skill, memory, docs).

### Step 2: Run the 6-Point Checklist

Read `instructions/checklist.md` for the full checklist. For each check, collect EVIDENCE - don't just say pass/fail.

**Evidence means:**
- Completeness: Compare task description against actual changes. List anything missing.
- Correctness: Run the script/code if possible (`python3 script.py --help` or `bash -n script.sh`). Check file paths exist with `ls`.
- Safety: `grep -rn "password\|secret\|api_key\|token" <changed_files>` (exclude legitimate config references)
- Integration: Check imports exist, dependencies installed, no conflicting cron schedules
- Documentation: Check if TOOLS.md/AGENTS.md were updated when they should have been
- Edge Cases: Read the code for error handling, empty input guards, timeout handling

### Step 3: Assign Verdict

Based on evidence:
- **PASS** (6/6 checks pass) - Accept work
- **PARTIAL** (4-5/6 pass, no safety failure) - Accept with noted issues
- **FAIL** (3 or fewer pass, OR any safety failure) - Reject

### Step 4: Write Report

Write the verdict to `memory/verification-logs/YYYY-MM-DD.md` (append if file exists).

Format: Use template from `templates/verdict.md`

### Step 5: Notify

- **PASS**: Post to CEO General (topic 10): "✅ Verification PASS: [task summary]"
- **PARTIAL**: Post: "⚠️ Verification PARTIAL: [task summary] - [issues]"
- **FAIL**: Post: "❌ Verification FAIL: [task summary] - [fix list]"

On FAIL: Include the specific fix actions needed. If this is the second FAIL for the same task, add "⚡ ESCALATE: Same task failed verification twice - needs Ahmed's review"

## Anti-Gaming Rules
- You receive ONLY the git diff and the original task description
- You do NOT see the working agent's self-assessment
- You judge the OUTPUT, not the intent
- "Almost done" is not PASS. "Works but no error handling" is PARTIAL at best.
