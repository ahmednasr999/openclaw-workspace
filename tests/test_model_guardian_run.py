import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'model-guardian-run.py'
SPEC = importlib.util.spec_from_file_location('model_guardian_run', MODULE_PATH)
MODEL_GUARDIAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL_GUARDIAN)


class ModelGuardianUsageTests(unittest.TestCase):
    def extract_from_label(self, label):
        payload = {
            'usage': {
                'providers': [
                    {
                        'provider': 'openai-codex',
                        'windows': [
                            {'label': '5h', 'usedPercent': 3, 'resetAt': 111},
                            {'label': label, 'usedPercent': 12, 'resetAt': 222},
                        ],
                    }
                ]
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = Path(tmpdir) / 'status.json'
            cache.write_text(json.dumps(payload))
            with patch.object(MODEL_GUARDIAN, 'STATUS_CACHE', cache):
                return MODEL_GUARDIAN.extract_codex_usage()

    def test_accepts_week_label(self):
        self.assertEqual(self.extract_from_label('Week'), (88.0, 222))

    def test_accepts_168h_label(self):
        self.assertEqual(self.extract_from_label('168h'), (88.0, 222))

    def test_normalizes_weekly_label_whitespace_and_case(self):
        self.assertEqual(self.extract_from_label('  WEEK  '), (88.0, 222))

    def test_rejects_non_weekly_windows(self):
        with self.assertRaisesRegex(RuntimeError, 'weekly Codex quota window missing'):
            self.extract_from_label('30d')

    def test_timeout_without_json_is_transient(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = Path(tmpdir) / 'missing-status.json'
            with (
                patch.object(MODEL_GUARDIAN, 'STATUS_CACHE', cache),
                patch.object(
                    MODEL_GUARDIAN,
                    'run_subprocess',
                    return_value=(124, '', 'TIMEOUT: status probe exceeded 30s'),
                ),
            ):
                with self.assertRaisesRegex(
                    MODEL_GUARDIAN.TransientProbeFailure,
                    'timed out after 20s',
                ):
                    MODEL_GUARDIAN.extract_codex_usage()

    def test_fallback_uses_quota_only_probe_not_openclaw_status(self):
        payload = {
            'provider': 'openai',
            'windows': [{'label': '168h', 'usedPercent': 7, 'resetAt': 333}],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = Path(tmpdir) / 'missing-status.json'
            with (
                patch.object(MODEL_GUARDIAN, 'STATUS_CACHE', cache),
                patch.object(
                    MODEL_GUARDIAN,
                    'run_subprocess',
                    return_value=(0, json.dumps(payload), ''),
                ) as run_subprocess,
            ):
                self.assertEqual(MODEL_GUARDIAN.extract_codex_usage(), (93.0, 333))

            args, kwargs = run_subprocess.call_args
            self.assertEqual(args[0][0], '/usr/bin/python3')
            self.assertEqual(args[0][1], str(MODEL_GUARDIAN.USAGE_PROBE_SCRIPT))
            self.assertNotIn('status', args[0])

    def test_quota_probe_network_failure_is_transient(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = Path(tmpdir) / 'missing-status.json'
            with (
                patch.object(MODEL_GUARDIAN, 'STATUS_CACHE', cache),
                patch.object(
                    MODEL_GUARDIAN,
                    'run_subprocess',
                    return_value=(75, '', 'TRANSIENT: temporary DNS failure'),
                ),
            ):
                with self.assertRaisesRegex(
                    MODEL_GUARDIAN.TransientProbeFailure,
                    'temporary DNS failure',
                ):
                    MODEL_GUARDIAN.extract_codex_usage()

    def test_transient_prefix_is_classified_as_suppressible(self):
        self.assertTrue(
            MODEL_GUARDIAN.is_transient_probe_failure(
                'FAIL: Codex quota-only probe failed after retries: TRANSIENT: temporary DNS failure'
            )
        )

    def test_main_suppresses_missing_cache_after_transient_check_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output = StringIO()
            with (
                patch.object(MODEL_GUARDIAN, 'STATUS_CACHE', root / 'status.json'),
                patch.object(MODEL_GUARDIAN, 'STATE_FILE', root / 'state.json'),
                patch.object(MODEL_GUARDIAN, 'USAGE_FILE', root / 'usage.jsonl'),
                patch.object(
                    MODEL_GUARDIAN,
                    'run_subprocess',
                    return_value=(124, '', 'TIMEOUT: model guardian check exceeded 140s'),
                ) as run_subprocess,
                patch.object(MODEL_GUARDIAN, 'send_telegram') as send_telegram,
                redirect_stdout(output),
            ):
                MODEL_GUARDIAN.main()

            self.assertEqual(run_subprocess.call_count, 1)
            send_telegram.assert_not_called()
            self.assertIn('TRANSIENT_SUPPRESSED', output.getvalue())
            self.assertIn('NO_ALERTS', output.getvalue())
            state = json.loads((root / 'state.json').read_text())
            self.assertEqual(state['consecutiveTransientProbeFailures'], 1)


if __name__ == '__main__':
    unittest.main()
