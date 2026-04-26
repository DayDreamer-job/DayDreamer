import Link from "next/link";
import { Briefcase, Twitter, Linkedin, Instagram } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-ink text-cream/80 mt-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center">
                <Briefcase size={16} className="text-white" />
              </div>
              <span className="font-display font-bold text-xl text-white">
                Day<span className="text-brand-400">Dreamer</span>
              </span>
            </div>
            <p className="text-sm leading-relaxed text-cream/60 max-w-sm">
              Your daily destination for fresh job opportunities in India.
              Curated jobs for freshers and professionals across all industries.
            </p>
            <div className="flex gap-4 mt-6">
              {[
                { icon: Twitter, href: "#", label: "Twitter" },
                { icon: Linkedin, href: "#", label: "LinkedIn" },
                { icon: Instagram, href: "#", label: "Instagram" },
              ].map(({ icon: Icon, href, label }) => (
                <a
                  key={label}
                  href={href}
                  aria-label={label}
                  className="w-8 h-8 rounded-lg bg-cream/10 flex items-center justify-center hover:bg-brand-500 transition-colors"
                >
                  <Icon size={14} />
                </a>
              ))}
            </div>
          </div>

          {/* Links */}
          <div>
            <h3 className="text-white font-semibold text-sm mb-4">
              Browse Jobs
            </h3>
            <ul className="space-y-2.5">
              {[
                { href: "/jobs?category=Technology", label: "Tech Jobs" },
                { href: "/jobs?category=Design", label: "Design Jobs" },
                { href: "/jobs?category=Marketing", label: "Marketing Jobs" },
                { href: "/jobs?work_mode=Remote", label: "Remote Jobs" },
                { href: "/jobs?job_type=Internship", label: "Internships" },
                { href: "/jobs?experience=Fresher", label: "Fresher Jobs" },
              ].map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-sm text-cream/60 hover:text-cream transition-colors"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-white font-semibold text-sm mb-4">Company</h3>
            <ul className="space-y-2.5">
              {[
                { href: "/about", label: "About Us" },
                { href: "/contact", label: "Contact" },
                { href: "/privacy", label: "Privacy Policy" },
                { href: "/terms", label: "Terms of Use" },
                { href: "/sitemap", label: "Sitemap" },
              ].map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-sm text-cream/60 hover:text-cream transition-colors"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="border-t border-cream/10 mt-12 pt-8 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-xs text-cream/40">
            © {new Date().getFullYear()} DayDreamer. All rights reserved.
          </p>
          <p className="text-xs text-cream/40">
            Jobs updated daily · Made with ❤️ for Indian job seekers
          </p>
        </div>
      </div>
    </footer>
  );
}
