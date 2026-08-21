from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "hr-career-sentinel.py"
SPEC = importlib.util.spec_from_file_location("hr_career_sentinel", MODULE_PATH)
assert SPEC and SPEC.loader
sentinel = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sentinel
SPEC.loader.exec_module(sentinel)


def message(
    message_id: str,
    body: str,
    *,
    subject: str = "Leadership role",
    sender: str = "Recruiter <recruiter@example.com>",
    internal_date: int = 1,
    list_unsubscribe: bool = False,
) -> dict:
    return {
        "id": message_id,
        "thread_id": "thread-1",
        "history_id": str(internal_date),
        "internal_date": str(internal_date),
        "from": sender,
        "to": sentinel.ACCOUNT,
        "reply_to": "",
        "subject": subject,
        "date": "Thu, 16 Jul 2026 12:00:00 +0300",
        "message_id_header": f"<{message_id}@example.com>",
        "list_unsubscribe": list_unsubscribe,
        "precedence": "bulk" if list_unsubscribe else "",
        "body": body,
        "attachments": [],
    }


def thread(*messages: dict, thread_id: str = "thread-1") -> dict:
    values = [dict(item, thread_id=thread_id) for item in messages]
    return {"thread_id": thread_id, "history_id": values[-1]["history_id"], "messages": values}


def raw_result(
    event_state: str,
    *,
    requires_attention: bool = True,
    requires_response: bool = True,
    deadline: str = "Not stated",
    importance: str = "high",
    confidence: int = 92,
) -> dict:
    return {
        "is_recruitment": True,
        "requires_attention": requires_attention,
        "requires_response": requires_response,
        "event_state": event_state,
        "company": "Example Corp",
        "sender": "Recruiter <recruiter@example.com>",
        "role": "VP Transformation",
        "what_changed": "The hiring process advanced",
        "sender_wants": "Ahmed to respond",
        "deadline": deadline,
        "importance": importance,
        "recommended_action": "Review and reply",
        "suggested_reply": "Thank you. I am available and look forward to the next step." if requires_response else "",
        "confidence": confidence,
    }


class PolicyClassifier:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.seen: list[dict] = []

    def classify(self, value: dict) -> dict:
        self.seen.append(value)
        validated = sentinel.validate_model_result(self.result, value, sentinel.reasoning_tier(value))
        return sentinel.apply_policy(value, validated)


class NeverPubSub:
    def pull(self):
        return []

    def ack(self, _ack_id):
        raise AssertionError("ack should not be called")


class TestClassificationRules(unittest.TestCase):
    def test_all_attention_event_states_alert(self):
        bodies = {
            "interview_invited": "We invite you to interview. Please confirm your availability.",
            "recruiter_contact": "I am a recruiter replying about a VP role. Please respond.",
            "availability_requested": "Please share your availability for the hiring manager call.",
            "assessment_requested": "Please complete the recruitment assessment.",
            "case_study_requested": "Please complete the case study assignment.",
            "offer_received": "We are pleased to extend an offer for the VP role.",
            "compensation_discussion": "Please confirm your salary and benefits expectations.",
            "reference_requested": "Please provide two references for this role.",
            "background_check_requested": "Please complete the background check for your candidacy.",
            "documents_requested": "Please provide the required employment documents.",
            "visa_or_relocation_requested": "Please confirm your visa and relocation requirements.",
            "response_required": "Regarding your application, please reply to this question.",
            "deadline_changed": "The recruitment deadline is Friday.",
            "other_action_required": "For this candidate process, please complete the requested action.",
        }
        for state, body in bodies.items():
            with self.subTest(state=state):
                value = thread(message(f"m-{state}", body))
                result = sentinel.apply_policy(
                    value,
                    sentinel.validate_model_result(
                        raw_result(state, requires_attention=False, requires_response=False),
                        value,
                        sentinel.reasoning_tier(value),
                    ),
                )
                self.assertTrue(result["requires_attention"])

    def test_deadline_or_response_forces_recruitment_attention(self):
        value = thread(message("m1", "Regarding your application, please respond by Friday."))
        for response, deadline in ((True, "Not stated"), (False, "Friday, 17 July 2026")):
            with self.subTest(response=response, deadline=deadline):
                source = raw_result(
                    "no_action",
                    requires_attention=False,
                    requires_response=response,
                    deadline=deadline,
                )
                result = sentinel.apply_policy(
                    value,
                    sentinel.validate_model_result(source, value, "medium"),
                )
                self.assertTrue(result["requires_attention"])

    def test_post_interview_rejection_alerts_but_routine_rejection_is_silent(self):
        active = thread(
            message("m1", "Your interview with the hiring manager is confirmed."),
            message("m2", "After your interview, unfortunately we will not move forward.", internal_date=2),
        )
        result = sentinel.apply_policy(
            active,
            sentinel.validate_model_result(
                raw_result(
                    "post_interview_rejection",
                    requires_attention=False,
                    requires_response=False,
                ),
                active,
                "medium",
            ),
        )
        self.assertTrue(result["requires_attention"])

        routine = thread(message("m3", "Unfortunately we will not move forward with your application."))
        self.assertEqual(sentinel.noise_reason(routine), "routine_pre_interview_rejection")

    def test_ignore_matrix(self):
        fixtures = [
            ("generic_job_alert", message("n1", "Here are matching jobs for you.", subject="Daily job alert")),
            ("generic_job_alert", message(
                "n1b",
                "Applications close on July 28, 2026.",
                subject="Job Vacancy",
                sender="recruitment.notify@oia.gov.om",
            )),
            ("linkedin_digest_or_social", message("n2", "Your weekly digest and profile views.", subject="LinkedIn weekly digest")),
            ("automatic_application_confirmation", message("n3", "Thank you for your application. It has been received.")),
            ("social_notification", message("n4", "Someone liked your post.", subject="Social notification")),
            ("newsletter_or_marketing", message("n5", "Newsletter promotion. Unsubscribe here.", list_unsubscribe=True)),
            ("unrelated_email", message("n6", "Your utility invoice is ready.", subject="Monthly invoice", sender="Billing <billing@example.com>")),
        ]
        for expected, item in fixtures:
            with self.subTest(expected=expected):
                self.assertEqual(sentinel.noise_reason(thread(item)), expected)

    def test_high_reasoning_for_sensitive_and_medium_for_normal_recruitment(self):
        high_terms = ["offer letter", "salary", "legal terms", "relocation", "visa", "passport", "background check"]
        for term in high_terms:
            with self.subTest(term=term):
                self.assertEqual(sentinel.reasoning_tier(thread(message("h", f"Recruitment {term}"))), "high")
        self.assertEqual(
            sentinel.reasoning_tier(thread(message("m", "Please confirm your interview availability."))),
            "medium",
        )

    def test_alert_has_every_required_field(self):
        rendered = sentinel.render_alert(sentinel.validate_model_result(
            raw_result("interview_invited"),
            thread(message("m1", "Interview invitation")),
            "medium",
        ))
        for label in (
            "Company:", "Sender:", "Role:", "What changed:", "What the sender wants:",
            "Deadline:", "Importance:", "Recommended next action:", "Suggested reply:", "Confidence:",
        ):
            self.assertIn(label, rendered)


class TestFullThreadAndGateway(unittest.TestCase):
    def test_gmail_json_decoder_uses_every_message(self):
        def part(text: str) -> dict:
            encoded = sentinel.base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")
            return {"mimeType": "text/plain", "body": {"data": encoded, "size": len(text)}}

        raw = {"thread": {"id": "t1", "historyId": "99", "messages": [
            {"id": "a", "threadId": "t1", "internalDate": "1", "payload": {
                "mimeType": "text/plain", "headers": [
                    {"name": "From", "value": "Recruiter <r@example.com>"},
                    {"name": "Subject", "value": "Interview"},
                ], "body": part("First complete body")["body"]}},
            {"id": "b", "threadId": "t1", "internalDate": "2", "payload": {
                "mimeType": "multipart/alternative", "headers": [
                    {"name": "From", "value": "Recruiter <r@example.com>"},
                    {"name": "Subject", "value": "Next step"},
                ], "parts": [part("Second complete body"), {
                    "mimeType": "text/html",
                    "body": {"data": sentinel.base64.urlsafe_b64encode(b"<p>duplicate html</p>").decode().rstrip("=")},
                }]}}
        ]}}
        decoded = sentinel.gmail_thread_from_json(raw)
        self.assertEqual(len(decoded["messages"]), 2)
        combined = sentinel.thread_text(decoded)
        self.assertIn("First complete body", combined)
        self.assertIn("Second complete body", combined)
        self.assertNotIn("duplicate html", combined)

    def test_full_thread_reaches_classifier(self):
        value = thread(
            message("m1", "We scheduled your interview with the hiring manager."),
            message("m2", "After the interview, we will not move forward.", internal_date=2),
        )
        classifier = PolicyClassifier(raw_result("post_interview_rejection", requires_response=False))
        with tempfile.TemporaryDirectory() as directory:
            store = sentinel.StateStore(Path(directory) / "state.sqlite")
            app = sentinel.CareerSentinel(
                store=store, gmail=None, pubsub=NeverPubSub(), classifier=classifier,
                log_path=Path(directory) / "log.jsonl",
            )
            outcome = app.process_thread(value)
            self.assertTrue(outcome["alert_created"])
            self.assertEqual(len(classifier.seen[0]["messages"]), 2)
            store.close()

    def test_gateway_payload_contains_full_thread_and_reasoning_tier(self):
        captured = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({"choices": [{"message": {"content": json.dumps(raw_result("offer_received"))}}]}).encode()

        def opener(request, timeout):
            captured["body"] = json.loads(request.data.decode())
            captured["timeout"] = timeout
            return Response()

        value = thread(
            message("m1", "Earlier interview discussion."),
            message("m2", "We are sending your offer letter. Please reply.", internal_date=2),
        )
        previous = os.environ.get("OPENCLAW_GATEWAY_TOKEN")
        os.environ["OPENCLAW_GATEWAY_TOKEN"] = "test-token"
        try:
            result = sentinel.GatewayClassifier(opener=opener).classify(value)
        finally:
            if previous is None:
                os.environ.pop("OPENCLAW_GATEWAY_TOKEN", None)
            else:
                os.environ["OPENCLAW_GATEWAY_TOKEN"] = previous
        self.assertTrue(result["requires_attention"])
        self.assertEqual(captured["body"]["reasoning_effort"], "high")
        prompt_data = json.loads(captured["body"]["messages"][1]["content"])
        self.assertEqual(prompt_data["message_count"], 2)
        self.assertIn("Earlier interview discussion", prompt_data["complete_thread"])
        self.assertIn("offer letter", prompt_data["complete_thread"])


class TestDeduplicationAndFailureSafety(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.store = sentinel.StateStore(self.directory / "state.sqlite")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def app(self, classifier, delivery_runner=sentinel.run_command):
        return sentinel.CareerSentinel(
            store=self.store,
            gmail=None,
            pubsub=NeverPubSub(),
            classifier=classifier,
            delivery_runner=delivery_runner,
            log_path=self.directory / "log.jsonl",
        )

    def alert_count(self):
        return self.store.db.execute("SELECT count(*) FROM alerts").fetchone()[0]

    def test_message_thread_and_material_state_deduplication(self):
        classifier = PolicyClassifier(raw_result("interview_invited", deadline="Friday"))
        app = self.app(classifier)
        first = thread(message("m1", "Interview invitation. Please confirm by Friday."))
        self.assertTrue(app.process_thread(first)["alert_created"])
        self.assertFalse(app.process_thread(first)["alert_created"])
        self.assertEqual(self.alert_count(), 1)

        unchanged = thread(
            message("m1", "Interview invitation. Please confirm by Friday."),
            message("m2", "Reminder: please confirm by Friday.", internal_date=2),
        )
        self.assertFalse(app.process_thread(unchanged)["alert_created"])
        self.assertEqual(self.alert_count(), 1)

        classifier.result = raw_result("deadline_changed", deadline="Thursday")
        changed = thread(
            *unchanged["messages"],
            message("m3", "The interview response deadline changed to Thursday.", internal_date=3),
        )
        self.assertTrue(app.process_thread(changed)["alert_created"])
        self.assertEqual(self.alert_count(), 2)

    def test_classifier_failure_does_not_checkpoint_message(self):
        class Broken:
            def classify(self, _value):
                raise RuntimeError("temporary model failure")

        value = thread(message("m1", "Please confirm your interview availability."))
        with self.assertRaises(RuntimeError):
            self.app(Broken()).process_thread(value)
        self.assertFalse(self.store.is_message_processed("m1"))
        self.assertEqual(self.alert_count(), 0)

    def test_failed_delivery_remains_pending(self):
        classifier = PolicyClassifier(raw_result("interview_invited"))

        def failed(command, timeout):
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="temporary failure")

        app = self.app(classifier, delivery_runner=failed)
        app.process_thread(thread(message("m1", "Interview invitation. Please reply.")))
        outcome = app.deliver_pending()
        self.assertEqual(outcome, {"attempted": 1, "delivered": 0, "failed": 1, "uncertain": 0})
        status = self.store.db.execute("SELECT status FROM alerts").fetchone()[0]
        self.assertEqual(status, "pending")

    def test_uncertain_success_is_not_retried_automatically(self):
        classifier = PolicyClassifier(raw_result("interview_invited"))

        def incomplete(command, timeout):
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"payload": {"ok": True}}), stderr="")

        app = self.app(classifier, delivery_runner=incomplete)
        app.process_thread(thread(message("m1", "Interview invitation. Please reply.")))
        outcome = app.deliver_pending()
        self.assertEqual(outcome["uncertain"], 1)
        self.assertEqual(app.deliver_pending()["attempted"], 0)

    def test_notification_is_durable_before_ack(self):
        owner = self

        class PubSub:
            def pull(self):
                return [sentinel.PubSubNotification("event-1", "ack-1", {"history_id": "88"})]

            def ack(self, ack_id):
                self.acked = ack_id
                row = owner.store.db.execute(
                    "SELECT status FROM notifications WHERE event_key='event-1'"
                ).fetchone()
                owner.assertIsNotNone(row)
                owner.assertEqual(row[0], "pending")

        app = sentinel.CareerSentinel(
            store=self.store, gmail=None, pubsub=PubSub(), classifier=None,
            log_path=self.directory / "log.jsonl",
        )
        self.assertEqual(app.ingest(), 1)

    def test_silent_path_has_empty_stdout(self):
        app = self.app(PolicyClassifier(raw_result("other_action_required")))
        value = thread(message("n1", "Here are recommended jobs for you.", subject="Daily job alert"))
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            outcome = app.process_thread(value)
        self.assertEqual(outcome["status"], "silent")
        self.assertEqual(output.getvalue(), "")

    def test_dry_run_has_no_state_or_delivery_side_effect(self):
        value = thread(message("m1", "Please confirm your interview availability."))

        class Gmail:
            def recent_thread_ids(self, days, *, limit):
                return ["thread-1"]

            def get_thread(self, thread_id):
                return value

        decisions = sentinel.dry_run(
            Gmail(), PolicyClassifier(raw_result("interview_invited")), days=1, max_threads=1
        )
        self.assertTrue(decisions[0]["would_alert"])
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM alerts").fetchone()[0], 0)

    def test_reconciliation_processes_unseen_once_and_deduplicates_repeat(self):
        value = thread(message("m1", "A recruiter reviewed your candidate profile."))

        class Gmail:
            def recent_thread_ids(self, days, *, limit):
                self.query = (days, limit)
                return ["thread-1"]

            def get_thread(self, thread_id):
                return value

        gmail = Gmail()
        classifier = PolicyClassifier(raw_result(
            "no_action", requires_attention=False, requires_response=False, confidence=90
        ))
        app = sentinel.CareerSentinel(
            store=self.store,
            gmail=gmail,
            pubsub=NeverPubSub(),
            classifier=classifier,
            log_path=self.directory / "log.jsonl",
        )
        first = app.reconcile_recent(days=1, max_threads=500)
        second = app.reconcile_recent(days=1, max_threads=500)
        self.assertEqual(gmail.query, (1, 500))
        self.assertEqual(first["processed"], 1)
        self.assertEqual(second["already_processed"], 1)
        self.assertEqual(len(classifier.seen), 1)

    def test_reconciliation_continues_after_thread_failure_then_fails_run(self):
        good = thread(message("good", "Here are recommended jobs for you.", subject="Daily job alert"))

        class Gmail:
            def __init__(self):
                self.requested = []

            def recent_thread_ids(self, days, *, limit):
                return ["bad", "good"]

            def get_thread(self, thread_id):
                self.requested.append(thread_id)
                if thread_id == "bad":
                    raise RuntimeError("temporary Gmail failure")
                return good

        gmail = Gmail()
        app = sentinel.CareerSentinel(
            store=self.store,
            gmail=gmail,
            pubsub=NeverPubSub(),
            classifier=PolicyClassifier(raw_result("no_action", requires_attention=False)),
            log_path=self.directory / "log.jsonl",
        )
        with self.assertRaisesRegex(RuntimeError, "failed for 1 of 2 threads"):
            app.reconcile_recent(days=1, max_threads=500)
        self.assertEqual(gmail.requested, ["bad", "good"])
        self.assertTrue(self.store.is_message_processed("good"))

    def test_gmail_recent_search_is_bounded_and_fetches_all_pages(self):
        captured = {}

        def runner(command, timeout):
            captured["command"] = command
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps({"threads": [{"id": "t1"}, {"id": "t2"}]}),
                stderr="",
            )

        ids = sentinel.GmailClient(runner=runner).recent_thread_ids(1, limit=500)
        self.assertEqual(ids, ["t1", "t2"])
        self.assertIn("in:inbox newer_than:1d", captured["command"])
        self.assertIn("--all", captured["command"])
        self.assertIn("--max=500", captured["command"])

    def test_gog_flat_history_message_ids_resolve_to_thread_ids(self):
        commands = []

        def runner(command, timeout):
            commands.append(command)
            if "history" in command:
                payload = {
                    "historyId": "35937238",
                    "messages": ["message-1", "message-2", "message-3"],
                }
            else:
                message_id = command[command.index("get") + 1]
                thread_id = "thread-a" if message_id in {"message-1", "message-2"} else "thread-b"
                payload = {"message": {"id": message_id, "threadId": thread_id}}
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload), stderr="")

        ids, checkpoint = sentinel.GmailClient(runner=runner).history_thread_ids("35937121")

        self.assertEqual(ids, ["thread-a", "thread-b"])
        self.assertEqual(checkpoint, "35937238")
        self.assertEqual(sum("get" in command for command in commands), 3)
        for command in commands[1:]:
            self.assertIn("--format=metadata", command)

    def test_nested_history_objects_remain_supported(self):
        def runner(command, timeout):
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps({
                    "historyId": "101",
                    "history": [{"messagesAdded": [{"message": {
                        "id": "message-1", "threadId": "thread-1",
                    }}]}],
                }),
                stderr="",
            )

        ids, checkpoint = sentinel.GmailClient(runner=runner).history_thread_ids("100")
        self.assertEqual(ids, ["thread-1"])
        self.assertEqual(checkpoint, "101")

    def test_advanced_empty_history_recovers_from_notification_time(self):
        class Gmail:
            def history_thread_ids(self, since_history_id):
                self.since = since_history_id
                return [], "101"

            def thread_ids_near_publish_time(self, publish_time):
                self.publish_time = publish_time
                return ["thread-recovered"]

        gmail = Gmail()
        self.store.set_meta("last_history_id", "100")
        app = sentinel.CareerSentinel(
            store=self.store,
            gmail=gmail,
            pubsub=NeverPubSub(),
            classifier=None,
            log_path=self.directory / "log.jsonl",
        )

        ids, checkpoint = app._thread_ids_for_notification({
            "history_id": "101",
            "publish_time": "2026-07-21T08:00:40Z",
        })

        self.assertEqual(ids, ["thread-recovered"])
        self.assertEqual(checkpoint, "101")
        self.assertEqual(gmail.since, "100")
        self.assertEqual(gmail.publish_time, "2026-07-21T08:00:40Z")

    def test_cycle_lock_rejects_overlapping_process_cycle(self):
        lock_path = self.directory / "cycle.lock"
        with sentinel.cycle_lock(lock_path, timeout_seconds=0.05):
            with self.assertRaises(sentinel.CycleLockTimeout):
                with sentinel.cycle_lock(lock_path, timeout_seconds=0.05):
                    self.fail("overlapping lock unexpectedly succeeded")

    def test_cli_modes_are_mutually_exclusive(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            sentinel.build_parser().parse_args(["--reconcile", "--dry-run"])

    def test_source_has_no_email_write_capability(self):
        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        forbidden = (
            "gog gmail send", "gmail send", "smtp", "smtplib", "message reply",
            "thread modify", "mark-read", "mark-unread", "gmail draft", "gmail trash",
        )
        self.assertEqual([token for token in forbidden if token in source], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
