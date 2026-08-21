from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "document-to-markdown.py"
SPEC = importlib.util.spec_from_file_location("document_to_markdown", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DocumentToMarkdownRoutingTests(unittest.TestCase):
    def test_anydoc_is_preferred_for_supported_documents(self) -> None:
        for source in ("file.pdf", "file.docx", "file.xlsx", "file.csv", "file.odt"):
            with self.subTest(source=source):
                self.assertEqual(MODULE.backend_order(source, "auto"), ["anydoc", "markitdown"])

    def test_markitdown_is_preferred_for_presentations(self) -> None:
        for source in ("deck.ppt", "deck.pptx", "deck.pptm"):
            with self.subTest(source=source):
                self.assertEqual(MODULE.backend_order(source, "auto"), ["markitdown", "anydoc"])

    def test_markitdown_handles_urls_and_unknown_formats(self) -> None:
        self.assertEqual(MODULE.backend_order("https://example.com/report", "auto"), ["markitdown"])
        self.assertEqual(MODULE.backend_order("notes.txt", "auto"), ["markitdown"])

    def test_explicit_backend_bypasses_auto_routing(self) -> None:
        self.assertEqual(MODULE.backend_order("deck.pptx", "anydoc"), ["anydoc"])
        self.assertEqual(MODULE.backend_order("report.pdf", "markitdown"), ["markitdown"])


if __name__ == "__main__":
    unittest.main()
