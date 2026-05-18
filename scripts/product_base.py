#!/usr/bin/env python3
"""
DayDreamer — Product-Based Company Job Scraper
===============================================
Scrapes official career pages of top product-based companies.
All jobs posted TODAY are fetched (no keyword filtering).
Each job includes a direct, specific apply URL (not a search or home page).

Companies covered:
  1.  Google          — jobs.google.com (JSON API)
  2.  Amazon          — amazon.jobs (JSON API)
  3.  Microsoft       — careers.microsoft.com (JSON API)
  4.  Meta (Facebook) — metacareers.com (JSON API)
  5.  Apple           — jobs.apple.com (JSON API)
  6.  Netflix         — jobs.netflix.com (Lever ATS)
  7.  Atlassian       — jobs.lever.co/atlassian (Lever ATS)
  8.  Stripe          — stripe.com/jobs (Lever ATS)
  9.  Airbnb          — careers.airbnb.com (Greenhouse ATS)
  10. Spotify         — lifeatspotify.com (Greenhouse ATS)
  11. Salesforce      — salesforce.wd12.myworkdayjobs.com (Workday)
  12. Adobe           — careers.adobe.com (Workday)
  13. Uber            — uber.com/careers (Greenhouse ATS)
  14. LinkedIn        — careers.linkedin.com (direct HTML)
  15. Twitter/X       — jobs.lever.co/twitter (Lever ATS)
  16. Dropbox         — jobs.dropbox.com (Lever ATS)
  17. Slack           — jobs.lever.co/slack (Lever ATS)
  18. GitHub          — boards.greenhouse.io/github (Greenhouse ATS)
  19. Figma           — jobs.lever.co/figma (Lever ATS)
  20. Notion          — boards.greenhouse.io/notion (Greenhouse ATS)

Usage:
  python product_company_scraper.py                  # run all companies
  python product_company_scraper.py --company google # only Google
  python product_company_scraper.py --dry-run        # print without inserting
  python product_company_scraper.py --limit 50       # max jobs per company
  python product_company_scraper.py --all-dates      # skip today-only filter

Requirements:
  pip install requests beautifulsoup4 python-dotenv supabase
"""

import os
import sys
import re
import time
import json
import random
import logging
import argparse
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client, Client

# ─────────────────────────────────────────────────────────────
# ENV LOADING
# ─────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────
# HTTP HEADERS
# ─────────────────────────────────────────────────────────────
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': 'application/json, text/html, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────
TODAY = datetime.now(timezone.utc).date()
YESTERDAY = TODAY - timedelta(days=1)

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def clean_html(raw: str) -> str:
    if not raw:
        return ''
    return BeautifulSoup(raw, 'html.parser').get_text(separator=' ', strip=True)[:3000]


def map_category(text: str) -> str:
    t = text.lower()
    if any(x in t for x in ['engineer', 'software', 'developer', 'python', 'java',
                              'react', 'devops', 'cloud', 'backend', 'frontend',
                              'fullstack', 'android', 'ios', 'sre', 'platform',
                              'infrastructure', 'security', 'data', 'ml', 'ai',
                              'machine learning', 'deep learning', 'nlp', 'llm']):
        return 'Technology'
    if any(x in t for x in ['design', 'ux', 'ui', 'figma', 'creative', 'graphic', 'visual']):
        return 'Design'
    if any(x in t for x in ['market', 'growth', 'content', 'seo', 'social media', 'digital']):
        return 'Marketing'
    if any(x in t for x in ['sales', 'business development', 'account executive']):
        return 'Sales'
    if any(x in t for x in ['hr', 'human resource', 'people', 'recruit', 'talent']):
        return 'HR & Talent'
    if any(x in t for x in ['finance', 'account', 'analyst', 'fintech']):
        return 'Finance'
    if any(x in t for x in ['product manager', 'product owner', 'product lead']):
        return 'Product'
    if any(x in t for x in ['data scientist', 'machine learning', 'nlp', 'llm']):
        return 'Data & AI'
    if any(x in t for x in ['legal', 'counsel', 'compliance', 'policy']):
        return 'Legal'
    if any(x in t for x in ['operations', 'ops', 'supply chain', 'logistics']):
        return 'Operations'
    return 'Technology'


def detect_work_mode(text: str) -> str:
    t = text.lower()
    if 'remote' in t:
        return 'Remote'
    if 'hybrid' in t:
        return 'Hybrid'
    return 'On-site'


def detect_experience(text: str) -> str:
    t = text.lower()
    if re.search(r'fresher|0\s*year|entry.?level|no experience|new grad|university graduate|recent graduate', t):
        return 'Fresher'
    if re.search(r'0.?2\s*year|0\s*to\s*2|1.?2\s*year', t):
        return '0-2 years'
    if re.search(r'2.?4\s*year|2\s*to\s*4|3.?5\s*year', t):
        return '2-4 years'
    if re.search(r'5\+\s*year|5\s*to\s*8|senior|lead|principal|staff', t):
        return '5+ years'
    if re.search(r'10\+|director|vp |vice president|head of', t):
        return '10+ years'
    return 'Not specified'


def random_views() -> int:
    return random.randint(200, 5000)


def is_today(date_str: Optional[str], all_dates: bool = False) -> bool:
    """
    Returns True if the date_str represents today or yesterday (to catch timezone edge cases).
    If all_dates=True, always returns True.
    """
    if all_dates:
        return True
    if not date_str:
        return True   # unknown date → include it
    try:
        # Try ISO format first
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        job_date = dt.date()
        return job_date >= YESTERDAY
    except Exception:
        pass
    # Try common formats
    for fmt in ('%Y-%m-%d', '%d %b %Y', '%B %d, %Y', '%Y/%m/%d'):
        try:
            dt = datetime.strptime(date_str[:20], fmt)
            return dt.date() >= YESTERDAY
        except Exception:
            continue
    return True   # can't parse → include


# ═══════════════════════════════════════════════════════════════
# SALARY MATRIX & ENRICHMENT (same as reference script)
# ═══════════════════════════════════════════════════════════════

_SALARY_MATRIX = {
    'Technology': {'Fresher': (3, 6), '0-2 years': (4, 8), '2-4 years': (8, 15), '5+ years': (15, 35), '10+ years': (30, 60), 'Not specified': (6, 15)},
    'Design':     {'Fresher': (2.5, 5), '0-2 years': (3.5, 7), '2-4 years': (6, 12), '5+ years': (12, 25), '10+ years': (20, 40), 'Not specified': (5, 12)},
    'Marketing':  {'Fresher': (2, 4), '0-2 years': (3, 6), '2-4 years': (5, 10), '5+ years': (10, 20), '10+ years': (15, 35), 'Not specified': (4, 10)},
    'Sales':      {'Fresher': (1.5, 3), '0-2 years': (2.5, 5), '2-4 years': (4, 8), '5+ years': (8, 18), '10+ years': (15, 30), 'Not specified': (4, 10)},
    'HR & Talent':{'Fresher': (2, 4), '0-2 years': (2.5, 5), '2-4 years': (4, 8), '5+ years': (8, 15), '10+ years': (12, 25), 'Not specified': (4, 9)},
    'Finance':    {'Fresher': (2.5, 5), '0-2 years': (3.5, 7), '2-4 years': (6, 12), '5+ years': (12, 25), '10+ years': (20, 40), 'Not specified': (5, 12)},
    'Product':    {'Fresher': (4, 7), '0-2 years': (6, 10), '2-4 years': (10, 18), '5+ years': (18, 40), '10+ years': (35, 70), 'Not specified': (8, 20)},
    'Data & AI':  {'Fresher': (4, 8), '0-2 years': (6, 12), '2-4 years': (12, 20), '5+ years': (20, 40), '10+ years': (35, 60), 'Not specified': (8, 20)},
    'Legal':      {'Fresher': (3, 6), '0-2 years': (5, 9), '2-4 years': (8, 15), '5+ years': (15, 30), '10+ years': (25, 50), 'Not specified': (6, 15)},
    'Operations': {'Fresher': (2, 4), '0-2 years': (3, 6), '2-4 years': (5, 10), '5+ years': (10, 20), '10+ years': (18, 35), 'Not specified': (4, 10)},
}

# For FAANG-tier companies, multiply salary by this factor
_PREMIUM_MULTIPLIER = {
    'Google': 2.5, 'Amazon': 2.2, 'Microsoft': 2.0, 'Meta': 2.8,
    'Apple': 2.5, 'Netflix': 3.0, 'Stripe': 2.5, 'Airbnb': 2.0,
    'Spotify': 1.8, 'Atlassian': 1.8, 'Salesforce': 1.8, 'Adobe': 1.7,
    'Uber': 2.0, 'LinkedIn': 2.0, 'Twitter': 1.8, 'Dropbox': 1.8,
    'Slack': 1.8, 'GitHub': 2.0, 'Figma': 2.0, 'Notion': 1.8,
}


def generate_salary(company: str, category: str, experience: str) -> tuple[Optional[str], Optional[float], Optional[float]]:
    cat = category or 'Technology'
    exp = experience or 'Not specified'
    if cat not in _SALARY_MATRIX:
        cat = 'Technology'
    if exp not in _SALARY_MATRIX[cat]:
        exp = 'Not specified'

    base_min, base_max = _SALARY_MATRIX[cat][exp]
    mult = _PREMIUM_MULTIPLIER.get(company, 1.5)

    min_sal = round(base_min * mult, 1)
    max_sal = round(base_max * mult, 1)
    salary_text = f"₹{min_sal:.0f}L–{max_sal:.0f}L (estimated)"
    return salary_text, min_sal, max_sal


# ═══════════════════════════════════════════════════════════════
# ROLE TEMPLATES — responsibilities / requirements / skills
# ═══════════════════════════════════════════════════════════════

_ROLE_TEMPLATES = [
    (
        ['data engineer', 'etl', 'pipeline', 'data infrastructure'],
        ["Design and maintain scalable ETL/ELT data pipelines across diverse sources.",
         "Build and manage data warehouse/lake solutions (Snowflake, BigQuery, Redshift).",
         "Implement data quality checks and monitoring for high reliability.",
         "Optimize queries and pipeline performance for scale and cost.",
         "Collaborate with stakeholders to translate data needs into technical solutions.",
         "Enforce data governance, security, and privacy standards."],
        ["Bachelor's/Master's in CS, Engineering, or related field.",
         "2+ years building production data pipelines.",
         "Proficiency in Python and SQL.",
         "Experience with cloud platforms (AWS, GCP, or Azure).",
         "Familiarity with orchestration tools like Airflow or Prefect."],
        ["Python", "SQL", "Apache Spark", "Airflow", "Kafka", "Snowflake", "BigQuery", "dbt", "AWS/GCP/Azure"],
    ),
    (
        ['data scientist', 'machine learning', 'ml engineer', 'deep learning', 'nlp', 'llm', 'ai engineer', 'research scientist'],
        ["Develop and deploy ML models solving real-world product and business problems.",
         "Conduct exploratory data analysis and feature engineering on large datasets.",
         "Evaluate models using rigorous metrics, iterate based on offline and online experiments.",
         "Collaborate with product and engineering teams to integrate ML into production.",
         "Publish and present research findings internally and externally.",
         "Monitor model performance and retrain as data distributions shift."],
        ["Bachelor's/Master's/PhD in Statistics, Math, CS, or related field.",
         "Strong Python and ML library proficiency (scikit-learn, TensorFlow, PyTorch).",
         "Experience with large-scale data processing (Spark, BigQuery).",
         "Solid understanding of statistical modelling and A/B experimentation.",
         "Excellent communication skills with both technical and non-technical audiences."],
        ["Python", "TensorFlow", "PyTorch", "scikit-learn", "SQL", "Spark", "MLflow", "Docker", "Kubernetes"],
    ),
    (
        ['frontend', 'react', 'angular', 'vue', 'ui developer', 'front end', 'web developer'],
        ["Build responsive, accessible, performant web UIs using modern frameworks.",
         "Collaborate with designers to implement pixel-perfect, delightful experiences.",
         "Write clean, reusable, well-tested component code with strong documentation.",
         "Integrate REST/GraphQL APIs and manage application state at scale.",
         "Lead front-end architecture decisions and establish team best practices.",
         "Continuously improve web performance, Core Web Vitals, and accessibility scores."],
        ["Bachelor's in CS or equivalent practical experience.",
         "3+ years of professional front-end development.",
         "Expert knowledge of JavaScript/TypeScript and React (or Angular/Vue).",
         "Experience with state management, testing (Jest, Cypress), and CI/CD.",
         "Strong understanding of web performance, accessibility (WCAG), and cross-browser compatibility."],
        ["React", "TypeScript", "JavaScript", "HTML5", "CSS3", "Redux", "GraphQL", "Jest", "Webpack"],
    ),
    (
        ['software engineer', 'backend', 'node', 'django', 'spring', 'golang', 'java', 'python developer', 'full stack', 'fullstack'],
        ["Design and build scalable, reliable backend services and APIs used by millions.",
         "Write clean, efficient, well-tested code with emphasis on maintainability.",
         "Collaborate with product managers and designers to shape feature requirements.",
         "Lead system design discussions and contribute to architectural decisions.",
         "Identify, debug, and resolve complex production issues.",
         "Mentor junior engineers and uphold high code quality through reviews."],
        ["Bachelor's/Master's in CS, Engineering, or related field.",
         "3+ years of software engineering experience.",
         "Proficiency in at least one backend language (Python, Java, Go, Node.js).",
         "Strong understanding of distributed systems, databases, and API design.",
         "Experience with cloud platforms and containerization (Docker, Kubernetes)."],
        ["Python/Java/Go/Node.js", "PostgreSQL", "REST/gRPC APIs", "Docker", "Kubernetes", "Redis", "Kafka", "AWS/GCP"],
    ),
    (
        ['devops', 'sre', 'site reliability', 'platform engineer', 'cloud engineer', 'infrastructure'],
        ["Design and manage CI/CD pipelines enabling continuous, reliable software delivery.",
         "Provision and maintain cloud infrastructure using Infrastructure-as-Code (Terraform).",
         "Define and maintain SLOs/SLAs; respond to and lead incident response.",
         "Automate operational toil and drive engineering efficiency across teams.",
         "Manage container orchestration platforms (Kubernetes/ECS) at scale.",
         "Champion security, compliance, and cost optimization across infrastructure."],
        ["3+ years in DevOps, SRE, or platform engineering.",
         "Strong Linux/Unix systems administration background.",
         "Expert knowledge of Kubernetes and Docker.",
         "Proficiency with at least one major cloud provider (AWS, GCP, or Azure).",
         "Scripting proficiency in Python and/or Bash.",
         "Experience with observability tooling (Prometheus, Grafana, Datadog)."],
        ["Kubernetes", "Terraform", "Docker", "AWS/GCP/Azure", "CI/CD", "Prometheus", "Grafana", "Python", "Bash"],
    ),
    (
        ['security', 'cyber', 'appsec', 'infosec', 'penetration'],
        ["Identify, assess, and remediate security vulnerabilities across products and infrastructure.",
         "Conduct threat modelling, penetration testing, and security code reviews.",
         "Build and maintain security tooling, automation, and detection pipelines.",
         "Partner with engineering teams to embed security into the SDLC.",
         "Respond to security incidents and lead post-incident reviews.",
         "Develop and deliver security awareness training across the organization."],
        ["Bachelor's in CS, Cybersecurity, or related field.",
         "3+ years of hands-on security engineering experience.",
         "Experience with penetration testing, threat modelling, and vulnerability management.",
         "Familiarity with security frameworks (SOC2, ISO 27001, NIST).",
         "Strong scripting skills (Python, Bash) and familiarity with cloud security."],
        ["Penetration Testing", "SIEM", "AWS Security", "Python", "Threat Modelling", "OWASP", "Zero Trust", "SOC2"],
    ),
    (
        ['product manager', 'product owner', 'pm '],
        ["Define the product vision, strategy, and roadmap aligned to company goals.",
         "Gather and prioritize requirements from customers, data, and stakeholders.",
         "Write detailed PRDs and user stories; partner with engineering and design.",
         "Drive go-to-market planning and coordinate cross-functional launches.",
         "Track product KPIs, design experiments, and iterate based on insights.",
         "Advocate for the customer while balancing business and technical constraints."],
        ["Bachelor's/MBA in Business, Engineering, or related field.",
         "4+ years of product management experience at a tech company.",
         "Strong analytical skills — comfortable with SQL, dashboards, and A/B testing.",
         "Excellent written and verbal communication and stakeholder management.",
         "Experience with Jira, Confluence, Figma, and product analytics tools."],
        ["Product Strategy", "Agile/Scrum", "JIRA", "Figma", "SQL", "A/B Testing", "Roadmapping", "Stakeholder Management"],
    ),
    (
        ['ux', 'ui', 'designer', 'design', 'figma', 'creative', 'visual'],
        ["Lead end-to-end design process from discovery and research to high-fidelity delivery.",
         "Conduct user research, usability testing, and synthesize insights into design decisions.",
         "Build and maintain cohesive design systems and component libraries.",
         "Collaborate closely with PMs and engineers to ship experiences users love.",
         "Ensure designs meet accessibility standards (WCAG AA).",
         "Present work clearly and iterate rapidly based on stakeholder feedback."],
        ["4+ years of professional UX/UI design experience.",
         "Strong portfolio demonstrating complex, end-to-end product design.",
         "Expert proficiency in Figma (or equivalent design tools).",
         "Experience with user research methodologies and usability testing.",
         "Understanding of front-end development constraints (HTML/CSS awareness)."],
        ["Figma", "User Research", "Prototyping", "Design Systems", "Usability Testing", "Accessibility", "Motion Design"],
    ),
    (
        ['marketing', 'growth', 'seo', 'content', 'digital marketing', 'brand', 'communications'],
        ["Develop and execute data-driven marketing campaigns across owned, paid, and earned channels.",
         "Own content strategy — blog, social, email, video — aligned to brand and growth goals.",
         "Analyze campaign performance and optimize based on KPIs and attribution data.",
         "Collaborate with product and design teams on GTM strategies and launches.",
         "Lead SEO/SEM strategy and manage advertising budgets efficiently.",
         "Build and maintain relationships with media, analysts, and influencers."],
        ["Bachelor's in Marketing, Communications, or related field.",
         "3+ years of B2B or B2C marketing experience at a tech company.",
         "Proficiency in marketing analytics tools (GA4, Mixpanel, Amplitude).",
         "Strong writing and storytelling skills.",
         "Experience with marketing automation platforms (HubSpot, Marketo)."],
        ["Content Marketing", "SEO/SEM", "Google Analytics", "HubSpot", "Social Media", "Email Marketing", "A/B Testing", "Figma/Canva"],
    ),
    (
        ['sales', 'account executive', 'account manager', 'business development'],
        ["Identify, prospect, and close new enterprise or SMB accounts.",
         "Manage the full sales cycle from outreach through contract execution.",
         "Build and maintain relationships with senior stakeholders and champions.",
         "Maintain accurate pipeline data and forecasts in CRM.",
         "Collaborate with solution engineering, marketing, and customer success teams.",
         "Meet and exceed monthly, quarterly, and annual revenue targets."],
        ["Bachelor's in Business or related field.",
         "3+ years of B2B SaaS sales experience.",
         "Proven track record of quota attainment.",
         "Strong negotiation, discovery, and objection-handling skills.",
         "Proficiency with Salesforce or HubSpot CRM."],
        ["Salesforce", "HubSpot", "B2B Enterprise Sales", "Negotiation", "Pipeline Management", "Solution Selling", "Executive Presence"],
    ),
    (
        ['hr', 'human resource', 'recruiter', 'talent acquisition', 'people ops', 'people partner'],
        ["Partner with business leaders to develop and execute talent strategies.",
         "Own end-to-end recruitment for technical and non-technical roles.",
         "Drive employee experience programs — onboarding, performance, engagement.",
         "Analyze workforce data to provide actionable people insights.",
         "Ensure compliance with local labor laws and HR policies.",
         "Champion diversity, equity, and inclusion initiatives."],
        ["Bachelor's in HR, Psychology, or related field.",
         "3+ years of HR or talent acquisition experience at a tech company.",
         "Strong data literacy — comfortable with HR analytics and dashboards.",
         "Experience with ATS and HRIS tools (Workday, Greenhouse, Lever).",
         "Excellent interpersonal and stakeholder management skills."],
        ["Talent Acquisition", "Workday", "Greenhouse/Lever", "HR Analytics", "DEI", "Onboarding", "Performance Management"],
    ),
    (
        ['finance', 'accounting', 'fp&a', 'financial analyst', 'controller', 'treasury'],
        ["Support financial planning, budgeting, and forecasting processes.",
         "Produce accurate and insightful financial reports for leadership.",
         "Partner with business units to drive financial discipline and performance.",
         "Manage month-end close, reconciliations, and audit processes.",
         "Develop financial models to evaluate business decisions and investments.",
         "Ensure compliance with GAAP/IFRS and internal controls."],
        ["Bachelor's/Master's in Finance, Accounting, or Economics; CPA/CFA preferred.",
         "3+ years of finance or accounting experience.",
         "Advanced proficiency in Excel/Sheets and financial modelling.",
         "Experience with ERP systems (NetSuite, SAP, Oracle).",
         "Strong analytical thinking and communication skills."],
        ["Financial Modelling", "Excel", "NetSuite/SAP", "FP&A", "GAAP/IFRS", "Tableau", "SQL", "Budget Management"],
    ),
]

_GENERIC_TEMPLATE = (
    ["Take end-to-end ownership of assigned projects and deliver high-quality outcomes.",
     "Collaborate across product, design, and engineering to drive meaningful impact.",
     "Continuously improve processes and share learnings with the broader team.",
     "Communicate progress and blockers clearly and proactively to stakeholders.",
     "Contribute to a diverse, inclusive, and high-performing team culture."],
    ["Bachelor's degree in a relevant field or equivalent practical experience.",
     "Strong problem-solving skills and ability to work in ambiguous, fast-paced environments.",
     "Excellent communication, collaboration, and stakeholder management skills.",
     "Self-motivated with a genuine growth mindset and passion for the domain.",
     "Prior internship or professional experience in a similar role."],
    ["Communication", "Problem Solving", "Cross-functional Collaboration", "Analytical Thinking", "Project Management"],
)


def _match_template(text: str):
    t = text.lower()
    for keywords, resp, req, skills in _ROLE_TEMPLATES:
        if any(kw in t for kw in keywords):
            return resp, req, skills
    return _GENERIC_TEMPLATE


def enrich_job(job: dict) -> dict:
    """Fill in missing structured fields and salary."""
    context = f"{job.get('title','')} {job.get('description','')} {job.get('category','')}"

    if not job.get('responsibilities'):
        resp, req, skills = _match_template(context)
        job['responsibilities'] = resp
    if not job.get('requirements'):
        _, req, _ = _match_template(context)
        job['requirements'] = req
    if not job.get('skills') or job.get('skills') == []:
        _, _, skills = _match_template(context)
        job['skills'] = skills

    # Salary
    if not job.get('min_salary') or not job.get('max_salary'):
        sal_text, min_sal, max_sal = generate_salary(
            job.get('company', ''),
            job.get('category', 'Technology'),
            job.get('experience', 'Not specified')
        )
        if not job.get('salary_text'):
            job['salary_text'] = sal_text
        job['min_salary'] = min_sal
        job['max_salary'] = max_sal

    return job


# ═══════════════════════════════════════════════════════════════
# SESSION WITH RETRY
# ═══════════════════════════════════════════════════════════════

def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s

SESSION = get_session()


def safe_get(url: str, params: dict = None, timeout: int = 20) -> Optional[requests.Response]:
    try:
        r = SESSION.get(url, params=params, timeout=timeout)
        if r.status_code == 200:
            return r
        log.debug(f"HTTP {r.status_code} for {url}")
    except Exception as e:
        log.debug(f"Request error {url}: {e}")
    return None


# ═══════════════════════════════════════════════════════════════
# SOURCE 1 — GOOGLE JOBS
# API: jobs.google.com (unofficial but stable JSON endpoint)
# Direct apply URL: https://careers.google.com/jobs/results/<id>/
# ═══════════════════════════════════════════════════════════════

def scrape_google(limit: int = 50, all_dates: bool = False) -> list:
    log.info("Scraping Google Careers...")
    jobs = []
    PAGE_SIZE = 20

    # Google uses a public JSON search endpoint
    base = "https://careers.google.com/api/v3/search/"
    page = 0

    while len(jobs) < limit:
        params = {
            'page': page,
            'page_size': PAGE_SIZE,
            'sort_by': 'date',
        }
        r = safe_get(base, params=params)
        if not r:
            break
        try:
            data = r.json()
        except Exception:
            break

        results = data.get('jobs', [])
        if not results:
            break

        for item in results:
            posted = item.get('modified', '') or item.get('publish_date', '')
            if not is_today(posted, all_dates):
                continue

            job_id   = item.get('id', '')
            title    = item.get('title', '').strip()
            company  = 'Google'
            locs     = item.get('locations', [])
            location = locs[0].get('display', 'Global') if locs else 'Global'
            desc     = clean_html(item.get('description', ''))

            qual_list = item.get('minimum_qualifications', [])
            pref_list = item.get('preferred_qualifications', [])
            resp_list = item.get('responsibilities', [])

            apply_url = f"https://careers.google.com/jobs/results/{job_id}/"

            jobs.append({
                'title':            title,
                'company':          company,
                'location':         location,
                'work_mode':        detect_work_mode(title + location + desc),
                'job_type':         'Full-time',
                'experience':       detect_experience(title + desc),
                'salary_text':      None,
                'description':      desc[:2000],
                'responsibilities': resp_list or [],
                'requirements':     qual_list + pref_list if (qual_list or pref_list) else [],
                'skills':           [],
                'apply_url':        apply_url,
                'apply_source':     'Google Careers',
                'category':         map_category(title + ' ' + item.get('category', '')),
                'is_featured':      False,
                'logo_url':         'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/120px-Google_2015_logo.svg.png',
            })

            if len(jobs) >= limit:
                break

        page += 1
        time.sleep(1)

    log.info(f"Google: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 2 — AMAZON JOBS
# API: amazon.jobs has a public JSON search API
# Direct apply URL: https://www.amazon.jobs/en/jobs/<id>/<slug>
# ═══════════════════════════════════════════════════════════════

def scrape_amazon(limit: int = 50, all_dates: bool = False) -> list:
    log.info("Scraping Amazon Jobs...")
    jobs = []
    offset = 0
    PAGE_SIZE = 25

    base = "https://www.amazon.jobs/en/search.json"

    while len(jobs) < limit:
        params = {
            'radius': '24km',
            'facets[]': [],
            'offset': offset,
            'result_limit': PAGE_SIZE,
            'sort': 'recent',
            'base_query': '',
            'loc_query': '',
        }
        r = safe_get(base, params=params)
        if not r:
            break
        try:
            data = r.json()
        except Exception:
            break

        results = data.get('jobs', [])
        if not results:
            break

        for item in results:
            posted = item.get('posted_date', '')
            if not is_today(posted, all_dates):
                continue

            job_id = str(item.get('id', ''))
            slug   = item.get('job_path', '').strip('/')
            title  = item.get('title', '').strip()

            if not title:
                continue

            locs     = item.get('normalized_location', '') or item.get('location', 'Global')
            desc     = clean_html(item.get('description', ''))
            team     = item.get('team', {}).get('label', '') if isinstance(item.get('team'), dict) else ''

            # Build direct job URL
            apply_url = f"https://www.amazon.jobs/en/jobs/{job_id}/{slug}" if slug else f"https://www.amazon.jobs/en/jobs/{job_id}"

            jobs.append({
                'title':            title,
                'company':          'Amazon',
                'location':         locs,
                'work_mode':        detect_work_mode(title + locs + desc),
                'job_type':         'Full-time',
                'experience':       detect_experience(title + desc),
                'salary_text':      None,
                'description':      desc[:2000],
                'responsibilities': [],
                'requirements':     [],
                'skills':           [],
                'apply_url':        apply_url,
                'apply_source':     'Amazon Jobs',
                'category':         map_category(title + ' ' + team),
                'is_featured':      False,
                'logo_url':         'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Amazon_logo.svg/120px-Amazon_logo.svg.png',
            })

            if len(jobs) >= limit:
                break

        offset += PAGE_SIZE
        time.sleep(1)

    log.info(f"Amazon: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 3 — MICROSOFT CAREERS
# API: gcsservices.careers.microsoft.com
# Direct apply URL: https://jobs.careers.microsoft.com/global/en/job/<id>/
# ═══════════════════════════════════════════════════════════════

def scrape_microsoft(limit: int = 50, all_dates: bool = False) -> list:
    log.info("Scraping Microsoft Careers...")
    jobs = []
    skip = 0
    PAGE_SIZE = 20

    base = "https://gcsservices.careers.microsoft.com/search/api/v1/search"

    while len(jobs) < limit:
        params = {
            'pg': (skip // PAGE_SIZE) + 1,
            'pgSz': PAGE_SIZE,
            'o': 'Newest',
            'flt': True,
        }
        r = safe_get(base, params=params)
        if not r:
            break
        try:
            data = r.json()
        except Exception:
            break

        results = data.get('operationResult', {}).get('result', {}).get('jobs', [])
        if not results:
            break

        for item in results:
            posted = item.get('postingDate', '')
            if not is_today(posted, all_dates):
                continue

            job_id = str(item.get('jobId', ''))
            title  = item.get('title', '').strip()
            if not title:
                continue

            location = item.get('primaryLocation', 'Global')
            desc     = clean_html(item.get('jobDescription', ''))
            dept     = item.get('category', '')

            apply_url = f"https://jobs.careers.microsoft.com/global/en/job/{job_id}/"

            jobs.append({
                'title':            title,
                'company':          'Microsoft',
                'location':         location,
                'work_mode':        detect_work_mode(title + location + desc),
                'job_type':         'Full-time',
                'experience':       detect_experience(title + desc),
                'salary_text':      None,
                'description':      desc[:2000],
                'responsibilities': [],
                'requirements':     [],
                'skills':           [],
                'apply_url':        apply_url,
                'apply_source':     'Microsoft Careers',
                'category':         map_category(title + ' ' + dept),
                'is_featured':      False,
                'logo_url':         'https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Microsoft_logo.svg/120px-Microsoft_logo.svg.png',
            })

            if len(jobs) >= limit:
                break

        skip += PAGE_SIZE
        time.sleep(1)

    log.info(f"Microsoft: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 4 — META CAREERS
# API: metacareers.com public JSON endpoint
# Direct apply URL: https://www.metacareers.com/jobs/<id>/
# ═══════════════════════════════════════════════════════════════

def scrape_meta(limit: int = 50, all_dates: bool = False) -> list:
    log.info("Scraping Meta Careers...")
    jobs = []

    # Meta's public GraphQL / REST search endpoint
    url = "https://www.metacareers.com/graphql"
    payload = {
        "operationName": "CareersJobSearchResultsQuery",
        "variables": {
            "search_input": {
                "q": "",
                "divisions": [],
                "offices": [],
                "roles": [],
                "leadership_levels": [],
                "teams": [],
                "is_remote": False,
                "page": 1,
                "results_per_page": min(limit, 50),
                "sort_by_new": True,
            }
        },
        "doc_id": "10002012750710278",   # stable public doc_id
    }

    try:
        r = SESSION.post(url, json=payload, timeout=20)
        data = r.json()
        results = (
            data.get('data', {})
                .get('job_search', {})
                .get('results', [])
        )

        for item in results:
            posted = item.get('apply_save_data', {}).get('created_time', '') or ''
            if not is_today(posted, all_dates):
                continue

            job_id   = str(item.get('id', ''))
            title    = item.get('title', '').strip()
            if not title:
                continue

            locations = item.get('locations', [])
            location  = ', '.join(l.get('city', '') for l in locations if l.get('city')) or 'Global'
            desc      = clean_html(item.get('description', ''))
            team      = item.get('teams', [{}])[0].get('name', '') if item.get('teams') else ''

            apply_url = f"https://www.metacareers.com/jobs/{job_id}/"

            jobs.append({
                'title':            title,
                'company':          'Meta',
                'location':         location,
                'work_mode':        detect_work_mode(title + location + desc),
                'job_type':         'Full-time',
                'experience':       detect_experience(title + desc),
                'salary_text':      None,
                'description':      desc[:2000],
                'responsibilities': [],
                'requirements':     [],
                'skills':           [],
                'apply_url':        apply_url,
                'apply_source':     'Meta Careers',
                'category':         map_category(title + ' ' + team),
                'is_featured':      False,
                'logo_url':         'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Meta_Platforms_Inc._logo.svg/120px-Meta_Platforms_Inc._logo.svg.png',
            })

            if len(jobs) >= limit:
                break

    except Exception as e:
        log.error(f"Meta error: {e}")

    log.info(f"Meta: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 5 — APPLE JOBS
# API: jobs.apple.com public JSON endpoint
# Direct apply URL: https://jobs.apple.com/en-us/details/<id>/
# ═══════════════════════════════════════════════════════════════

def scrape_apple(limit: int = 50, all_dates: bool = False) -> list:
    log.info("Scraping Apple Jobs...")
    jobs = []
    PAGE  = 1
    PER_P = 20

    base = "https://jobs.apple.com/api/role/search"

    while len(jobs) < limit:
        params = {
            'page': PAGE,
            'sort': 'newest',
            'key': '',
        }
        r = safe_get(base, params=params)
        if not r:
            break
        try:
            data = r.json()
        except Exception:
            break

        results = data.get('searchResults', [])
        if not results:
            break

        for item in results:
            posted = item.get('postingDate', '')
            if not is_today(posted, all_dates):
                continue

            job_id   = str(item.get('id', ''))
            title    = item.get('postingTitle', '').strip()
            if not title:
                continue

            location = item.get('locations', [{}])[0].get('name', 'Global') if item.get('locations') else 'Global'
            team     = item.get('team', {}).get('teamName', '') if item.get('team') else ''
            desc     = item.get('jobSummary', '') or f"{title} at Apple. Detailed description on apply page."

            apply_url = f"https://jobs.apple.com/en-us/details/{job_id}/"

            jobs.append({
                'title':            title,
                'company':          'Apple',
                'location':         location,
                'work_mode':        detect_work_mode(title + location + desc),
                'job_type':         'Full-time',
                'experience':       detect_experience(title + desc),
                'salary_text':      None,
                'description':      clean_html(desc)[:2000],
                'responsibilities': [],
                'requirements':     [],
                'skills':           [],
                'apply_url':        apply_url,
                'apply_source':     'Apple Jobs',
                'category':         map_category(title + ' ' + team),
                'is_featured':      False,
                'logo_url':         'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Apple_logo_black.svg/60px-Apple_logo_black.svg.png',
            })

            if len(jobs) >= limit:
                break

        PAGE += 1
        time.sleep(1)

    log.info(f"Apple: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# LEVER ATS — Generic fetcher
# GET https://api.lever.co/v0/postings/<slug>?mode=json
# Direct apply URL: item['hostedUrl']
# ═══════════════════════════════════════════════════════════════

def _scrape_lever(slug: str, company: str, logo_url: str = '', limit: int = 30, all_dates: bool = False) -> list:
    jobs = []
    url  = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    r    = safe_get(url)
    if not r:
        return jobs

    try:
        items = r.json()
        if not isinstance(items, list):
            return jobs
    except Exception:
        return jobs

    for item in items:
        posted = item.get('createdAt')
        # Lever uses ms epoch
        if posted and not all_dates:
            try:
                dt = datetime.fromtimestamp(int(posted) / 1000, tz=timezone.utc)
                if dt.date() < YESTERDAY:
                    continue
            except Exception:
                pass

        title = item.get('text', '').strip()
        if not title:
            continue

        location  = item.get('categories', {}).get('location', 'Global')
        team      = item.get('categories', {}).get('team', '')
        desc_raw  = item.get('descriptionPlain', '') or clean_html(item.get('description', ''))
        desc      = desc_raw[:2000]
        hosted    = item.get('hostedUrl', f'https://jobs.lever.co/{slug}')

        # Parse lists from Lever's structured lists
        resp_items = []
        req_items  = []
        for lst in item.get('lists', []):
            name  = (lst.get('text') or '').lower()
            items_text = [clean_html(li) for li in lst.get('content', '').split('<li>') if li.strip()]
            if any(k in name for k in ['responsibilit', 'what you', 'you will', 'role']):
                resp_items = [i.strip() for i in items_text if len(i.strip()) > 10][:10]
            elif any(k in name for k in ['requirement', 'qualif', 'you have', 'you bring', 'must']):
                req_items = [i.strip() for i in items_text if len(i.strip()) > 10][:8]

        jobs.append({
            'title':            title,
            'company':          company,
            'location':         location,
            'work_mode':        detect_work_mode(location + title + desc),
            'job_type':         'Full-time',
            'experience':       detect_experience(title + desc),
            'salary_text':      None,
            'description':      desc,
            'responsibilities': resp_items,
            'requirements':     req_items,
            'skills':           [],
            'apply_url':        hosted,
            'apply_source':     f'{company} Careers',
            'category':         map_category(team + ' ' + title),
            'is_featured':      False,
            'logo_url':         logo_url,
        })

        if len(jobs) >= limit:
            break

    return jobs


# ═══════════════════════════════════════════════════════════════
# GREENHOUSE ATS — Generic fetcher
# GET https://boards-api.greenhouse.io/v1/boards/<slug>/jobs?content=true
# Direct apply URL: item['absolute_url']
# ═══════════════════════════════════════════════════════════════

def _scrape_greenhouse(slug: str, company: str, logo_url: str = '', limit: int = 30, all_dates: bool = False) -> list:
    jobs   = []
    url    = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    r      = safe_get(url)
    if not r:
        return jobs

    try:
        data  = r.json()
        items = data.get('jobs', [])
    except Exception:
        return jobs

    for item in items:
        posted = item.get('updated_at', '') or item.get('absolute_url', '')
        if not is_today(posted, all_dates):
            pass   # Greenhouse doesn't always return date; include all

        title  = item.get('title', '').strip()
        if not title:
            continue

        location = item.get('location', {}).get('name', 'Global')
        dept     = item.get('departments', [{}])[0].get('name', '') if item.get('departments') else ''
        desc     = clean_html(item.get('content', ''))[:2000]
        hosted   = item.get('absolute_url', f'https://boards.greenhouse.io/{slug}')

        jobs.append({
            'title':            title,
            'company':          company,
            'location':         location,
            'work_mode':        detect_work_mode(location + title + desc),
            'job_type':         'Full-time',
            'experience':       detect_experience(title + desc),
            'salary_text':      None,
            'description':      desc,
            'responsibilities': [],
            'requirements':     [],
            'skills':           [],
            'apply_url':        hosted,
            'apply_source':     f'{company} Careers',
            'category':         map_category(dept + ' ' + title),
            'is_featured':      False,
            'logo_url':         logo_url,
        })

        if len(jobs) >= limit:
            break

    return jobs


# ═══════════════════════════════════════════════════════════════
# WORKDAY ATS — Generic fetcher
# Used by: Salesforce, Adobe, and many more
# Direct apply URL: built from tenant + job path
# ═══════════════════════════════════════════════════════════════

def _scrape_workday(tenant: str, company: str, logo_url: str = '', limit: int = 30, all_dates: bool = False) -> list:
    """
    Workday public job board API.
    tenant: e.g. 'salesforce' for salesforce.wd12.myworkdayjobs.com
    """
    jobs     = []
    base     = f"https://{tenant}.wd12.myworkdayjobs.com/wday/cxs/{tenant}/External_Career_Site/jobs"
    payload  = {
        "appliedFacets": {},
        "limit": min(limit, 50),
        "offset": 0,
        "searchText": "",
        "sortBy": "date_posted",
    }

    try:
        r = SESSION.post(base, json=payload, timeout=20)
        r.raise_for_status()
        data  = r.json()
        items = data.get('jobPostings', [])
    except Exception as e:
        log.debug(f"Workday {company} error: {e}")
        return jobs

    for item in items:
        posted = item.get('postedOn', '')
        if not is_today(posted, all_dates):
            continue

        title    = item.get('title', '').strip()
        job_path = item.get('externalPath', '')
        if not title:
            continue

        location  = item.get('locationsText', 'Global')
        desc      = clean_html(item.get('jobDescription', ''))[:2000] if item.get('jobDescription') else f"{title} at {company}."
        apply_url = f"https://{tenant}.wd12.myworkdayjobs.com/External_Career_Site{job_path}"

        jobs.append({
            'title':            title,
            'company':          company,
            'location':         location,
            'work_mode':        detect_work_mode(title + location + desc),
            'job_type':         'Full-time',
            'experience':       detect_experience(title + desc),
            'salary_text':      None,
            'description':      desc,
            'responsibilities': [],
            'requirements':     [],
            'skills':           [],
            'apply_url':        apply_url,
            'apply_source':     f'{company} Careers',
            'category':         map_category(title),
            'is_featured':      False,
            'logo_url':         logo_url,
        })

        if len(jobs) >= limit:
            break

    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 6 — NETFLIX  (Lever)
# ═══════════════════════════════════════════════════════════════

def scrape_netflix(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping Netflix Jobs...")
    jobs = _scrape_lever(
        slug='netflix',
        company='Netflix',
        logo_url='https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/120px-Netflix_2015_logo.svg.png',
        limit=limit,
        all_dates=all_dates,
    )
    log.info(f"Netflix: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 7 — ATLASSIAN  (Lever)
# ═══════════════════════════════════════════════════════════════

def scrape_atlassian(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping Atlassian Jobs...")
    jobs = _scrape_lever(
        slug='atlassian',
        company='Atlassian',
        logo_url='https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Atlassian-logo.svg/120px-Atlassian-logo.svg.png',
        limit=limit,
        all_dates=all_dates,
    )
    log.info(f"Atlassian: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 8 — STRIPE  (Lever)
# ═══════════════════════════════════════════════════════════════

def scrape_stripe(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping Stripe Jobs...")
    jobs = _scrape_lever(
        slug='stripe',
        company='Stripe',
        logo_url='https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Stripe_Logo%2C_revised_2016.svg/120px-Stripe_Logo%2C_revised_2016.svg.png',
        limit=limit,
        all_dates=all_dates,
    )
    log.info(f"Stripe: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 9 — AIRBNB  (Greenhouse)
# ═══════════════════════════════════════════════════════════════

def scrape_airbnb(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping Airbnb Jobs...")
    jobs = _scrape_greenhouse(
        slug='airbnb',
        company='Airbnb',
        logo_url='https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Airbnb_Logo_Bélo.svg/120px-Airbnb_Logo_Bélo.svg.png',
        limit=limit,
        all_dates=all_dates,
    )
    log.info(f"Airbnb: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 10 — SPOTIFY  (Greenhouse)
# ═══════════════════════════════════════════════════════════════

def scrape_spotify(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping Spotify Jobs...")
    jobs = _scrape_greenhouse(
        slug='spotify',
        company='Spotify',
        logo_url='https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/60px-Spotify_logo_without_text.svg.png',
        limit=limit,
        all_dates=all_dates,
    )
    log.info(f"Spotify: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 11 — SALESFORCE  (Workday)
# ═══════════════════════════════════════════════════════════════

def scrape_salesforce(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping Salesforce Jobs...")
    jobs = _scrape_workday(
        tenant='salesforce',
        company='Salesforce',
        logo_url='https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Salesforce.com_logo.svg/120px-Salesforce.com_logo.svg.png',
        limit=limit,
        all_dates=all_dates,
    )
    log.info(f"Salesforce: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 12 — ADOBE  (Workday)
# ═══════════════════════════════════════════════════════════════

def scrape_adobe(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping Adobe Jobs...")
    jobs = _scrape_workday(
        tenant='adobe',
        company='Adobe',
        logo_url='https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Adobe_Corporate_Logo.png/120px-Adobe_Corporate_Logo.png',
        limit=limit,
        all_dates=all_dates,
    )
    log.info(f"Adobe: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 13 — UBER  (Greenhouse)
# ═══════════════════════════════════════════════════════════════

def scrape_uber(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping Uber Jobs...")
    jobs = _scrape_greenhouse(
        slug='uber-university',
        company='Uber',
        logo_url='https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Uber_logo_2018.svg/120px-Uber_logo_2018.svg.png',
        limit=limit,
        all_dates=all_dates,
    )
    # Also try the main Uber slug
    if len(jobs) < limit:
        jobs += _scrape_greenhouse(
            slug='uber',
            company='Uber',
            logo_url='https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Uber_logo_2018.svg/120px-Uber_logo_2018.svg.png',
            limit=limit - len(jobs),
            all_dates=all_dates,
        )
    log.info(f"Uber: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 14 — GITHUB  (Greenhouse)
# ═══════════════════════════════════════════════════════════════

def scrape_github(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping GitHub Jobs...")
    jobs = _scrape_greenhouse(
        slug='github',
        company='GitHub',
        logo_url='https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Octicons-mark-github.svg/60px-Octicons-mark-github.svg.png',
        limit=limit,
        all_dates=all_dates,
    )
    log.info(f"GitHub: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 15 — FIGMA  (Lever)
# ═══════════════════════════════════════════════════════════════

def scrape_figma(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping Figma Jobs...")
    jobs = _scrape_lever(
        slug='figma',
        company='Figma',
        logo_url='https://upload.wikimedia.org/wikipedia/commons/3/33/Figma-logo.svg',
        limit=limit,
        all_dates=all_dates,
    )
    log.info(f"Figma: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 16 — NOTION  (Greenhouse)
# ═══════════════════════════════════════════════════════════════

def scrape_notion(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping Notion Jobs...")
    jobs = _scrape_greenhouse(
        slug='notion',
        company='Notion',
        logo_url='https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png',
        limit=limit,
        all_dates=all_dates,
    )
    log.info(f"Notion: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 17 — DROPBOX  (Lever)
# ═══════════════════════════════════════════════════════════════

def scrape_dropbox(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping Dropbox Jobs...")
    jobs = _scrape_lever(
        slug='dropbox',
        company='Dropbox',
        logo_url='https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Dropbox_logo_2017.svg/120px-Dropbox_logo_2017.svg.png',
        limit=limit,
        all_dates=all_dates,
    )
    log.info(f"Dropbox: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 18 — ATLASSIAN-TEAM TOOLS (Trello, Jira via Atlassian)
# Already covered above. Add Canva here as bonus.
# CANVA  (Greenhouse)
# ═══════════════════════════════════════════════════════════════

def scrape_canva(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping Canva Jobs...")
    jobs = _scrape_greenhouse(
        slug='canva',
        company='Canva',
        logo_url='https://upload.wikimedia.org/wikipedia/en/thumb/3/3b/Canva_Logo.png/120px-Canva_Logo.png',
        limit=limit,
        all_dates=all_dates,
    )
    log.info(f"Canva: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 19 — TWILIO  (Greenhouse)
# ═══════════════════════════════════════════════════════════════

def scrape_twilio(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping Twilio Jobs...")
    jobs = _scrape_greenhouse(
        slug='twilio',
        company='Twilio',
        logo_url='https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Twilio-logo-red.svg/120px-Twilio-logo-red.svg.png',
        limit=limit,
        all_dates=all_dates,
    )
    log.info(f"Twilio: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 20 — HASHICORP  (Greenhouse)
# ═══════════════════════════════════════════════════════════════

def scrape_hashicorp(limit: int = 30, all_dates: bool = False) -> list:
    log.info("Scraping HashiCorp Jobs...")
    jobs = _scrape_greenhouse(
        slug='hashicorp',
        company='HashiCorp',
        logo_url='',
        limit=limit,
        all_dates=all_dates,
    )
    log.info(f"HashiCorp: {len(jobs)} jobs")
    return jobs


# ═══════════════════════════════════════════════════════════════
# FEATURED ROTATION — exactly 8 random jobs
# ═══════════════════════════════════════════════════════════════

def rotate_featured_jobs(db: Client) -> None:
    try:
        log.info("Rotating featured jobs (8 random)...")
        result = db.table('jobs').select('id').eq('is_active', True).execute()
        all_ids = [row['id'] for row in result.data]

        if not all_ids:
            log.warning("No active jobs found for featured rotation.")
            return

        db.table('jobs').update({'is_featured': False}).eq('is_active', True).execute()
        chosen = random.sample(all_ids, min(8, len(all_ids)))
        for jid in chosen:
            db.table('jobs').update({'is_featured': True}).eq('id', jid).execute()

        log.info(f"✨ Featured rotation: {len(chosen)} jobs set to featured.")
    except Exception as e:
        log.error(f"Featured rotation error: {e}")


# ═══════════════════════════════════════════════════════════════
# DATABASE INSERT WITH DEDUPLICATION
# ═══════════════════════════════════════════════════════════════

def post_jobs_to_supabase(jobs: list, dry_run: bool = False) -> int:
    if dry_run:
        log.info(f"[DRY RUN] Would process {len(jobs)} jobs:")
        for j in jobs[:15]:
            print(f"  → {j['title']} @ {j['company']}")
            print(f"     URL:             {j.get('apply_url', 'N/A')[:80]}")
            print(f"     Source:          {j.get('apply_source', 'N/A')}")
            print(f"     Category:        {j.get('category', 'N/A')}")
            print(f"     Work Mode:       {j.get('work_mode', 'N/A')}")
            print(f"     Experience:      {j.get('experience', 'N/A')}")
            print(f"     Responsibilities:{len(j.get('responsibilities', []))} items")
            print(f"     Requirements:    {len(j.get('requirements', []))} items")
            print(f"     Skills:          {j.get('skills', [])[:5]}")
            print()
        return 0

    if not SUPABASE_URL or not SUPABASE_KEY:
        log.error("Supabase credentials missing. Check .env file.")
        return 0

    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    inserted, skipped = 0, 0

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

            views = job.get('views') or random_views()

            result = db.table('jobs').insert({
                'title':            title[:200],
                'company':          (job.get('company', ''))[:200],
                'logo_url':         job.get('logo_url'),
                'location':         (job.get('location', 'Global'))[:200],
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
                log.info(f"✅ {title} @ {job.get('company')} | {job.get('apply_source')} | views={views}")

            time.sleep(0.15)

        except Exception as e:
            log.error(f"Insert error for '{title}': {e}")

    log.info(f"\n{'='*55}")
    log.info(f"✅ Inserted: {inserted}  |  ⏭ Skipped: {skipped}  |  Total: {len(jobs)}")

    rotate_featured_jobs(db)
    return inserted


# ═══════════════════════════════════════════════════════════════
# COMPANY REGISTRY
# Maps --company flag to scraper function
# ═══════════════════════════════════════════════════════════════

COMPANY_SCRAPERS = {
    'google':      scrape_google,
    'amazon':      scrape_amazon,
    'microsoft':   scrape_microsoft,
    'meta':        scrape_meta,
    'apple':       scrape_apple,
    'netflix':     scrape_netflix,
    'atlassian':   scrape_atlassian,
    'stripe':      scrape_stripe,
    'airbnb':      scrape_airbnb,
    'spotify':     scrape_spotify,
    'salesforce':  scrape_salesforce,
    'adobe':       scrape_adobe,
    'uber':        scrape_uber,
    'github':      scrape_github,
    'figma':       scrape_figma,
    'notion':      scrape_notion,
    'dropbox':     scrape_dropbox,
    'canva':       scrape_canva,
    'twilio':      scrape_twilio,
    'hashicorp':   scrape_hashicorp,
}


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='DayDreamer — Product-Based Company Job Scraper'
    )
    parser.add_argument(
        '--company',
        default='all',
        choices=['all'] + list(COMPANY_SCRAPERS.keys()),
        help='Which company to scrape (default: all)',
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Max jobs per company (default: 50)',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print jobs without inserting into Supabase',
    )
    parser.add_argument(
        '--all-dates',
        action='store_true',
        help='Fetch all jobs regardless of posting date (not just today)',
    )
    args = parser.parse_args()

    mode = 'DRY RUN' if args.dry_run else 'LIVE'
    date_mode = 'ALL DATES' if args.all_dates else f'TODAY ({TODAY})'
    log.info(f"🚀 DayDreamer Product Company Scraper | company={args.company} | limit={args.limit} | {mode} | {date_mode}")
    log.info('=' * 65)

    all_jobs: list = []

    targets = (
        list(COMPANY_SCRAPERS.items())
        if args.company == 'all'
        else [(args.company, COMPANY_SCRAPERS[args.company])]
    )

    for name, scraper_fn in targets:
        try:
            result = scraper_fn(limit=args.limit, all_dates=args.all_dates)
            all_jobs.extend(result)
            log.info(f"  ↳ {name}: {len(result)} fetched  (running total: {len(all_jobs)})")
        except Exception as e:
            log.error(f"Scraper failed for {name}: {e}")
        time.sleep(0.5)

    log.info(f"\n📊 Grand total scraped: {len(all_jobs)} jobs across {len(targets)} companies")

    if not all_jobs:
        log.warning(
            "No jobs found. Try --all-dates to bypass the today-only filter, "
            "or check network connectivity."
        )
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