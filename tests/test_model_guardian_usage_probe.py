import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'model-guardian-usage-probe.py'
SPEC = importlib.util.spec_from_file_location('model_guardian_usage_probe', MODULE_PATH)
USAGE_PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(USAGE_PROBE)


class ModelGuardianUsageProbeTests(unittest.TestCase):
    def test_normalizes_primary_weekly_window(self):
        snapshot = USAGE_PROBE.normalize_usage(
            {
                'plan_type': 'pro',
                'rate_limit': {
                    'primary_window': {
                        'limit_window_seconds': 168 * 3600,
                        'used_percent': 5,
                        'reset_at': 123,
                    }
                },
                'credits': {'balance': '0'},
            }
        )
        self.assertEqual(snapshot['windows'][0], {'label': '168h', 'usedPercent': 5.0, 'resetAt': 123000})
        self.assertEqual(snapshot['plan'], 'pro')
        self.assertEqual(snapshot['billing'][0]['amount'], 0.0)

    def test_labels_long_secondary_window_as_week(self):
        snapshot = USAGE_PROBE.normalize_usage(
            {
                'rate_limit': {
                    'primary_window': {
                        'limit_window_seconds': 5 * 3600,
                        'used_percent': 1,
                        'reset_at': 100,
                    },
                    'secondary_window': {
                        'limit_window_seconds': 168 * 3600,
                        'used_percent': 10,
                        'reset_at': 200,
                    },
                }
            }
        )
        self.assertEqual([window['label'] for window in snapshot['windows']], ['5h', 'Week'])

    def test_clamps_provider_percentages(self):
        snapshot = USAGE_PROBE.normalize_usage(
            {
                'rate_limit': {
                    'primary_window': {
                        'limit_window_seconds': 3600,
                        'used_percent': 150,
                    }
                }
            }
        )
        self.assertEqual(snapshot['windows'][0]['usedPercent'], 100)

    def test_error_snapshot_contains_no_credentials(self):
        snapshot = USAGE_PROBE.error_snapshot('OAuth token expired')
        self.assertEqual(snapshot['provider'], 'openai')
        self.assertEqual(snapshot['error'], 'OAuth token expired')
        self.assertNotIn('token', snapshot)


if __name__ == '__main__':
    unittest.main()
