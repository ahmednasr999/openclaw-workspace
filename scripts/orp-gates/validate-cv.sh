#!/bin/bash
# ORP Gate Script: CV Validation
# Usage: validate-cv.sh <pdf_path>
# Exit 0 = all gates pass, Exit 1 = gate failure

set -e

PDF_PATH="$1"

if [ -z "$PDF_PATH" ]; then
  echo "GATE FAIL: No PDF path provided"
  exit 1
fi

if [ ! -f "$PDF_PATH" ]; then
  echo "GATE FAIL: PDF file does not exist: $PDF_PATH"
  exit 1
fi

# Extract text from PDF
TEXT=$(pdftotext "$PDF_PATH" - 2>/dev/null)

if [ -z "$TEXT" ]; then
  echo "GATE FAIL: PDF text extraction returned empty"
  exit 1
fi

# Gate B: Header check - no role/company label in first 3 lines
FIRST_LINES=$(echo "$TEXT" | head -n 3)

# Check for "Ahmed Nasr CV" pattern
if echo "$FIRST_LINES" | grep -qi "Ahmed Nasr CV"; then
  echo "GATE FAIL: Found 'Ahmed Nasr CV' in header. Remove extra label."
  exit 1
fi

# Check for role-company pattern like "Ahmed Nasr - Role - Company"
if echo "$FIRST_LINES" | grep -qiE "Ahmed Nasr\s*[-]+\s*"; then
  echo "GATE FAIL: Found role/company label in header. Header must be name + contact only."
  exit 1
fi

# Gate B: No em dashes anywhere
if echo "$TEXT" | grep -qP '\x{2014}'; then
  echo "GATE FAIL: Em dash found in CV content. Replace with commas, periods, or colons."
  exit 1
fi

# Gate C: Verify first line is "Ahmed Nasr"
FIRST_LINE=$(echo "$TEXT" | head -n 1 | xargs)
if [ "$FIRST_LINE" != "Ahmed Nasr" ]; then
  echo "GATE FAIL: First line is '$FIRST_LINE', expected 'Ahmed Nasr'"
  exit 1
fi

# Gate C: Verify contact line exists
if ! echo "$TEXT" | head -n 5 | grep -q "ahmednasr999@gmail.com"; then
  echo "GATE FAIL: Contact email not found in header area"
  exit 1
fi

# Gate C: Verify Executive Summary exists
if ! echo "$TEXT" | grep -qi "Executive Summary"; then
  echo "GATE FAIL: Executive Summary section missing"
  exit 1
fi

# Gate C: Verify Professional Experience exists
if ! echo "$TEXT" | grep -qi "Professional Experience\|Experience"; then
  echo "GATE FAIL: Professional Experience section missing"
  exit 1
fi

echo "ALL GATES PASSED"
exit 0
