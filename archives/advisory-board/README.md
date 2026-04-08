# Advisory Board Phase 1

This folder contains the Phase 1 core engine for the Business Advisory Board.

## What is implemented
- Scoring engine: `(I × U × C) / (E × (1.1 - A))`
- Three adapters in one runner:
  - Career/Jobs (`jobs-bank/pipeline.md`)
  - Top priorities (`memory/active-tasks.md`)
  - Personal brand signals (`memory/active-tasks.md` entries like LinkedIn/Threads)
- Daily brief generator to: `advisory-board/outputs/daily-brief-YYYY-MM-DD.md`
- Conflict note + one daily new idea + recommendation line
- Input freshness check (>48h stale flag)

## Run
```bash
python3 advisory-board/phase1_engine.py
```

Optional date override:
```bash
python3 advisory-board/phase1_engine.py --date 2026-03-02
```

## Phase 2
A second runner is now available:

```bash
python3 advisory-board/phase2_engine.py --mode daily
python3 advisory-board/phase2_engine.py --mode weekly
python3 advisory-board/phase2_engine.py --mode calibrate
```

Phase 2 adds:
- New adapters: AI automation, risk/compliance, time allocation, financial
- Conflict detection and domain-balance checks
- Weekly strategy report output
- Monthly calibration JSON output

## Next step
If approved, switch the daily cron to `phase2_engine.py --mode daily`, and add a weekly Sunday 20:00 Cairo cron for `--mode weekly`.
