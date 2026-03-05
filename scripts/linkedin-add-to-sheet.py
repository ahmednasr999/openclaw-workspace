#!/usr/bin/env python3
"""
Add a scored job to the NASR Job Pipeline Google Sheet.
Usage: python3 linkedin-add-to-sheet.py --url URL --title TITLE --company COMPANY
       --jd JD_FILE --score 85 --verdict GO --reason "Strong match" --gaps "gap1|gap2"
"""

import subprocess
import json
import argparse
import sys
import os
import re
from datetime import datetime

SHEET_ID = "1uKOh3XlsVb6SC0tAHkr239N4Y2d2fQr_BiQJcMHrjNw"
ACCOUNT  = "ahmednasr999@gmail.com"
GOG_ENV  = {"GOG_KEYRING_PASSWORD": "pass@123", **os.environ}

def gog(cmd: list) -> dict:
    result = subprocess.run(
        ["gog"] + cmd + ["--account", ACCOUNT, "--json"],
        capture_output=True, text=True, env=GOG_ENV
    )
    if result.returncode != 0:
        raise RuntimeError(f"gog error: {result.stderr}")
    return json.loads(result.stdout) if result.stdout.strip() else {}

def get_next_row() -> int:
    """Find the next empty row in the sheet."""
    data = gog(["sheets", "get", SHEET_ID, "Sheet1!A:A"])
    values = data.get("values", [])
    return len(values) + 1

def check_duplicate(url: str) -> bool:
    """Check if URL already exists in column A."""
    data = gog(["sheets", "get", SHEET_ID, "Sheet1!A:A"])
    values = data.get("values", [])
    for row in values:
        if row and url.split("?")[0].rstrip("/") in row[0]:
            return True
    return False

def add_job(url, title, company, jd, score, verdict, reason, gaps):
    """Append a job row to the sheet."""

    # Duplicate check
    if check_duplicate(url):
        return {"status": "duplicate", "message": f"Already in sheet: {url}"}

    next_row = get_next_row()

    # Column layout: A=Link, B=Company, C=Role Title, D=Full JD,
    #                E=Salary, F=Notes, G=ATS Score, H=Decision,
    #                I=Reason, J=CV Status, K=Ahmed Decision,
    #                L=Applied Date, M=CV GitHub Link
    row_data = [
        url,                          # A: Link
        company,                      # B: Company
        title,                        # C: Role Title
        jd[:5000],                    # D: Full JD (trimmed)
        "",                           # E: Salary
        gaps,                         # F: Notes (gaps)
        f"{score}%",                  # G: ATS Score
        verdict,                      # H: Decision
        reason,                       # I: Reason
        "Discovered",                 # J: CV Status
        "",                           # K: Ahmed Decision
        "",                           # L: Applied Date
        "",                           # M: CV GitHub Link
    ]

    values_json = json.dumps([row_data])
    range_ref = f"Sheet1!A{next_row}:M{next_row}"

    subprocess.run(
        ["gog", "sheets", "update", SHEET_ID, range_ref,
         "--values-json", values_json, "--input", "USER_ENTERED",
         "--account", ACCOUNT],
        capture_output=True, text=True, env=GOG_ENV, check=True
    )

    return {
        "status": "added",
        "row": next_row,
        "message": f"Added to Sheet row {next_row}: {title} at {company} ({score}%)"
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url",     required=True)
    parser.add_argument("--title",   required=True)
    parser.add_argument("--company", default="Unknown")
    parser.add_argument("--jd",      required=True, help="Path to JD text file or inline text")
    parser.add_argument("--score",   required=True, type=int)
    parser.add_argument("--verdict", required=True, choices=["GO", "SKIP"])
    parser.add_argument("--reason",  default="")
    parser.add_argument("--gaps",    default="")
    args = parser.parse_args()

    # Load JD from file or inline
    if os.path.exists(args.jd):
        with open(args.jd) as f:
            jd = f.read()
    else:
        jd = args.jd

    result = add_job(
        url=args.url,
        title=args.title,
        company=args.company,
        jd=jd,
        score=args.score,
        verdict=args.verdict,
        reason=args.reason,
        gaps=args.gaps
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
