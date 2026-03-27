# HR Agent Quality Checklist — eval/checklist.md

Run this checklist before closing any HR task. All items are binary: PASS or FAIL.

---

## Before Marking Any Task Done

### 1. Duplicate Guard
- [ ] **PASS:** New job checked against SQLite AND Notion before adding — no duplicate exists
- [ ] **FAIL:** Job added without duplicate check → remove duplicate, log lesson

### 2. CV Coverage
- [ ] **PASS:** Every job in "Applied" status has a tailored CV PDF attached in Notion
- [ ] **FAIL:** Applied job missing CV → build CV before next pipeline sync

### 3. Interview Prep Coverage
- [ ] **PASS:** Every job in "Interview" status has a prep brief in Notion notes field
- [ ] **FAIL:** Interview job missing prep → run interviews.md workflow immediately

### 4. Stale Application Check
- [ ] **PASS:** No job has been in "Applied" status for >14 days without a follow-up action logged
- [ ] **FAIL:** Stale apps found → draft follow-up for Ahmed's approval, flag to CEO

### 5. Outreach Tracking
- [ ] **PASS:** Every recruiter who responded (positive or negative) has their response logged in ontology graph with updated `response_status` and `last_contacted`
- [ ] **FAIL:** Untracked response found → update ontology immediately

### 6. Discovery Rate
- [ ] **PASS:** At least 5 new jobs discovered and added to pipeline in the past 7 days
- [ ] **FAIL:** Discovery rate below target → run job search across all platforms, report to CEO

### 7. Source Documentation
- [ ] **PASS:** Every application in the pipeline has a `source` field populated (LinkedIn / Bayt / Naukri / Indeed / Glassdoor / ZipRecruiter / Google Jobs / Referral / Outreach / Other)
- [ ] **FAIL:** Missing source → research and fill, or mark "Unknown"

---

## Weekly Checklist (Run Every Monday)

- [ ] Pipeline summary posted to topic 9
- [ ] Stale apps reviewed and follow-ups drafted
- [ ] Outreach queue checked for pending responses
- [ ] CEO briefed on pipeline status
- [ ] Ontology graph in sync with Notion (spot-check 3 entries)
- [ ] At least 5 new job discoveries initiated for the week

---

## Score Reporting

After running the checklist, report to CEO with:
```
✅ HR Checklist: {date}
Passed: {n}/7 checks
Failed: {list any failures with action taken}
```
