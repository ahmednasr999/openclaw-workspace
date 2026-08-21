#!/usr/bin/env python3
"""Replay Daily Executive Intelligence with a second-source corroboration gate.

This script reads only retained local collector outputs. It writes aggregate,
PII-free shadow evidence and never changes the live brief, ranking config, cron,
or publishing state.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
INTELLIGENCE_SCRIPT = WORKSPACE / "scripts" / "executive-intelligence-brief.py"
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "is", "it", "new", "of", "on", "the", "to", "with",
}


def load_intelligence_module():
    spec = importlib.util.spec_from_file_location("executive_intelligence_shadow_source", INTELLIGENCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {INTELLIGENCE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def tokens(title: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9]+", title.lower())
        if len(token) >= 3 and token not in STOPWORDS
    }


def related_title(left: str, right: str) -> bool:
    left_tokens, right_tokens = tokens(left), tokens(right)
    if not left_tokens or not right_tokens:
        return False
    overlap = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return overlap >= 3 and overlap / union >= 0.5


def credible(signal: Any, config: dict[str, Any], module: Any) -> bool:
    domain = module.domain_of(signal.url) or signal.source.lower()
    if not domain or module.normalized_domain_match(domain, config.get("weak_domains", [])):
        return False
    if signal.source_type == "x_signal" or domain in {"linkedin.com", "x.com", "news.google.com"}:
        return False
    return (
        module.normalized_domain_match(domain, config.get("trusted_domains", []))
        or signal.evidence_grade.upper() in {"PRIMARY", "OFFICIAL", "TRUSTED_REPORTING"}
    )


def corroborated_ids(signals: list[Any], config: dict[str, Any], module: Any) -> set[str]:
    supported: set[str] = set()
    credible_signals = [signal for signal in signals if credible(signal, config, module)]
    for index, left in enumerate(credible_signals):
        left_domain = module.domain_of(left.url)
        for right in credible_signals[index + 1:]:
            right_domain = module.domain_of(right.url)
            if not left_domain or left_domain == right_domain:
                continue
            if related_title(left.title, right.title):
                supported.update({left.signal_id, right.signal_id})
    return supported


def metric_values(
    selected: list[Any], supported: set[str], unique_count: int, elapsed_ms: float,
    config: dict[str, Any], module: Any,
) -> dict[str, float]:
    selected_count = len(selected)
    supported_count = sum(signal.signal_id in supported for signal in selected)
    domains = {module.domain_of(signal.url) for signal in selected if module.domain_of(signal.url)}
    false_positive_proxy = 0
    for signal in selected:
        domain = module.domain_of(signal.url) or signal.source.lower()
        if (
            not signal.pillar_matches
            or module.normalized_domain_match(domain, config.get("weak_domains", []))
        ):
            false_positive_proxy += 1
    return {
        "two-source-actionable-rate": round(supported_count / selected_count, 6) if selected_count else 0.0,
        "processing-latency-ms": round(elapsed_ms, 6),
        "source-diversity-ratio": round(len(domains) / selected_count, 6) if selected_count else 0.0,
        "candidate-coverage-rate": round(selected_count / unique_count, 6) if unique_count else 0.0,
        "false-positive-proxy-rate": round(false_positive_proxy / selected_count, 6) if selected_count else 0.0,
    }


def build_shadow(run_date: date) -> tuple[dict[str, Any], dict[str, Any]]:
    module = load_intelligence_module()
    config = module.load_json(module.CONFIG_PATH, {})
    if not config:
        raise RuntimeError(f"missing or invalid config: {module.CONFIG_PATH}")
    sources = {
        "rss": module.load_rss(),
        "fintech_radar": module.load_fintech(),
        "daily_web": module.load_daily_web(run_date),
        "x_signal": module.load_x_signals(),
    }
    raw = [signal for rows in sources.values() for signal in rows]
    valid = [signal for signal in raw if signal.title and signal.url]
    feedback = module.load_feedback()
    for signal in valid:
        module.infer_pillars(signal, config)
        signal.signal_id = module.hashlib.sha256(
            (signal.url or module.title_key(signal.title)).encode()
        ).hexdigest()[:16]
        module.score_signal(signal, config, run_date, feedback)
        module.ensure_executive_fields(signal)
    unique = module.dedupe(valid)

    control_started = time.perf_counter()
    control = module.select_balanced(unique, config)
    control_elapsed_ms = (time.perf_counter() - control_started) * 1000

    treatment_started = time.perf_counter()
    supported = corroborated_ids(unique, config, module)
    treatment_pool = [signal for signal in unique if signal.signal_id in supported]
    treatment = module.select_balanced(treatment_pool, config)
    treatment_elapsed_ms = (time.perf_counter() - treatment_started) * 1000

    cairo = timezone(timedelta(hours=3))
    start = datetime.combine(run_date, datetime.min.time(), cairo)
    end = start + timedelta(days=1)
    snapshot = {
        "schema_version": 1,
        "snapshot_id": f"daily-executive-intelligence-{run_date.isoformat()}",
        "data_policy": "aggregated-sanitized",
        "source_type": "local-aggregated-replay",
        "workflow": "Daily Executive Intelligence",
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "privacy": {"contains_pii": False, "aggregated": True},
        "steps": [
            {
                "id": "source-fetch",
                "name": "Fetch retained local candidates",
                "entered": len(raw),
                "completed": len(valid),
                "errors": len(raw) - len(valid),
                "dropoff_classification": "friction",
            },
            {
                "id": "normalize-deduplicate",
                "name": "Normalize and deduplicate candidates",
                "entered": len(valid),
                "completed": len(unique),
                "errors": 0,
                "dropoff_classification": "intentional-filter",
            },
            {
                "id": "second-source-corroboration",
                "name": "Find support from two credible sources",
                "entered": len(unique),
                "completed": len(supported),
                "errors": 0,
                "dropoff_classification": "friction",
            },
            {
                "id": "executive-ranking",
                "name": "Apply editorial ranking and balance gates",
                "entered": len(unique),
                "completed": len(control),
                "errors": 0,
                "dropoff_classification": "intentional-filter",
            },
        ],
    }
    measurement = {
        "schema_version": 1,
        "run_date": run_date.isoformat(),
        "generated_at": datetime.now(cairo).isoformat(),
        "mode": "shadow",
        "live_workflow_changed": False,
        "candidate_count": len(unique),
        "corroborated_candidate_count": len(supported),
        "control_selected_count": len(control),
        "treatment_selected_count": len(treatment),
        "comparison": {
            "method": "paired-control-treatment",
            "control_sample_size": len(unique),
            "treatment_sample_size": len(unique),
            "control_metrics": metric_values(
                control, supported, len(unique), control_elapsed_ms, config, module
            ),
            "treatment_metrics": metric_values(
                treatment, supported, len(unique), treatment_elapsed_ms, config, module
            ),
        },
    }
    return snapshot, measurement


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, help="Replay date in YYYY-MM-DD form")
    parser.add_argument("--snapshot-output", type=Path, required=True)
    parser.add_argument("--measurement-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        snapshot, measurement = build_shadow(date.fromisoformat(args.date))
        write_json(args.snapshot_output, snapshot)
        write_json(args.measurement_output, measurement)
        print(json.dumps({
            "ok": True,
            "snapshot": str(args.snapshot_output),
            "measurement": str(args.measurement_output),
            "candidate_count": measurement["candidate_count"],
            "corroborated_candidate_count": measurement["corroborated_candidate_count"],
            "live_workflow_changed": False,
        }, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
