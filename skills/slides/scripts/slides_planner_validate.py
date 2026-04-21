#!/usr/bin/env python3
"""Validate slides planner pattern selection against lightweight fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import slides_plan_from_sources as planner  # noqa: E402


def match_expectation(slides: list[dict], expectation: dict) -> tuple[bool, str]:
    matched_candidates: list[dict] = []
    for slide in slides:
        if "slideNumber" in expectation and slide.get("slideNumber") != expectation["slideNumber"]:
            continue
        if "workingTitle" in expectation and slide.get("workingTitle") != expectation["workingTitle"]:
            continue
        matched_candidates.append(slide)
        if slide.get("pattern") == expectation.get("pattern"):
            return True, f"matched slide {slide.get('slideNumber')} ({slide.get('workingTitle')})"
    if matched_candidates:
        patterns = ", ".join(
            f"slide {slide.get('slideNumber')}={slide.get('pattern')!r}" for slide in matched_candidates
        )
        return False, f"matched candidates but none had expected pattern {expectation.get('pattern')!r}: {patterns}"
    return False, "no matching slide found"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate slides planner fixtures.")
    parser.add_argument(
        "--fixtures",
        default=str(Path(__file__).resolve().parent.parent / "examples" / "planner-fixtures.json"),
        help="Path to planner fixture JSON file.",
    )
    args = parser.parse_args()

    fixtures_path = Path(args.fixtures).expanduser().resolve()
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))

    failures = 0
    for fixture in fixtures:
        name = fixture["name"]
        target_slide_count = fixture["targetSlideCount"]
        entries = fixture["entries"]
        outline = planner.build_slide_outline(entries, target_slide_count)
        deck_spec = planner.build_deck_spec(entries, target_slide_count, outline)
        print(f"\n## {name}")
        print(json.dumps([
            {
                "slideNumber": slide.get("slideNumber"),
                "workingTitle": slide.get("workingTitle"),
                "pattern": slide.get("pattern"),
            }
            for slide in outline
        ], indent=2, ensure_ascii=False))
        print(f"Starter pack: {deck_spec.get('starterPack')}")

        for expectation in fixture.get("expectations", []):
            ok, detail = match_expectation(outline, expectation)
            target = expectation.get("workingTitle") or f"slide {expectation.get('slideNumber')}"
            if ok:
                print(f"PASS {target}: {detail}")
            else:
                failures += 1
                print(f"FAIL {target}: {detail}")

    if failures:
        print(f"\nValidation failed with {failures} expectation error(s).")
        return 1

    print("\nAll planner fixtures passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
