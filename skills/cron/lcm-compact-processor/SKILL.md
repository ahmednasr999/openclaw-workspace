# LCM Force-Compact Processor

## Purpose
Runs after LCM Nightly Health Check. Identifies uncompacted conversations (10+ messages, 0 summaries) and processes them through the force-compact queue.

## Steps

1. Run the queue builder to identify candidates:
```bash
node /root/.openclaw/workspace-cto/scripts/lcm-force-compact.mjs
```

2. Run the processor to compact the queue:
```bash
bash /root/.openclaw/workspace-cto/scripts/lcm-compact-processor.sh
```

3. Log results and report summary count to the CTO topic.

## On failure
- Log to `/var/log/openclaw/lcm-compact-processor.log`
- If > 5 failures, alert CTO via telegram topic 8
