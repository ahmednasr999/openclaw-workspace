# Context Audit Trail System

This directory stores trace files for sub-agent executions to enable quick debugging when agents produce unexpected results.

## Purpose

When sub-agents are spawned, there's no built-in log of what context, files, or skills they loaded. Debugging "why did the agent do X?" currently requires reading full session transcripts. This system provides a quick reference trail.

## Trace File Naming

Each trace is a markdown file named: `{date}-{label}.md`

- **Date:** ISO format (YYYY-MM-DD)
- **Label:** Short descriptive label for the task

Example: `2026-03-19-cv-agent-amazon.md`

## Trace Contents

Each trace contains:
- **Timestamp** - When the trace was created
- **Model** - Which AI model was used
- **Task** - One-line summary of what the agent was asked to do
- **Files Read** - List of files the agent accessed
- **Skills Loaded** - List of skills triggered
- **Tools Called** - External tools/APIs used
- **Outcome** - Success/failure status and brief result
- **Notes** - Any anomalies or debugging insights

## When to Log

**Mandatory** for:
- CV creation tasks
- Content posting (LinkedIn, X)
- Research tasks
- Any multi-step workflow

**Optional** for:
- Simple file lookups
- Quick questions
- Trivial information retrieval

## Usage

1. Before spawning a sub-agent for a significant task, create a trace file
2. During execution, record files read, skills loaded, and tools called
3. After completion, update with outcome and any notes
4. When debugging unexpected behavior, review the relevant trace

## Template

See `_template.md` for the standard format to follow.
