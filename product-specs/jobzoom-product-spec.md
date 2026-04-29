# JobZoom Product Specification

## 1. Product Name

**JobZoom**

## 2. One-Line Description

JobZoom is a paid monthly GCC job-search automation service where a user uploads their CV once, and the system sends them a daily email containing a PDF report of the best matching GCC jobs plus a ZIP file of tailored ATS-friendly CVs for those roles.

## 3. Product Vision

JobZoom is not a job board, not a generic AI CV writer, and not an auto-apply bot.

It is a **daily job-search production engine** for serious professionals targeting GCC opportunities.

The product should make the user feel:

> “Every morning, JobZoom has scanned the GCC market for me, selected the roles worth my attention, and prepared tailored CVs so I can apply quickly.”

## 4. Target Customer

### Primary Segment

Professionals targeting jobs across GCC countries:

- Saudi Arabia
- United Arab Emirates
- Qatar
- Kuwait
- Bahrain
- Oman

### Best-Fit Users

The product is best suited for:

- senior professionals
- managers
- senior managers
- directors
- PMO leaders
- operations leaders
- IT leaders
- digital transformation professionals
- healthcare / technology / business transformation professionals
- expatriates seeking GCC opportunities
- professionals actively looking for a better role

### Not Ideal For

JobZoom is not optimized for:

- fresh graduates
- junior workers
- blue-collar mass hiring
- users expecting guaranteed jobs
- users expecting JobZoom to apply on their behalf

## 5. Pricing Model

### Single Plan

**$200 per month**

No complicated tiers at launch.

### Included

- CV upload and parsing
- ATS-optimized master CV generation
- automatic career path and position-title generation
- daily GCC-wide job scanning
- daily matching and scoring
- daily PDF report
- daily ZIP file of tailored CVs for top matches
- email delivery
- weekly summary can be added later

### Important Limits

To control cost, quality, and user experience:

- Generate tailored CVs only for the strongest matches.
- Recommended cap: **maximum 5 tailored CVs per user per day**.
- If no strong matches are found, send a “No strong matches today” report instead of forcing weak CVs.

## 6. Core Product Promise

User uploads CV once.

JobZoom then does the daily work:

1. Understands the user’s career history.
2. Creates an ATS-safe master CV.
3. Identifies suitable job titles based on the user’s career path.
4. Searches all GCC countries daily.
5. Scores jobs against the user profile.
6. Generates tailored CVs for the strongest matches.
7. Sends a daily email with:
   - a PDF report
   - a ZIP file containing tailored CVs

## 7. What JobZoom Must Not Promise

JobZoom must not promise:

- guaranteed interviews
- guaranteed job offers
- guaranteed recruiter responses
- automatic application submission
- fake experience enhancement
- inflated credentials
- visa sponsorship guarantees
- full coverage of every job in the market

Recommended disclaimer:

> JobZoom helps you discover relevant opportunities and prepare tailored application documents. It does not guarantee interviews, offers, or hiring outcomes.

## 8. User Journey

### Step 1: Landing Page

User visits the JobZoom website.

Landing page explains:

- Upload your CV once.
- We scan GCC jobs daily.
- We send you a PDF report and tailored CV pack every day.
- One plan: $200/month.

Primary CTA:

> Start JobZoom

Secondary CTA:

> View sample report

### Step 2: Signup

User creates an account with:

- name
- email
- password or magic link login
- country of residence, optional
- preferred contact email

### Step 3: Payment

User pays $200/month through Stripe or equivalent payment provider.

Payment status must be stored in the user database.

If payment is inactive, daily processing should stop.

### Step 4: CV Upload

User uploads their CV.

Accepted formats:

- PDF
- DOCX

Optional later:

- LinkedIn profile URL
- portfolio URL

### Step 5: CV Parsing

System extracts structured profile data:

- full name
- email
- phone, if available
- current title
- current company
- total years of experience
- countries worked in
- industries
- companies
- job titles
- responsibilities
- achievements
- education
- certifications
- skills
- technologies
- languages
- project types
- leadership scope

The system must not invent facts.

If a fact is not in the uploaded CV, it must not be added as a factual claim.

### Step 6: Master ATS CV Generation

System creates an optimized ATS master CV.

Requirements:

- single column
- no tables
- no text boxes
- no icons
- no images
- no graphics
- no headers/footers that hide important text
- standard section titles
- clear bullet points
- keyword-rich but factual
- reverse chronological experience
- simple PDF/DOCX export

Sections:

- Professional Summary
- Core Skills
- Professional Experience
- Education
- Certifications
- Languages, if available

The master CV becomes the source for tailoring.

### Step 7: Career Path and Position-Title Generation

System generates target job-title tracks based on the user’s previous career path.

For each user, generate:

1. Direct-fit titles
2. Adjacent-fit titles
3. Stretch titles
4. Titles to avoid, optional internal list

Example output for a PMO/digital transformation user:

Direct-fit:

- Program Manager
- Senior Program Manager
- PMO Manager
- Portfolio Manager
- Digital Transformation Manager

Adjacent-fit:

- Operations Manager
- Business Excellence Manager
- Transformation Lead
- IT Project Manager

Stretch-fit:

- PMO Director
- Head of Transformation
- Director of Operations

The system should use these generated titles to build search queries.

### Step 8: Daily GCC Job Search

Every day, the system searches jobs across:

- Saudi Arabia
- United Arab Emirates
- Qatar
- Kuwait
- Bahrain
- Oman

The system should use the generated title tracks and career keywords.

Job sources can include:

- LinkedIn Jobs
- Indeed
- Bayt
- GulfTalent
- Naukrigulf
- company career pages, later
- other supported sources

The system should not depend on one source only.

### Step 9: Job Normalization

For every job found, store:

- job ID
- source
- source URL
- title
- company
- country
- city, if available
- posted date, if available
- discovered date
- description
- seniority
- employment type, if available
- salary, if available
- required skills
- required experience
- industry
- raw source data

### Step 10: Deduplication

The same job may appear multiple times.

Deduplicate by:

- source job ID
- URL
- title + company + country
- fuzzy matching title/company/description

Keep one canonical job record.

### Step 11: User-Specific Matching

Each job is scored against each active user profile.

Scoring should consider:

- title fit
- seniority fit
- industry fit
- skills fit
- experience fit
- country fit
- keyword match
- leadership fit
- career path relevance
- risk factors

Score range:

- 0 to 100

Recommended interpretation:

- 85-100: excellent match
- 75-84: strong match
- 70-74: possible match
- 60-69: near miss / watchlist
- under 60: do not include

Daily tailored CV generation should normally happen only for jobs scoring 70+ or 75+, depending on calibration.

### Step 12: Match Explanation

Every selected job must include an explanation.

Required fields:

- why it matches
- why it may not be perfect
- recommended positioning angle
- suggested CV filename
- application URL

Example:

> Strong fit because the role requires enterprise PMO, stakeholder management, vendor governance, and digital transformation experience. Main concern: the title is manager-level rather than director-level.

### Step 13: Tailored CV Generation

For each top matched job, generate a tailored CV.

Rules:

- Use only facts from the uploaded CV/master profile.
- Mirror job description keywords naturally.
- Do not invent achievements.
- Do not invent employers.
- Do not invent certifications.
- Do not invent tools.
- Do not change employment dates.
- Keep ATS-safe formatting.
- Output as PDF and optionally DOCX later.

Recommended filename format:

`{User Name} - {Job Title} - {Company}.pdf`

Example:

`Ahmed Nasr - Program Manager - Amazon.pdf`

### Step 14: Daily PDF Report Generation

The PDF report is the main user-facing decision brief.

It should be clean, premium, and easy to read.

Report sections:

#### 1. Header

- JobZoom Daily Report
- user name
- date
- generated time

#### 2. Today’s Summary

Example:

- Jobs scanned: 1,240
- Strong matches: 4
- Tailored CVs generated: 4
- Countries with matches: UAE, Saudi Arabia, Qatar

#### 3. Recommended Action

Example:

> Apply first to: Program Manager at Malomatia, Senior Commercial Project Manager at Siemens, Infrastructure Project Manager at Dautom.

#### 4. Top Matches

For each match:

- rank
- job title
- company
- country/city
- score
- why it fits
- concern/gap
- application link
- tailored CV filename

#### 5. Near Misses

Include jobs scoring 60-69 or jobs worth monitoring.

Fields:

- score
- title
- company
- country
- reason it missed

#### 6. Market Signals

Simple insights:

- most active country today
- most common title track
- recurring skills in matched jobs
- suggested profile improvement, if relevant

#### 7. Footer

- disclaimer
- next scan time
- support email

### Step 15: ZIP File Generation

The system creates one ZIP file per user per day.

ZIP contains:

- tailored CV PDFs for the top matched jobs
- optionally a text file listing application URLs

ZIP filename:

`JobZoom_CV_Pack_{UserName}_{YYYY-MM-DD}.zip`

### Step 16: Daily Email Delivery

User receives one email daily.

Subject example:

`JobZoom Daily: 4 GCC matches and 4 tailored CVs ready`

Email body example:

```
Hi {Name},

Your JobZoom daily report is ready.

Today we scanned GCC opportunities and found {X} strong matches for your profile.

Attached:
1. Your daily PDF report
2. ZIP file with tailored CVs

Recommended first application: {Top Job Title} at {Company}, score {Score}/100.

Regards,
JobZoom
```

Attachments:

1. PDF report
2. ZIP CV pack

If attachments become too large, use secure download links instead.

## 9. Admin Dashboard Requirements

Admin dashboard is internal only for MVP.

Admin should see:

- total users
- active subscriptions
- inactive subscriptions
- uploaded CV status
- latest daily run per user
- number of matches per user
- number of CVs generated
- email delivery status
- failed runs
- error logs
- manual resend button
- manual pause/resume user

## 10. User Dashboard Requirements

For MVP, user dashboard can be minimal.

User should be able to:

- login
- upload/replace CV
- see subscription status
- download latest report
- download latest ZIP
- cancel subscription
- request data deletion

A full dashboard with job tracking can be added later.

## 11. Database Entities

### User

Fields:

- id
- name
- email
- password hash or auth provider ID
- subscription status
- stripe customer ID
- created at
- updated at

### User Profile

Fields:

- user id
- parsed CV JSON
- master profile JSON
- target title tracks
- skills
- industries
- seniority level
- countries of interest, default all GCC
- generated master CV path

### Uploaded CV

Fields:

- id
- user id
- original filename
- file path
- file type
- upload date
- parsed status
- parsing errors

### Job

Fields:

- id
- source
- source job id
- url
- title
- company
- country
- city
- description
- posted date
- discovered date
- normalized data JSON
- active/expired status

### Job Match

Fields:

- id
- user id
- job id
- score
- score band
- explanation
- concern/gap
- positioning angle
- match date
- selected for report true/false
- selected for CV true/false

### Generated CV

Fields:

- id
- user id
- job id
- match id
- filename
- file path
- generated date
- status

### Daily Report

Fields:

- id
- user id
- date
- PDF path
- ZIP path
- jobs scanned
- matches count
- CVs generated count
- email status
- generated at

### Email Delivery

Fields:

- id
- user id
- report id
- recipient email
- subject
- provider message id
- status
- sent at
- error message

## 12. Technical Architecture

### Recommended MVP Architecture

Frontend:

- simple web app
- landing page
- signup/login
- CV upload
- subscription/payment page
- basic user dashboard

Backend:

- API server
- background job worker
- scheduler/cron
- database
- file storage
- email service
- payment integration

Database:

- PostgreSQL recommended

Storage:

- S3-compatible storage recommended
- local storage acceptable only for early prototype

Email:

- SendGrid, Postmark, Amazon SES, Mailgun, or similar

Payments:

- Stripe or Paddle

PDF generation:

- HTML to PDF or document template engine

CV generation:

- deterministic template with AI-generated content inserted into safe sections

Job processing:

- central daily job scan
- per-user matching workers
- per-user CV/report generation

## 13. Daily Processing Flow

Recommended daily sequence:

1. Start daily job scan.
2. Search all GCC countries using all active title tracks.
3. Normalize jobs.
4. Deduplicate jobs.
5. For each active paid user:
   - score jobs against profile
   - select top matches
   - generate tailored CVs
   - generate PDF report
   - create ZIP file
   - send email
   - log success/failure
6. Send admin summary.

## 14. Failure Handling

The system must handle failures gracefully.

Examples:

### Job scan fails

- retry
- use cached jobs from previous scan
- alert admin
- do not send misleading report

### One user report fails

- mark that user as failed
- continue processing other users
- alert admin

### CV generation fails for one job

- include the job in report
- mark CV as not generated
- continue with other CVs

### Email fails

- retry
- log provider error
- alert admin
- allow manual resend

## 15. Security and Privacy Requirements

CV data is sensitive.

Minimum requirements:

- HTTPS
- secure authentication
- encrypted database backups
- private file storage
- signed URLs for downloads
- no public file paths
- access control by user ID
- admin access protected
- delete user data on request
- privacy policy
- terms of service

Critical rule:

A user must never access another user’s CV, report, ZIP file, or profile data.

## 16. Quality Rules

### Matching Quality

- Do not include weak jobs just to make the report look full.
- Better to send 2 strong matches than 10 weak ones.
- Explain gaps honestly.

### CV Quality

- ATS-safe formatting only.
- No fabricated claims.
- No exaggerated titles.
- No fake certifications.
- Use clear measurable achievements only if present in original CV.

### Report Quality

- User-facing language.
- No internal technical terms like pass 1, pass 2, scraping health, fuzzy dedupe.
- Keep it action-focused.

## 17. MVP Scope

### Must Have

- landing page
- user signup/login
- payment
- CV upload
- CV parsing
- master ATS CV generation
- title-track generation
- GCC job scan
- job dedupe
- scoring
- tailored CV generation
- PDF report generation
- ZIP generation
- daily email delivery
- admin run monitoring

### Should Have

- latest report download in dashboard
- manual resend
- failure alerts
- user cancellation
- data deletion request

### Not Needed for MVP

- auto-apply
- mobile app
- advanced analytics dashboard
- recruiter messaging
- interview preparation
- complex user customization
- multiple pricing tiers
- in-app job tracker

## 18. Success Metrics

### Product Metrics

- active paying users
- daily reports successfully delivered
- report open rate
- number of tailored CVs generated
- cancellation rate
- users retained after 30 days

### Quality Metrics

- user-rated match relevance
- percentage of matches users apply to
- number of complaints about irrelevant jobs
- number of CV correction requests

### Business Metrics

- monthly recurring revenue
- cost per user
- gross margin
- support time per user
- churn rate

## 19. Beta Plan

### Beta Size

Start with 10 users.

### Beta Price

Either:

- full price: $200/month
- or founding beta price: $99/month for first month only

### Beta Duration

30 days.

### Beta Goal

Prove users are willing to pay and find the daily report/CV pack valuable.

### Beta Success Criteria

Proceed if:

- at least 7 out of 10 users remain active after 30 days
- users open reports at least 3 times per week
- users apply using generated CVs
- support time stays manageable
- match quality feedback is positive

## 20. Main Risks

### Risk: Bad match quality

Mitigation:

- strict thresholds
- cap CVs per day
- explain matches clearly
- collect feedback

### Risk: AI fabricates CV details

Mitigation:

- source CV as only truth
- structured profile extraction
- validation checks
- no unsupported claims

### Risk: Job source instability

Mitigation:

- multiple sources
- caching
- monitoring
- source fallback

### Risk: Email attachments too large

Mitigation:

- cap CV count
- compress ZIP
- switch to secure links if needed

### Risk: User data leakage

Mitigation:

- tenant isolation
- private storage
- access-control testing
- user-specific file paths

### Risk: Too much support

Mitigation:

- simple one-plan product
- no custom preferences at MVP
- clear terms
- strong onboarding

## 21. Recommended Build Phases

### Phase 1: Prototype Productization

Goal: make current JobZoom work for multiple users manually.

Deliverables:

- user profile folder structure
- CV parser
- profile JSON
- daily report/CV output per user
- manual email sending

### Phase 2: MVP Automation

Goal: automate daily processing and delivery.

Deliverables:

- database
- scheduler
- email provider
- payment status check
- admin monitoring

### Phase 3: Customer Portal

Goal: allow users to self-serve.

Deliverables:

- login
- CV upload
- subscription page
- latest report download
- cancellation

### Phase 4: Scale Hardening

Goal: improve reliability and quality.

Deliverables:

- multi-source job ingestion
- feedback loop
- secure download links
- monitoring dashboard
- cost optimization

## 22. AI Builder Instructions

If an AI builder is implementing this product, they should not build a generic job board.

They should build a daily automated pipeline:

CV Upload -> Profile Extraction -> ATS Master CV -> Title Tracks -> GCC Job Scan -> Job Matching -> Tailored CVs -> PDF Report -> ZIP -> Daily Email.

The first implementation should prioritize:

1. correctness
2. user data isolation
3. report/CV quality
4. reliable delivery
5. simple admin visibility

Do not prioritize advanced UI before the backend workflow works reliably.

## 23. Definition of Done for MVP

The MVP is done when:

1. A user can sign up and pay.
2. A user can upload a CV.
3. The system can parse the CV and create a structured profile.
4. The system can generate an ATS master CV.
5. The system can generate job-title tracks.
6. The system can scan GCC jobs daily.
7. The system can score jobs against the user profile.
8. The system can select top matches.
9. The system can generate tailored CVs for top matches.
10. The system can generate a daily PDF report.
11. The system can create a ZIP CV pack.
12. The system can email both attachments to the user.
13. Admin can see whether each user’s daily run succeeded or failed.
14. No user can access another user’s files or data.
15. The system can run successfully for at least 10 users for 7 consecutive days.

## 24. Suggested First Build Prompt for an AI Builder

Build JobZoom, a paid monthly GCC job-search automation SaaS.

The product flow is:

1. User signs up and pays $200/month.
2. User uploads a CV in PDF or DOCX.
3. System parses the CV into structured profile data.
4. System generates an ATS-friendly master CV.
5. System generates target job-title tracks from the user’s career history.
6. System scans jobs daily across all GCC countries: Saudi Arabia, UAE, Qatar, Kuwait, Bahrain, Oman.
7. System normalizes and deduplicates jobs.
8. System scores jobs against each user profile from 0-100.
9. System selects the strongest matches only.
10. System generates tailored ATS CV PDFs for up to 5 top matches per user per day.
11. System generates a daily PDF report summarizing matches, reasoning, gaps, links, and CV filenames.
12. System creates a ZIP file containing tailored CVs.
13. System emails the user the PDF report and ZIP file daily.
14. Admin can monitor users, run status, generated reports, emails, and failures.

Important constraints:

- Do not build an auto-apply bot.
- Do not fabricate CV content.
- Use the uploaded CV as the only factual source.
- Keep CVs ATS-safe: no tables, columns, icons, images, headers/footers, or complex formatting.
- Use strict user data isolation.
- One user must never access another user’s CV, report, ZIP, or profile.
- Start with a simple MVP, not a complex dashboard.
- Prioritize backend reliability and daily delivery over UI polish.

MVP screens:

- landing page
- signup/login
- payment page
- CV upload page
- simple dashboard showing subscription status and latest report downloads
- admin dashboard for user/run/email monitoring

MVP backend:

- user management
- payment status
- CV upload and storage
- CV parser
- profile extractor
- ATS CV generator
- title-track generator
- job ingestion
- deduplication
- matching/scoring
- tailored CV generator
- PDF report generator
- ZIP generator
- email sender
- daily scheduler
- admin logs and retry/resend

Done when the system can run daily for 10 paid users, generate user-specific reports and CV ZIPs, email them successfully, and prove that user data is isolated.
