-- ============================================================
-- DayDreamer — Supabase Database Schema
-- Run this in Supabase SQL Editor (supabase.com → SQL Editor)
-- ============================================================

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- ── JOBS TABLE ──────────────────────────────────────────────
create table if not exists jobs (
  id            uuid primary key default uuid_generate_v4(),
  title         text not null,
  company       text not null,
  logo_url      text,
  location      text not null,
  work_mode     text not null default 'Hybrid',       -- Remote / Hybrid / On-site
  job_type      text not null default 'Full-time',    -- Full-time / Part-time / Contract / Internship
  experience    text not null,                        -- e.g. "0-2 years" / "Fresher"
  salary_min    integer,                              -- in LPA (lakhs per annum)
  salary_max    integer,
  salary_text   text,                                 -- e.g. "8-12 LPA" or "Not disclosed"
  description   text not null,
  responsibilities text[],
  requirements  text[],
  skills        text[],
  apply_url     text not null,
  apply_source  text not null default 'Company',      -- Company / Naukri / LinkedIn / Indeed / JobFoundIt
  category      text not null default 'Technology',
  is_featured   boolean default false,
  is_active     boolean default true,
  posted_at     timestamptz default now(),
  expires_at    timestamptz default (now() + interval '30 days'),
  views         integer default 0,
  created_at    timestamptz default now(),
  updated_at    timestamptz default now()
);

-- ── COMPANIES TABLE ──────────────────────────────────────────
create table if not exists companies (
  id            uuid primary key default uuid_generate_v4(),
  name          text not null unique,
  logo_url      text,
  website       text,
  industry      text,
  size          text,    -- "1-10" / "11-50" / "51-200" / "201-500" / "500+"
  description   text,
  created_at    timestamptz default now()
);

-- ── CATEGORIES TABLE ─────────────────────────────────────────
create table if not exists categories (
  id    serial primary key,
  name  text not null unique,
  slug  text not null unique,
  icon  text,
  color text
);

-- ── INDEXES ──────────────────────────────────────────────────
create index if not exists jobs_posted_at_idx on jobs(posted_at desc);
create index if not exists jobs_category_idx on jobs(category);
create index if not exists jobs_company_idx on jobs(company);
create index if not exists jobs_is_active_idx on jobs(is_active);
create index if not exists jobs_work_mode_idx on jobs(work_mode);

-- ── FULL TEXT SEARCH ─────────────────────────────────────────
alter table jobs add column if not exists fts tsvector
  generated always as (
    to_tsvector('english',
      coalesce(title, '') || ' ' ||
      coalesce(company, '') || ' ' ||
      coalesce(location, '') || ' ' ||
      coalesce(description, '')
    )
  ) stored;

create index if not exists jobs_fts_idx on jobs using gin(fts);

-- ── ROW LEVEL SECURITY ────────────────────────────────────────
alter table jobs enable row level security;
alter table companies enable row level security;
alter table categories enable row level security;

-- Public read access
create policy "Public can read active jobs"
  on jobs for select using (is_active = true);

create policy "Public can read companies"
  on companies for select using (true);

create policy "Public can read categories"
  on categories for select using (true);

-- ── SEED CATEGORIES ──────────────────────────────────────────
insert into categories (name, slug, icon, color) values
  ('Technology', 'technology', '💻', '#6366f1'),
  ('Design', 'design', '🎨', '#ec4899'),
  ('Marketing', 'marketing', '📣', '#f59e0b'),
  ('Finance', 'finance', '💰', '#10b981'),
  ('Sales', 'sales', '📈', '#3b82f6'),
  ('HR & Talent', 'hr', '👥', '#8b5cf6'),
  ('Data & AI', 'data-ai', '🤖', '#06b6d4'),
  ('Product', 'product', '📦', '#f97316')
on conflict (slug) do nothing;

-- ── SEED SAMPLE JOBS (10 realistic entries) ──────────────────
insert into jobs (title, company, location, work_mode, job_type, experience, salary_min, salary_max, salary_text, description, responsibilities, requirements, skills, apply_url, apply_source, category, is_featured) values

('Python Backend Developer', 'Wonkstec Technologies', 'Bangalore, Karnataka', 'Remote', 'Full-time', '1-3 years', 8, 14,  '8-14 LPA',
 'We are looking for a skilled Python Backend Developer to join our growing engineering team. You will build scalable APIs, work with modern frameworks, and collaborate with a distributed team.',
 ARRAY['Design and implement RESTful APIs using FastAPI or Django', 'Write clean, testable, well-documented code', 'Collaborate with frontend engineers to integrate APIs', 'Participate in code reviews and technical design discussions'],
 ARRAY['1+ years of Python experience', 'Familiarity with REST API design principles', 'Experience with SQL and NoSQL databases', 'Good understanding of version control with Git'],
 ARRAY['Python', 'FastAPI', 'Django', 'PostgreSQL', 'Redis', 'Docker', 'Git'],
 'https://linkedin.com/jobs/view/python-developer', 'LinkedIn', 'Technology', true),

('UI/UX Designer', 'Zomato', 'Gurugram, Haryana', 'Hybrid', 'Full-time', '2-4 years', 12, 20, '12-20 LPA',
 'Zomato is looking for a passionate UI/UX Designer to shape world-class food discovery experiences for millions of users across India and the world.',
 ARRAY['Create wireframes, prototypes and high-fidelity mockups', 'Conduct user research and usability testing', 'Collaborate with product and engineering teams', 'Maintain and evolve the Zomato design system'],
 ARRAY['2+ years of product design experience', 'Strong portfolio demonstrating mobile and web design', 'Proficiency in Figma', 'Understanding of user-centered design principles'],
 ARRAY['Figma', 'Prototyping', 'User Research', 'Design Systems', 'Mobile Design', 'Usability Testing'],
 'https://www.naukri.com/job-listings-ui-ux-designer-zomato', 'Naukri', 'Design', true),

('Data Scientist — Fresher', 'Mu Sigma', 'Bangalore, Karnataka', 'On-site', 'Full-time', 'Fresher', 5, 9, '5-9 LPA',
 'Mu Sigma invites fresh graduates passionate about data to join its Decision Sciences team. You will work on real-world analytics problems across Fortune 500 clients.',
 ARRAY['Analyse large datasets to extract actionable insights', 'Build and validate statistical and ML models', 'Present findings to client stakeholders', 'Work in cross-functional agile teams'],
 ARRAY['B.Tech / M.Tech / MBA with quantitative background', 'Strong foundation in statistics and probability', 'Python or R programming skills', 'Fresher or up to 1 year of experience'],
 ARRAY['Python', 'R', 'Machine Learning', 'Statistics', 'SQL', 'Tableau', 'Excel'],
 'https://www.musigma.com/careers', 'Company', 'Data & AI', false),

('Frontend Engineer (React)', 'Razorpay', 'Bangalore, Karnataka', 'Hybrid', 'Full-time', '2-5 years', 18, 30, '18-30 LPA',
 'Razorpay is hiring a Frontend Engineer to build the next generation of payments infrastructure used by 8M+ businesses. You will own entire product surfaces from design to delivery.',
 ARRAY['Build performant, accessible React applications', 'Architect reusable component libraries', 'Optimise web vitals and page performance', 'Mentor junior engineers and drive best practices'],
 ARRAY['3+ years of React experience', 'Deep understanding of JavaScript fundamentals', 'Experience with state management (Redux / Zustand)', 'Familiarity with GraphQL or REST APIs'],
 ARRAY['React', 'TypeScript', 'Next.js', 'GraphQL', 'Tailwind CSS', 'Webpack', 'Testing'],
 'https://razorpay.com/jobs/', 'Company', 'Technology', true),

('DevOps Engineer', 'Infosys', 'Pune, Maharashtra', 'On-site', 'Full-time', '3-5 years', 10, 18, '10-18 LPA',
 'Infosys is looking for a DevOps Engineer to streamline CI/CD pipelines and cloud infrastructure for enterprise clients. You will work with leading-edge cloud platforms and automation tools.',
 ARRAY['Design and maintain CI/CD pipelines using Jenkins or GitHub Actions', 'Manage Kubernetes clusters and containerised workloads', 'Monitor infrastructure health and respond to incidents', 'Collaborate with development teams on deployment strategies'],
 ARRAY['3+ years of DevOps/SRE experience', 'Hands-on with AWS, GCP, or Azure', 'Kubernetes administration experience', 'Scripting skills in Bash or Python'],
 ARRAY['Docker', 'Kubernetes', 'AWS', 'Terraform', 'Jenkins', 'GitHub Actions', 'Linux', 'Python'],
 'https://www.naukri.com/jobs-in-infosys', 'Naukri', 'Technology', false),

('Product Manager', 'Meesho', 'Bangalore, Karnataka', 'Remote', 'Full-time', '3-6 years', 22, 40, '22-40 LPA',
 'Meesho is on a mission to democratise internet commerce for the next billion Indians. We need a Product Manager to lead our seller growth product area.',
 ARRAY['Define product vision and roadmap for seller tools', 'Partner with design, engineering and analytics teams', 'Drive product launches and measure impact with data', 'Identify opportunities through user research and market analysis'],
 ARRAY['3+ years of product management experience', 'Track record of shipping products at scale', 'Strong analytical mindset with SQL skills', 'Excellent communication and stakeholder management'],
 ARRAY['Product Strategy', 'SQL', 'Roadmapping', 'A/B Testing', 'User Research', 'Figma', 'JIRA'],
 'https://meesho.io/careers', 'Company', 'Product', true),

('Digital Marketing Executive', 'Byju''s', 'Remote, India', 'Remote', 'Full-time', '1-3 years', 4, 8, '4-8 LPA',
 'Join Byju''s growth marketing team and own performance marketing campaigns across Google, Meta, and other digital channels to drive learner acquisition at scale.',
 ARRAY['Plan and execute paid campaigns on Google Ads and Meta Ads', 'Analyse campaign performance and optimise for CAC and ROAS', 'Coordinate with creative team for ad creatives', 'Prepare weekly performance reports for leadership'],
 ARRAY['1+ years in performance marketing', 'Google Ads certification preferred', 'Experience with Google Analytics 4', 'Strong excel/sheets skills'],
 ARRAY['Google Ads', 'Meta Ads', 'SEO', 'Google Analytics', 'Excel', 'Email Marketing', 'Canva'],
 'https://indeed.com/jobs?q=digital+marketing+byjus', 'Indeed', 'Marketing', false),

('HR Generalist', 'Freshworks', 'Chennai, Tamil Nadu', 'Hybrid', 'Full-time', '2-4 years', 7, 12, '7-12 LPA',
 'Freshworks is looking for an HR Generalist to support people operations for our fastest growing business units. You''ll be the go-to person for everything from onboarding to employee relations.',
 ARRAY['Manage end-to-end onboarding for new hires', 'Handle employee relations, grievances, and HR queries', 'Partner with talent acquisition for hiring drives', 'Maintain HRIS data accuracy and generate reports'],
 ARRAY['2+ years of HR operations experience', 'Knowledge of Indian labour laws', 'Experience with HRIS tools (Darwinbox / Zoho People)', 'Strong interpersonal and communication skills'],
 ARRAY['HRIS', 'Recruitment', 'Employee Relations', 'Labour Law', 'Onboarding', 'Excel', 'Darwinbox'],
 'https://www.freshworks.com/company/careers/', 'Company', 'HR & Talent', false),

('Full Stack Engineer — Internship', 'CRED', 'Bangalore, Karnataka', 'Hybrid', 'Internship', 'Fresher', 3, 5, '3-5 LPA (Stipend)',
 'CRED is offering a 6-month full stack engineering internship for pre-final and final year students. You''ll ship real features, not toy projects — we believe in giving interns ownership.',
 ARRAY['Develop features across the full stack (React + Node.js)', 'Write unit and integration tests', 'Participate in design discussions and stand-ups', 'Document your work and present demos bi-weekly'],
 ARRAY['Pursuing B.Tech/B.E in CS or related field', 'Solid understanding of JavaScript/TypeScript', 'Familiarity with React and any backend framework', 'Active GitHub profile is a plus'],
 ARRAY['React', 'Node.js', 'TypeScript', 'MongoDB', 'REST APIs', 'Git', 'Jest'],
 'https://www.cred.club/careers', 'Company', 'Technology', false),

('Sales Development Representative', 'Chargebee', 'Chennai, Tamil Nadu', 'On-site', 'Full-time', '0-2 years', 5, 9, '5-9 LPA + Incentives',
 'Chargebee is a global SaaS company powering subscription billing for thousands of businesses. We''re looking for SDRs to join our outbound sales engine and accelerate global revenue growth.',
 ARRAY['Prospect and qualify outbound leads via email, LinkedIn, and cold calls', 'Book meetings for Account Executive team', 'Maintain accurate CRM records in Salesforce', 'Consistently hit monthly meeting quotas'],
 ARRAY['0-2 years of B2B sales or SDR experience', 'Excellent written and verbal English', 'Hunger to learn and grow in a SaaS sales career', 'CRM experience (Salesforce preferred)'],
 ARRAY['CRM', 'Salesforce', 'Cold Outreach', 'LinkedIn Sales Navigator', 'Email Prospecting', 'SaaS'],
 'https://www.chargebee.com/careers/', 'Company', 'Sales', false);

-- ── VIEWS INCREMENT FUNCTION ──────────────────────────────────
create or replace function increment_job_views(job_id uuid)
returns void as $$
  update jobs set views = views + 1 where id = job_id;
$$ language sql;

-- Allow public to call the increment function
grant execute on function increment_job_views(uuid) to anon, authenticated;
