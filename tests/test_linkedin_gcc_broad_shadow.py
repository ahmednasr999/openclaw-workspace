import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "linkedin-gcc-broad-shadow.py"
SPEC = importlib.util.spec_from_file_location("linkedin_gcc_broad_shadow", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class BroadShadowTests(unittest.TestCase):
    def test_parse_dedupe_and_query_provenance(self):
        html = """
        <li><div data-entity-urn="urn:li:jobPosting:4439313633"></div>
          <a href="https://ae.linkedin.com/jobs/view/example-4439313633?x=1"></a>
          <h3>Vice President, Group Commercial &amp; Technology Enablement</h3>
          <h4>ADNOC Group</h4><span class="job-search-card__location">Abu Dhabi</span>
          <time datetime="2026-08-09"></time></li>
        """
        first = MODULE.parse_cards(html, "healthcare transformation", "UAE")
        second = MODULE.parse_cards(html, "digital transformation", "UAE")
        jobs = MODULE.dedupe_jobs(first + second)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["id"], "4439313633")
        self.assertEqual(
            jobs[0]["matched_queries"],
            ["healthcare transformation", "digital transformation"],
        )

    def test_build_report_finds_incremental_senior_role(self):
        jobs = [
            {
                "id": "4439313633",
                "title": "Vice President, Group Commercial & Technology Enablement",
                "company": "ADNOC Group",
                "matched_queries": ["healthcare transformation"],
            },
            {
                "id": "4451507971",
                "title": "Senior Specialist, Digital Change Management",
                "company": "ADNOC Group",
                "matched_queries": ["healthcare transformation"],
            },
        ]
        report = MODULE.build_report(
            jobs,
            {
                "4439313633": {
                    "title": "Vice President, Group Commercial & Technology Enablement",
                    "company": "ADNOC Group",
                    "search_title": "Chief Digital Officer",
                },
                "4451507971": {
                    "title": "Senior Specialist, Digital Change Management",
                    "search_title": "Chief Digital Officer",
                },
            },
            [],
        )
        self.assertEqual(report["counts"]["senior_jobs"], 1)
        self.assertEqual(report["counts"]["novel_vs_jobzoom_raw"], 0)
        self.assertEqual(report["counts"]["jobzoom_pass1_gaps"], 1)
        self.assertEqual(report["jobzoom_pass1_gaps"][0]["id"], "4439313633")
        self.assertEqual(report["counts"]["controlled_rescue_candidates"], 1)
        self.assertEqual(
            report["controlled_rescue_candidates"][0]["id"], "4439313633"
        )

    def test_extract_job_id_handles_jobspy_and_linkedin_urls(self):
        self.assertEqual(MODULE.extract_job_id("li-4450938768"), "4450938768")
        self.assertEqual(
            MODULE.extract_job_id(
                "https://ae.linkedin.com/jobs/view/example-4439313633?x=1"
            ),
            "4439313633",
        )


if __name__ == "__main__":
    unittest.main()
