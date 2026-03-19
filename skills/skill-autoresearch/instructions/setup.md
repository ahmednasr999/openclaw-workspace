# Setup - Autoresearch

## Step 1: Identify the Target Skill

Ask the user or infer from context:
- Which skill to optimize?
- Where is the SKILL.md? (check `skills/[name]/SKILL.md`)

Read the entire skill, including sub-files if it's modular (instructions/, eval/, examples/).

## Step 2: Define Test Inputs

The skill needs realistic inputs to test against. Ask the user:
- "What are 3-5 realistic scenarios this skill should handle?"
- Each scenario = one test run

For common skill types, suggest defaults:
- **CV builder**: 3 different JDs (tech, healthcare, PMO)
- **LinkedIn writer**: 3 different topics (story, contrarian take, list post)
- **Content pipeline**: 3 different platforms (LinkedIn, X, Reddit)
- **Email writer**: 3 different contexts (cold outreach, follow-up, reply)

**Minimum 3 test inputs. Maximum 5.** More than 5 makes each iteration too slow.

## Step 3: Build the Evaluation Checklist

The checklist defines what "good" looks like. Each item is a **binary yes/no question**.

Rules for good checklist questions:
- Must be objectively answerable (no "is it good?")
- Must check ONE specific thing per question
- Must catch a real failure mode (not theoretical)
- 3-6 questions is the sweet spot
- More than 6 and the skill starts gaming the checklist

**Ask the user:** "What does a perfect output from this skill look like?"

Then help them turn that into yes/no questions. Use the template at `eval/checklist-template.md`.

**If the skill already has an eval/ folder:** Load the existing checklist and use it as the starting point. The modular skill structure we use already has eval checklists built in.

## Step 4: Create the Working Directory

```
/tmp/autoresearch-[skill-name]/
├── baseline/          # Baseline outputs
├── iterations/        # Output from each iteration
├── log.tsv            # Iteration log
├── checklist.md       # The active checklist
└── skill-snapshot.md  # Current version of skill being modified
```

Copy the target skill's instruction files to `skill-snapshot.md` (concatenated). This is what gets modified. The original stays untouched.
