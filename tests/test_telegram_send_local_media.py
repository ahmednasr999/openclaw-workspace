from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "telegram-send-local-media.py"
SPEC = importlib.util.spec_from_file_location("telegram_send_local_media", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class TelegramMediaReceiptTests(unittest.TestCase):
    def test_accepts_real_message_receipt(self):
        raw = json.dumps({"payload": {"ok": True, "messageId": "61246"}})
        success, message_id, _ = MODULE.parse_result(raw)
        self.assertTrue(success)
        self.assertEqual(message_id, "61246")

    def test_rejects_ok_without_message_id(self):
        raw = json.dumps({"payload": {"ok": True}})
        success, message_id, _ = MODULE.parse_result(raw)
        self.assertFalse(success)
        self.assertIsNone(message_id)

    def test_rejects_message_id_without_ok(self):
        raw = json.dumps({"payload": {"ok": False, "messageId": "61246"}})
        success, _, _ = MODULE.parse_result(raw)
        self.assertFalse(success)

    def test_accepts_json_after_runtime_warning(self):
        raw = "runtime warning\n" + json.dumps({"payload": {"ok": True, "messageId": "70001"}})
        success, message_id, _ = MODULE.parse_result(raw)
        self.assertTrue(success)
        self.assertEqual(message_id, "70001")


if __name__ == "__main__":
    unittest.main()
