import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "rss-intelligence-crawler.py"
SPEC = importlib.util.spec_from_file_location("rss_intelligence_crawler", SCRIPT)
RSS = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(RSS)


def article(title, category, source, description="", published=""):
    return {
        "title": title,
        "link": f"https://{source}/{title.lower().replace(' ', '-')}",
        "description": description,
        "published": published,
        "category": category,
        "source": source,
        "item": None,
    }


class RssContentPolicyTests(unittest.TestCase):
    def test_healthcare_ai_signal_maps_to_both_relevant_pillars(self):
        candidate = RSS.build_candidate(article(
            "Practical AI and data standards in hospitals",
            "Healthcare",
            "health.example",
            "Healthcare leaders redesign clinical workflow, AI governance, and model accountability.",
        ))
        self.assertEqual(candidate["pillar"], "Healthcare transformation")
        self.assertIn("AI execution and governance", candidate["pillar_matches"])
        self.assertGreaterEqual(candidate["content_fit_score"], RSS.MIN_CONTENT_FIT_SCORE)

    def test_weekly_slate_enforces_pillar_source_and_angle_diversity(self):
        articles = [
            article("Agentic AI needs accountable workflows", "AI", "ai.example", "AI governance and operating model execution."),
            article("Portfolio decisions are the PMO control point", "PMO", "pmo.example", "PMO portfolio decision latency and execution."),
            article("Open finance operations need stronger reconciliation", "FinTech", "fintech.example", "Fintech payment banking reconciliation controls."),
            article("Saudi transformation requires decision discipline", "Digital Transformation", "gcc.example", "Saudi Vision 2030 GCC transformation leadership."),
            article("A second AI automation story", "AI", "ai.example", "AI automation and governance."),
        ]
        slate = RSS.select_weekly_rss_slate([RSS.build_candidate(item) for item in articles])
        self.assertEqual(len(slate), 4)
        self.assertEqual(len({item["angle"] for item in slate}), 4)
        self.assertGreaterEqual(len({item["pillar"] for item in slate}), 4)
        self.assertTrue(all(item["content_fit_score"] >= RSS.MIN_CONTENT_FIT_SCORE for item in slate))

    def test_stale_signal_is_not_selected(self):
        stale = RSS.build_candidate(article(
            "Old AI governance story", "AI", "ai.example", "AI governance execution.", "2020-01-01"
        ))
        self.assertEqual(RSS.select_weekly_rss_slate([stale]), [])


if __name__ == "__main__":
    unittest.main()
