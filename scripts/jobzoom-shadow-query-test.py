#!/usr/bin/env python3
"""Shadow-test candidate JobZoom LinkedIn queries without touching the daily output file."""

import json
import time
from collections import OrderedDict
from datetime import datetime, timezone, timedelta
from pathlib import Path

import importlib.util
import sys
sys.path.insert(0, str(Path(__file__).parent))
_scraper_path = Path(__file__).parent / 'jobs-source-linkedin-jobspy.py'
_spec = importlib.util.spec_from_file_location('jobs_source_linkedin_jobspy', _scraper_path)
_scraper = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_scraper)
scrape_linkedin_jobspy = _scraper.scrape_linkedin_jobspy

CAIRO = timezone(timedelta(hours=2))
OUT_DIR = Path('/root/.openclaw/workspace-jobzoom/reports/shadow')
OUT_DIR.mkdir(parents=True, exist_ok=True)

LOCATION_MAP = OrderedDict({
    'United Arab Emirates': 'Dubai, UAE',
    'Saudi Arabia': 'Riyadh, Saudi Arabia',
    'Qatar': 'Doha, Qatar',
    'Bahrain': 'Manama, Bahrain',
    'Kuwait': 'Kuwait City, Kuwait',
    'Oman': 'Muscat, Oman',
})

CANDIDATE_KEYWORDS = [
    'Digital Transformation Director',
    'Healthcare Transformation Director',
    'FinTech Program Director',
    'Banking Program Director',
    'Hospital Transformation Lead',
]

WATCHLIST = [
    'Saudi German Hospital Group',
    'Cleveland Clinic Abu Dhabi',
    'Mediclinic Middle East',
    'NMC Healthcare',
    'Aster DM Healthcare',
    'King Faisal Specialist Hospital',
    'SEHA',
    'Abu Dhabi Health Services',
    'Hamad Medical Corporation',
    'Al Habib Medical Group',
    'Fakeeh Care',
    'Careem',
]

# Keep the first shadow cheap and diagnostic: UAE + KSA only for watchlist,
# company name alone. If this produces zero, complex company Boolean queries are not worth keeping.
WATCHLIST_COUNTRIES = ['United Arab Emirates', 'Saudi Arabia']


def run_search(kind, query, country, location, seq, total):
    started = time.time()
    print(f'[{seq}/{total}] [{kind}] {query!r} @ {location}...', end=' ', flush=True)
    error = None
    jobs = []
    try:
        jobs = scrape_linkedin_jobspy(query, location, country)
    except Exception as exc:  # scrape function normally swallows, keep belt+suspenders
        error = f'{type(exc).__name__}: {exc}'
    runtime_ms = int((time.time() - started) * 1000)
    print(f'{len(jobs)} found in {runtime_ms}ms' + (f' ERROR {error}' if error else ''))
    return {
        'seq': seq,
        'kind': kind,
        'query': query,
        'country': country,
        'location': location,
        'found': len(jobs),
        'runtime_ms': runtime_ms,
        'error': error,
        'sample_jobs': [
            {
                'title': j.get('title', ''),
                'company': j.get('company', ''),
                'location': j.get('location', ''),
                'url': j.get('url', ''),
            }
            for j in jobs[:5]
        ],
    }, jobs


def main():
    searches = []
    for country, location in LOCATION_MAP.items():
        for query in CANDIDATE_KEYWORDS:
            searches.append(('keyword-candidate', query, country, location))
    for company in WATCHLIST:
        for country in WATCHLIST_COUNTRIES:
            searches.append(('watchlist-company-simple', company, country, LOCATION_MAP[country]))

    started = datetime.now(CAIRO).isoformat()
    per_search = []
    all_jobs = OrderedDict()
    total = len(searches)
    for idx, (kind, query, country, location) in enumerate(searches, 1):
        row, jobs = run_search(kind, query, country, location, idx, total)
        new_count = 0
        for job in jobs:
            key = job.get('linkedin_id') or job.get('id') or job.get('url')
            if key and key not in all_jobs:
                all_jobs[key] = job
                new_count += 1
        row['new_unique'] = new_count
        row['running_unique_total'] = len(all_jobs)
        per_search.append(row)
        time.sleep(2)

    output = {
        'meta': {
            'name': 'jobzoom-shadow-query-test',
            'started_at': started,
            'finished_at': datetime.now(CAIRO).isoformat(),
            'searches': total,
            'unique_jobs': len(all_jobs),
            'mode': 'shadow-no-daily-output-change',
        },
        'per_search': per_search,
        'jobs': list(all_jobs.values()),
    }
    out_json = OUT_DIR / f"jobzoom-shadow-query-test-{datetime.now(CAIRO).strftime('%Y%m%d-%H%M%S')}.json"
    out_json.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    out_md = out_json.with_suffix('.md')
    lines = [
        '# JobZoom shadow query test',
        '',
        f"Started: {output['meta']['started_at']}",
        f"Searches: {total}",
        f"Unique jobs: {len(all_jobs)}",
        '',
        '| # | Kind | Country | Query | Found | New unique | Runtime ms |',
        '|---:|---|---|---|---:|---:|---:|',
    ]
    for r in per_search:
        q = r['query'].replace('|', '\\|')
        lines.append(f"| {r['seq']} | {r['kind']} | {r['country']} | {q} | {r['found']} | {r['new_unique']} | {r['runtime_ms']} |")
    lines.append('')
    lines.append('## Searches with hits')
    lines.append('')
    for r in per_search:
        if r['found']:
            lines.append(f"### #{r['seq']} {r['country']} - {r['query']} ({r['found']} found, {r['new_unique']} new)")
            for j in r['sample_jobs']:
                lines.append(f"- {j['title']} @ {j['company']} - {j['location']}")
            lines.append('')
    out_md.write_text('\n'.join(lines))
    print(f'Wrote {out_json}')
    print(f'Wrote {out_md}')


if __name__ == '__main__':
    main()
