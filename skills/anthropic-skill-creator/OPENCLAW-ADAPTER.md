# OpenClaw Adapter for Anthropic Skill Creator

The Anthropic skill-creator framework was built for Claude Code (`claude -p`).
We run on OpenClaw. This adapter documents how to use the methodology on our platform.

## What Works As-Is
- SKILL.md writing guide and anatomy
- Skill directory structure (SKILL.md + scripts/ + references/ + assets/)
- Progressive disclosure pattern (metadata → body → bundled resources)
- Description optimization principles ("pushy" descriptions, trigger phrases)
- Test case design methodology (realistic prompts, edge cases)
- Grading assertions (objective checks on outputs)
- Eval viewer HTML (generate_review.py) for qualitative review

## What Needs Adaptation

### Running Test Cases
**Anthropic way:** `claude -p` with skill loaded as a command file
**OpenClaw way:** Use `sessions_spawn` with the skill context injected:

```
sessions_spawn(
  task="Read the skill at skills/<name>/SKILL.md, then execute this task: <eval prompt>",
  model="<target model>",
  mode="run"
)
```

For baseline (no skill), spawn without the skill read instruction.

### Parallel Execution
**Anthropic way:** Spawn subagents in same turn
**OpenClaw way:** Use `sessions_spawn` for each test case. They run in parallel automatically.

### Description Optimization Loop
**Anthropic way:** `scripts/run_loop.py` uses `claude -p`
**OpenClaw way:** Manual iteration:
1. Write 20 trigger eval queries (10 should-trigger, 10 should-not)
2. For each query, check if the skill description would cause selection
3. Identify failures, rewrite description, re-test
4. Repeat 3-5 times

### Grading
**Anthropic way:** Subagent reads agents/grader.md and evaluates
**OpenClaw way:** For objective checks, write bash scripts (file exists, size check, content validation). For subjective, present to Ahmed in Telegram.

## Quick Start: New Skill Creation

1. Define intent (what, when, expected output)
2. Write SKILL.md following the anatomy in this framework
3. Create 3 test prompts (realistic user requests)
4. Spawn test runs via sessions_spawn
5. Grade outputs (automated checks + Ahmed review)
6. Improve SKILL.md based on failures
7. Repeat until quality is stable
8. Optimize description with trigger eval queries

## Quick Start: Existing Skill Improvement

1. Review past runs/failures (check .learnings/, session history)
2. Identify patterns (common failures, wasted work, repeated scripts)
3. Update SKILL.md with fixes
4. Run 3 test cases to verify improvement
5. Optimize description if triggering is unreliable
