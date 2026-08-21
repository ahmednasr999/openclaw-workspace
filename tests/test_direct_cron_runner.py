from __future__ import annotations

import argparse
import importlib.util
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "direct-cron-runner.py"
SPEC = importlib.util.spec_from_file_location("direct_cron_runner", SCRIPT)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class LinkedInCommentRadarCronTests(unittest.TestCase):
    def test_incomplete_judged_round_is_internal_skip_not_failure_alert(self) -> None:
        result = {
            "returncode": 2,
            "stdout": "\n".join(
                [
                    "workflow_run=2026-07-29-1100-recovery terminal=exhausted",
                    "/tmp/2026-07-29-1100-recovery.md",
                    "cards=/tmp/2026-07-29-1100-recovery.json",
                    "status=incomplete_no_candidates posts=0",
                ]
            ),
            "stderr": "judge_failures=five-card pack unavailable",
            "log_path": "/tmp/linkedin-radar-fixture.log",
        }
        args = argparse.Namespace(validate=False, no_send=False)

        with (
            patch.object(runner, "run_command", return_value=result),
            patch.object(runner, "linkedin_radar_ready_count", return_value=0),
            patch.object(
                runner,
                "send_telegram",
                side_effect=AssertionError("incomplete rounds must not alert Ahmed"),
            ),
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                returncode = runner.linkedin_comment_radar(args, "1100")

        self.assertEqual(returncode, 0)
        self.assertIn('"skipped": true', output.getvalue())
        self.assertIn("incomplete radar rounds stay internal", output.getvalue())


if __name__ == "__main__":
    unittest.main()
