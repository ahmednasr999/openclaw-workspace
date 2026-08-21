# Proactive Opportunity Loop — Bounded Pilot

## Contract

- Outcome: once daily, identify up to three valuable missed actions from current NASR evidence, challenge them independently, prepare safe internal work, and escalate only approval-bound actions.
- Constraints: no new data collector where an existing source exists; no arbitrary executor; no public/external actions; no email or third-party messages; no applications; no financial, credential, destructive, gateway/runtime/config, database, or sibling-workspace mutation.
- Definition of done: producer and evaluator run in fresh isolated sessions; every surviving item has exact evidence; duplicates and stale/weak claims fail closed; only allowlisted local artifacts are auto-prepared; the evaluator is silent on clean no-op days.
- Evidence: active-task register, daily context note, Resolver briefing, executive-intelligence output, Daily Intel, calendar cache, and live OpenClaw cron state.
- Authority: reversible writes under `data/proactive-opportunity-loop/` and `reports/proactive-opportunity-loop/` only. All other actions require Ahmed or the existing owning workflow.
- Stop states: `complete`, `clean_noop`, `approval_required`, `blocked`, or `rejected`.
- Owner: NASR/main.
- Review tier: substantial.

## Schedule

- Producer: 06:10 Cairo, after Daily Intel and executive-intelligence generation.
- Evaluator: 06:25 Cairo, fresh isolated session, after producer completion.
- Delivery: producer is silent; evaluator delivers only evaluator-approved internal preparations or approval cards. Clean no-op is `NO_REPLY`.

## Automatic action allowlist

- `prepare_action_brief`: create a local evidence-backed next-action brief.
- `prepare_owner_handoff`: create a local evidence-backed handoff for the existing lane owner.

These artifacts are preparation, not authority. They cannot change active tasks, runtime, cron, databases, credentials, public content, applications, messages, or external state.

## Rollback

Disable or remove the two cron declarations. The workflow has no external side effects; generated state and reports can be retained as audit evidence. Removing generated artifacts is optional and not required to stop the loop.
