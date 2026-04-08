# Step 0 — Pre-Flight Checks (BLOCKING, before any CV work)

1. **Model check:** Verify you are running on **Opus 4.6** (opus46). If not, STOP. Either switch to Opus or spawn a sub-agent on opus46. Never generate a CV on any other model. Zero exceptions.
2. **Full JD check:** Do you have the COMPLETE job description? If Ahmed only shared a LinkedIn URL or job title, fetch the full JD first using `scripts/linkedin-jd-fetcher.py` or ask Ahmed to paste it. Never score or build a CV from title/summary alone (learned from Anduril incident: title said 85%, full JD revealed 64%).
3. **Duplicate check:** Search `cvs/` directory for existing CV for this company/role. If found, confirm with Ahmed before rebuilding.
