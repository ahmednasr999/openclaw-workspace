import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "weekly-self-health-fast.py"
SPEC = importlib.util.spec_from_file_location("weekly_self_health_fast", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_report_retries_are_important_not_critical():
    critical, important, monitor = MODULE.cron_findings({
        "jobs": [{
            "id": "report",
            "name": "CMO Weekly Content Report",
            "status": "error",
            "state": {
                "consecutiveErrors": 4,
                "lastError": "cron: job execution timed out",
            },
        }],
    })

    assert critical == []
    assert important[0][0] == "Repeated cron failure: CMO Weekly Content Report"
    assert monitor == []


def test_repeated_publisher_failure_remains_critical():
    critical, important, monitor = MODULE.cron_findings({
        "jobs": [{
            "id": "publisher",
            "name": "CMO Notion LinkedIn Publisher",
            "status": "error",
            "state": {
                "consecutiveErrors": 2,
                "lastError": "publish workflow failed",
            },
        }],
    })

    assert critical == ["CMO Notion LinkedIn Publisher: publish workflow failed"]
    assert important == []
    assert monitor == []


def test_repeated_jobzoom_daily_failure_remains_critical():
    critical, important, monitor = MODULE.cron_findings({
        "jobs": [{
            "id": "jobzoom",
            "name": "JobZoom Managed Daily",
            "status": "error",
            "state": {
                "consecutiveErrors": 2,
                "lastError": "daily scan failed",
            },
        }],
    })

    assert critical == ["JobZoom Managed Daily: daily scan failed"]
    assert important == []
    assert monitor == []


def test_previous_self_health_failure_is_monitor_only():
    critical, important, monitor = MODULE.cron_findings({
        "jobs": [{
            "id": "current-id-can-change",
            "name": "Weekly OpenClaw read-only health baseline",
            "status": "error",
            "state": {
                "consecutiveErrors": 3,
                "lastError": "cron isolated agent run aborted",
            },
        }],
    })

    assert critical == []
    assert important == []
    assert monitor == [
        "Weekly OpenClaw read-only health baseline: previous failures before this bounded run - cron isolated agent run aborted"
    ]
