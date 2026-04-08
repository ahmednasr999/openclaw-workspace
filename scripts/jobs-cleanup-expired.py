#!/usr/bin/env python3
"""Mark stale/expired job URLs as expired. Run before cron merge to keep pipeline clean."""

import requests, sqlite3, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

DB = "/root/.openclaw/workspace/data/nasr-pipeline.db"


def check_url_alive(url, timeout=4):
    """Check if a URL returns a valid page. Returns True if alive."""
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return True
        # 403 = LinkedIn detected bot, might still be alive
        if r.status_code == 403:
            # Try with a proper user-agent
            r = requests.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            return r.status_code in [200, 403]
        return False
    except:
        return False


def main():
    db = sqlite3.connect(DB)
    c = db.cursor()

    # Get jobs with URLs from LinkedIn/Indeed that are not already applied/skip/expired
    c.execute(
        """
        SELECT id, job_url FROM jobs
        WHERE status NOT IN ('applied', 'skip', 'expired', 'discarded', 'rejected')
          AND job_url LIKE '%linkedin.com%'
    """
    )
    linkedin_jobs = [(r[0], r[1]) for r in c.fetchall() if r[1]]

    c.execute(
        """
        SELECT id, job_url FROM jobs
        WHERE status NOT IN ('applied', 'skip', 'expired', 'discarded', 'rejected')
          AND job_url LIKE '%indeed.com%'
    """
    )
    indeed_jobs = [(r[0], r[1]) for r in c.fetchall() if r[1]]

    total = len(linkedin_jobs) + len(indeed_jobs)
    print(f"Checking {total} URLs ({len(linkedin_jobs)} LinkedIn, {len(indeed_jobs)} Indeed)")

    expired_count = 0
    alive_count = 0
    checked = 0

    def check_and_mark(row):
        job_id, url = row
        alive = check_url_alive(url)
        return job_id, alive, url

    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(check_and_mark, r): r for r in linkedin_jobs + indeed_jobs}
        for f in as_completed(futures):
            job_id, alive, url = f.result()
            checked += 1
            if alive:
                alive_count += 1
            else:
                expired_count += 1
                c.execute("UPDATE jobs SET status = 'expired' WHERE id = ?", (job_id,))
                db.commit()

            if checked % 50 == 0:
                print(f"  Checked {checked}/{total}: {expired_count} expired, {alive_count} alive")

    print(f"\nDone: {checked} checked, {expired_count} marked expired, {alive_count} still alive")

    # Also mark duplicate-applied status for jobs already in the applied table
    c.execute(
        """
        UPDATE jobs SET status = 'duplicate-applied'
        WHERE ats_score IN (SELECT ats_score FROM jobs WHERE status='applied')
          AND status = 'discovered'
          AND title IN (SELECT title FROM jobs WHERE status='applied')
    """
    )
    print(f"Duplicate-applied cleanup: {c.rowcount} rows affected")

    db.close()
    return expired_count


if __name__ == "__main__":
    count = main()
    sys.exit(0 if count >= 0 else 1)
