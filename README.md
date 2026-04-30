# 🚀 DayDreamer — Full Stack Job Portal

A professional job listing website built with **Next.js 14**, **Supabase**, **Tailwind CSS**, and a **Python scraper** for daily automated updates.

---

## ✨ Features

- 🏠 Beautiful homepage with hero, job ticker, category grid, featured jobs
- 🔍 Full-text search + filters (category, work mode, job type)
- 📄 Detailed job pages with responsibilities, requirements, skills
- 🤖 Python scraper for automated daily job imports
- ⚙️ GitHub Actions cron job — runs scraper at 7 AM IST every day
- 🎨 Original design — Playfair Display + DM Sans, warm cream palette
- 📱 Fully responsive (mobile + tablet + desktop)
- ⚡ Next.js 14 App Router with server-side rendering
- 🔒 Admin API endpoint for secure job posting
- 🗺️ SEO-ready with OpenGraph metadata

---

## 🗂️ Project Structure

```
DayDreamer/
├── src/
│   ├── app/
│   │   ├── page.tsx              ← Homepage
│   │   ├── layout.tsx            ← Root layout + fonts
│   │   ├── globals.css           ← Global styles
│   │   ├── not-found.tsx         ← 404 page
│   │   ├── jobs/
│   │   │   ├── page.tsx          ← All jobs listing page
│   │   │   └── [id]/
│   │   │       └── page.tsx      ← Job detail page
│   │   └── api/
│   │       └── jobs/
│   │           └── route.ts      ← REST API (GET + POST)
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navbar.tsx
│   │   │   └── Footer.tsx
│   │   └── ui/
│   │       ├── JobCard.tsx
│   │       ├── SearchBar.tsx
│   │       └── CategoryFilter.tsx
│   ├── lib/
│   │   ├── supabase.ts           ← All DB queries
│   │   └── utils.ts              ← Helpers + constants
│   └── types/
│       └── index.ts              ← TypeScript interfaces
├── supabase/
│   └── schema.sql                ← Full DB schema + seed data
├── scripts/
│   ├── scraper.py                ← Python job scraper
│   └── requirements.txt
├── .github/
│   └── workflows/
│       └── daily-scraper.yml     ← GitHub Actions cron
├── .env.example
├── tailwind.config.js
└── README.md
```

---

## 🛠️ Step-by-Step Setup

### Step 1 — Clone & Install

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/DayDreamer.git
cd DayDreamer

# Install Node dependencies
npm install
```

---

### Step 2 — Create a Supabase Project (FREE)

1. Go to **https://supabase.com** → Sign up (free)
2. Click **"New Project"**
3. Choose a name (e.g., `DayDreamer`), set a strong password, choose region **Asia South (Mumbai)**
4. Wait ~2 minutes for the project to provision
5. Go to **Settings → API**
6. Copy:
   - **Project URL** → looks like `https://xxxxxxxxxxxx.supabase.co`
   - **anon/public key** → long JWT string

---

### Step 3 — Create the Database

1. In Supabase dashboard, go to **SQL Editor**
2. Click **"New query"**
3. Open the file `supabase/schema.sql` from this project
4. Paste the entire contents into the SQL editor
5. Click **"Run"** (green button)
6. You should see: `Success. No rows returned`
7. Go to **Table Editor** → you should see tables: `jobs`, `companies`, `categories`
8. Check the `jobs` table — it should already have **10 sample jobs** seeded!

---

### Step 4 — Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env.local

# Open .env.local in any text editor and fill in:
```

Edit `.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
ADMIN_SECRET=make-this-a-long-random-string-nobody-can-guess
```

---

### Step 5 — Run the Development Server

```bash
npm run dev
```

Open **http://localhost:3000** in your browser.

You should see:
- ✅ Homepage with hero and 10 sample jobs
- ✅ /jobs page with search + filters
- ✅ Individual job detail pages

---

### Step 6 — Build & Test Production Build

```bash
npm run build
npm start
```

---

## 🌐 Deploy to Vercel (FREE hosting)

### Step 7 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit — DayDreamer"
git remote add origin https://github.com/YOUR_USERNAME/DayDreamer.git
git push -u origin main
```

### Step 8 — Deploy on Vercel

1. Go to **https://vercel.com** → Sign up / Log in with GitHub
2. Click **"Add New Project"**
3. Import your `DayDreamer` GitHub repository
4. In the **Environment Variables** section, add:
   - `NEXT_PUBLIC_SUPABASE_URL` → your Supabase URL
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` → your Supabase anon key
   - `ADMIN_SECRET` → your admin secret
5. Click **"Deploy"**
6. Wait ~2 minutes → your site is live! 🎉

You'll get a URL like: `https://DayDreamer.vercel.app`

### Step 9 — Add a Custom Domain (Optional, ~₹800/year)

1. Buy a domain from [Porkbun](https://porkbun.com) (cheapest) or [GoDaddy](https://godaddy.com)
2. In Vercel → **Settings → Domains**
3. Add your domain and follow the DNS instructions

---

## 🤖 Python Scraper Setup

### Step 10 — Set Up Python Environment

```bash
cd scripts
python -m venv venv
source venv/bin/activate      # Linux/Mac
# OR
venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

Create `scripts/.env` (copy from root .env.local):
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
ADMIN_SECRET=your-admin-secret
SITE_URL=https://DayDreamer.vercel.app
```

### Step 11 — Test the Scraper

```bash
# Dry run — just print jobs, don't insert
python scraper.py --dry-run

# Insert manually defined jobs (edit MANUAL_JOBS in scraper.py)
python scraper.py --source manual

# Use Adzuna free API (register at developer.adzuna.com first)
python scraper.py --source adzuna --keyword "python developer"

# Run everything
python scraper.py --source all
```

### Step 12 — Register for Adzuna Free API (Optional)

1. Go to **https://developer.adzuna.com**
2. Sign up for a free account
3. Create an app → get `App ID` and `API Key`
4. Add to your `.env.local`:
   ```env
   ADZUNA_APP_ID=your-app-id
   ADZUNA_API_KEY=your-api-key
   ```
5. Free tier: 250 API calls/month, 50 jobs per call = 12,500 jobs/month

---

## ⚙️ Automate with GitHub Actions

### Step 13 — Add Secrets to GitHub

1. Go to your GitHub repo → **Settings → Secrets → Actions**
2. Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase anon key |
| `ADMIN_SECRET` | Your admin secret |
| `ADZUNA_APP_ID` | Adzuna App ID (optional) |
| `ADZUNA_API_KEY` | Adzuna API Key (optional) |
| `VERCEL_DEPLOY_HOOK_URL` | Vercel deploy hook (see below) |
| `SITE_URL` | `https://DayDreamer.vercel.app` |

### Step 14 — Create a Vercel Deploy Hook

1. In Vercel → your project → **Settings → Git → Deploy Hooks**
2. Create a hook named `daily-scraper`
3. Copy the hook URL → add as `VERCEL_DEPLOY_HOOK_URL` secret

### Step 15 — Enable GitHub Actions

The workflow file is already at `.github/workflows/daily-scraper.yml`.

It runs:
- **Every day at 7:00 AM IST** (1:30 AM UTC)
- You can also trigger it manually from GitHub → **Actions → Daily Job Scraper → Run workflow**

---

## 📝 Adding Jobs Manually

### Option A — Supabase Dashboard (Easiest)

1. Go to **supabase.com → Table Editor → jobs**
2. Click **"Insert row"**
3. Fill in all fields and save

### Option B — Python Script

Edit `scripts/scraper.py`, add jobs to the `MANUAL_JOBS` list:

```python
MANUAL_JOBS = [
    {
        "title": "Frontend Developer",
        "company": "My Company",
        "location": "Mumbai, Maharashtra",
        "work_mode": "Remote",          # Remote / Hybrid / On-site
        "job_type": "Full-time",         # Full-time / Part-time / Contract / Internship
        "experience": "2-4 years",
        "salary_text": "12-18 LPA",
        "description": "We are looking for...",
        "responsibilities": ["Build UI components", "..."],
        "requirements": ["3+ years React", "..."],
        "skills": ["React", "TypeScript", "CSS"],
        "apply_url": "https://company.com/jobs/123",
        "apply_source": "Company",       # Company / Naukri / LinkedIn / Indeed / JobFoundIt
        "category": "Technology",
        "is_featured": False,
    },
]
```

Then run:
```bash
python scripts/scraper.py --source manual
```

### Option C — API (For automation / integrations)

```bash
curl -X POST https://DayDreamer.vercel.app/api/jobs \
  -H "Content-Type: application/json" \
  -H "x-admin-secret: YOUR_ADMIN_SECRET" \
  -d '{
    "title": "Data Scientist",
    "company": "Acme Corp",
    "location": "Bangalore",
    "work_mode": "Hybrid",
    "job_type": "Full-time",
    "experience": "2-4 years",
    "description": "Join our data team...",
    "apply_url": "https://acme.com/jobs/ds",
    "apply_source": "Company",
    "category": "Data & AI"
  }'
```

---

## 💰 Hosting Costs

| Service | Free Tier | Paid |
|---------|-----------|------|
| **Vercel** | 100GB bandwidth, unlimited deployments | ~₹1,600/mo (Pro) |
| **Supabase** | 500MB DB, 2GB bandwidth | ~₹2,000/mo (Pro) |
| **GitHub Actions** | 2,000 min/month free | Free for public repos |
| **Domain** | — | ~₹800–1,200/year |
| **Total** | **₹0/month** | Just domain cost |

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, TypeScript |
| Styling | Tailwind CSS, custom design system |
| Database | Supabase (PostgreSQL) |
| Hosting | Vercel |
| Automation | Python 3.12, GitHub Actions |
| Fonts | Playfair Display, DM Sans, DM Mono |

---

## 🤝 Need Help?

- Supabase docs: https://supabase.com/docs
- Next.js docs: https://nextjs.org/docs
- Vercel docs: https://vercel.com/docs
- Adzuna API: https://developer.adzuna.com

---

Built with ❤️ for Indian job seekers.
