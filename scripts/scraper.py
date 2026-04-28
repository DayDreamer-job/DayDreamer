#!/usr/bin/env python3
"""
DayDreamer — Multi-Source Job Scraper v2
========================================
Sources:
  1. Adzuna API       — free official API, aggregates Indeed + others
  2. Naukri           — HTML scraping, public pages
  3. LinkedIn         — public job search pages (no login)
  4. Indeed RSS       — official public RSS feed
  5. Foundit.in       — formerly Monster India
  6. Company Pages    — Razorpay, CRED, Meesho, Zepto, Freshworks, Infosys (via ATS APIs)
  7. Manual           — paste jobs directly in MANUAL_JOBS list

Setup:
  pip install -r requirements.txt

Usage:
  python scraper.py                          # run all sources
  python scraper.py --source naukri          # only Naukri
  python scraper.py --source linkedin        # only LinkedIn
  python scraper.py --source indeed          # only Indeed RSS
  python scraper.py --source adzuna          # only Adzuna API
  python scraper.py --source companies       # only company career pages
  python scraper.py --source manual          # only manual jobs
  python scraper.py --keyword "data analyst" # custom search keyword
  python scraper.py --dry-run                # print without inserting to DB
  python scraper.py --limit 50               # max jobs per source
"""

import os, sys, json, time, argparse, logging, re, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv('../.env.local')
load_dotenv('.env.local')
load_dotenv('.env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

SUPABASE_URL  = os.environ.get('NEXT_PUBLIC_SUPABASE_URL', '')
SUPABASE_KEY  = os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY', '')
ADZUNA_APP_ID = os.environ.get('ADZUNA_APP_ID', '')
ADZUNA_KEY    = os.environ.get('ADZUNA_API_KEY', '')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'en-IN,en;q=0.9',
}

# Edit these keywords to match your niche
DEFAULT_KEYWORDS = [
    'python developer india',
    'react developer india',
    'data scientist india',
    'full stack developer india',
    'ui ux designer india',
    'digital marketing india',
    'devops engineer india',
    'fresher software engineer india',
    'java developer india',
    'product manager india',
]

AGGREGATOR_DOMAINS = [
    'naukri.com', 'linkedin.com', 'indeed.com', 'foundit.in',
    'shine.com', 'monster.com', 'glassdoor.com', 'timesjobs.com',
]

def is_direct_company_link(url: str) -> bool:
    return bool(url) and not any(d in url.lower() for d in AGGREGATOR_DOMAINS)

def clean_html(raw: str) -> str:
    if not raw: return ''
    return BeautifulSoup(raw, 'html.parser').get_text(separator=' ', strip=True)[:2000]

def map_category(text: str) -> str:
    t = text.lower()
    if any(x in t for x in ['engineer','software','developer','python','java','react','devops','cloud','backend','frontend','fullstack','android','ios','data','ml','ai']): return 'Technology'
    if any(x in t for x in ['design','ux','ui','figma','creative','graphic']): return 'Design'
    if any(x in t for x in ['market','growth','content','seo','social media','digital']): return 'Marketing'
    if any(x in t for x in ['sales','business development','account executive']): return 'Sales'
    if any(x in t for x in ['hr','human resource','people','recruit','talent']): return 'HR & Talent'
    if any(x in t for x in ['finance','account','fintech','analyst','ca ','cfa']): return 'Finance'
    if any(x in t for x in ['product manager','product owner']): return 'Product'
    if any(x in t for x in ['data scientist','machine learning','deep learning','nlp','llm']): return 'Data & AI'
    return 'Technology'

def detect_work_mode(text: str) -> str:
    t = text.lower()
    if 'remote' in t: return 'Remote'
    if 'hybrid' in t: return 'Hybrid'
    return 'On-site'

def detect_experience(text: str) -> str:
    t = text.lower()
    if re.search(r'fresher|0\s*year|entry.?level|no experience', t): return 'Fresher'
    if re.search(r'0.?2\s*year|0\s*to\s*2|1.?2\s*year', t): return '0-2 years'
    if re.search(r'2.?4\s*year|2\s*to\s*4|3.?5\s*year', t): return '2-4 years'
    if re.search(r'5\+\s*year|5\s*to\s*8|senior', t): return '5+ years'
    return 'Not specified'


# ═══════════════════════════════════════════════════════════════
# SOURCE 1 — NAUKRI (HTML scraping)
# ═══════════════════════════════════════════════════════════════
def scrape_naukri(keywords: list, limit: int = 30) -> list:
    log.info("Scraping Naukri...")
    jobs = []
    per_kw = max(1, limit // min(len(keywords), 5))

    for keyword in keywords[:5]:
        try:
            slug = keyword.replace(' ', '-').replace('india','').strip('-')
            url  = f"https://www.naukri.com/{slug}-jobs?jobAge=1"
            resp = requests.get(url, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')

            cards = soup.select('article.jobTuple, div[class*="jobTuple"], div[class*="job-container"]')
            log.info(f"Naukri '{keyword}': {len(cards)} cards found")

            for card in cards[:per_kw]:
                try:
                    title_el   = card.select_one('a.title, a[class*="title"]')
                    company_el = card.select_one('a.subTitle, [class*="company"]')
                    loc_el     = card.select_one('li.location, [class*="location"]')
                    exp_el     = card.select_one('li.experience, [class*="exp"]')
                    sal_el     = card.select_one('li.salary, [class*="salary"]')
                    if not title_el: continue

                    href = title_el.get('href','')
                    if href and not href.startswith('http'): href = 'https://www.naukri.com' + href

                    jobs.append({
                        'title':        title_el.get_text(strip=True),
                        'company':      company_el.get_text(strip=True) if company_el else 'Hiring Company',
                        'location':     loc_el.get_text(strip=True) if loc_el else 'India',
                        'work_mode':    detect_work_mode((title_el.get_text() or '') + (loc_el.get_text() if loc_el else '')),
                        'job_type':     'Full-time',
                        'experience':   detect_experience(exp_el.get_text() if exp_el else title_el.get_text()),
                        'salary_text':  sal_el.get_text(strip=True) if sal_el else None,
                        'description':  f"{title_el.get_text(strip=True)} position. Visit Naukri for full details and to apply.",
                        'apply_url':    href or f"https://www.naukri.com/{slug}-jobs",
                        'apply_source': 'Naukri',
                        'category':     map_category(title_el.get_text()),
                        'skills':       [],
                        'is_featured':  False,
                    })
                except Exception as e:
                    log.debug(f"Naukri card error: {e}")

            time.sleep(2)
        except Exception as e:
            log.error(f"Naukri error for '{keyword}': {e}")

    log.info(f"Naukri total: {len(jobs)}")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 2 — LINKEDIN (public pages, no login)
# ═══════════════════════════════════════════════════════════════
def scrape_linkedin(keywords: list, limit: int = 30) -> list:
    log.info("Scraping LinkedIn public pages...")
    jobs = []
    per_kw = max(1, limit // min(len(keywords), 5))

    for keyword in keywords[:5]:
        try:
            url  = f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keyword)}&location=India&f_TPR=r86400&position=1&pageNum=0"
            resp = requests.get(url, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')

            cards = soup.select('div.base-card, div[class*="job-search-card"], li[class*="jobs-search"]')
            log.info(f"LinkedIn '{keyword}': {len(cards)} cards found")

            for card in cards[:per_kw]:
                try:
                    title_el   = card.select_one('h3[class*="title"], .base-search-card__title')
                    company_el = card.select_one('h4[class*="subtitle"], .base-search-card__subtitle, a[class*="company"]')
                    loc_el     = card.select_one('[class*="location"], .job-search-card__location')
                    link_el    = card.select_one('a[class*="base-card__full-link"], a[class*="job-card"]')
                    if not title_el: continue

                    jobs.append({
                        'title':        title_el.get_text(strip=True),
                        'company':      company_el.get_text(strip=True) if company_el else 'Hiring Company',
                        'location':     loc_el.get_text(strip=True) if loc_el else 'India',
                        'work_mode':    detect_work_mode((title_el.get_text() or '') + (loc_el.get_text() if loc_el else '')),
                        'job_type':     'Full-time',
                        'experience':   detect_experience(title_el.get_text()),
                        'salary_text':  None,
                        'description':  f"{title_el.get_text(strip=True)} at {company_el.get_text(strip=True) if company_el else 'a company'}. Apply via LinkedIn.",
                        'apply_url':    link_el.get('href','') if link_el else f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keyword)}",
                        'apply_source': 'LinkedIn',
                        'category':     map_category(title_el.get_text()),
                        'skills':       [],
                        'is_featured':  False,
                    })
                except Exception as e:
                    log.debug(f"LinkedIn card error: {e}")

            time.sleep(3)
        except Exception as e:
            log.error(f"LinkedIn error for '{keyword}': {e}")

    log.info(f"LinkedIn total: {len(jobs)}")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 3 — INDEED RSS (most reliable, official feed)
# ═══════════════════════════════════════════════════════════════
def scrape_indeed_rss(keywords: list, limit: int = 30) -> list:
    log.info("Scraping Indeed RSS...")
    jobs = []
    per_kw = max(1, limit // min(len(keywords), 5))

    for keyword in keywords[:5]:
        try:
            url  = f"https://in.indeed.com/rss?q={quote_plus(keyword)}&l=India&fromage=1&limit={per_kw}"
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()

            root = ET.fromstring(resp.content)
            channel = root.find('channel')
            if not channel: continue
            items = channel.findall('item')

            for item in items:
                try:
                    title    = item.findtext('title','').strip()
                    link     = item.findtext('link','').strip()
                    desc_raw = item.findtext('description','')
                    company  = ''

                    if ' - ' in title:
                        parts   = title.rsplit(' - ', 1)
                        title   = parts[0].strip()
                        company = parts[1].strip()

                    if not title: continue

                    desc_clean = clean_html(desc_raw)
                    # Check if description has a direct company apply link
                    soup_desc = BeautifulSoup(desc_raw, 'html.parser')
                    direct_link = ''
                    for a in soup_desc.find_all('a', href=True):
                        if is_direct_company_link(a['href']):
                            direct_link = a['href']
                            break

                    apply_url = direct_link or link
                    apply_src = 'Company' if direct_link else 'Indeed'

                    jobs.append({
                        'title':        title,
                        'company':      company or 'Hiring Company',
                        'location':     'India',
                        'work_mode':    detect_work_mode(title + ' ' + desc_clean),
                        'job_type':     'Full-time',
                        'experience':   detect_experience(title + ' ' + desc_clean),
                        'salary_text':  None,
                        'description':  desc_clean[:1000] or f"{title} position available in India.",
                        'apply_url':    apply_url,
                        'apply_source': apply_src,
                        'category':     map_category(title),
                        'skills':       [],
                        'is_featured':  False,
                    })
                except Exception as e:
                    log.debug(f"Indeed item error: {e}")

            log.info(f"Indeed '{keyword}': {len(items)} items")
            time.sleep(1)
        except ET.ParseError as e:
            log.error(f"Indeed RSS parse error for '{keyword}': {e}")
        except Exception as e:
            log.error(f"Indeed error for '{keyword}': {e}")

    log.info(f"Indeed total: {len(jobs)}")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 4 — FOUNDIT (formerly Monster India)
# ═══════════════════════════════════════════════════════════════
def scrape_foundit(keywords: list, limit: int = 20) -> list:
    log.info("Scraping Foundit.in...")
    jobs = []
    per_kw = max(1, limit // min(len(keywords), 3))

    for keyword in keywords[:3]:
        try:
            url  = f"https://www.foundit.in/srp/results?query={quote_plus(keyword)}&location=India"
            resp = requests.get(url, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')

            cards = soup.select('div[class*="jobCard"], div[class*="job-card"], div[class*="srpResultCard"]')
            log.info(f"Foundit '{keyword}': {len(cards)} cards")

            for card in cards[:per_kw]:
                try:
                    title_el   = card.select_one('h3[class*="title"], a[class*="title"], [class*="jobTitle"]')
                    company_el = card.select_one('[class*="company"], [class*="companyName"]')
                    loc_el     = card.select_one('[class*="location"]')
                    link_el    = card.select_one('a[href]')
                    if not title_el: continue

                    href = link_el.get('href','') if link_el else ''
                    if href and not href.startswith('http'): href = 'https://www.foundit.in' + href

                    jobs.append({
                        'title':        title_el.get_text(strip=True),
                        'company':      company_el.get_text(strip=True) if company_el else 'Hiring Company',
                        'location':     loc_el.get_text(strip=True) if loc_el else 'India',
                        'work_mode':    detect_work_mode(title_el.get_text()),
                        'job_type':     'Full-time',
                        'experience':   detect_experience(title_el.get_text()),
                        'salary_text':  None,
                        'description':  f"{title_el.get_text(strip=True)} position. Visit Foundit for full details.",
                        'apply_url':    href or 'https://www.foundit.in',
                        'apply_source': 'JobFoundIt',
                        'category':     map_category(title_el.get_text()),
                        'skills':       [],
                        'is_featured':  False,
                    })
                except Exception as e:
                    log.debug(f"Foundit card error: {e}")

            time.sleep(2)
        except Exception as e:
            log.error(f"Foundit error for '{keyword}': {e}")

    log.info(f"Foundit total: {len(jobs)}")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 5 — ADZUNA API (most reliable, free official API)
# Register free: https://developer.adzuna.com
# ═══════════════════════════════════════════════════════════════
def scrape_adzuna(keywords: list, limit: int = 50) -> list:
    if not ADZUNA_APP_ID or not ADZUNA_KEY:
        log.warning("Adzuna keys not set. Register free at developer.adzuna.com → add to .env")
        return []

    log.info("Fetching from Adzuna API...")
    jobs = []
    CAT_MAP = {
        'IT Jobs':'Technology','Engineering Jobs':'Technology','Design Jobs':'Design',
        'Marketing Jobs':'Marketing','Sales Jobs':'Sales','HR & Recruitment Jobs':'HR & Talent',
        'Finance Jobs':'Finance',
    }

    for keyword in keywords[:5]:
        try:
            resp = requests.get(
                "https://api.adzuna.com/v1/api/jobs/in/search/1",
                params={
                    'app_id': ADZUNA_APP_ID, 'app_key': ADZUNA_KEY,
                    'results_per_page': min(limit//5, 50),
                    'what': keyword, 'where': 'india', 'max_days_old': 1,
                },
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data.get('results', []):
                apply_url = item.get('apply_url') or item.get('redirect_url','')
                apply_src = 'Company' if is_direct_company_link(apply_url) else 'Indeed'
                low, high = item.get('salary_min'), item.get('salary_max')
                salary    = f"₹{int(low/100000):.0f}L–{int(high/100000):.0f}L" if low and high else None

                jobs.append({
                    'title':        item.get('title','').strip(),
                    'company':      item.get('company',{}).get('display_name','Unknown'),
                    'location':     item.get('location',{}).get('display_name','India'),
                    'work_mode':    detect_work_mode(item.get('title','') + item.get('description','')),
                    'job_type':     'Full-time',
                    'experience':   detect_experience(item.get('title','') + item.get('description','')),
                    'salary_text':  salary,
                    'description':  clean_html(item.get('description',''))[:1000],
                    'apply_url':    apply_url,
                    'apply_source': apply_src,
                    'category':     CAT_MAP.get(item.get('category',{}).get('label',''), map_category(item.get('title',''))),
                    'skills':       [],
                    'is_featured':  False,
                })

            log.info(f"Adzuna '{keyword}': {len(data.get('results',[]))} results")
            time.sleep(1)
        except Exception as e:
            log.error(f"Adzuna error for '{keyword}': {e}")

    log.info(f"Adzuna total: {len(jobs)}")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 6 — COMPANY CAREER PAGES
# Uses Lever/Greenhouse ATS public APIs — super reliable & direct links
# ═══════════════════════════════════════════════════════════════
def scrape_company_pages() -> list:
    log.info("Scraping company career pages...")
    jobs = []

    # Companies using Lever ATS (public JSON API — no scraping needed!)
    LEVER_COMPANIES = [
        ('razorpay',      'Razorpay',   'Bangalore, India'),
        ('zepto',         'Zepto',      'Mumbai, India'),
        ('cred-club',     'CRED',       'Bangalore, India'),
        ('meesho',        'Meesho',     'Bangalore, India'),
        ('swiggy',        'Swiggy',     'Bangalore, India'),
        ('dunzo',         'Dunzo',      'Bangalore, India'),
        ('browserstack',  'BrowserStack','Mumbai, India'),
        ('postman',       'Postman',    'Bangalore, India'),
    ]

    for slug, company, default_loc in LEVER_COMPANIES:
        try:
            url  = f"https://api.lever.co/v0/postings/{slug}?mode=json"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            data = resp.json()
            if not isinstance(data, list): continue

            for item in data[:12]:
                title = item.get('text','').strip()
                if not title: continue
                jobs.append({
                    'title':        title,
                    'company':      company,
                    'location':     item.get('categories',{}).get('location', default_loc),
                    'work_mode':    detect_work_mode(item.get('categories',{}).get('location','') + title),
                    'job_type':     'Full-time',
                    'experience':   detect_experience(title),
                    'salary_text':  None,
                    'description':  clean_html(item.get('descriptionPlain',''))[:800] or f"Join {company} as a {title}.",
                    'apply_url':    item.get('hostedUrl', f'https://jobs.lever.co/{slug}'),
                    'apply_source': 'Company',
                    'category':     map_category(item.get('categories',{}).get('team','') + ' ' + title),
                    'skills':       [],
                    'is_featured':  False,
                })
            log.info(f"{company}: {len(data)} jobs from Lever API")
            time.sleep(0.5)
        except Exception as e:
            log.error(f"{company} Lever error: {e}")

    # Companies using Greenhouse ATS (public JSON API)
    GREENHOUSE_COMPANIES = [
        ('freshworks',    'Freshworks',  'Chennai, India'),
        ('chargebee',     'Chargebee',   'Chennai, India'),
        ('hasura',        'Hasura',      'Bangalore, India'),
        ('setu',          'Setu',        'Bangalore, India'),
    ]

    for slug, company, default_loc in GREENHOUSE_COMPANIES:
        try:
            url  = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            data = resp.json()
            items = data.get('jobs', [])

            for item in items[:12]:
                title = item.get('title','').strip()
                if not title: continue
                loc   = item.get('location',{}).get('name', default_loc)
                jobs.append({
                    'title':        title,
                    'company':      company,
                    'location':     loc,
                    'work_mode':    detect_work_mode(loc + title),
                    'job_type':     'Full-time',
                    'experience':   detect_experience(title),
                    'salary_text':  None,
                    'description':  clean_html(item.get('content',''))[:800] or f"Join {company} as a {title}.",
                    'apply_url':    item.get('absolute_url', f'https://boards.greenhouse.io/{slug}'),
                    'apply_source': 'Company',
                    'category':     map_category(item.get('departments',[{}])[0].get('name','') + ' ' + title if item.get('departments') else title),
                    'skills':       [],
                    'is_featured':  False,
                })
            log.info(f"{company}: {len(items)} jobs from Greenhouse API")
            time.sleep(0.5)
        except Exception as e:
            log.error(f"{company} Greenhouse error: {e}")

    log.info(f"Company pages total: {len(jobs)}")
    return jobs


# ═══════════════════════════════════════════════════════════════
# MANUAL JOBS — paste jobs here to post instantly
# ═══════════════════════════════════════════════════════════════
MANUAL_JOBS = [
    # Uncomment a block, fill in details, run: python scraper.py --source manual
    # {
    #     "title": "React Developer",
    #     "company": "Startup XYZ",
    #     "location": "Bangalore, Karnataka",
    #     "work_mode": "Remote",
    #     "job_type": "Full-time",
    #     "experience": "1-3 years",
    #     "salary_text": "10-15 LPA",
    #     "description": "We are looking for a React developer...",
    #     "responsibilities": ["Build components", "Code reviews"],
    #     "requirements": ["2+ years React", "TypeScript knowledge"],
    #     "skills": ["React", "TypeScript", "CSS"],
    #     "apply_url": "https://company.com/careers/react-dev",
    #     "apply_source": "Company",
    #     "category": "Technology",
    #     "is_featured": False,
    # },
]


# ═══════════════════════════════════════════════════════════════
# DATABASE: Insert into Supabase with deduplication
# ═══════════════════════════════════════════════════════════════
def post_jobs_to_supabase(jobs: list, dry_run: bool = False) -> int:
    if dry_run:
        log.info(f"[DRY RUN] Would process {len(jobs)} jobs:")
        for j in jobs[:10]:
            print(f"  → {j['title']} @ {j['company']} [{j.get('apply_source','?')}]")
        return 0

    if not SUPABASE_URL or not SUPABASE_KEY:
        log.error("Supabase credentials missing. Check .env file.")
        return 0

    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    inserted, skipped = 0, 0

    for job in jobs:
        title = (job.get('title') or '').strip()
        if not title or len(title) < 3 or not job.get('apply_url'):
            continue
        try:
            exists = db.table('jobs').select('id').eq('title', title[:200]).eq('company', (job.get('company',''))[:200]).execute()
            if exists.data:
                skipped += 1
                continue

            result = db.table('jobs').insert({
                'title':           title[:200],
                'company':         (job.get('company',''))[:200],
                'logo_url':        job.get('logo_url'),
                'location':        (job.get('location','India'))[:200],
                'work_mode':       job.get('work_mode','On-site'),
                'job_type':        job.get('job_type','Full-time'),
                'experience':      (job.get('experience','Not specified'))[:100],
                'salary_text':     job.get('salary_text'),
                'description':     (job.get('description',''))[:3000],
                'responsibilities':job.get('responsibilities',[]),
                'requirements':    job.get('requirements',[]),
                'skills':          job.get('skills',[]),
                'apply_url':       (job.get('apply_url',''))[:500],
                'apply_source':    job.get('apply_source','Company'),
                'category':        job.get('category','Technology'),
                'is_featured':     job.get('is_featured', False),
                'is_active':       True,
                'posted_at':       datetime.now(timezone.utc).isoformat(),
            }).execute()

            if result.data:
                inserted += 1
                log.info(f"✅ {title} @ {job.get('company')} [{job.get('apply_source','?')}]")
            time.sleep(0.15)

        except Exception as e:
            log.error(f"Insert error for '{title}': {e}")

    log.info(f"\n{'='*50}")
    log.info(f"✅ Inserted: {inserted}  |  ⏭ Duplicates skipped: {skipped}  |  Total: {len(jobs)}")
    return inserted


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description='DayDreamer Multi-Source Scraper v2')
    parser.add_argument('--source', default='all',
        choices=['all','naukri','linkedin','indeed','foundit','adzuna','companies','manual'])
    parser.add_argument('--keyword', default=None, help='Override search keyword')
    parser.add_argument('--limit',   type=int, default=30, help='Max jobs per source')
    parser.add_argument('--dry-run', action='store_true', help='Print without inserting')
    args = parser.parse_args()

    keywords = [args.keyword] if args.keyword else DEFAULT_KEYWORDS

    log.info(f"🚀 DayDreamer Scraper v2 | source={args.source} | limit={args.limit} | {'DRY RUN' if args.dry_run else 'LIVE'}")
    log.info('='*60)

    all_jobs = []

    if args.source in ('all','naukri'):     all_jobs += scrape_naukri(keywords, args.limit)
    if args.source in ('all','linkedin'):   all_jobs += scrape_linkedin(keywords, args.limit)
    if args.source in ('all','indeed'):     all_jobs += scrape_indeed_rss(keywords, args.limit)
    if args.source in ('all','foundit'):    all_jobs += scrape_foundit(keywords, args.limit)
    if args.source in ('all','adzuna'):     all_jobs += scrape_adzuna(keywords, args.limit)
    if args.source in ('all','companies'):  all_jobs += scrape_company_pages()
    if args.source in ('all','manual') and MANUAL_JOBS:
        log.info(f"Manual: {len(MANUAL_JOBS)} jobs queued")
        all_jobs += MANUAL_JOBS

    log.info(f"\n📊 Total scraped: {len(all_jobs)} jobs across all sources")

    if not all_jobs:
        log.warning("No jobs found. Check network and try --dry-run to debug.")
        return

    inserted = post_jobs_to_supabase(all_jobs, dry_run=args.dry_run)

    if not args.dry_run and inserted > 0:
        hook = os.environ.get('VERCEL_DEPLOY_HOOK_URL')
        if hook:
            try:
                requests.post(hook, timeout=10)
                log.info("🚀 Vercel redeploy triggered!")
            except Exception as e:
                log.warning(f"Vercel hook error: {e}")

    log.info("✅ Done!")


if __name__ == '__main__':
    main()