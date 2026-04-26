'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Menu, X, Briefcase } from 'lucide-react'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-cream/95 backdrop-blur-md shadow-sm border-b border-cream-border'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 bg-ink rounded-lg flex items-center justify-center group-hover:bg-brand-500 transition-colors">
              <Briefcase size={16} className="text-white" />
            </div>
            <span className="font-display font-bold text-xl text-ink">
              Day<span className="text-brand-500">Dreamer</span>
            </span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-8">
            <Link href="/" className="text-sm font-medium text-ink-subtle hover:text-ink transition-colors">
              Home
            </Link>
            <Link href="/jobs" className="text-sm font-medium text-ink-subtle hover:text-ink transition-colors">
              All Jobs
            </Link>
            <Link href="/jobs?category=Technology" className="text-sm font-medium text-ink-subtle hover:text-ink transition-colors">
              Tech Jobs
            </Link>
            <Link href="/jobs?work_mode=Remote" className="text-sm font-medium text-ink-subtle hover:text-ink transition-colors">
              Remote
            </Link>
            <Link href="/jobs?job_type=Internship" className="text-sm font-medium text-ink-subtle hover:text-ink transition-colors">
              Internships
            </Link>
          </nav>

          {/* CTA */}
          <div className="hidden md:flex items-center gap-3">
            <Link
              href="/jobs"
              className="btn-primary text-xs px-4 py-2"
            >
              Browse Jobs
            </Link>
          </div>

          {/* Mobile menu toggle */}
          <button
            className="md:hidden p-2 rounded-lg hover:bg-cream-warm transition-colors"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle menu"
          >
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Mobile nav */}
        {menuOpen && (
          <div className="md:hidden py-4 border-t border-cream-border bg-cream/95 backdrop-blur-md">
            <nav className="flex flex-col gap-3 pb-4">
              {[
                { href: '/', label: 'Home' },
                { href: '/jobs', label: 'All Jobs' },
                { href: '/jobs?category=Technology', label: 'Tech Jobs' },
                { href: '/jobs?work_mode=Remote', label: 'Remote Jobs' },
                { href: '/jobs?job_type=Internship', label: 'Internships' },
              ].map(item => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="text-sm font-medium text-ink-subtle hover:text-ink px-2 py-1.5 rounded-lg hover:bg-cream-warm transition-all"
                  onClick={() => setMenuOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
              <Link
                href="/jobs"
                className="btn-primary text-sm mt-2"
                onClick={() => setMenuOpen(false)}
              >
                Browse All Jobs
              </Link>
            </nav>
          </div>
        )}
      </div>
    </header>
  )
}
