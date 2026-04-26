#!/usr/bin/env python3
"""
DayDreamer — Python Job Scraper
==============================
Scrapes job listings from company career pages and inserts them into Supabase.
Also supports the Adzuna free API for automated job discovery.

Setup:
  pip install requests beautifulsoup4 supabase python-dotenv adzuna

Usage:
  python scripts/scraper.py                    # scrape all sources
  python scripts/scraper.py --source adzuna    # only Adzuna API
  python scripts/scraper.py --source infosys   # only Infosys careers
  python scripts/scraper.py --dry-run          # print without inserting
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv('../.env.local')

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

# ── Supabase client ───────────────────────────────────────────
SUPABASE_URL = os.environ.get('NEXT_PUBLIC_SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY', '')
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', '')
API_BASE_URL = os.environ.get('SITE_URL', 'http://localhost:3000')

# ── Adzuna API (free tier: 250 calls/month) ───────────────────
ADZUNA_APP_ID = os.environ.get('ADZUNA_APP_ID', '')    # register at developer.adzuna.com
ADZUNA_API_KEY = os.environ.get('ADZUNA_API_KEY', '')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


# ═══════════════════════════════════════════════════════════════
# ADZUNA API SCRAPER (free, no scraping, recommended)
# ═══════════════════════════════════════════════════════════════

def scrape_adzuna(keywords: str = 'software developer', location: str = 'india', pages: int = 3) -> list[dict]:
    """
    Fetch jobs from Adzuna free API.
    Register at https://developer.adzuna.com to get free API keys.
    Free tier: 250 calls/month, 50 results/call.
    """
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        log.warning("Adzuna API keys not set. Skipping Adzuna scraper.")
        return []

    jobs = []
    for page in range(1, pages + 1):
        url = f"https://api.adzuna.com/v1/api/jobs/in/search/{page}"
        params = {
            'app_id': ADZUNA_APP_ID,
            'app_key': ADZUNA_API_KEY,
            'results_per_page': 50,
            'what': keywords,
            'where': location,
            'content-type': 'application/json',
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get('results', []):
                job = {
                    'title': item.get('title', ''),
                    'company': item.get('company', {}).get('display_name', 'Unknown'),
                    'location': item.get('location', {}).get('display_name', 'India'),
                    'work_mode': 'On-site',
                    'job_type': 'Full-time',
                    'experience': 'Not specified',
                    'description': item.get('description', ''),
                    'apply_url': item.get('redirect_url', ''),
                    'apply_source': 'Indeed',  # Adzuna aggregates Indeed/etc
                    'category': map_adzuna_category(item.get('category', {}).get('label', '')),
                    'salary_text': format_adzuna_salary(item),
                    'skills': [],
                    'is_featured': False,
                }
                if job['title'] and job['apply_url']:
                    jobs.append(job)

            log.info(f"Adzuna page {page}: fetched {len(data.get('results', []))} jobs")
            time.sleep(1)  # be polite

        except Exception as e:
            log.error(f"Adzuna page {page} error: {e}")

    log.info(f"Adzuna total: {len(jobs)} jobs")
    return jobs


def map_adzuna_category(label: str) -> str:
    mapping = {
        'IT Jobs': 'Technology',
        'Engineering Jobs': 'Technology',
        'Design Jobs': 'Design',
        'Marketing Jobs': 'Marketing',
        'Sales Jobs': 'Sales',
        'HR & Recruitment Jobs': 'HR & Talent',
        'Finance Jobs': 'Finance',
        'Product Manager': 'Product',
    }
    return mapping.get(label, 'Technology')


def format_adzuna_salary(item: dict) -> Optional[str]:
    low = item.get('salary_min')
    high = item.get('salary_max')
    if low and high:
        # Convert annual GBP/USD rough estimate to LPA
        return f"₹{int(low/100000):.0f}L–{int(high/100000):.0f}L"
    return None


# ═══════════════════════════════════════════════════════════════
# COMPANY CAREER PAGE SCRAPERS
# ═══════════════════════════════════════════════════════════════

def scrape_freshworks() -> list[dict]:
    """Scrape Freshworks careers page."""
    log.info("Scraping Freshworks careers...")
    jobs = []
    try:
        url = "https://www.freshworks.com/company/careers/job-openings/"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Freshworks uses Greenhouse.io — jobs listed as <tr> rows
        for row in soup.select('tr.job'):
            title_el = row.select_one('td.cell-title a')
            dept_el = row.select_one('td.cell-department')
            loc_el = row.select_one('td.cell-location')

            if not title_el:
                continue

            jobs.append({
                'title': title_el.get_text(strip=True),
                'company': 'Freshworks',
                'location': loc_el.get_text(strip=True) if loc_el else 'India',
                'work_mode': 'Hybrid',
                'job_type': 'Full-time',
                'experience': 'Not specified',
                'description': f"Join Freshworks as a {title_el.get_text(strip=True)}. Visit the career page for full details.",
                'apply_url': 'https://www.freshworks.com' + title_el.get('href', ''),
                'apply_source': 'Company',
                'category': map_dept_to_category(dept_el.get_text(strip=True) if dept_el else ''),
                'skills': [],
                'is_featured': False,
            })

    except Exception as e:
        log.error(f"Freshworks scrape error: {e}")

    log.info(f"Freshworks: found {len(jobs)} jobs")
    return jobs


def scrape_zoho() -> list[dict]:
    """Scrape Zoho careers JSON feed."""
    log.info("Scraping Zoho careers...")
    jobs = []
    try:
        url = "https://careers.zohocorp.com/jobs/Careers"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        for item in soup.select('.job-listing-item, .careers-job-item')[:20]:
            title_el = item.select_one('h3, .job-title, a.job-link')
            loc_el = item.select_one('.location, .job-location')
            dept_el = item.select_one('.department, .job-dept')
            link_el = item.select_one('a')

            if not title_el:
                continue

            href = link_el.get('href', '') if link_el else ''
            if href and not href.startswith('http'):
                href = 'https://careers.zohocorp.com' + href

            jobs.append({
                'title': title_el.get_text(strip=True),
                'company': 'Zoho',
                'location': loc_el.get_text(strip=True) if loc_el else 'Chennai, India',
                'work_mode': 'On-site',
                'job_type': 'Full-time',
                'experience': 'Not specified',
                'description': f"Exciting opportunity at Zoho. Visit career page for full details.",
                'apply_url': href or 'https://careers.zohocorp.com',
                'apply_source': 'Company',
                'category': map_dept_to_category(dept_el.get_text(strip=True) if dept_el else ''),
                'skills': [],
                'is_featured': False,
            })

    except Exception as e:
        log.error(f"Zoho scrape error: {e}")

    log.info(f"Zoho: found {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# MANUAL JOB POSTING (for automation via scripts)
# ═══════════════════════════════════════════════════════════════

def post_job_via_api(job: dict, dry_run: bool = False) -> bool:
    """
    Post a job to DayDreamer via the API.
    The API requires the ADMIN_SECRET header.
    """
    if dry_run:
        log.info(f"[DRY RUN] Would post: {job['title']} @ {job['company']}")
        print(json.dumps(job, indent=2))
        return True

    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/jobs",
            json=job,
            headers={
                'Content-Type': 'application/json',
                'x-admin-secret': ADMIN_SECRET,
            },
            timeout=15
        )
        if resp.status_code == 201:
            log.info(f"✅ Posted: {job['title']} @ {job['company']}")
            return True
        else:
            log.error(f"❌ Failed: {job['title']} — {resp.status_code} {resp.text[:200]}")
            return False
    except Exception as e:
        log.error(f"❌ Error posting {job['title']}: {e}")
        return False


def post_jobs_direct_to_supabase(jobs: list[dict], dry_run: bool = False) -> int:
    """
    Insert jobs directly into Supabase (faster for bulk inserts).
    Skips duplicates based on title + company.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        log.error("Supabase credentials not set. Check .env.local")
        return 0

    if dry_run:
        log.info(f"[DRY RUN] Would insert {len(jobs)} jobs into Supabase")
        for job in jobs[:3]:
            print(json.dumps(job, indent=2))
        return 0

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    inserted = 0

    for job in jobs:
        try:
            # Check for duplicate
            existing = supabase.table('jobs') \
                .select('id') \
                .eq('title', job['title']) \
                .eq('company', job['company']) \
                .execute()

            if existing.data:
                log.debug(f"Skipping duplicate: {job['title']} @ {job['company']}")
                continue

            # Insert
            result = supabase.table('jobs').insert(job).execute()
            if result.data:
                inserted += 1
                log.info(f"✅ Inserted: {job['title']} @ {job['company']}")
            time.sleep(0.1)

        except Exception as e:
            log.error(f"Supabase insert error for {job.get('title', '?')}: {e}")

    return inserted


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def map_dept_to_category(dept: str) -> str:
    dept_lower = dept.lower()
    if any(x in dept_lower for x in ['engineer', 'software', 'tech', 'develop', 'data', 'ml', 'ai']):
        return 'Technology'
    if any(x in dept_lower for x in ['design', 'ux', 'ui', 'creative']):
        return 'Design'
    if any(x in dept_lower for x in ['market', 'growth', 'content', 'seo']):
        return 'Marketing'
    if any(x in dept_lower for x in ['sales', 'business development', 'bd']):
        return 'Sales'
    if any(x in dept_lower for x in ['hr', 'people', 'recruit', 'talent']):
        return 'HR & Talent'
    if any(x in dept_lower for x in ['finance', 'account', 'fintech']):
        return 'Finance'
    if any(x in dept_lower for x in ['product', 'pm', 'strategy']):
        return 'Product'
    return 'Technology'


# ═══════════════════════════════════════════════════════════════
# MANUAL POST EXAMPLE — paste jobs here for quick daily updates
# ═══════════════════════════════════════════════════════════════

MANUAL_JOBS = [
    # Add jobs here manually and run: python scraper.py --source manual
    # {
    #     "title": "React Developer",
    #     "company": "Startup XYZ",
    #     "location": "Bangalore, Karnataka",
    #     "work_mode": "Remote",
    #     "job_type": "Full-time",
    #     "experience": "1-3 years",
    #     "salary_text": "10-15 LPA",
    #     "description": "...",
    #     "responsibilities": ["Build React components", "..."],
    #     "requirements": ["2+ years React", "..."],
    #     "skills": ["React", "TypeScript", "Node.js"],
    #     "apply_url": "https://company.com/careers",
    #     "apply_source": "Company",
    #     "category": "Technology",
    #     "is_featured": False,
    # },
]


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='DayDreamer Scraper')
    parser.add_argument('--source', choices=['all', 'adzuna', 'freshworks', 'zoho', 'manual'], default='all')
    parser.add_argument('--dry-run', action='store_true', help='Print jobs without inserting')
    parser.add_argument('--keyword', default='software developer', help='Search keyword for Adzuna')
    args = parser.parse_args()

    all_jobs = []

    if args.source in ('all', 'adzuna'):
        all_jobs += scrape_adzuna(keywords=args.keyword)

    if args.source in ('all', 'freshworks'):
        all_jobs += scrape_freshworks()

    if args.source in ('all', 'zoho'):
        all_jobs += scrape_zoho()

    if args.source in ('all', 'manual') and MANUAL_JOBS:
        log.info(f"Manual jobs: {len(MANUAL_JOBS)} queued")
        all_jobs += MANUAL_JOBS

    log.info(f"\n{'='*50}")
    log.info(f"Total jobs to process: {len(all_jobs)}")

    if not all_jobs:
        log.warning("No jobs found. Check your API keys and network connectivity.")
        return

    inserted = post_jobs_direct_to_supabase(all_jobs, dry_run=args.dry_run)

    if not args.dry_run:
        log.info(f"\n✅ Done! Inserted {inserted}/{len(all_jobs)} new jobs.")

        # Trigger Vercel redeploy if webhook is set
        deploy_hook = os.environ.get('VERCEL_DEPLOY_HOOK_URL')
        if deploy_hook:
            try:
                requests.post(deploy_hook, timeout=10)
                log.info("🚀 Vercel redeploy triggered!")
            except Exception as e:
                log.warning(f"Could not trigger Vercel redeploy: {e}")


if __name__ == '__main__':
    main()
