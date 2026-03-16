# ExamGenius: Complete Enterprise Blueprint

## AI-Powered Examination Platform for International Schools in Egypt

**Version:** 1.0
**Date:** March 15, 2026
**Classification:** Confidential
**Author:** Ahmed Nasr, CEO & Co-Founder

---

# PART A: EXECUTIVE OVERVIEW

## 1. Problem Statement

Egypt's international education sector is experiencing rapid growth but remains critically underserved by examination technology. The market reality:

- **430 international schools** operate across Egypt (British, American, IB, French, German systems)
- **336,000+ students** enrolled in international curricula (IGCSE, AP, IB, SAT-prep)
- **12,000+ teachers** creating and grading exams manually
- **Average teacher spends 8-12 hours per week** on exam creation, administration, and grading
- **85% of schools** still use paper-based examinations as the primary assessment method
- **Zero purpose-built platforms** exist for the Egyptian international school market
- **$2.1 billion** annual spend on international education in Egypt (tuition fees)
- **15% year-over-year growth** in international school enrollment since 2020

The core problems:

1. **Exam creation is manual and inconsistent.** Teachers spend hours writing questions from scratch each term, with no standardized quality assurance or curriculum alignment verification.
2. **No institutional question banks.** When a teacher leaves, their questions leave with them. Schools have no systematic way to build, curate, or share assessment assets.
3. **Grading is slow and subjective.** Essay and short-answer grading varies 15-25% between teachers grading the same response. Results take 1-3 weeks to reach students.
4. **Cheating is rampant and undetectable.** Online exams during COVID exposed massive integrity gaps. Schools lack proctoring tools designed for their context.
5. **Analytics are nonexistent.** Schools cannot identify which topics students struggle with, which questions are poorly written, or how student performance trends over time.
6. **Existing tools don't fit.** Moodle is too complex, ExamSoft is too expensive ($85/student), Kahoot is too gamified for formal assessment, and none support Arabic RTL or Egyptian curricula natively.

## 2. Solution Overview

**ExamGenius** is an AI-powered examination platform purpose-built for international schools in Egypt. It transforms the entire assessment lifecycle: from curriculum ingestion and AI-driven question generation, through secure exam delivery and automated grading, to deep learning analytics for students, teachers, parents, and administrators.

The platform's "Build Once" AI architecture starts with cloud API-based question generation (OpenAI/Anthropic) and progressively trains a proprietary model on validated teacher-reviewed questions, reducing per-question cost by 86% over three years while improving quality through continuous learning.

### Key Differentiators

1. **AI Question Generation:** Upload a curriculum document, get a complete exam in under 5 minutes, aligned to Bloom's Taxonomy with quality scores
2. **Build Once AI:** Transition from API dependency to proprietary fine-tuned model, cutting costs from $450K to $65K over 3 years
3. **Full Arabic RTL Support:** Native bidirectional text rendering, Arabic question generation, and localized UI
4. **Egypt-First Data Residency:** All data stored in AWS Cairo region (or nearest compliant region), meeting Egyptian data sovereignty requirements
5. **Integrated Proctoring:** Browser lockdown, webcam monitoring, AI anomaly detection, and plagiarism checking in one platform
6. **Curriculum-Native:** Pre-loaded support for IGCSE, IB, AP, American Diploma, and Egyptian National curricula

## 3. Value Proposition by User Type

### School Administrators
- **Reduce exam-related costs by 40%** through elimination of printing, physical logistics, and manual coordination
- **Institutional question bank** that grows with every exam, surviving teacher turnover
- **Real-time dashboards** showing school-wide performance, teacher effectiveness, and curriculum coverage gaps
- **Compliance and audit trails** for accreditation bodies (CIS, NEASC, AdvancED)
- **Subscription management** with predictable per-student pricing

### Teachers
- **Save 6-8 hours per week** on exam creation and grading
- **AI-generated questions** aligned to specific curriculum topics and Bloom's Taxonomy levels
- **One-click exam creation** from uploaded syllabi and past papers
- **Automated grading** for objective questions with AI-assisted rubric scoring for essays
- **Question quality analytics** showing which questions discriminate well vs. which are too easy/hard
- **Collaborative question sharing** across departments and schools (with permissions)

### Students
- **Immediate feedback** on objective questions after submission
- **Detailed explanations** for every wrong answer, linked to curriculum topics
- **Performance dashboard** showing strengths/weaknesses by topic and Bloom level
- **Trend tracking** across terms and years
- **Fair, consistent assessment** through randomized questions and AI proctoring
- **Accessible interface** with RTL support, font scaling, and extra time accommodations

### Parents
- **Real-time visibility** into child's exam performance without waiting for report cards
- **Topic-level insights:** "Your child is strong in Cell Biology but struggling with Genetics"
- **Comparison to class averages** (anonymized) for context
- **Trend visualization** showing improvement or decline over time
- **Push notifications** for upcoming exams and grade releases

## 4. Business Objectives

### Year 1 (Months 1-12)
| Metric | Target |
|--------|--------|
| Pilot schools (free) | 5 schools |
| Paying schools | 15 schools |
| Total students on platform | 8,000 |
| Annual Recurring Revenue (ARR) | $280,000 |
| Questions generated (AI) | 100,000+ |
| Teacher satisfaction score | 4.2/5.0 |
| Platform uptime | 99.5% |
| NPS score | 40+ |

### Year 2 (Months 13-24)
| Metric | Target |
|--------|--------|
| Total paying schools | 60 schools |
| Total students on platform | 35,000 |
| ARR | $1,400,000 |
| Proprietary AI model deployed | Yes (Llama fine-tune) |
| Mobile app launched | iOS + Android |
| API marketplace partners | 5+ |
| Teacher satisfaction score | 4.5/5.0 |
| Platform uptime | 99.9% |
| NPS score | 50+ |

### Year 3 (Months 25-36)
| Metric | Target |
|--------|--------|
| Total paying schools | 150 schools (Egypt + GCC) |
| Total students on platform | 90,000 |
| ARR | $4,500,000 |
| GCC expansion markets | UAE, Saudi Arabia, Qatar |
| White-label deployments | 3+ |
| Employee headcount | 35-45 |
| Gross margin | 72% |
| NPS score | 55+ |

## 5. Target Market Sizing

### Total Addressable Market (TAM)
- **Egypt international schools:** 430 schools, 336,000 students
- **Average student spend on assessment tools:** $40/year (blended across tiers)
- **Egypt TAM:** 336,000 x $40 = **$13.4M/year**

### Serviceable Addressable Market (SAM)
- **Target: IGCSE + IB + American Diploma schools** (premium tier, tech-forward): ~180 schools, 140,000 students
- **SAM:** 140,000 x $45 (Professional tier avg) = **$6.3M/year**

### Serviceable Obtainable Market (SOM) - Year 3
- **Realistic capture:** 150 schools, 90,000 students
- **SOM:** 90,000 x $50 (blended) = **$4.5M/year**

### GCC Expansion (Year 3+)
- **UAE:** 620 international schools, 520,000 students
- **Saudi Arabia:** 400+ international schools, 300,000+ students
- **Qatar, Bahrain, Kuwait, Oman:** 350+ schools combined
- **GCC TAM:** 1,370 schools, 1.17M students = **$47M/year**

## 6. Competitive Analysis

| Feature | ExamGenius | Moodle Quiz | ExamSoft | Kahoot | SchoolNotion |
|---------|-----------|-------------|----------|--------|-------------|
| AI question generation | Yes (9 types) | No | No | No | Limited |
| Bloom taxonomy alignment | Yes (6 levels) | No | No | No | No |
| Arabic RTL support | Native | Partial | No | No | Partial |
| Curriculum ingestion | Yes (PDF/DOCX/PPTX) | No | No | No | No |
| Browser lockdown proctoring | Yes | Plugin required | Yes | No | No |
| Webcam AI proctoring | Yes | No | Yes | No | No |
| Auto-grading | 7 question types | MCQ only | MCQ only | MCQ only | MCQ only |
| Parent portal | Yes | No | No | No | Yes |
| Egypt data residency | Yes | Self-hosted | No (US) | No (EU) | No |
| Price per student/year | $30-75 | Free (hidden costs) | $85+ | $6-12 | $15-40 |
| Implementation time | 2 weeks | 2-6 months | 4-8 weeks | 1 day | 2-4 weeks |
| Question bank management | Enterprise-grade | Basic | Good | None | Basic |
| Analytics depth | Deep (topic/Bloom) | Basic stats | Good | Engagement only | Basic |

### Competitive Advantages
1. **Only platform with AI question generation** from curriculum documents
2. **Only platform with native Arabic RTL** and Egypt data residency
3. **Build Once model** eliminates long-term API dependency (unique in market)
4. **Purpose-built for international schools** vs. adapted from LMS or corporate testing
5. **30-65% cheaper than ExamSoft** with more features

## 7. Pricing Tiers

### Starter - $30/student/year
- Up to 500 students
- AI question generation (500 questions/month)
- 5 question types (MCQ, T/F, Short Answer, Fill-in-blank, Matching)
- Basic exam builder
- Auto-grading for objective questions
- Student results portal
- Email support
- 5GB storage per school

### Professional - $45/student/year
- Up to 2,000 students
- AI question generation (2,000 questions/month)
- All 9 question types
- Bloom taxonomy alignment
- Advanced exam builder with sections
- Full auto-grading + manual grading tools
- Student, teacher, and parent portals
- Class and school analytics
- Basic proctoring (browser lockdown)
- SSO (Google, Microsoft)
- Priority email + chat support
- 25GB storage per school

### Enterprise - $75/student/year
- Unlimited students
- Unlimited AI question generation
- All 9 question types + custom types
- Full Bloom taxonomy with custom frameworks
- Advanced exam builder with all features
- Full proctoring (browser + webcam + AI)
- Plagiarism detection
- All portals with white-label option
- Advanced analytics with comparative reports
- SIS integration (PowerSchool, Skyward)
- LMS integration (Moodle, Canvas)
- API access
- Dedicated account manager
- Phone + chat + email support (SLA: 4hr response)
- 100GB storage per school
- Custom training and onboarding

### Add-ons
- Additional storage: $2/GB/month
- API access (non-Enterprise): $500/month
- Custom AI model training: $5,000 one-time
- On-site training: $1,500/day
- SIS integration setup: $2,000 one-time

---

# PART B: FULL PRODUCT REQUIREMENTS (BRD)

## 5.1 Curriculum Ingestion System

### 5.1.1 Supported File Formats and Constraints

| Format | Extension | Max Size | Notes |
|--------|-----------|----------|-------|
| PDF | .pdf | 50MB | Scanned PDFs processed via OCR |
| Microsoft Word | .docx | 50MB | Legacy .doc not supported |
| PowerPoint | .pptx | 50MB | Speaker notes extracted |
| Plain Text | .txt | 10MB | UTF-8 encoding required |
| ZIP Archive | .zip | 50MB | Contains any of above formats |

- **Batch upload:** Up to 20 files per upload session
- **Total batch size:** 200MB maximum
- **Concurrent processing:** Up to 5 files processed simultaneously per school

### 5.1.2 Processing Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Text extraction accuracy | 95%+ | Compared against manual transcription of 100 sample pages |
| Processing time (<10MB) | Under 30 seconds | From upload complete to processing complete |
| Processing time (10-50MB) | Under 120 seconds | From upload complete to processing complete |
| OCR accuracy (scanned PDFs) | 90%+ | Tesseract OCR with English + Arabic models |
| Image extraction success | 98%+ | All embedded images extracted and stored |
| Heading detection accuracy | 92%+ | Correct hierarchy identification |

### 5.1.3 AI Preprocessing Pipeline

```
Upload -> Validate -> Store (S3) -> Extract Text -> Detect Language
   -> Extract Structure (headings, sections)
   -> Extract Images -> Store Images (S3)
   -> AI Topic Extraction (OpenAI)
      -> Subject identification
      -> Grade level detection
      -> Learning objectives extraction
      -> Topic/subtopic hierarchy
      -> Key concepts and terms
   -> Generate Curriculum Map (JSON)
   -> Store Processed Data (PostgreSQL)
   -> Notify Teacher (WebSocket + email)
```

### 5.1.4 Curriculum Library Features

- **Versioning:** Each curriculum document maintains version history; teachers can compare versions
- **Search:** Full-text search across all uploaded curricula with filters (subject, grade, standard, date)
- **Sharing:** School-level sharing (all teachers in school), department-level sharing, or private
- **Usage stats:** Track how many questions generated from each curriculum, which topics most/least used
- **Tagging:** Custom tags for organization (e.g., "Term 1", "Revision", "Past Paper 2024")
- **Favorites:** Teachers can bookmark frequently used curricula
- **Duplication detection:** SHA-256 hash comparison to prevent duplicate uploads
- **Archive/restore:** Soft delete with 90-day retention

## 5.2 AI Exam Generation Engine: Build Once Architecture

### 5.2.1 Phase 1: API-Based Generation (Months 1-8)

**Primary Provider:** OpenAI GPT-4o
**Fallback Provider:** Anthropic Claude 3.5 Sonnet
**Cost:** ~$0.03-0.08 per question generated

#### Prompt Engineering Architecture

Each question type has a dedicated prompt template with the following structure:

```
SYSTEM: You are an expert {subject} teacher creating {curriculum_standard} 
examination questions for Grade {grade} students. Your questions must align 
with Bloom's Taxonomy Level {bloom_level} ({bloom_description}).

CONTEXT: The following curriculum content covers {topic} - {subtopic}:
{curriculum_text_chunk}

TASK: Generate {count} {question_type} questions at {difficulty} difficulty.

CONSTRAINTS:
- Language: {language}
- Each question must be answerable solely from the provided curriculum content
- Distractors (for MCQ) must be plausible but clearly incorrect
- Include a detailed explanation for the correct answer
- Tag each question with the specific learning objective it assesses

OUTPUT FORMAT: {json_schema}
```

#### 9 Question Types with Specifications

**1. Multiple Choice Questions (MCQ)**
- 4 or 5 options (configurable)
- Exactly 1 correct answer
- All distractors must be plausible and content-related
- Options shuffled on delivery
- Output: `{question, options[], correct_index, explanation}`

**2. True/False**
- Clear, unambiguous statement
- No trick questions or double negatives
- Explanation for both true and false reasoning
- Output: `{statement, correct_answer: boolean, explanation}`

**3. Short Answer**
- Question requiring 1-3 sentence response
- Sample answer provided for grading reference
- Marking guide with key terms to look for
- Acceptable answer variations listed
- Output: `{question, sample_answer, key_terms[], marking_guide, max_marks}`

**4. Essay**
- Open-ended question requiring extended response
- Word limit specified (100-1000 words)
- Rubric with 3-5 criteria, each scored independently
- Output: `{question, word_limit, rubric_criteria[], max_marks}`

**5. Fill-in-the-Blank**
- Sentence with 1-3 blanks marked as [BLANK]
- Correct answer for each blank
- List of acceptable alternative answers
- Case-sensitivity configurable
- Output: `{sentence_with_blanks, answers[], alternatives[][], case_sensitive: boolean}`

**6. Matching**
- Two columns of 4-8 items each
- Each item in Column A matches exactly one item in Column B
- Column B may have 1-2 extra distractors
- Output: `{column_a[], column_b[], correct_pairs[], extra_distractors[]}`

**7. Ordering/Sequencing**
- List of 4-8 items to arrange in correct order
- Context provided (chronological, procedural, size, etc.)
- Output: `{items_shuffled[], correct_order[], ordering_criterion}`

**8. Case Study**
- Scenario paragraph (100-300 words)
- 3-5 sub-questions of varying types (MCQ, short answer, analysis)
- All sub-questions reference the scenario
- Output: `{scenario, sub_questions[{type, question, answer, marks}]}`

**9. Data Interpretation**
- Table or chart description (structured data)
- 3-5 analysis questions requiring data reading and inference
- Supports: bar charts, line graphs, pie charts, data tables, scatter plots
- Output: `{data_description, data_json, visualization_type, questions[{question, answer, marks}]}`

#### Bloom's Taxonomy Alignment

| Level | Name | Verb Examples | Question Types Best Suited |
|-------|------|---------------|---------------------------|
| 1 | Remember | Define, list, recall, identify | MCQ, T/F, Fill-in-blank |
| 2 | Understand | Explain, summarize, compare | Short Answer, MCQ, Matching |
| 3 | Apply | Calculate, demonstrate, use | Short Answer, Fill-in-blank, Data Interp |
| 4 | Analyze | Differentiate, examine, categorize | Case Study, Essay, Data Interpretation |
| 5 | Evaluate | Justify, critique, argue | Essay, Case Study |
| 6 | Create | Design, construct, propose | Essay, Case Study |

#### Quality Scoring Algorithm (0-100)

```python
def calculate_quality_score(question, metadata):
    score = 0
    
    # 1. Grammar & Clarity (20 points)
    grammar_score = check_grammar(question.content)  # LanguageTool API
    clarity_score = check_readability(question.content)  # Flesch-Kincaid
    score += min(20, grammar_score * 10 + clarity_score * 10)
    
    # 2. Distractor/Answer Quality (20 points) 
    if question.type == 'MCQ':
        plausibility = assess_distractor_plausibility(question.options)
        distinctness = check_option_distinctness(question.options)
        score += min(20, plausibility * 10 + distinctness * 10)
    elif question.type in ['SHORT_ANSWER', 'ESSAY']:
        rubric_quality = assess_rubric_completeness(question.rubric)
        score += min(20, rubric_quality * 20)
    else:
        answer_quality = assess_answer_completeness(question)
        score += min(20, answer_quality * 20)
    
    # 3. Curriculum Alignment (20 points)
    alignment = calculate_semantic_similarity(
        question.content, 
        metadata.curriculum_text
    )
    topic_match = verify_topic_coverage(question, metadata.topic)
    score += min(20, alignment * 10 + topic_match * 10)
    
    # 4. Difficulty Calibration (20 points)
    actual_difficulty = estimate_difficulty(question)
    requested_difficulty = metadata.requested_difficulty
    diff_delta = abs(actual_difficulty - requested_difficulty)
    score += max(0, 20 - diff_delta * 5)
    
    # 5. Bias Check (20 points)
    bias_flags = check_bias(question.content)  # Gender, cultural, religious
    score += max(0, 20 - len(bias_flags) * 5)
    
    return score
```

- Questions scoring **80-100:** Auto-approved, ready for use
- Questions scoring **60-79:** Flagged for teacher review
- Questions scoring **below 60:** Auto-rejected, regenerated

#### Performance Requirements
- Generate 10 questions: under 15 seconds
- Generate 50 questions: under 45 seconds
- Generate 100 questions: under 90 seconds
- Generate 500 questions: under 120 seconds (batched, parallel API calls)

### 5.2.2 Phase 2: Training Data Collection (Months 5-12)

**Goal:** Collect 5,000+ validated, teacher-reviewed questions to fine-tune a proprietary model.

#### Collection Workflow
1. Every AI-generated question enters the review queue
2. Teacher reviews: Accept (as-is), Edit (modify and accept), or Reject (with reason)
3. Accepted and edited questions are stored in `training_data` table with full metadata
4. Quality metrics tracked: acceptance rate by subject, topic, question type, Bloom level
5. Monthly reports on collection progress toward 5,000 target

#### Training Data Schema
```json
{
  "curriculum_context": "The cell membrane is a selectively permeable...",
  "topic": "Cell Biology",
  "subtopic": "Cell Membrane",
  "question_type": "MCQ",
  "difficulty": "medium",
  "bloom_level": 2,
  "grade": 10,
  "subject": "Biology",
  "curriculum_standard": "IGCSE",
  "question": "Which of the following best describes...",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "correct_answer": "B",
  "explanation": "The cell membrane uses selective...",
  "teacher_action": "accepted",
  "teacher_edits": null,
  "quality_score": 87,
  "teacher_id": "usr_abc123",
  "reviewed_at": "2026-09-15T14:30:00Z"
}
```

### 5.2.3 Phase 3: Fine-Tuned Proprietary Model (Months 10-14)

**Base Model:** Llama 3 8B (initial), upgrade to 13B when data exceeds 10,000 questions
**Fine-Tuning Method:** LoRA (Low-Rank Adaptation) for parameter-efficient training
**Framework:** Hugging Face Transformers + PEFT library

#### GPU Infrastructure Options

**Option A: On-Premise (Recommended for Year 2+)**
- NVIDIA A100 40GB GPU
- Hardware cost: $15,000 one-time
- Hosting: co-located server or office rack
- Power + cooling: ~$200/month
- Training time: 4-8 hours for 5,000 examples
- Inference: 50-100 questions/second

**Option B: Cloud GPU (Recommended for initial training)**
- AWS p4d.24xlarge or Lambda Labs A100
- Cost: $2-3/hour
- Training cost per run: $16-24 (8 hours)
- Monthly inference cost: ~$500-1,000 (on-demand)
- Use for training iterations; transition to on-prem for production inference

#### Cost Comparison: API vs Build Once (3-Year Projection)

| Cost Category | API Approach (3 years) | Build Once (3 years) |
|--------------|----------------------|---------------------|
| API calls (generation) | $360,000 | $12,000 (Phase 1 only) |
| API calls (quality scoring) | $60,000 | $3,000 (Phase 1 only) |
| Training data collection | $0 | $15,000 (teacher time) |
| GPU hardware | $0 | $15,000 (one-time) |
| Model training (compute) | $0 | $5,000 |
| Inference infrastructure | $0 | $12,000 |
| Engineering time | $30,000 | $18,000 |
| **Total** | **$450,000** | **$65,000** |
| **Savings** | - | **$385,000 (86%)** |

## 5.3 Question Bank Management

### 5.3.1 Question Entity (Complete Schema)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| school_id | UUID | FK to schools |
| curriculum_id | UUID | FK to curricula (nullable) |
| question_type | ENUM | MCQ, TRUE_FALSE, SHORT_ANSWER, ESSAY, FILL_IN_BLANK, MATCHING, ORDERING, CASE_STUDY, DATA_INTERPRETATION |
| difficulty | ENUM | EASY, MEDIUM, HARD, EXPERT |
| bloom_level | INTEGER | 1-6 (Remember through Create) |
| subject | VARCHAR(100) | e.g., "Biology", "Mathematics" |
| grade | INTEGER | Grade level (1-12) |
| topic | VARCHAR(200) | Main topic |
| sub_topic | VARCHAR(200) | Subtopic (nullable) |
| curriculum_standard | VARCHAR(50) | IGCSE, IB, AP, etc. |
| content_text | TEXT | Plain text version of question |
| content_rich | JSONB | Rich content: LaTeX, images, audio, video |
| answer_key | JSONB | Structured answer data |
| explanation | TEXT | Detailed explanation |
| tags | TEXT[] | Array of tags |
| quality_score | INTEGER | 0-100 |
| usage_count | INTEGER | Times used in exams |
| success_rate | DECIMAL(5,2) | Percentage of correct responses |
| discrimination_index | DECIMAL(5,4) | Item discrimination (-1.0 to 1.0) |
| created_by | UUID | FK to users (teacher or AI) |
| reviewed_by | UUID | FK to users (reviewer) |
| status | ENUM | DRAFT, SUBMITTED, IN_REVIEW, APPROVED, PUBLISHED, ARCHIVED |
| ai_generated | BOOLEAN | Whether AI-generated |
| ai_model | VARCHAR(50) | Model used (if AI-generated) |
| ai_prompt_version | VARCHAR(20) | Prompt template version |
| language | VARCHAR(10) | en, ar, fr, de |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last modification |

### 5.3.2 Question Lifecycle States

```
DRAFT -> SUBMITTED -> IN_REVIEW -> APPROVED -> PUBLISHED
                         |              |
                         v              v
                      REJECTED      ARCHIVED
                         |
                         v
                    DRAFT (revised)
```

- **DRAFT:** Created by teacher or AI; not visible to others
- **SUBMITTED:** Teacher submits for departmental review
- **IN_REVIEW:** Assigned to a reviewer (department head or designated reviewer)
- **APPROVED:** Passed quality review; ready for exam use
- **PUBLISHED:** Actively available in the shared question bank
- **ARCHIVED:** Removed from active use but preserved for historical reference
- **REJECTED:** Failed review; returned to creator with feedback

### 5.3.3 Bulk Import

- **Formats:** CSV, Excel (.xlsx)
- **Template download:** Pre-formatted template with all required columns
- **Validation:** Column mapping wizard, data type validation, enum validation
- **Duplicate detection:** Content similarity check (cosine similarity > 0.95 = likely duplicate)
- **Batch size:** Up to 500 questions per import
- **Error handling:** Row-level error reporting; valid rows imported, invalid rows flagged
- **Preview:** Show first 10 rows parsed before committing import

### 5.3.4 Rich Content Support

- **LaTeX equations:** KaTeX rendering for inline ($...$) and display ($$...$$) math
- **Images:** Embedded images in question body and options; stored in S3 with CDN
- **Audio:** MP3/WAV attachments for listening comprehension questions (max 10MB)
- **Video:** MP4 embeds for data interpretation or case study context (max 50MB)
- **Tables:** HTML table support in question body
- **Code blocks:** Syntax-highlighted code for Computer Science questions
- **Chemical equations:** mhchem notation for Chemistry

## 5.4 Exam Builder

### 5.4.1 Exam Structure

An exam consists of:
- **Metadata:** Title, description, subject, grade, curriculum, total points, overall time limit
- **Sections:** 1 or more sections, each with optional separate time limit
- **Questions:** Ordered list of questions within each section, each with point value

### 5.4.2 Section Configuration

| Feature | Description |
|---------|-------------|
| Title | Section name (e.g., "Section A: Multiple Choice") |
| Time limit | Optional per-section time limit (independent of overall) |
| Instructions | Section-specific instructions displayed to student |
| Question count | Number of questions in section |
| Points | Total points for section (sum of question points) |
| Navigation | Allow backward navigation within section (configurable) |
| Order | Sequential ordering of sections |

### 5.4.3 Randomization Options

- **Shuffle questions within sections:** Each student sees questions in different order
- **Shuffle MCQ options:** Option order randomized per student (correct answer position varies)
- **Question pooling:** Define a pool of 20 questions, each student gets random 10
- **Variant generation:** Create multiple exam variants automatically from question pool
- **Seed-based:** Randomization uses student_id + exam_id as seed for reproducibility

### 5.4.4 Access Control

| Control | Description |
|---------|-------------|
| Password | Optional exam password required before starting |
| IP whitelist | Restrict to specific IP addresses or ranges (school network) |
| Time window | Start and end datetime; exam only accessible within window |
| Attempt limits | Maximum number of attempts (1 for formal exams, unlimited for practice) |
| Late submission | Allow/disallow late submissions with configurable penalty |
| Accommodations | Per-student extra time (25%, 50%, 100%), large font, screen reader support |

### 5.4.5 Scheduling

- **Conflict detection:** Warn if students have overlapping exams
- **Calendar view:** Visual calendar showing all scheduled exams per class/grade
- **Timezone handling:** All times stored in UTC, displayed in school's timezone
- **Reminder notifications:** 24hr, 1hr, 15min before exam start (configurable)
- **Auto-publish:** Schedule exam to become visible to students at specific time

### 5.4.6 PDF Export

- **Professional formatting:** School logo, exam header, instructions, questions, answer sheet
- **Answer key PDF:** Separate document with correct answers and explanations
- **Bubble sheet:** Auto-generated OMR-compatible answer sheet for MCQ sections
- **Accommodated versions:** Large print (18pt), extra spacing versions
- **Watermark:** Student name/ID watermarked on each page (optional)

### 5.4.7 Validation Rules

Before publishing an exam, the system validates:
1. All questions have assigned point values
2. Total points match declared total
3. Time limit is reasonable (estimated completion time within 80-120% of limit)
4. All questions have correct answers defined
5. No duplicate questions
6. All referenced questions exist and are in PUBLISHED status
7. Section time limits sum to less than or equal to overall time limit (if both set)
8. At least one question in each section

## 5.5 Proctoring System

### 5.5.1 Browser Lockdown

| Feature | Implementation |
|---------|---------------|
| Fullscreen enforcement | Exam launches in fullscreen; exit triggers warning |
| Tab switch detection | Visibility API + focus event monitoring |
| Copy/paste disabled | Clipboard API blocked; keyboard shortcuts intercepted |
| Right-click disabled | Context menu suppressed |
| Keyboard shortcuts blocked | Ctrl+C, Ctrl+V, Ctrl+A, Ctrl+P, Alt+Tab, Print Screen |
| Developer tools blocked | F12, Ctrl+Shift+I, Ctrl+Shift+J detection |
| URL navigation blocked | Address bar interactions detected |
| Multiple monitor detection | Screen.availWidth comparison |
| Virtual machine detection | WebGL renderer string analysis |
| Screenshot tool detection | Known screenshot tool process detection (best effort) |

**Warning Escalation:**
- 1st violation: Warning popup, logged
- 2nd violation: Warning popup, proctor notified
- 3rd violation: Exam paused, proctor must approve continuation
- 4th+ violation: Auto-submit option (configurable by school)

### 5.5.2 Webcam Monitoring

| Feature | Specification |
|---------|--------------|
| Identity photo | Captured at exam start; compared against school photo (if available) |
| Periodic photos | Every 30s to 5min (configurable) |
| Video recording | Optional continuous recording (stored in S3) |
| Photo storage | S3 with 90-day retention (configurable) |
| Video storage | S3 with 30-day retention (configurable) |
| Camera check | Pre-exam camera test with lighting/position guidance |
| Consent | Explicit consent captured before proctoring begins |

### 5.5.3 AI Detection Capabilities

| Detection | Method | Alert Threshold |
|-----------|--------|----------------|
| No face detected | Face detection model (MTCNN) | >5 seconds |
| Multiple faces | Face count > 1 | Immediate |
| Different person | Face embedding comparison (FaceNet) | Confidence > 80% |
| Person looking away | Head pose estimation | >10 seconds continuous |
| Suspicious audio | Sound level + speech detection | Background speech detected |
| Device movement | Accelerometer/gyroscope data | Unusual movement pattern |
| Phone detection | Object detection (YOLO) | Phone-like object in frame |
| Screen sharing | Screen capture API monitoring | Active screen share detected |

### 5.5.4 Anomaly Alert System

- **Alert latency:** Under 5 seconds from detection to proctor dashboard
- **Alert delivery:** WebSocket push to proctor dashboard + optional email/SMS
- **Alert priority:** LOW (informational), MEDIUM (review needed), HIGH (immediate action), CRITICAL (possible cheating)
- **Proctor actions:** Dismiss, Flag for review, Send warning to student, Pause exam, Terminate exam

### 5.5.5 Integrity Score (0-100)

```python
def calculate_integrity_score(session):
    score = 100
    
    # Browser violations (max -30 points)
    for violation in session.browser_violations:
        if violation.type == 'tab_switch':
            score -= 5
        elif violation.type == 'fullscreen_exit':
            score -= 3
        elif violation.type == 'copy_paste':
            score -= 8
        elif violation.type == 'dev_tools':
            score -= 15
    
    # Proctoring violations (max -40 points)
    for event in session.proctoring_events:
        if event.type == 'no_face':
            score -= 5
        elif event.type == 'multiple_faces':
            score -= 15
        elif event.type == 'different_person':
            score -= 25
        elif event.type == 'phone_detected':
            score -= 20
        elif event.type == 'looking_away':
            score -= 3
    
    # Time anomalies (max -15 points)
    if session.completion_time < expected_time * 0.3:
        score -= 10  # Suspiciously fast
    if session.idle_periods > 3:
        score -= 5   # Multiple long pauses
    
    # Plagiarism score (max -15 points)
    plagiarism_pct = check_plagiarism(session.responses)
    score -= min(15, plagiarism_pct * 0.15)
    
    return max(0, score)
```

### 5.5.6 Plagiarism Detection

- **Peer comparison:** Compare student responses against all other students in the same exam session
- **Question bank comparison:** Check if responses match stored answers verbatim
- **Internet comparison:** API integration with Turnitin or Copyscape (Enterprise tier)
- **Similarity threshold:** Flag at 70%+ similarity for short answers, 40%+ for essays
- **Report:** Highlighted matching segments with source attribution

## 5.6 Grading and Analytics

### 5.6.1 Auto-Grading Rules

| Question Type | Grading Method | Partial Credit |
|--------------|----------------|----------------|
| MCQ (single answer) | Exact match | No |
| MCQ (multiple answers) | Set comparison | Yes: (correct selections / total correct) |
| True/False | Exact match | No |
| Fill-in-blank | Exact match + fuzzy (Levenshtein distance <= 2) | No (configurable) |
| Matching | Pair-by-pair comparison | Yes: (correct pairs / total pairs) |
| Ordering | Sequence comparison (Kendall tau) | Yes: based on displacement score |
| Short Answer | AI-assisted (keyword matching + semantic) | Yes: rubric-based |
| Essay | Manual (AI suggestions) | Yes: rubric-based |
| Data Interpretation | Varies by sub-question type | Per sub-question |
| Case Study | Varies by sub-question type | Per sub-question |

### 5.6.2 Partial Credit Configuration

- **Per-question toggle:** Teachers can enable/disable partial credit per question
- **MCQ multiple-answer:** 3/4 correct selections = 75% of points (configurable)
- **Matching:** Each correct pair earns proportional credit
- **Ordering:** Credit based on number of items in correct relative position
- **Numeric tolerance:** Configurable epsilon for math answers (e.g., answer = 3.14, accept 3.13-3.15)
- **Unit flexibility:** Accept "5 m/s" or "5 meters per second" or "5m/s"

### 5.6.3 Manual Grading Interface

- **Queue-based:** Ungraded essay/short-answer responses appear in grading queue
- **Inline rubric:** Rubric criteria displayed alongside student response
- **Annotation tools:** Highlight text, add inline comments, strikethrough
- **Quick scores:** Click rubric level for each criterion, total auto-calculated
- **Batch grading:** Grade same question across all students (horizontal grading)
- **AI suggestions:** AI provides suggested score and feedback; teacher can accept/modify
- **Moderation:** Random sample (10%) double-graded for consistency check
- **Keyboard shortcuts:** Number keys for score assignment, Tab to next response

### 5.6.4 Class Analytics

| Metric | Description |
|--------|-------------|
| Mean score | Average score across all students |
| Median score | Middle score value |
| Standard deviation | Score spread |
| Pass rate | Percentage scoring above pass threshold |
| Score distribution | Histogram of score ranges |
| Question difficulty index | Percentage of students answering correctly |
| Question discrimination index | Correlation between question score and total score |
| Bloom level performance | Average score per Bloom taxonomy level |
| Topic performance | Average score per curriculum topic |
| Time analysis | Average, min, max completion time |
| Reliability coefficient | Cronbach's alpha for exam reliability |

### 5.6.5 Comparative Analytics

- **Class vs. school:** How does this class compare to school average for same subject/grade?
- **Current vs. historical:** How does this exam compare to previous terms?
- **Teacher comparison:** Anonymized comparison of class performance across teachers (admin only)
- **Question bank insights:** Which questions are most/least effective across all uses?
- **Trend lines:** Performance trends over time by class, subject, topic

### 5.6.6 Individual Student Analytics

- **Strengths/weaknesses map:** Visual heatmap of performance by topic
- **Bloom level profile:** Radar chart showing performance at each Bloom level
- **Growth trajectory:** Score trend line across all exams in subject
- **Time management:** How student allocates time across sections and question types
- **Comparison to peers:** Percentile ranking (anonymized)
- **Recommendations:** AI-generated study suggestions based on weak areas
- **Exportable report:** PDF report card for parent distribution

## 5.7 Student Portal

### Features
- **Dashboard:** Upcoming exams, recent results, study recommendations
- **Exam list:** Active, upcoming, and past exams with status
- **Exam-taking interface:** Clean, distraction-free exam UI with timer, progress bar, question navigation
- **Auto-save:** Responses saved every 30 seconds; resume from last save on connection loss
- **Review mode:** After submission, review answers with correct answers and explanations (if enabled)
- **Results:** Score, percentage, pass/fail, detailed breakdown by section/topic/Bloom level
- **Performance analytics:** Personal trends, strengths/weaknesses, improvement suggestions
- **Practice exams:** Access to practice exams and past papers (if shared by teacher)
- **Notifications:** Exam reminders, grade releases, teacher messages
- **Profile:** Update personal info, change password, language preference
- **Accessibility:** Font size adjustment, high contrast mode, screen reader support, RTL toggle

## 5.8 Teacher Portal

### Features
- **Dashboard:** Quick stats (exams created, pending grading, class averages), recent activity
- **Curriculum management:** Upload, view, search, share curricula
- **Question bank:** Create, import, search, filter, edit, review questions
- **AI generation:** Generate questions from curriculum with parameter controls
- **Exam builder:** Create exams with sections, questions, settings, scheduling
- **Exam monitoring:** Live view of ongoing exams (students connected, progress, flags)
- **Grading center:** Auto-graded results, manual grading queue, grade override
- **Analytics:** Class reports, question analytics, student reports, comparative analysis
- **Communication:** Announcements to classes, individual student messages
- **Settings:** Notification preferences, default exam settings, language

## 5.9 Parent Portal

### Features
- **Dashboard:** Child's upcoming exams, recent results, overall performance summary
- **Results view:** Exam scores with topic-level breakdown (no question-level detail)
- **Performance trends:** Charts showing progress over time by subject
- **Comparison:** Child's performance vs. class average (anonymized)
- **Recommendations:** AI-generated suggestions for supporting child's learning
- **Calendar:** Exam schedule for all children
- **Notifications:** Grade releases, upcoming exams, performance alerts (score drops)
- **Multi-child support:** Parents with multiple children see unified dashboard
- **Communication:** Read-only view of teacher announcements
- **Language:** Full Arabic and English support

## 5.10 Admin Dashboard

### Features
- **School overview:** Total students, teachers, exams created, questions in bank
- **User management:** CRUD for teachers, students, parents; role assignment; bulk import via CSV
- **Subscription management:** Current plan, usage vs. limits, upgrade/downgrade
- **Analytics:** School-wide performance trends, subject comparisons, teacher effectiveness
- **Curriculum oversight:** Approve/reject shared curricula, manage standards
- **Question bank oversight:** Review queue management, quality metrics
- **Proctoring dashboard:** Flagged sessions, integrity score distributions
- **Audit logs:** All system actions with user, timestamp, IP, and change details
- **Billing:** Invoice history, payment methods, usage reports
- **Settings:** School branding (logo, colors), grading policies, default exam settings
- **Integrations:** Configure SSO, SIS, LMS connections
- **Support:** Submit tickets, knowledge base access

## 5.11 Reporting

### Standard Reports
1. **Exam Summary Report:** Per-exam statistics, question analysis, score distribution
2. **Class Performance Report:** Class averages by subject, topic, Bloom level over time
3. **Student Report Card:** Individual student performance across all subjects and exams
4. **Teacher Activity Report:** Exams created, questions generated, grading turnaround time
5. **School Performance Report:** School-wide KPIs, year-over-year comparisons
6. **Question Quality Report:** Question bank health: discrimination indices, usage patterns
7. **Proctoring Report:** Integrity score distributions, violation patterns, flagged sessions
8. **Usage Report:** Platform adoption metrics: logins, exam sessions, feature utilization

### Report Features
- **Scheduled generation:** Daily, weekly, monthly, or term-end automatic generation
- **Distribution:** Email PDF to stakeholders (admin, department heads, parents)
- **Customization:** Select metrics, date ranges, filters, groupings
- **Export:** PDF, Excel, CSV formats
- **Dashboards:** Interactive web dashboards with drill-down capability

## 5.12 API Integrations

### 5.12.1 Single Sign-On (SSO)

| Provider | Protocol | Configuration |
|----------|----------|---------------|
| Google Workspace | OAuth 2.0 | Client ID, redirect URI, scopes (email, profile) |
| Microsoft Azure AD | OAuth 2.0 / OIDC | Tenant ID, client ID, redirect URI |
| Generic SAML | SAML 2.0 | IdP metadata URL, certificate, attribute mapping |

### 5.12.2 Student Information System (SIS) Integration

| System | Integration Method | Data Synced |
|--------|-------------------|-------------|
| PowerSchool | REST API | Students, classes, enrollments, teachers |
| Skyward | REST API | Students, grades, schedules |
| Infinite Campus | REST API | Students, sections, demographics |

- **Sync frequency:** Real-time webhook or scheduled (hourly/daily)
- **Direction:** Bidirectional (read students from SIS, write grades back)
- **Conflict resolution:** SIS is master for student data; ExamGenius is master for exam data

### 5.12.3 LMS Integration

| System | Integration Method | Features |
|--------|-------------------|----------|
| Moodle | LTI 1.3 | Launch exams from Moodle, grade passback |
| Canvas | LTI 1.3 + REST API | Assignment sync, grade passback, deep linking |
| Google Classroom | REST API | Assignment creation, grade passback |
| Microsoft Teams Education | Graph API | Assignment sync, grade passback |

### 5.12.4 Third-Party APIs

| Service | Purpose | Integration |
|---------|---------|-------------|
| OpenAI | Question generation, quality scoring | REST API |
| Anthropic | Fallback AI provider | REST API |
| Turnitin | Plagiarism detection (Enterprise) | REST API |
| SendGrid | Transactional email | REST API |
| Twilio | SMS notifications (optional) | REST API |
| Stripe | Payment processing | REST API + webhooks |
| AWS S3 | File storage | AWS SDK |
| AWS SES | Bulk email | AWS SDK |

---

# PART C: NON-FUNCTIONAL REQUIREMENTS

## 1. Performance

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Page load time | < 2 seconds | Lighthouse Performance Score > 80 |
| API response time (CRUD) | < 500ms (p95) | Datadog APM |
| Search response time | < 2 seconds | Full-text search across 100K+ questions |
| AI generation time | < 120 seconds for 500 questions | End-to-end measurement |
| Auto-grading time | < 30 seconds per exam session | From submission to score available |
| Concurrent users per school | 500+ | Load test with k6 |
| WebSocket latency | < 100ms | Real-time proctoring alerts |
| File upload throughput | 10MB/s minimum | S3 direct upload with presigned URLs |
| Database query time | < 100ms (p95) | PostgreSQL query monitoring |

## 2. Scalability

| Metric | Target |
|--------|--------|
| Schools supported | 100+ simultaneously |
| Concurrent exam sessions | 50,000 |
| Questions in bank | 1,000,000+ |
| Files stored | 500TB+ (S3) |
| API requests/second | 10,000 |
| Auto-scaling response | < 2 minutes to scale out |
| Database connections | Connection pooling (PgBouncer, max 500) |

### Scaling Strategy
- **Horizontal:** ECS auto-scaling based on CPU/memory thresholds
- **Database:** Read replicas for analytics queries; primary for writes
- **Caching:** Redis for session data, question search results, user permissions
- **CDN:** CloudFront for static assets, images, generated PDFs
- **Queue:** SQS for async processing (file parsing, AI generation, grading)
- **Search:** Elasticsearch cluster with auto-scaling for question bank search

## 3. Availability

| Metric | Target |
|--------|--------|
| Uptime SLA | 99.9% (8.7 hours downtime/year) |
| Recovery Time Objective (RTO) | < 1 hour |
| Recovery Point Objective (RPO) | < 5 minutes |
| Planned maintenance window | Sundays 02:00-06:00 Cairo time |
| Failover | Automatic, multi-AZ deployment |
| Backup frequency | Continuous (WAL archiving) + daily snapshots |
| Backup retention | 30 days for daily, 1 year for monthly |
| Disaster recovery | Cross-region backup to eu-west-1 |

## 4. Security

| Requirement | Implementation |
|-------------|---------------|
| Authentication | Auth0 with MFA mandatory for teachers and admins |
| Authorization | RBAC with 6 roles: Super Admin, School Admin, Teacher, Reviewer, Student, Parent |
| Transport encryption | TLS 1.3 (minimum TLS 1.2) |
| Data at rest encryption | AES-256 via AWS KMS |
| Key management | AWS KMS with HSM-backed keys |
| Password policy | Min 12 chars, complexity requirements, bcrypt hashing |
| Session management | JWT with 15-min access token, 7-day refresh token |
| API rate limiting | Per-user and per-school limits via Redis |
| Input validation | Server-side validation for all inputs; parameterized queries |
| XSS prevention | Content Security Policy headers; output encoding |
| CSRF protection | SameSite cookies + CSRF tokens |
| SQL injection | Parameterized queries exclusively (no raw SQL) |
| File upload security | Type validation, virus scanning (ClamAV), size limits |
| Audit logging | All data mutations logged with user, timestamp, IP, before/after values |
| Penetration testing | Annual third-party pen test (OWASP Top 10) |
| Vulnerability scanning | Weekly automated scans (Dependabot + Snyk) |
| Data classification | PII tagged and encrypted; exam content access-controlled |

## 5. Data Residency

| Requirement | Implementation |
|-------------|---------------|
| Primary region | AWS me-south-1 (Bahrain) or af-south-1 (Cape Town) - nearest to Egypt |
| Preference | AWS Cairo region when available; Azure UAE North as alternative |
| Data sovereignty | All student PII stored in primary region only |
| Cross-border transfer | Explicit consent required; encrypted in transit |
| Backup region | Same region; cross-region only for disaster recovery (encrypted) |
| Compliance | Egyptian Data Protection Law alignment |
| Data retention | Student data: 7 years after graduation; exam data: 5 years |
| Right to erasure | Admin can request full data deletion (30-day processing) |

## 6. Accessibility

| Requirement | Standard |
|-------------|----------|
| WCAG compliance | Level AA (WCAG 2.1) |
| Arabic RTL support | Full bidirectional text rendering |
| Screen reader | ARIA labels on all interactive elements |
| Keyboard navigation | Full keyboard accessibility; visible focus indicators |
| Color contrast | Minimum 4.5:1 for normal text, 3:1 for large text |
| Font scaling | Support 50-200% browser zoom without layout breaking |
| Alt text | All images have descriptive alt text |
| Captions | Video content has captions/subtitles |
| Extra time | Per-student accommodation settings (25%, 50%, 100% extra) |
| High contrast mode | Toggle for high contrast color scheme |
| Language | English and Arabic; French and German planned for Year 2 |

---

# PART D: COMPLETE DATABASE SCHEMA

```sql
-- =============================================================
-- ExamGenius Database Schema
-- PostgreSQL 15+
-- All timestamps in UTC
-- UUIDs for primary keys (gen_random_uuid())
-- =============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================
-- ENUM TYPES
-- =============================================================

CREATE TYPE subscription_tier AS ENUM ('STARTER', 'PROFESSIONAL', 'ENTERPRISE');
CREATE TYPE user_role AS ENUM ('SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'REVIEWER', 'STUDENT', 'PARENT');
CREATE TYPE question_type AS ENUM (
    'MCQ', 'TRUE_FALSE', 'SHORT_ANSWER', 'ESSAY', 
    'FILL_IN_BLANK', 'MATCHING', 'ORDERING', 
    'CASE_STUDY', 'DATA_INTERPRETATION'
);
CREATE TYPE difficulty_level AS ENUM ('EASY', 'MEDIUM', 'HARD', 'EXPERT');
CREATE TYPE question_status AS ENUM ('DRAFT', 'SUBMITTED', 'IN_REVIEW', 'APPROVED', 'PUBLISHED', 'ARCHIVED', 'REJECTED');
CREATE TYPE exam_status AS ENUM ('DRAFT', 'SCHEDULED', 'PUBLISHED', 'ACTIVE', 'COMPLETED', 'ARCHIVED');
CREATE TYPE session_status AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'PAUSED', 'SUBMITTED', 'TIMED_OUT', 'TERMINATED');
CREATE TYPE subscription_status AS ENUM ('TRIAL', 'ACTIVE', 'PAST_DUE', 'CANCELLED', 'EXPIRED');
CREATE TYPE proctoring_event_type AS ENUM (
    'TAB_SWITCH', 'FULLSCREEN_EXIT', 'COPY_PASTE', 'RIGHT_CLICK',
    'DEV_TOOLS', 'NO_FACE', 'MULTIPLE_FACES', 'DIFFERENT_PERSON',
    'LOOKING_AWAY', 'PHONE_DETECTED', 'SUSPICIOUS_AUDIO',
    'DEVICE_MOVEMENT', 'SCREENSHOT_ATTEMPT', 'VM_DETECTED'
);
CREATE TYPE severity_level AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE school_type AS ENUM ('BRITISH', 'AMERICAN', 'IB', 'FRENCH', 'GERMAN', 'NATIONAL', 'OTHER');

-- =============================================================
-- TABLE: schools
-- =============================================================

CREATE TABLE schools (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    type            school_type NOT NULL DEFAULT 'OTHER',
    country         VARCHAR(100) NOT NULL DEFAULT 'Egypt',
    city            VARCHAR(100) NOT NULL,
    address         TEXT,
    phone           VARCHAR(50),
    website         VARCHAR(255),
    admin_email     VARCHAR(255) NOT NULL,
    logo_url        VARCHAR(500),
    subscription_tier subscription_tier NOT NULL DEFAULT 'STARTER',
    student_count   INTEGER NOT NULL DEFAULT 0,
    teacher_count   INTEGER NOT NULL DEFAULT 0,
    timezone        VARCHAR(50) NOT NULL DEFAULT 'Africa/Cairo',
    language        VARCHAR(10) NOT NULL DEFAULT 'en',
    settings        JSONB DEFAULT '{}',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_schools_country ON schools(country);
CREATE INDEX idx_schools_city ON schools(city);
CREATE INDEX idx_schools_type ON schools(type);
CREATE INDEX idx_schools_tier ON schools(subscription_tier);

-- =============================================================
-- TABLE: users
-- =============================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id       UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    email           VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(255),  -- NULL for SSO-only users
    role            user_role NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    phone           VARCHAR(50),
    avatar_url      VARCHAR(500),
    language        VARCHAR(10) NOT NULL DEFAULT 'en',
    mfa_enabled     BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret      VARCHAR(255),
    sso_provider    VARCHAR(50),  -- 'google', 'microsoft', 'saml'
    sso_id          VARCHAR(255),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified  BOOLEAN NOT NULL DEFAULT FALSE,
    last_login      TIMESTAMP WITH TIME ZONE,
    login_count     INTEGER NOT NULL DEFAULT 0,
    settings        JSONB DEFAULT '{}',
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(email, school_id)
);

CREATE INDEX idx_users_school ON users(school_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_sso ON users(sso_provider, sso_id);

-- =============================================================
-- TABLE: curricula
-- =============================================================

CREATE TABLE curricula (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id       UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    standard        VARCHAR(50) NOT NULL,  -- 'IGCSE', 'IB', 'AP', etc.
    grade_levels    INTEGER[] NOT NULL,
    subjects        TEXT[] NOT NULL,
    description     TEXT,
    version         VARCHAR(50) NOT NULL DEFAULT '1.0',
    is_shared       BOOLEAN NOT NULL DEFAULT FALSE,
    sharing_scope   VARCHAR(20) DEFAULT 'school',  -- 'school', 'department', 'private'
    topics_json     JSONB,  -- Extracted topic hierarchy
    metadata        JSONB DEFAULT '{}',
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_curricula_school ON curricula(school_id);
CREATE INDEX idx_curricula_standard ON curricula(standard);
CREATE INDEX idx_curricula_subjects ON curricula USING GIN(subjects);
CREATE INDEX idx_curricula_grades ON curricula USING GIN(grade_levels);

-- =============================================================
-- TABLE: curriculum_documents
-- =============================================================

CREATE TABLE curriculum_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    curriculum_id   UUID NOT NULL REFERENCES curricula(id) ON DELETE CASCADE,
    filename        VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_type       VARCHAR(20) NOT NULL,  -- 'pdf', 'docx', 'pptx', 'txt'
    storage_path    VARCHAR(500) NOT NULL,  -- S3 key
    size_bytes      BIGINT NOT NULL,
    page_count      INTEGER,
    extracted_text   TEXT,
    extracted_topics JSONB,
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    processing_error TEXT,
    checksum        VARCHAR(64),  -- SHA-256 for dedup
    processed_at    TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_currdocs_curriculum ON curriculum_documents(curriculum_id);
CREATE INDEX idx_currdocs_status ON curriculum_documents(processing_status);
CREATE INDEX idx_currdocs_checksum ON curriculum_documents(checksum);

-- =============================================================
-- TABLE: questions
-- =============================================================

CREATE TABLE questions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id           UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    curriculum_id       UUID REFERENCES curricula(id) ON DELETE SET NULL,
    question_type       question_type NOT NULL,
    difficulty          difficulty_level NOT NULL DEFAULT 'MEDIUM',
    bloom_level         INTEGER NOT NULL CHECK (bloom_level BETWEEN 1 AND 6),
    subject             VARCHAR(100) NOT NULL,
    grade               INTEGER NOT NULL CHECK (grade BETWEEN 1 AND 12),
    topic               VARCHAR(200) NOT NULL,
    sub_topic           VARCHAR(200),
    curriculum_standard VARCHAR(50),
    content_text        TEXT NOT NULL,  -- Plain text version
    content_rich        JSONB NOT NULL,  -- Rich content (LaTeX, images, etc.)
    answer_key_json     JSONB NOT NULL,  -- Structured answer data
    explanation         TEXT,
    quality_score       INTEGER CHECK (quality_score BETWEEN 0 AND 100),
    usage_count         INTEGER NOT NULL DEFAULT 0,
    success_rate        DECIMAL(5,2),
    discrimination_index DECIMAL(5,4),
    status              question_status NOT NULL DEFAULT 'DRAFT',
    ai_generated        BOOLEAN NOT NULL DEFAULT FALSE,
    ai_model            VARCHAR(50),
    ai_prompt_version   VARCHAR(20),
    language            VARCHAR(10) NOT NULL DEFAULT 'en',
    created_by          UUID NOT NULL REFERENCES users(id),
    reviewed_by         UUID REFERENCES users(id),
    review_notes        TEXT,
    reviewed_at         TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_questions_school ON questions(school_id);
CREATE INDEX idx_questions_curriculum ON questions(curriculum_id);
CREATE INDEX idx_questions_type ON questions(question_type);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_questions_bloom ON questions(bloom_level);
CREATE INDEX idx_questions_subject ON questions(subject);
CREATE INDEX idx_questions_grade ON questions(grade);
CREATE INDEX idx_questions_topic ON questions(topic);
CREATE INDEX idx_questions_status ON questions(status);
CREATE INDEX idx_questions_quality ON questions(quality_score);
CREATE INDEX idx_questions_content ON questions USING GIN(to_tsvector('english', content_text));

-- =============================================================
-- TABLE: question_tags
-- =============================================================

CREATE TABLE question_tags (
    question_id     UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    tag             VARCHAR(100) NOT NULL,
    PRIMARY KEY (question_id, tag)
);

CREATE INDEX idx_qtags_tag ON question_tags(tag);

-- =============================================================
-- TABLE: exams
-- =============================================================

CREATE TABLE exams (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id           UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    curriculum_id       UUID REFERENCES curricula(id) ON DELETE SET NULL,
    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    subject             VARCHAR(100) NOT NULL,
    grade               INTEGER NOT NULL,
    total_points        DECIMAL(10,2) NOT NULL,
    time_limit_minutes  INTEGER,
    shuffle_questions   BOOLEAN NOT NULL DEFAULT FALSE,
    shuffle_options     BOOLEAN NOT NULL DEFAULT FALSE,
    show_results        BOOLEAN NOT NULL DEFAULT TRUE,
    show_answers        BOOLEAN NOT NULL DEFAULT FALSE,
    show_explanations   BOOLEAN NOT NULL DEFAULT FALSE,
    access_password     VARCHAR(255),  -- Hashed
    allowed_ips         TEXT[],  -- IP whitelist
    start_at            TIMESTAMP WITH TIME ZONE,
    end_at              TIMESTAMP WITH TIME ZONE,
    max_attempts        INTEGER NOT NULL DEFAULT 1,
    late_submission     BOOLEAN NOT NULL DEFAULT FALSE,
    late_penalty_pct    DECIMAL(5,2) DEFAULT 0,
    passing_score_pct   DECIMAL(5,2) DEFAULT 50.00,
    proctoring_enabled  BOOLEAN NOT NULL DEFAULT FALSE,
    proctoring_level    VARCHAR(20) DEFAULT 'basic',  -- 'basic', 'standard', 'strict'
    instructions        TEXT,
    status              exam_status NOT NULL DEFAULT 'DRAFT',
    settings            JSONB DEFAULT '{}',
    created_by          UUID NOT NULL REFERENCES users(id),
    published_at        TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_exams_school ON exams(school_id);
CREATE INDEX idx_exams_status ON exams(status);
CREATE INDEX idx_exams_subject ON exams(subject);
CREATE INDEX idx_exams_grade ON exams(grade);
CREATE INDEX idx_exams_start ON exams(start_at);
CREATE INDEX idx_exams_end ON exams(end_at);

-- =============================================================
-- TABLE: exam_sections
-- =============================================================

CREATE TABLE exam_sections (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id             UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    title               VARCHAR(255) NOT NULL,
    instructions        TEXT,
    time_limit_minutes  INTEGER,
    allow_back_nav      BOOLEAN NOT NULL DEFAULT TRUE,
    order_index         INTEGER NOT NULL,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_exam_sections_exam ON exam_sections(exam_id);

-- =============================================================
-- TABLE: exam_questions
-- =============================================================

CREATE TABLE exam_questions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id         UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    section_id      UUID REFERENCES exam_sections(id) ON DELETE SET NULL,
    question_id     UUID NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    points          DECIMAL(10,2) NOT NULL,
    order_index     INTEGER NOT NULL,
    is_required     BOOLEAN NOT NULL DEFAULT TRUE,
    is_bonus        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_exam_questions_exam ON exam_questions(exam_id);
CREATE INDEX idx_exam_questions_section ON exam_questions(section_id);
CREATE INDEX idx_exam_questions_question ON exam_questions(question_id);
CREATE UNIQUE INDEX idx_exam_questions_unique ON exam_questions(exam_id, question_id);

-- =============================================================
-- TABLE: exam_sessions
-- =============================================================

CREATE TABLE exam_sessions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id             UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    student_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    attempt_number      INTEGER NOT NULL DEFAULT 1,
    start_time          TIMESTAMP WITH TIME ZONE,
    end_time            TIMESTAMP WITH TIME ZONE,
    submitted_at        TIMESTAMP WITH TIME ZONE,
    status              session_status NOT NULL DEFAULT 'NOT_STARTED',
    integrity_score     INTEGER CHECK (integrity_score BETWEEN 0 AND 100),
    ip_address          INET,
    user_agent          TEXT,
    proctoring_enabled  BOOLEAN NOT NULL DEFAULT FALSE,
    browser_info        JSONB,
    time_spent_seconds  INTEGER,
    questions_answered  INTEGER NOT NULL DEFAULT 0,
    total_questions     INTEGER NOT NULL,
    last_activity       TIMESTAMP WITH TIME ZONE,
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sessions_exam ON exam_sessions(exam_id);
CREATE INDEX idx_sessions_student ON exam_sessions(student_id);
CREATE INDEX idx_sessions_status ON exam_sessions(status);
CREATE INDEX idx_sessions_start ON exam_sessions(start_time);
CREATE UNIQUE INDEX idx_sessions_attempt ON exam_sessions(exam_id, student_id, attempt_number);

-- =============================================================
-- TABLE: student_responses
-- =============================================================

CREATE TABLE student_responses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID NOT NULL REFERENCES exam_sessions(id) ON DELETE CASCADE,
    question_id         UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    exam_question_id    UUID NOT NULL REFERENCES exam_questions(id) ON DELETE CASCADE,
    response_json       JSONB NOT NULL,  -- Student's answer
    is_auto_graded      BOOLEAN NOT NULL DEFAULT FALSE,
    auto_grade_score    DECIMAL(10,2),
    auto_grade_feedback TEXT,
    manual_grade_score  DECIMAL(10,2),
    manual_grade_feedback TEXT,
    final_score         DECIMAL(10,2),
    graded_by           UUID REFERENCES users(id),
    graded_at           TIMESTAMP WITH TIME ZONE,
    time_spent_seconds  INTEGER,
    flagged             BOOLEAN NOT NULL DEFAULT FALSE,
    flag_reason         TEXT,
    response_order      INTEGER NOT NULL,  -- Order student saw the question
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_responses_session ON student_responses(session_id);
CREATE INDEX idx_responses_question ON student_responses(question_id);
CREATE INDEX idx_responses_graded ON student_responses(is_auto_graded, graded_at);
CREATE UNIQUE INDEX idx_responses_unique ON student_responses(session_id, question_id);

-- =============================================================
-- TABLE: proctoring_events
-- =============================================================

CREATE TABLE proctoring_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID NOT NULL REFERENCES exam_sessions(id) ON DELETE CASCADE,
    event_type          proctoring_event_type NOT NULL,
    severity            severity_level NOT NULL DEFAULT 'LOW',
    confidence_score    DECIMAL(5,4),  -- AI confidence (0-1)
    description         TEXT,
    media_path          VARCHAR(500),  -- S3 path for screenshot/video clip
    metadata            JSONB DEFAULT '{}',
    reviewed            BOOLEAN NOT NULL DEFAULT FALSE,
    reviewed_by         UUID REFERENCES users(id),
    review_action       VARCHAR(50),  -- 'dismissed', 'flagged', 'warning_sent', 'exam_paused'
    detected_at         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_proctoring_session ON proctoring_events(session_id);
CREATE INDEX idx_proctoring_type ON proctoring_events(event_type);
CREATE INDEX idx_proctoring_severity ON proctoring_events(severity);
CREATE INDEX idx_proctoring_reviewed ON proctoring_events(reviewed);

-- =============================================================
-- TABLE: grades
-- =============================================================

CREATE TABLE grades (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID NOT NULL REFERENCES exam_sessions(id) ON DELETE CASCADE UNIQUE,
    exam_id             UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    student_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_score         DECIMAL(10,2) NOT NULL,
    max_score           DECIMAL(10,2) NOT NULL,
    percentage          DECIMAL(5,2) NOT NULL,
    pass_fail           BOOLEAN NOT NULL,
    grade_letter        VARCHAR(5),  -- 'A*', 'A', 'B', etc.
    auto_graded_score   DECIMAL(10,2),
    manual_graded_score DECIMAL(10,2),
    score_breakdown     JSONB,  -- Per-section, per-topic, per-bloom breakdown
    graded_at           TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    released            BOOLEAN NOT NULL DEFAULT FALSE,
    released_at         TIMESTAMP WITH TIME ZONE,
    report_generated    BOOLEAN NOT NULL DEFAULT FALSE,
    report_path         VARCHAR(500),
    override_score      DECIMAL(10,2),
    override_by         UUID REFERENCES users(id),
    override_reason     TEXT,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_grades_exam ON grades(exam_id);
CREATE INDEX idx_grades_student ON grades(student_id);
CREATE INDEX idx_grades_released ON grades(released);

-- =============================================================
-- TABLE: subscriptions
-- =============================================================

CREATE TABLE subscriptions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id           UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    tier                subscription_tier NOT NULL,
    student_count       INTEGER NOT NULL,
    price_per_student   DECIMAL(10,2) NOT NULL,
    annual_total        DECIMAL(10,2) NOT NULL,
    currency            VARCHAR(3) NOT NULL DEFAULT 'USD',
    billing_cycle       VARCHAR(20) NOT NULL DEFAULT 'annual',  -- 'annual', 'semi-annual'
    start_date          DATE NOT NULL,
    end_date            DATE NOT NULL,
    auto_renew          BOOLEAN NOT NULL DEFAULT TRUE,
    status              subscription_status NOT NULL DEFAULT 'TRIAL',
    stripe_customer_id  VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    payment_method      VARCHAR(50),
    last_payment_date   DATE,
    next_payment_date   DATE,
    trial_ends_at       DATE,
    cancelled_at        TIMESTAMP WITH TIME ZONE,
    cancel_reason       TEXT,
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_subs_school ON subscriptions(school_id);
CREATE INDEX idx_subs_status ON subscriptions(status);
CREATE INDEX idx_subs_dates ON subscriptions(start_date, end_date);

-- =============================================================
-- TABLE: audit_logs
-- =============================================================

CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id       UUID REFERENCES schools(id) ON DELETE SET NULL,
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(100) NOT NULL,  -- 'create', 'update', 'delete', 'login', 'export'
    entity_type     VARCHAR(100) NOT NULL,  -- 'exam', 'question', 'user', 'grade', etc.
    entity_id       UUID,
    old_value       JSONB,
    new_value       JSONB,
    ip_address      INET,
    user_agent      TEXT,
    request_id      UUID,  -- Correlation ID for request tracing
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_school ON audit_logs(school_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at);

-- =============================================================
-- TABLE: training_data (for AI model fine-tuning)
-- =============================================================

CREATE TABLE training_data (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id         UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    curriculum_context  TEXT NOT NULL,
    question_type       question_type NOT NULL,
    difficulty          difficulty_level NOT NULL,
    bloom_level         INTEGER NOT NULL,
    subject             VARCHAR(100) NOT NULL,
    grade               INTEGER NOT NULL,
    topic               VARCHAR(200) NOT NULL,
    curriculum_standard VARCHAR(50) NOT NULL,
    input_prompt        TEXT NOT NULL,  -- The prompt used to generate
    output_json         JSONB NOT NULL,  -- The final approved question
    teacher_action      VARCHAR(20) NOT NULL,  -- 'accepted', 'edited'
    teacher_edits       JSONB,  -- Original vs edited diff
    quality_score       INTEGER NOT NULL,
    teacher_id          UUID NOT NULL REFERENCES users(id),
    reviewed_at         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    used_in_training    BOOLEAN NOT NULL DEFAULT FALSE,
    training_batch      VARCHAR(50),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_training_subject ON training_data(subject);
CREATE INDEX idx_training_type ON training_data(question_type);
CREATE INDEX idx_training_used ON training_data(used_in_training);

-- =============================================================
-- TABLE: notifications
-- =============================================================

CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    school_id       UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    type            VARCHAR(50) NOT NULL,  -- 'exam_reminder', 'grade_released', 'review_request'
    title           VARCHAR(255) NOT NULL,
    message         TEXT NOT NULL,
    link            VARCHAR(500),
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    read_at         TIMESTAMP WITH TIME ZONE,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(user_id, is_read);

-- =============================================================
-- TABLE: parent_student_links
-- =============================================================

CREATE TABLE parent_student_links (
    parent_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relationship    VARCHAR(50) NOT NULL DEFAULT 'parent',  -- 'parent', 'guardian'
    verified        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (parent_id, student_id)
);

CREATE INDEX idx_parent_links_student ON parent_student_links(student_id);
```

---

# PART E: API ENDPOINTS

## Authentication

| Method | Path | Description | Auth Roles | Key Params |
|--------|------|-------------|------------|------------|
| POST | /api/auth/login | Email/password login | Public | `{email, password}` -> `{access_token, refresh_token, user}` |
| POST | /api/auth/refresh | Refresh access token | Public | `{refresh_token}` -> `{access_token}` |
| POST | /api/auth/logout | Invalidate tokens | All authenticated | `{refresh_token}` -> `{success: true}` |
| GET | /api/auth/sso/:provider | Initiate SSO flow | Public | provider: google, microsoft, saml -> redirect URL |
| GET | /api/auth/sso/:provider/callback | SSO callback | Public | `{code, state}` -> `{access_token, refresh_token, user}` |
| POST | /api/auth/mfa/setup | Set up MFA | All authenticated | -> `{secret, qr_code_url}` |
| POST | /api/auth/mfa/verify | Verify MFA code | All authenticated | `{code}` -> `{verified: true}` |
| POST | /api/auth/password/reset | Request password reset | Public | `{email}` -> `{message}` |
| POST | /api/auth/password/change | Change password | All authenticated | `{old_password, new_password}` -> `{success: true}` |

## Curriculum Management

| Method | Path | Description | Auth Roles | Key Params |
|--------|------|-------------|------------|------------|
| POST | /api/curriculum/upload | Upload curriculum document(s) | Teacher, Admin | multipart/form-data: files[], curriculum_id? -> `{document_ids[], status}` |
| POST | /api/curriculum | Create curriculum entry | Teacher, Admin | `{name, standard, grade_levels, subjects}` -> `{curriculum}` |
| GET | /api/curriculum | List curricula | Teacher, Admin | `?subject, grade, standard, search, page, limit` -> `{curricula[], total, page}` |
| GET | /api/curriculum/:id | Get curriculum detail | Teacher, Admin | -> `{curriculum, documents[], topics}` |
| PUT | /api/curriculum/:id | Update curriculum | Teacher (owner), Admin | `{name, standard, ...}` -> `{curriculum}` |
| DELETE | /api/curriculum/:id | Delete curriculum | Teacher (owner), Admin | -> `{success: true}` |
| GET | /api/curriculum/:id/topics | Get extracted topics | Teacher, Admin | -> `{topics_hierarchy}` |
| POST | /api/curriculum/:id/process | Trigger reprocessing | Teacher (owner), Admin | -> `{job_id, status}` |
| GET | /api/curriculum/:id/documents | List documents | Teacher, Admin | -> `{documents[]}` |
| DELETE | /api/curriculum/:id/documents/:docId | Delete document | Teacher (owner), Admin | -> `{success: true}` |
| POST | /api/curriculum/search | Search across curricula | Teacher, Admin | `{query, filters}` -> `{results[], total}` |

## Question Management

| Method | Path | Description | Auth Roles | Key Params |
|--------|------|-------------|------------|------------|
| POST | /api/questions | Create question | Teacher | `{question_type, content_text, ...}` -> `{question}` |
| GET | /api/questions/:id | Get question | Teacher, Admin | -> `{question, tags[], usage_stats}` |
| PUT | /api/questions/:id | Update question | Teacher (owner/reviewer), Admin | `{content_text, ...}` -> `{question}` |
| DELETE | /api/questions/:id | Delete question | Teacher (owner), Admin | -> `{success: true}` |
| GET | /api/questions/search | Search questions | Teacher, Admin | `?type, difficulty, bloom, subject, grade, topic, status, tags, q, page, limit` -> `{questions[], total}` |
| POST | /api/questions/bulk-import | Import questions from CSV/Excel | Teacher, Admin | multipart/form-data: file -> `{imported, failed, errors[]}` |
| POST | /api/questions/generate | AI generate questions | Teacher, Admin | `{curriculum_id, topic, type, count, difficulty, bloom_level}` -> `{questions[], job_id}` |
| GET | /api/questions/generate/:jobId | Check generation status | Teacher, Admin | -> `{status, progress, questions[]}` |
| POST | /api/questions/:id/submit | Submit for review | Teacher (owner) | -> `{question}` |
| POST | /api/questions/:id/review | Submit review decision | Reviewer, Admin | `{action: 'approve'/'reject', notes}` -> `{question}` |
| GET | /api/questions/review-queue | Get review queue | Reviewer, Admin | `?subject, grade, page` -> `{questions[], total}` |
| POST | /api/questions/:id/tags | Add tags | Teacher (owner), Admin | `{tags[]}` -> `{question}` |
| DELETE | /api/questions/:id/tags/:tag | Remove tag | Teacher (owner), Admin | -> `{success: true}` |

## Exam Management

| Method | Path | Description | Auth Roles | Key Params |
|--------|------|-------------|------------|------------|
| POST | /api/exams | Create exam | Teacher | `{title, subject, grade, ...}` -> `{exam}` |
| GET | /api/exams/:id | Get exam detail | Teacher (owner), Admin | -> `{exam, sections[], questions[]}` |
| PUT | /api/exams/:id | Update exam | Teacher (owner), Admin | `{title, ...}` -> `{exam}` |
| DELETE | /api/exams/:id | Delete exam | Teacher (owner), Admin | -> `{success: true}` |
| GET | /api/exams | List exams | Teacher, Admin | `?status, subject, grade, page` -> `{exams[], total}` |
| POST | /api/exams/:id/sections | Add section | Teacher (owner) | `{title, time_limit, order}` -> `{section}` |
| PUT | /api/exams/:id/sections/:sectionId | Update section | Teacher (owner) | `{title, ...}` -> `{section}` |
| DELETE | /api/exams/:id/sections/:sectionId | Delete section | Teacher (owner) | -> `{success: true}` |
| POST | /api/exams/:id/questions | Add questions to exam | Teacher (owner) | `{question_ids[], section_id, points}` -> `{exam_questions[]}` |
| DELETE | /api/exams/:id/questions/:eqId | Remove question from exam | Teacher (owner) | -> `{success: true}` |
| PUT | /api/exams/:id/questions/reorder | Reorder questions | Teacher (owner) | `{order: [{id, index}]}` -> `{success: true}` |
| POST | /api/exams/:id/publish | Publish exam | Teacher (owner), Admin | -> `{exam}` |
| POST | /api/exams/:id/schedule | Schedule exam | Teacher (owner) | `{start_at, end_at}` -> `{exam}` |
| POST | /api/exams/:id/clone | Clone exam | Teacher | -> `{new_exam}` |
| GET | /api/exams/:id/export-pdf | Export exam as PDF | Teacher (owner), Admin | `?include_answers` -> PDF file |
| POST | /api/exams/:id/validate | Validate exam | Teacher (owner) | -> `{valid, errors[], warnings[]}` |
| GET | /api/exams/:id/preview | Preview exam as student | Teacher (owner) | -> `{preview_url}` |

## Exam Sessions

| Method | Path | Description | Auth Roles | Key Params |
|--------|------|-------------|------------|------------|
| POST | /api/sessions/start | Start exam session | Student | `{exam_id, password?}` -> `{session_id, questions[], time_remaining}` |
| POST | /api/sessions/:id/respond | Submit response | Student | `{question_id, response_json}` -> `{saved: true}` |
| POST | /api/sessions/:id/complete | Complete/submit exam | Student | -> `{session, grade?}` |
| GET | /api/sessions/:id/status | Get session status | Student, Teacher, Admin | -> `{session, progress, time_remaining}` |
| GET | /api/sessions/:id/responses | Get all responses | Student (own), Teacher, Admin | -> `{responses[]}` |
| POST | /api/sessions/:id/pause | Pause session (teacher/proctor) | Teacher, Admin | -> `{session}` |
| POST | /api/sessions/:id/resume | Resume paused session | Teacher, Admin | -> `{session}` |
| POST | /api/sessions/:id/terminate | Terminate session | Teacher, Admin | `{reason}` -> `{session}` |
| GET | /api/exams/:id/sessions | List all sessions for exam | Teacher, Admin | `?status, page` -> `{sessions[], total}` |
| GET | /api/exams/:id/monitor | Live monitoring data | Teacher, Admin | -> `{active_sessions[], stats}` (WebSocket upgrade) |

## Grading

| Method | Path | Description | Auth Roles | Key Params |
|--------|------|-------------|------------|------------|
| POST | /api/grading/auto/:sessionId | Auto-grade a session | System, Teacher | -> `{grade, details[]}` |
| POST | /api/grading/auto/exam/:examId | Auto-grade all sessions for exam | Teacher, Admin | -> `{job_id, status}` |
| GET | /api/grading/manual/queue | Get manual grading queue | Teacher | `?exam_id, question_type, page` -> `{items[], total}` |
| POST | /api/grading/manual/:responseId | Submit manual grade | Teacher | `{score, feedback, rubric_scores}` -> `{response}` |
| PUT | /api/grading/override/:gradeId | Override final grade | Admin | `{score, reason}` -> `{grade}` |
| GET | /api/grading/exam/:examId/summary | Grading summary | Teacher, Admin | -> `{graded, pending, stats}` |
| POST | /api/grading/release/:examId | Release grades to students | Teacher, Admin | -> `{released_count}` |

## Analytics

| Method | Path | Description | Auth Roles | Key Params |
|--------|------|-------------|------------|------------|
| GET | /api/analytics/class/:examId | Class summary analytics | Teacher, Admin | -> `{mean, median, stdev, pass_rate, distribution, ...}` |
| GET | /api/analytics/questions/:examId | Question-level analytics | Teacher, Admin | -> `{questions[{id, difficulty_index, discrimination_index, ...}]}` |
| GET | /api/analytics/student/:studentId | Student performance report | Teacher, Admin, Student (own), Parent | `?subject, from, to` -> `{performance, trends, strengths, weaknesses}` |
| GET | /api/analytics/school | School-wide report | Admin | `?from, to, subject, grade` -> `{kpis, trends, comparisons}` |
| GET | /api/analytics/comparative | Comparative analysis | Admin | `{exam_ids[], or class_ids[]}` -> `{comparison}` |
| GET | /api/analytics/bloom/:examId | Bloom level analysis | Teacher, Admin | -> `{levels[{level, avg_score, question_count}]}` |
| GET | /api/analytics/topics/:examId | Topic performance | Teacher, Admin | -> `{topics[{topic, avg_score, question_count}]}` |
| GET | /api/analytics/trends | Performance trends | Teacher, Admin | `?student_id, subject, period` -> `{data_points[]}` |

## Admin

| Method | Path | Description | Auth Roles | Key Params |
|--------|------|-------------|------------|------------|
| POST | /api/admin/schools | Create school | Super Admin | `{name, type, city, ...}` -> `{school}` |
| GET | /api/admin/schools | List all schools | Super Admin | -> `{schools[], total}` |
| PUT | /api/admin/schools/:id | Update school | Super Admin, School Admin | `{...}` -> `{school}` |
| GET | /api/admin/users | List users | School Admin | `?role, search, page` -> `{users[], total}` |
| POST | /api/admin/users | Create user | School Admin | `{email, role, ...}` -> `{user}` |
| PUT | /api/admin/users/:id | Update user | School Admin | `{...}` -> `{user}` |
| DELETE | /api/admin/users/:id | Deactivate user | School Admin | -> `{success: true}` |
| POST | /api/admin/users/bulk-import | Bulk import users | School Admin | CSV file -> `{imported, failed, errors[]}` |
| GET | /api/admin/billing | Billing information | School Admin | -> `{subscription, invoices[], usage}` |
| POST | /api/admin/billing/upgrade | Upgrade subscription | School Admin | `{tier, student_count}` -> `{subscription}` |
| GET | /api/admin/audit-logs | Get audit logs | School Admin, Super Admin | `?user_id, action, from, to, page` -> `{logs[], total}` |
| GET | /api/admin/system/health | System health check | Super Admin | -> `{services[], status, uptime}` |
| GET | /api/admin/system/metrics | System metrics | Super Admin | -> `{cpu, memory, db_connections, api_latency, ...}` |

## Proctoring

| Method | Path | Description | Auth Roles | Key Params |
|--------|------|-------------|------------|------------|
| GET | /api/proctoring/sessions/:sessionId/events | Get proctoring events | Teacher, Admin | `?type, severity, page` -> `{events[], total}` |
| POST | /api/proctoring/events | Report proctoring event | System (client) | `{session_id, event_type, severity, media?}` -> `{event}` |
| PUT | /api/proctoring/events/:id/review | Review/flag event | Teacher, Admin | `{action, notes}` -> `{event}` |
| GET | /api/proctoring/sessions/:sessionId/integrity | Get integrity score | Teacher, Admin | -> `{score, breakdown, events_summary}` |
| GET | /api/proctoring/dashboard | Proctor dashboard | Teacher, Admin | `?exam_id` -> `{active_sessions[], alerts[], stats}` (WebSocket) |
| POST | /api/proctoring/sessions/:sessionId/warning | Send warning to student | Teacher | `{message}` -> `{sent: true}` |
| GET | /api/proctoring/sessions/:sessionId/photos | Get session photos | Teacher, Admin | `?from, to` -> `{photos[]}` |
| GET | /api/proctoring/sessions/:sessionId/video | Get session video | Admin | -> video stream |

## Notifications

| Method | Path | Description | Auth Roles | Key Params |
|--------|------|-------------|------------|------------|
| GET | /api/notifications | Get user notifications | All authenticated | `?unread_only, page` -> `{notifications[], total, unread_count}` |
| PUT | /api/notifications/:id/read | Mark as read | All authenticated | -> `{notification}` |
| PUT | /api/notifications/read-all | Mark all as read | All authenticated | -> `{updated_count}` |
| GET | /api/notifications/settings | Get notification preferences | All authenticated | -> `{settings}` |
| PUT | /api/notifications/settings | Update notification preferences | All authenticated | `{...}` -> `{settings}` |

## Reports

| Method | Path | Description | Auth Roles | Key Params |
|--------|------|-------------|------------|------------|
| POST | /api/reports/generate | Generate report | Teacher, Admin | `{type, params}` -> `{job_id}` |
| GET | /api/reports/:jobId | Get report status/download | Teacher, Admin | -> `{status, download_url?}` |
| GET | /api/reports | List generated reports | Teacher, Admin | `?type, page` -> `{reports[], total}` |
| POST | /api/reports/schedule | Schedule recurring report | Admin | `{type, frequency, recipients}` -> `{schedule}` |

---

# PART F: TECHNOLOGY STACK WITH RATIONALE

## Frontend

### React.js 18+ with TypeScript
**Why React over Vue/Angular:**
- **Developer availability in Egypt:** 3x more React developers on Wuzzuf and LinkedIn than Vue developers. Hiring will be significantly easier.
- **Enterprise ecosystem:** Fortune 500 companies (Meta, Airbnb, Netflix) use React, giving access to battle-tested patterns for complex UIs like exam builders.
- **Component library ecosystem:** Material UI, Ant Design, and Chakra UI provide production-ready components, accelerating development by 2-3 months.
- **TypeScript integration:** First-class TypeScript support with comprehensive type definitions for every major library.
- **Long-term support:** Meta's continued investment ensures React won't be abandoned. Vue has a smaller sponsorship base.

### Next.js 14+
**Why:** Server-side rendering for SEO (marketing pages), API routes for BFF pattern, file-based routing, image optimization, built-in internationalization support for Arabic/English.

### Additional Frontend Stack
- **State management:** Zustand (simpler than Redux for our scale, better TypeScript support)
- **Forms:** React Hook Form + Zod (validation schema shared with backend)
- **UI framework:** Tailwind CSS + Headless UI (accessible components, easy RTL support with dir="rtl")
- **Rich text editor:** TipTap (extensible, supports LaTeX via KaTeX plugin)
- **Math rendering:** KaTeX (faster than MathJax, lightweight)
- **Charts:** Recharts (React-native charts, good for analytics dashboards)
- **Real-time:** Socket.IO client (proctoring alerts, live exam monitoring)
- **Testing:** Vitest + React Testing Library + Playwright (unit + integration + E2E)

## Backend API

### Node.js 20+ with Express.js and TypeScript
**Why Node.js over Python Django or Java Spring:**
- **Same language as frontend:** TypeScript end-to-end reduces context switching. Shared types between frontend and backend eliminate API contract bugs.
- **I/O performance:** Node.js excels at handling many concurrent connections (exam sessions, WebSocket proctoring), which is our primary bottleneck.
- **NPM ecosystem:** 2M+ packages; mature libraries for every integration we need (AWS SDK, Auth0, Stripe, Socket.IO).
- **Developer cost in Egypt:** Node.js developers command 15-20% lower salaries than Java developers with equivalent experience.
- **Deployment simplicity:** Single runtime for API, WebSocket server, and background workers.

### Additional Backend Stack
- **ORM:** Prisma (type-safe database access, auto-generated types, migrations)
- **Validation:** Zod (shared schemas with frontend)
- **Authentication:** Auth0 SDK + Passport.js
- **File upload:** Multer + AWS S3 SDK (presigned URLs for large files)
- **Job queue:** BullMQ with Redis (exam grading, file processing, report generation)
- **WebSocket:** Socket.IO (proctoring, live monitoring, notifications)
- **Rate limiting:** express-rate-limit with Redis store
- **Logging:** Winston + Datadog transport
- **API documentation:** OpenAPI 3.0 via swagger-jsdoc
- **Testing:** Jest + Supertest

## AI Service

### Python 3.11+ with FastAPI
**Why Python for AI service (not Node.js):**
- **AI library ecosystem is Python-native:** transformers, torch, vLLM, langchain, sentence-transformers, scikit-learn are all Python-first. Node.js alternatives are immature wrappers.
- **FastAPI performance:** Async Python with uvicorn rivals Node.js for I/O-bound tasks and is 2-5x faster than Flask/Django for API throughput.
- **ML pipeline compatibility:** When we transition to Phase 3 (fine-tuned Llama), the entire training and inference pipeline stays in Python. No language boundary.
- **Data science tooling:** pandas, numpy, scipy for analytics calculations (Cronbach's alpha, discrimination index) are Python-native.

### AI Service Components
- **OpenAI SDK:** Question generation, quality scoring
- **Anthropic SDK:** Fallback provider
- **LangChain:** Prompt management, output parsing, chain-of-thought
- **Sentence Transformers:** Semantic similarity for plagiarism and deduplication
- **PyMuPDF (fitz):** PDF text extraction
- **python-docx / python-pptx:** Office document parsing
- **Tesseract OCR:** Scanned PDF text extraction
- **LanguageTool:** Grammar checking for generated questions
- **Hugging Face Transformers + PEFT:** Phase 3 model fine-tuning
- **vLLM:** Phase 3 model serving (high-throughput inference)

## Database

### PostgreSQL 15+
**Why PostgreSQL:**
- **ACID compliance:** Exam data integrity is non-negotiable. Eventual consistency is unacceptable for grades and responses.
- **JSONB support:** Rich question content, answer keys, and analytics data stored as structured JSON without sacrificing relational integrity.
- **Full-text search:** Built-in tsvector/tsquery for question search at small scale (Elasticsearch for large scale).
- **Array types:** Native array support for tags, grade_levels, subjects without junction tables.
- **Maturity:** 35+ years of development. Enterprise-proven. Extensive documentation and community.
- **Cost:** Open source, no licensing fees. AWS RDS manages backups, patching, failover.

### Redis 7+
**Why Redis:**
- **Session storage:** JWT blacklist and active session tracking with automatic TTL expiration.
- **Caching:** Question search results (60s TTL), user permissions (5min TTL), curriculum topic trees (1hr TTL).
- **Rate limiting:** Token bucket algorithm for API rate limiting per user and per school.
- **Job queue backend:** BullMQ uses Redis for reliable job queue with retry, priority, and delayed jobs.
- **Real-time:** Pub/sub for WebSocket message distribution across multiple API instances.
- **Exam locks:** Distributed locks to prevent concurrent exam modifications.

### Elasticsearch 8+
**Why Elasticsearch (not just PostgreSQL FTS):**
- **Scale:** PostgreSQL FTS degrades at 100K+ questions with complex filters. Elasticsearch maintains <100ms response.
- **Fuzzy matching:** Better fuzzy search for finding similar questions (deduplication).
- **Faceted search:** Native support for filter counts (e.g., "15 Easy MCQ questions in Biology Grade 10").
- **Analyzers:** Custom analyzers for Arabic text, scientific terms, mathematical notation.
- **Relevance scoring:** BM25 ranking with boost fields produces more relevant search results than PostgreSQL.
- **Aggregations:** Built-in aggregation pipeline for analytics (question usage patterns, topic distribution).

## Cloud Infrastructure

### AWS (Cairo region when available, me-south-1 Bahrain interim)
**Why AWS over Azure/GCP:**
- **Egypt proximity:** AWS me-south-1 (Bahrain) is the closest major cloud region to Egypt (~15ms latency). AWS has announced Cairo region interest.
- **Service breadth:** ECS, RDS, ElastiCache, S3, SQS, CloudFront, KMS, Route53, ACM all needed and mature on AWS.
- **Cost:** Savings Plans and Reserved Instances reduce compute costs 30-40% vs. on-demand.
- **Compliance:** SOC 2, ISO 27001, GDPR compliant. AWS signed Egypt's data processing addendum.

### Infrastructure Services
| Service | AWS Service | Purpose |
|---------|------------|---------|
| Compute | ECS Fargate | Containerized API and AI service |
| Database | RDS PostgreSQL | Primary database |
| Cache | ElastiCache Redis | Session, cache, queue backend |
| Search | OpenSearch Service | Question bank search |
| Storage | S3 | Files, media, backups |
| CDN | CloudFront | Static assets, API caching |
| Queue | SQS | Async job processing |
| Email | SES | Transactional emails |
| DNS | Route 53 | Domain management |
| SSL | ACM | Certificate management |
| Secrets | Secrets Manager | API keys, credentials |
| Encryption | KMS | Key management |
| Monitoring | CloudWatch | Infrastructure metrics |
| Load Balancer | ALB | Traffic distribution |
| Container Registry | ECR | Docker image storage |

## Authentication

### Auth0
**Why Auth0 over building it ourselves:**
- **MFA built-in:** TOTP, SMS, push notification MFA without custom development. Building MFA from scratch takes 3-4 weeks and is a security risk.
- **SSO support:** Google Workspace and Microsoft Azure AD SSO configured in hours, not weeks. SAML 2.0 support for enterprise schools.
- **Security:** Auth0's team of security engineers handles token management, brute force protection, anomaly detection. We can't match this.
- **Time saved:** 6-8 weeks of development time saved vs. building auth from scratch.
- **Cost:** Free tier covers 7,500 MAU. Paid tiers are $23/month for 1,000 MAU, scaling with growth.

## CI/CD

### GitHub Actions
**Why GitHub Actions over Jenkins/CircleCI:**
- **Free for public repos:** Unlimited minutes. Private repos get 2,000 free minutes/month.
- **Native GitHub integration:** PR checks, branch protection, deployment environments without plugins.
- **YAML-based:** Declarative pipeline definition, version-controlled alongside code.
- **Marketplace:** 15,000+ pre-built actions for testing, deployment, notifications.
- **Self-hosted runners:** Option to run on own infrastructure for cost savings at scale.

### Deployment

### Docker + ECS Fargate
**Why containers on ECS (not EC2 or Lambda):**
- **Consistency:** Same Docker image runs in development, staging, and production. "Works on my machine" eliminated.
- **Auto-scaling:** ECS auto-scales containers based on CPU/memory/request count. No server management.
- **Cost:** Fargate charges per vCPU-second. No idle EC2 instances burning money overnight.
- **Deployment:** Blue-green deployments with zero downtime. Rollback in under 60 seconds.
- **Why not Lambda:** AI service requires persistent connections and GPU access. Lambda's 15-minute timeout and cold starts are incompatible.

## Observability

### Datadog
**Why Datadog over Prometheus/Grafana or New Relic:**
- **All-in-one:** APM, infrastructure monitoring, log management, dashboards, alerting in a single platform.
- **APM traces:** Distributed tracing across Node.js API, Python AI service, PostgreSQL, Redis, and Elasticsearch. Identify bottlenecks instantly.
- **Custom metrics:** Track business metrics (questions generated, exams taken, grading time) alongside infrastructure metrics.
- **Alerting:** PagerDuty integration, Slack notifications, escalation policies.
- **Cost:** $15/host/month for infrastructure, $31/host/month for APM. Reasonable for 5-15 hosts.

### Sentry
**Why Sentry (in addition to Datadog):**
- **Error tracking with code context:** Sentry shows the exact line of code, variable values, and stack trace when an error occurs. Datadog logs show the error message.
- **Release tracking:** See which deployment introduced new errors.
- **User impact:** "This error affected 47 students during the Biology exam."
- **Source maps:** JavaScript error traces map to TypeScript source, not compiled output.
- **Cost:** Free for 5,000 errors/month. $26/month for 50,000 errors.

---

# PART G: COMPLETE IMPLEMENTATION PLAN

## PHASE 0: PRE-BUILD (Weeks 1-4)

### Legal (Steps 0.1-0.7)

**0.1 Register company as LLC or S.A.E. in Egypt**
- Duration: 2-4 weeks
- Requirements: National ID copies, address proof, minimum 50,000 EGP capital
- Process: GAFI (General Authority for Free Zones and Investment) one-stop shop
- Output: Commercial Registration Certificate, Tax Card
- Cost: ~15,000 EGP (registration + lawyer fees)
- Owner: Ahmed

**0.2 Open corporate bank account**
- Duration: 1-2 weeks
- Requirements: Commercial Registration Certificate, company stamp, authorized signatories
- Recommended banks: CIB (best for tech startups) or HSBC Egypt (international transfers)
- Output: Corporate bank account with online banking
- Owner: Ahmed

**0.3 Draft co-founder agreement**
- Duration: 1 week
- Hire a tech lawyer experienced in Egyptian startup law
- Cover: equity split, roles and responsibilities, vesting schedule, IP assignment, decision-making process, exit provisions, deadlock resolution
- Output: Signed co-founder agreement
- Cost: ~10,000-20,000 EGP (lawyer fees)
- Owner: Ahmed + co-founder

**0.4 Define equity structure**
- Duration: 1 week (parallel with 0.3)
- Suggested split: 60/40 (Ahmed as CEO with business/domain expertise, co-founder as CTO with technical expertise)
- Vesting: 4-year vesting with 1-year cliff
- ESOP pool: Reserve 10-15% for future employee options
- Output: Equity structure documented in co-founder agreement
- Owner: Ahmed + co-founder

**0.5 Legal consultation for EdTech compliance**
- Duration: 1 week
- Consult with education law specialist on: Egyptian Data Protection Law (Law 151/2020), student data handling requirements, parental consent for minors, cross-border data transfer rules
- FERPA equivalent: Egypt does not have an exact FERPA equivalent; Law 151/2020 covers personal data protection broadly
- Output: Compliance checklist and policy templates
- Cost: ~5,000-10,000 EGP
- Owner: Ahmed

**0.6 Trademark ExamGenius**
- Duration: 2-4 weeks
- File with EGIPO (Egyptian Intellectual Property Office)
- Classes: 9 (software), 41 (education services), 42 (SaaS)
- Conduct trademark search before filing
- Output: Trademark application filed, receipt number
- Cost: ~3,000-5,000 EGP per class
- Owner: Ahmed

**0.7 Get tax ID and VAT registration**
- Duration: 1 week
- Egyptian Tax Authority registration
- VAT registration (mandatory if revenue > 500,000 EGP/year)
- E-invoice system registration (mandatory in Egypt since 2023)
- Output: Tax ID number, VAT registration certificate
- Owner: Ahmed

### Technology (Steps 0.8-0.17)

**0.8 Create GitHub organization**
- Duration: 1 day
- Create organization: ExamGenius-Platform
- Set up teams: Core, Frontend, Backend, AI, DevOps
- Configure org-level settings: branch protection, required reviews, signed commits
- Owner: CTO

**0.9 Create repositories**
- Duration: 2 days
- Repositories:
  - `examgenius-frontend` (Next.js + React + TypeScript)
  - `examgenius-api` (Node.js + Express + TypeScript)
  - `examgenius-ai` (Python + FastAPI)
  - `examgenius-infra` (Terraform + Docker configs)
- Each repo initialized with: README, .gitignore, .editorconfig, LICENSE (proprietary), CONTRIBUTING.md
- Branch strategy: main (production), develop (staging), feature/* (features)
- Owner: CTO

**0.10 Set up GitHub Actions CI/CD**
- Duration: 3 days
- Pipeline stages per repo:
  1. **Lint:** ESLint (TS), Ruff (Python), Prettier
  2. **Test:** Unit tests (Jest/Vitest/pytest), integration tests
  3. **Build:** Docker image build and push to ECR
  4. **Deploy:** Deploy to staging (auto on develop merge), production (manual approval on main merge)
- Environment secrets: AWS credentials, database URLs, API keys
- Owner: CTO/DevOps

**0.11 Create AWS account and infrastructure**
- Duration: 1 day
- AWS Organization with separate accounts: Production, Staging, Shared Services
- VPC setup: 3 AZs, public/private subnets, NAT gateway
- IAM roles: Admin, Developer, CI/CD, Application
- Enable CloudTrail, GuardDuty, AWS Config
- Region: me-south-1 (Bahrain)
- Owner: CTO

**0.12 Design PostgreSQL schema**
- Duration: 1 week
- Design all 16 tables (as specified in Part D)
- Write migration files using Prisma
- Seed data: sample school, users, 100 sample questions
- Performance: Add indexes as specified
- Document: ER diagram using dbdiagram.io
- Owner: CTO

**0.13 Set up RDS PostgreSQL instances**
- Duration: 2 days
- Staging: db.t3.medium (2 vCPU, 4GB RAM), 50GB storage
- Production: db.r6g.large (2 vCPU, 16GB RAM), 100GB storage, Multi-AZ
- Configuration: max_connections=200, shared_buffers=4GB, WAL archiving to S3
- Backups: Automated daily snapshots, 30-day retention
- Owner: CTO/DevOps

**0.14 Configure Datadog and Sentry**
- Duration: 2 days
- Datadog: Install agent on ECS tasks, configure APM for Node.js and Python, set up log collection, create initial dashboards (API latency, error rates, database query times)
- Sentry: Create projects for frontend, API, AI service; configure source maps upload in CI/CD; set up Slack alert channel
- Owner: CTO

**0.15 Purchase domain and SSL**
- Duration: 1 day
- Domain: examgenius.io (or .com if available)
- DNS: Route 53 hosted zone
- SSL: ACM certificate with auto-renewal
- Subdomains: api.examgenius.io, app.examgenius.io, ai.examgenius.io, admin.examgenius.io
- Owner: CTO

**0.16 Get AI API keys**
- Duration: 1 day
- OpenAI: Organization account, API key, set billing limit ($500/month initially)
- Anthropic: API key for Claude as fallback
- Store in AWS Secrets Manager
- Owner: CTO

**0.17 Validate AI question quality**
- Duration: 1 week
- Run 20 test prompts across 5 subjects (Biology, Chemistry, Physics, Math, English)
- Generate 10 questions per prompt (200 total)
- Evaluate: accuracy, curriculum alignment, difficulty appropriateness, language quality
- Document: prompt engineering findings, best-performing prompt patterns
- Target: 70%+ of generated questions rated "usable" by test reviewers
- Owner: CTO

### Team (Steps 0.18-0.22)

**0.18 Define job descriptions**
- Duration: 1 week
- CTO: Node.js, PostgreSQL, AWS, team lead experience, 8+ years. Salary: 30,000 EGP/month + equity
- Full-Stack Developer #1: React, Node.js, TypeScript, 4+ years. Salary: 20,000 EGP/month
- Owner: Ahmed

**0.19 Post job listings**
- Duration: Week 1
- Platforms: LinkedIn, Wuzzuf, Bayt, AngelList
- Targeting: Egypt-based developers, remote-friendly
- Referral bonus: 5,000 EGP for successful referrals
- Owner: Ahmed

**0.20 Interview and hire CTO**
- Duration: Weeks 2-4
- Process: Resume screen -> Technical assessment (take-home) -> Technical interview -> Culture fit -> Offer
- Must-have: Node.js production experience, PostgreSQL, AWS, led team of 3+
- Nice-to-have: EdTech experience, AI/ML familiarity, Arabic speaker
- Owner: Ahmed

**0.21 Interview and hire Full-Stack Developer #1**
- Duration: Weeks 3-4
- Process: Resume screen -> Coding challenge -> Technical interview -> Offer
- Must-have: React, Node.js, TypeScript, Git, 4+ years experience
- Owner: Ahmed + CTO

**0.22 Set up development environment documentation**
- Duration: Week 4
- README.md for each repo with: prerequisites, local setup steps, environment variables, running tests, coding standards
- Development tools: VSCode settings, recommended extensions, ESLint/Prettier config
- Docker Compose for local development (PostgreSQL, Redis, Elasticsearch)
- Owner: CTO

**Success Criteria Phase 0:** Company registered, 2 devs hired, GitHub repos created with CI/CD, AWS account live with VPC and RDS, AI prompts validated with 70%+ quality rate.

---

## PHASE 1: MVP (Months 1-4)

### Curriculum Ingestion (Steps 1.1-1.7) - Weeks 1-6

**1.1 Build document upload API** - 1 week
- Owner: Backend Dev | Deps: 0.12
- POST /api/curriculum/upload endpoint
- Multer middleware for multipart file handling
- Validate: file type (pdf, docx, pptx, txt), size < 50MB
- Generate unique S3 key: `{school_id}/curricula/{curriculum_id}/{uuid}.{ext}`
- Upload to S3 with server-side encryption (AES-256)
- Create curriculum_documents record with status='pending'
- Enqueue processing job in BullMQ
- Success: File stored in S3, DB record created, job queued

**1.2 PDF text extraction service** - 1 week
- Owner: Backend Dev | Deps: 1.1
- Python FastAPI endpoint: POST /ai/extract/pdf
- Use PyMuPDF (fitz) for text extraction
- Preserve page numbers and section structure
- Handle multi-column layouts with column detection heuristic
- Extract embedded images, save to S3, replace with reference tags
- Handle password-protected PDFs (reject with clear error)
- OCR fallback for scanned pages using Tesseract
- Success: >95% text accuracy on 20 sample IGCSE past papers

**1.3 DOCX/PPTX parsing** - 1 week
- Owner: Backend Dev | Deps: 1.2
- python-docx for DOCX: extract text with heading hierarchy (H1-H6)
- python-pptx for PPTX: extract text from slides + speaker notes
- Preserve: bold, italic, lists, tables
- Extract embedded images
- Success: All heading levels correctly identified in 10 test documents

**1.4 Image and equation handling** - 1 week
- Owner: Backend Dev | Deps: 1.3
- Extract images from documents, save to S3 with CDN URL
- Insert image reference markers in extracted text
- Detect LaTeX-style equations: inline ($...$) and display ($$...$$)
- Detect chemical equations and formulas
- Flag math/science-heavy sections for specialized AI processing
- Success: Chemistry and Physics IGCSE papers extracted with diagrams preserved as image references

**1.5 Curriculum storage and library API** - 1 week
- Owner: Backend Dev | Deps: 1.4
- Store processed text in curriculum_documents.extracted_text
- Build curriculum_topics from AI extraction (step 1.7)
- API endpoints:
  - GET /api/curriculum (list with pagination, filters)
  - GET /api/curriculum/:id (detail with documents and topics)
  - PUT /api/curriculum/:id (update metadata)
  - DELETE /api/curriculum/:id (soft delete)
- Success: Curriculum searchable by subject, grade, standard

**1.6 Curriculum library UI** - 2 weeks
- Owner: Frontend Dev | Deps: 1.5
- Upload page: drag-and-drop zone, file type indicators, progress bar, batch upload support
- Library view: card grid layout with subject icons, grade badges, standard labels, search bar, filter sidebar
- Detail view: curriculum metadata, document list, extracted topic tree visualization, processing status
- Responsive design: works on tablet (teachers use iPads)
- Success: Teacher can upload IGCSE Biology syllabus PDF, see it processing, and view extracted topics

**1.7 AI topic extraction and curriculum map** - 2 weeks
- Owner: Backend Dev | Deps: 1.4 + 0.16
- Send extracted text to OpenAI with structured extraction prompt
- Extract: subject, grade level, learning objectives, topics (hierarchical), subtopics, key terms
- Store in curricula.topics_json as hierarchical JSON
- Generate curriculum map data for frontend tree visualization
- Handle chunking: split long documents into 4000-token chunks with overlap
- Success: IGCSE Biology syllabus correctly identifies all 12 topic areas with subtopics

### AI Question Generation (Steps 1.8-1.13) - Weeks 3-8

**1.8 OpenAI API integration** - 1 week
- Owner: Backend Dev | Deps: 0.16
- Python FastAPI AI service with endpoints for generation and scoring
- OpenAI client with: exponential backoff retry (3 attempts), rate limiting (60 RPM), timeout (30s)
- Anthropic client as automatic fallback on OpenAI failure
- Request/response logging for debugging and cost tracking
- Cost tracking: log model, tokens in, tokens out, estimated cost per request
- Success: Service handles 50 concurrent requests with proper queuing

**1.9 Question generation prompt engineering** - 2 weeks
- Owner: CTO + Backend Dev | Deps: 1.8
- Create prompt templates for each of 9 question types (detailed above in 5.2.1)
- Few-shot examples: 3 high-quality example questions per type
- Output format: strict JSON schema with validation
- Prompt versioning: store version in each generated question for A/B testing
- Temperature testing: evaluate quality at 0.3, 0.5, 0.7, 0.9
- Test: Generate 50 questions per type (450 total), have 3 teachers rate quality
- Success: MCQ questions rated >70/100 quality by majority of test teachers

**1.10 Implement all 9 question types** - 2 weeks
- Owner: Backend Dev | Deps: 1.9
- Implement question type schemas, validation, storage, and rendering for all 9 types
- Each type has: input schema, generation prompt, output parser, database schema, frontend renderer
- API: POST /api/questions/generate with type-specific parameters
- Batch generation: generate multiple types in one request
- Success: All 9 types generate correctly with valid JSON output

**1.11 Bloom Taxonomy alignment** - 1 week
- Owner: Backend Dev | Deps: 1.10
- Add bloom_level parameter (1-6) to generation request
- Modify prompts to include Bloom-specific verb lists and instructions
- Exam blueprint feature: specify Bloom distribution (e.g., 30% L1, 40% L2, 30% L3)
- System validates generated questions match requested Bloom level
- Success: Exam with specified Bloom distribution generates questions at correct levels

**1.12 Quality scoring implementation** - 1 week
- Owner: Backend Dev | Deps: 1.11
- Implement 5-dimension scoring algorithm (as specified in 5.2.1)
- Grammar check: LanguageTool API integration
- Distractor analysis: semantic similarity between options
- Curriculum alignment: cosine similarity between question and source text
- Difficulty estimation: vocabulary complexity, Bloom level, concept count
- Bias check: keyword list for gender, cultural, religious bias indicators
- Auto-flag below 60, auto-approve above 80
- Success: Quality scores correlate with teacher ratings (>0.7 Pearson correlation)

**1.13 Training data collection workflow** - 2 weeks
- Owner: Backend Dev | Deps: 1.12
- All AI-generated questions enter review queue with status='IN_REVIEW'
- Teacher review UI: display question with quality score, curriculum context
- Actions: Accept (store as-is), Edit (inline editor, store both versions), Reject (mandatory reason)
- Track metrics: acceptance rate, edit rate, rejection rate, avg quality score by type
- Store accepted/edited questions in training_data table
- Dashboard showing progress toward 5,000-question target
- Success: Review workflow functional, metrics tracked, collection pipeline active

### Question Bank and Exam Builder (Steps 1.14-1.20) - Weeks 5-10

**1.14 Question bank database and API** - 1 week
- Owner: Backend Dev | Deps: 0.12
- Full CRUD API for questions with all fields
- Search API with 12+ filter parameters: type, difficulty, bloom_level, subject, grade, topic, status, tags, created_by, quality_score range, date range, free text
- Cursor-based pagination for large result sets
- Elasticsearch indexing for full-text search
- Bulk operations: bulk status update, bulk tag, bulk delete
- Success: Search returns relevant results in <500ms across 10K+ questions

**1.15 Question bank UI** - 2 weeks
- Owner: Frontend Dev | Deps: 1.14
- List view with multi-filter sidebar, search bar, bulk selection
- Question preview: expandable card showing full question with answer
- Create/edit form: type-specific fields, rich text editor, LaTeX preview
- Import wizard: CSV/Excel upload with column mapping and preview
- Review interface: side-by-side view of question and curriculum context
- Success: Teacher can search, filter, create, edit, and review questions efficiently

**1.16 Exam builder API** - 1 week
- Owner: Backend Dev | Deps: 1.14
- CRUD for exams with sections and questions
- Add questions from bank with point assignment
- Validation endpoint: check all rules before publishing
- Clone exam: deep copy with new ID
- PDF export: generate formatted PDF via Puppeteer
- Success: Complete exam CRUD with validation

**1.17 Exam builder UI** - 2 weeks
- Owner: Frontend Dev | Deps: 1.16
- Drag-and-drop section and question ordering
- Question picker: search question bank inline, add to exam
- Section configuration: title, time limit, instructions
- Settings panel: randomization, access control, scheduling
- Preview mode: see exam as student would see it
- Validation feedback: errors and warnings before publishing
- Success: Teacher can build a complete exam from question bank in under 10 minutes

**1.18 Question randomization engine** - 1 week
- Owner: Backend Dev | Deps: 1.16
- Shuffle questions within sections (seed-based for reproducibility)
- Shuffle MCQ options (maintain correct answer tracking)
- Question pooling: randomly select N questions from pool of M
- Variant generation: create 4 exam variants from one template
- Success: Each student gets unique question/option order; correct answer always tracked

**1.19 Exam scheduling and access control** - 1 week
- Owner: Backend Dev | Deps: 1.16
- Schedule exam with start/end time window
- Password protection: hashed password required to start
- IP whitelist: validate student IP against allowed ranges
- Attempt limits: enforce max_attempts per student
- Conflict detection: warn if student has overlapping exams
- Success: Exam only accessible within configured parameters

**1.20 Basic exam settings UI** - 1 week
- Owner: Frontend Dev | Deps: 1.19
- Scheduling calendar picker
- Access control configuration panel
- Randomization toggles
- Attempt limit selector
- Success: All exam settings configurable through UI

### Student Portal (Steps 1.21-1.26) - Weeks 7-10

**1.21 Student authentication** - 1 week
- Owner: Backend Dev | Deps: 0.12
- Auth0 integration for student login
- Google OAuth for schools using Google Workspace
- Student self-registration with school code
- Role-based redirect after login
- Success: Students can log in via email/password or Google SSO

**1.22 Exam taking interface** - 2 weeks
- Owner: Frontend Dev | Deps: 1.21 + 1.16
- Clean, distraction-free exam UI
- Question navigation panel (sidebar with question numbers)
- Question rendering for all 9 types with answer input components
- Flag question for review feature
- Progress indicator: answered/total questions
- Success: Student can view and answer all 9 question types

**1.23 Exam timer and auto-save** - 1 week
- Owner: Frontend Dev + Backend Dev | Deps: 1.22
- Countdown timer with visual warning at 5 min and 1 min remaining
- Section timers (if per-section limits set)
- Auto-save: POST response every 30 seconds or on answer change
- Connection loss handling: queue responses locally, sync on reconnect
- Auto-submit when time expires
- Success: No student loses work due to connection issues

**1.24 Exam submission flow** - 1 week
- Owner: Backend Dev | Deps: 1.23
- Pre-submission review: show unanswered questions
- Confirmation dialog before final submission
- Lock session after submission (no modifications)
- Trigger auto-grading for objective questions
- Calculate and store scores
- Success: Smooth submission flow with immediate auto-grading

**1.25 Results display** - 1 week
- Owner: Frontend Dev | Deps: 1.24
- Score summary: total score, percentage, pass/fail
- Section breakdown: score per section
- Question review: show each question with student answer, correct answer, and explanation (if enabled)
- Score distribution chart (anonymous class comparison)
- Success: Student sees comprehensive results immediately after auto-grading

**1.26 Student dashboard** - 1 week
- Owner: Frontend Dev | Deps: 1.25
- Upcoming exams with countdown timers
- Recent results with quick score view
- Performance summary chart (last 5 exams)
- Notifications panel
- Success: Student has clear overview of exam schedule and performance

### Teacher Portal (Steps 1.27-1.30) - Weeks 9-12

**1.27 Teacher dashboard** - 1 week
- Owner: Frontend Dev | Deps: 1.17 + 1.25
- Quick stats: exams created, pending grading, average class scores
- Recent activity feed
- Upcoming exam schedule
- Quick action buttons: create exam, generate questions, grade responses
- Success: Teacher has actionable dashboard on login

**1.28 Manual grading interface** - 2 weeks
- Owner: Frontend Dev + Backend Dev | Deps: 1.24
- Grading queue: list of ungraded essay/short answer responses
- Inline rubric display alongside student response
- Score assignment per rubric criterion
- Text annotation: highlight, comment, strikethrough
- Keyboard shortcuts for efficient grading
- Batch mode: grade same question across all students
- AI suggestion: show AI-recommended score (teacher can accept/modify)
- Success: Teacher can grade 30 essays in under 1 hour with rubric

**1.29 Teacher curriculum management** - 1 week
- Owner: Frontend Dev | Deps: 1.6
- Upload curricula from teacher portal
- View own curricula and shared curricula
- Manage sharing settings
- Success: Teachers manage curricula without admin involvement

**1.30 Question bank management** - 1 week
- Owner: Frontend Dev | Deps: 1.15
- Access question bank from teacher portal
- Create, edit, import questions
- Submit questions for review
- View question quality metrics
- Success: Teachers actively contribute to question bank

### Testing and Pilot (Steps 1.31-1.35) - Weeks 11-16

**1.31 Recruit 5 pilot schools** - 2 weeks
- Owner: Ahmed (CEO)
- Target: IGCSE schools in Cairo with 500+ students
- Approach: Personal network, LinkedIn outreach, school visits
- Offer: 1 semester free, dedicated support, input on product roadmap
- Success: 5 schools signed pilot agreements

**1.32 User Acceptance Testing (UAT)** - 2 weeks
- Owner: Full team
- Create test plans for each user role
- Conduct testing with real teachers and students from pilot schools
- Track bugs in GitHub Issues with severity labels
- Fix all critical and high severity bugs
- Success: Zero critical bugs, <5 high severity bugs remaining

**1.33 Performance testing** - 1 week
- Owner: CTO
- Load test with k6: simulate 500 concurrent students taking exam
- Stress test: find breaking point for concurrent sessions
- API latency benchmarking under load
- Database query optimization based on slow query logs
- Success: 500 concurrent sessions with <2s page load

**1.34 Feedback collection and iteration** - 2 weeks
- Owner: Full team
- In-app feedback widget for pilot school users
- Weekly check-in calls with pilot school contacts
- Prioritize feedback into: MVP fix, V1.0, V1.5, backlog
- Implement top 10 feedback items
- Success: Pilot schools report 4.0+ satisfaction score

**1.35 Pilot school case studies** - 1 week
- Owner: Ahmed
- Document each pilot school's experience with metrics
- Before/after comparison: time spent on exams, grading turnaround
- Teacher and admin testimonials
- Success: 3 publishable case studies for sales materials

**MVP Success Metrics:**
- 90% question generation success rate
- 3 pilot schools actively using platform
- Teacher can upload curriculum and generate 50-question exam in under 5 minutes
- Students can take exam and see results immediately (auto-graded)
- <2s page load under 500 concurrent users
- Quality score average >70 for AI-generated questions

---

## PHASE 2: V1.0 (Months 5-8)

**2.1 Advanced question bank features** - 2 weeks
- Duplicate detection with similarity scoring
- Question versioning with diff view
- Collaborative editing with conflict resolution
- Usage analytics per question

**2.2 Advanced search and filtering** - 1 week
- Elasticsearch integration for full-text search
- Faceted search with result counts
- Saved search filters
- Related questions suggestion

**2.3 Auto-grading engine for all objective types** - 2 weeks
- MCQ: exact match with option mapping
- True/False: exact match
- Fill-in-blank: exact match + Levenshtein distance fuzzy matching
- Matching: pair-by-pair comparison with partial credit
- Ordering: Kendall tau distance for partial credit
- Numeric answers: configurable epsilon tolerance

**2.4 Partial credit system** - 1 week
- Per-question partial credit toggle
- MCQ multiple-answer: proportional scoring
- Matching: per-pair credit
- Configurable scoring rules per exam

**2.5 AI-assisted essay grading** - 2 weeks
- Send essay + rubric to AI for suggested score
- Provide score per rubric criterion with justification
- Teacher review and override UI
- Track AI vs teacher score correlation for model improvement

**2.6 Class analytics dashboard** - 2 weeks
- Mean, median, standard deviation, pass rate
- Score distribution histogram
- Question difficulty and discrimination indices
- Bloom level performance breakdown
- Topic performance heatmap
- Export to PDF/Excel

**2.7 Student analytics** - 1 week
- Individual performance trends over time
- Strengths/weaknesses by topic radar chart
- Bloom level performance profile
- Comparison to class average (percentile)
- AI-generated study recommendations

**2.8 Comparative analytics** - 1 week
- Class vs school comparison
- Current exam vs historical comparison
- Year-over-year trend analysis
- Teacher effectiveness metrics (admin only)

**2.9 Google SSO integration** - 1 week
- Auth0 Google social connection
- Auto-provision users from Google Workspace directory
- Role mapping from Google groups

**2.10 Microsoft Azure AD SSO** - 1 week
- Auth0 Microsoft enterprise connection
- Tenant-specific configuration per school
- Auto-provision users from Azure AD

**2.11 Student portal enhancements** - 2 weeks
- Practice exam mode with instant feedback
- Past exam review with explanations
- Performance dashboard with charts
- Study recommendations by weak topics
- Notification preferences

**2.12 Teacher portal enhancements** - 2 weeks
- Exam monitoring dashboard (live view of ongoing exams)
- Class management tools
- Announcement system
- Enhanced grading workflow
- Question quality insights

**2.13 Parent portal (basic)** - 2 weeks
- Parent registration with student linking
- View child's exam results and scores
- Performance trend charts
- Upcoming exam calendar
- Push notifications for grade releases

**2.14 Admin dashboard (complete)** - 2 weeks
- User management with bulk operations
- Subscription and billing view
- School-wide analytics
- Audit log viewer with filters
- System settings configuration

**2.15 Email notification system** - 1 week
- SendGrid integration
- Templates: exam reminders, grade releases, account notifications
- Configurable notification preferences per user
- Digest mode: daily summary instead of individual emails

**2.16 PDF report generation** - 1 week
- Student report cards (PDF)
- Class performance reports
- Exam summary reports
- Scheduled generation and distribution

**2.17 Exam PDF export enhancement** - 1 week
- Professional formatting with school branding
- Answer key with explanations
- Bubble sheet generation for OMR
- Multiple variants export

**2.18 Question import from Excel/CSV** - 1 week
- Template download
- Column mapping wizard
- Validation with row-level error reporting
- Preview before commit
- Duplicate detection during import

**2.19 Basic browser lockdown** - 1 week
- Fullscreen enforcement
- Tab switch detection and logging
- Copy/paste disabled
- Basic violation tracking and reporting

**2.20 Stripe payment integration** - 2 weeks
- School subscription management
- Payment method capture
- Invoice generation
- Usage-based billing calculation
- Webhook handling for payment events

**2.21 API documentation** - 1 week
- OpenAPI 3.0 specification
- Swagger UI at /api/docs
- Authentication guide
- Rate limiting documentation
- Webhook documentation

**2.22 Internationalization framework** - 1 week
- i18next integration
- English and Arabic translation files
- RTL layout support
- Date/number/currency formatting per locale

**2.23 Arabic RTL support** - 2 weeks
- Full Arabic translation of UI
- RTL layout for all components
- Arabic question generation (AI)
- Bidirectional text rendering in exams
- Arabic PDF generation

**2.24 Performance optimization** - 1 week
- Database query optimization
- Redis caching implementation
- CDN configuration for assets
- Image optimization pipeline
- Lazy loading for heavy components

**2.25 Security hardening** - 1 week
- Penetration testing (internal)
- OWASP Top 10 review
- Content Security Policy headers
- Rate limiting per endpoint
- Input sanitization audit

**2.26 Sales materials and website** - 2 weeks
- Marketing website with pricing, features, case studies
- Demo video (2-3 minutes)
- Sales deck (15 slides)
- ROI calculator for schools
- Free trial signup flow

**V1.0 Success Metrics:**
- 15 paying schools
- 8,000 students on platform
- $280K ARR
- Auto-grading accuracy >95% for objective questions
- Arabic RTL fully functional
- NPS 40+

---

## PHASE 3: V1.5 (Months 9-12)

**3.1 Advanced browser lockdown** - 2 weeks
- Keyboard shortcut blocking (all common shortcuts)
- Right-click context menu suppression
- Developer tools detection
- Multiple monitor detection
- Virtual machine detection
- Print screen blocking (best effort)
- Warning escalation system (4 levels)

**3.2 Webcam proctoring - basic** - 2 weeks
- Camera permission request and setup
- Identity photo capture at exam start
- Periodic photo capture (configurable interval)
- Photo storage in S3 with encryption
- Photo review interface for proctors

**3.3 Webcam proctoring - AI** - 3 weeks
- Face detection using MTCNN
- Face count monitoring (alert on multiple faces)
- Face recognition for identity verification (compare to enrollment photo)
- Head pose estimation (detect looking away)
- Processing: on-device (WebRTC) + server-side validation

**3.4 AI anomaly detection** - 2 weeks
- Phone/device detection using YOLO object detection
- Audio analysis for background speech
- Behavioral pattern analysis (unusual response timing)
- Anomaly scoring and alert generation
- Proctor dashboard with real-time alerts

**3.5 Integrity score calculation** - 1 week
- Implement scoring algorithm (as specified in 5.5.5)
- Weight configuration per school
- Score display on proctor dashboard and grade report
- Flag sessions below threshold for review

**3.6 Proctoring dashboard** - 2 weeks
- Live view of all active proctored sessions
- Real-time alerts via WebSocket
- Student webcam feed thumbnails (optional)
- One-click actions: warn, pause, terminate
- Session timeline: chronological event log with screenshots

**3.7 Plagiarism detection - peer comparison** - 2 weeks
- Compare student responses against all peers in same exam
- Similarity scoring using cosine similarity on TF-IDF vectors
- Highlighted matching segments
- Report generation with evidence

**3.8 Plagiarism detection - internet** - 1 week
- Turnitin API integration (Enterprise tier)
- Or custom web search comparison (Starter/Professional)
- Similarity report with source URLs
- Integration with integrity score

**3.9 PowerSchool SIS integration** - 2 weeks
- REST API connector
- Sync: students, classes, enrollments, teachers
- Grade passback: write ExamGenius grades to PowerSchool
- Scheduled sync (daily) and on-demand
- Conflict resolution rules

**3.10 Skyward SIS integration** - 1 week
- REST API connector
- Same sync capabilities as PowerSchool
- Grade passback support

**3.11 Moodle LTI integration** - 2 weeks
- LTI 1.3 tool provider implementation
- Launch exams from Moodle course page
- Grade passback via LTI Assignment and Grade Services
- Deep linking for specific exams

**3.12 Canvas LTI integration** - 1 week
- LTI 1.3 tool provider (shared framework with Moodle)
- Canvas-specific API integration for grade passback
- Assignment sync

**3.13 Google Classroom integration** - 1 week
- Google Classroom API integration
- Create assignments linked to ExamGenius exams
- Grade passback to Google Classroom gradebook
- Roster sync

**3.14 Microsoft Teams Education integration** - 1 week
- Microsoft Graph API integration
- Create assignments in Teams
- Grade passback
- SSO deep linking

**3.15 SAML 2.0 SSO** - 1 week
- Generic SAML 2.0 identity provider support
- Configurable attribute mapping
- Multi-tenant SAML configuration
- Just-in-time user provisioning

**3.16 Advanced reporting engine** - 2 weeks
- Custom report builder (select metrics, filters, groupings)
- Scheduled reports (daily, weekly, monthly, term-end)
- Email distribution lists
- Export: PDF, Excel, CSV
- Report templates library

**3.17 Student accommodations** - 1 week
- Per-student extra time settings (25%, 50%, 100%)
- Large font mode
- High contrast mode
- Screen reader optimization
- Separate room/session support

**3.18 Training data collection milestone** - ongoing
- Target: 5,000+ validated questions by Month 12
- Monthly progress tracking
- Quality metrics by subject and type
- Teacher incentive program for reviewers

**3.19 AI model evaluation framework** - 1 week
- Benchmark suite for question quality
- A/B testing framework for prompt versions
- Automated quality scoring on generated batches
- Cost tracking and optimization

**3.20 Prepare fine-tuning dataset** - 2 weeks
- Export training_data table to fine-tuning format
- Data cleaning and deduplication
- Train/validation/test split (80/10/10)
- Format for Llama fine-tuning (instruction format)
- Quality analysis: distribution by type, subject, difficulty, Bloom level

**3.21 Fine-tune Llama 3 8B (initial)** - 2 weeks
- LoRA fine-tuning on 5,000+ questions
- Hyperparameter search: learning rate, rank, alpha
- Evaluation: compare against GPT-4o on benchmark suite
- A/B test: deploy to 10% of generation requests
- Success: Fine-tuned model achieves >85% of GPT-4o quality at 10% cost

**3.22 Mobile-responsive optimization** - 2 weeks
- Responsive design audit and fixes
- Touch-optimized exam-taking interface
- Mobile-friendly teacher grading
- PWA support: offline capability for student dashboard

**3.23 Webhook system** - 1 week
- Webhook registration API for schools
- Events: exam.completed, grade.released, user.created, etc.
- Retry with exponential backoff
- Webhook logs and debugging tools

**3.24 API rate limiting and throttling** - 1 week
- Per-user and per-school rate limits
- Token bucket algorithm via Redis
- Rate limit headers in API responses
- Graceful degradation under load

**3.25 Backup and disaster recovery testing** - 1 week
- Test RDS failover
- Test S3 cross-region replication
- Document and test recovery procedures
- Measure actual RTO and RPO

**3.26 Compliance audit** - 1 week
- Egyptian Data Protection Law review
- Data processing documentation
- Consent flow audit
- Privacy policy and terms of service update

**3.27 Customer success onboarding** - 1 week
- Onboarding checklist and wizard for new schools
- Video tutorials for teachers and admins
- Knowledge base articles
- In-app tooltips and guided tours

**3.28 Sales acceleration** - 2 weeks
- Automated demo environment
- Free trial: 30-day trial with 100-student limit
- Sales pipeline tracking
- Referral program: existing school gets 10% discount for referral

**V1.5 Success Metrics:**
- 30 paying schools
- 18,000 students on platform
- $700K ARR
- Browser lockdown + webcam proctoring functional
- 2+ SIS integrations live
- Fine-tuned Llama model achieving >85% of GPT-4o quality
- 5,000 validated questions in training dataset

---

## PHASE 4: V2.0 (Year 2, Months 13-24)

**4.1 Advanced analytics platform** - 4 weeks
- Predictive analytics: identify at-risk students based on performance trends
- Curriculum gap analysis: identify topics with consistently low scores across schools
- Teacher effectiveness insights (anonymized, admin only)
- Custom dashboard builder
- Data warehouse (AWS Redshift) for heavy analytical queries

**4.2 iOS mobile app** - 6 weeks
- React Native for cross-platform development
- Student exam-taking with offline support
- Push notifications for exams and grades
- Biometric authentication (Face ID, fingerprint)
- Camera integration for proctoring

**4.3 Android mobile app** - 4 weeks (parallel with iOS, shared React Native codebase)
- Same feature set as iOS
- Optimized for common Android devices used in Egypt
- Play Store submission and review

**4.4 API marketplace (v1)** - 4 weeks
- Public API with API key authentication
- Developer portal with documentation
- Usage-based pricing for API access
- Sandbox environment for testing
- SDK packages: JavaScript, Python

**4.5 Full Llama 13B deployment** - 3 weeks
- Upgrade from 8B to 13B model with larger training set (10,000+ questions)
- Deploy on AWS p4d instance or dedicated GPU server
- vLLM serving for high-throughput inference
- A/B testing against GPT-4o
- Cost tracking: target <$0.005 per question

**4.6 AI question improvement engine** - 2 weeks
- AI suggests improvements to existing questions based on discrimination index
- Auto-rewrite poor-quality distractors
- Difficulty recalibration based on actual student performance data
- Automatic Bloom level verification

**4.7 Adaptive testing (basic)** - 4 weeks
- Computer Adaptive Testing (CAT) engine
- Item Response Theory (IRT) model calibration
- Dynamic difficulty adjustment based on student responses
- Ability estimation with confidence intervals
- Practice exam mode with adaptive difficulty

**4.8 White-label foundation** - 3 weeks
- Customizable branding: logo, colors, fonts, domain
- Custom email templates
- White-label API documentation
- Multi-tenant configuration management

**4.9 Advanced exam types** - 2 weeks
- Group exams: collaborative assessment for teams
- Take-home exams with extended deadlines
- Portfolio assessment: submit multiple artifacts over time
- Oral exam scheduling and rubric support (manual grading only)

**4.10 Gamification for students** - 2 weeks
- Achievement badges for performance milestones
- Streak tracking for consistent study
- Leaderboards (optional, per teacher)
- XP system for practice exam completion

**4.11 Advanced parent portal** - 2 weeks
- Detailed per-subject performance reports
- Teacher communication channel (read-only messages)
- Study resource recommendations
- Multi-language support (Arabic, English, French)
- Calendar sync (Google Calendar, iCal)

**4.12 Infinite Campus SIS integration** - 1 week
- REST API connector
- Student and enrollment sync
- Grade passback

**4.13 Advanced PDF generation** - 2 weeks
- Custom exam templates (school can upload)
- OMR bubble sheet generation
- Accommodated versions (large print, extra spacing)
- Watermarking with student information
- Batch generation for entire class

**4.14 Data export and portability** - 1 week
- Full data export: questions, exams, results in JSON/CSV
- School data deletion request processing
- Data portability compliance (right to data portability)

**4.15 Multi-language question generation** - 2 weeks
- Arabic question generation with AI
- French question generation (for French system schools)
- Language-specific quality scoring
- Bilingual exam support (questions in two languages)

**4.16 SOC 2 Type II preparation** - 4 weeks
- Security policies and procedures documentation
- Access control reviews
- Change management process formalization
- Incident response plan
- Evidence collection automation
- Engage SOC 2 auditor

**4.17 Infrastructure scaling** - 2 weeks
- Database read replicas for analytics
- Elasticsearch cluster scaling
- CDN optimization
- Multi-region failover testing
- Cost optimization review

**4.18 Team scaling** - ongoing
- Hire: Backend Developer #2, Mobile Developer, Marketing Manager, Account Manager
- Engineering team processes: sprint planning, code reviews, on-call rotation
- Customer success team: onboarding specialist, technical support

**V2.0 Success Metrics:**
- 60 paying schools
- 35,000 students
- $1.4M ARR
- Mobile apps on App Store and Play Store
- Proprietary AI model handling 80%+ of generation
- API marketplace with 5+ external consumers
- SOC 2 Type II certification in progress

---

## PHASE 5: V2.5 (Year 3, Months 25-36)

**5.1 AI model improvements** - 4 weeks
- Train on 25,000+ validated questions
- Subject-specific models for STEM vs humanities
- Multi-language training (English + Arabic)
- Question difficulty prediction model
- Automated curriculum alignment verification

**5.2 White-label deployment** - 4 weeks
- Complete white-label solution for education groups
- Dedicated instances for large clients
- Custom feature configurations
- Partner management portal
- Revenue sharing model

**5.3 GCC market expansion - UAE** - 8 weeks
- Legal entity in UAE (DMCC or DIFC)
- Azure UAE North region deployment
- Sales team in Dubai
- Localization for UAE curriculum standards
- 5 pilot schools in Dubai/Abu Dhabi

**5.4 GCC market expansion - Saudi Arabia** - 6 weeks
- Partnership with local EdTech distributor
- AWS Bahrain region (already deployed)
- Localization for Saudi curriculum standards (IB and national)
- 3 pilot schools in Riyadh/Jeddah

**5.5 GCC market expansion - Qatar/Bahrain/Kuwait/Oman** - 4 weeks
- Partnership-led expansion
- Shared infrastructure (AWS Bahrain)
- Localization per country
- 2 pilot schools per country

**5.6 Advanced proctoring** - 4 weeks
- Screen recording (with consent)
- Keystroke dynamics analysis
- Browser fingerprinting for device verification
- Multi-session comparison for behavior patterns
- Integration with external ID verification services

**5.7 Curriculum publisher partnerships** - ongoing
- Pearson: access to IGCSE content for question generation
- Cambridge Assessment: official past paper integration
- IB Organization: alignment with IB assessment framework
- Revenue sharing or licensing model

**5.8 Advanced analytics and AI insights** - 4 weeks
- Natural language queries: "Show me which Biology topics Grade 10 struggled with this term"
- Automated insight generation
- Predictive model: student performance forecasting
- Curriculum effectiveness scoring
- Benchmarking across schools (anonymized)

**5.9 Enterprise features** - 4 weeks
- Multi-campus management (school groups)
- Centralized question bank across campuses
- Cross-campus analytics and benchmarking
- Enterprise admin portal
- Custom SLA agreements
- Dedicated infrastructure option

**V2.5 Success Metrics:**
- 150 paying schools (Egypt + GCC)
- 90,000 students
- $4.5M ARR
- 3+ GCC markets active
- 3+ white-label deployments
- Gross margin 72%
- Team: 35-45 employees

---

# PART H: FINANCIAL MODEL

## Revenue Projections

### Year 1

| Tier | Schools | Avg Students | Price/Student | Revenue |
|------|---------|-------------|---------------|---------|
| Starter ($30) | 5 | 400 | $30 | $60,000 |
| Professional ($45) | 8 | 600 | $45 | $216,000 |
| Enterprise ($75) | 2 | 800 | $75 | $120,000 |
| Pilot (free) | 5 | 500 | $0 | $0 |
| **Total** | **20** | | | **$396,000** |

*Note: Pilots convert at 60% to paid in Year 2. Conservative estimate uses $280K reflecting ramp-up timing.*

### Year 2

| Tier | Schools | Avg Students | Price/Student | Revenue |
|------|---------|-------------|---------------|---------|
| Starter ($30) | 15 | 400 | $30 | $180,000 |
| Professional ($45) | 30 | 600 | $45 | $810,000 |
| Enterprise ($75) | 15 | 800 | $75 | $900,000 |
| **Total** | **60** | | | **$1,890,000** |

*Conservative adjusted: $1,400,000 accounting for churn and delayed onboarding.*

### Year 3

| Tier | Schools | Avg Students | Price/Student | Revenue |
|------|---------|-------------|---------------|---------|
| Starter ($30) | 25 | 400 | $30 | $300,000 |
| Professional ($45) | 70 | 600 | $45 | $1,890,000 |
| Enterprise ($75) | 55 | 800 | $75 | $3,300,000 |
| **Total** | **150** | | | **$5,490,000** |

*Conservative adjusted: $4,500,000 accounting for GCC ramp-up delays.*

## Cost Breakdown

### Year 1 Costs

| Category | Monthly | Annual |
|----------|---------|--------|
| **Salaries** | | |
| CTO | 30,000 EGP ($600) | $7,200 |
| Full-Stack Dev #1 | 20,000 EGP ($400) | $4,800 |
| Frontend Dev (from Month 2) | 18,000 EGP ($360) | $3,960 |
| DevOps (from Month 3) | 22,000 EGP ($440) | $4,400 |
| Sales Rep (from Month 4) | 15,000 EGP ($300) + commission | $3,600 + $10,000 commission |
| AI/ML Engineer (from Month 6) | 28,000 EGP ($560) | $3,920 |
| Customer Success (from Month 6) | 15,000 EGP ($300) | $2,100 |
| **Subtotal Salaries** | | **$40,000** |
| **Infrastructure** | | |
| AWS (RDS, ECS, S3, etc.) | $2,000 | $24,000 |
| Auth0 | $200 | $2,400 |
| Datadog + Sentry | $300 | $3,600 |
| Domain + SSL | - | $200 |
| SendGrid | $50 | $600 |
| **Subtotal Infra** | | **$30,800** |
| **AI Costs** | | |
| OpenAI API | $1,500 | $18,000 |
| Anthropic API (fallback) | $200 | $2,400 |
| **Subtotal AI** | | **$20,400** |
| **Operations** | | |
| Legal (company, trademark, compliance) | - | $5,000 |
| Office space (co-working) | $300 | $3,600 |
| Marketing | $500 | $6,000 |
| Travel (school visits, conferences) | $500 | $6,000 |
| Insurance | $200 | $2,400 |
| Misc | $300 | $3,600 |
| **Subtotal Ops** | | **$26,600** |
| **TOTAL YEAR 1** | | **$117,800** |

### Year 2 Costs

| Category | Annual |
|----------|--------|
| Salaries (expanded team: 12 people) | $150,000 |
| Infrastructure (scaled) | $72,000 |
| AI (reduced with fine-tuned model) | $15,000 |
| GPU hardware (one-time) | $15,000 |
| Operations | $60,000 |
| Sales and marketing | $50,000 |
| **TOTAL YEAR 2** | **$362,000** |

### Year 3 Costs

| Category | Annual |
|----------|--------|
| Salaries (35 people, incl. GCC) | $500,000 |
| Infrastructure (multi-region) | $150,000 |
| AI (proprietary model, minimal API) | $10,000 |
| Operations | $120,000 |
| Sales and marketing | $150,000 |
| GCC expansion costs | $200,000 |
| **TOTAL YEAR 3** | **$1,130,000** |

## Build Once Savings

| Cost Category | API Only (3 Years) | Build Once (3 Years) |
|--------------|-------------------|---------------------|
| API costs | $450,000 | $35,000 |
| GPU hardware | $0 | $15,000 |
| Training compute | $0 | $5,000 |
| Engineering | $30,000 | $18,000 |
| Inference infra | $0 | $12,000 |
| **Total** | **$450,000** | **$65,000** |
| **Savings** | | **$385,000 (86%)** |

## Profitability

| Metric | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| Revenue | $280,000 | $1,400,000 | $4,500,000 |
| Costs | $117,800 | $362,000 | $1,130,000 |
| Gross Profit | $162,200 | $1,038,000 | $3,370,000 |
| Gross Margin | ~58% | ~74% | ~75% |
| Net Margin (after overhead) | ~45% | ~60% | ~72% |
| Break-even month | - | Month 18 | - |

---

# PART I: RISK REGISTER

| ID | Risk | Likelihood (1-5) | Impact (1-5) | Risk Score | Mitigation |
|----|------|-------------------|--------------|------------|------------|
| R1 | **AI question quality insufficient for formal exams.** Teachers reject >50% of generated questions, undermining core value proposition. | 3 | 5 | 15 | 1. Extensive prompt engineering with teacher feedback loops. 2. Quality scoring gates prevent low-quality questions from reaching users. 3. Teacher review workflow builds trust gradually. 4. Fallback: position as "AI-assisted" not "AI-generated" - teacher always has final approval. |
| R2 | **Slow school adoption.** Schools resistant to change, procurement cycles take 6-12 months, decision makers hard to reach. | 4 | 4 | 16 | 1. Free pilot program removes financial risk for early adopters. 2. Target tech-forward schools (already using Google Workspace/LMS). 3. Champion strategy: win over 1-2 teachers, let them advocate internally. 4. Case studies from pilot schools accelerate trust. 5. Attend GESS and EdTech events. |
| R3 | **Data breach or security incident.** Student PII leaked, exam content compromised, or system hacked during high-stakes exam. | 2 | 5 | 10 | 1. Auth0 for authentication (battle-tested). 2. AES-256 encryption at rest, TLS 1.3 in transit. 3. Annual penetration testing. 4. SOC 2 certification by Year 2. 5. Incident response plan with <1hr notification. 6. Cyber insurance policy. |
| R4 | **OpenAI/Anthropic API dependency.** API pricing increases, rate limits, or service outages disrupt question generation. | 3 | 4 | 12 | 1. Dual-provider strategy (OpenAI primary, Anthropic fallback). 2. Build Once strategy: fine-tuned Llama model by Month 12 reduces API dependency to <20%. 3. Request caching for common question patterns. 4. Graceful degradation: exam builder works without AI generation. |
| R5 | **Co-founder conflict or departure.** Technical co-founder leaves before product achieves product-market fit, taking institutional knowledge. | 2 | 5 | 10 | 1. Vesting with 1-year cliff protects against early departure. 2. Comprehensive documentation and code review practices. 3. No single point of failure: at least 2 engineers familiar with each system. 4. Co-founder agreement covers IP assignment and non-compete. |
| R6 | **Competitor enters market.** International player (Examsoft, ClassMarker) or regional startup targets Egyptian international schools. | 3 | 3 | 9 | 1. First-mover advantage with pilot schools. 2. Egypt-specific features (Arabic, data residency, local curriculum) are hard to replicate. 3. Switching costs increase as schools build question banks. 4. Teacher relationships and school champion network create moat. 5. Build Once AI model is proprietary and trained on Egypt-specific data. |
| R7 | **Proctoring privacy backlash.** Parents or schools object to webcam monitoring, face detection, or student surveillance. | 3 | 3 | 9 | 1. Proctoring is optional and configurable per exam. 2. Explicit consent captured before every proctored session. 3. Data retention policies: photos deleted after 90 days. 4. Transparency: students see what data is collected. 5. No facial recognition database - only session-specific comparison. |
| R8 | **Scaling infrastructure costs exceed projections.** AWS costs spiral as usage grows, especially during peak exam periods. | 2 | 3 | 6 | 1. AWS Reserved Instances and Savings Plans (30-40% savings). 2. Auto-scaling with aggressive scale-down policies. 3. Build Once AI reduces most expensive API costs by 86%. 4. Cost monitoring with Datadog alerts at 80% of budget. 5. Architecture designed for horizontal scaling with cost-effective components. |

---

# PART J: GO-TO-MARKET STRATEGY

## Target School Profile

| Criterion | Ideal Target |
|-----------|-------------|
| Location | Cairo, Alexandria, New Cairo, 6th of October, Sheikh Zayed |
| Curriculum | IGCSE (British), IB, American Diploma |
| Size | 500+ students |
| Tuition | 100,000+ EGP/year (premium tier) |
| Tech maturity | Already using Google Workspace or Microsoft 365 |
| Decision maker | Head of School, VP Academic, IT Director |
| Pain point | Manual exam creation, inconsistent grading, no analytics |

## Top 20 Target Schools (Cairo)

1. British International School in Cairo (BISC)
2. Cairo American College (CAC)
3. Modern English School (MES Cairo)
4. Malvern College Egypt
5. The American International School in Egypt (AISE)
6. New Cairo British International School (NCBIS)
7. Hayah International Academy
8. International School of Choueifat
9. El Alsson School (British & American)
10. Green Heights International School
11. Heritage International School
12. The British International School of Cairo (West)
13. Narmer American College
14. Rajac International School
15. Continental Palace International School
16. Cairo English School (CES)
17. Capital International School
18. Schutz American School (Alexandria)
19. British International School Alexandria
20. Alexandria American International School

## Sales Process (5 Steps)

**Step 1: Outreach (Week 1)**
- LinkedIn connection with Head of School / VP Academic / IT Director
- Personalized message referencing their curriculum and school
- Email with 2-minute explainer video
- Success metric: 20% response rate

**Step 2: Discovery Call (Week 2)**
- 30-minute video call
- Understand: current exam process, pain points, tech stack, decision process
- Qualify: budget, timeline, authority, need (BANT)
- Success metric: 60% proceed to demo

**Step 3: Live Demo (Week 3)**
- 45-minute demo customized to their curriculum
- Show: curriculum upload, AI generation, exam builder, student experience, analytics
- Use their actual curriculum content (with permission) for wow factor
- Include teacher participant from their school if possible
- Success metric: 50% proceed to pilot

**Step 4: Pilot (Weeks 4-12)**
- 1 semester free pilot with 2-3 teachers and 1-2 classes
- Dedicated onboarding support
- Weekly check-in calls
- Success metric: 70% of pilots convert to paid

**Step 5: Contract (Week 13)**
- Annual subscription contract
- Pilot school discount: 50% off Year 1
- Net 30 payment terms
- Implementation support included

## Pilot Terms

- **Duration:** 1 semester (4-5 months)
- **Scope:** Up to 3 teachers, 200 students, 1 subject
- **Support:** Dedicated account manager, weekly calls, on-site training (1 day)
- **Data:** School keeps all generated questions and exam data after pilot
- **Conversion incentive:** 50% discount on Year 1 subscription if signed within 30 days of pilot end
- **Success criteria:** Defined upfront with school (e.g., teacher time saved, student satisfaction, exam completion rate)

## Key Events and Conferences

| Event | Timing | Location | Purpose |
|-------|--------|----------|---------|
| GESS Education Middle East | Feb/Mar | Dubai | Networking, lead generation, brand awareness |
| EdTech Egypt Summit | Oct/Nov | Cairo | Local market, school partnerships |
| BETT Show | Jan | London | International exposure, curriculum publisher meetings |
| IB Global Conference | Jul | Various | IB school targeting |
| NESA Conference | Mar | Various | Regional school network |

## Partner Strategy

### Curriculum Publishers
- **Pearson:** Content licensing for IGCSE question generation training data
- **Cambridge Assessment:** Official past paper integration, quality endorsement
- **IB Organization:** Alignment certification with IB assessment framework
- **McGraw-Hill:** AP curriculum content access

### Technology Partners
- **Google for Education:** Google Classroom integration, referral partnership
- **Microsoft Education:** Teams integration, Azure AD SSO, co-marketing
- **AWS EdStart:** Startup credits, technical mentorship, co-marketing

### Channel Partners
- **Education consultancies:** Commission-based referrals (15% Year 1 revenue)
- **IT integrators:** Schools' existing IT vendors can resell/implement ExamGenius

---

# PART K: TEAM AND HIRING PLAN

## Hiring Timeline

### Month 1
| Role | Salary (EGP/month) | Equity | Key Skills |
|------|-------------------|--------|------------|
| CTO / Co-Founder | 30,000 | 40% (vesting) | Node.js, PostgreSQL, AWS, team lead, 8+ years |
| Full-Stack Developer #1 | 20,000 | 0.5% (options) | React, Node.js, TypeScript, 4+ years |

### Month 2
| Role | Salary (EGP/month) | Equity | Key Skills |
|------|-------------------|--------|------------|
| Frontend Developer #1 | 18,000 | 0.3% (options) | React, TypeScript, responsive design, 3+ years |

### Month 3
| Role | Salary (EGP/month) | Equity | Key Skills |
|------|-------------------|--------|------------|
| DevOps Engineer | 22,000 | 0.3% (options) | AWS, Docker, Terraform, CI/CD, monitoring, 4+ years |

### Month 4
| Role | Salary (EGP/month) | Equity | Key Skills |
|------|-------------------|--------|------------|
| Sales Representative | 15,000 + commission | 0.1% (options) | EdTech or B2B SaaS sales, school relationships, English + Arabic |

### Month 6
| Role | Salary (EGP/month) | Equity | Key Skills |
|------|-------------------|--------|------------|
| AI/ML Engineer | 28,000 | 0.5% (options) | Python, NLP, transformers, fine-tuning, 4+ years |
| Customer Success Manager | 15,000 | 0.1% (options) | EdTech, teacher training, onboarding, English + Arabic |

### Year 2 Additions
| Role | Salary (EGP/month) | Timing |
|------|-------------------|--------|
| Backend Developer #2 | 22,000 | Month 8 |
| Mobile Developer (React Native) | 22,000 | Month 10 |
| QA Engineer | 15,000 | Month 10 |
| Marketing Manager | 18,000 | Month 12 |
| Sales Representative #2 | 15,000 + commission | Month 14 |
| Account Manager | 16,000 | Month 16 |

### Year 3 Additions (GCC Expansion)
| Role | Salary | Location |
|------|--------|----------|
| UAE Sales Manager | 25,000 AED/month | Dubai |
| UAE Account Manager | 15,000 AED/month | Dubai |
| Backend Developer #3 | 25,000 EGP/month | Cairo (remote) |
| Frontend Developer #2 | 20,000 EGP/month | Cairo (remote) |
| Data Analyst | 18,000 EGP/month | Cairo |
| Technical Support (x2) | 12,000 EGP/month each | Cairo |
| Content Specialist (Arabic) | 15,000 EGP/month | Cairo |

## Organizational Structure

```
Ahmed Nasr (CEO)
├── Co-Founder / CTO
│   ├── Backend Team
│   │   ├── Full-Stack Dev #1
│   │   ├── Backend Dev #2 (Year 2)
│   │   └── Backend Dev #3 (Year 3)
│   ├── Frontend Team
│   │   ├── Frontend Dev #1
│   │   ├── Frontend Dev #2 (Year 3)
│   │   └── Mobile Dev (Year 2)
│   ├── AI/ML Engineer
│   ├── DevOps Engineer
│   └── QA Engineer (Year 2)
├── Sales & Marketing
│   ├── Sales Rep #1
│   ├── Sales Rep #2 (Year 2)
│   ├── Marketing Manager (Year 2)
│   └── UAE Sales Team (Year 3)
└── Customer Success
    ├── CS Manager
    ├── Account Manager (Year 2)
    ├── Technical Support (Year 3)
    └── Content Specialist (Year 3)
```

## ESOP (Employee Stock Option Pool)

- **Total pool:** 10% of company equity
- **Vesting:** 4 years with 1-year cliff
- **Allocation:**
  - CTO: 40% (separate co-founder agreement)
  - Engineering team: 3.5%
  - Sales and marketing: 1%
  - Customer success: 0.5%
  - Future hires reserve: 5%

## Salary Benchmarks (Egypt Market, 2026)

| Role | Junior (0-3yr) | Mid (3-6yr) | Senior (6+yr) |
|------|---------------|-------------|----------------|
| Backend Developer | 10-15K EGP | 18-25K EGP | 28-40K EGP |
| Frontend Developer | 10-15K EGP | 16-22K EGP | 25-35K EGP |
| Full-Stack Developer | 12-18K EGP | 20-28K EGP | 30-45K EGP |
| DevOps Engineer | 12-18K EGP | 20-28K EGP | 30-40K EGP |
| AI/ML Engineer | 15-22K EGP | 25-35K EGP | 38-55K EGP |
| QA Engineer | 8-12K EGP | 14-20K EGP | 22-30K EGP |
| Sales (SaaS) | 10-15K + commission | 15-22K + commission | 25-35K + commission |

*Our salaries are positioned at 60-70th percentile to attract quality while managing costs.*

---

# APPENDIX A: GLOSSARY

| Term | Definition |
|------|-----------|
| **Bloom's Taxonomy** | Educational framework with 6 cognitive levels: Remember, Understand, Apply, Analyze, Evaluate, Create |
| **Discrimination Index** | Statistical measure (-1 to +1) of how well a question differentiates between high and low performing students |
| **IGCSE** | International General Certificate of Secondary Education (Cambridge) |
| **IB** | International Baccalaureate |
| **IRT** | Item Response Theory - statistical model for adaptive testing |
| **LoRA** | Low-Rank Adaptation - parameter-efficient fine-tuning method |
| **LTI** | Learning Tools Interoperability - standard for LMS integration |
| **MTCNN** | Multi-task Cascaded Convolutional Networks - face detection model |
| **RBAC** | Role-Based Access Control |
| **SIS** | Student Information System |
| **SSO** | Single Sign-On |
| **vLLM** | High-throughput LLM serving engine |
| **WCAG** | Web Content Accessibility Guidelines |

---

# APPENDIX B: DOCUMENT REVISION HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-15 | Ahmed Nasr | Initial complete blueprint |

---

*This document is confidential and proprietary to ExamGenius. Distribution outside the founding team requires explicit written permission.*