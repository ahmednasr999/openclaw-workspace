#!/usr/bin/env python3
import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".venv",
    "venv",
    "__pycache__",
    ".next",
    ".idea",
    ".vscode",
}

TEXT_SUFFIXES = {
    ".sh", ".bash", ".zsh", ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx",
    ".jsx", ".json", ".yaml", ".yml", ".md", ".txt", ".toml", ".ini", ".conf",
    ".env", ".properties", ".sql", ".rb", ".go", ".rs",
}

FALSE_POSITIVE_HINTS = re.compile(
    r"example|template|placeholder|sample|demo|todo|your[-_ ]|fake|dummy|redacted",
    re.IGNORECASE,
)

@dataclass(frozen=True)
class Rule:
    id: str
    category: str
    severity: str
    pattern: str
    note: str


RULES: list[Rule] = [
    Rule("openai_key", "secret", "high", r"\bsk-[A-Za-z0-9_-]{20,}\b", "Possible OpenAI-style secret"),
    Rule("anthropic_key", "secret", "high", r"\bsk-ant-[A-Za-z0-9_-]{20,}\b", "Possible Anthropic-style secret"),
    Rule("github_token", "secret", "high", r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b", "Possible GitHub token"),
    Rule("github_pat", "secret", "high", r"\bgithub_pat_[A-Za-z0-9_]{20,}\b", "Possible GitHub PAT"),
    Rule("slack_token", "secret", "high", r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", "Possible Slack token"),
    Rule("aws_key", "secret", "high", r"\bAKIA[0-9A-Z]{16}\b", "Possible AWS access key"),
    Rule("google_api_key", "secret", "high", r"\bAIza[0-9A-Za-z_-]{35}\b", "Possible Google API key"),
    Rule("huggingface_token", "secret", "high", r"\bhf_[A-Za-z0-9]{20,}\b", "Possible Hugging Face token"),
    Rule("private_key", "secret", "high", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", "Private key material"),
    Rule("curl_pipe_shell", "network", "high", r"curl[^\n|]{0,200}\|\s*(?:bash|sh)\b", "Piped remote shell execution"),
    Rule("eval_remote", "network", "high", r"eval\s*\(\s*\$\((?:curl|wget)", "Evaluating remote command output"),
    Rule("curl_post", "network", "medium", r"\bcurl\b[^\n]{0,200}(?:--data|-d|--data-binary|-F|--form)\b", "curl sending request body or files"),
    Rule("wget_post", "network", "medium", r"\bwget\b[^\n]{0,200}(?:--post-data|--body-data)\b", "wget sending request body"),
    Rule("python_requests_write", "network", "medium", r"\brequests\.(?:post|put|patch)\s*\(", "Python code writing to remote HTTP endpoint"),
    Rule("fetch_remote_write", "network", "medium", r"\bfetch\s*\(\s*['\"]https?://", "JS fetch to remote endpoint"),
    Rule("raw_ip_url", "network", "low", r"https?://(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?", "Direct network call to raw IP"),
    Rule("rm_root", "dangerous", "high", r"\brm\s+-rf\s+/(?:\s|$)", "Dangerous recursive delete from root"),
    Rule("chmod_777", "dangerous", "medium", r"\bchmod\s+777\b", "World-writable permissions"),
    Rule("kill_all", "dangerous", "high", r"\bkill\s+-9\s+-1\b", "Kill-all command"),
    Rule("mkfs", "dangerous", "high", r"\bmkfs\.[A-Za-z0-9_+-]+\b", "Filesystem formatting command"),
    Rule("dd_to_device", "dangerous", "high", r"\bdd\b[^\n]{0,200}\bof=/dev/", "Raw disk write command"),
    Rule("sudoers_edit", "dangerous", "high", r"/etc/sudoers|/etc/sudoers\.d/", "Touching sudoers configuration"),
    Rule("cron_persistence", "persistence", "medium", r"\bcrontab\b|/etc/cron\.|/etc/cron/|/var/spool/cron", "Cron persistence or scheduled task edit"),
    Rule("launchctl", "persistence", "medium", r"\blaunchctl\b|LaunchAgent|LaunchDaemon", "macOS persistence hook"),
    Rule("systemd_enable", "persistence", "medium", r"\bsystemctl\s+enable\b|/etc/systemd/system", "systemd persistence"),
    Rule("shell_profile_write", "persistence", "medium", r"\.(?:bashrc|zshrc|profile|bash_profile)\b", "Shell profile modification"),
]


@dataclass
class Finding:
    severity: str
    category: str
    rule_id: str
    note: str
    path: str
    line: int
    excerpt: str


def is_text_candidate(path: Path) -> bool:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    name = path.name.lower()
    return name in {"dockerfile", "makefile", "justfile"}


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not is_text_candidate(path):
            continue
        try:
            if path.stat().st_size > 1_000_000:
                continue
        except OSError:
            continue
        yield path


def looks_like_false_positive(line: str) -> bool:
    return bool(FALSE_POSITIVE_HINTS.search(line))


def sanitize_excerpt(line: str, match: re.Match[str] | None) -> str:
    text = re.sub(r"\s+", " ", line.strip())
    if match:
        secret = match.group(0)
        if len(secret) > 6:
            redacted = f"{secret[:3]}...REDACTED...{secret[-2:]}"
        else:
            redacted = "REDACTED"
        text = text.replace(secret, redacted, 1)
    return text[:220]


def scan_path(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for file_path in iter_files(root):
        try:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        rel = str(file_path)
        for idx, line in enumerate(lines, start=1):
            for rule in RULES:
                match = re.search(rule.pattern, line, re.IGNORECASE)
                if not match:
                    continue
                if looks_like_false_positive(line):
                    continue
                findings.append(
                    Finding(
                        severity=rule.severity,
                        category=rule.category,
                        rule_id=rule.id,
                        note=rule.note,
                        path=rel,
                        line=idx,
                        excerpt=sanitize_excerpt(line, match if rule.category == "secret" else None),
                    )
                )
    return findings


def summarize(findings: list[Finding]) -> dict:
    by_severity = {"high": 0, "medium": 0, "low": 0}
    by_category: dict[str, int] = {}
    for finding in findings:
        by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
        by_category[finding.category] = by_category.get(finding.category, 0) + 1
    return {
        "total_findings": len(findings),
        "by_severity": by_severity,
        "by_category": dict(sorted(by_category.items())),
    }


def print_human(root: Path, findings: list[Finding]) -> None:
    summary = summarize(findings)
    print(f"Skill audit target: {root}")
    print(f"Total findings: {summary['total_findings']}")
    print(
        "Severity counts: "
        f"high={summary['by_severity'].get('high', 0)} "
        f"medium={summary['by_severity'].get('medium', 0)} "
        f"low={summary['by_severity'].get('low', 0)}"
    )
    if summary["by_category"]:
        print("Categories: " + ", ".join(f"{k}={v}" for k, v in summary["by_category"].items()))
    if not findings:
        print("No findings.")
        return
    print()
    for finding in findings:
        print(
            f"[{finding.severity.upper()}] {finding.category}/{finding.rule_id} "
            f"{finding.path}:{finding.line}"
        )
        print(f"  note: {finding.note}")
        print(f"  excerpt: {finding.excerpt}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only audit for local skill or repo directories.")
    parser.add_argument("path", help="Path to the skill or repository directory to scan")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument(
        "--fail-on",
        choices=["none", "high", "any"],
        default="none",
        help="Exit non-zero when matching findings are present",
    )
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"Directory not found: {root}", file=sys.stderr)
        return 2

    findings = scan_path(root)
    summary = summarize(findings)

    payload = {
        "target": str(root),
        "summary": summary,
        "findings": [asdict(finding) for finding in findings],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_human(root, findings)

    if args.fail_on == "any" and findings:
        return 1
    if args.fail_on == "high" and summary["by_severity"].get("high", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
