# HR Career Sentinel v1

HR Career Sentinel is an isolated, event-driven Gmail workflow. Its default output is silence. It emits one Telegram alert only when a complete recruitment thread establishes that Ahmed must pay attention.

## Architecture

1. Pull private Gmail notifications from the existing Google Pub/Sub subscription without auto-acknowledgement.
2. Write each event to the sentinel's isolated SQLite database using `synchronous=FULL`.
3. Acknowledge Pub/Sub only after the local event is durable.
4. Resolve changed Gmail threads through Gmail History. First boot or expired history uses a bounded search around the Pub/Sub notification's publish time, not a broad inbox scan.
5. Fetch every message and decoded text/calendar part in the Gmail thread using `gog gmail thread get --full`.
6. Apply the deterministic ignore guard to the complete thread.
7. Classify possible recruitment threads through GPT-5.6 Sol with medium reasoning. Offers, negotiation, legal terms, relocation, visa, background checks, reference requests, document/identity requests, and other sensitive content use high reasoning.
8. Validate the model's strict JSON and apply deterministic policy gates.
9. Deduplicate by Gmail message ID, Gmail thread ID, and a normalized material-event state hash.
10. Persist an alert before Telegram delivery. No email write, draft, reply, forwarding, label, flag, trash, or delete path exists.

Runtime state is isolated under `data/hr-career-sentinel/`. Sanitized operational logs are written to `logs/hr-career-sentinel.jsonl`; email bodies are not logged.

## Alert policy

Alerts are allowed only for:

- Interview invitations
- Recruiter requests or replies
- Availability requests
- Assessments, tests, case studies, or assignments
- Offers, salary, benefits, or negotiation
- Reference requests or background checks
- Document, visa, or relocation requests
- Rejections after evidence of an active interview/assessment process in the complete thread
- Recruitment deadlines
- Recruitment messages requiring Ahmed's response

The deterministic veto keeps these silent even if a model over-classifies them:

- Generic job alerts and recommendations
- Newsletters, marketing, promotions, and bulk mail
- LinkedIn digests and social notifications
- Automatic application confirmations
- Routine rejections before an active interview process
- Unrelated personal or business email
- Threads whose latest message is Ahmed's reply and therefore no longer require him to act
- Classifications below the configured 70% confidence threshold

## Failure behavior

- Pub/Sub is not acknowledged until the event is on local durable storage.
- Model, Gmail, or parsing failures do not checkpoint the affected Gmail message. The local event remains pending for a later cycle.
- Telegram non-zero failures remain pending.
- A successful Telegram command without a verifiable `ok=true` and `messageId` is marked `uncertain` and is not automatically retried, preventing an ambiguous duplicate.
- All failure paths are silent to Ahmed and recorded without email bodies in the local operational log.

## Dry run

Dry run reads complete recent Gmail threads and invokes the same rules and reasoning tiers. It does not pull or acknowledge Pub/Sub, open the state database, or deliver Telegram alerts.

```bash
python3 scripts/hr-career-sentinel.py --dry-run --days 1 --max-threads 10
```

Dry-run output is an explicit diagnostic JSON report. Production mode remains silent.

## Verification

```bash
python3 -m unittest -v tests/test_hr_career_sentinel.py
python3 scripts/test-gmail-pubsub-pull-worker.py
systemd-analyze --user verify infrastructure/systemd/hr-career-sentinel.service
```

## Enable

Production activation was approved on 2026-07-17. The service is installed, enabled, and running. Use the following command as the reproducible activation gate after a rollback or clean install:

```bash
python3 -m unittest -q tests/test_hr_career_sentinel.py && python3 scripts/test-gmail-pubsub-pull-worker.py && systemd-analyze --user verify infrastructure/systemd/hr-career-sentinel.service && install -m 0600 infrastructure/systemd/hr-career-sentinel.service /root/.config/systemd/user/hr-career-sentinel.service && systemctl --user daemon-reload && systemctl --user enable --now hr-career-sentinel.service
```

## Rollback

Rollback stops and disables only HR Career Sentinel. It does not touch Gmail watch renewal or any legacy email unit.

```bash
systemctl --user disable --now hr-career-sentinel.service; rm -f /root/.config/systemd/user/hr-career-sentinel.service; systemctl --user daemon-reload; systemctl --user reset-failed hr-career-sentinel.service 2>/dev/null || true
```

The isolated SQLite database is retained for audit and deduplication. Archive or remove `data/hr-career-sentinel/` only under a separate data-retention decision.

## Production activation evidence

- Installed unit checksum matches `infrastructure/systemd/hr-career-sentinel.service`.
- Service state: enabled, active, running, zero restarts.
- Initial live intake processed 32 durable Pub/Sub notifications, with zero notification or alert errors.
- The initial two Gmail messages/threads were classified silently and produced no alert.
- A post-activation synthetic interview request passed the live GPT-5.6 Sol path as `interview_invited` with medium reasoning, 99% confidence, and no delivery.
- Legacy Email Agent schedules, Email Health Card, Email Hygiene, Email Synthetic Regression, OpenClaw Health Guard, and `gog-gmail-watch.service` remain disabled.
- `gog-gmail-watch-renew.timer` remains enabled because it only renews the Gmail Pub/Sub watch.
