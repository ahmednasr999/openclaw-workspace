#!/usr/bin/env python3
"""
Pre-commit hook to prevent committing sensitive data
Installs to .git/hooks/pre-commit
"""

import os, re, sys

# Patterns that should NEVER be committed
BLOCKED_PATTERNS = [
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
    (r"xoxb-[0-9]{10,}", "Slack Bot Token"),
    (r"xoxp-[0-9]{10,}", "Slack User Token"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API Key"),
    (r"sk-antapi03-[a-zA-Z0-9\-]{40,}", "Anthropic API Key"),
    (r"AIza[0-9A-Za-z\-]{35}", "Google API Key"),
    (r"wvdklorwnunbyjir", "Gmail App Password"),
    (r"password\s*=\s*[\"'][^\"']+[\"']", "Hardcoded password"),
    (r"api_key\s*=\s*[\"'][^\"']+[\"']", "Hardcoded API key"),
    (r"secret\s*=\s*[\"'][^\"']+[\"']", "Hardcoded secret"),
]

# Files that should never be committed
BLOCKED_FILES = [
    ".env",
    ".env.local",
    ".env.*.local",
    "*.pem",
    "*.key",
    "cookies.txt",
]

def check_file(filepath):
    """Check a file for blocked patterns"""
    issues = []
    
    # Skip binary files
    if os.path.isdir(filepath):
        return issues
    
    try:
        with open(filepath, 'rb') as f:
            content = f.read(100000)  # Limit to 100KB
    except:
        return issues
    
    # Try UTF-8
    try:
        text = content.decode('utf-8')
    except:
        return issues
    
    for pattern, description in BLOCKED_PATTERNS:
        if re.search(pattern, text):
            issues.append(f"{description} found in {filepath}")
    
    return issues

def main():
    """Pre-commit hook main"""
    # Get staged files
    result = os.popen("git diff --cached --name-only").read()
    files = [f.strip() for f in result.split('\n') if f.strip()]
    
    all_issues = []
    
    for filepath in files:
        # Check blocked files
        filename = os.path.basename(filepath)
        for blocked in BLOCKED_FILES:
            if filename == blocked or filename.startswith(blocked.replace("*", "")):
                all_issues.append(f"Blocked file: {filepath}")
                continue
        
        # Check content
        issues = check_file(filepath)
        all_issues.extend(issues)
    
    if all_issues:
        print("\n🛡️ PRE-COMMIT SECURITY CHECK FAILED\n")
        print("The following issues were detected:\n")
        for issue in all_issues[:10]:
            print(f"   ❌ {issue}")
        if len(all_issues) > 10:
            print(f"   ... and {len(all_issues) - 10} more")
        print("\nPlease remove sensitive data before committing.")
        print("If this is a false positive, use --no-verify to bypass.")
        sys.exit(1)
    
    print("🛡️ Pre-commit security check passed")
    sys.exit(0)

if __name__ == "__main__":
    if "--no-verify" in sys.argv:
        sys.exit(0)
    main()
