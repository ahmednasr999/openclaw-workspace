import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit-prompt-context.py"
SPEC = importlib.util.spec_from_file_location("prompt_context_audit", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PromptContextAuditTest(unittest.TestCase):
    def test_report_uses_metadata_without_message_bodies(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        tmp_path = Path(temporary.name)
        workspace = tmp_path / "workspace"
        openclaw_root = tmp_path / ".openclaw"
        workspace.mkdir()
        for name in MODULE.BOOTSTRAP_FILES:
            (workspace / name).write_text(f"# {name}\nVerify evidence before approval.\n", encoding="utf-8")

        registry = openclaw_root / "agents" / "main" / "sessions" / "sessions.json"
        registry.parent.mkdir(parents=True)
        registry.write_text(
            json.dumps(
                {
                    "agent:main:telegram:direct:123": {
                        "updatedAt": 20,
                        "contextTokens": 200000,
                        "totalTokens": 40000,
                        "inputTokens": 32000,
                        "outputTokens": 800,
                        "compactionCount": 1,
                        "messages": [{"body": "must not be read"}],
                        "systemPromptReport": {
                            "generatedAt": 20,
                            "systemPrompt": {"chars": 41000},
                            "injectedWorkspaceFiles": [{"injectedChars": 30000}],
                            "skills": {"promptChars": 15000, "entries": [{"name": "one"}]},
                            "tools": {"schemaChars": 1200},
                        },
                    },
                    "agent:main:cron:abc": {
                        "updatedAt": 30,
                        "totalTokens": 90000,
                        "inputTokens": 90000,
                    },
                }
            ),
            encoding="utf-8",
        )
        (openclaw_root / "openclaw.json").write_text(
            json.dumps(
                {
                    "plugins": {
                        "entries": {
                            "lossless-claw": {
                                "config": {"freshTailMaxTokens": 12000, "summaryPrefixTargetTokens": 12000}
                            }
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        report = MODULE.build_report(workspace, openclaw_root, 20)

        self.assertFalse(report["scope"]["message_bodies_read"])
        self.assertEqual(report["scope"]["session_sample_size"], 1)
        self.assertEqual(report["latest_prompt"]["skill_prompt_chars"], 15000)
        self.assertEqual(report["sessions"]["total_tokens"]["median"], 40000)
        self.assertEqual(report["sessions"]["lane_counts"], {"main/telegram/direct": 1})
        self.assertEqual(report["lossless_claw"]["freshTailMaxTokens"], 12000)


if __name__ == "__main__":
    unittest.main()
