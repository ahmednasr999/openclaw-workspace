from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fintech-radar.py"
PROMPT = Path(__file__).resolve().parents[1] / "prompts" / "fintech-radar-daily.md"
SPEC = importlib.util.spec_from_file_location("fintech_radar", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FintechRadarTests(unittest.TestCase):
    def test_daily_prompt_has_compact_delivery_contract(self):
        prompt = PROMPT.read_text()
        self.assertIn("Required output:", prompt)
        self.assertIn("Boundaries:", prompt)
        self.assertIn("Done when:", prompt)
        self.assertIn("actual 1080x1350 PNG", prompt)
        self.assertIn("`ok=true` and a non-empty `messageId`", prompt)
        self.assertNotIn("chain-of-thought", prompt.lower())

    def test_daily_report_requires_actual_image(self):
        cfg = {
            "top_items": 8,
            "content_output": {
                "image_format": "PNG",
                "image_dimensions": "1080x1350",
            },
        }
        story = MODULE.Story(
            title="Aria raises equity and debt financing",
            url="https://example.com/aria",
            snippet="Funding announcement",
            source="example.com",
            category="Capital",
            evidence_grade="TRUSTED_REPORTING",
        )
        report = MODULE.render([story], cfg, MODULE.dt.datetime(2099, 7, 11, tzinfo=MODULE.CAIRO))
        self.assertIn("DELIVERY BLOCKED", report)
        self.assertIn("A prompt or concept never satisfies the image requirement", report)
        self.assertIn("PNG, 1080x1350", report)

    def test_debt_facility_is_preferred_content_angle(self):
        equity = MODULE.Story(title="Acme raises $20m seed", url="https://example.com/a", snippet="", source="example.com", category="Capital", score=90)
        mixed = MODULE.Story(title="Aria raises €7m and launches €240m debt facility", url="https://example.com/b", snippet="", source="example.com", category="Capital", score=70)
        self.assertEqual(MODULE.select_content_candidate([equity, mixed]), mixed)

    def test_extracts_funding_amount_and_stage(self):
        text = "Acme raises $45 million Series B led by Example Ventures"
        self.assertEqual(MODULE.extract_amount(text), "$45 million")
        self.assertEqual(MODULE.extract_stage(text), "Series B")

    def test_funding_amount_beats_valuation(self):
        text = "Super.com hits $1.2bn valuation after $65m Series D"
        self.assertEqual(MODULE.extract_amount(text), "$65m")

    def test_detects_gcc_relevance(self):
        geo, relevance = MODULE.classify_geography("Company expands payments platform in Saudi Arabia", ["saudi arabia", "uae"])
        self.assertEqual(geo, "Saudi Arabia")
        self.assertEqual(relevance, "High")

    def test_reporting_is_not_primary(self):
        cfg = {"primary_domains": ["centralbank.ae"], "trusted_reporting_domains": ["reuters.com"]}
        self.assertFalse(MODULE.is_probable_company_primary("reuters.com", "Acme", cfg))

    def test_company_domain_can_be_primary(self):
        cfg = {"primary_domains": [], "trusted_reporting_domains": ["reuters.com"]}
        self.assertTrue(MODULE.is_probable_company_primary("acme.com", "Acme", cfg))

    def test_reporting_brand_is_not_company_primary(self):
        cfg = {"primary_domains": [], "trusted_reporting_domains": []}
        self.assertFalse(MODULE.is_probable_company_primary("fintechglobal.com", "Slow week for FinTech", cfg))

    def test_company_prefixes_are_removed(self):
        self.assertEqual(MODULE.infer_company("Sydney mortgage fintech LendUs banks $5m Seed round"), "LendUs")

    def test_title_normalization_removes_update_noise(self):
        self.assertEqual(MODULE.normalized_title("UPDATE: Acme Raises New Round"), "acme raises round")

    def test_relevance_rejects_unrelated_ipo(self):
        self.assertFalse(MODULE.is_relevant("Fashion retailer files for IPO", "US listing", "Capital"))

    def test_relevance_accepts_fintech_funding(self):
        self.assertTrue(MODULE.is_relevant("Payments fintech Acme raises $45m", "Series B funding", "Capital"))


if __name__ == "__main__":
    unittest.main()
