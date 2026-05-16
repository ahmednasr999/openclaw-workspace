# Pre-Send Validation Gates (MANDATORY, BLOCKING)

Before sending any CV PDF to Ahmed, all 3 gates must pass:

1. **Model Gate (GPT-5.5-only for CV work)**
   - CV tailoring/writing must run on **openai-codex/gpt-5.5**.
   - If GPT-5.5 is unavailable, STOP and ask Ahmed before continuing.

2. **Header Gate (No extra labels)**
   - First page header must contain only:
     - `Ahmed Nasr`
     - contact line
   - Forbidden in page content: `Ahmed Nasr CV`, `[Role] - [Company]`, or any role/company header label.
   - Role/company belongs in file name only.

3. **Text Extraction Gate (automated check)**
   - Run `pdftotext` on the final PDF before send.
   - Block send if any forbidden header string appears.

If any gate fails: regenerate CV, re-check, and only then send.
