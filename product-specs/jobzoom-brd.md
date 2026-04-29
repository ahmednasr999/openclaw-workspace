# Business Requirements Document - JobZoom

## Document Control

| Item | Details |
|---|---|
| Product | JobZoom |
| Document Type | Business Requirements Document (BRD) |
| Version | 1.0 |
| Date | 2026-04-28 |
| Owner | Ahmed Nasr |
| Prepared by | NASR |
| Status | Draft for product validation and AI-builder handoff |

---

## 1. Executive Summary

JobZoom is a subscription-based GCC job-search automation product. The user uploads their CV once, pays a single monthly subscription fee, and receives a daily email containing:

1. A PDF report showing the best matched jobs across GCC countries.
2. A ZIP file containing tailored ATS-friendly CVs for the top matched jobs.

The product is designed for serious professionals who are actively looking for opportunities across Saudi Arabia, UAE, Qatar, Kuwait, Bahrain, and Oman. It is not a generic job board and not a simple AI CV writer. It is a daily career-application production engine.

The core promise is:

> Upload your CV once. JobZoom scans GCC jobs daily and sends you ready-to-apply tailored CVs for the roles that fit your career.

The initial commercial model is a single plan priced at **$200/month**.

The recommended go-to-market approach is a controlled beta with 10 paying users, using an MVP that focuses on reliable daily delivery rather than a complex dashboard.

---

## 2. Business Background

Professionals searching for GCC jobs face several recurring problems:

- Job portals contain too many irrelevant listings.
- Searching across multiple GCC countries is time-consuming.
- Job titles vary widely across companies and countries.
- Most candidates do not know which jobs are truly worth applying to.
- Tailoring CVs for each role is repetitive and slow.
- ATS optimization is confusing.
- Job seekers often miss opportunities because they lack daily discipline.
- Existing platforms provide job listings, but not a complete daily action package.

JobZoom solves this by combining job discovery, matching, ATS CV optimization, and daily delivery into one subscription service.

---

## 3. Business Objectives

### 3.1 Primary Objectives

1. Create a paid monthly product that automates daily GCC job-search preparation.
2. Save users time by filtering jobs and preparing tailored CVs.
3. Improve user application quality through ATS-friendly CV tailoring.
4. Build a repeatable, scalable subscription business.
5. Validate willingness to pay at $200/month.

### 3.2 Secondary Objectives

1. Build a job-market intelligence database across GCC countries.
2. Create reusable user career profiles from uploaded CVs.
3. Build a foundation for future features such as weekly market insights, interview preparation, recruiter outreach drafts, and application tracking.
4. Establish JobZoom as a premium job-search automation service for GCC professionals.

---

## 4. Problem Statement

Job seekers across the GCC spend too much time searching, filtering, and tailoring applications manually. Job portals help users find listings, but they do not solve the full workflow.

The current job-search process is fragmented:

1. User searches across multiple job sites.
2. User filters irrelevant jobs manually.
3. User decides whether a job fits their experience.
4. User edits the CV for each job.
5. User checks ATS keywords manually.
6. User tracks daily opportunities inconsistently.

This creates wasted time, inconsistent application quality, and missed opportunities.

JobZoom addresses the full workflow by converting the job-search process into a daily automated service.

---

## 5. Product Concept

JobZoom is a subscription service with this workflow:

1. User signs up and pays $200/month.
2. User uploads a CV.
3. System parses the CV and creates a structured profile.
4. System generates an optimized ATS master CV.
5. System generates position-title tracks based on the user’s career history.
6. System scans jobs daily across all GCC countries.
7. System scores and ranks jobs against the user profile.
8. System generates tailored ATS CVs for the strongest matches.
9. System creates a daily PDF report.
10. System creates a ZIP file containing tailored CVs.
11. System emails both attachments to the user daily.

---

## 6. Product Scope

### 6.1 In Scope for MVP

- Landing page
- User signup/login
- Subscription payment
- CV upload
- CV parsing
- Structured profile creation
- ATS master CV generation
- Position-title generation
- GCC-wide daily job search
- Job normalization
- Job deduplication
- User-job matching and scoring
- Tailored CV generation
- Daily PDF report generation
- ZIP file generation
- Daily email delivery
- Admin monitoring dashboard
- Failure logging and manual resend

### 6.2 Out of Scope for MVP

- Auto-apply functionality
- Recruiter messaging
- Interview coaching
- Advanced analytics dashboard
- Mobile app
- Complex user customization
- Multiple subscription tiers
- Public job board
- Employer-side product
- Guaranteeing interviews or offers
- Manual consultant review for every report

---

## 7. Target Market

### 7.1 Geographic Scope

JobZoom will focus on GCC countries:

- Saudi Arabia
- United Arab Emirates
- Qatar
- Kuwait
- Bahrain
- Oman

### 7.2 Primary Customer Segment

The initial target customer is a professional actively seeking GCC opportunities and willing to pay for time savings and better applications.

Best-fit profiles:

- senior professionals
- managers
- senior managers
- directors
- PMO professionals
- digital transformation professionals
- IT and technology professionals
- operations leaders
- healthcare and business transformation professionals
- expatriates targeting GCC relocation or mobility

### 7.3 Excluded or Lower-Priority Segments

- fresh graduates
- junior job seekers
- blue-collar workers
- users seeking free job alerts
- users expecting guaranteed job placement
- users expecting automatic applications

---

## 8. Customer Personas

### Persona 1: Senior Manager Seeking GCC Move

- Age: 35-50
- Experience: 10-20 years
- Goal: move to UAE, Saudi Arabia, Qatar, or another GCC country
- Pain: does not have time to search daily
- Value trigger: daily relevant jobs with tailored CVs ready
- Willingness to pay: high if product saves time and improves application quality

### Persona 2: GCC-Based Professional Seeking Better Role

- Already located in GCC
- Wants better compensation or seniority
- Uses LinkedIn and job boards but finds too much noise
- Needs help identifying suitable titles and applying consistently

### Persona 3: Executive or Director-Level Candidate

- Higher salary target
- Limited time
- Needs quality over volume
- Will pay if the product feels premium, private, and accurate

---

## 9. Value Proposition

### Main Value Proposition

JobZoom saves professionals hours every week by scanning GCC jobs, filtering relevant opportunities, and generating tailored ATS-friendly CVs every day.

### User-Facing Promise

> Upload your CV once. Receive a daily GCC job report and tailored CV pack ready for application.

### Differentiation

JobZoom is different because it does not stop at job alerts. It produces application-ready documents.

| Existing Solution | Limitation | JobZoom Advantage |
|---|---|---|
| Job portals | Too many irrelevant jobs | Filters and ranks jobs for the user |
| CV writers | One-time CV service | Daily tailored CVs for real jobs |
| AI writing tools | User must do all workflow steps | End-to-end daily automation |
| Recruiters | Focus on employer needs | Focus on candidate’s daily search |
| Job alerts | Send listings only | Sends report plus tailored CV pack |

---

## 10. Pricing and Revenue Model

### 10.1 Pricing

Single plan:

**$200 per month**

### 10.2 Billing

- Monthly recurring subscription
- Payment collected upfront
- Cancel anytime
- Access continues until end of billing cycle

### 10.3 Revenue Scenarios

| Paying Users | Monthly Revenue | Annualized Revenue |
|---:|---:|---:|
| 10 | $2,000 | $24,000 |
| 25 | $5,000 | $60,000 |
| 50 | $10,000 | $120,000 |
| 100 | $20,000 | $240,000 |
| 250 | $50,000 | $600,000 |
| 500 | $100,000 | $1,200,000 |

### 10.4 Unit Economics Target

Target gross margin should be above 70% after:

- AI/API usage
- email delivery
- storage
- hosting
- payment processing
- operational support

### 10.5 Usage Cap

To protect quality and margin:

- Maximum 5 tailored CVs per user per day.
- If fewer than 5 strong matches exist, generate fewer CVs.
- Do not force weak matches just to fill the quota.

---

## 11. Business Rules

### 11.1 Subscription Rules

1. Only active paid users receive daily reports.
2. If payment fails, user enters grace period, if configured.
3. After grace period, daily processing pauses.
4. User can cancel subscription.
5. User can request data deletion.

### 11.2 Job Matching Rules

1. Jobs must be scored from 0 to 100.
2. Jobs below 60 should not appear in the main report.
3. Jobs from 60-69 may appear as near misses.
4. Jobs above 70 may appear as matches.
5. Tailored CVs should normally be generated only for top matches.
6. Maximum 5 tailored CVs should be generated per user per day.
7. Quality is more important than quantity.

### 11.3 CV Rules

1. Do not fabricate experience.
2. Do not fabricate education.
3. Do not fabricate certifications.
4. Do not change employment dates.
5. Do not invent metrics.
6. Do not invent tools or technologies.
7. Tailoring must use facts from the uploaded CV/profile only.
8. CV format must be ATS-safe.

### 11.4 Delivery Rules

1. Each active user receives one daily email.
2. Email includes PDF report and ZIP file, unless using secure download links.
3. Failed email deliveries must be logged.
4. Admin must be able to resend.

### 11.5 Privacy Rules

1. A user must never access another user’s files.
2. Reports, CVs, and ZIPs must be user-specific.
3. Uploaded CVs must be private.
4. Admin access must be controlled.
5. User data deletion must be supported.

---

## 12. Functional Requirements

### FR-001 Landing Page

The system shall provide a public landing page explaining JobZoom, the $200/month plan, key benefits, sample output, and signup CTA.

Acceptance criteria:

- Visitor can understand the product in under 60 seconds.
- Pricing is visible.
- CTA leads to signup/payment.
- Sample report link or image is available.

### FR-002 User Signup

The system shall allow users to create an account.

Required fields:

- name
- email
- password or magic link authentication

Acceptance criteria:

- User can create account.
- User receives confirmation or login access.
- Duplicate email handling exists.

### FR-003 Subscription Payment

The system shall collect $200/month subscription payment.

Acceptance criteria:

- User can pay.
- Payment status is stored.
- Failed/cancelled subscriptions are tracked.
- Only active paid users are processed daily.

### FR-004 CV Upload

The system shall allow users to upload a CV.

Accepted formats:

- PDF
- DOCX

Acceptance criteria:

- File upload succeeds.
- File is linked to the correct user.
- File is stored privately.
- User cannot access another user’s file.

### FR-005 CV Parsing

The system shall parse the uploaded CV into structured profile data.

Extract:

- name
- contact details
- work history
- job titles
- companies
- dates
- responsibilities
- achievements
- skills
- education
- certifications
- languages
- industries

Acceptance criteria:

- Parsed profile is stored as structured data.
- Parsing failure is logged.
- Admin can see parsing status.

### FR-006 ATS Master CV Generation

The system shall generate an ATS-friendly master CV from the uploaded CV.

Acceptance criteria:

- Output is PDF.
- Format is single-column.
- No tables, icons, images, columns, text boxes, or complex formatting.
- No unsupported facts are added.

### FR-007 Position-Title Generation

The system shall generate target job-title tracks based on user career history.

Title categories:

- direct-fit titles
- adjacent-fit titles
- stretch-fit titles
- avoid/low-fit titles, internal optional

Acceptance criteria:

- Titles are generated and stored.
- Titles are used in daily job search.
- Titles are relevant to the user profile.

### FR-008 GCC Job Search

The system shall scan job sources across all GCC countries daily.

Countries:

- Saudi Arabia
- UAE
- Qatar
- Kuwait
- Bahrain
- Oman

Acceptance criteria:

- Jobs are collected daily.
- Source, title, company, location, URL, and description are stored.
- Search execution status is logged.

### FR-009 Job Normalization

The system shall normalize jobs into a standard schema.

Acceptance criteria:

- Raw job source data is converted into standard fields.
- Missing optional data does not break processing.
- Source URL is retained.

### FR-010 Job Deduplication

The system shall deduplicate jobs from multiple sources or repeated scans.

Deduplication logic:

- source job ID
- URL
- title + company + country
- fuzzy matching where needed

Acceptance criteria:

- Duplicate jobs are reduced.
- Canonical job record is maintained.
- Deduplication reason can be logged internally.

### FR-011 Job Scoring

The system shall score each relevant job against each active user profile.

Acceptance criteria:

- Score is 0-100.
- Score is stored.
- Explanation is generated.
- Risk/gap is generated.

### FR-012 Top Match Selection

The system shall select top matches for the daily report.

Acceptance criteria:

- Only high-quality matches are selected.
- Maximum 5 jobs are selected for tailored CV generation.
- If no strong matches exist, report states that clearly.

### FR-013 Tailored CV Generation

The system shall generate tailored ATS CVs for top selected jobs.

Acceptance criteria:

- Each generated CV is user-specific.
- Each CV references the target job.
- Each CV uses only source profile facts.
- Each CV is ATS-safe.
- Filename includes user name, job title, and company.

### FR-014 PDF Daily Report

The system shall generate a daily PDF report for each active user.

Report must include:

- user name
- date
- daily summary
- recommended actions
- top matches
- match scores
- why each job fits
- concern/gap for each job
- application links
- tailored CV filenames
- near misses
- market signals
- disclaimer

Acceptance criteria:

- Report is readable and polished.
- Report does not expose internal technical logs.
- Report is attached or linked in daily email.

### FR-015 ZIP CV Pack

The system shall generate a ZIP file containing tailored CVs.

Acceptance criteria:

- ZIP contains only that user’s files.
- ZIP is named clearly.
- ZIP is attached or linked in daily email.

### FR-016 Daily Email Delivery

The system shall email the report and ZIP to each active user daily.

Acceptance criteria:

- Email subject summarizes match count.
- PDF and ZIP are attached or linked.
- Delivery status is logged.
- Failed deliveries can be retried.

### FR-017 Admin Dashboard

The system shall provide an admin dashboard.

Admin can view:

- users
- subscription status
- CV upload status
- latest run status
- match counts
- CV generation counts
- report links
- email status
- failures

Acceptance criteria:

- Admin can identify failed users quickly.
- Admin can manually resend report.
- Admin can pause/resume user.

### FR-018 User Dashboard

The system shall provide a minimal user dashboard.

User can:

- view subscription status
- upload/replace CV
- download latest report
- download latest ZIP
- cancel subscription
- request data deletion

Acceptance criteria:

- User sees only their own data.
- Downloads are secure.

---

## 13. Non-Functional Requirements

### NFR-001 Security

- Use HTTPS.
- Store files privately.
- Enforce user-level access control.
- Protect admin routes.
- Avoid public file URLs.
- Use signed URLs if download links are used.

### NFR-002 Privacy

- Treat CVs as sensitive personal data.
- Provide deletion request process.
- Minimize data collection.
- Do not share user data externally except required processors.

### NFR-003 Reliability

- Daily run should complete for all active users.
- Partial failures should not stop the full batch.
- System must retry recoverable failures.
- Admin must receive failure alerts.

### NFR-004 Performance

- User dashboard should load within reasonable time.
- Daily batch should complete before target delivery time.
- Scoring should be batched and optimized.

### NFR-005 Scalability

Architecture should support growth from 10 users to 100+ users without redesign.

Key scaling principle:

- scan jobs centrally once
- score jobs per user
- generate reports per user

### NFR-006 Maintainability

- Code should be modular.
- Job ingestion, scoring, CV generation, report generation, and email delivery should be separate services/modules.
- Logs must be clear.

### NFR-007 Compliance and Legal

- Terms of service required.
- Privacy policy required.
- No job guarantee claims.
- No auto-apply unless future legal review is completed.

---

## 14. Data Requirements

### 14.1 User Data

- user ID
- name
- email
- subscription status
- payment provider customer ID
- signup date
- cancellation status

### 14.2 CV Data

- original CV file
- parsed CV JSON
- generated master CV
- extracted skills
- extracted work history
- certifications
- education

### 14.3 Job Data

- source
- source job ID
- title
- company
- country
- city
- URL
- description
- posted date
- discovered date
- normalized job fields

### 14.4 Match Data

- user ID
- job ID
- score
- match explanation
- gap/concern
- ranking
- selected for CV
- selected for report

### 14.5 Generated Artifact Data

- master CV path
- tailored CV paths
- daily report path
- ZIP path
- email delivery status

---

## 15. Recommended Database Model

### users

- id
- name
- email
- auth_provider_id
- subscription_status
- payment_customer_id
- created_at
- updated_at

### uploaded_cvs

- id
- user_id
- original_filename
- storage_path
- file_type
- upload_status
- parsed_status
- created_at

### user_profiles

- id
- user_id
- parsed_profile_json
- master_profile_json
- title_tracks_json
- skills_json
- industries_json
- seniority_level
- master_cv_path
- created_at
- updated_at

### jobs

- id
- source
- source_job_id
- url
- title
- company
- country
- city
- description
- posted_date
- discovered_date
- normalized_json
- is_active
- created_at
- updated_at

### job_matches

- id
- user_id
- job_id
- score
- score_band
- explanation
- concern
- positioning_angle
- selected_for_report
- selected_for_cv
- match_date
- created_at

### generated_cvs

- id
- user_id
- job_id
- match_id
- filename
- storage_path
- generation_status
- created_at

### daily_reports

- id
- user_id
- report_date
- pdf_path
- zip_path
- jobs_scanned
- matches_count
- cvs_generated_count
- generation_status
- email_status
- created_at

### email_deliveries

- id
- user_id
- report_id
- recipient_email
- subject
- provider_message_id
- status
- error_message
- sent_at

---

## 16. Process Flow

### 16.1 Onboarding Flow

1. User visits landing page.
2. User creates account.
3. User pays subscription.
4. User uploads CV.
5. System parses CV.
6. System creates structured profile.
7. System generates ATS master CV.
8. System generates title tracks.
9. User becomes active for daily processing.

### 16.2 Daily Processing Flow

1. Scheduler starts daily run.
2. System scans jobs across GCC countries.
3. System normalizes jobs.
4. System deduplicates jobs.
5. System retrieves active users.
6. For each user:
   - score jobs against user profile
   - select top matches
   - generate tailored CVs
   - generate PDF report
   - generate ZIP file
   - email user
   - log result
7. Admin receives internal run summary.

### 16.3 Failure Flow

If a user’s report fails:

1. Mark user run as failed.
2. Continue processing other users.
3. Log error.
4. Alert admin.
5. Allow manual retry/resend.

---

## 17. Report Requirements

The report must feel like a decision brief, not a system log.

### Required Report Sections

1. Cover/header
2. Today’s summary
3. Recommended action list
4. Top matched jobs
5. Tailored CV filenames
6. Application links
7. Near misses
8. Market signals
9. Disclaimer/footer

### Report Language

Use simple professional language.

Avoid internal terms:

- scraping engine
- pass 1
- pass 2
- fuzzy dedupe
- model health check
- raw token count

### Example Top Match Format

**Rank #1 - Program Manager at Example Company**

- Country: Saudi Arabia
- Score: 86/100
- Why it fits: Strong match with program governance, stakeholder management, and transformation experience.
- Concern: Role may be slightly below director level.
- Recommended action: Apply today.
- CV included: John Smith - Program Manager - Example Company.pdf
- Link: [job URL]

---

## 18. Email Requirements

### Daily Email Subject

`JobZoom Daily: {X} GCC matches and {Y} tailored CVs ready`

### Daily Email Body

```
Hi {Name},

Your JobZoom daily report is ready.

Today we found {X} strong GCC job matches for your profile and prepared {Y} tailored CVs.

Attached:
1. Daily PDF report
2. Tailored CV ZIP pack

Recommended first application: {Top Role} at {Company}, score {Score}/100.

Regards,
JobZoom
```

### Attachment Rules

- Attach PDF and ZIP if within size limits.
- If too large, provide secure download links.
- Links must expire or require authentication.

---

## 19. Admin Requirements

Admin must be able to manage and monitor operations.

### Admin Features

- View all users
- View subscription status
- View uploaded CV status
- View latest daily report
- View latest ZIP
- View daily run status
- View email delivery status
- Retry failed report generation
- Resend email
- Pause user
- Resume user
- Delete user data on request

### Admin Daily Summary

Admin should receive a daily internal summary:

- users processed
- reports generated
- emails sent
- failed users
- job scan health
- total jobs collected
- total matches generated

---

## 20. Security Requirements

### Critical Security Requirement

No user must ever access another user’s data.

### Controls

- Use user IDs in all file paths and database records.
- Enforce backend authorization on every download.
- Do not expose raw storage paths publicly.
- Use private buckets or private server storage.
- Use signed URLs with expiration if direct downloads are needed.
- Log admin access to sensitive files.
- Protect admin dashboard with strong authentication.

---

## 21. Privacy Requirements

The product handles sensitive personal data.

Required privacy controls:

- privacy policy
- user consent at signup
- data deletion request
- secure storage
- limited internal access
- no selling user data
- no sharing CVs with employers automatically

Recommended privacy statement:

> JobZoom uses your CV only to generate your career profile, match jobs, and prepare application documents. We do not apply to jobs or share your CV with employers without your action.

---

## 22. Legal and Compliance Requirements

JobZoom must include:

- Terms of Service
- Privacy Policy
- Refund/Cancellation Policy
- Disclaimer that JobZoom does not guarantee employment outcomes
- Consent for AI-assisted CV generation
- Consent for processing uploaded CV data

Avoid these claims:

- guaranteed interviews
- guaranteed job offer
- guaranteed ATS pass
- official partnership with job platforms unless true

---

## 23. Technical Assumptions

Recommended stack can be flexible, but one MVP stack could be:

- Frontend: Next.js or similar
- Backend: Node.js/Python API
- Database: PostgreSQL
- Queue/Jobs: BullMQ, Celery, or equivalent
- Storage: S3-compatible private storage
- Email: Postmark, SendGrid, Mailgun, SES
- Payments: Stripe or Paddle
- PDF generation: HTML-to-PDF engine
- CV generation: deterministic document templates plus LLM rewriting
- Scheduler: cron/background worker

The AI builder may choose equivalent tools if they satisfy the requirements.

---

## 24. Integration Requirements

### Payment Provider

- Create subscription
- Track active/inactive status
- Process renewals
- Handle failed payments
- Handle cancellations

### Email Provider

- Send daily emails
- Attach PDF and ZIP or send download links
- Track delivery status
- Track bounces/errors

### Job Sources

- Search and retrieve job listings
- Store source and URL
- Handle source failures gracefully

### AI/LLM Provider

Used for:

- CV parsing support
- profile extraction
- title-track generation
- job matching explanation
- tailored CV rewriting
- report narrative

Must be constrained to avoid fabrication.

---

## 25. Quality Assurance Requirements

### Test Cases

1. User signup and payment.
2. CV upload with PDF.
3. CV upload with DOCX.
4. CV parsing success.
5. CV parsing failure.
6. Master CV generation.
7. Title-track generation.
8. Job ingestion.
9. Deduplication.
10. Scoring.
11. Tailored CV generation.
12. PDF report generation.
13. ZIP generation.
14. Email delivery.
15. Failed email retry.
16. User cancellation.
17. Payment inactive user not processed.
18. User cannot access another user file.
19. Admin can resend report.
20. Daily run completes for 10 users.

### Security Tests

- Try downloading another user’s report.
- Try accessing another user’s ZIP URL.
- Try changing user ID in API request.
- Confirm access is denied.

### CV Quality Tests

- Verify no fabricated details.
- Verify ATS-safe formatting.
- Extract PDF text to ensure ATS readability.

---

## 26. MVP Acceptance Criteria

The MVP is accepted when:

1. A user can sign up.
2. A user can pay $200/month.
3. A user can upload a CV.
4. System can parse CV into structured profile.
5. System can generate ATS master CV.
6. System can generate title tracks.
7. System can scan GCC jobs.
8. System can match and score jobs.
9. System can generate up to 5 tailored CVs per user per day.
10. System can generate daily PDF report.
11. System can generate ZIP file.
12. System can email report and ZIP to user.
13. Admin can monitor daily run status.
14. Failed deliveries are visible and retryable.
15. User data is isolated.
16. System runs successfully for 10 users for 7 consecutive days.

---

## 27. Key Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Poor match quality | User cancels | strict thresholds, feedback, scoring tuning |
| AI fabricates CV details | Trust/reputation risk | use uploaded CV as only source, validation checks |
| Job source failure | Weak daily reports | multiple sources, caching, monitoring |
| Email delivery issues | User does not receive product | proper email provider, retries, logs |
| Attachments too large | Delivery failure | max 5 CVs, compression, secure links |
| Data leakage | Severe trust/legal risk | strict tenant isolation, private storage, tests |
| High support load | Low margin | no customization MVP, clear rules, admin tools |
| Users expect job guarantee | Misaligned expectations | clear disclaimer and positioning |

---

## 28. Launch Plan

### Phase 1 - Internal Productization

Goal: convert current JobZoom logic into multi-user-ready pipeline.

Duration: 2-4 weeks.

Deliverables:

- user folders/database
- profile extraction
- per-user reports
- per-user CV packs
- manual/admin delivery

### Phase 2 - Paid Beta

Goal: validate willingness to pay.

Duration: 30 days.

Users: 10.

Price: $200/month or temporary founding price.

Success criteria:

- 7/10 users remain after 30 days
- users open reports regularly
- users apply using generated CVs
- support remains manageable

### Phase 3 - MVP Platform

Goal: automate customer onboarding and delivery.

Deliverables:

- landing page
- payment
- CV upload
- user dashboard
- admin dashboard
- automated daily email

### Phase 4 - Scale

Goal: improve reliability and expand user base.

Deliverables:

- more job sources
- feedback loops
- secure download links
- weekly insights
- analytics

---

## 29. Open Questions

1. Should daily reports be sent every day or only business days?
2. Should the first month be full price or discounted beta?
3. Should ZIP files be attached or delivered as secure links?
4. Which payment provider will be available for the target market?
5. Which email provider should be used for best deliverability?
6. What refund policy should apply?
7. Should users be allowed to replace CV anytime or once per month?
8. Should the system support Arabic CVs at launch?
9. Should reports include salary information when available?
10. Should weekly market summary be included in MVP or Phase 2?

---

## 30. Final Business Recommendation

JobZoom is commercially feasible if launched as a premium, focused, GCC-wide job-search automation service.

The product should not compete as a normal job board. It should compete as a daily application preparation engine.

Recommended initial offer:

> JobZoom Premium - $200/month. Upload your CV once. Receive a daily GCC job report and up to 5 tailored ATS CVs for the strongest matching roles.

Recommended next step:

Build a controlled MVP and test with 10 paying beta users before investing in a full SaaS dashboard.

---

## Appendix A - AI Builder Build Prompt

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
