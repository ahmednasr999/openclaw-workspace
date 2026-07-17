---
title: "<concise failure mode and component>"
status: verified
verified_on: YYYY-MM-DD
area: <runtime|automation|media|jobs|integrations|other>
tags: [<searchable-term>, <component>]
---

# <Title>

## Summary

One paragraph: what failed, the proven cause, and the working remedy.

## Symptoms

- Observable symptom, error, or state.
- Conditions that distinguish this failure mode from similar ones.

## Root cause

Explain the causal chain. Separate verified facts from remaining inference.

## Failed approaches

- Attempt worth remembering: why it failed or why it was unsafe.

Write `None worth preserving.` when failed attempts add no reusable value.

## Verified solution

Give the smallest safe sequence. Include prerequisites, approval boundary, rollback, and stop conditions when relevant.

## Evidence

- Check or artifact that proved the cause.
- Check or artifact that proved recovery.
- Relevant source references such as `path:line`.

## Prevention

- Guardrail, test, alert, retention rule, or operating practice that reduces recurrence.

## When to revisit

State what environmental or architectural change would invalidate this solution.
