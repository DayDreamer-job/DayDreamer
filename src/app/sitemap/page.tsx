import { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Sitemap - DayDreamer",
  description: "Complete sitemap of DayDreamer with all pages and job categories.",
};

export default function Sitemap() {
  const sections = [
    {
      title: "Main Pages",
      links: [
        { href: "/", label: "Home" },
        { href: "/jobs", label: "Browse All Jobs" },
        { href: "/about", label: "About Us" },
        { href: "/contact", label: "Contact Us" },
      ],
    },
    {
      title: "Job Categories",
      links: [
        { href: "/jobs?category=Technology", label: "Technology Jobs" },
        { href: "/jobs?category=Design", label: "Design Jobs" },
        { href: "/jobs?category=Marketing", label: "Marketing Jobs" },
        { href: "/jobs?category=Finance", label: "Finance Jobs" },
        { href: "/jobs?category=Sales", label: "Sales Jobs" },
        { href: "/jobs?category=HR", label: "HR & Recruitment" },
      ],
    },
    {
      title: "Job Types",
      links: [
        { href: "/jobs?job_type=Full-time", label: "Full-time Jobs" },
        { href: "/jobs?job_type=Part-time", label: "Part-time Jobs" },
        { href: "/jobs?job_type=Contract", label: "Contract Jobs" },
        { href: "/jobs?job_type=Internship", label: "Internships" },
        { href: "/jobs?job_type=Freelance", label: "Freelance Jobs" },
      ],
    },
    {
      title: "Work Mode",
      links: [
        { href: "/jobs?work_mode=Remote", label: "Remote Jobs" },
        { href: "/jobs?work_mode=On-site", label: "On-site Jobs" },
        { href: "/jobs?work_mode=Hybrid", label: "Hybrid Jobs" },
      ],
    },
    {
      title: "Experience Level",
      links: [
        { href: "/jobs?experience=Fresher", label: "Fresher Jobs" },
        { href: "/jobs?experience=Entry-Level", label: "Entry-Level Jobs" },
        { href: "/jobs?experience=Mid-Level", label: "Mid-Level Jobs" },
        { href: "/jobs?experience=Senior", label: "Senior Jobs" },
        { href: "/jobs?experience=Executive", label: "Executive Jobs" },
      ],
    },
    {
      title: "Cities & Locations",
      links: [
        { href: "/jobs?location=Delhi", label: "Jobs in Delhi" },
        { href: "/jobs?location=Mumbai", label: "Jobs in Mumbai" },
        { href: "/jobs?location=Bangalore", label: "Jobs in Bangalore" },
        { href: "/jobs?location=Hyderabad", label: "Jobs in Hyderabad" },
        { href: "/jobs?location=Pune", label: "Jobs in Pune" },
        { href: "/jobs?location=Chennai", label: "Jobs in Chennai" },
        { href: "/jobs?location=Kolkata", label: "Jobs in Kolkata" },
      ],
    },
    {
      title: "Legal & Policies",
      links: [
        { href: "/privacy", label: "Privacy Policy" },
        { href: "/terms", label: "Terms of Use" },
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-cream to-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h1 className="text-4xl font-display font-bold text-ink mb-4">
          <span className="text-brand-500">Sitemap</span>
        </h1>
        <p className="text-lg text-ink/60 mb-12">
          Complete directory of all pages and job categories on DayDreamer
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {sections.map((section, idx) => (
            <div
              key={idx}
              className="bg-white rounded-lg border-2 border-brand-100 p-6"
            >
              <h2 className="text-lg font-display font-bold text-ink mb-4">
                {section.title}
              </h2>
              <ul className="space-y-2.5">
                {section.links.map((link, linkIdx) => (
                  <li key={linkIdx}>
                    <Link
                      href={link.href}
                      className="text-brand-500 hover:text-brand-600 font-medium transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Additional Info */}
        <div className="mt-16 pt-16 border-t-2 border-brand-100">
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-brand-50 rounded-lg p-8">
              <h2 className="text-2xl font-display font-bold text-ink mb-4">
                About DayDreamer
              </h2>
              <p className="text-ink/70 leading-relaxed mb-4">
                DayDreamer is your daily destination for fresh job opportunities
                across India. We curate jobs for freshers, mid-level
                professionals, and senior leaders across all major industries.
              </p>
              <p className="text-ink/70 leading-relaxed">
                New jobs are added every day at 7 AM IST. Explore our
                comprehensive database of legitimate, verified job opportunities
                from top companies, startups, and enterprises across India.
              </p>
            </div>

            <div className="bg-brand-50 rounded-lg p-8">
              <h2 className="text-2xl font-display font-bold text-ink mb-4">
                Quick Stats
              </h2>
              <div className="space-y-4">
                <div>
                  <p className="text-3xl font-bold text-brand-500">1000+</p>
                  <p className="text-ink/70">Active Job Listings</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-brand-500">50+</p>
                  <p className="text-ink/70">Job Categories</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-brand-500">25+</p>
                  <p className="text-ink/70">Major Cities</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Help Section */}
        <div className="mt-16 bg-white rounded-lg border-2 border-brand-100 p-8">
          <h2 className="text-2xl font-display font-bold text-ink mb-6">
            Can't Find What You're Looking For?
          </h2>
          <p className="text-lg text-ink/70 mb-6">
            If you can't find the job or information you're looking for, we're
            here to help:
          </p>
          <div className="grid md:grid-cols-2 gap-6">
            <Link
              href="/contact"
              className="bg-brand-500 hover:bg-brand-600 text-white font-semibold py-3 px-6 rounded-lg transition-colors text-center"
            >
              Contact Us
            </Link>
            <Link
              href="/jobs"
              className="border-2 border-brand-500 text-brand-500 hover:bg-brand-50 font-semibold py-3 px-6 rounded-lg transition-colors text-center"
            >
              Browse All Jobs
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
