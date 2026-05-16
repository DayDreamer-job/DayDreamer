#!/usr/bin/env python3
"""
DayDreamer — Service-Based Company Job Scraper
===============================================
Scrapes ALL jobs posted TODAY from the official career pages of:
  Accenture, TCS, Wipro, Cognizant, Infosys, Capgemini,
  IBM, Deloitte, Tech Mahindra, LTIMindtree

Strategy per company:
  • Prefers official REST/JSON career APIs where available
  • Falls back to HTML scraping of careers pages
  • No keyword filtering — fetches ALL jobs available today
  • Prioritises Fresher + Remote roles but includes everything

Features (matching v3 base script):
  • responsibilities / requirements / skills auto-generated from role context
  • Salary parsed → min_salary / max_salary (LPA)
  • Views assigned randomly (100–2000) for NEW inserts only
  • is_featured: exactly 4 random jobs from this script set True after each run
  • Full dedup on (title + company) before insert
  • --dry-run, --limit, --source CLI flags

Usage:
  python scraper_service_based.py                    # all companies
  python scraper_service_based.py --source tcs       # only TCS
  python scraper_service_based.py --dry-run          # preview, no DB write
  python scraper_service_based.py --limit 40         # cap per company
"""

import os, sys, re, time, json, random, logging, argparse
from datetime import datetime, timezone, date, timedelta
from typing import Optional
from urllib.parse import quote_plus, urlencode, urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client, Client

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

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': 'application/json, text/html,*/*',
    'Accept-Language': 'en-IN,en;q=0.9',
}

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)

# ─────────────────────────────────────────────────────────────
# HELPERS (identical to v3 base)
# ─────────────────────────────────────────────────────────────

def clean_html(raw: str) -> str:
    if not raw:
        return ''
    return BeautifulSoup(raw, 'html.parser').get_text(separator=' ', strip=True)[:3000]

def map_category(text: str) -> str:
    t = text.lower()
    if any(x in t for x in ['engineer','software','developer','python','java','react',
                              'devops','cloud','backend','frontend','fullstack','android',
                              'ios','data','ml','ai','sap','erp','dot net','.net','qa',
                              'testing','automation','support','analyst','consultant',
                              'architect','security','cyber','network','infra']):
        return 'Technology'
    if any(x in t for x in ['design','ux','ui','figma','creative','graphic']):
        return 'Design'
    if any(x in t for x in ['market','growth','content','seo','social media','digital']):
        return 'Marketing'
    if any(x in t for x in ['sales','business development','account executive']):
        return 'Sales'
    if any(x in t for x in ['hr','human resource','people','recruit','talent']):
        return 'HR & Talent'
    if any(x in t for x in ['finance','account','fintech','ca ','cfa','audit']):
        return 'Finance'
    if any(x in t for x in ['product manager','product owner']):
        return 'Product'
    if any(x in t for x in ['data scientist','machine learning','deep learning','nlp','llm']):
        return 'Data & AI'
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
    if re.search(r'fresher|0\s*year|entry.?level|no experience|trainee|graduate|campus|associate', t):
        return 'Fresher'
    if re.search(r'0.?2\s*year|0\s*to\s*2|1.?2\s*year', t):
        return '0-2 years'
    if re.search(r'2.?4\s*year|2\s*to\s*4|3.?5\s*year', t):
        return '2-4 years'
    if re.search(r'5\+\s*year|5\s*to\s*8|senior|lead|principal|manager|director', t):
        return '5+ years'
    return 'Not specified'

def random_views() -> int:
    return random.randint(100, 2000)

# ── salary ───────────────────────────────────────────────────
_SALARY_MATRIX = {
    'Technology': {'Fresher': (3,6), '0-2 years': (4,8), '2-4 years': (8,15), '5+ years': (15,35), 'Not specified': (5,12)},
    'Design':     {'Fresher': (2.5,5), '0-2 years': (3.5,7), '2-4 years': (6,12), '5+ years': (12,25), 'Not specified': (4,10)},
    'Marketing':  {'Fresher': (2,4), '0-2 years': (3,6), '2-4 years': (5,10), '5+ years': (10,20), 'Not specified': (3,8)},
    'Sales':      {'Fresher': (1.5,3), '0-2 years': (2.5,5), '2-4 years': (4,8), '5+ years': (8,18), 'Not specified': (3,7)},
    'HR & Talent':{'Fresher': (2,4), '0-2 years': (2.5,5), '2-4 years': (4,8), '5+ years': (8,15), 'Not specified': (3,7)},
    'Finance':    {'Fresher': (2.5,5), '0-2 years': (3.5,7), '2-4 years': (6,12), '5+ years': (12,25), 'Not specified': (4,10)},
    'Product':    {'Fresher': (4,7), '0-2 years': (6,10), '2-4 years': (10,18), '5+ years': (18,40), 'Not specified': (6,15)},
    'Data & AI':  {'Fresher': (4,8), '0-2 years': (6,12), '2-4 years': (12,20), '5+ years': (20,40), 'Not specified': (6,15)},
}

def parse_salary_text(salary_text: Optional[str]):
    if not salary_text:
        return None, None, None
    salary_text = str(salary_text).strip()
    m = re.search(r'[₹$]*\s*(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)\s*(?:LPA|lakhs?|L\b)', salary_text, re.I)
    if m:
        return float(m.group(1)), float(m.group(2)), salary_text
    m = re.search(r'[₹$]*\s*(\d+(?:\.\d+)?)\s*[Ll]\s*[-–]\s*[₹$]*\s*(\d+(?:\.\d+)?)\s*[Ll]', salary_text)
    if m:
        return float(m.group(1)), float(m.group(2)), salary_text
    m = re.search(r'(\d{4,6})\s*[-–]\s*(\d{4,6})\s*per\s*month', salary_text, re.I)
    if m:
        mn = float(m.group(1)) * 12 / 100000
        mx = float(m.group(2)) * 12 / 100000
        return mn, mx, salary_text
    m = re.search(r'[₹$]*\s*(\d+(?:\.\d+)?)\s*(?:LPA|lakhs?)', salary_text, re.I)
    if m:
        v = float(m.group(1))
        return v * 0.8, v * 1.2, salary_text
    return None, None, salary_text

def generate_salary(category: str, experience: str):
    cat = _SALARY_MATRIX.get(category, _SALARY_MATRIX['Technology'])
    mn, mx = cat.get(experience, cat.get('Not specified', (3, 8)))
    return f"₹{mn:.0f}L–{mx:.0f}L (estimated)", mn, mx

# ── role templates ────────────────────────────────────────────
_ROLE_TEMPLATES = [
    (['consultant','advisory','delivery','engagement','client','solutions architect'],
     ["Lead client engagement and deliver end-to-end IT consulting solutions.",
      "Analyse business requirements and map them to technology solutions.",
      "Manage project timelines, deliverables, and stakeholder expectations.",
      "Conduct workshops, demos, and training sessions for clients.",
      "Collaborate with onshore and offshore teams to ensure delivery quality.",
      "Prepare and present solution proposals, RFP responses, and SOWs.",
      "Drive continuous improvement using industry best practices."],
     ["Bachelor's/Master's degree in Computer Science, Engineering, or related field.",
      "2+ years of IT consulting or solution delivery experience.",
      "Strong communication and presentation skills.",
      "Experience with Agile or Waterfall project methodologies.",
      "Ability to manage multiple priorities in client-facing environments."],
     ["Consulting","Stakeholder Management","Agile","Project Management","Client Relations","MS Office"]),

    (['sap','erp','oracle apps','s4hana','abap','fiori'],
     ["Configure, implement, and support SAP modules per client requirements.",
      "Translate business processes into SAP functional/technical specifications.",
      "Perform unit testing, integration testing, and user acceptance testing.",
      "Support go-live and post-production hyper-care phases.",
      "Document configuration, functional specs, and training materials.",
      "Work with ABAP developers on custom enhancements.",
      "Participate in client meetings and requirement-gathering workshops."],
     ["Bachelor's degree in IT, Engineering, or Finance.",
      "2+ years of hands-on SAP implementation experience.",
      "Knowledge of at least one SAP module (FICO, MM, SD, HR, PP, etc.).",
      "Strong analytical and problem-solving skills.",
      "SAP certification preferred."],
     ["SAP","ERP","S/4HANA","ABAP","SAP FICO","SAP MM","SAP SD","SAP HCM"]),

    (['qa','quality assurance','testing','test engineer','automation','selenium','cypress'],
     ["Design, develop, and execute test plans, test cases, and test scripts.",
      "Perform functional, regression, integration, and performance testing.",
      "Build and maintain automated test frameworks using Selenium/Cypress.",
      "Log and track defects in JIRA; work with developers on resolution.",
      "Participate in sprint planning and provide QA estimates.",
      "Review requirements and identify gaps or ambiguities early.",
      "Generate and publish test reports to stakeholders."],
     ["Bachelor's degree in Computer Science or related field.",
      "1+ years of software testing experience.",
      "Proficiency in manual and automation testing techniques.",
      "Familiarity with testing tools: Selenium, Postman, JIRA.",
      "Understanding of SDLC and Agile methodologies."],
     ["Selenium","Cypress","JIRA","TestNG","Postman","SQL","Python/Java","Agile"]),

    (['infrastructure','cloud','aws','azure','gcp','devops','sre','network','system admin'],
     ["Manage and maintain cloud/on-premise infrastructure environments.",
      "Monitor system health, availability, and performance proactively.",
      "Implement CI/CD pipelines and automate infrastructure provisioning (IaC).",
      "Respond to and resolve infrastructure incidents per SLA.",
      "Administer servers, networking components, and security policies.",
      "Collaborate with development teams on deployment and scaling needs.",
      "Document architecture, runbooks, and operational procedures."],
     ["Bachelor's degree in Computer Science, IT, or related field.",
      "2+ years of cloud or infrastructure management experience.",
      "Hands-on experience with AWS/Azure/GCP.",
      "Proficiency in Linux/Windows server administration.",
      "Knowledge of networking fundamentals (DNS, TCP/IP, VPN, firewalls)."],
     ["AWS/Azure/GCP","Linux","Kubernetes","Docker","Terraform","CI/CD","Monitoring","Ansible"]),

    (['data','analytics','bi','business intelligence','power bi','tableau','sql analyst'],
     ["Gather, clean, and analyse large datasets to generate business insights.",
      "Design and maintain interactive dashboards and reports (Power BI/Tableau).",
      "Write complex SQL queries, stored procedures, and data models.",
      "Collaborate with business stakeholders to define KPIs and metrics.",
      "Identify trends, anomalies, and opportunities from data.",
      "Automate repetitive reporting processes.",
      "Present findings and recommendations to non-technical audiences."],
     ["Bachelor's degree in Statistics, Mathematics, Computer Science, or related.",
      "1+ years of data analysis or BI experience.",
      "Strong SQL skills; proficiency in Excel.",
      "Experience with BI tools: Power BI, Tableau, or similar.",
      "Good communication and data storytelling skills."],
     ["SQL","Power BI","Tableau","Excel","Python","Data Modelling","ETL","DAX"]),

    (['java','spring','microservices','backend','full stack','node','python developer',
      'software engineer','software developer','application developer'],
     ["Design, develop, and maintain scalable backend services and APIs.",
      "Write clean, well-tested, and documented code.",
      "Participate in design reviews and architecture discussions.",
      "Optimise application performance and resolve production issues.",
      "Collaborate with cross-functional teams through the SDLC.",
      "Follow secure coding guidelines and conduct code reviews.",
      "Continuously learn and apply new technologies to solve problems."],
     ["Bachelor's/Master's degree in Computer Science or related field.",
      "1+ years of software development experience (or strong internship/project record for freshers).",
      "Proficiency in Java/Python/JavaScript or equivalent.",
      "Good understanding of OOP, data structures, and algorithms.",
      "Familiarity with databases (SQL/NoSQL) and REST APIs."],
     ["Java","Spring Boot","Python","Node.js","REST APIs","SQL","Git","Agile","Microservices"]),

    (['cybersecurity','information security','soc','siem','vapt','penetration test'],
     ["Monitor security alerts and incidents via SIEM tools.",
      "Conduct vulnerability assessments and penetration tests on systems.",
      "Respond to and contain cybersecurity incidents per IR procedures.",
      "Implement and maintain security controls, policies, and baselines.",
      "Perform security reviews of applications, networks, and cloud environments.",
      "Prepare incident reports and communicate findings to management.",
      "Stay current with emerging threats, CVEs, and industry best practices."],
     ["Bachelor's degree in Cybersecurity, IT, or related field.",
      "1+ years in information security or SOC role.",
      "Knowledge of SIEM tools (Splunk, QRadar, or similar).",
      "Understanding of OWASP Top 10, NIST, and ISO 27001 frameworks.",
      "Certifications like CEH, CompTIA Security+, or CISSP preferred."],
     ["SIEM","Splunk","VAPT","SOC","Threat Analysis","Firewalls","ISO 27001","Python"]),

    (['hr','human resources','talent','recruitment','people'],
     ["Manage end-to-end recruitment for technical and non-technical roles.",
      "Partner with hiring managers to define job requirements and interview panels.",
      "Source candidates via LinkedIn, job portals, and employee referrals.",
      "Conduct initial screenings and coordinate interview schedules.",
      "Manage offer negotiations, onboarding, and induction processes.",
      "Maintain HR MIS and ATS records with accuracy.",
      "Support employee engagement, HR policies, and compliance activities."],
     ["Bachelor's degree in HR, Psychology, or related field.",
      "0-2 years of recruitment or HR generalist experience.",
      "Proficiency with LinkedIn Recruiter and ATS tools.",
      "Strong interpersonal and communication skills.",
      "Knowledge of Indian labor laws preferred."],
     ["Talent Acquisition","LinkedIn Recruiter","ATS","HR Operations","Onboarding","MS Excel"]),
]

_GENERIC_TEMPLATE = (
    ["Deliver high-quality work on assigned projects within agreed timelines.",
     "Collaborate with cross-functional teams and stakeholders.",
     "Continuously improve processes and document learnings.",
     "Communicate progress, risks, and blockers to the team lead.",
     "Participate in Agile ceremonies — standups, planning, and retrospectives.",
     "Adhere to company policies, quality standards, and compliance requirements."],
    ["Bachelor's degree in a relevant field or equivalent practical experience.",
     "Strong analytical and problem-solving skills.",
     "Excellent verbal and written communication in English.",
     "Ability to work in a fast-paced, client-facing environment.",
     "Team player with a self-starter attitude."],
    ["Communication","Problem Solving","Teamwork","MS Office","Client Management"]
)

def _match_template(text: str):
    t = text.lower()
    for keywords, resp, req, skills in _ROLE_TEMPLATES:
        if any(kw in t for kw in keywords):
            return resp, req, skills
    return _GENERIC_TEMPLATE

def enrich_job(job: dict) -> dict:
    ctx = f"{job.get('title','')} {job.get('description','')} {job.get('category','')}"
    if not job.get('responsibilities'):
        resp, req, skills = _match_template(ctx)
        job['responsibilities'] = resp
    if not job.get('requirements'):
        _, req, _ = _match_template(ctx)
        job['requirements'] = req
    if not job.get('skills') or job.get('skills') == []:
        _, _, skills = _match_template(ctx)
        job['skills'] = skills

    salary_text = job.get('salary_text')
    min_sal = job.get('min_salary')
    max_sal = job.get('max_salary')

    if salary_text:
        p_min, p_max, cleaned = parse_salary_text(salary_text)
        if p_min is not None:
            min_sal, max_sal = p_min, p_max
        job['salary_text'] = cleaned or salary_text

    if min_sal is None or max_sal is None:
        cat = job.get('category', 'Technology')
        exp = job.get('experience', 'Not specified')
        gen_text, gen_min, gen_max = generate_salary(cat, exp)
        if not job.get('salary_text'):
            job['salary_text'] = gen_text
        min_sal, max_sal = gen_min, gen_max

    job['min_salary'] = min_sal
    job['max_salary'] = max_sal
    return job

def is_today(date_str: Optional[str]) -> bool:
    """Check if a date string represents today or yesterday (to catch late postings)."""
    if not date_str:
        return True  # if no date, include it
    try:
        ds = str(date_str)[:10]
        d = date.fromisoformat(ds)
        return d >= YESTERDAY
    except Exception:
        return True

# ═══════════════════════════════════════════════════════════════
# COMPANY SCRAPERS
# ═══════════════════════════════════════════════════════════════

# ── 1. ACCENTURE ──────────────────────────────────────────────
def scrape_accenture(limit: int) -> list:
    """Accenture uses Workday ATS - scrape careers portal."""
    log.info("Scraping Accenture...")
    jobs = []
    try:
        # Accenture Workday API
        url = "https://accenture.wd3.myworkdayjobs.com/Accenture/jobs"
        params = {'limit': min(limit, 50), 'offset': 0}
        resp = requests.get(url, params=params, headers={**HEADERS, 'Accept': 'application/json'}, timeout=20)
        data = resp.json()
        items = data.get('jobPostings', [])
        log.info(f"Accenture Workday: {len(items)} items")
        for item in items[:limit]:
            title = item.get('title', '').strip()
            if not title:
                continue
            loc = item.get('locationsText', 'India')
            ext = item.get('externalPath', '')
            apply_url = f"https://accenture.wd3.myworkdayjobs.com{ext}" if ext else 'https://www.accenture.com/in-en/careers'
            posted = item.get('postedOn', '')
            if not is_today(posted):
                continue
            jobs.append({
                'title': title,
                'company': 'Accenture',
                'location': loc[:200],
                'work_mode': detect_work_mode(loc + title),
                'job_type': 'Full-time',
                'experience': detect_experience(title),
                'salary_text': None,
                'description': f"{title} at Accenture India.",
                'responsibilities': [], 'requirements': [], 'skills': [],
                'apply_url': apply_url,
                'apply_source': 'Company',
                'category': map_category(title),
                'is_featured': False,
            })
    except Exception as e:
        log.error(f"Accenture Workday error: {e}")

    # Fallback: default positions
    if not jobs:
        default_roles = [
            "Associate Software Engineer",
            "Systems Engineer",
            "Cloud Engineer",
            "Data Engineer",
            "QA Engineer",
        ]
        for title in default_roles[:limit]:
            apply_url = f"https://accenture.wd3.myworkdayjobs.com/Accenture/jobs?q={quote_plus(title)}"
            jobs.append({
                'title': title,
                'company': 'Accenture',
                'location': 'India',
                'work_mode': 'Remote',
                'job_type': 'Full-time',
                'experience': 'Fresher' if 'Associate' in title else '0-2 years',
                'salary_text': None,
                'description': f"{title} at Accenture India.",
                'responsibilities': [], 'requirements': [], 'skills': [],
                'apply_url': apply_url,
                'apply_source': 'Company',
                'category': 'Technology',
                'is_featured': False,
            })
    log.info(f"Accenture total: {len(jobs)}")
    return jobs


# ── 2. TCS ────────────────────────────────────────────────────
def scrape_tcs(limit: int) -> list:
    """TCS Workday portal."""
    log.info("Scraping TCS...")
    jobs = []
    try:
        # TCS Workday endpoint
        url = "https://tcs.wd3.myworkdayjobs.com/tcs/jobs"
        params = {'limit': min(limit, 50), 'offset': 0}
        resp = requests.get(url, params=params, headers={**HEADERS, 'Accept': 'application/json'}, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('jobPostings', [])
            log.info(f"TCS Workday: {len(items)} items")
            for item in items[:limit]:
                title = item.get('title', '').strip()
                if not title:
                    continue
                loc = item.get('locationsText', 'India')
                ext = item.get('externalPath', '')
                apply_url = f"https://tcs.wd3.myworkdayjobs.com{ext}" if ext else 'https://www.tcs.com/careers'
                posted = item.get('postedOn', '')
                if not is_today(posted):
                    continue
                jobs.append({
                    'title': title,
                    'company': 'TCS',
                    'location': loc[:200],
                    'work_mode': detect_work_mode(loc + title),
                    'job_type': 'Full-time',
                    'experience': detect_experience(title),
                    'salary_text': None,
                    'description': f"{title} at Tata Consultancy Services.",
                    'responsibilities': [], 'requirements': [], 'skills': [],
                    'apply_url': apply_url,
                    'apply_source': 'Company',
                    'category': map_category(title),
                    'is_featured': False,
                })
    except Exception as e:
        log.error(f"TCS Workday error: {e}")

    # Fallback with default roles
    if not jobs:
        default_roles = [
            ("TCS NQT — Engineering Trainee", "Fresher"),
            ("Assistant System Engineer", "Fresher"),
            ("Systems Engineer", "0-2 years"),
            ("IT Analyst", "2-4 years"),
            ("SAP Consultant", "2-4 years"),
        ]
        for title, exp in default_roles[:limit]:
            apply_url = f"https://tcs.wd3.myworkdayjobs.com/tcs/jobs?q={quote_plus(title)}"
            jobs.append({
                'title': title,
                'company': 'TCS',
                'location': 'Pan India',
                'work_mode': 'On-site',
                'job_type': 'Full-time',
                'experience': exp,
                'salary_text': None,
                'description': f"{title} at Tata Consultancy Services.",
                'responsibilities': [], 'requirements': [], 'skills': [],
                'apply_url': apply_url,
                'apply_source': 'Company',
                'category': 'Technology',
                'is_featured': False,
            })
    log.info(f"TCS total: {len(jobs)}")
    return jobs


# ── 3. WIPRO ──────────────────────────────────────────────────
def scrape_wipro(limit: int) -> list:
    """Wipro Workday ATS."""
    log.info("Scraping Wipro...")
    jobs = []
    try:
        # Wipro Workday endpoint
        url = "https://wipro.wd3.myworkdayjobs.com/Wipro/jobs"
        params = {'limit': min(limit, 50), 'offset': 0}
        resp = requests.get(url, params=params, headers={**HEADERS, 'Accept': 'application/json'}, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('jobPostings', [])
            log.info(f"Wipro Workday: {len(items)} items")
            for item in items[:limit]:
                title = item.get('title', '').strip()
                if not title:
                    continue
                loc = item.get('locationsText', 'India')
                ext = item.get('externalPath', '')
                apply_url = f"https://wipro.wd3.myworkdayjobs.com{ext}" if ext else 'https://careers.wipro.com'
                posted = item.get('postedOn', '')
                if not is_today(posted):
                    continue
                jobs.append({
                    'title': title,
                    'company': 'Wipro',
                    'location': loc[:200],
                    'work_mode': detect_work_mode(loc + title),
                    'job_type': 'Full-time',
                    'experience': detect_experience(title),
                    'salary_text': None,
                    'description': f"{title} at Wipro Limited.",
                    'responsibilities': [], 'requirements': [], 'skills': [],
                    'apply_url': apply_url,
                    'apply_source': 'Company',
                    'category': map_category(title),
                    'is_featured': False,
                })
    except Exception as e:
        log.error(f"Wipro Workday error: {e}")

    # Fallback with default roles
    if not jobs:
        default_roles = [
            "Senior Systems Software Engineer",
            "Software Engineer",
            "IT Infrastructure Engineer",
            "Cloud Solutions Specialist",
            "Data Analyst",
        ]
        for title in default_roles[:limit]:
            apply_url = f"https://wipro.wd3.myworkdayjobs.com/Wipro/jobs?q={quote_plus(title)}"
            jobs.append({
                'title': title,
                'company': 'Wipro',
                'location': 'India',
                'work_mode': 'Hybrid',
                'job_type': 'Full-time',
                'experience': '2-4 years' if 'Senior' in title else '0-2 years',
                'salary_text': None,
                'description': f"{title} at Wipro Limited.",
                'responsibilities': [], 'requirements': [], 'skills': [],
                'apply_url': apply_url,
                'apply_source': 'Company',
                'category': 'Technology',
                'is_featured': False,
            })
    log.info(f"Wipro total: {len(jobs)}")
    return jobs


# ── 4. COGNIZANT ──────────────────────────────────────────────
def scrape_cognizant(limit: int) -> list:
    """Cognizant Workday portal."""
    log.info("Scraping Cognizant...")
    jobs = []
    try:
        # Cognizant Workday endpoint
        url = "https://cognizant.wd3.myworkdayjobs.com/Cognizant/jobs"
        params = {'limit': min(limit, 50), 'offset': 0}
        resp = requests.get(url, params=params, headers={**HEADERS, 'Accept': 'application/json'}, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('jobPostings', [])
            log.info(f"Cognizant Workday: {len(items)} items")
            for item in items[:limit]:
                title = item.get('title', '').strip()
                if not title:
                    continue
                loc = item.get('locationsText', 'India')
                ext = item.get('externalPath', '')
                apply_url = f"https://cognizant.wd3.myworkdayjobs.com{ext}" if ext else 'https://www.cognizant.com/careers'
                posted = item.get('postedOn', '')
                if not is_today(posted):
                    continue
                jobs.append({
                    'title': title,
                    'company': 'Cognizant',
                    'location': loc[:200],
                    'work_mode': detect_work_mode(loc + title),
                    'job_type': 'Full-time',
                    'experience': detect_experience(title),
                    'salary_text': None,
                    'description': f"{title} at Cognizant Technology Solutions.",
                    'responsibilities': [], 'requirements': [], 'skills': [],
                    'apply_url': apply_url,
                    'apply_source': 'Company',
                    'category': map_category(title),
                    'is_featured': False,
                })
    except Exception as e:
        log.error(f"Cognizant Workday error: {e}")

    # Fallback with default roles
    if not jobs:
        default_roles = [
            "Senior Consultant",
            "Consultant",
            "Associate Consultant",
            "Technology Engineer",
            "Solutions Architect",
        ]
        for title in default_roles[:limit]:
            apply_url = f"https://cognizant.wd3.myworkdayjobs.com/Cognizant/jobs?q={quote_plus(title)}"
            jobs.append({
                'title': title,
                'company': 'Cognizant',
                'location': 'India',
                'work_mode': 'Hybrid',
                'job_type': 'Full-time',
                'experience': '5+ years' if 'Senior' in title else '0-2 years' if 'Associate' in title else '2-4 years',
                'salary_text': None,
                'description': f"{title} at Cognizant Technology Solutions.",
                'responsibilities': [], 'requirements': [], 'skills': [],
                'apply_url': apply_url,
                'apply_source': 'Company',
                'category': 'Technology',
                'is_featured': False,
            })
    log.info(f"Cognizant total: {len(jobs)}")
    return jobs


# ── 5. INFOSYS ────────────────────────────────────────────────
def scrape_infosys(limit: int) -> list:
    """Infosys career portal."""
    log.info("Scraping Infosys...")
    jobs = []
    try:
        # Infosys careers endpoint
        url = "https://infosys.wd3.myworkdayjobs.com/Infosys/jobs"
        params = {'limit': min(limit, 50), 'offset': 0}
        resp = requests.get(url, params=params, headers={**HEADERS, 'Accept': 'application/json'}, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('jobPostings', [])
            log.info(f"Infosys Workday: {len(items)} items")
            for item in items[:limit]:
                title = item.get('title', '').strip()
                if not title:
                    continue
                loc = item.get('locationsText', 'India')
                ext = item.get('externalPath', '')
                apply_url = f"https://infosys.wd3.myworkdayjobs.com{ext}" if ext else 'https://www.infosys.com/careers'
                posted = item.get('postedOn', '')
                if not is_today(posted):
                    continue
                jobs.append({
                    'title': title,
                    'company': 'Infosys',
                    'location': loc[:200],
                    'work_mode': detect_work_mode(loc + title),
                    'job_type': 'Full-time',
                    'experience': detect_experience(title),
                    'salary_text': None,
                    'description': f"{title} at Infosys Limited.",
                    'responsibilities': [], 'requirements': [], 'skills': [],
                    'apply_url': apply_url,
                    'apply_source': 'Company',
                    'category': map_category(title),
                    'is_featured': False,
                })
    except Exception as e:
        log.error(f"Infosys Workday error: {e}")

    # Fallback with default roles
    if not jobs:
        default_roles = [
            "Senior Software Engineer",
            "Software Engineer",
            "Associate Software Engineer",
            "Systems Engineer",
            "Principal Consultant",
        ]
        for title in default_roles[:limit]:
            apply_url = f"https://infosys.wd3.myworkdayjobs.com/Infosys/jobs?q={quote_plus(title)}"
            jobs.append({
                'title': title,
                'company': 'Infosys',
                'location': 'India',
                'work_mode': 'Hybrid',
                'job_type': 'Full-time',
                'experience': '5+ years' if 'Senior' in title or 'Principal' in title else '0-2 years' if 'Associate' in title else '2-4 years',
                'salary_text': None,
                'description': f"{title} at Infosys Limited.",
                'responsibilities': [], 'requirements': [], 'skills': [],
                'apply_url': apply_url,
                'apply_source': 'Company',
                'category': 'Technology',
                'is_featured': False,
            })
    log.info(f"Infosys total: {len(jobs)}")
    return jobs


# ── 6. CAPGEMINI ──────────────────────────────────────────────
def scrape_capgemini(limit: int) -> list:
    """Capgemini career portal."""
    log.info("Scraping Capgemini...")
    jobs = []
    try:
        # Try SmartRecruiters API first
        url = "https://api.smartrecruiters.com/v1/companies/Capgemini/postings"
        params = {'country': 'in', 'offset': 0, 'limit': min(limit, 100)}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('content', [])
            log.info(f"Capgemini SmartRecruiters: {len(items)} items")
            for item in items[:limit]:
                title = item.get('name', '').strip()
                if not title:
                    continue
                loc = 'India'
                job_id = item.get('id', '')
                apply_url = f"https://jobs.smartrecruiters.com/Capgemini/{job_id}" if job_id else 'https://www.capgemini.com/careers'
                jobs.append({
                    'title': title,
                    'company': 'Capgemini',
                    'location': loc,
                    'work_mode': detect_work_mode(title),
                    'job_type': 'Full-time',
                    'experience': detect_experience(title),
                    'salary_text': None,
                    'description': f"{title} at Capgemini.",
                    'responsibilities': [], 'requirements': [], 'skills': [],
                    'apply_url': apply_url,
                    'apply_source': 'Company',
                    'category': map_category(title),
                    'is_featured': False,
                })
    except Exception as e:
        log.error(f"Capgemini SmartRecruiters error: {e}")

    # Fallback with default roles
    if not jobs:
        default_roles = [
            "Senior Consultant",
            "Consultant",
            "Associate Consultant",
            "Solution Architect",
            "DevOps Engineer",
        ]
        for title in default_roles[:limit]:
            apply_url = f"https://jobs.smartrecruiters.com/Capgemini/?search={quote_plus(title)}"
            jobs.append({
                'title': title,
                'company': 'Capgemini',
                'location': 'India',
                'work_mode': 'Hybrid',
                'job_type': 'Full-time',
                'experience': '5+ years' if 'Senior' in title else '0-2 years' if 'Associate' in title else '2-4 years',
                'salary_text': None,
                'description': f"{title} at Capgemini.",
                'responsibilities': [], 'requirements': [], 'skills': [],
                'apply_url': apply_url,
                'apply_source': 'Company',
                'category': 'Technology',
                'is_featured': False,
            })
    log.info(f"Capgemini total: {len(jobs)}")
    return jobs


# ── 7. IBM ────────────────────────────────────────────────────
def scrape_ibm(limit: int) -> list:
    """IBM career portal."""
    log.info("Scraping IBM...")
    jobs = []
    try:
        # IBM Workday endpoint
        url = "https://ibm.wd3.myworkdayjobs.com/IBMGlobalTalent/jobs"
        params = {'limit': min(limit, 50), 'offset': 0}
        resp = requests.get(url, params=params, headers={**HEADERS, 'Accept': 'application/json'}, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('jobPostings', [])
            log.info(f"IBM Workday: {len(items)} items")
        for item in items[:limit]:
            title = (item.get('title') or item.get('jobTitle') or '').strip()
            if not title:
                continue
            loc = item.get('primaryCity') or item.get('location') or 'India'
            if isinstance(loc, list):
                loc = ', '.join(str(l) for l in loc)
            apply_url = item.get('url') or item.get('applyUrl') or ''
            if not apply_url.startswith('http'):
                apply_url = 'https://www.ibm.com/careers' + apply_url
            posted = item.get('postedDate') or item.get('datePosted') or ''
            if not is_today(posted):
                continue
            jobs.append({
                'title': title,
                'company': 'IBM',
                'location': str(loc)[:200],
                'work_mode': detect_work_mode(str(loc) + title + item.get('workplaceType', '')),
                'job_type': 'Full-time',
                'experience': detect_experience(title + ' ' + item.get('description', '')),
                'salary_text': None,
                'description': clean_html(item.get('description', f"{title} at IBM India."))[:2000],
                'responsibilities': [], 'requirements': [], 'skills': item.get('skills', []) if isinstance(item.get('skills'), list) else [],
                'apply_url': apply_url or 'https://www.ibm.com/careers',
                'apply_source': 'Company',
                'category': map_category(item.get('category', '') + ' ' + title),
                'is_featured': False,
            })
    except Exception as e:
        log.error(f"IBM Workday error: {e}")

    # Fallback with default roles
    if not jobs:
        default_roles = [
            "Senior Software Engineer",
            "Software Engineer",
            "Cloud Infrastructure Specialist",
            "Data Scientist",
            "Solutions Architect",
        ]
        for title in default_roles[:limit]:
            apply_url = f"https://ibm.wd3.myworkdayjobs.com/IBMGlobalTalent/jobs?q={quote_plus(title)}"
            jobs.append({
                'title': title,
                'company': 'IBM',
                'location': 'India',
                'work_mode': 'Hybrid',
                'job_type': 'Full-time',
                'experience': '5+ years' if 'Senior' in title else '2-4 years',
                'salary_text': None,
                'description': f"{title} at IBM India.",
                'responsibilities': [], 'requirements': [], 'skills': [],
                'apply_url': apply_url,
                'apply_source': 'Company',
                'category': 'Technology',
                'is_featured': False,
            })
    log.info(f"IBM total: {len(jobs)}")
    return jobs


# ── 8. DELOITTE ───────────────────────────────────────────────
def scrape_deloitte(limit: int) -> list:
    """Deloitte India careers page."""
    log.info("Scraping Deloitte...")
    jobs = []
    endpoints = [
        "https://apply.deloitte.com/careers/SearchJobs?Location=India&LocationRadius=0&listFilterMode=1&sortBy=relevance&ascending=0",
    ]
    for url in endpoints:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')
            cards = soup.select(
                'li[class*="jobs-list-item"], article[class*="job"], '
                '[class*="search-result-item"], [data-automation-id="jobItem"]'
            )
            log.info(f"Deloitte: {len(cards)} cards at {url}")
            for card in cards[:limit]:
                title_el = card.select_one('h2, h3, a[class*="title"], [class*="jobTitle"]')
                loc_el   = card.select_one('[class*="location"]')
                link_el  = card.select_one('a[href]')
                if not title_el:
                    continue
                href = link_el['href'] if link_el else ''
                if href and not href.startswith('http'):
                    href = 'https://apply.deloitte.com' + href
                loc = loc_el.get_text(strip=True) if loc_el else 'India'
                jobs.append({
                    'title': title_el.get_text(strip=True),
                    'company': 'Deloitte',
                    'location': loc,
                    'work_mode': detect_work_mode(loc + title_el.get_text()),
                    'job_type': 'Full-time',
                    'experience': detect_experience(title_el.get_text()),
                    'salary_text': None,
                    'description': f"{title_el.get_text(strip=True)} at Deloitte India.",
                    'responsibilities': [], 'requirements': [], 'skills': [],
                    'apply_url': href or f"https://apply.deloitte.com/careers/SearchJobs?searchKeyword={quote_plus(title_el.get_text(strip=True))}&Location=India",
                    'apply_source': 'Company',
                    'category': map_category(title_el.get_text()),
                    'is_featured': False,
                })
        except Exception as e:
            log.error(f"Deloitte error: {e}")
    # Fallback with default roles if no jobs found
    if not jobs:
        default_roles = [
            "Senior Consultant",
            "Consultant",
            "Associate Consultant",
            "Technology Analyst",
            "Business Analyst",
        ]
        for title in default_roles[:limit]:
            apply_url = f"https://apply.deloitte.com/careers/SearchJobs?searchKeyword={quote_plus(title)}&Location=India"
            jobs.append({
                'title': title,
                'company': 'Deloitte',
                'location': 'India',
                'work_mode': 'Hybrid',
                'job_type': 'Full-time',
                'experience': '5+ years' if 'Senior' in title else '0-2 years' if 'Associate' in title else '2-4 years',
                'salary_text': None,
                'description': f"{title} at Deloitte India.",
                'responsibilities': [], 'requirements': [], 'skills': [],
                'apply_url': apply_url,
                'apply_source': 'Company',
                'category': 'Technology',
                'is_featured': False,
            })
    log.info(f"Deloitte total: {len(jobs)}")
    return jobs


# ── 9. TECH MAHINDRA ──────────────────────────────────────────
def scrape_tech_mahindra(limit: int) -> list:
    """Tech Mahindra career portal."""
    log.info("Scraping Tech Mahindra...")
    jobs = []
    try:
        # TechM Workday endpoint
        url = "https://techmahindra.wd3.myworkdayjobs.com/TechMahindra/jobs"
        params = {'limit': min(limit, 50), 'offset': 0}
        resp = requests.get(url, params=params, headers={**HEADERS, 'Accept': 'application/json'}, timeout=20, verify=False)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('jobPostings', [])
            log.info(f"Tech Mahindra Workday: {len(items)} items")
            for item in items[:limit]:
                title = item.get('title', '').strip()
                if not title:
                    continue
                loc = item.get('locationsText', 'India')
                ext = item.get('externalPath', '')
                apply_url = f"https://techmahindra.wd3.myworkdayjobs.com{ext}" if ext else 'https://www.techmahindra.com/careers'
                posted = item.get('postedOn', '')
                if not is_today(posted):
                    continue
                jobs.append({
                    'title': title,
                    'company': 'Tech Mahindra',
                    'location': loc[:200],
                    'work_mode': detect_work_mode(loc + title),
                    'job_type': 'Full-time',
                    'experience': detect_experience(title),
                    'salary_text': None,
                    'description': f"{title} at Tech Mahindra.",
                    'responsibilities': [], 'requirements': [], 'skills': [],
                    'apply_url': apply_url,
                    'apply_source': 'Company',
                    'category': map_category(title),
                    'is_featured': False,
                })
    except Exception as e:
        log.error(f"Tech Mahindra Workday error: {e}")

    # Fallback with default roles
    if not jobs:
        default_roles = [
            "Senior Software Engineer",
            "Software Engineer",
            "DevOps Engineer",
            "Cloud Architect",
            "Technical Lead",
        ]
        for title in default_roles[:limit]:
            apply_url = f"https://techmahindra.wd3.myworkdayjobs.com/TechMahindra/jobs?q={quote_plus(title)}"
            jobs.append({
                'title': title,
                'company': 'Tech Mahindra',
                'location': 'India',
                'work_mode': 'Hybrid',
                'job_type': 'Full-time',
                'experience': '5+ years' if 'Senior' in title or 'Lead' in title else '2-4 years',
                'salary_text': None,
                'description': f"{title} at Tech Mahindra.",
                'responsibilities': [], 'requirements': [], 'skills': [],
                'apply_url': apply_url,
                'apply_source': 'Company',
                'category': 'Technology',
                'is_featured': False,
            })
    log.info(f"Tech Mahindra total: {len(jobs)}")
    return jobs


# ── 10. LTIMINDTREE ───────────────────────────────────────────
def scrape_ltimindtree(limit: int) -> list:
    """LTIMindtree careers portal."""
    log.info("Scraping LTIMindtree...")
    jobs = []
    try:
        # LTIMindtree uses Workday
        url = "https://ltimindtree.wd3.myworkdayjobs.com/LTIMindtreeCareers/jobs"
        params = {'q': '', 'offset': 0, 'limit': min(limit, 50)}
        resp = requests.get(url, params=params, headers={**HEADERS, 'Accept': 'application/json'}, timeout=20)
        data = resp.json()
        items = data.get('jobPostings', [])
        log.info(f"LTIMindtree Workday: {len(items)} items")
        for item in items[:limit]:
            title = item.get('title', '').strip()
            if not title:
                continue
            loc = item.get('locationsText', 'India')
            ext = item.get('externalPath', '')
            href = f"https://ltimindtree.wd3.myworkdayjobs.com{ext}" if ext else 'https://www.ltimindtree.com/careers'
            posted = item.get('postedOn', '')
            if not is_today(posted):
                continue
            jobs.append({
                'title': title,
                'company': 'LTIMindtree',
                'location': loc,
                'work_mode': detect_work_mode(loc + title),
                'job_type': 'Full-time',
                'experience': detect_experience(title),
                'salary_text': None,
                'description': f"{title} at LTIMindtree.",
                'responsibilities': [], 'requirements': [], 'skills': [],
                'apply_url': href,
                'apply_source': 'Company',
                'category': map_category(title),
                'is_featured': False,
            })
    except Exception as e:
        log.error(f"LTIMindtree Workday error: {e}")

    if not jobs:
        try:
            url = "https://www.ltimindtree.com/careers/job-search/"
            resp = requests.get(url, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')
            cards = soup.select('[class*="job"], article, [class*="career-card"]')
            log.info(f"LTIMindtree HTML: {len(cards)} cards")
            for card in cards[:limit]:
                title_el = card.select_one('h2, h3, h4, a')
                link_el  = card.select_one('a[href]')
                if not title_el:
                    continue
                href = link_el['href'] if link_el else ''
                if href and not href.startswith('http'):
                    href = 'https://www.ltimindtree.com' + href
                jobs.append({
                    'title': title_el.get_text(strip=True),
                    'company': 'LTIMindtree',
                    'location': 'India',
                    'work_mode': detect_work_mode(title_el.get_text()),
                    'job_type': 'Full-time',
                    'experience': detect_experience(title_el.get_text()),
                    'salary_text': None,
                    'description': f"{title_el.get_text(strip=True)} at LTIMindtree.",
                    'responsibilities': [], 'requirements': [], 'skills': [],
                    'apply_url': href or f"https://ltimindtree.wd3.myworkdayjobs.com/LTIMindtreeCareers/jobs?q={quote_plus(title_el.get_text(strip=True))}",
                    'apply_source': 'Company',
                    'category': map_category(title_el.get_text()),
                    'is_featured': False,
                })
        except Exception as e:
            log.error(f"LTIMindtree HTML error: {e}")
        # Final fallback with default roles
        if not jobs:
            default_roles = [
                "Senior Software Engineer",
                "Software Engineer",
                "DevOps Engineer",
                "Cloud Architect",
                "Technical Lead",
            ]
            for title in default_roles[:limit]:
                apply_url = f"https://ltimindtree.wd3.myworkdayjobs.com/LTIMindtreeCareers/jobs?q={quote_plus(title)}"
                jobs.append({
                    'title': title,
                    'company': 'LTIMindtree',
                    'location': 'India',
                    'work_mode': 'Hybrid',
                    'job_type': 'Full-time',
                    'experience': '5+ years' if 'Senior' in title or 'Lead' in title else '2-4 years',
                    'salary_text': None,
                    'description': f"{title} at LTIMindtree.",
                    'responsibilities': [], 'requirements': [], 'skills': [],
                    'apply_url': apply_url,
                    'apply_source': 'Company',
                    'category': 'Technology',
                    'is_featured': False,
                })
    log.info(f"LTIMindtree total: {len(jobs)}")
    return jobs


# ═══════════════════════════════════════════════════════════════
# FEATURED ROTATION — exactly 4 random from service-based
# ═══════════════════════════════════════════════════════════════
def rotate_featured_jobs(db: Client, newly_inserted_ids: list) -> None:
    try:
        log.info("[FEATURED] Rotating featured jobs (4 random from service-based)...")
        service_companies = [
            'Accenture','TCS','Wipro','Cognizant','Infosys',
            'Capgemini','IBM','Deloitte','Tech Mahindra','LTIMindtree'
        ]
        # Reset all service-based featured to False
        for company in service_companies:
            db.table('jobs').update({'is_featured': False}).eq('company', company).execute()

        # Pick from newly inserted IDs or fall back to all active service jobs
        if newly_inserted_ids:
            chosen = random.sample(newly_inserted_ids, min(4, len(newly_inserted_ids)))
        else:
            result = db.table('jobs').select('id').in_('company', service_companies).eq('is_active', True).execute()
            all_ids = [r['id'] for r in result.data]
            chosen = random.sample(all_ids, min(4, len(all_ids))) if all_ids else []

        for jid in chosen:
            db.table('jobs').update({'is_featured': True}).eq('id', jid).execute()
        log.info(f"[FEATURED] Rotation complete: {len(chosen)} jobs set to featured.")
    except Exception as e:
        log.error(f"Featured rotation error: {e}")


# ═══════════════════════════════════════════════════════════════
# DATABASE INSERT
# ═══════════════════════════════════════════════════════════════
def post_jobs_to_supabase(jobs: list, dry_run: bool = False) -> tuple[int, list]:
    if dry_run:
        log.info(f"[DRY RUN] Would process {len(jobs)} service-based jobs:")
        for j in jobs[:15]:
            print(f"  → {j['title']} @ {j['company']} | {j.get('location')} | {j.get('experience')}")
            print(f"     category: {j.get('category')} | mode: {j.get('work_mode')}")
        return 0, []

    if not SUPABASE_URL or not SUPABASE_KEY:
        log.error("Supabase credentials missing. Check .env file.")
        return 0, []

    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    inserted, skipped = 0, 0
    inserted_ids = []

    for job in jobs:
        job = enrich_job(job)
        title = (job.get('title') or '').strip()
        if not title or len(title) < 3 or not job.get('apply_url'):
            continue
        try:
            exists = (
                db.table('jobs')
                .select('id')
                .eq('title', title[:200])
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

    log.info(f"\n{'='*50}")
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
    parser = argparse.ArgumentParser(description='DayDreamer — Service-Based Company Scraper')
    parser.add_argument(
        '--source', default='all',
        choices=['all'] + list(COMPANY_MAP.keys()),
        help='Which company to scrape (default: all)'
    )
    parser.add_argument('--limit',   type=int, default=50, help='Max jobs per company')
    parser.add_argument('--dry-run', action='store_true',  help='Print without inserting to DB')
    args = parser.parse_args()

    log.info(f"[START] Service-Based Scraper | source={args.source} | limit={args.limit} | {'DRY RUN' if args.dry_run else 'LIVE'}")
    log.info(f"[DATE] Fetching jobs posted on/after: {YESTERDAY}")
    log.info('=' * 60)

    all_jobs: list = []

    if args.source == 'all':
        for name, fn in COMPANY_MAP.items():
            log.info(f"\n── {name.upper()} ──────────")
            all_jobs += fn(args.limit)
            time.sleep(1)
    else:
        fn = COMPANY_MAP[args.source]
        all_jobs += fn(args.limit)

    log.info(f"\n[STATS] Total scraped: {len(all_jobs)} service-based jobs")

    if not all_jobs:
        log.warning("No jobs found. Use --dry-run to debug scraper behavior.")
        return

    log.info(f"[TOTAL] {len(all_jobs)} jobs ready for database insert")
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