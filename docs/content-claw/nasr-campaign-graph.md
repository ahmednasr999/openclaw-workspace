# NASR Campaign Graph

The Campaign Graph is the local coordination and learning layer for Ahmed's
multi-asset executive content. It complements the Notion Content Calendar; it
does not replace it.

## Operating boundary

- Notion remains the only live source of truth for approval, scheduling, and publishing.
- A campaign-direction sign-off does not approve any asset for publication.
- The Campaign Graph never posts, schedules, messages, emails, or changes Notion.
- Every public asset still follows the normal draft, visual, duplicate, publisher-QA, approval, and post-publish checks.

## Graph

`raw input -> structured brief -> angles -> evidence -> campaign plan -> Ahmed sign-off -> build -> publish gate -> measured results -> next-cycle lesson`

The eight explicit gates are:

1. `intake`
2. `angles`
3. `evidence`
4. `campaign_plan`
5. `signoff`
6. `build`
7. `publish`
8. `feedback`

Every gate records either `pass` or `loop_back`, the decision maker, evidence,
reason, and timestamp. A stage cannot pass until earlier stages have passed.

## Storage

- Campaigns: `/root/.openclaw/workspace-cmo/data/campaign-graph/campaigns/{campaign_id}/manifest.json`
- Readable brief: `/root/.openclaw/workspace-cmo/data/campaign-graph/campaigns/{campaign_id}/brief.md`
- Feedback ledger: `/root/.openclaw/workspace-cmo/data/campaign-graph/performance-feedback.jsonl`

The campaign manifest links primary and derivative assets through
`parent_asset_id`. Each asset carries its platform, format, owner, purpose,
hook, funnel role, intended outcome, success signal, artifact path, Notion page
ID, quality-gate result, post URL, and measurement state.

## Standard intake

```bash
python3 /root/.openclaw/workspace/scripts/nasr-campaign-graph.py intake \
  --source-type voice_note \
  --raw-input "Transcribed or typed rough idea" \
  --title "Campaign title" \
  --objective "What this campaign should establish" \
  --audience "Specific GCC executive audience" \
  --pillar ai_execution_and_governance \
  --funnel-role authority \
  --intended-outcome "Qualified executive dialogue" \
  --success-signal "Saves, substantive comments, and qualified profile visits" \
  --core-tension "The operating tension" \
  --chosen-angle "The selected executive angle" \
  --primary-hook "The first-line hook"
```

Supported pillars:

- `ai_execution_and_governance`
- `pmo_and_decision_discipline`
- `healthcare_transformation`
- `fintech_operations`
- `gcc_transformation_leadership`

## Add evidence and derivatives

```bash
python3 /root/.openclaw/workspace/scripts/nasr-campaign-graph.py direction \
  --campaign-id CAMPAIGN_ID \
  --chosen-angle "The selected executive angle" \
  --rejected-angle "A weaker generic angle" \
  --primary-hook "The approved working hook"

python3 /root/.openclaw/workspace/scripts/nasr-campaign-graph.py evidence \
  --campaign-id CAMPAIGN_ID \
  --kind internal \
  --label "Ahmed voice and operating rules" \
  --source "/root/.openclaw/workspace/docs/standards/nasr-writing-standard.md"

python3 /root/.openclaw/workspace/scripts/nasr-campaign-graph.py asset \
  --campaign-id CAMPAIGN_ID \
  --asset-id linkedin-carousel \
  --parent-asset-id primary-linkedin-post \
  --platform linkedin \
  --format carousel \
  --purpose "Expand the operating model into a reusable framework" \
  --success-signal "Saves and qualified profile visits"
```

## Gate decisions

```bash
python3 /root/.openclaw/workspace/scripts/nasr-campaign-graph.py gate \
  --campaign-id CAMPAIGN_ID \
  --stage evidence \
  --decision pass \
  --decided-by CMO \
  --evidence "Internal and external evidence recorded"
```

Use `--decision loop_back --reason "..."` when a stage needs revision.

The `signoff` gate only passes when `--decided-by` explicitly identifies Ahmed.
The `publish` gate additionally requires:

```bash
--notion-status Approved --publisher-qa pass
```

That records readiness only. It performs no external action.

## Performance feedback

Record whatever is actually available. Missing metrics remain `null`; never
infer them. When measurement is unavailable, use `--metrics-unavailable` with a
specific `--measurement-note`.

```bash
python3 /root/.openclaw/workspace/scripts/nasr-campaign-graph.py feedback \
  --campaign-id CAMPAIGN_ID \
  --asset-id primary-linkedin-post \
  --impressions 1200 \
  --saves 18 \
  --qualified-profile-visits 4 \
  --metric-source "LinkedIn analytics export" \
  --lesson "Operating-system hooks earn saves." \
  --next-action "Test the thesis as a six-slide carousel."
```

Each feedback row is automatically tied to campaign, asset, pillar, hook,
format, platform, funnel role, intended outcome, and success signal. This is
the durable return path from results to the content brain.

## Validation

```bash
python3 /root/.openclaw/workspace/scripts/nasr-campaign-graph.py validate \
  --campaign-id CAMPAIGN_ID

python3 /root/.openclaw/workspace/scripts/nasr-campaign-graph.py status \
  --campaign-id CAMPAIGN_ID
```

Validation rejects unsafe governance changes, duplicate asset IDs, dangling
parents, asset cycles, invalid funnel roles, missing gates, and invalid gate
decisions.
