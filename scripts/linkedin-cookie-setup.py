#!/usr/bin/env python3
"""Disabled LinkedIn cookie setup.

LinkedIn cookies must not be extracted, stored, refreshed, or used. Use JobSpy for job descriptions, Composio for approved posting, or a live visible browser session when account state matters.
"""

import sys


def main():
    print("ERROR: LinkedIn cookie setup is disabled by policy. Do not use li_at or JSESSIONID cookies.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
