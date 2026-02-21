-- ============================================
-- Personal CRM Schema v2 (with Vector Embeddings)
-- ============================================
-- Based on OpenClaw gist #1: Personal CRM
-- Database: /root/.openclaw/workspace/knowledge-base/kb.db

-- Enable required extensions
.load /usr/lib/x86_64-linux-gnu/libsqlite3_vec.so

-- ============================================
-- CONTACTS TABLE (enhanced)
-- ============================================
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    first_name TEXT,
    last_name TEXT,
    company TEXT,
    job_title TEXT,
    role TEXT,                    -- recruiter, hiring_manager, colleague, network, vendor
    how_i_know TEXT,             -- linkedin, gmail, referral, event, conference, mutual
    source TEXT,                 -- gmail, calendar, linkedin, manual
    domain TEXT,                 -- company domain for grouping
    phone TEXT,
    linkedin_url TEXT,
    notes TEXT,
    
    -- Health scoring
    relationship_score INTEGER DEFAULT 50,  -- 0-100
    last_contact_date DATE,
    last_interaction_type TEXT,
    stale_since DATE,            -- when relationship became stale
    
    -- Vector embedding (384-dim for all-MiniLM-L6-v2)
    embedding BLOB,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_noisy INTEGER DEFAULT 0,  -- auto-detected marketing/newsletter
    is_active INTEGER DEFAULT 1,  -- soft delete
    tags TEXT                     -- JSON: ["ai", "pmf", "investor"]
);

-- ============================================
-- INTERACTIONS TABLE (enhanced)
-- ============================================
CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER REFERENCES contacts(id),
    type TEXT NOT NULL,          -- email, meeting, call, linkedin, message, application
    direction TEXT,              -- inbound, outbound
    subject TEXT,
    summary TEXT,
    date DATE NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT,                 -- gmail, calendar, manual, api
    has_attachment INTEGER DEFAULT 0,
    thread_id TEXT,             -- Gmail thread ID
    json_metadata TEXT           -- Raw JSON for debugging
);

-- ============================================
-- FOLLOW_UPS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS follow_ups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER REFERENCES contacts(id),
    job_id INTEGER REFERENCES job_pipeline(id),
    action TEXT NOT NULL,
    due_date DATE,
    priority TEXT DEFAULT 'medium', -- low, medium, high, urgent
    status TEXT DEFAULT 'pending',  -- pending, done, snoozed, skipped
    snoozed_until DATE,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);

-- ============================================
-- JOB PIPELINE (existing - keep compatible)
-- ============================================
CREATE TABLE IF NOT EXISTS job_pipeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    url TEXT,
    status TEXT DEFAULT 'discovered',  -- discovered, applied, screening, interview, offer, rejected, withdrawn
    ats_score INTEGER,
    cv_filename TEXT,
    applied_date DATE,
    contact_id INTEGER REFERENCES contacts(id),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- DUPLICATE DETECTION TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS contact_duplicates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id_1 INTEGER REFERENCES contacts(id),
    contact_id_2 INTEGER REFERENCES contacts(id),
    similarity_score REAL,       -- 0.0-1.0
    match_type TEXT,            -- email, name, company, all
    status TEXT DEFAULT 'pending',  -- pending, merged, ignored
    resolved_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- BOX DOCUMENTS LINK (new)
-- ============================================
CREATE TABLE IF NOT EXISTS contact_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER REFERENCES contacts(id),
    document_name TEXT,
    document_path TEXT,         -- Box file path or URL
    document_type TEXT,         -- resume, proposal, contract, notes, other
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company);
CREATE INDEX IF NOT EXISTS idx_contacts_stale ON contacts(stale_since) WHERE stale_since IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_contacts_active ON contacts(is_active, is_noisy);
CREATE INDEX IF NOT EXISTS idx_interactions_contact ON interactions(contact_id, date);
CREATE INDEX IF NOT EXISTS idx_interactions_type ON interactions(type, date);
CREATE INDEX IF NOT EXISTS idx_followups_status ON follow_ups(status, due_date);

-- ============================================
-- VIRTUAL TABLE FOR VECTOR SEARCH
-- ============================================
-- sqlite-vec requires virtual table
CREATE VIRTUAL TABLE IF NOT EXISTS contacts_vec USING vec0(
    embedding float[384]
);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Health score calculation
-- Returns 0-100 based on recency and frequency
CREATE FUNCTION IF NOT EXISTS calculate_health_score(contact_id INTEGER)
RETURNS INTEGER AS
WITH RECURSIVE
    days_since AS (
        SELECT COALESCE(
            (SELECT MIN(julianday('now') - julianday(last_contact_date)) FROM contacts WHERE id = contact_id),
            365
        )
    ),
    interaction_count AS (
        SELECT COUNT(*) as cnt FROM interactions WHERE contact_id = calculate_health_score.contact_id
    )
SELECT 
    CASE 
        WHEN days_since <= 7 THEN 90
        WHEN days_since <= 30 THEN 75
        WHEN days_since <= 90 THEN 60
        WHEN days_since <= 180 THEN 40
        WHEN days_since <= 365 THEN 25
        ELSE 10
    END +
    CASE 
        WHEN (SELECT cnt FROM interaction_count) >= 10 THEN 10
        WHEN (SELECT cnt FROM interaction_count) >= 5 THEN 5
        WHEN (SELECT cnt FROM interaction_count) >= 1 THEN 2
        ELSE 0
    END;

-- Stale relationship flag
CREATE FUNCTION IF NOT EXISTS is_stale(contact_id INTEGER)
RETURNS INTEGER AS
SELECT CASE 
    WHEN last_contact_date IS NULL THEN 1
    WHEN julianday('now') - julianday(last_contact_date) > 90 THEN 1
    ELSE 0
END FROM contacts WHERE id = contact_id;

-- ============================================
-- VIEWS
-- ============================================

-- View: All contacts with health scores
CREATE VIEW IF NOT EXISTS contacts_with_health AS
SELECT 
    c.*,
    calculate_health_score(c.id) as health_score,
    is_stale(c.id) as is_stale,
    (SELECT COUNT(*) FROM interactions WHERE contact_id = c.id) as total_interactions,
    (SELECT MAX(date) FROM interactions WHERE contact_id = c.id) as last_interaction
FROM contacts c
WHERE c.is_active = 1 AND c.is_noisy = 0;

-- View: Stale relationships needing attention
CREATE VIEW IF NOT EXISTS stale_relationships AS
SELECT 
    c.name, c.email, c.company, c.job_title,
    c.last_contact_date,
    calculate_health_score(c.id) as health_score,
    c.stale_since
FROM contacts c
WHERE is_stale(c.id) = 1 AND c.is_active = 1
ORDER BY c.last_contact_date ASC;

-- View: Interaction summary by contact
CREATE VIEW IF NOT EXISTS interaction_summary AS
SELECT 
    c.name, c.company,
    COUNT(i.id) as total_interactions,
    SUM(CASE WHEN i.direction = 'inbound' THEN 1 ELSE 0 END) as inbound,
    SUM(CASE WHEN i.direction = 'outbound' THEN 1 ELSE 0 END) as outbound,
    MAX(i.date) as last_interaction
FROM contacts c
LEFT JOIN interactions i ON c.id = i.contact_id
WHERE c.is_active = 1
GROUP BY c.id;
