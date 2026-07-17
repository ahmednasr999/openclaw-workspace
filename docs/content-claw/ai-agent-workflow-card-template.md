# AI Agent Workflow Card Template

## Source pattern

X post inspected 2026-05-01:
`https://x.com/ludoviccreator/status/2049855050613240060`

The post showed horizontal dashboard-style examples for visualizing an AI agent or automation with inputs, logic, tools, steps, outputs, guardrails, and human escalation.

Useful pattern: the anatomy of the card, not the dense horizontal design.

## Ahmed adaptation

Use this template when Ahmed needs to explain an AI agent, automation, operating model, or execution system as a premium LinkedIn visual.

Do **not** copy the source layout. Ahmed's default static LinkedIn visual is the hand-drawn sketchnote concept:

`/root/.openclaw/workspace/media/inbound/234fe40d-96c3-4b4a-bf6f-dc1f75f91bbf.jpg`

Quality floor:

`/root/.openclaw/workspace/output/linkedin/return-on-tokens-rot-handdrawn-reference-quality-latest-2026-06-10.png`

## Card anatomy

A strong Ahmed-style AI Agent Workflow Card should include these elements, simplified for mobile readability:

1. **Agent name**
   - Short, credible name.
   - Avoid cute names unless the product/system already has one.

2. **Job-to-be-done**
   - One sentence: what the agent is responsible for.
   - Example: `Turns noisy market signals into executive-ready action briefs.`

3. **Inputs**
   - 3-5 source types maximum.
   - Examples: emails, X posts, job boards, CRM notes, meeting transcripts, KPI logs, documents.

4. **Workflow stages**
   - 4-6 steps maximum.
   - Recommended pattern:
     - Collect
     - Classify
     - Score
     - Draft / Decide
     - Escalate
     - Deliver

5. **Tools / systems touched**
   - Keep this as icons or short labels, not dense text.
   - Examples: Gmail, Notion, Telegram, browser, vector memory, CRM, dashboard.

6. **Guardrails**
   - Show what the agent refuses or escalates.
   - Examples:
     - no external send without approval
     - confidence threshold
     - evidence required
     - human escalation for public/paid/destructive actions

7. **Human role**
   - Clarify where Ahmed or the operator remains in control.
   - Examples:
     - approves final outreach
     - reviews high-risk recommendations
     - decides public posting

8. **Output**
   - One clear deliverable.
   - Examples:
     - Telegram decision card
     - recruiter-ready CV
     - opportunity brief
     - risk register update
     - content draft plus visual

9. **Metric / confidence**
   - One measurable proof point or control indicator.
   - Examples:
     - `82%+ ATS threshold`
     - `critical only if recruiter screen/interview invite`
     - `confidence: high / medium / low`
     - `5+ hours saved weekly`

## Visual hierarchy

For LinkedIn, compress the anatomy into a premium mobile-readable hand-drawn sketchnote:

- Dominant handwritten hook: what the agent does.
- Compact diagram: 4-5 stages, visually connected.
- Small guardrail/approval notes only where readable.
- Toolkit/system metaphor tied to the post thesis.
- Footer/signature: Ahmed Nasr.

Avoid trying to show every field. If it requires tiny copy, it belongs in the post body, not the card.

## Prompt skeleton

```text
Create a premium LinkedIn hand-drawn sketchnote visual in Ahmed Nasr's approved style.

Topic: [agent/system name]
Dominant hook: [short mobile-readable headline]
Compact diagram labels: [3-5 short labels]
Agent job: [job-to-be-done]
Inputs: [3-5 inputs]
Workflow stages: [4-6 stages]
Guardrails: [2-3 controls]
Human role: [approval/escalation point]
Output: [deliverable]
Metric/confidence: [one proof point]

Style: warm off-white paper, black ink illustration, restrained orange accents, authentic hand lettering, compact flow/toolkit/system metaphor, strong whitespace, Ahmed Nasr signature/footer.

Do not create a dense infographic, dashboard, horizontal system map, generic dark tech card, stock background, tiny text, generic boxes, or sketch-filter look.
```

## Example: AI Research Agent

- Agent: `Meridian`
- Job: turns noisy AI/operator signals into decision-ready briefs.
- Inputs: X posts, docs, changelogs, GitHub, product releases.
- Stages: collect -> verify -> compare evidence -> score relevance -> draft brief -> escalate.
- Guardrails: source link required, no claims without evidence, low confidence marked clearly.
- Human role: Ahmed decides whether to act, save, or convert into content.
- Output: Telegram decision card plus content angle.
- Metric: `20-30 candidates daily, top 5 surfaced`.

## Example: Inbox Agent

- Agent: `InboxPilot`
- Job: classifies inbound messages and surfaces only what needs action.
- Inputs: Gmail, LinkedIn alerts, recruiter messages, newsletters.
- Stages: ingest -> classify -> dedupe -> urgency score -> draft action -> escalate.
- Guardrails: never sends email without approval, critical only for recruiter screen/interview invite.
- Human role: Ahmed approves replies and decisions.
- Output: morning inbox decision card.
- Metric: `critical / useful / noise` classification.

## Completion gate

This template does not override the premium visual gate:

`docs/content-claw/premium-linkedin-visual-quality-gate.md`

Completion still requires an inspected artifact that passes both:

1. hand-drawn concept compliance
2. premium craft parity

A dense dashboard-style card or generic dark tech card fails for Ahmed's LinkedIn default unless Ahmed explicitly asks for that direction.
