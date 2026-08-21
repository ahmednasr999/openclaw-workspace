import importlib.util
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "nasr-campaign-graph.py"
SPEC = importlib.util.spec_from_file_location("nasr_campaign_graph", SCRIPT)
campaign = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(campaign)


class CampaignGraphTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.campaign_id = "2026-07-31-ai-operating-model"
        rc = campaign.main(
            [
                "--root",
                str(self.root),
                "intake",
                "--campaign-id",
                self.campaign_id,
                "--source-type",
                "voice_note",
                "--raw-input",
                "One idea should create a coordinated executive campaign.",
                "--title",
                "AI operating model campaign",
                "--objective",
                "Position Ahmed around governed AI execution.",
                "--audience",
                "GCC transformation executives",
                "--pillar",
                "ai_execution_and_governance",
                "--funnel-role",
                "authority",
                "--intended-outcome",
                "Qualified executive dialogue",
                "--success-signal",
                "Substantive comments and qualified profile visits",
                "--core-tension",
                "Models are common; operating systems are scarce.",
                "--chosen-angle",
                "The graph, brain, and protocols create the advantage.",
                "--primary-hook",
                "The model is not your advantage.",
            ]
        )
        self.assertEqual(rc, 0)

    def tearDown(self):
        self.tmp.cleanup()

    def load(self):
        return campaign.load_manifest(self.root, self.campaign_id)

    def pass_gate(self, stage, decided_by="CMO", extra=None):
        args = [
            "--root",
            str(self.root),
            "gate",
            "--campaign-id",
            self.campaign_id,
            "--stage",
            stage,
            "--decision",
            "pass",
            "--decided-by",
            decided_by,
            "--evidence",
            f"{stage} evidence",
        ]
        if extra:
            args.extend(extra)
        return campaign.main(args)

    def test_intake_creates_safe_manifest_and_brief(self):
        manifest = self.load()
        self.assertEqual(manifest["next_stage"], "intake")
        self.assertFalse(manifest["governance"]["external_writes_allowed"])
        self.assertFalse(manifest["governance"]["auto_publish_allowed"])
        self.assertTrue(manifest["governance"]["notion_is_live_publish_source"])
        brief = (
            self.root / "campaigns" / self.campaign_id / "brief.md"
        ).read_text()
        self.assertIn("Notion Content Calendar remains", brief)
        self.assertIn("primary-linkedin-post", brief)

    def test_gates_are_sequential_and_evidence_requires_both_sources(self):
        self.assertEqual(self.pass_gate("angles"), 2)
        self.assertEqual(self.pass_gate("intake"), 0)
        self.assertEqual(self.pass_gate("angles"), 0)
        self.assertEqual(self.pass_gate("evidence"), 2)

        for kind in ("internal", "external"):
            self.assertEqual(
                campaign.main(
                    [
                        "--root",
                        str(self.root),
                        "evidence",
                        "--campaign-id",
                        self.campaign_id,
                        "--kind",
                        kind,
                        "--label",
                        f"{kind} source",
                        "--source",
                        f"https://example.com/{kind}",
                    ]
                ),
                0,
            )
        self.assertEqual(self.pass_gate("evidence"), 0)

    def test_asset_graph_and_manifest_validation(self):
        rc = campaign.main(
            [
                "--root",
                str(self.root),
                "asset",
                "--campaign-id",
                self.campaign_id,
                "--asset-id",
                "carousel",
                "--parent-asset-id",
                "primary-linkedin-post",
                "--platform",
                "linkedin",
                "--format",
                "carousel",
                "--purpose",
                "Expand the operating model",
                "--success-signal",
                "Saves",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(campaign.main(["--root", str(self.root), "validate", "--campaign-id", self.campaign_id]), 0)

        manifest = self.load()
        manifest["assets"][0]["parent_asset_id"] = "carousel"
        manifest["assets"][1]["parent_asset_id"] = "primary-linkedin-post"
        errors = campaign.validate_manifest(manifest)
        self.assertTrue(any("cycle" in error for error in errors))

    def test_direction_can_be_selected_after_intake(self):
        manifest = self.load()
        manifest["brief"]["chosen_angle"] = ""
        campaign.save_manifest(self.root, manifest)
        self.assertEqual(self.pass_gate("intake"), 0)
        self.assertEqual(self.pass_gate("angles"), 2)
        rc = campaign.main(
            [
                "--root",
                str(self.root),
                "direction",
                "--campaign-id",
                self.campaign_id,
                "--chosen-angle",
                "Campaign systems beat isolated content.",
                "--rejected-angle",
                "More models create the advantage.",
                "--primary-hook",
                "One post is not a campaign.",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(self.pass_gate("angles"), 0)
        updated = self.load()
        self.assertEqual(
            updated["assets"][0]["hook"], "One post is not a campaign."
        )
        self.assertEqual(len(updated["brief"]["rejected_angles"]), 1)

    def test_signoff_requires_ahmed_and_publish_gate_requires_live_controls(self):
        self.assertEqual(self.pass_gate("intake"), 0)
        self.assertEqual(self.pass_gate("angles"), 0)
        for kind in ("internal", "external"):
            campaign.main(
                [
                    "--root",
                    str(self.root),
                    "evidence",
                    "--campaign-id",
                    self.campaign_id,
                    "--kind",
                    kind,
                    "--label",
                    kind,
                    "--source",
                    kind,
                ]
            )
        self.assertEqual(self.pass_gate("evidence"), 0)
        self.assertEqual(self.pass_gate("campaign_plan"), 0)
        self.assertEqual(self.pass_gate("signoff", decided_by="CMO"), 2)
        self.assertEqual(self.pass_gate("signoff", decided_by="Ahmed Nasr"), 0)
        artifact = self.root / "primary.md"
        artifact.write_text("Primary asset")
        self.assertEqual(
            campaign.main(
                [
                    "--root",
                    str(self.root),
                    "update-asset",
                    "--campaign-id",
                    self.campaign_id,
                    "--asset-id",
                    "primary-linkedin-post",
                    "--status",
                    "completed",
                    "--artifact-path",
                    str(artifact),
                    "--notion-page-id",
                    "notion-page-1",
                    "--quality-gate",
                    "pass",
                ]
            ),
            0,
        )
        self.assertEqual(self.pass_gate("build"), 0)
        self.assertEqual(self.pass_gate("publish"), 2)
        self.assertEqual(
            self.pass_gate(
                "publish",
                extra=["--notion-status", "Approved", "--publisher-qa", "pass"],
            ),
            0,
        )
        self.assertEqual(
            campaign.main(
                [
                    "--root",
                    str(self.root),
                    "feedback",
                    "--campaign-id",
                    self.campaign_id,
                    "--asset-id",
                    "primary-linkedin-post",
                    "--metrics-unavailable",
                    "--measurement-note",
                    "Fixture has no live LinkedIn metrics.",
                    "--lesson",
                    "The campaign completed its governed path.",
                    "--next-action",
                    "Collect live metrics after a real publication.",
                ]
            ),
            0,
        )
        self.assertEqual(self.pass_gate("feedback"), 0)
        self.assertEqual(self.load()["status"], "complete")

    def test_feedback_record_carries_campaign_dimensions(self):
        rc = campaign.main(
            [
                "--root",
                str(self.root),
                "feedback",
                "--campaign-id",
                self.campaign_id,
                "--asset-id",
                "primary-linkedin-post",
                "--impressions",
                "1200",
                "--saves",
                "18",
                "--qualified-profile-visits",
                "4",
                "--lesson",
                "Operating-system hooks earn saves.",
                "--next-action",
                "Test the same thesis as a carousel.",
            ]
        )
        self.assertEqual(rc, 0)
        record = json.loads(
            (self.root / "performance-feedback.jsonl").read_text().strip()
        )
        self.assertEqual(record["pillar"], "ai_execution_and_governance")
        self.assertEqual(record["funnel_role"], "authority")
        self.assertEqual(record["format"], "static_post")
        self.assertEqual(record["metrics"]["saves"], 18)
        self.assertEqual(record["intended_outcome"], "Qualified executive dialogue")
        self.assertTrue(self.load()["assets"][0]["performance_recorded"])

    def test_loop_back_requires_reason(self):
        rc = campaign.main(
            [
                "--root",
                str(self.root),
                "gate",
                "--campaign-id",
                self.campaign_id,
                "--stage",
                "angles",
                "--decision",
                "loop_back",
                "--decided-by",
                "CMO",
            ]
        )
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
