#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("exec_intel", ROOT / "scripts" / "executive-intelligence-brief.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class ExecutiveIntelligenceTests(unittest.TestCase):
    def test_canonical_url_removes_tracking(self):
        value = MOD.canonical_url("https://www.example.com/a/?utm_source=x&s=46&id=7#top")
        self.assertEqual(value, "https://example.com/a?id=7")

    def test_duplicate_titles(self):
        a = MOD.Signal("GCC banks accelerate AI governance", "https://a.example/x")
        b = MOD.Signal("GCC banks accelerate AI governance!", "https://b.example/y")
        self.assertTrue(MOD.duplicate(a, b))

    def test_scoring_rewards_fresh_pillar_signal(self):
        cfg = MOD.load_json(MOD.CONFIG_PATH, {})
        signal = MOD.Signal(
            "Saudi healthcare adopts governed AI workflows",
            "https://reuters.com/example",
            summary="Hospital leaders redesign clinical workflow and decision governance.",
            source_type="rss",
            published="2026-07-13",
        )
        MOD.infer_pillars(signal, cfg)
        MOD.score_signal(signal, cfg, date(2026, 7, 13), {})
        self.assertGreaterEqual(signal.score, 70)
        self.assertIn("Healthcare transformation", signal.pillar_matches)
        self.assertIn("GCC transformation leadership", signal.pillar_matches)

    def test_balancer_caps_domains(self):
        cfg = MOD.load_json(MOD.CONFIG_PATH, {})
        rows = []
        for n in range(5):
            item = MOD.Signal(f"Unique signal {n}", f"https://same.example/{n}", score=90-n)
            rows.append(item)
        selected = MOD.select_balanced(rows, cfg)
        self.assertLessEqual(sum(MOD.domain_of(x.url) == "same.example" for x in selected), 2)

    def test_content_candidates_prefer_distinct_pillars(self):
        cfg = MOD.load_json(MOD.CONFIG_PATH, {})
        rows = [
            MOD.Signal("Health one", "https://a/1", pillar="Healthcare transformation", angle="workflow", score=90),
            MOD.Signal("Health two", "https://b/2", pillar="Healthcare transformation", angle="clinical risk", score=89),
            MOD.Signal("AI one", "https://c/3", pillar="AI execution and governance", angle="AI controls", score=88),
        ]
        selected = MOD.select_content_candidates(rows, cfg)
        self.assertEqual([x.pillar for x in selected[:2]], ["Healthcare transformation", "AI execution and governance"])


if __name__ == "__main__":
    unittest.main()
