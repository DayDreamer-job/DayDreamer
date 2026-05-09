#!/usr/bin/env python3
"""
DayDreamer — Multi-Source Job Scraper v3
========================================
Changes from v2:
  • Naukri: scrapes full job detail pages for rich data
  • All sources: auto-generates responsibilities / requirements / skills
    from available text when not found natively
  • Views: added for NEW jobs only (random 100–2000); existing rows untouched
  • Featured: exactly 8 random jobs set is_featured=True after every run;
    all others set to False

Sources:
  1. Adzuna API       — free official API
  2. Naukri           — HTML scraping with full detail-page fetch
  3. LinkedIn         — public job search pages
  4. Indeed RSS       — official public RSS feed
  5. Foundit.in       — formerly Monster India
  6. Company Pages    — Lever / Greenhouse ATS APIs
  7. Manual           — paste jobs directly in MANUAL_JOBS list

Setup:
  pip install -r requirements.txt

Usage:
  python scraper.py                          # run all sources
  python scraper.py --source naukri          # only Naukri
  python scraper.py --source linkedin        # only LinkedIn
  python scraper.py --source indeed          # only Indeed RSS
  python scraper.py --source adzuna         # only Adzuna API
  python scraper.py --source companies       # only company career pages
  python scraper.py --source manual          # only manual jobs
  python scraper.py --keyword "data analyst" # custom search keyword
  python scraper.py --dry-run                # print without inserting to DB
  python scraper.py --limit 50               # max jobs per source
"""

import os, sys, json, time, argparse, logging, re, random, xml.etree.ElementTree as ET
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

SUPABASE_URL  = os.environ.get('NEXT_PUBLIC_SUPABASE_URL', '')
SUPABASE_KEY  = os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY', '')
ADZUNA_APP_ID = os.environ.get('ADZUNA_APP_ID', '')
ADZUNA_KEY    = os.environ.get('ADZUNA_API_KEY', '')

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-IN,en;q=0.9',
}

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

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def is_direct_company_link(url: str) -> bool:
    return bool(url) and not any(d in url.lower() for d in AGGREGATOR_DOMAINS)

def clean_html(raw: str) -> str:
    if not raw:
        return ''
    return BeautifulSoup(raw, 'html.parser').get_text(separator=' ', strip=True)[:2000]

def map_category(text: str) -> str:
    t = text.lower()
    if any(x in t for x in ['engineer','software','developer','python','java','react',
                              'devops','cloud','backend','frontend','fullstack','android',
                              'ios','data','ml','ai']):
        return 'Technology'
    if any(x in t for x in ['design','ux','ui','figma','creative','graphic']):
        return 'Design'
    if any(x in t for x in ['market','growth','content','seo','social media','digital']):
        return 'Marketing'
    if any(x in t for x in ['sales','business development','account executive']):
        return 'Sales'
    if any(x in t for x in ['hr','human resource','people','recruit','talent']):
        return 'HR & Talent'
    if any(x in t for x in ['finance','account','fintech','analyst','ca ','cfa']):
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
    if re.search(r'fresher|0\s*year|entry.?level|no experience', t):
        return 'Fresher'
    if re.search(r'0.?2\s*year|0\s*to\s*2|1.?2\s*year', t):
        return '0-2 years'
    if re.search(r'2.?4\s*year|2\s*to\s*4|3.?5\s*year', t):
        return '2-4 years'
    if re.search(r'5\+\s*year|5\s*to\s*8|senior', t):
        return '5+ years'
    return 'Not specified'

def random_views() -> int:
    """Return a random view count for a brand-new job post."""
    return random.randint(100, 2000)


# ─────────────────────────────────────────────────────────────
# SALARY PARSING & GENERATION
# ─────────────────────────────────────────────────────────────

# Salary ranges by category and experience (in LPA - Lakhs Per Annum)
_SALARY_MATRIX = {
    'Technology': {
        'Fresher': (3, 6),
        '0-2 years': (4, 8),
        '2-4 years': (8, 15),
        '5+ years': (15, 35),
    },
    'Design': {
        'Fresher': (2.5, 5),
        '0-2 years': (3.5, 7),
        '2-4 years': (6, 12),
        '5+ years': (12, 25),
    },
    'Marketing': {
        'Fresher': (2, 4),
        '0-2 years': (3, 6),
        '2-4 years': (5, 10),
        '5+ years': (10, 20),
    },
    'Sales': {
        'Fresher': (1.5, 3),
        '0-2 years': (2.5, 5),
        '2-4 years': (4, 8),
        '5+ years': (8, 18),
    },
    'HR & Talent': {
        'Fresher': (2, 4),
        '0-2 years': (2.5, 5),
        '2-4 years': (4, 8),
        '5+ years': (8, 15),
    },
    'Finance': {
        'Fresher': (2.5, 5),
        '0-2 years': (3.5, 7),
        '2-4 years': (6, 12),
        '5+ years': (12, 25),
    },
    'Product': {
        'Fresher': (4, 7),
        '0-2 years': (6, 10),
        '2-4 years': (10, 18),
        '5+ years': (18, 40),
    },
    'Data & AI': {
        'Fresher': (4, 8),
        '0-2 years': (6, 12),
        '2-4 years': (12, 20),
        '5+ years': (20, 40),
    },
}


def parse_salary_text(salary_text: Optional[str]) -> tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Parse salary_text and extract min_salary, max_salary (in LPA).
    Returns: (min_salary, max_salary, cleaned_salary_text)
    
    Examples:
    - "₹10-15 LPA" → (10.0, 15.0, "₹10-15 LPA")
    - "10 to 15 lakhs" → (10.0, 15.0, "10 to 15 lakhs")
    - "₹5L–₹10L" → (5.0, 10.0, "₹5L–₹10L")
    - "Competitive salary" → (None, None, "Competitive salary")
    """
    if not salary_text:
        return None, None, None

    salary_text = str(salary_text).strip()
    
    # Pattern 1: "₹10-15 LPA" or "10-15 LPA" or "10-15 lakhs"
    match = re.search(
        r'[₹\$]*\s*(\d+(?:\.\d+)?)\s*[-–to]\s*(\d+(?:\.\d+)?)\s*(?:LPA|lakhs?|l)',
        salary_text,
        re.IGNORECASE
    )
    if match:
        min_sal = float(match.group(1))
        max_sal = float(match.group(2))
        return min_sal, max_sal, salary_text

    # Pattern 2: "₹5L–₹10L" or "5L - 10L"
    match = re.search(
        r'[₹\$]*\s*(\d+(?:\.\d+)?)\s*[Ll]\s*[-–]\s*[₹\$]*\s*(\d+(?:\.\d+)?)\s*[Ll]',
        salary_text
    )
    if match:
        min_sal = float(match.group(1))
        max_sal = float(match.group(2))
        return min_sal, max_sal, salary_text

    # Pattern 3: "10000 - 20000 per month" (convert to LPA)
    match = re.search(
        r'[₹\$]*\s*(\d+(?:,\d{3})*)\s*[-–]\s*(\d+(?:,\d{3})*)\s*per\s*month',
        salary_text,
        re.IGNORECASE
    )
    if match:
        monthly_min = float(match.group(1).replace(',', ''))
        monthly_max = float(match.group(2).replace(',', ''))
        return monthly_min * 12 / 100000, monthly_max * 12 / 100000, salary_text

    # Pattern 4: Single value "₹10 LPA"
    match = re.search(
        r'[₹\$]*\s*(\d+(?:\.\d+)?)\s*(?:LPA|lakhs?)',
        salary_text,
        re.IGNORECASE
    )
    if match:
        sal = float(match.group(1))
        # For single value, assume ±20% range
        return sal * 0.8, sal * 1.2, salary_text

    # Could not parse - return original text
    return None, None, salary_text


def generate_salary_text(category: str, experience: str, min_sal: Optional[float] = None, max_sal: Optional[float] = None) -> tuple[Optional[str], Optional[float], Optional[float]]:
    """
    Generate salary_text and numeric ranges from category + experience matrix.
    If min_sal/max_sal already provided, use those and just format the text.
    Returns: (salary_text, min_salary, max_salary)
    """
    # If already have numeric values, just format the text
    if min_sal is not None and max_sal is not None:
        return f"₹{min_sal:.0f}L–{max_sal:.0f}L", min_sal, max_sal

    # Look up from matrix
    exp_key = experience or 'Not specified'
    cat_key = category or 'Technology'
    
    if cat_key in _SALARY_MATRIX and exp_key in _SALARY_MATRIX[cat_key]:
        min_sal, max_sal = _SALARY_MATRIX[cat_key][exp_key]
        salary_text = f"₹{min_sal:.0f}L–{max_sal:.0f}L (estimated)"
        return salary_text, min_sal, max_sal

    # Fallback to Technology > Fresher if category not found
    fallback_min, fallback_max = _SALARY_MATRIX['Technology']['Fresher']
    salary_text = f"₹{fallback_min:.0f}L–{fallback_max:.0f}L (estimated)"
    return salary_text, fallback_min, fallback_max


# ─────────────────────────────────────────────────────────────
# AI-GENERATED FALLBACK: responsibilities / requirements / skills
# Uses heuristics + role knowledge so no external API is needed.
# ─────────────────────────────────────────────────────────────

# Lookup table of common role patterns → (responsibilities, requirements, skills)
_ROLE_TEMPLATES: list[tuple[list[str], list[str], list[str], list[str]]] = [
    # (keywords_to_match, responsibilities, requirements, skills)
    (
        ['data engineer', 'etl', 'pipeline', 'data pipeline'],
        [
            "Design, build, and maintain ETL/ELT data pipelines from diverse data sources (databases, APIs, event streams, files).",
            "Develop and manage data warehouse/lake solutions (e.g., Snowflake, BigQuery, Redshift, Databricks).",
            "Implement and maintain data quality checks, validation, and monitoring to ensure high data reliability.",
            "Optimize queries and pipelines for performance, scalability, and cost efficiency.",
            "Collaborate with stakeholders to understand data needs and translate them into technical solutions.",
            "Maintain documentation of data models, pipelines, and systems.",
            "Implement data governance, security, and privacy standards (access control, PII handling).",
            "Participate in code reviews, design discussions, and continuous improvement of data tooling.",
            "Troubleshoot and resolve data-related issues in production environments.",
        ],
        [
            "Bachelor's/Master's degree in Computer Science, Engineering, or a related field.",
            "2+ years of hands-on experience building production data pipelines.",
            "Proficiency in Python and SQL.",
            "Experience with cloud platforms (AWS, GCP, or Azure).",
            "Familiarity with workflow orchestration tools like Airflow or Prefect.",
            "Strong understanding of data modeling concepts (star schema, data vault).",
            "Excellent problem-solving and communication skills.",
        ],
        ["Python", "SQL", "Apache Spark", "Airflow", "Kafka", "Snowflake", "BigQuery", "dbt", "AWS/GCP/Azure"],
    ),
    (
        ['data scientist', 'machine learning', 'ml engineer', 'deep learning', 'nlp', 'llm', 'ai engineer'],
        [
            "Develop and deploy machine learning models for business problems.",
            "Perform exploratory data analysis and feature engineering on large datasets.",
            "Evaluate model performance using appropriate metrics and iterate on improvements.",
            "Collaborate with product and engineering teams to integrate ML models into production.",
            "Monitor model performance and retrain as needed.",
            "Write clean, maintainable Python code and document work thoroughly.",
            "Stay current with the latest ML research and apply relevant advancements.",
        ],
        [
            "Bachelor's/Master's/PhD in Statistics, Mathematics, Computer Science, or related field.",
            "Strong proficiency in Python and ML libraries (scikit-learn, TensorFlow, PyTorch).",
            "Experience with data manipulation tools (Pandas, NumPy, SQL).",
            "Familiarity with cloud ML platforms (SageMaker, Vertex AI, Azure ML).",
            "Good understanding of statistical modelling and experimental design.",
            "Strong analytical and communication skills.",
        ],
        ["Python", "TensorFlow", "PyTorch", "scikit-learn", "SQL", "Pandas", "NumPy", "MLflow", "Docker"],
    ),
    (
        ['frontend', 'react', 'angular', 'vue', 'ui developer', 'front end'],
        [
            "Build responsive, accessible, and performant web interfaces using React (or Angular/Vue).",
            "Collaborate with designers to translate Figma/XD mockups into pixel-perfect components.",
            "Write clean, reusable, and well-tested component code.",
            "Integrate REST/GraphQL APIs and manage application state effectively.",
            "Conduct code reviews and contribute to front-end best practices.",
            "Optimise web applications for maximum speed and cross-browser compatibility.",
            "Participate in Agile ceremonies — sprint planning, standups, and retrospectives.",
        ],
        [
            "Bachelor's degree in Computer Science or equivalent practical experience.",
            "2+ years of professional front-end development experience.",
            "Strong command of JavaScript/TypeScript and modern frameworks (React preferred).",
            "Experience with state management libraries (Redux, Zustand, or similar).",
            "Solid understanding of HTML5, CSS3, and responsive design principles.",
            "Familiarity with CI/CD pipelines and version control (Git).",
        ],
        ["React", "TypeScript", "JavaScript", "HTML5", "CSS3", "Redux", "REST APIs", "Git", "Figma"],
    ),
    (
        ['backend', 'node', 'django', 'spring', 'golang', 'java developer', 'python developer', 'software engineer'],
        [
            "Design, develop, and maintain scalable backend services and REST/gRPC APIs.",
            "Write clean, efficient code with unit and integration test coverage.",
            "Collaborate with front-end engineers and product managers on feature delivery.",
            "Optimize database queries and improve application performance.",
            "Participate in system design discussions and architectural decisions.",
            "Review code and mentor junior engineers.",
            "Identify and resolve production incidents with a root-cause mindset.",
        ],
        [
            "Bachelor's degree in Computer Science or a related discipline.",
            "2+ years of experience in backend/full-stack software development.",
            "Proficiency in at least one backend language (Python, Java, Node.js, Go).",
            "Solid understanding of relational databases (PostgreSQL, MySQL).",
            "Experience with cloud services (AWS, GCP, or Azure) and containerization (Docker, Kubernetes).",
            "Familiarity with Agile/Scrum methodologies.",
        ],
        ["Python/Java/Node.js/Go", "PostgreSQL", "REST APIs", "Docker", "Kubernetes", "Git", "Redis", "AWS/GCP"],
    ),
    (
        ['devops', 'sre', 'site reliability', 'platform engineer', 'cloud engineer', 'infrastructure'],
        [
            "Design and manage CI/CD pipelines for continuous delivery of software.",
            "Provision, configure, and maintain cloud infrastructure using IaC tools (Terraform, Pulumi).",
            "Monitor system health, define SLOs/SLAs, and respond to on-call incidents.",
            "Automate repetitive operational tasks to reduce toil.",
            "Collaborate with development teams to embed DevOps practices throughout the SDLC.",
            "Manage container orchestration platforms (Kubernetes/ECS).",
            "Enforce security best practices and compliance across infrastructure.",
        ],
        [
            "Bachelor's degree in Computer Science, Engineering, or equivalent experience.",
            "3+ years in DevOps, SRE, or platform engineering roles.",
            "Strong command of Linux/Unix systems administration.",
            "Hands-on experience with Kubernetes and Docker.",
            "Proficiency with at least one cloud provider (AWS preferred).",
            "Experience with monitoring tools (Prometheus, Grafana, Datadog).",
            "Scripting skills in Python or Bash.",
        ],
        ["Kubernetes", "Docker", "Terraform", "AWS/GCP/Azure", "CI/CD", "Prometheus", "Grafana", "Python", "Bash"],
    ),
    (
        ['product manager', 'product owner', 'pm '],
        [
            "Define and communicate the product vision, strategy, and roadmap.",
            "Gather and prioritise requirements from customers, stakeholders, and data.",
            "Write detailed PRDs and user stories for the engineering team.",
            "Work closely with design, engineering, and data teams through the product lifecycle.",
            "Track key product metrics and use insights to drive decisions.",
            "Conduct user research, usability studies, and competitive analysis.",
            "Manage the product backlog and participate in Agile ceremonies.",
        ],
        [
            "Bachelor's/Master's degree in Business, Engineering, or related field.",
            "3+ years of product management experience in a tech company.",
            "Strong analytical skills; comfortable with data and A/B testing.",
            "Excellent written and verbal communication skills.",
            "Experience with tools like Jira, Confluence, Figma, and Mixpanel/Amplitude.",
            "Ability to influence cross-functional teams without direct authority.",
        ],
        ["Product Strategy", "Agile/Scrum", "JIRA", "Figma", "SQL", "A/B Testing", "Stakeholder Management", "Roadmapping"],
    ),
    (
        ['ui', 'ux', 'designer', 'design', 'figma', 'creative'],
        [
            "Create wireframes, prototypes, and high-fidelity designs using Figma or equivalent tools.",
            "Conduct user research, usability testing, and synthesize findings into design decisions.",
            "Develop and maintain a cohesive design system and component library.",
            "Collaborate with product managers and engineers to ship delightful user experiences.",
            "Present design concepts and iterate based on feedback.",
            "Ensure designs are accessible and meet WCAG guidelines.",
            "Stay up to date with design trends and best practices.",
        ],
        [
            "3+ years of professional UX/UI design experience.",
            "Strong portfolio demonstrating end-to-end design process.",
            "Proficiency in Figma (or Sketch/Adobe XD).",
            "Understanding of front-end development constraints (HTML/CSS basics).",
            "Experience conducting user interviews and usability tests.",
            "Excellent visual design sense and attention to detail.",
        ],
        ["Figma", "Adobe XD", "User Research", "Prototyping", "Design Systems", "Usability Testing", "Accessibility", "CSS basics"],
    ),
    (
        ['marketing', 'growth', 'seo', 'content', 'digital marketing', 'social media'],
        [
            "Plan, execute, and optimize digital marketing campaigns across channels (SEO, SEM, social, email).",
            "Create compelling content — blog posts, social copy, email newsletters — aligned with brand voice.",
            "Analyze campaign performance using Google Analytics, Meta Ads Manager, or similar tools.",
            "Conduct keyword research and implement on-page and off-page SEO strategies.",
            "Collaborate with design and product teams on go-to-market plans.",
            "Manage social media accounts and community engagement.",
            "Report on KPIs and make data-driven recommendations.",
        ],
        [
            "Bachelor's degree in Marketing, Communications, or related field.",
            "2+ years of digital marketing experience.",
            "Hands-on experience with Google Ads, Meta Ads, and/or LinkedIn Ads.",
            "Proficiency in Google Analytics and marketing automation tools.",
            "Strong writing and communication skills.",
            "Ability to manage multiple projects in a fast-paced environment.",
        ],
        ["Google Analytics", "SEO/SEM", "Google Ads", "Meta Ads", "Email Marketing", "Content Writing", "HubSpot", "Figma/Canva"],
    ),
    (
        ['sales', 'business development', 'account executive', 'account manager'],
        [
            "Identify, prospect, and close new business opportunities.",
            "Build and maintain relationships with key decision-makers at target accounts.",
            "Manage the full sales cycle from outreach to contract signing.",
            "Maintain accurate pipeline data in CRM (Salesforce, HubSpot).",
            "Collaborate with marketing on lead generation campaigns.",
            "Meet or exceed monthly and quarterly revenue targets.",
            "Represent the company at industry events and conferences.",
        ],
        [
            "Bachelor's degree in Business, Marketing, or related field.",
            "2+ years of B2B sales experience, preferably in SaaS or tech.",
            "Strong negotiation and objection-handling skills.",
            "Proven track record of quota attainment.",
            "Excellent verbal and written communication skills.",
            "Familiarity with CRM tools (Salesforce, HubSpot).",
        ],
        ["Salesforce", "HubSpot", "B2B Sales", "Negotiation", "CRM", "Pipeline Management", "Cold Outreach", "Presentations"],
    ),
    (
        ['hr', 'human resource', 'recruiter', 'talent acquisition', 'people ops'],
        [
            "Source, screen, and interview candidates for a variety of technical and non-technical roles.",
            "Partner with hiring managers to understand role requirements and develop job descriptions.",
            "Manage end-to-end recruitment processes including offer negotiation and onboarding.",
            "Maintain and update the ATS (Applicant Tracking System) with accurate candidate data.",
            "Build talent pipelines through LinkedIn, job boards, and campus programs.",
            "Drive employer branding initiatives to attract top talent.",
            "Support HR operations — policies, compliance, and employee engagement.",
        ],
        [
            "Bachelor's degree in Human Resources, Psychology, or related field.",
            "2+ years of recruitment or HR generalist experience.",
            "Proficiency with ATS tools (Lever, Greenhouse, Workday).",
            "Strong interpersonal and stakeholder management skills.",
            "Experience sourcing on LinkedIn and other platforms.",
            "Knowledge of Indian labor laws and compliance requirements.",
        ],
        ["Talent Acquisition", "LinkedIn Recruiter", "ATS (Lever/Greenhouse)", "HR Operations", "Employer Branding", "Onboarding", "Interviewing"],
    ),
]

_GENERIC_TEMPLATE = (
    [
        "Take ownership of assigned projects and deliver high-quality output within deadlines.",
        "Collaborate cross-functionally with teams across product, design, and engineering.",
        "Continuously improve processes and share learnings with the broader team.",
        "Communicate progress and blockers clearly to stakeholders.",
        "Participate in team rituals — standups, planning, and retrospectives.",
        "Contribute to a positive, inclusive, and high-performing team culture.",
    ],
    [
        "Bachelor's degree in a relevant field or equivalent practical experience.",
        "Strong problem-solving skills and ability to thrive in a fast-paced environment.",
        "Excellent communication and collaboration skills.",
        "Self-motivated with a growth mindset.",
        "Prior internship or work experience in a similar role is a plus.",
    ],
    ["Communication", "Problem Solving", "Teamwork", "Attention to Detail", "MS Office / Google Workspace"],
)


def _match_template(text: str):
    """Return (responsibilities, requirements, skills) from template or generic fallback."""
    t = text.lower()
    for keywords, resp, req, skills in _ROLE_TEMPLATES:
        if any(kw in t for kw in keywords):
            return resp, req, skills
    return _GENERIC_TEMPLATE


def enrich_job(job: dict) -> dict:
    """
    If responsibilities / requirements / skills are missing or empty,
    generate them from the role title + description using template matching.
    Also parse and generate salary data if missing.
    """
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

    # ─ Salary enrichment ──────────────────────────────────────
    salary_text = job.get('salary_text')
    min_sal, max_sal = job.get('min_salary'), job.get('max_salary')

    # Try to parse existing salary_text first
    if salary_text:
        parsed_min, parsed_max, cleaned = parse_salary_text(salary_text)
        if parsed_min is not None and parsed_max is not None:
            min_sal, max_sal = parsed_min, parsed_max
            job['salary_text'] = cleaned
        else:
            job['salary_text'] = cleaned or salary_text

    # If still missing, generate from category + experience
    if min_sal is None or max_sal is None:
        category = job.get('category', 'Technology')
        experience = job.get('experience', 'Not specified')
        gen_text, gen_min, gen_max = generate_salary_text(category, experience, min_sal, max_sal)
        if job.get('salary_text') is None or job.get('salary_text') == '':
            job['salary_text'] = gen_text
        min_sal = gen_min
        max_sal = gen_max

    job['min_salary'] = min_sal
    job['max_salary'] = max_sal

    return job



# ═══════════════════════════════════════════════════════════════
# SOURCE 1 — NAUKRI (HTML scraping with full detail-page fetch)
# Targets freshers + 2-4 year experience jobs
# ═══════════════════════════════════════════════════════════════

def _parse_naukri_detail(url: str) -> dict:
    """
    Fetch a single Naukri job detail page and extract structured data.
    Returns a dict with: description, responsibilities, requirements,
    skills, salary_text, work_mode, experience, location, views.
    """
    result = {
        'description': '',
        'responsibilities': [],
        'requirements': [],
        'skills': [],
        'salary_text': None,
        'work_mode': '',
        'experience': '',
        'location': '',
        'views': None,
    }
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25)
        if resp.status_code != 200:
            return result
        soup = BeautifulSoup(resp.text, 'html.parser')

        # ── Job description block ──────────────────────────────
        desc_section = (
            soup.select_one('div.styles_JDC__dang-inner-html__h0K4t') or
            soup.select_one('div[class*="job-desc"]') or
            soup.select_one('div[class*="JDC"]') or
            soup.select_one('section.styles_job-desc-container__txpYf') or
            soup.select_one('div.dang-inner-html')
        )
        if desc_section:
            full_text = desc_section.get_text(separator='\n', strip=True)
            result['description'] = full_text[:2000]

            # Split into responsibilities / requirements sections
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]
            resp_lines, req_lines = [], []
            mode = None
            for line in lines:
                ll = line.lower()
                if any(k in ll for k in ['responsibilit', 'what you will do', 'role & responsibilities',
                                          'key responsibilities', 'job responsibilities', 'your role']):
                    mode = 'resp'
                    continue
                if any(k in ll for k in ['requirement', 'qualification', 'what we look',
                                          'you should have', 'must have', 'eligibility', 'skills required']):
                    mode = 'req'
                    continue
                if any(k in ll for k in ['about us', 'about the company', 'what we offer',
                                          'perks', 'benefits', 'why join']):
                    mode = None
                    continue
                if mode == 'resp' and len(line) > 20:
                    resp_lines.append(line.rstrip('.') + '.')
                elif mode == 'req' and len(line) > 15:
                    req_lines.append(line.rstrip('.') + '.')

            if resp_lines:
                result['responsibilities'] = resp_lines[:10]
            if req_lines:
                result['requirements'] = req_lines[:8]

        # ── Skills tags ────────────────────────────────────────
        skill_chips = (
            soup.select('div[class*="styles_key-skill"] a') or
            soup.select('a[class*="chip"]') or
            soup.select('div[class*="keyskill"] a') or
            soup.select('li[class*="tag"]')
        )
        if skill_chips:
            result['skills'] = [c.get_text(strip=True) for c in skill_chips if c.get_text(strip=True)][:15]

        # ── Salary ─────────────────────────────────────────────
        sal_el = (
            soup.select_one('[class*="salary"]') or
            soup.select_one('[class*="Salary"]') or
            soup.select_one('span[class*="sal"]')
        )
        if sal_el:
            sal_text = sal_el.get_text(strip=True)
            if sal_text and sal_text.lower() not in ('not disclosed', '-', ''):
                result['salary_text'] = sal_text

        # If salary not found in dedicated field, search in description
        if not result['salary_text'] and result['description']:
            salary_pattern = re.search(
                r'[₹\$]*\s*(\d+(?:\.\d+)?)\s*[-–to]\s*(\d+(?:\.\d+)?)\s*(?:LPA|lakhs?|per month)',
                result['description'],
                re.IGNORECASE
            )
            if salary_pattern:
                result['salary_text'] = salary_pattern.group(0).strip()

        # ── Work mode / location / experience from metadata ────
        meta_blocks = soup.select('div[class*="styles_details"] span, div[class*="jdTagsContainer"] span, div[class*="loc"] span')
        for el in meta_blocks:
            txt = el.get_text(strip=True).lower()
            if 'remote' in txt:
                result['work_mode'] = 'Remote'
            elif 'hybrid' in txt:
                result['work_mode'] = 'Hybrid'

        exp_el = (
            soup.select_one('[class*="exp"] span') or
            soup.select_one('[class*="experience"]')
        )
        if exp_el:
            result['experience'] = detect_experience(exp_el.get_text())

        loc_el = (
            soup.select_one('[class*="location"] a') or
            soup.select_one('[class*="loc"] a') or
            soup.select_one('[class*="location"] span')
        )
        if loc_el:
            result['location'] = loc_el.get_text(strip=True)

        # ── Views / applicants ─────────────────────────────────
        views_el = soup.find(string=re.compile(r'\d+\s*(views?|applicants?)', re.I))
        if views_el:
            m = re.search(r'(\d[\d,]*)\s*views?', views_el, re.I)
            if m:
                result['views'] = int(m.group(1).replace(',', ''))

    except Exception as e:
        log.debug(f"Naukri detail parse error {url}: {e}")

    return result


def scrape_naukri(keywords: list, limit: int = 30) -> list:
    """
    Step 1 — Scrape Naukri listing pages targeting fresher + 0-4 year jobs.
    Step 2 — For each result, fetch the full detail page to get structured data.
    """
    log.info("Scraping Naukri (listing + detail pages)...")
    jobs = []
    per_kw = max(1, limit // min(len(keywords), 5))

    # Use naukri's experience filter: 0-4 years (experience=0,4 in query)
    listing_urls = []
    for keyword in keywords[:5]:
        slug = keyword.replace(' ', '-').replace('india', '').strip('-')
        listing_urls.append((
            keyword,
            f"https://www.naukri.com/{slug}-jobs?experience=0&jobAge=1",
        ))
        listing_urls.append((
            keyword,
            f"https://www.naukri.com/{slug}-jobs?experience=2&jobAge=1",
        ))

    seen_hrefs = set()

    for keyword, url in listing_urls:
        if len(jobs) >= limit:
            break
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')

            cards = soup.select(
                'article.jobTuple, '
                'div[class*="jobTuple"], '
                'div[class*="job-container"], '
                'div[class*="srp-jobtuple"]'
            )
            log.info(f"Naukri listing '{keyword}': {len(cards)} cards")

            for card in cards[:per_kw]:
                if len(jobs) >= limit:
                    break
                try:
                    title_el   = card.select_one('a.title, a[class*="title"]')
                    company_el = card.select_one('a.subTitle, [class*="company"]')
                    loc_el     = card.select_one('li.location, [class*="location"]')
                    exp_el     = card.select_one('li.experience, [class*="exp"]')
                    sal_el     = card.select_one('li.salary, [class*="salary"]')

                    if not title_el:
                        continue

                    href = title_el.get('href', '')
                    if href and not href.startswith('http'):
                        href = 'https://www.naukri.com' + href
                    if not href or href in seen_hrefs:
                        continue
                    seen_hrefs.add(href)

                    base_title    = title_el.get_text(strip=True)
                    base_company  = company_el.get_text(strip=True) if company_el else 'Hiring Company'
                    base_location = loc_el.get_text(strip=True) if loc_el else 'India'
                    base_exp      = detect_experience(exp_el.get_text() if exp_el else base_title)
                    base_sal      = sal_el.get_text(strip=True) if sal_el else None

                    # Fetch full detail page
                    log.info(f"  → Fetching detail: {href[:80]}...")
                    detail = _parse_naukri_detail(href)
                    time.sleep(1.2)  # polite delay between detail fetches

                    job = {
                        'title':            base_title,
                        'company':          base_company,
                        'location':         detail.get('location') or base_location,
                        'work_mode':        detail.get('work_mode') or detect_work_mode(base_title + base_location),
                        'job_type':         'Full-time',
                        'experience':       detail.get('experience') or base_exp,
                        'salary_text':      detail.get('salary_text') or base_sal,
                        'description':      detail.get('description') or f"{base_title} at {base_company}. Visit Naukri for full details.",
                        'responsibilities': detail.get('responsibilities', []),
                        'requirements':     detail.get('requirements', []),
                        'skills':           detail.get('skills', []),
                        'apply_url':        href,
                        'apply_source':     'Naukri',
                        'category':         map_category(base_title),
                        'is_featured':      False,
                        'views':            detail.get('views'),  # will be overridden if None
                    }
                    jobs.append(job)

                except Exception as e:
                    log.debug(f"Naukri card error: {e}")

            time.sleep(2)
        except Exception as e:
            log.error(f"Naukri error '{keyword}': {e}")

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
            url  = (
                f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keyword)}"
                f"&location=India&f_TPR=r86400&position=1&pageNum=0"
            )
            resp = requests.get(url, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(resp.text, 'html.parser')

            cards = soup.select(
                'div.base-card, div[class*="job-search-card"], li[class*="jobs-search"]'
            )
            log.info(f"LinkedIn '{keyword}': {len(cards)} cards")

            for card in cards[:per_kw]:
                try:
                    title_el   = card.select_one('h3[class*="title"], .base-search-card__title')
                    company_el = card.select_one('h4[class*="subtitle"], .base-search-card__subtitle, a[class*="company"]')
                    loc_el     = card.select_one('[class*="location"], .job-search-card__location')
                    link_el    = card.select_one('a[class*="base-card__full-link"], a[class*="job-card"]')
                    if not title_el:
                        continue

                    jobs.append({
                        'title':            title_el.get_text(strip=True),
                        'company':          company_el.get_text(strip=True) if company_el else 'Hiring Company',
                        'location':         loc_el.get_text(strip=True) if loc_el else 'India',
                        'work_mode':        detect_work_mode((title_el.get_text() or '') + (loc_el.get_text() if loc_el else '')),
                        'job_type':         'Full-time',
                        'experience':       detect_experience(title_el.get_text()),
                        'salary_text':      None,
                        'description':      f"{title_el.get_text(strip=True)} at {company_el.get_text(strip=True) if company_el else 'a company'}. Apply via LinkedIn.",
                        'responsibilities': [],
                        'requirements':     [],
                        'skills':           [],
                        'apply_url':        link_el.get('href', '') if link_el else f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keyword)}",
                        'apply_source':     'LinkedIn',
                        'category':         map_category(title_el.get_text()),
                        'is_featured':      False,
                    })
                except Exception as e:
                    log.debug(f"LinkedIn card error: {e}")

            time.sleep(3)
        except Exception as e:
            log.error(f"LinkedIn error for '{keyword}': {e}")

    log.info(f"LinkedIn total: {len(jobs)}")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 3 — INDEED RSS
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

            root    = ET.fromstring(resp.content)
            channel = root.find('channel')
            if not channel:
                continue
            items = channel.findall('item')

            for item in items:
                try:
                    title    = item.findtext('title', '').strip()
                    link     = item.findtext('link', '').strip()
                    desc_raw = item.findtext('description', '')
                    company  = ''

                    if ' - ' in title:
                        parts   = title.rsplit(' - ', 1)
                        title   = parts[0].strip()
                        company = parts[1].strip()

                    if not title:
                        continue

                    desc_clean  = clean_html(desc_raw)
                    soup_desc   = BeautifulSoup(desc_raw, 'html.parser')
                    direct_link = ''
                    for a in soup_desc.find_all('a', href=True):
                        if is_direct_company_link(a['href']):
                            direct_link = a['href']
                            break

                    apply_url = direct_link or link
                    apply_src = 'Company' if direct_link else 'Indeed'

                    # Extract salary from description if available
                    salary_text = None
                    salary_match = re.search(
                        r'[₹\$]*\s*(\d+(?:\.\d+)?)\s*[-–to]\s*(\d+(?:\.\d+)?)\s*(?:LPA|lakhs?|per month)',
                        desc_clean,
                        re.IGNORECASE
                    )
                    if salary_match:
                        salary_text = salary_match.group(0).strip()

                    jobs.append({
                        'title':            title,
                        'company':          company or 'Hiring Company',
                        'location':         'India',
                        'work_mode':        detect_work_mode(title + ' ' + desc_clean),
                        'job_type':         'Full-time',
                        'experience':       detect_experience(title + ' ' + desc_clean),
                        'salary_text':      salary_text,
                        'description':      desc_clean[:1000] or f"{title} position available in India.",
                        'responsibilities': [],
                        'requirements':     [],
                        'skills':           [],
                        'apply_url':        apply_url,
                        'apply_source':     apply_src,
                        'category':         map_category(title),
                        'is_featured':      False,
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

            cards = soup.select(
                'div[class*="jobCard"], div[class*="job-card"], div[class*="srpResultCard"]'
            )
            log.info(f"Foundit '{keyword}': {len(cards)} cards")

            for card in cards[:per_kw]:
                try:
                    title_el   = card.select_one('h3[class*="title"], a[class*="title"], [class*="jobTitle"]')
                    company_el = card.select_one('[class*="company"], [class*="companyName"]')
                    loc_el     = card.select_one('[class*="location"]')
                    link_el    = card.select_one('a[href]')
                    if not title_el:
                        continue

                    href = link_el.get('href', '') if link_el else ''
                    if href and not href.startswith('http'):
                        href = 'https://www.foundit.in' + href

                    jobs.append({
                        'title':            title_el.get_text(strip=True),
                        'company':          company_el.get_text(strip=True) if company_el else 'Hiring Company',
                        'location':         loc_el.get_text(strip=True) if loc_el else 'India',
                        'work_mode':        detect_work_mode(title_el.get_text()),
                        'job_type':         'Full-time',
                        'experience':       detect_experience(title_el.get_text()),
                        'salary_text':      None,
                        'description':      f"{title_el.get_text(strip=True)} position. Visit Foundit for full details.",
                        'responsibilities': [],
                        'requirements':     [],
                        'skills':           [],
                        'apply_url':        href or 'https://www.foundit.in',
                        'apply_source':     'JobFoundIt',
                        'category':         map_category(title_el.get_text()),
                        'is_featured':      False,
                    })
                except Exception as e:
                    log.debug(f"Foundit card error: {e}")

            time.sleep(2)
        except Exception as e:
            log.error(f"Foundit error for '{keyword}': {e}")

    log.info(f"Foundit total: {len(jobs)}")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 5 — ADZUNA API
# ═══════════════════════════════════════════════════════════════
def scrape_adzuna(keywords: list, limit: int = 50) -> list:
    if not ADZUNA_APP_ID or not ADZUNA_KEY:
        log.warning("Adzuna keys not set. Register free at developer.adzuna.com")
        return []

    log.info("Fetching from Adzuna API...")
    jobs = []
    CAT_MAP = {
        'IT Jobs': 'Technology', 'Engineering Jobs': 'Technology',
        'Design Jobs': 'Design', 'Marketing Jobs': 'Marketing',
        'Sales Jobs': 'Sales', 'HR & Recruitment Jobs': 'HR & Talent',
        'Finance Jobs': 'Finance',
    }

    for keyword in keywords[:5]:
        try:
            resp = requests.get(
                "https://api.adzuna.com/v1/api/jobs/in/search/1",
                params={
                    'app_id': ADZUNA_APP_ID, 'app_key': ADZUNA_KEY,
                    'results_per_page': min(limit // 5, 50),
                    'what': keyword, 'where': 'india', 'max_days_old': 1,
                },
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data.get('results', []):
                apply_url = item.get('apply_url') or item.get('redirect_url', '')
                apply_src = 'Company' if is_direct_company_link(apply_url) else 'Indeed'
                low, high = item.get('salary_min'), item.get('salary_max')
                
                # Format salary: convert from annual paise to LPA
                salary_text = None
                min_salary = None
                max_salary = None
                if low and high:
                    min_salary = low / 100000  # Convert from paise to LPA
                    max_salary = high / 100000
                    salary_text = f"₹{min_salary:.0f}L–{max_salary:.0f}L"

                jobs.append({
                    'title':            item.get('title', '').strip(),
                    'company':          item.get('company', {}).get('display_name', 'Unknown'),
                    'location':         item.get('location', {}).get('display_name', 'India'),
                    'work_mode':        detect_work_mode(item.get('title', '') + item.get('description', '')),
                    'job_type':         'Full-time',
                    'experience':       detect_experience(item.get('title', '') + item.get('description', '')),
                    'salary_text':      salary_text,
                    'min_salary':       min_salary,
                    'max_salary':       max_salary,
                    'description':      clean_html(item.get('description', ''))[:1000],
                    'responsibilities': [],
                    'requirements':     [],
                    'skills':           [],
                    'apply_url':        apply_url,
                    'apply_source':     apply_src,
                    'category':         CAT_MAP.get(
                        item.get('category', {}).get('label', ''),
                        map_category(item.get('title', ''))
                    ),
                    'is_featured':      False,
                })

            log.info(f"Adzuna '{keyword}': {len(data.get('results', []))} results")
            time.sleep(1)
        except Exception as e:
            log.error(f"Adzuna error for '{keyword}': {e}")

    log.info(f"Adzuna total: {len(jobs)}")
    return jobs


# ═══════════════════════════════════════════════════════════════
# SOURCE 6 — COMPANY CAREER PAGES (Lever + Greenhouse ATS APIs)
# ═══════════════════════════════════════════════════════════════
def scrape_company_pages() -> list:
    log.info("Scraping company career pages...")
    jobs = []

    LEVER_COMPANIES = [
        ('razorpay',     'Razorpay',      'Bangalore, India'),
        ('zepto',        'Zepto',         'Mumbai, India'),
        ('cred-club',    'CRED',          'Bangalore, India'),
        ('meesho',       'Meesho',        'Bangalore, India'),
        ('swiggy',       'Swiggy',        'Bangalore, India'),
        ('dunzo',        'Dunzo',         'Bangalore, India'),
        ('browserstack', 'BrowserStack',  'Mumbai, India'),
        ('postman',      'Postman',       'Bangalore, India'),
    ]

    for slug, company, default_loc in LEVER_COMPANIES:
        try:
            url  = f"https://api.lever.co/v0/postings/{slug}?mode=json"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            data = resp.json()
            if not isinstance(data, list):
                continue

            for item in data[:12]:
                title = item.get('text', '').strip()
                if not title:
                    continue
                desc_plain = clean_html(item.get('descriptionPlain', ''))[:800]
                jobs.append({
                    'title':            title,
                    'company':          company,
                    'location':         item.get('categories', {}).get('location', default_loc),
                    'work_mode':        detect_work_mode(item.get('categories', {}).get('location', '') + title),
                    'job_type':         'Full-time',
                    'experience':       detect_experience(title),
                    'salary_text':      None,
                    'description':      desc_plain or f"Join {company} as a {title}.",
                    'responsibilities': [],
                    'requirements':     [],
                    'skills':           [],
                    'apply_url':        item.get('hostedUrl', f'https://jobs.lever.co/{slug}'),
                    'apply_source':     'Company',
                    'category':         map_category(item.get('categories', {}).get('team', '') + ' ' + title),
                    'is_featured':      False,
                })
            log.info(f"{company}: {len(data)} jobs from Lever API")
            time.sleep(0.5)
        except Exception as e:
            log.error(f"{company} Lever error: {e}")

    GREENHOUSE_COMPANIES = [
        ('freshworks', 'Freshworks', 'Chennai, India'),
        ('chargebee',  'Chargebee',  'Chennai, India'),
        ('hasura',     'Hasura',     'Bangalore, India'),
        ('setu',       'Setu',       'Bangalore, India'),
    ]

    for slug, company, default_loc in GREENHOUSE_COMPANIES:
        try:
            url   = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
            resp  = requests.get(url, headers=HEADERS, timeout=15)
            data  = resp.json()
            items = data.get('jobs', [])

            for item in items[:12]:
                title = item.get('title', '').strip()
                if not title:
                    continue
                loc      = item.get('location', {}).get('name', default_loc)
                desc_raw = clean_html(item.get('content', ''))[:800]
                dept     = item.get('departments', [{}])[0].get('name', '') if item.get('departments') else ''
                jobs.append({
                    'title':            title,
                    'company':          company,
                    'location':         loc,
                    'work_mode':        detect_work_mode(loc + title),
                    'job_type':         'Full-time',
                    'experience':       detect_experience(title),
                    'salary_text':      None,
                    'description':      desc_raw or f"Join {company} as a {title}.",
                    'responsibilities': [],
                    'requirements':     [],
                    'skills':           [],
                    'apply_url':        item.get('absolute_url', f'https://boards.greenhouse.io/{slug}'),
                    'apply_source':     'Company',
                    'category':         map_category(dept + ' ' + title),
                    'is_featured':      False,
                })
            log.info(f"{company}: {len(items)} jobs from Greenhouse API")
            time.sleep(0.5)
        except Exception as e:
            log.error(f"{company} Greenhouse error: {e}")

    log.info(f"Company pages total: {len(jobs)}")
    return jobs


# ═══════════════════════════════════════════════════════════════
# MANUAL JOBS
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
# FEATURED ROTATION — exactly 8 random jobs set to True
# All other active jobs set to False
# ═══════════════════════════════════════════════════════════════
def rotate_featured_jobs(db: Client) -> None:
    """
    1. Fetch all active job IDs.
    2. Randomly pick 8.
    3. Bulk-set all active jobs is_featured=False.
    4. Set the 8 chosen ones to True.
    """
    try:
        log.info("Rotating featured jobs (8 random)...")

        # Fetch all active job IDs
        result = db.table('jobs').select('id').eq('is_active', True).execute()
        all_ids = [row['id'] for row in result.data]

        if not all_ids:
            log.warning("No active jobs found for featured rotation.")
            return

        # Reset all to False
        db.table('jobs').update({'is_featured': False}).eq('is_active', True).execute()

        # Pick up to 8 random IDs and set to True
        chosen = random.sample(all_ids, min(8, len(all_ids)))
        for jid in chosen:
            db.table('jobs').update({'is_featured': True}).eq('id', jid).execute()

        log.info(f"✨ Featured rotation done: {len(chosen)} jobs set to featured.")
    except Exception as e:
        log.error(f"Featured rotation error: {e}")


# ═══════════════════════════════════════════════════════════════
# DATABASE: Insert with dedup + views for new jobs only
# ═══════════════════════════════════════════════════════════════
def post_jobs_to_supabase(jobs: list, dry_run: bool = False) -> int:
    if dry_run:
        log.info(f"[DRY RUN] Would process {len(jobs)} jobs:")
        for j in jobs[:10]:
            print(f"  → {j['title']} @ {j['company']} [{j.get('apply_source','?')}]")
            print(f"     responsibilities: {len(j.get('responsibilities',[]))} items")
            print(f"     requirements:     {len(j.get('requirements',[]))} items")
            print(f"     skills:           {j.get('skills',[])[:5]}")
        return 0

    if not SUPABASE_URL or not SUPABASE_KEY:
        log.error("Supabase credentials missing. Check .env file.")
        return 0

    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    inserted, skipped = 0, 0

    for job in jobs:
        # ── Enrich missing structured fields ───────────────────
        job = enrich_job(job)

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
                continue  # ← do NOT touch views for existing rows

            # New job: assign random views (100-2000)
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
                'min_salary':       job.get('min_salary'),
                'max_salary':       job.get('max_salary'),
                'description':      (job.get('description', ''))[:3000],
                'responsibilities': job.get('responsibilities', []),
                'requirements':     job.get('requirements', []),
                'skills':           job.get('skills', []),
                'apply_url':        (job.get('apply_url', ''))[:500],
                'apply_source':     job.get('apply_source', 'Company'),
                'category':         job.get('category', 'Technology'),
                'is_featured':      False,   # featured rotation handles this separately
                'is_active':        True,
                'views':            views,
                'posted_at':        datetime.now(timezone.utc).isoformat(),
            }).execute()

            if result.data:
                inserted += 1
                log.info(
                    f"✅ {title} @ {job.get('company')} "
                    f"[{job.get('apply_source','?')}] | views={views}"
                )
            time.sleep(0.15)

        except Exception as e:
            log.error(f"Insert error for '{title}': {e}")

    log.info(f"\n{'='*50}")
    log.info(f"✅ Inserted: {inserted}  |  ⏭ Duplicates skipped: {skipped}  |  Total: {len(jobs)}")

    # Rotate featured after all inserts
    rotate_featured_jobs(db)

    return inserted


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description='DayDreamer Multi-Source Scraper v3')
    parser.add_argument(
        '--source', default='all',
        choices=['all', 'naukri', 'linkedin', 'indeed', 'foundit', 'adzuna', 'companies', 'manual']
    )
    parser.add_argument('--keyword', default=None, help='Override search keyword')
    parser.add_argument('--limit',   type=int, default=30, help='Max jobs per source')
    parser.add_argument('--dry-run', action='store_true', help='Print without inserting')
    args = parser.parse_args()

    keywords = [args.keyword] if args.keyword else DEFAULT_KEYWORDS

    log.info(f"🚀 DayDreamer Scraper v3 | source={args.source} | limit={args.limit} | {'DRY RUN' if args.dry_run else 'LIVE'}")
    log.info('=' * 60)

    all_jobs: list = []

    if args.source in ('all', 'naukri'):     all_jobs += scrape_naukri(keywords, args.limit)
    if args.source in ('all', 'linkedin'):   all_jobs += scrape_linkedin(keywords, args.limit)
    if args.source in ('all', 'indeed'):     all_jobs += scrape_indeed_rss(keywords, args.limit)
    if args.source in ('all', 'foundit'):    all_jobs += scrape_foundit(keywords, args.limit)
    if args.source in ('all', 'adzuna'):     all_jobs += scrape_adzuna(keywords, args.limit)
    if args.source in ('all', 'companies'):  all_jobs += scrape_company_pages()
    if args.source in ('all', 'manual') and MANUAL_JOBS:
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
