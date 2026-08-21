import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit


SCRIPT = Path(__file__).parents[1] / "scripts" / "executive-intelligence-corroboration-shadow.py"
SPEC = importlib.util.spec_from_file_location("executive_intelligence_corroboration_shadow", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FakeIntelligenceModule:
    @staticmethod
    def domain_of(url):
        return urlsplit(url).netloc.lower().removeprefix("www.")

    @staticmethod
    def normalized_domain_match(domain, candidates):
        return any(domain == item or domain.endswith("." + item) for item in candidates)


def signal(title, domain, signal_id, source_type="rss", pillar_matches=None):
    return SimpleNamespace(
        title=title,
        url=f"https://{domain}/story",
        source=domain,
        source_type=source_type,
        evidence_grade="",
        signal_id=signal_id,
        pillar_matches=["AI execution"] if pillar_matches is None else pillar_matches,
    )


class ExecutiveIntelligenceCorroborationShadowTests(unittest.TestCase):
    def setUp(self):
        self.module = FakeIntelligenceModule()
        self.config = {"trusted_domains": ["source-a.com", "source-b.com"], "weak_domains": ["weak.com"]}

    def test_related_titles_require_meaningful_overlap(self):
        self.assertTrue(MODULE.related_title(
            "G42 launches Arabic AI model for enterprise workflows",
            "G42 launches enterprise Arabic AI model in UAE",
        ))
        self.assertFalse(MODULE.related_title(
            "G42 launches Arabic AI model",
            "Hospital improves patient scheduling workflow",
        ))

    def test_corroboration_requires_two_distinct_credible_domains(self):
        first = signal("G42 launches Arabic AI model for enterprise workflows", "source-a.com", "one")
        second = signal("G42 launches enterprise Arabic AI model in UAE", "source-b.com", "two")
        duplicate_domain = signal("G42 launches Arabic AI model for enterprise use", "source-a.com", "three")
        supported = MODULE.corroborated_ids(
            [first, second, duplicate_domain], self.config, self.module
        )
        self.assertEqual({"one", "two", "three"}, supported)

        weak = signal("G42 launches Arabic AI model for enterprise use", "weak.com", "weak")
        supported = MODULE.corroborated_ids([first, weak], self.config, self.module)
        self.assertEqual(set(), supported)

    def test_zero_treatment_is_reported_without_division_errors(self):
        values = MODULE.metric_values([], set(), 38, 1.2, self.config, self.module)
        self.assertEqual(0.0, values["two-source-actionable-rate"])
        self.assertEqual(0.0, values["candidate-coverage-rate"])
        self.assertEqual(1.2, values["processing-latency-ms"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
