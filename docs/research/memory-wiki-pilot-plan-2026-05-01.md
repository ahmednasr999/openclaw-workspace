# OpenClaw Memory Wiki Pilot Plan - 2026-05-01

Source reviewed: `https://docs.openclaw.ai/plugins/memory-wiki`

## Decision

Do not enable `memory-wiki` in the live memory stack yet.

Treat it as a structured-knowledge pilot candidate. The current stack already has `memory-core`, `active-memory`, and `lossless-claw` enabled, and the live Telegram memory path was recently stabilized. Adding another memory plugin should be controlled and isolated first.

## What Memory Wiki Adds

`memory-wiki` turns durable knowledge into a compiled wiki-style vault with:

- pages for entities, people, systems, decisions, and sources
- structured claims with evidence and confidence
- provenance-aware search
- contradiction, stale-fact, and open-question visibility
- optional Obsidian-friendly rendering
- optional bridge mode from existing memory artifacts
- tools such as `wiki_status`, `wiki_search`, `wiki_get`, `wiki_apply`, and `wiki_lint`

It does not replace the active memory plugin. It is best viewed as a maintained knowledge layer above raw memory files and transcript recall.

## Current State

Observed config state:

- `plugins.entries.memory-wiki`: not configured
- `plugins.entries.memory-core.enabled`: true
- `plugins.entries.active-memory.enabled`: true
- `plugins.entries.lossless-claw.enabled`: true

Current recommendation: keep that stable stack unchanged until a pilot is explicitly approved.

## Best Use Cases For Ahmed/NASR

High-value uses:

- Ahmed/NASR knowledge base for people, companies, roles, relationships, and decisions.
- CV/job-search evidence map, where facts need provenance and confidence.
- Governance memory, especially rules, incidents, decisions, and active contradictions.
- Agent routing and capability cards, for example who owns CMO/CTO/HR/CEO responsibilities.
- Contradiction dashboard for memory hygiene.
- Open questions dashboard to drive the daily memory-gap pilot.

Lower-value or risky uses:

- Live Telegram prompt injection.
- Replacing `MEMORY.md`.
- Replacing `lossless-claw` for conversation recall.
- Exact reminders or scheduled operations.
- Operational alerts that already belong in cron or heartbeat.

## Recommended Pilot Mode

Start with isolated mode only.

```json5
{
  plugins: {
    entries: {
      "memory-wiki": {
        enabled: true,
        config: {
          vaultMode: "isolated",
          vault: {
            path: "~/.openclaw/wiki/main",
            renderMode: "native"
          },
          bridge: {
            enabled: false
          },
          ingest: {
            autoCompile: false,
            maxConcurrentJobs: 1,
            allowUrlIngest: false
          },
          search: {
            backend: "local",
            corpus: "wiki"
          },
          context: {
            includeCompiledDigestPrompt: false
          },
          render: {
            preserveHumanBlocks: true,
            createBacklinks: true,
            createDashboards: true
          }
        }
      }
    }
  }
}
```

Why this mode:

- No live prompt shape changes.
- No bridge import from active memory yet.
- No automatic URL ingestion.
- No shared search side effects.
- Compile and lint behavior can be inspected manually.

## Pilot Dataset

Use a small curated seed set, not the full memory corpus.

Suggested seed pages:

1. `person.ahmed-nasr`
   - durable profile facts only
   - source links back to `USER.md`, `MEMORY.md`, and master CV data where appropriate

2. `system.openclaw-runtime`
   - gateway version, local patch discipline, update policy, runtime safety notes

3. `workflow.linkedin-premium-visuals`
   - execution-card doctrine, reference asset, quality gate, image-to-UI workflow

4. `workflow.jobzoom-protected-lane`
   - protected lane rules, ATS threshold, report interpretation rules

5. `governance.approval-boundaries`
   - external write, public post, gateway config, restart, destructive action boundaries

Do not ingest private raw transcripts, credentials, email bodies, or broad job-search logs during the first pilot.

## Success Criteria

The pilot is useful if it can answer provenance-sensitive questions better than current memory alone.

Pass signals:

- `wiki_search` finds the right page quickly.
- `wiki_get` shows clear claims and evidence.
- `wiki_lint` surfaces real contradictions or stale facts.
- Wiki pages stay readable as human documents.
- No prompt-injection behavior changes in Telegram.
- No duplication or conflict with `MEMORY.md` and `lossless-claw`.

Fail signals:

- It creates noisy duplicate facts.
- It makes memory behavior slower or more confusing.
- It indexes sensitive content too broadly.
- It changes live prompt behavior before approval.
- It requires too much manual maintenance for too little recall value.

## Review Method

After the pilot is enabled and seeded, run:

```bash
openclaw wiki status
openclaw wiki compile
openclaw wiki lint
openclaw wiki search "Ahmed Nasr"
openclaw wiki search "LinkedIn premium visual"
openclaw wiki get person.ahmed-nasr
```

Compare against:

```bash
openclaw memory search "Ahmed Nasr"
```

Use `memory_search corpus=all` for broad recall. Use `wiki_search` plus `wiki_get` when provenance, wiki-specific ranking, source evidence, or page-level belief structure matters.

Useful search modes from the docs:

- `auto`
- `find-person`
- `route-question`
- `source-evidence`
- `raw-claim`

## Approval Boundary

Enabling `memory-wiki` is a gateway/plugin config change and must not be done without explicit approval for the config change.

This plan creates no runtime, gateway, or config changes by itself.

## Recommendation

Next safe step, if Ahmed wants to continue later:

1. Approve isolated pilot config.
2. Enable `memory-wiki` with `includeCompiledDigestPrompt: false`.
3. Seed only 3 to 5 curated pages.
4. Compile and lint.
5. Review whether the answers are better than current memory.
6. Only then consider bridge mode or broader ingestion.
