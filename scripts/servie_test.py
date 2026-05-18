#!/usr/bin/env python3
"""
DayDreamer — Service-Based Company Job Scraper v5
==================================================
Uses Playwright (headless Chromium) to scrape JS-rendered career pages.

Companies:
  Accenture, TCS, Wipro, Cognizant, Infosys, Capgemini,
  IBM, Deloitte, Tech Mahindra, LTIMindtree

Install deps (once on your server):
  pip install playwright beautifulsoup4 python-dotenv supabase requests
  playwright install chromium

Usage:
  python scraper_service_based.py                      # all companies
  python scraper_service_based.py --source wipro       # one company
  python scraper_service_based.py --dry-run            # preview only
  python scraper_service_based.py --limit 20           # cap per company
"""

import os
import re
import sys
import json
import time
import random
import logging
import argparse
from datetime import datetime, timezone, date, timedelta
from typing import Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ── env ──────────────────────────────────────────────────────
load_dotenv('../.env.local')
load_dotenv('.env.local')
load_dotenv('.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get('NEXT_PUBLIC_SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY', '')

TODAY     = date.today()
YESTERDAY = TODAY - timedelta(days=1)


# ─────────────────────────────────────────────────────────────
# PLAYWRIGHT HELPERS
# ─────────────────────────────────────────────────────────────

def get_browser():
    from playwright.sync_api import sync_playwright
    pw      = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
        ],
    )
    return pw, browser


def new_page(browser):
    ctx = browser.new_context(
        user_agent=(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/122.0.0.0 Safari/537.36'
        ),
        locale='en-IN',
        viewport={'width': 1280, 'height': 900},
    )
    page = ctx.new_page()
    page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )
    return page


def safe_goto(page, url, wait='networkidle', timeout=30000):
    try:
        page.goto(url, wait_until=wait, timeout=timeout)
        return True
    except Exception:
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            return True
        except Exception as e:
            log.error(f"Navigation failed [{url}]: {e}")
            return False


def wait_for_any(page, selectors, timeout=12000):
    for sel in selectors:
        try:
            page.wait_for_selector(sel, timeout=timeout)
            return True
        except Exception:
            pass
    return False


def get_soup(page):
    return BeautifulSoup(page.content(), 'html.parser')


# ─────────────────────────────────────────────────────────────
# GENERAL HELPERS
# ─────────────────────────────────────────────────────────────

def clean_html(raw):
    if not raw:
        return ''
    return BeautifulSoup(raw, 'html.parser').get_text(separator=' ', strip=True)[:3000]


def map_category(text):
    t = text.lower()
    if any(x in t for x in [
        'engineer', 'software', 'developer', 'python', 'java', 'react',
        'devops', 'cloud', 'backend', 'frontend', 'fullstack', 'android',
        'ios', 'data', 'ml', 'ai', 'sap', 'erp', '.net', 'qa',
        'testing', 'automation', 'support', 'analyst', 'consultant',
        'architect', 'security', 'cyber', 'network', 'infra',
    ]):
        return 'Technology'
    if any(x in t for x in ['design', 'ux', 'ui', 'figma', 'creative', 'graphic']):
        return 'Design'
    if any(x in t for x in ['market', 'growth', 'content', 'seo', 'social', 'digital']):
        return 'Marketing'
    if any(x in t for x in ['sales', 'business development', 'account executive']):
        return 'Sales'
    if any(x in t for x in ['hr', 'human resource', 'people', 'recruit', 'talent']):
        return 'HR & Talent'
    if any(x in t for x in ['finance', 'account', 'fintech', 'ca ', 'cfa', 'audit']):
        return 'Finance'
    if any(x in t for x in ['product manager', 'product owner']):
        return 'Product'
    if any(x in t for x in ['data scientist', 'machine learning', 'deep learning', 'nlp', 'llm']):
        return 'Data & AI'
    return 'Technology'


def detect_work_mode(text):
    t = text.lower()
    if 'remote' in t:
        return 'Remote'
    if 'hybrid' in t:
        return 'Hybrid'
    return 'On-site'


def detect_experience(text):
    t = text.lower()
    if re.search(r'fresher|0\s*year|entry.?level|no experience|trainee|graduate|campus', t):
        return 'Fresher'
    if re.search(r'0.?2\s*year|0\s*to\s*2|1.?2\s*year', t):
        return '0-2 years'
    if re.search(r'2.?4\s*year|2\s*to\s*4|3.?5\s*year', t):
        return '2-4 years'
    if re.search(r'5\+\s*year|5\s*to\s*8|senior|lead|principal|manager|director', t):
        return '5+ years'
    return 'Not specified'


def random_views():
    return random.randint(100, 2000)


def _job_stub(title, company, location, apply_url,
              description='', experience=None, work_mode=None):
    return {
        'title':            title,
        'company':          company,
        'location':         str(location)[:200],
        'work_mode':        work_mode or detect_work_mode(str(location) + title),
        'job_type':         'Full-time',
        'experience':       experience or detect_experience(title),
        'salary_text':      None,
        'description':      (description or f"{title} at {company}.")[:3000],
        'responsibilities': [],
        'requirements':     [],
        'skills':           [],
        'apply_url':        apply_url,
        'apply_source':     'Company',
        'category':         map_category(title),
        'is_featured':      False,
    }


# ── salary ────────────────────────────────────────────────────
_SALARY_MATRIX = {
    'Technology':  {'Fresher': (3, 6),    '0-2 years': (4, 8),   '2-4 years': (8, 15),  '5+ years': (15, 35), 'Not specified': (5, 12)},
    'Design':      {'Fresher': (2.5, 5),  '0-2 years': (3.5, 7), '2-4 years': (6, 12),  '5+ years': (12, 25), 'Not specified': (4, 10)},
    'Marketing':   {'Fresher': (2, 4),    '0-2 years': (3, 6),   '2-4 years': (5, 10),  '5+ years': (10, 20), 'Not specified': (3, 8)},
    'Sales':       {'Fresher': (1.5, 3),  '0-2 years': (2.5, 5), '2-4 years': (4, 8),   '5+ years': (8, 18),  'Not specified': (3, 7)},
    'HR & Talent': {'Fresher': (2, 4),    '0-2 years': (2.5, 5), '2-4 years': (4, 8),   '5+ years': (8, 15),  'Not specified': (3, 7)},
    'Finance':     {'Fresher': (2.5, 5),  '0-2 years': (3.5, 7), '2-4 years': (6, 12),  '5+ years': (12, 25), 'Not specified': (4, 10)},
    'Product':     {'Fresher': (4, 7),    '0-2 years': (6, 10),  '2-4 years': (10, 18), '5+ years': (18, 40), 'Not specified': (6, 15)},
    'Data & AI':   {'Fresher': (4, 8),    '0-2 years': (6, 12),  '2-4 years': (12, 20), '5+ years': (20, 40), 'Not specified': (6, 15)},
}


def generate_salary(category, experience):
    cat      = _SALARY_MATRIX.get(category, _SALARY_MATRIX['Technology'])
    mn, mx   = cat.get(experience, cat.get('Not specified', (3, 8)))
    return f"₹{mn:.0f}L–{mx:.0f}L (estimated)", mn, mx


# ── role content templates ────────────────────────────────────
_ROLE_TEMPLATES = [
    (
        ['consultant', 'advisory', 'delivery', 'engagement', 'client', 'solutions architect'],
        [
            "Lead client engagement and deliver end-to-end IT consulting solutions.",
            "Analyse business requirements and map them to technology solutions.",
            "Manage project timelines, deliverables, and stakeholder expectations.",
            "Conduct workshops, demos, and training sessions for clients.",
            "Collaborate with onshore and offshore teams to ensure delivery quality.",
        ],
        [
            "Bachelor's/Master's in CS, Engineering, or related field.",
            "2+ years of IT consulting or solution delivery experience.",
            "Strong communication and presentation skills.",
            "Experience with Agile or Waterfall methodologies.",
        ],
        ["Consulting", "Stakeholder Management", "Agile", "Project Management", "Client Relations"],
    ),
    (
        ['sap', 'erp', 's4hana', 'abap', 'fiori'],
        [
            "Configure and implement SAP modules per client requirements.",
            "Translate business processes into SAP functional/technical specifications.",
            "Perform unit, integration, and user acceptance testing.",
            "Support go-live and post-production hyper-care phases.",
        ],
        [
            "Bachelor's in IT, Engineering, or Finance.",
            "2+ years of hands-on SAP implementation experience.",
            "Knowledge of SAP modules (FICO, MM, SD, HR, PP).",
        ],
        ["SAP", "ERP", "S/4HANA", "ABAP", "SAP FICO", "SAP MM"],
    ),
    (
        ['qa', 'quality assurance', 'testing', 'test engineer', 'automation', 'selenium'],
        [
            "Design, develop, and execute test plans, cases, and scripts.",
            "Perform functional, regression, and integration testing.",
            "Build and maintain automated test frameworks.",
            "Log and track defects in JIRA; work with developers on resolution.",
        ],
        [
            "Bachelor's in Computer Science or related field.",
            "1+ years of software testing experience.",
            "Proficiency in manual and automation testing.",
        ],
        ["Selenium", "JIRA", "TestNG", "Postman", "SQL", "Python/Java", "Agile"],
    ),
    (
        ['infrastructure', 'cloud', 'aws', 'azure', 'gcp', 'devops', 'sre', 'network'],
        [
            "Manage and maintain cloud/on-premise infrastructure environments.",
            "Monitor system health, availability, and performance proactively.",
            "Implement CI/CD pipelines and automate infrastructure provisioning.",
            "Respond to and resolve infrastructure incidents per SLA.",
        ],
        [
            "Bachelor's in Computer Science, IT, or related field.",
            "2+ years of cloud or infrastructure management experience.",
            "Hands-on experience with AWS/Azure/GCP.",
        ],
        ["AWS/Azure/GCP", "Linux", "Kubernetes", "Docker", "Terraform", "CI/CD"],
    ),
    (
        [
            'java', 'spring', 'microservices', 'backend', 'full stack', 'node',
            'python', 'software engineer', 'software developer', 'application developer',
        ],
        [
            "Design, develop, and maintain scalable backend services and APIs.",
            "Write clean, well-tested, and documented code.",
            "Participate in design reviews and architecture discussions.",
            "Optimise application performance and resolve production issues.",
        ],
        [
            "Bachelor's/Master's in Computer Science or related field.",
            "1+ years of software development experience.",
            "Proficiency in Java/Python/JavaScript or equivalent.",
            "Good understanding of OOP, data structures, and algorithms.",
        ],
        ["Java", "Spring Boot", "Python", "Node.js", "REST APIs", "SQL", "Git", "Agile"],
    ),
]

_GENERIC_TEMPLATE = (
    [
        "Deliver high-quality work on assigned projects within agreed timelines.",
        "Collaborate with cross-functional teams and stakeholders.",
        "Continuously improve processes and document learnings.",
        "Participate in Agile ceremonies — standups, planning, and retrospectives.",
    ],
    [
        "Bachelor's degree in a relevant field or equivalent practical experience.",
        "Strong analytical and problem-solving skills.",
        "Excellent verbal and written communication in English.",
    ],
    ["Communication", "Problem Solving", "Teamwork", "MS Office", "Client Management"],
)


def _match_template(text):
    t = text.lower()
    for kws, resp, req, skills in _ROLE_TEMPLATES:
        if any(kw in t for kw in kws):
            return resp, req, skills
    return _GENERIC_TEMPLATE


def enrich_job(job):
    ctx = f"{job.get('title', '')} {job.get('description', '')} {job.get('category', '')}"
    if not job.get('responsibilities'):
        resp, req, skills = _match_template(ctx)
        job['responsibilities'] = resp
    if not job.get('requirements'):
        _, req, _ = _match_template(ctx)
        job['requirements'] = req
    if not job.get('skills') or job['skills'] == []:
        _, _, skills = _match_template(ctx)
        job['skills'] = skills
    if job.get('min_salary') is None or job.get('max_salary') is None:
        cat      = job.get('category', 'Technology')
        exp      = job.get('experience', 'Not specified')
        txt, mn, mx = generate_salary(cat, exp)
        if not job.get('salary_text'):
            job['salary_text'] = txt
        job['min_salary'] = mn
        job['max_salary'] = mx
    return job


# ═══════════════════════════════════════════════════════════════
# COMPANY SCRAPERS
# ═══════════════════════════════════════════════════════════════

# ── 1. ACCENTURE ──────────────────────────────────────────────
def scrape_accenture(browser, limit):
    """
    Career page: https://www.accenture.com/in-en/careers/jobsearch
    Filters 0-2 and 2-4 years exp.
    Apply URL: https://www.accenture.com/in-en/careers/jobdetails?id=<ID>&title=<slug>
    """
    log.info("Scraping Accenture...")
    jobs = []
    page = new_page(browser)

    try:
        # Accenture uses a React app; filter by experience range via URL params
        for exp_max in ['2', '4']:
            if len(jobs) >= limit:
                break
            url = (
                "https://www.accenture.com/in-en/careers/jobsearch"
                f"?jk=&sb=1&vw=0&is_rj=0&ct=India&mn=0&mx={exp_max}&pg=1&n=20"
            )
            log.info(f"Accenture → {url}")
            if not safe_goto(page, url):
                continue

            # Wait for job cards to appear
            wait_for_any(page, [
                '[class*="JobCard"]',
                '[class*="job-card"]',
                '[data-test="job-list-item"]',
                'li[class*="result"]',
                '.cmp-teaser',
            ], timeout=15000)

            # Scroll down to trigger lazy load
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            s     = get_soup(page)
            cards = (
                s.select('[class*="JobCard"]')
                or s.select('[class*="job-card"]')
                or s.select('[data-test="job-list-item"]')
                or s.select('li[class*="result"]')
                or s.select('.cmp-teaser')
                or s.select('article')
            )
            log.info(f"Accenture exp_max={exp_max}: {len(cards)} cards")

            for card in cards:
                if len(jobs) >= limit:
                    break
                # Look for a link whose href contains jobdetails
                link = (
                    card.select_one('a[href*="jobdetails"]')
                    or card.select_one('a[href*="careers"]')
                    or card.select_one('a[href]')
                )
                if not link:
                    continue
                href = link.get('href', '')
                if href.startswith('/'):
                    href = 'https://www.accenture.com' + href
                if not href.startswith('http'):
                    continue

                title_el = (
                    card.select_one('[class*="title"]')
                    or card.select_one('h2')
                    or card.select_one('h3')
                    or link
                )
                title = title_el.get_text(strip=True) if title_el else ''
                if not title or len(title) < 3:
                    continue

                loc_el = card.select_one('[class*="location"]') or card.select_one('[class*="city"]')
                loc    = loc_el.get_text(strip=True) if loc_el else 'India'

                exp_el  = card.select_one('[class*="xp"]') or card.select_one('[class*="experience"]')
                exp_txt = exp_el.get_text(strip=True) if exp_el else ''

                jobs.append(_job_stub(title, 'Accenture', loc, href,
                                      experience=detect_experience(exp_txt or title)))
                log.info(f"  + Accenture: {title[:60]} | {href}")

            time.sleep(2)

    except Exception as e:
        log.error(f"Accenture error: {e}")
    finally:
        page.close()

    if not jobs:
        log.warning("Accenture: 0 real jobs found — using static fallback")
        for title, exp in [
            ("Custom Software Engineer",      "0-2 years"),
            ("Associate Software Engineer",   "Fresher"),
            ("Cloud Infrastructure Engineer", "0-2 years"),
            ("Data Engineer",                 "0-2 years"),
            ("QA Engineer",                   "0-2 years"),
        ]:
            if len(jobs) >= limit:
                break
            jobs.append(_job_stub(
                title, 'Accenture', 'India',
                f"https://www.accenture.com/in-en/careers/jobsearch?jk={quote_plus(title)}&ct=India",
                experience=exp,
            ))

    log.info(f"Accenture total: {len(jobs)}")
    return jobs[:limit]


# ── 2. TCS ────────────────────────────────────────────────────
def scrape_tcs(browser, limit):
    """
    Career page: https://ibegin.tcs.com/iBegin/jobs/search
    Apply URL: https://ibegin.tcs.com/iBegin/jobs/<JobCode>
    """
    log.info("Scraping TCS...")
    jobs = []
    page = new_page(browser)

    try:
        url = "https://ibegin.tcs.com/iBegin/jobs/search?searchType=1&location=India"
        log.info(f"TCS → {url}")
        if safe_goto(page, url):
            wait_for_any(page, [
                '[class*="job"]',
                'tr[class*="result"]',
                '[class*="jobRow"]',
                'table.tableResults',
                '.job-title',
            ], timeout=15000)
            time.sleep(2)

            s     = get_soup(page)
            cards = (
                s.select('tr[class*="result"]')
                or s.select('[class*="jobRow"]')
                or s.select('.job-item')
                or s.select('li[class*="job"]')
            )
            log.info(f"TCS: {len(cards)} cards")

            for card in cards:
                if len(jobs) >= limit:
                    break
                link     = card.select_one('a[href]')
                title_el = (
                    card.select_one('[class*="title"]')
                    or card.select_one('a')
                    or card.select_one('td')
                )
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 3:
                    continue
                href = link['href'] if link else ''
                if href and not href.startswith('http'):
                    href = 'https://ibegin.tcs.com' + href
                if not href:
                    href = 'https://ibegin.tcs.com/iBegin/jobs/search'
                loc_el = card.select_one('[class*="location"]') or card.select_one('td:nth-child(3)')
                loc    = loc_el.get_text(strip=True) if loc_el else 'India'
                jobs.append(_job_stub(title, 'TCS', loc, href))
                log.info(f"  + TCS: {title[:60]} | {href}")

    except Exception as e:
        log.error(f"TCS error: {e}")
    finally:
        page.close()

    if not jobs:
        log.warning("TCS: 0 real jobs — using static fallback")
        for title, exp in [
            ("TCS NQT — Engineering Trainee", "Fresher"),
            ("Assistant System Engineer",     "Fresher"),
            ("Systems Engineer",              "0-2 years"),
            ("IT Analyst",                    "2-4 years"),
            ("SAP Consultant",                "2-4 years"),
        ]:
            if len(jobs) >= limit:
                break
            jobs.append(_job_stub(
                title, 'TCS', 'Pan India',
                "https://ibegin.tcs.com/iBegin/jobs/search?searchType=1&location=India",
                experience=exp,
            ))

    log.info(f"TCS total: {len(jobs)}")
    return jobs[:limit]


# ── 3. WIPRO ──────────────────────────────────────────────────
def scrape_wipro(browser, limit):
    """
    Career page: https://careers.wipro.com/search/?q=&locationsearch=india&sortBy=date
    Apply URL: https://careers.wipro.com/job/<Title>/<JobCode>-en_US
    """
    log.info("Scraping Wipro...")
    jobs = []
    page = new_page(browser)

    try:
        base_url = (
            "https://careers.wipro.com/search/"
            "?q=&locationsearch=india&searchResultView=LIST&sortBy=date&pageNumber="
        )
        for pg in range(5):
            if len(jobs) >= limit:
                break
            url = base_url + str(pg)
            log.info(f"Wipro page {pg} → {url}")
            if not safe_goto(page, url):
                break

            wait_for_any(page, [
                'li.results-item',
                '[data-ph-at-id="job-item"]',
                '[class*="job-tile"]',
                'article[class*="job"]',
                '.job-listing',
            ], timeout=15000)

            # Scroll to load lazy results
            for _ in range(2):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)

            s     = get_soup(page)
            cards = (
                s.select('li.results-item')
                or s.select('[data-ph-at-id="job-item"]')
                or s.select('[class*="job-tile"]')
                or s.select('article[class*="job"]')
            )
            log.info(f"Wipro page {pg}: {len(cards)} cards")
            if not cards:
                break

            for card in cards:
                if len(jobs) >= limit:
                    break
                link = (
                    card.select_one('a[data-ph-at-id="job-title-link"]')
                    or card.select_one('a[href*="/job/"]')
                    or card.select_one('a[href]')
                )
                title_el = (
                    card.select_one('[data-ph-at-id="job-title"]')
                    or card.select_one('h2')
                    or card.select_one('h3')
                    or link
                )
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 3:
                    continue
                href = link['href'] if link else ''
                if href and not href.startswith('http'):
                    href = 'https://careers.wipro.com' + href
                if not href:
                    href = f"https://careers.wipro.com/search/?q={quote_plus(title)}&locationsearch=india"
                loc_el = (
                    card.select_one('[data-ph-at-id="job-location"]')
                    or card.select_one('[class*="location"]')
                )
                loc = loc_el.get_text(strip=True) if loc_el else 'India'
                jobs.append(_job_stub(title, 'Wipro', loc, href))
                log.info(f"  + Wipro: {title[:60]} | {href}")

            time.sleep(1.5)

    except Exception as e:
        log.error(f"Wipro error: {e}")
    finally:
        page.close()

    if not jobs:
        log.warning("Wipro: 0 real jobs — using static fallback")
        for title in [
            "Software Engineer",
            "Cloud Solutions Specialist",
            "IT Infrastructure Engineer",
            "Data Analyst",
            "DevOps Engineer",
        ]:
            if len(jobs) >= limit:
                break
            jobs.append(_job_stub(
                title, 'Wipro', 'India',
                f"https://careers.wipro.com/search/?q={quote_plus(title)}&locationsearch=india",
            ))

    log.info(f"Wipro total: {len(jobs)}")
    return jobs[:limit]


# ── 4. COGNIZANT ──────────────────────────────────────────────
def scrape_cognizant(browser, limit):
    """
    Career page: https://careers.cognizant.com/india-en/jobs/?keyword=&location=India&radius=100#results
    Apply URL: https://careers.cognizant.com/india-en/jobs/<ID>/<slug>/
    """
    log.info("Scraping Cognizant...")
    jobs = []
    page = new_page(browser)

    try:
        url = (
            "https://careers.cognizant.com/india-en/jobs/"
            "?keyword=&location=India&radius=100&pagesize=20#results"
        )
        log.info(f"Cognizant → {url}")
        if safe_goto(page, url):
            wait_for_any(page, [
                '[class*="job-result"]',
                '[class*="job-listing"]',
                '[class*="jobs-list"]',
                'li[class*="job"]',
                '.job-card',
                '[data-job-id]',
            ], timeout=20000)
            time.sleep(3)

            s     = get_soup(page)
            cards = (
                s.select('[class*="job-result-item"]')
                or s.select('[class*="job-listing-item"]')
                or s.select('li[class*="job"]')
                or s.select('[data-job-id]')
                or s.select('.job-card')
                or s.select('article')
            )
            log.info(f"Cognizant: {len(cards)} cards")

            for card in cards:
                if len(jobs) >= limit:
                    break
                link = (
                    card.select_one('a[href*="/jobs/"]')
                    or card.select_one('a[href]')
                )
                title_el = (
                    card.select_one('[class*="title"]')
                    or card.select_one('h2')
                    or card.select_one('h3')
                    or link
                )
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 3:
                    continue
                href = link['href'] if link else ''
                if href and not href.startswith('http'):
                    href = 'https://careers.cognizant.com' + href
                if not href:
                    href = (
                        "https://careers.cognizant.com/india-en/jobs/"
                        "?keyword=&location=India&radius=100#results"
                    )
                loc_el = card.select_one('[class*="location"]') or card.select_one('[class*="city"]')
                loc    = loc_el.get_text(strip=True) if loc_el else 'India'
                jobs.append(_job_stub(title, 'Cognizant', loc, href))
                log.info(f"  + Cognizant: {title[:60]} | {href}")

    except Exception as e:
        log.error(f"Cognizant error: {e}")
    finally:
        page.close()

    if not jobs:
        log.warning("Cognizant: 0 real jobs — using static fallback")
        for title, exp in [
            ("Technology Architect",  "5+ years"),
            ("Senior Consultant",     "5+ years"),
            ("Consultant",            "2-4 years"),
            ("Associate Consultant",  "0-2 years"),
            ("Technology Analyst",    "0-2 years"),
        ]:
            if len(jobs) >= limit:
                break
            jobs.append(_job_stub(
                title, 'Cognizant', 'India',
                (
                    "https://careers.cognizant.com/india-en/jobs/"
                    f"?keyword={quote_plus(title)}&location=India&radius=100#results"
                ),
                experience=exp,
            ))

    log.info(f"Cognizant total: {len(jobs)}")
    return jobs[:limit]


# ── 5. INFOSYS ────────────────────────────────────────────────
def scrape_infosys(browser, limit):
    """
    Career page: https://career.infosys.com/jobs?companyhiringtype=IL&countrycode=IN
    Filters 1-3 years experience.
    Apply URL: https://career.infosys.com/jobdesc?jobReferenceCode=INFSYS-EXTERNAL-<ID>&rc=0&jobType=normal
    """
    log.info("Scraping Infosys...")
    jobs = []
    page = new_page(browser)

    try:
        url = "https://career.infosys.com/jobs?companyhiringtype=IL&countrycode=IN"
        log.info(f"Infosys → {url}")
        if safe_goto(page, url):
            wait_for_any(page, [
                '[class*="job-card"]',
                '[class*="jobCard"]',
                '[class*="position-item"]',
                '.job-listing',
                '[data-jobid]',
            ], timeout=20000)
            time.sleep(3)

            s     = get_soup(page)
            cards = (
                s.select('[class*="job-card"]')
                or s.select('[class*="jobCard"]')
                or s.select('[class*="position-item"]')
                or s.select('[data-jobid]')
                or s.select('li[class*="job"]')
            )
            log.info(f"Infosys: {len(cards)} cards")

            for card in cards:
                if len(jobs) >= limit:
                    break
                link = (
                    card.select_one('a[href*="jobdesc"]')
                    or card.select_one('a[href*="jobReferenceCode"]')
                    or card.select_one('a[href]')
                )
                title_el = (
                    card.select_one('[class*="title"]')
                    or card.select_one('h2')
                    or card.select_one('h3')
                    or link
                )
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 3:
                    continue

                exp_el  = (
                    card.select_one('[class*="exp"]')
                    or card.select_one('[class*="experience"]')
                )
                exp_txt = exp_el.get_text(strip=True) if exp_el else ''
                exp     = detect_experience(exp_txt + ' ' + title)
                # Only keep <= 3 years experience
                if exp == '5+ years':
                    continue

                href = link['href'] if link else ''
                if href and not href.startswith('http'):
                    href = 'https://career.infosys.com' + href
                if not href:
                    href = "https://career.infosys.com/jobs?companyhiringtype=IL&countrycode=IN"

                loc_el = card.select_one('[class*="location"]') or card.select_one('[class*="city"]')
                loc    = loc_el.get_text(strip=True) if loc_el else 'India'
                jobs.append(_job_stub(title, 'Infosys', loc, href, experience=exp))
                log.info(f"  + Infosys: {title[:60]} | {href}")

    except Exception as e:
        log.error(f"Infosys error: {e}")
    finally:
        page.close()

    if not jobs:
        log.warning("Infosys: 0 real jobs — using static fallback")
        for title, exp in [
            ("Software Engineer",           "0-2 years"),
            ("Associate Software Engineer", "Fresher"),
            ("Systems Engineer",            "0-2 years"),
            ("Technology Analyst",          "2-4 years"),
            ("SAP Consultant",              "2-4 years"),
        ]:
            if len(jobs) >= limit:
                break
            jobs.append(_job_stub(
                title, 'Infosys', 'India',
                "https://career.infosys.com/jobs?companyhiringtype=IL&countrycode=IN",
                experience=exp,
            ))

    log.info(f"Infosys total: {len(jobs)}")
    return jobs[:limit]


# ── 6. CAPGEMINI ──────────────────────────────────────────────
def scrape_capgemini(browser, limit):
    """
    Career page: https://www.capgemini.com/careers/join-capgemini/job-search/?page=1&size=11&country_code=en-in
    Apply URL: https://www.capgemini.com/jobs/<id>-<slug>
    """
    log.info("Scraping Capgemini...")
    jobs = []
    page = new_page(browser)

    try:
        for pg in range(1, 6):
            if len(jobs) >= limit:
                break
            url = (
                "https://www.capgemini.com/careers/join-capgemini/job-search/"
                f"?page={pg}&size=11&country_code=en-in"
            )
            log.info(f"Capgemini page {pg} → {url}")
            if not safe_goto(page, url):
                break

            wait_for_any(page, [
                '[class*="job-card"]',
                '[class*="job-listing"]',
                '[class*="job-tile"]',
                'article[class*="job"]',
                '.jobs-list-item',
                '[class*="search-result"]',
            ], timeout=20000)
            time.sleep(2)

            s     = get_soup(page)
            cards = (
                s.select('[class*="job-card"]')
                or s.select('[class*="job-listing-item"]')
                or s.select('[class*="job-tile"]')
                or s.select('article[class*="job"]')
                or s.select('.jobs-list li')
                or s.select('[class*="search-result-item"]')
            )
            log.info(f"Capgemini page {pg}: {len(cards)} cards")
            if not cards:
                break

            for card in cards:
                if len(jobs) >= limit:
                    break
                link = (
                    card.select_one('a[href*="/jobs/"]')
                    or card.select_one('a[href*="capgemini.com"]')
                    or card.select_one('a[href]')
                )
                title_el = (
                    card.select_one('[class*="title"]')
                    or card.select_one('h2')
                    or card.select_one('h3')
                    or link
                )
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 3:
                    continue
                href = link['href'] if link else ''
                if href and not href.startswith('http'):
                    href = 'https://www.capgemini.com' + href
                if not href:
                    href = (
                        "https://www.capgemini.com/careers/join-capgemini/"
                        "job-search/?page=1&country_code=en-in"
                    )
                loc_el = card.select_one('[class*="location"]') or card.select_one('[class*="city"]')
                loc    = loc_el.get_text(strip=True) if loc_el else 'India'
                jobs.append(_job_stub(title, 'Capgemini', loc, href))
                log.info(f"  + Capgemini: {title[:60]} | {href}")

            time.sleep(1.5)

    except Exception as e:
        log.error(f"Capgemini error: {e}")
    finally:
        page.close()

    if not jobs:
        log.warning("Capgemini: 0 real jobs — using static fallback")
        for title, exp in [
            ("Senior Consultant",    "5+ years"),
            ("Consultant",           "2-4 years"),
            ("Associate Consultant", "0-2 years"),
            ("Solution Architect",   "5+ years"),
            ("DevOps Engineer",      "2-4 years"),
        ]:
            if len(jobs) >= limit:
                break
            jobs.append(_job_stub(
                title, 'Capgemini', 'India',
                "https://www.capgemini.com/careers/join-capgemini/job-search/?page=1&country_code=en-in",
                experience=exp,
            ))

    log.info(f"Capgemini total: {len(jobs)}")
    return jobs[:limit]


# ── 7. IBM ────────────────────────────────────────────────────
def scrape_ibm(browser, limit):
    """
    Career page: https://www.ibm.com/in-en/careers/search?field_keyword_18[0]=Entry%20Level&field_keyword_05[0]=India
    Apply URL: https://careers.ibm.com/en_US/careers/JobDetail?jobId=<ID>&source=WEB_Search_INDIA
    """
    log.info("Scraping IBM...")
    jobs = []
    page = new_page(browser)

    try:
        url = (
            "https://www.ibm.com/in-en/careers/search"
            "?field_keyword_18[0]=Entry%20Level&field_keyword_05[0]=India"
        )
        log.info(f"IBM → {url}")
        if safe_goto(page, url):
            wait_for_any(page, [
                '[class*="job-card"]',
                '[class*="bx--tile"]',
                '[class*="ibm-job"]',
                '.job-item',
                '[data-job-id]',
                '[class*="careers-search"]',
            ], timeout=20000)
            time.sleep(3)

            s     = get_soup(page)
            cards = (
                s.select('[class*="job-card"]')
                or s.select('[class*="bx--tile"]')
                or s.select('[data-job-id]')
                or s.select('.job-item')
                or s.select('[class*="ibm-job"]')
            )
            log.info(f"IBM: {len(cards)} cards")

            for card in cards:
                if len(jobs) >= limit:
                    break
                link = (
                    card.select_one('a[href*="JobDetail"]')
                    or card.select_one('a[href*="jobId"]')
                    or card.select_one('a[href]')
                )
                title_el = (
                    card.select_one('[class*="title"]')
                    or card.select_one('h2')
                    or card.select_one('h3')
                    or link
                )
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 3:
                    continue
                href = link['href'] if link else ''
                if href and not href.startswith('http'):
                    href = 'https://careers.ibm.com' + href
                # Ensure proper IBM job URL format
                jid_m = re.search(r'jobId=(\d+)', href)
                if jid_m:
                    href = (
                        f"https://careers.ibm.com/en_US/careers/JobDetail"
                        f"?jobId={jid_m.group(1)}&source=WEB_Search_INDIA"
                    )
                if not href or not href.startswith('http'):
                    href = (
                        "https://www.ibm.com/in-en/careers/search"
                        "?field_keyword_18[0]=Entry%20Level&field_keyword_05[0]=India"
                    )
                loc_el = card.select_one('[class*="location"]') or card.select_one('[class*="city"]')
                loc    = loc_el.get_text(strip=True) if loc_el else 'India'
                jobs.append(_job_stub(title, 'IBM', loc, href))
                log.info(f"  + IBM: {title[:60]} | {href}")

    except Exception as e:
        log.error(f"IBM error: {e}")
    finally:
        page.close()

    if not jobs:
        log.warning("IBM: 0 real jobs — using static fallback")
        for title, exp in [
            ("Software Engineer",               "0-2 years"),
            ("Cloud Infrastructure Specialist", "2-4 years"),
            ("Data Scientist",                  "2-4 years"),
            ("DevOps Engineer",                 "2-4 years"),
            ("Solutions Architect",             "5+ years"),
        ]:
            if len(jobs) >= limit:
                break
            jobs.append(_job_stub(
                title, 'IBM', 'India',
                (
                    "https://www.ibm.com/in-en/careers/search"
                    "?field_keyword_18[0]=Entry%20Level&field_keyword_05[0]=India"
                ),
                experience=exp,
            ))

    log.info(f"IBM total: {len(jobs)}")
    return jobs[:limit]


# ── 8. DELOITTE ───────────────────────────────────────────────
def scrape_deloitte(browser, limit):
    """
    Career page: https://southasiacareers.deloitte.com/go/Deloitte-India/718244/?q=&sortColumn=referencedate&sortDirection=desc
    Only includes jobs with experience <= 3 years (skips 5+ years roles).
    """
    log.info("Scraping Deloitte...")
    jobs = []
    page = new_page(browser)

    base_url = (
        "https://southasiacareers.deloitte.com/go/Deloitte-India/718244/"
        "?q=&sortColumn=referencedate&sortDirection=desc"
    )

    try:
        for pg in range(1, 6):
            if len(jobs) >= limit:
                break
            url = base_url if pg == 1 else f"{base_url}&start={(pg - 1) * 10}"
            log.info(f"Deloitte page {pg} → {url}")
            if not safe_goto(page, url):
                break

            wait_for_any(page, [
                '[class*="job"]',
                '[class*="result-item"]',
                '[class*="search-result"]',
                'li[class*="job"]',
                '.job-listing',
            ], timeout=20000)
            time.sleep(2)

            s     = get_soup(page)
            cards = (
                s.select('[class*="job-result"]')
                or s.select('[class*="result-item"]')
                or s.select('li[class*="job"]')
                or s.select('[class*="search-result-item"]')
                or s.select('article')
            )
            log.info(f"Deloitte page {pg}: {len(cards)} cards")
            if not cards:
                break

            for card in cards:
                if len(jobs) >= limit:
                    break
                link     = card.select_one('a[href]')
                title_el = (
                    card.select_one('[class*="title"]')
                    or card.select_one('h2')
                    or card.select_one('h3')
                    or link
                )
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 3:
                    continue

                exp = detect_experience(title)
                if exp == '5+ years':
                    continue   # skip senior roles per spec

                href = link['href'] if link else ''
                if href and not href.startswith('http'):
                    href = 'https://southasiacareers.deloitte.com' + href
                if not href:
                    href = base_url
                loc_el = card.select_one('[class*="location"]')
                loc    = loc_el.get_text(strip=True) if loc_el else 'India'
                jobs.append(_job_stub(title, 'Deloitte', loc, href, experience=exp))
                log.info(f"  + Deloitte: {title[:60]} | {href}")

            time.sleep(1.5)

    except Exception as e:
        log.error(f"Deloitte error: {e}")
    finally:
        page.close()

    if not jobs:
        log.warning("Deloitte: 0 real jobs — using static fallback")
        for title, exp in [
            ("Technology Analyst",   "0-2 years"),
            ("Business Analyst",     "0-2 years"),
            ("Consultant",           "2-4 years"),
            ("Associate Consultant", "0-2 years"),
        ]:
            if len(jobs) >= limit:
                break
            jobs.append(_job_stub(
                title, 'Deloitte', 'India',
                base_url,
                experience=exp,
            ))

    log.info(f"Deloitte total: {len(jobs)}")
    return jobs[:limit]


# ── 9. TECH MAHINDRA ──────────────────────────────────────────
def scrape_tech_mahindra(browser, limit):
    """
    Career page: https://careers.techmahindra.com/JobSearch.aspx
    Apply URL: https://careers.techmahindra.com/JobDetails.aspx?JobCode=<encoded>&IndustryType=<encoded>
    """
    log.info("Scraping Tech Mahindra...")
    jobs = []
    page = new_page(browser)

    try:
        url = "https://careers.techmahindra.com/JobSearch.aspx"
        log.info(f"Tech Mahindra → {url}")
        if safe_goto(page, url, wait='domcontentloaded'):
            wait_for_any(page, [
                'a[href*="JobDetails"]',
                'a[href*="jobdetails"]',
                '[class*="job"]',
                'table.tableResults',
                'tr[class*="result"]',
            ], timeout=20000)
            time.sleep(3)

            s = get_soup(page)
            # Tech Mahindra renders direct anchor links to JobDetails
            job_links = (
                s.select('a[href*="JobDetails.aspx"]')
                or s.select('a[href*="jobdetails"]')
            )
            log.info(f"Tech Mahindra: {len(job_links)} job links")

            seen = set()
            for link in job_links:
                if len(jobs) >= limit:
                    break
                href = link.get('href', '')
                if href and not href.startswith('http'):
                    href = 'https://careers.techmahindra.com/' + href.lstrip('/')
                if not href or href in seen:
                    continue
                seen.add(href)

                title = link.get_text(strip=True)
                if not title or len(title) < 3:
                    # check parent row/cell
                    parent = link.find_parent(['td', 'tr', 'div', 'li'])
                    if parent:
                        title = parent.get_text(strip=True)[:120].split('\n')[0].strip()
                if not title or len(title) < 3:
                    continue

                parent = link.find_parent(['tr', 'li', 'div'])
                loc    = 'India'
                if parent:
                    loc_el = (
                        parent.select_one('[class*="location"]')
                        or parent.select_one('td:nth-child(2)')
                    )
                    if loc_el:
                        loc = loc_el.get_text(strip=True)

                jobs.append(_job_stub(title, 'Tech Mahindra', loc, href))
                log.info(f"  + TechM: {title[:60]} | {href}")

    except Exception as e:
        log.error(f"Tech Mahindra error: {e}")
    finally:
        page.close()

    if not jobs:
        log.warning("Tech Mahindra: 0 real jobs — using static fallback")
        for title, exp in [
            ("Software Engineer",        "2-4 years"),
            ("DevOps Engineer",          "2-4 years"),
            ("Senior Software Engineer", "5+ years"),
            ("Cloud Architect",          "5+ years"),
            ("Technical Lead",           "5+ years"),
        ]:
            if len(jobs) >= limit:
                break
            jobs.append(_job_stub(
                title, 'Tech Mahindra', 'India',
                "https://careers.techmahindra.com/JobSearch.aspx",
                experience=exp,
            ))

    log.info(f"Tech Mahindra total: {len(jobs)}")
    return jobs[:limit]


# ── 10. LTIMINDTREE ───────────────────────────────────────────
def scrape_ltimindtree(browser, limit):
    """
    Career pages (by exp year):
      exp=0: https://ltimindtree.ripplehire.com/candidate/?token=xviyQvbnyYZdGtozXoNm&lang=en&source=CAREERSITE#list/geo=India&exp=0
      exp=1/2/3: same with exp=N
    Apply URL: https://ltimindtree.ripplehire.com/candidate/?token=...#detail/job/<jobId>
    """
    log.info("Scraping LTIMindtree...")
    jobs    = []
    TOKEN   = "xviyQvbnyYZdGtozXoNm"
    BASE    = f"https://ltimindtree.ripplehire.com/candidate/?token={TOKEN}&lang=en&source=CAREERSITE"
    EXP_MAP = {0: 'Fresher', 1: '0-2 years', 2: '0-2 years', 3: '2-4 years'}
    page    = new_page(browser)

    try:
        for exp_yr in [0, 1, 2, 3]:
            if len(jobs) >= limit:
                break
            url = f"{BASE}#list/geo=India&exp={exp_yr}"
            log.info(f"LTIMindtree exp={exp_yr} → {url}")
            if not safe_goto(page, url):
                continue

            # RippleHire is fully client-side rendered
            found = wait_for_any(page, [
                '[class*="job-card"]',
                '[class*="position-card"]',
                '[class*="job-item"]',
                '.job-list-item',
                '[data-job-id]',
                '[class*="rh-job"]',
                '.rh-card',
                '[class*="card"]',
            ], timeout=20000)

            if not found:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3)
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(2)

            s = get_soup(page)

            # ── Attempt 1: extract from embedded JS state ──
            for script in s.find_all('script'):
                txt = script.string or ''
                if 'jobId' not in txt and 'job_id' not in txt:
                    continue
                # Pattern: {"jobId":123456,"jobTitle":"Something"}
                for m in re.finditer(
                    r'"jobId"\s*:\s*(\d+).*?"jobTitle"\s*:\s*"([^"]+)"',
                    txt,
                ):
                    if len(jobs) >= limit:
                        break
                    jid, jtitle = m.group(1), m.group(2)
                    apply_url   = f"{BASE}#detail/job/{jid}"
                    jobs.append(_job_stub(
                        jtitle, 'LTIMindtree', 'India', apply_url,
                        experience=EXP_MAP.get(exp_yr, 'Not specified'),
                    ))
                    log.info(f"  + LTIMindtree (JS): {jtitle[:60]} | {apply_url}")

            if len(jobs) >= limit:
                break

            # ── Attempt 2: HTML card extraction ──
            cards = (
                s.select('[class*="job-card"]')
                or s.select('[class*="position-card"]')
                or s.select('[class*="rh-card"]')
                or s.select('[data-job-id]')
                or s.select('[class*="job-item"]')
                or s.select('li[class*="job"]')
            )
            log.info(f"LTIMindtree exp={exp_yr}: {len(cards)} HTML cards")

            for card in cards:
                if len(jobs) >= limit:
                    break
                job_id = (
                    card.get('data-job-id')
                    or card.get('data-id')
                    or (card.get('id', '') or '').replace('job-', '')
                )
                link     = card.select_one('a[href]')
                title_el = (
                    card.select_one('[class*="title"]')
                    or card.select_one('h2')
                    or card.select_one('h3')
                    or link
                )
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 3:
                    continue

                if job_id and str(job_id).isdigit():
                    apply_url = f"{BASE}#detail/job/{job_id}"
                elif link:
                    h = link.get('href', '')
                    apply_url = h if h.startswith('http') else BASE + h
                else:
                    apply_url = f"{BASE}#list/geo=India&exp={exp_yr}"

                loc_el = card.select_one('[class*="location"]') or card.select_one('[class*="city"]')
                loc    = loc_el.get_text(strip=True) if loc_el else 'India'
                jobs.append(_job_stub(
                    title, 'LTIMindtree', loc, apply_url,
                    experience=EXP_MAP.get(exp_yr, 'Not specified'),
                ))
                log.info(f"  + LTIMindtree: {title[:60]} | {apply_url}")

            time.sleep(2)

    except Exception as e:
        log.error(f"LTIMindtree error: {e}")
    finally:
        page.close()

    if not jobs:
        log.warning("LTIMindtree: 0 real jobs — using static fallback")
        for title, exp, exp_yr in [
            ("Software Engineer",        "0-2 years", 1),
            ("Senior Software Engineer", "5+ years",  3),
            ("DevOps Engineer",          "2-4 years", 2),
            ("Cloud Architect",          "5+ years",  3),
            ("Technical Lead",           "5+ years",  3),
        ]:
            if len(jobs) >= limit:
                break
            jobs.append(_job_stub(
                title, 'LTIMindtree', 'India',
                f"{BASE}#list/geo=India&exp={exp_yr}",
                experience=exp,
            ))

    log.info(f"LTIMindtree total: {len(jobs)}")
    return jobs[:limit]


# ═══════════════════════════════════════════════════════════════
# FEATURED ROTATION
# ═══════════════════════════════════════════════════════════════

def rotate_featured_jobs(db, newly_inserted_ids):
    try:
        log.info("[FEATURED] Rotating featured jobs (4 random from service-based)...")
        service_companies = [
            'Accenture', 'TCS', 'Wipro', 'Cognizant', 'Infosys',
            'Capgemini', 'IBM', 'Deloitte', 'Tech Mahindra', 'LTIMindtree',
        ]
        for company in service_companies:
            db.table('jobs').update({'is_featured': False}).eq('company', company).execute()

        if newly_inserted_ids:
            chosen = random.sample(newly_inserted_ids, min(4, len(newly_inserted_ids)))
        else:
            result  = (
                db.table('jobs')
                .select('id')
                .in_('company', service_companies)
                .eq('is_active', True)
                .execute()
            )
            all_ids = [r['id'] for r in result.data]
            chosen  = random.sample(all_ids, min(4, len(all_ids))) if all_ids else []

        for jid in chosen:
            db.table('jobs').update({'is_featured': True}).eq('id', jid).execute()
        log.info(f"[FEATURED] Done: {len(chosen)} jobs set to featured.")
    except Exception as e:
        log.error(f"Featured rotation error: {e}")


# ═══════════════════════════════════════════════════════════════
# DATABASE INSERT
# ═══════════════════════════════════════════════════════════════

def post_jobs_to_supabase(jobs, dry_run=False):
    if dry_run:
        log.info(f"[DRY RUN] Would process {len(jobs)} jobs:")
        for j in jobs:
            print(
                f"  → {j['title']} @ {j['company']} "
                f"| {j.get('location')} | {j.get('experience')}"
            )
            print(f"     apply_url: {j.get('apply_url')}")
        return 0, []

    if not SUPABASE_URL or not SUPABASE_KEY:
        log.error("Supabase credentials missing.")
        return 0, []

    from supabase import create_client
    db       = create_client(SUPABASE_URL, SUPABASE_KEY)
    inserted = 0
    skipped  = 0
    inserted_ids = []

    for job in jobs:
        job   = enrich_job(job)
        title = (job.get('title') or '').strip()
        if not title or len(title) < 3 or not job.get('apply_url'):
            continue
        try:
            exists = (
                db.table('jobs')
                .select('id')
                .eq('title',   title[:200])
                .eq('company', (job.get('company', ''))[:200])
                .execute()
            )
            if exists.data:
                skipped += 1
                continue

            views  = job.get('views') or random_views()
            result = db.table('jobs').insert({
                'title':            title[:200],
                'company':          (job.get('company', ''))[:200],
                'logo_url':         job.get('logo_url'),
                'location':         (job.get('location', 'India'))[:200],
                'work_mode':        job.get('work_mode', 'On-site'),
                'job_type':         job.get('job_type', 'Full-time'),
                'experience':       (job.get('experience', 'Not specified'))[:100],
                'salary_text':      job.get('salary_text'),
                'salary_min':       job.get('min_salary'),
                'salary_max':       job.get('max_salary'),
                'description':      (job.get('description', ''))[:3000],
                'responsibilities': job.get('responsibilities', []),
                'requirements':     job.get('requirements', []),
                'skills':           job.get('skills', []),
                'apply_url':        (job.get('apply_url', ''))[:500],
                'apply_source':     job.get('apply_source', 'Company'),
                'category':         job.get('category', 'Technology'),
                'is_featured':      False,
                'is_active':        True,
                'views':            views,
                'posted_at':        datetime.now(timezone.utc).isoformat(),
            }).execute()

            if result.data:
                inserted += 1
                inserted_ids.append(result.data[0]['id'])
                log.info(f"[INSERT] {title} @ {job.get('company')} | views={views}")
            time.sleep(0.15)

        except Exception as e:
            log.error(f"Insert error for '{title}': {e}")

    log.info(f"\n{'=' * 50}")
    log.info(f"[RESULT] Inserted: {inserted}  |  Skipped: {skipped}  |  Total: {len(jobs)}")
    rotate_featured_jobs(db, inserted_ids)
    return inserted, inserted_ids


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

COMPANY_MAP = {
    'accenture':    scrape_accenture,
    'tcs':          scrape_tcs,
    'wipro':        scrape_wipro,
    'cognizant':    scrape_cognizant,
    'infosys':      scrape_infosys,
    'capgemini':    scrape_capgemini,
    'ibm':          scrape_ibm,
    'deloitte':     scrape_deloitte,
    'techmahindra': scrape_tech_mahindra,
    'ltimindtree':  scrape_ltimindtree,
}


def main():
    parser = argparse.ArgumentParser(
        description='DayDreamer — Service-Based Scraper v5 (Playwright)'
    )
    parser.add_argument(
        '--source', default='all',
        choices=['all'] + list(COMPANY_MAP.keys()),
        help='Which company to scrape (default: all)',
    )
    parser.add_argument('--limit',   type=int, default=50, help='Max jobs per company')
    parser.add_argument('--dry-run', action='store_true',  help='Print without DB insert')
    args = parser.parse_args()

    log.info(
        f"[START] Service-Based Scraper v5 | "
        f"source={args.source} | limit={args.limit} | "
        f"{'DRY RUN' if args.dry_run else 'LIVE'}"
    )
    log.info(f"[DATE] Today: {TODAY} | Cutoff: {YESTERDAY}")
    log.info('=' * 60)

    pw, browser = get_browser()
    all_jobs    = []

    try:
        if args.source == 'all':
            for name, fn in COMPANY_MAP.items():
                log.info(f"\n── {name.upper()} ──────────")
                all_jobs += fn(browser, args.limit)
                time.sleep(2)
        else:
            fn        = COMPANY_MAP[args.source]
            all_jobs += fn(browser, args.limit)
    finally:
        browser.close()
        pw.stop()

    log.info(f"\n[STATS] Total scraped: {len(all_jobs)} jobs")

    if not all_jobs:
        log.warning("No jobs found at all.")
        return

    inserted, _ = post_jobs_to_supabase(all_jobs, dry_run=args.dry_run)

    if not args.dry_run and inserted > 0:
        hook = os.environ.get('VERCEL_DEPLOY_HOOK_URL')
        if hook:
            try:
                requests.post(hook, timeout=10)
                log.info("[DEPLOY] Vercel redeploy triggered!")
            except Exception as e:
                log.warning(f"Vercel hook error: {e}")

    log.info("[DONE] All operations completed!")


if __name__ == '__main__':
    main()