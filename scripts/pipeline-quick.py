#!/usr/bin/env python3
"""
Pipeline Quick Actions
======================
Fast CLI for manual pipeline updates triggered by chat.

Usage:
    pipeline-quick.py register-url <linkedin_url>       # Register a job from URL
    pipeline-quick.py mark-applied <company_or_id>      # Mark job as applied
    pipeline-quick.py add-contact <company> --name X --email Y --phone Z
    pipeline-quick.py add-note <company> --note "..."
    pipeline-quick.py lookup <company_or_keyword>        # Search DB
    pipeline-quick.py status                             # Quick funnel summary
"""

import json, os, sys, re, argparse, sqlite3, urllib.request, time
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import pipeline_db as _pdb
except ImportError:
    print("ERROR: pipeline_db.py not found")
    sys.exit(1)

DB_PATH = "/root/.openclaw/workspace/data/nasr-pipeline.db"
COOKIE_PATH = "/root/.openclaw/cookies/linkedin.txt"
CAIRO = timezone(timedelta(hours=2))


def extract_linkedin_job_id(url):
    """Extract job ID from LinkedIn URL."""
    # https://www.linkedin.com/jobs/view/12345678/
    # https://linkedin.com/jobs/view/12345678
    m = re.search(r'/jobs/view/(\d+)', url)
    if m:
        return m.group(1)
    # ?currentJobId=12345678
    m = re.search(r'currentJobId=(\d+)', url)
    if m:
        return m.group(1)
    return None


def fetch_linkedin_jd(job_id):
    """Fetch job details from LinkedIn Voyager API."""
    cookies = {}
    if os.path.exists(COOKIE_PATH):
        with open(COOKIE_PATH) as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 7:
                    cookies[parts[5]] = parts[6]

    li_at = cookies.get('li_at', '')
    jsessionid = cookies.get('JSESSIONID', '').strip('"')

    if not li_at:
        return None

    url = f"https://www.linkedin.com/voyager/api/jobs/jobPostings/{job_id}"
    headers = {
        "Cookie": f"li_at={li_at}; JSESSIONID=\"{jsessionid}\"",
        "Csrf-Token": jsessionid,
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/vnd.linkedin.normalized+json+2.1",
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            title = data.get("title", "Unknown Role")
            company_name = "Unknown"
            
            # Try to extract company
            company_data = data.get("companyDetails", {})
            if isinstance(company_data, dict):
                company_name = company_data.get("company", {}).get("name", "Unknown")
            
            # Try different company name paths
            if company_name == "Unknown":
                for key in ["companyName", "formattedLocation"]:
                    if key in data and data[key]:
                        if key == "companyName":
                            company_name = data[key]
                            break

            location = data.get("formattedLocation", "")
            description = data.get("description", {})
            if isinstance(description, dict):
                jd_text = description.get("text", "")
            else:
                jd_text = str(description)

            return {
                "job_id": f"li-{job_id}",
                "title": title,
                "company": company_name,
                "location": location,
                "jd_text": jd_text,
                "job_url": f"https://www.linkedin.com/jobs/view/{job_id}/",
                "source": "linkedin-manual",
            }
    except Exception as e:
        print(f"Voyager API failed: {e}")
        return None


def cmd_register_url(url):
    """Register a job from a LinkedIn URL."""
    job_id = extract_linkedin_job_id(url)
    if not job_id:
        print(f"Could not extract job ID from: {url}")
        return None

    # Check if already in DB
    existing = _pdb.get_job(f"li-{job_id}")
    if existing:
        print(json.dumps({
            "status": "exists",
            "job_id": f"li-{job_id}",
            "company": existing.get("company", "?"),
            "title": existing.get("title", "?"),
            "db_status": existing.get("status", "?"),
        }))
        return existing

    # Fetch from Voyager
    data = fetch_linkedin_jd(job_id)
    if not data:
        # Register with minimal info
        data = {
            "job_id": f"li-{job_id}",
            "title": "Unknown Role",
            "company": "Unknown",
            "job_url": url,
            "source": "linkedin-manual",
        }

    # Register in DB
    _pdb.register_job(
        job_id=data["job_id"],
        source=data.get("source", "linkedin-manual"),
        company=data.get("company", "Unknown"),
        title=data.get("title", "Unknown"),
        location=data.get("location", ""),
        job_url=data.get("job_url", url),
    )

    # Cache JD if available
    jd = data.get("jd_text", "")
    if jd and len(jd) > 50:
        _pdb.update_field(data["job_id"], jd_text=jd)
        # Also save to jd-cache
        cache_dir = "/root/.openclaw/workspace/data/jd-cache"
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = f"{cache_dir}/{job_id}.json"
        with open(cache_path, 'w') as f:
            json.dump({"job_id": job_id, "jd": jd, "fetched_at": datetime.now(CAIRO).isoformat()}, f)

    # Classify cluster
    title = data.get("title", "").lower()
    CLUSTERS = {
        "PMO & Program Management": ["pmo", "program manager", "project director", "project management", "project controls", "project execution", "program director"],
        "Digital Transformation & Strategy": ["transformation", "strategy", "strategic", "chief strategy", "business excellence", "innovation"],
        "CTO & Technology Leadership": ["cto", "chief technology", "head of engineering", "head of it", "director of it", "director of engineering", "it director", "vp technology"],
        "Data & AI Leadership": ["data", "analytics", "ai ", "artificial intelligence", "machine learning", "data science"],
        "Product & E-Commerce": ["product", "e-commerce", "ecommerce", "head of product", "director of product"],
        "FinTech & Financial Services": ["fintech", "financial", "banking", "payments", "credit"],
        "Operations & COO": ["coo", "chief operating", "operations", "facilities", "logistics"],
    }
    for cluster, keywords in CLUSTERS.items():
        if any(kw in title for kw in keywords):
            _pdb.update_field(data["job_id"], cv_cluster=cluster)
            data["cluster"] = cluster
            break

    print(json.dumps({
        "status": "registered",
        "job_id": data["job_id"],
        "company": data.get("company", "?"),
        "title": data.get("title", "?"),
        "location": data.get("location", "?"),
        "jd_length": len(data.get("jd_text", "")),
        "cluster": data.get("cluster", "unclassified"),
    }, indent=2))
    return data


def cmd_mark_applied(identifier, via="linkedin"):
    """Mark a job as applied by company name, job ID, or title keyword."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Try exact job_id match first
    row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (identifier,)).fetchone()

    if not row:
        # Try company name match
        rows = conn.execute(
            "SELECT * FROM jobs WHERE LOWER(company) LIKE ? ORDER BY created_at DESC",
            (f"%{identifier.lower()}%",)
        ).fetchall()
        if len(rows) == 1:
            row = rows[0]
        elif len(rows) > 1:
            print(f"Multiple matches for '{identifier}':")
            for r in rows[:10]:
                print(f"  {r['job_id']:20s} | {r['company']:25s} | {r['title']:40s} | {r['status']}")
            conn.close()
            return None

    if not row:
        # Try title keyword match
        rows = conn.execute(
            "SELECT * FROM jobs WHERE LOWER(title) LIKE ? ORDER BY created_at DESC",
            (f"%{identifier.lower()}%",)
        ).fetchall()
        if len(rows) == 1:
            row = rows[0]
        elif len(rows) > 1:
            print(f"Multiple matches for '{identifier}':")
            for r in rows[:10]:
                print(f"  {r['job_id']:20s} | {r['company']:25s} | {r['title']:40s} | {r['status']}")
            conn.close()
            return None

    conn.close()

    if not row:
        print(f"No job found matching: {identifier}")
        return None

    _pdb.mark_applied(row['job_id'], via=via)
    now = datetime.now(CAIRO).strftime("%Y-%m-%d")

    print(json.dumps({
        "status": "updated",
        "job_id": row['job_id'],
        "company": row['company'],
        "title": row['title'],
        "new_status": "applied",
        "applied_date": now,
        "applied_via": via,
    }, indent=2))


def cmd_add_contact(identifier, name=None, email=None, phone=None):
    """Add recruiter contact to a job."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM jobs WHERE LOWER(company) LIKE ? ORDER BY created_at DESC",
        (f"%{identifier.lower()}%",)
    ).fetchall()
    conn.close()

    if not rows:
        print(f"No job found matching: {identifier}")
        return
    if len(rows) > 1:
        print(f"Multiple matches — using most recent: {rows[0]['title']} @ {rows[0]['company']}")

    job = rows[0]
    fields = {}
    if name:
        fields["recruiter_name"] = name
    if email:
        fields["recruiter_email"] = email
    if phone:
        fields["recruiter_phone"] = phone
    if fields:
        _pdb.update_field(job['job_id'], **fields)

    print(json.dumps({
        "status": "contact_added",
        "job_id": job['job_id'],
        "company": job['company'],
        "recruiter_name": name,
        "recruiter_email": email,
        "recruiter_phone": phone,
    }, indent=2))


def cmd_add_note(identifier, note):
    """Add a note to a job."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM jobs WHERE LOWER(company) LIKE ? ORDER BY created_at DESC",
        (f"%{identifier.lower()}%",)
    ).fetchall()
    conn.close()

    if not rows:
        print(f"No job found matching: {identifier}")
        return

    job = rows[0]
    existing = job['notes'] or ""
    timestamp = datetime.now(CAIRO).strftime("%Y-%m-%d %H:%M")
    updated = f"{existing}\n[{timestamp}] {note}".strip()
    _pdb.update_field(job['job_id'], notes=updated)

    print(json.dumps({
        "status": "note_added",
        "job_id": job['job_id'],
        "company": job['company'],
        "note": note,
    }, indent=2))


def cmd_lookup(query):
    """Search the DB for jobs matching a query."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    q = f"%{query.lower()}%"
    rows = conn.execute("""
        SELECT job_id, company, title, location, status, cv_cluster, ats_score,
               recruiter_name, recruiter_email, applied_date, cv_path, notes
        FROM jobs 
        WHERE LOWER(company) LIKE ? OR LOWER(title) LIKE ? OR LOWER(notes) LIKE ?
        ORDER BY created_at DESC
        LIMIT 20
    """, (q, q, q)).fetchall()
    conn.close()

    if not rows:
        print(f"No results for: {query}")
        return

    results = []
    for r in rows:
        results.append({
            "job_id": r['job_id'],
            "company": r['company'],
            "title": r['title'],
            "location": r['location'],
            "status": r['status'],
            "cluster": r['cv_cluster'],
            "ats_score": r['ats_score'],
            "recruiter": r['recruiter_name'] or "",
            "applied": r['applied_date'] or "",
            "has_cv": bool(r['cv_path']),
            "notes": (r['notes'] or "")[:100],
        })

    print(json.dumps(results, indent=2))


def cmd_status():
    """Quick pipeline status."""
    funnel = _pdb.get_funnel()
    stale = _pdb.get_stale(days=7)
    
    conn = sqlite3.connect(DB_PATH)
    with_contact = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE recruiter_email IS NOT NULL OR recruiter_name IS NOT NULL"
    ).fetchone()[0]
    with_cv = conn.execute("SELECT COUNT(*) FROM jobs WHERE cv_path IS NOT NULL").fetchone()[0]
    
    clusters = conn.execute(
        "SELECT cv_cluster, COUNT(*) FROM jobs WHERE cv_cluster IS NOT NULL GROUP BY cv_cluster ORDER BY COUNT(*) DESC"
    ).fetchall()
    conn.close()

    print(json.dumps({
        "funnel": funnel,
        "stale_with_contact": len(stale),
        "jobs_with_recruiter_contact": with_contact,
        "jobs_with_cv": with_cv,
        "clusters": {r[0]: r[1] for r in clusters},
        "timestamp": datetime.now(CAIRO).isoformat(),
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Pipeline Quick Actions")
    sub = parser.add_subparsers(dest="command")

    p_reg = sub.add_parser("register-url", help="Register job from LinkedIn URL")
    p_reg.add_argument("url")

    p_apply = sub.add_parser("mark-applied", help="Mark job as applied")
    p_apply.add_argument("identifier", help="Company name, job ID, or title keyword")
    p_apply.add_argument("--via", default="linkedin", help="Application channel")

    p_contact = sub.add_parser("add-contact", help="Add recruiter contact")
    p_contact.add_argument("identifier", help="Company name")
    p_contact.add_argument("--name", help="Recruiter name")
    p_contact.add_argument("--email", help="Recruiter email")
    p_contact.add_argument("--phone", help="Recruiter phone")

    p_note = sub.add_parser("add-note", help="Add note to a job")
    p_note.add_argument("identifier", help="Company name")
    p_note.add_argument("--note", required=True, help="Note text")

    p_lookup = sub.add_parser("lookup", help="Search DB")
    p_lookup.add_argument("query")

    sub.add_parser("status", help="Quick funnel summary")

    args = parser.parse_args()

    if args.command == "register-url":
        cmd_register_url(args.url)
    elif args.command == "mark-applied":
        cmd_mark_applied(args.identifier, via=args.via)
    elif args.command == "add-contact":
        cmd_add_contact(args.identifier, name=args.name, email=args.email, phone=args.phone)
    elif args.command == "add-note":
        cmd_add_note(args.identifier, note=args.note)
    elif args.command == "lookup":
        cmd_lookup(args.query)
    elif args.command == "status":
        cmd_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
