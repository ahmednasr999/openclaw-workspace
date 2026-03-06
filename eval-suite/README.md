# Agent Skill Evaluation Suite

Based on Philipp Schmid's framework: https://x.com/_philschmid/status/2029570052530360719

## Structure

```
eval-suite/
├── cv-optimizer/
│   ├── eval_prompts.json    # 10-12 test prompts
│   ├── deterministic.json   # Regex checks
│   └── judge_prompt.md     # LLM-as-judge criteria
├── job-hunter/
│   ├── eval_prompts.json
│   ├── deterministic.json
│   └── judge_prompt.md
├── content-creator/
│   ├── eval_prompts.json
│   ├── deterministic.json
│   └── judge_prompt.md
└── linkedin-writer/
    ├── eval_prompts.json
    ├── deterministic.json
    └── judge_prompt.md
```

---

## Step 1: Define Success Criteria

### CV Optimizer
- **Outcome:** ATS score >= 82%
- **Style:** Professional, quantified achievements
- **Efficiency:** < 30 seconds per CV

### Job Hunter
- **Outcome:** Finds relevant jobs, filters correctly
- **Style:** Actionable, organized output
- **Efficiency:** < 60 seconds per search

### Content Creator
- **Outcome:** Post is publish-ready
- **Style:** Ahmed's voice (direct, strategic, no fluff)
- **Efficiency:** < 2 minutes per post

---

## Step 2: Deterministic Checks (Example)

### CV Optimizer - deterministic.json
```json
{
  "checks": [
    {
      "name": "has_contact_info",
      "pattern": "(email|phone|linkedin|location)",
      "required": true
    },
    {
      "name": "has_quantification",
      "pattern": "(\\d+%?|[$€£]\\d+[kKmM]?|million|billion)",
      "required": true
    },
    {
      "name": "has_action_verbs",
      "pattern": "(led|managed|built|scaled|delivered|achieved)",
      "required": true
    }
  ]
}
```

### Content Creator - deterministic.json
```json
{
  "checks": [
    {
      "name": "no_em_dashes",
      "pattern": "—",
      "required": false,
      "fail_if_found": true
    },
    {
      "name": "has_cta",
      "pattern": "(what do you think|comments below|let's discuss)",
      "required": true
    },
    {
      "name": "linkedin_safe",
      "pattern": "(http|www\\.)",
      "required": false
    }
  ]
}
```

---

## Step 3: LLM-as-Judge Prompt

### judge_prompt.md (template)
```
You are evaluating a skill's output. Rate 1-10:

## Criteria
1. **Relevance** - Does it answer the prompt correctly?
2. **Tone** - Does it match the desired voice?
3. **Completeness** - Are all required elements present?
4. **Accuracy** - Are facts correct?

## Output Format
Provide JSON:
{
  "scores": {
    "relevance": 8,
    "tone": 9,
    "completeness": 7,
    "accuracy": 8
  },
  "total": 32,
  "max": 40,
  "verdict": "PASS|FAIL",
  "feedback": "specific suggestions"
}
```

---

## Step 4: Run Eval

### CLI Command
```bash
# Example: Test CV Optimizer
for prompt in $(cat eval-suite/cv-optimizer/eval_prompts.json | jq -r '.[].id'); do
  echo "Testing: $prompt"
  # Run agent with prompt
  # Run deterministic checks
  # Run LLM judge
  # Log result
done
```

---

## Continuous Improvement

1. Add failed evals to eval_prompts.json
2. Fix skill behavior
3. Re-run evals
4. Track score trends over time

---

## Quick Test Command

```bash
# Test single skill
echo "Test prompt" | openclaw exec -a cv-optimizer --prompt "@cv-optimizer"
```
