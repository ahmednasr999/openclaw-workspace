import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check-skill-lifecycle.py"
SPEC = importlib.util.spec_from_file_location("check_skill_lifecycle", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def base_config():
    return {
        "schema_version": 1,
        "resident_max_count": 2,
        "resident": [
            {"name": "safety", "reason": "global control"},
        ],
        "local_on_demand": {
            "research": ["search"],
        },
        "quarantined_external": [
            {
                "name": "candidate",
                "source": "https://github.com/example/candidate",
                "revision": "a" * 40,
                "execution_allowed": False,
                "promotion_status": "blocked",
            }
        ],
    }


def skills_snapshot(*names):
    return {
        "skills": [
            {"name": name, "modelVisible": True, "source": "test"}
            for name in names
        ]
    }


class SkillLifecycleValidationTests(unittest.TestCase):
    def test_valid_classification_passes(self):
        result = MODULE.validate(base_config(), skills_snapshot("safety", "search"))
        self.assertEqual([], result.errors)
        self.assertEqual(1, result.resident_count)
        self.assertEqual(1, result.local_on_demand_count)
        self.assertEqual(1, result.quarantined_count)

    def test_duplicate_active_skill_fails(self):
        config = base_config()
        config["local_on_demand"]["research"].append("safety")
        result = MODULE.validate(config, skills_snapshot("safety", "search"))
        self.assertTrue(any("classified more than once" in item for item in result.errors))

    def test_unclassified_visible_skill_fails(self):
        result = MODULE.validate(
            base_config(), skills_snapshot("safety", "search", "surprise")
        )
        self.assertTrue(any("Unclassified model-visible skills" in item for item in result.errors))

    def test_resident_cap_fails_closed(self):
        config = base_config()
        config["resident"].extend(
            [
                {"name": "core-two", "reason": "frequent"},
                {"name": "core-three", "reason": "frequent"},
            ]
        )
        result = MODULE.validate(
            config, skills_snapshot("safety", "core-two", "core-three", "search")
        )
        self.assertTrue(any("Resident tier exceeds cap" in item for item in result.errors))

    def test_external_candidate_requires_full_sha_and_inert_status(self):
        config = base_config()
        config["quarantined_external"][0]["revision"] = "main"
        config["quarantined_external"][0]["execution_allowed"] = True
        result = MODULE.validate(config, skills_snapshot("safety", "search"))
        self.assertTrue(any("full 40-character Git SHA" in item for item in result.errors))
        self.assertTrue(any("execution_allowed=false" in item for item in result.errors))

    def test_quarantined_candidate_cannot_be_model_visible(self):
        result = MODULE.validate(
            base_config(), skills_snapshot("safety", "search", "candidate")
        )
        self.assertTrue(any("Quarantined skills are model-visible" in item for item in result.errors))

    def test_cli_writes_compact_index_and_json_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            skills_path = root / "skills.json"
            report_path = root / "report.json"
            index_path = root / "INDEX.md"
            config_path.write_text(json.dumps(base_config()), encoding="utf-8")
            skills_path.write_text(
                json.dumps(skills_snapshot("safety", "search")), encoding="utf-8"
            )

            rc = MODULE.main(
                [
                    "--config",
                    str(config_path),
                    "--skills-json",
                    str(skills_path),
                    "--report",
                    str(report_path),
                    "--index",
                    str(index_path),
                ]
            )

            self.assertEqual(0, rc)
            self.assertEqual("PASS", json.loads(report_path.read_text())["verdict"])
            index = index_path.read_text(encoding="utf-8")
            self.assertIn("## Resident (1/2)", index)
            self.assertIn("### research", index)
            self.assertIn("candidate", index)


if __name__ == "__main__":
    unittest.main()
