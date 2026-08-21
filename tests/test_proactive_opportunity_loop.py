import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/proactive-opportunity-loop.py"
SPEC = importlib.util.spec_from_file_location("proactive_loop", SCRIPT)
loop = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(loop)


class Args:
    pass


class ProactiveLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        (self.workspace / "config").mkdir()
        config = {
            "max_candidates": 3,
            "minimum_priority": 60,
            "duplicate_window_days": 14,
            "duplicate_similarity": 0.88,
            "allowed_auto_actions": ["prepare_action_brief", "prepare_owner_handoff"],
            "approval_only_terms": ["publish", "gateway", "email"],
        }
        (self.workspace / loop.CONFIG_REL).write_text(json.dumps(config))
        self.run_id = "20260813T100000+0300"
        self.evidence = {
            "evidence_id": "ev-one",
            "kind": "active_tasks",
            "source": str(self.workspace / "memory/active-tasks.md"),
            "locator": "status",
            "observed_at": "2026-08-13T10:00:00+03:00",
            "source_modified_at": "2026-08-13T09:55:00+03:00",
            "freshness_hours": 0.08,
            "summary": "A material unresolved decision exists",
            "details": ["Status: pending"],
        }
        snapshot = {"run_id": self.run_id, "evidence": [self.evidence]}
        path = self.workspace / loop.DATA_REL / "snapshots" / f"{self.run_id}.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(snapshot))
        latest = self.workspace / loop.DATA_REL / "latest-run-id.txt"
        latest.write_text(self.run_id + "\n")

    def tearDown(self):
        self.temp.cleanup()

    def proposal_args(self, **overrides):
        args = Args()
        args.workspace = self.workspace
        args.run_id = self.run_id
        args.title = overrides.get("title", "Resolve the pending decision")
        args.priority = overrides.get("priority", 80)
        args.action_kind = overrides.get("action_kind", "prepare_action_brief")
        args.action_summary = overrides.get("action_summary", "Prepare a decision brief with verified options")
        args.why_now = "The source shows an unresolved high-priority item"
        args.owner = "NASR"
        args.evidence_id = overrides.get("evidence_id", ["ev-one"])
        args.approval_reason = overrides.get("approval_reason", "")
        return args

    def review_args(self, proposal_id, **overrides):
        args = Args()
        args.workspace = self.workspace
        args.run_id = self.run_id
        args.proposal_id = proposal_id
        args.verdict = overrides.get("verdict", "accept")
        args.reason = overrides.get("reason", "Opened the cited source; the claim and smallest next step are supported")
        args.checked_evidence = overrides.get("checked_evidence", ["ev-one"])
        return args

    def finalize_args(self, now="2026-08-13T10:10:00+03:00"):
        args = Args()
        args.workspace = self.workspace
        args.run_id = self.run_id
        args.now = now
        return args

    def proposal_id(self):
        data = json.loads((self.workspace / loop.DATA_REL / "proposals" / f"{self.run_id}.json").read_text())
        return data["proposals"][0]["proposal_id"]

    def test_proposal_requires_valid_evidence(self):
        with self.assertRaises(loop.LoopError):
            loop.propose(self.proposal_args(evidence_id=["ev-missing"]))

    def test_candidate_cap_is_enforced(self):
        for index in range(3):
            loop.propose(self.proposal_args(title=f"Candidate {index}"))
        with self.assertRaises(loop.LoopError):
            loop.propose(self.proposal_args(title="Candidate 4"))

    def test_review_must_check_every_citation(self):
        loop.propose(self.proposal_args())
        with self.assertRaises(loop.LoopError):
            loop.review(self.review_args(self.proposal_id(), checked_evidence=[]))

    def test_accepted_safe_action_creates_local_artifact(self):
        loop.propose(self.proposal_args())
        loop.review(self.review_args(self.proposal_id()))
        self.assertEqual(loop.finalize(self.finalize_args()), 0)
        result = json.loads((self.workspace / loop.DATA_REL / "latest-result.json").read_text())
        self.assertEqual(result["outcomes"][0]["status"], "auto_prepared")
        self.assertTrue(Path(result["outcomes"][0]["artifact"]).exists())

    def test_dangerous_language_is_upgraded_to_approval(self):
        loop.propose(self.proposal_args(action_summary="Publish the finding externally"))
        loop.review(self.review_args(self.proposal_id()))
        loop.finalize(self.finalize_args())
        result = json.loads((self.workspace / loop.DATA_REL / "latest-result.json").read_text())
        self.assertEqual(result["outcomes"][0]["status"], "approval_required")

    def test_explicit_approval_request_never_auto_executes(self):
        loop.propose(self.proposal_args(action_kind="approval_request", approval_reason="External action"))
        loop.review(self.review_args(self.proposal_id()))
        loop.finalize(self.finalize_args())
        result = json.loads((self.workspace / loop.DATA_REL / "latest-result.json").read_text())
        self.assertEqual(result["outcomes"][0]["status"], "approval_required")

    def test_rejected_review_fails_closed(self):
        loop.propose(self.proposal_args())
        loop.review(self.review_args(self.proposal_id(), verdict="reject", reason="Evidence does not support urgency"))
        loop.finalize(self.finalize_args())
        result = json.loads((self.workspace / loop.DATA_REL / "latest-result.json").read_text())
        self.assertEqual(result["outcomes"][0]["status"], "rejected")

    def test_recent_duplicate_is_suppressed(self):
        loop.propose(self.proposal_args())
        proposal_id = self.proposal_id()
        history = self.workspace / loop.DATA_REL / "history.jsonl"
        history.write_text(json.dumps({
            "proposal_id": "prior",
            "title": "Resolve the pending decision",
            "action_summary": "Prepare a decision brief with verified options",
            "finalized_at": "2026-08-12T10:00:00+03:00",
        }) + "\n")
        loop.review(self.review_args(proposal_id))
        loop.finalize(self.finalize_args())
        result = json.loads((self.workspace / loop.DATA_REL / "latest-result.json").read_text())
        self.assertEqual(result["outcomes"][0]["status"], "duplicate")


if __name__ == "__main__":
    unittest.main()
