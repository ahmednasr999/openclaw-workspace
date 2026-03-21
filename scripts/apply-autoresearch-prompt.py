#!/usr/bin/env python3
"""
apply-autoresearch-prompt.py — Human-in-the-loop step to apply an autoresearch prompt candidate.

Shows a diff of what changed and replaces the LLM prompt in jobs-review.py.
Run manually after reviewing the candidate:

    python3 scripts/apply-autoresearch-prompt.py           # interactive review + confirm
    python3 scripts/apply-autoresearch-prompt.py --auto    # auto-apply latest (CI/trusted use only)
    python3 scripts/apply-autoresearch-prompt.py --version 2  # apply specific version
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
SCRIPTS_DIR = WORKSPACE / "scripts"
DATA_DIR = WORKSPACE / "data"

JOBS_REVIEW_SCRIPT = SCRIPTS_DIR / "jobs-review.py"
AUTORESEARCH_DIR = DATA_DIR / "autoresearch"
PROMPT_CANDIDATES_DIR = AUTORESEARCH_DIR / "prompt-candidates"
LOG_FILE = AUTORESEARCH_DIR / "job-review-log.json"


def get_latest_candidate() -> Path | None:
    """Get the latest prompt candidate file."""
    candidates = sorted(
        PROMPT_CANDIDATES_DIR.glob("prompt-v[0-9]*.md"),
        key=lambda p: int(re.search(r"v(\d+)", p.name).group(1)),
    )
    if not candidates:
        return None
    return candidates[-1]


def get_candidate_by_version(version: int) -> Path | None:
    """Get a prompt candidate by version number."""
    path = PROMPT_CANDIDATES_DIR / f"prompt-v{version}.md"
    return path if path.exists() else None


def extract_prompt_from_candidate(candidate_path: Path) -> str:
    """Extract the prompt block from a candidate .md file."""
    with open(candidate_path) as f:
        content = f.read()

    # Extract content between ```...```
    match = re.search(r"```\n(.*?)\n```", content, re.DOTALL)
    if match:
        return match.group(1)

    return ""


def extract_prompt_from_script(script_content: str) -> tuple[str, int, int]:
    """Extract the current prompt block from jobs-review.py, return (block, start_idx, end_idx)."""
    # Match: prompt = f"""..."""
    match = re.search(r'(prompt\s*=\s*f""")(.*?)(""")', script_content, re.DOTALL)
    if match:
        return match.group(2), match.start(2), match.end(2)
    return "", -1, -1


def show_diff(old_prompt: str, new_prompt: str):
    """Show a unified diff between old and new prompt."""
    import difflib

    old_lines = old_prompt.splitlines(keepends=True)
    new_lines = new_prompt.splitlines(keepends=True)

    diff = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="current prompt",
            tofile="candidate prompt",
            lineterm="",
        )
    )

    if not diff:
        print("  No differences found.")
        return

    print(f"\n{'=' * 60}")
    print("DIFF (current → candidate):")
    print("=" * 60)
    for line in diff[:100]:  # cap at 100 lines for readability
        if line.startswith("+"):
            print(f"\033[92m{line}\033[0m", end="")  # green
        elif line.startswith("-"):
            print(f"\033[91m{line}\033[0m", end="")  # red
        elif line.startswith("@"):
            print(f"\033[94m{line}\033[0m", end="")  # blue
        else:
            print(line, end="")

    if len(diff) > 100:
        print(f"\n  ... (truncated, {len(diff) - 100} more lines)")

    print(f"\n{'=' * 60}")


def apply_prompt(script_content: str, new_prompt_block: str) -> str:
    """Replace the prompt block in jobs-review.py with the new one."""
    old_block, start, end = extract_prompt_from_script(script_content)
    if start == -1:
        raise ValueError("Could not find prompt block in jobs-review.py")

    return script_content[:start] + new_prompt_block + script_content[end:]


def backup_script():
    """Create a backup of jobs-review.py before applying changes."""
    backup_path = JOBS_REVIEW_SCRIPT.with_suffix(".py.bak")
    import shutil
    shutil.copy(JOBS_REVIEW_SCRIPT, backup_path)
    print(f"  Backup saved to: {backup_path}")


def git_commit(message: str):
    """Git commit the updated jobs-review.py."""
    try:
        subprocess.run(
            ["git", "-C", str(WORKSPACE), "add", str(JOBS_REVIEW_SCRIPT)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(WORKSPACE), "commit", "-m", message],
            check=True,
            capture_output=True,
        )
        print(f"  Git committed: {message}")
    except subprocess.CalledProcessError as e:
        print(f"  Git commit failed: {e.stderr.decode()[:200]}")


def main():
    parser = argparse.ArgumentParser(
        description="Apply an autoresearch prompt candidate to jobs-review.py"
    )
    parser.add_argument("--auto", action="store_true", help="Auto-apply without confirmation prompt")
    parser.add_argument("--version", type=int, help="Apply a specific prompt version")
    parser.add_argument("--list", action="store_true", help="List available prompt candidates")
    args = parser.parse_args()

    # List mode
    if args.list:
        candidates = sorted(
            PROMPT_CANDIDATES_DIR.glob("prompt-v[0-9]*.md"),
            key=lambda p: int(re.search(r"v(\d+)", p.name).group(1)),
        )
        if not candidates:
            print("No prompt candidates found in data/autoresearch/prompt-candidates/")
            print("Run: python3 scripts/autoresearch-job-review.py to generate one.")
            sys.exit(0)

        print("\nAvailable prompt candidates:")
        for c in candidates:
            print(f"  {c.name}")
        print(f"\nLatest: {candidates[-1].name}")
        sys.exit(0)

    # Find candidate
    if args.version:
        candidate_path = get_candidate_by_version(args.version)
        if not candidate_path:
            print(f"Error: Prompt candidate v{args.version} not found.")
            sys.exit(1)
    else:
        candidate_path = get_latest_candidate()
        if not candidate_path:
            print("No prompt candidates found.")
            print("Run: python3 scripts/autoresearch-job-review.py to generate one.")
            sys.exit(1)

    print(f"\nCandidate: {candidate_path.name}")
    print(f"Source: {candidate_path}")

    # Load candidate and current script
    new_prompt_block = extract_prompt_from_candidate(candidate_path)
    if not new_prompt_block:
        print(f"Error: Could not extract prompt block from {candidate_path}")
        sys.exit(1)

    with open(JOBS_REVIEW_SCRIPT) as f:
        script_content = f.read()

    current_prompt_block, _, _ = extract_prompt_from_script(script_content)
    if not current_prompt_block:
        print("Error: Could not find current prompt block in jobs-review.py")
        print("Check that build_review_prompt() contains: prompt = f\"\"\"...\"\"\"")
        sys.exit(1)

    # Show diff
    show_diff(current_prompt_block, new_prompt_block)

    # Confirm
    if not args.auto:
        try:
            answer = input("\nApply this prompt to jobs-review.py? [y/N] ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(0)

        if answer != "y":
            print("Aborted. Prompt NOT applied.")
            print(f"\nTo apply later: python3 scripts/apply-autoresearch-prompt.py --version {re.search(r'v(\\d+)', candidate_path.name).group(1)}")
            sys.exit(0)
    else:
        print("\n[--auto] Applying without confirmation...")

    # Apply
    backup_script()
    updated_script = apply_prompt(script_content, new_prompt_block)

    with open(JOBS_REVIEW_SCRIPT, "w") as f:
        f.write(updated_script)

    version_num = re.search(r"v(\d+)", candidate_path.name).group(1)
    print(f"\n✅ Applied prompt v{version_num} to jobs-review.py")

    # Git commit
    git_commit(f"apply autoresearch prompt v{version_num} to jobs-review.py")

    print("\nDone. Test with:")
    print("  python3 scripts/jobs-review.py --dry-run")


if __name__ == "__main__":
    main()
