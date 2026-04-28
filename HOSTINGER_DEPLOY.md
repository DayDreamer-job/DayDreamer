# 🚀 JobsAdda — Hostinger Deployment + WordPress Automation Guide

---

## ❓ Should I Store the Database on Hostinger or Keep Supabase?

**Keep Supabase. Do NOT move to Hostinger.**

Here's why:

| | Supabase (keep) | Hostinger MySQL |
|---|---|---|
| Free storage | 500MB (enough for ~100,000 jobs) | Depends on plan |
| REST API built-in | ✅ Yes | ❌ Need to build it yourself |
| Real-time updates | ✅ Yes | ❌ No |
| Full-text search | ✅ Built-in | ❌ Manual setup |
| Next.js integration | ✅ One-line SDK | ❌ Complex |
| Connection pooling | ✅ Handled | ❌ Manual |

500MB = roughly **100,000+ job posts** — you will NOT hit this limit for years.
The database stays on Supabase. Only the website files go to Hostinger.

---

## 🏗️ Architecture Overview

```
Your Hostinger Domain
       │
       ▼
jobs.yourdomain.com  (subdomain)
       │
       ▼
Vercel (Next.js website)  ◄──────► Supabase (PostgreSQL database)
       │                                     ▲
       │                                     │
       ▼                                     │
WordPress (yourdomain.com)         Python Scraper (GitHub Actions)
  └── WP JobsAdda Plugin                    │
      posts new jobs ─────────────────────►─┘
      via Supabase API
```

---

## PART 1 — Deploy Next.js to Vercel + Point Subdomain from Hostinger

### Step 1 — Build & Deploy to Vercel

If not already done:

```bash
# In your jobsadda project folder
git init
git add .
git commit -m "jobsadda v1"
git remote add origin https://github.com/YOURUSERNAME/jobsadda.git
git push -u origin main
```

1. Go to https://vercel.com → Log in with GitHub
2. Click **"Add New Project"** → Import `jobsadda` repo
3. Add Environment Variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `ADMIN_SECRET`
4. Click **Deploy**
5. Your site is live at `https://jobsadda.vercel.app`

---

### Step 2 — Add Subdomain on Hostinger

1. Log in to **hPanel** (Hostinger control panel)
2. Go to **Domains → your domain → Subdomains**
3. Click **"Create Subdomain"**
4. Enter: `jobs` → so it becomes `jobs.yourdomain.com`
5. For the **Document Root**, set it to `/public_html/jobs` (doesn't matter since we're pointing to Vercel via DNS — just create it)
6. Click **Create**

---

### Step 3 — Point the Subdomain DNS to Vercel

1. Still in hPanel → go to **DNS Zone** for your domain
2. Find the DNS record for `jobs.yourdomain.com` that was auto-created (it'll be an A record)
3. **Delete** that A record
4. **Add a new CNAME record**:
   - **Name/Host**: `jobs`
   - **Value/Points to**: `cname.vercel-dns.com`
   - **TTL**: 3600 (or Auto)
5. Save

---

### Step 4 — Add Custom Domain in Vercel

1. In Vercel → your project → **Settings → Domains**
2. Click **"Add Domain"**
3. Enter: `jobs.yourdomain.com`
4. Vercel will verify → click **"Verify"**
5. Wait 5-30 minutes for DNS propagation
6. Your site is now live at: **https://jobs.yourdomain.com** ✅

---

## PART 2 — WordPress Job Posting Automation

### Overview

You have WordPress on your main Hostinger domain. We'll install a simple custom plugin that adds a **"Add New Job"** form inside WordPress. When you fill in the form and click Submit, it posts the job directly into your Supabase database → it instantly appears on your Next.js site.

**No coding required to add jobs. Just fill a form in WordPress.**

---

### Step 5 — Install the WordPress Plugin

#### Method A — Upload via WordPress Dashboard (Easiest)

1. Download the plugin file: `jobsadda-poster.php` (in this folder at `wordpress/jobsadda-poster.php`)
2. In WordPress Admin → **Plugins → Add New → Upload Plugin**
3. Upload the `.php` file wrapped in a `.zip`
4. Click **"Install Now"** → **"Activate Plugin"**

#### Method B — Upload via Hostinger File Manager

1. In hPanel → **File Manager**
2. Navigate to: `/public_html/wp-content/plugins/`
3. Create folder: `jobsadda-poster`
4. Upload `jobsadda-poster.php` into that folder
5. In WordPress → **Plugins** → find "JobsAdda Poster" → **Activate**

---

### Step 6 — Configure the Plugin

1. In WordPress Admin → **JobsAdda → Settings**
2. Enter:
   - **Supabase URL**: `https://xxxx.supabase.co`
   - **Supabase Anon Key**: your anon key
   - **Admin Secret**: your admin secret from `.env.local`
3. Save Settings

---

### Step 7 — Post a New Job from WordPress

1. WordPress Admin → **JobsAdda → Add New Job**
2. Fill in the form (title, company, location, description, apply link, etc.)
3. Click **"Post Job to JobsAdda"**
4. ✅ Job appears on your Next.js website immediately!

---

## PART 3 — Python Automation from Hostinger

If you want to run the Python scraper on Hostinger's server (instead of GitHub Actions):

### Step 8 — Enable SSH on Hostinger

1. hPanel → **Advanced → SSH Access**
2. Enable SSH
3. Note your SSH username and server hostname

### Step 9 — Connect via SSH

```bash
# On your computer terminal / PuTTY (Windows)
ssh username@server123.hostinger.com
# Enter your password
```

### Step 10 — Set Up Python on Hostinger

```bash
# Check Python version (Hostinger has Python 3)
python3 --version

# Create a folder for your scripts
mkdir ~/jobsadda-scripts
cd ~/jobsadda-scripts

# Upload your scraper files via File Manager or SCP:
# On your computer:
# scp scripts/scraper.py username@server.hostinger.com:~/jobsadda-scripts/
# scp scripts/requirements.txt username@server.hostinger.com:~/jobsadda-scripts/

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 11 — Create .env file on Hostinger

```bash
nano ~/jobsadda-scripts/.env
```

Paste:
```
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
ADMIN_SECRET=your-admin-secret
SITE_URL=https://jobs.yourdomain.com
```
Press `Ctrl+X` → `Y` → `Enter` to save.

### Step 12 — Test the scraper

```bash
cd ~/jobsadda-scripts
source venv/bin/activate
python3 scraper.py --dry-run
```

### Step 13 — Schedule with Cron (Hostinger Cron Jobs)

1. hPanel → **Advanced → Cron Jobs**
2. Click **"Add New Cron Job"**
3. Set schedule to: **Daily at 7:00 AM**
4. Command:
```bash
/home/username/jobsadda-scripts/venv/bin/python3 /home/username/jobsadda-scripts/scraper.py --source all >> /home/username/jobsadda-scripts/scraper.log 2>&1
```
(Replace `username` with your actual Hostinger SSH username)
5. Save

The scraper now runs every day automatically on Hostinger. ✅

---

## PART 4 — Keeping the Database Small (Under 500MB Forever)

### Auto-Expire Old Jobs

Add this SQL in Supabase SQL Editor — run it once:

```sql
-- Auto-delete jobs older than 60 days (run this as a cron in Supabase)
create or replace function cleanup_expired_jobs()
returns void as $$
  update jobs set is_active = false
  where expires_at < now() and is_active = true;
$$ language sql;

-- Schedule it in Supabase: Dashboard → Database → Extensions → pg_cron
-- Then: select cron.schedule('cleanup-jobs', '0 2 * * *', 'select cleanup_expired_jobs()');
```

### Storage Reality Check

- Each job row ≈ 3-5 KB
- 500MB free / 4KB avg = **125,000 jobs**
- If you post 10 jobs/day and expire after 60 days = only 600 rows active at any time
- You will **never** hit 500MB at this rate

---

## 📋 Quick Summary of What Goes Where

| Component | Where it lives | Cost |
|---|---|---|
| Next.js website | Vercel | Free |
| Database (jobs) | Supabase | Free |
| Domain & DNS | Hostinger | Already paid |
| WordPress | Hostinger | Already paid |
| Python scraper | GitHub Actions OR Hostinger cron | Free |
| WordPress plugin | Hostinger WordPress | Free |

**Total ongoing cost: ₹0/month** (just your existing Hostinger plan)

---

## 🔧 Troubleshooting

**Subdomain not working after 30 mins?**
- Check DNS propagation: https://dnschecker.org → enter `jobs.yourdomain.com`
- CNAME record value must be exactly: `cname.vercel-dns.com`

**Jobs not appearing on site after adding in Supabase?**
- Next.js uses ISR (Incremental Static Regeneration) — new jobs appear within 60 seconds
- Force a redeploy on Vercel to see them immediately

**WordPress plugin can't connect to Supabase?**
- Check Supabase RLS policies — anon key must have INSERT permission
- Run this in Supabase SQL Editor:
```sql
create policy "Allow anon insert" on jobs for insert to anon with check (true);
```
