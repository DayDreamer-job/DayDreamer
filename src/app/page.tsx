import Link from "next/link";
import {
  ArrowRight,
  Briefcase,
  TrendingUp,
  Users,
  Zap,
  MapPin,
  Star,
} from "lucide-react";
import JobCard from "@/components/ui/JobCard";
import SearchBar from "@/components/ui/SearchBar";
import { getFeaturedJobs, getJobCount, getCategories } from "@/lib/supabase";
import { CATEGORY_ICONS } from "@/lib/utils";
import { Suspense } from "react";

export const revalidate = 60; // Revalidate every 60 seconds

const TICKER_COMPANIES = [
  "Google",
  "Microsoft",
  "Amazon",
  "Flipkart",
  "Zomato",
  "Razorpay",
  "CRED",
  "Swiggy",
  "Meesho",
  "PhonePe",
  "Infosys",
  "TCS",
  "Wipro",
  "Freshworks",
  "Zoho",
  "Byju's",
  "Ola",
  "Paytm",
  "Dream11",
  "Nykaa",
];

export default async function HomePage() {
  const [featuredJobs, jobCount, categories] = await Promise.all([
    getFeaturedJobs(6).catch(() => []),
    getJobCount().catch(() => 0),
    getCategories().catch(() => []),
  ]);

  return (
    <>
      {/* ── HERO ─────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col justify-center overflow-hidden pt-16">
        {/* Background */}
        <div className="absolute inset-0 dot-pattern opacity-60" />
        <div className="absolute top-1/4 right-0 w-[600px] h-[600px] bg-brand-100/40 rounded-full blur-3xl -translate-y-1/4 translate-x-1/4" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-amber-50/60 rounded-full blur-3xl translate-y-1/4 -translate-x-1/4" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="max-w-4xl">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-brand-50 border border-brand-200 text-brand-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-6 animate-on-mount animate-fade-up">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse-slow" />
              {jobCount.toLocaleString()}+ Active Jobs Today
            </div>

            {/* Headline */}
            <h1 className="font-display text-5xl md:text-7xl font-bold text-ink leading-[1.05] mb-6 animate-on-mount animate-fade-up animation-delay-100">
              Your Next Big{" "}
              <span className="relative inline-block">
                <span className="gradient-text">Opportunity</span>
                <svg
                  className="absolute -bottom-2 left-0 w-full"
                  viewBox="0 0 300 12"
                  fill="none"
                >
                  <path
                    d="M2 8C50 3 100 1 150 5C200 9 250 7 298 4"
                    stroke="#f97316"
                    strokeWidth="3"
                    strokeLinecap="round"
                  />
                </svg>
              </span>{" "}
              Starts Here
            </h1>

            <p className="text-lg md:text-xl text-ink-subtle max-w-2xl leading-relaxed mb-10 animate-on-mount animate-fade-up animation-delay-200">
              Handpicked jobs for freshers and professionals across India.
              Updated daily from top companies, startups, and leading job
              platforms.
            </p>

            {/* Search */}
            <div className="animate-on-mount animate-fade-up animation-delay-300">
              <Suspense>
                <SearchBar />
              </Suspense>
            </div>

            {/* Quick links */}
            <div className="flex flex-wrap gap-2 mt-5 animate-on-mount animate-fade-up animation-delay-400">
              <span className="text-xs text-ink-subtle">Popular:</span>
              {[
                "Remote Jobs",
                "Fresher Jobs",
                "Python Developer",
                "UI/UX Designer",
                "Data Scientist",
              ].map((term) => (
                <Link
                  key={term}
                  href={`/jobs?search=${encodeURIComponent(term)}`}
                  className="text-xs text-ink-subtle border border-cream-border bg-white rounded-full px-3 py-1 hover:border-ink/40 hover:text-ink transition-all"
                >
                  {term}
                </Link>
              ))}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 max-w-lg mt-16 animate-on-mount animate-fade-up animation-delay-500">
            {[
              { icon: Briefcase, value: `${jobCount}+`, label: "Live Jobs" },
              { icon: Users, value: "500+", label: "Companies" },
              { icon: TrendingUp, value: "Daily", label: "Updates" },
            ].map(({ icon: Icon, value, label }) => (
              <div key={label} className="card text-center py-4">
                <Icon size={18} className="text-brand-500 mx-auto mb-1.5" />
                <div className="font-display font-bold text-xl text-ink">
                  {value}
                </div>
                <div className="text-xs text-ink-subtle mt-0.5">{label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Ticker */}
        <div className="relative border-y border-cream-border bg-white/70 backdrop-blur-sm overflow-hidden marquee-container">
          <div className="flex animate-marquee marquee-inner whitespace-nowrap py-3">
            {[...TICKER_COMPANIES, ...TICKER_COMPANIES].map((company, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-3 mx-6 text-sm text-ink-subtle font-medium"
              >
                <span className="w-1 h-1 rounded-full bg-brand-400" />
                {company}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── CATEGORIES ───────────────────────────────── */}
      <section className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-end justify-between mb-10">
          <div>
            <p className="text-brand-500 font-semibold text-sm uppercase tracking-widest mb-2">
              Explore by Category
            </p>
            <h2 className="section-title">Browse by Field</h2>
          </div>
          <Link
            href="/jobs"
            className="hidden sm:flex items-center gap-1 text-sm font-medium text-ink-subtle hover:text-ink transition-colors"
          >
            View all <ArrowRight size={14} />
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {(categories.length > 0
            ? categories
            : Object.entries(CATEGORY_ICONS).map(([name, icon]) => ({
                name,
                icon,
                slug: name.toLowerCase(),
                color: "#f97316",
                id: 0,
              }))
          ).map((cat) => (
            <Link
              key={cat.name}
              href={`/jobs?category=${encodeURIComponent(cat.name)}`}
              className="card-hover flex flex-col items-center justify-center gap-2 py-7 text-center group"
            >
              <span className="text-3xl group-hover:scale-110 transition-transform duration-200">
                {cat.icon}
              </span>
              <span className="font-semibold text-sm text-ink">{cat.name}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* ── FEATURED JOBS ────────────────────────────── */}
      <section className="py-20 bg-cream-warm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-end justify-between mb-10">
            <div>
              <p className="text-brand-500 font-semibold text-sm uppercase tracking-widest mb-2">
                Hand-picked For You
              </p>
              <h2 className="section-title flex items-center gap-3">
                <Star
                  size={28}
                  className="text-brand-500"
                  fill="currentColor"
                />
                Featured Jobs
              </h2>
            </div>
            <Link
              href="/jobs?featured=true"
              className="hidden sm:flex items-center gap-1 text-sm font-medium text-ink-subtle hover:text-ink transition-colors"
            >
              All featured <ArrowRight size={14} />
            </Link>
          </div>

          {featuredJobs.length === 0 ? (
            <div className="card text-center py-16 text-ink-subtle">
              <Briefcase size={32} className="mx-auto mb-4 opacity-30" />
              <p className="font-medium">
                No jobs found. Add your Supabase credentials to see live data.
              </p>
              <p className="text-sm mt-2">
                Check the README for setup instructions.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {featuredJobs.map((job) => (
                <JobCard key={job.id} job={job} featured />
              ))}
            </div>
          )}

          <div className="text-center mt-10">
            <Link href="/jobs" className="btn-primary">
              Browse All Jobs
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      {/* ── WHY DAYDREAMER ─────────────────────────────── */}
      <section className="py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <p className="text-brand-500 font-semibold text-sm uppercase tracking-widest mb-2">
            Why Choose Us
          </p>
          <h2 className="section-title">Jobs the way you deserve them</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {[
            {
              icon: "⚡",
              title: "Daily Updates",
              desc: "Fresh jobs added every single day from top companies, startups, and leading job platforms across India.",
            },
            {
              icon: "🎯",
              title: "Curated Quality",
              desc: "Every job is manually verified. No spam, no duplicates — only real opportunities worth your time.",
            },
            {
              icon: "🔗",
              title: "Direct Apply Links",
              desc: "Apply directly on company websites or trusted platforms. Zero middlemen, zero registration walls.",
            },
          ].map((item) => (
            <div key={item.title} className="card-hover p-8">
              <div className="text-4xl mb-4">{item.icon}</div>
              <h3 className="font-display font-bold text-xl text-ink mb-3">
                {item.title}
              </h3>
              <p className="text-sm text-ink-subtle leading-relaxed">
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────── */}
      <section className="mx-4 sm:mx-8 lg:mx-auto max-w-6xl mb-24 rounded-3xl bg-ink text-white overflow-hidden relative">
        <div className="absolute inset-0 dot-pattern opacity-10" />
        <div className="absolute top-0 right-0 w-64 h-64 bg-brand-500/20 rounded-full blur-3xl" />
        <div className="relative px-8 py-16 md:py-20 text-center">
          <Zap size={32} className="text-brand-400 mx-auto mb-4" />
          <h2 className="font-display text-4xl md:text-5xl font-bold mb-4">
            Ready to find your next job?
          </h2>
          <p className="text-white/60 text-lg mb-8 max-w-xl mx-auto">
            Browse {jobCount}+ curated opportunities and apply directly. No
            account needed.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/jobs" className="btn-apply text-base px-8 py-4">
              Explore All Jobs
              <ArrowRight size={18} />
            </Link>
            <Link
              href="/jobs?work_mode=Remote"
              className="inline-flex items-center gap-2 bg-white/10 text-white border border-white/20 px-8 py-4 rounded-full font-semibold text-base hover:bg-white/20 transition-all"
            >
              <MapPin size={16} />
              Remote Jobs
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
