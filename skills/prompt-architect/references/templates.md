# Prompt Templates

Load only the relevant template.

## General LLM

```text
Objective: [specific outcome]

Context:
- [relevant facts]

Constraints:
- [must do]
- [must not do]

Output format:
- [sections / length / JSON schema / tone]

Done when:
- [observable success condition]
```

## Reasoning LLM

```text
[Task in one or two sentences.]

Return only:
- [final format]
- [any assumptions or uncertainty if needed]

Do not include hidden reasoning or scratchwork.
```

## Coding Agent

```text
Goal:
[Target state]

Starting context:
- Repo/path: [path]
- Relevant files: [files]
- Current behavior: [behavior]

Scope:
- You may edit: [paths]
- Do not touch: [paths/config/secrets]
- Ask before: deleting files, adding dependencies, changing schemas, touching credentials/config.

Implementation requirements:
- [requirements]

Verification:
- Run: [test/build/lint]
- If a command cannot run, explain why and inspect the smallest equivalent evidence.

Stop conditions:
- Stop when verification passes and summarize changed files.
- Stop and ask if scope needs to expand or an irreversible action is required.
```

## Browser / Computer-Use Agent

```text
Outcome:
[What to accomplish]

Constraints:
- Use only: [sites/apps/accounts]
- Do not: purchase, submit, send, delete, or change settings without approval.
- Prefer official/current sources.

Deliverable:
- [summary/table/file]
- Include source URLs or screenshots where relevant.

Stop when:
- [objective complete]
- Ask before any irreversible action or credential prompt.
```

## Image Generation

```text
[subject], [environment], [composition], [style], [lighting], [mood], [details], [quality/rendering cues], [aspect ratio/parameters]

Negative: [unwanted elements]
```

## Reference Image Editing

```text
Edit the attached reference image.

Change only:
- [specific delta]

Keep unchanged:
- identity, composition, colors, background, lighting, clothing, text, proportions unless listed above.

Output:
- [format/aspect/style]
```

## Research Tool

```text
Mode: [search / analyze / compare]
Question: [specific question]

Use:
- Current, primary sources where possible.
- Cite sources for factual claims.
- Mark uncertain claims as [uncertain].

Output:
- [table/brief/recommendation]
- Include bottom-line answer first.
```

## Workflow Automation

```text
Build a workflow that:
1. Trigger: [app + event]
2. Filter/condition: [rules]
3. Actions: [app + action + field mapping]
4. Error handling: [retry/notify/log]

Assume connected apps are already authenticated. Ask before sending live messages, deleting data, or changing production records.
```
