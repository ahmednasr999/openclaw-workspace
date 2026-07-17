# Owner Reference

The canonical workflow is `skills/skill-discovery-pilot/`. This cron skill owns scheduling and operational verification only.

Preserve these invariants when changing the schedule:

- OS cron and deterministic shell/Python runner, not an agent-turn wrapper
- 5-10 candidates, currently eight
- inert metadata/README quarantine only
- no candidate execution, installation, promotion, or external messaging
- lock, persistent log, and status JSON
- `CRON_RUNNER_NO_ALERT=1` while the lane remains a pilot

If the workflow changes beyond these boundaries, disable the schedule and return to a manual pilot until a fresh live sample passes.
