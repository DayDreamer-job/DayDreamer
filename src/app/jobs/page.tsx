import { Suspense } from 'react'
import type { Metadata } from 'next'
import JobCard from '@/components/ui/JobCard'
import SearchBar from '@/components/ui/SearchBar'
import CategoryFilter from '@/components/ui/CategoryFilter'
import { getJobs, getJobCount } from '@/lib/supabase'
import { JobFilters, Job } from '@/types'
import { Briefcase, ArrowLeft, ArrowRight } from 'lucide-react'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Browse All Jobs',
  description: 'Browse hundreds of curated job opportunities across tech, design, marketing, and more.',
}

interface JobsPageProps {
  searchParams: {
    search?: string
    category?: string
    work_mode?: string
    job_type?: string
    page?: string
  }
}

const PAGE_SIZE = 12
const PAGINATION_WINDOW = 3 // pages shown on each side of the current page

export default async function JobsPage({ searchParams }: JobsPageProps) {
  const searchParamsResolved = await searchParams
  const page = parseInt(searchParamsResolved.page || '1', 10)
  const offset = (page - 1) * PAGE_SIZE

  const filters: JobFilters = {
    search: searchParamsResolved.search,
    category: searchParamsResolved.category,
    work_mode: searchParamsResolved.work_mode,
    job_type: searchParamsResolved.job_type,
  }

  let jobs: Job[] = []
  let count: number | null = 0
  let totalActiveJobs: number = 0
  try {
    const [result, total] = await Promise.all([
      getJobs(filters, PAGE_SIZE, offset),
      getJobCount()
    ])
    jobs = result.jobs
    count = result.count ?? 0
    totalActiveJobs = total
  } catch (error) {
    console.error('Error fetching jobs:', error)
  }
  const totalPages = Math.ceil((count || 0) / PAGE_SIZE)

  const activeFilterCount = Object.values(filters).filter(Boolean).length

  // Build pagination URL preserving all active filters
  const buildPageUrl = (p: number) => {
    const params = new URLSearchParams()
    if (filters.search) params.set('search', filters.search)
    if (filters.category) params.set('category', filters.category)
    if (filters.work_mode) params.set('work_mode', filters.work_mode)
    if (filters.job_type) params.set('job_type', filters.job_type)
    params.set('page', String(p))
    return `/jobs?${params.toString()}`
  }

  // Build a sliding window of page numbers with ellipsis markers
  const buildPageList = (): (number | 'ellipsis')[] => {
    const pages: (number | 'ellipsis')[] = []

    // Always show first page
    pages.push(1)

    // Left ellipsis — if the window start is more than 1 away from page 1
    if (page - PAGINATION_WINDOW > 2) {
      pages.push('ellipsis')
    }

    // Sliding window around current page (excluding first and last pages)
    for (
      let p = Math.max(2, page - PAGINATION_WINDOW);
      p <= Math.min(totalPages - 1, page + PAGINATION_WINDOW);
      p++
    ) {
      pages.push(p)
    }

    // Right ellipsis — if the window end is more than 1 away from the last page
    if (page + PAGINATION_WINDOW < totalPages - 1) {
      pages.push('ellipsis')
    }

    // Always show last page (if there's more than one page)
    if (totalPages > 1) {
      pages.push(totalPages)
    }

    return pages
  }

  return (
    <>
      <main className="min-h-screen pt-16">
        {/* Header */}
        <div className="bg-cream-warm border-b border-cream-border">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <h1 className="font-display text-3xl md:text-4xl font-bold text-ink mb-2">
              {filters.category && filters.category !== 'All'
                ? `${filters.category} Jobs`
                : filters.search
                ? `Results for "${filters.search}"`
                : 'All Jobs'}
            </h1>
            <p className="text-ink-subtle text-sm mb-6">
              {count || 0} job{count !== 1 ? 's' : ''} found
              {filters.category && filters.category !== 'All' ? ` in ${filters.category}` : ''}
            </p>
            <Suspense>
              <SearchBar />
            </Suspense>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Category filter strip */}
          <div className="mb-6">
            <Suspense>
              <CategoryFilter />
            </Suspense>
          </div>

          {/* Active filter tags */}
          {activeFilterCount > 0 && (
            <div className="flex flex-wrap gap-2 mb-6">
              {Object.entries(filters).map(([key, val]) =>
                val ? (
                  <span
                    key={key}
                    className="inline-flex items-center gap-1.5 bg-ink text-white text-xs font-medium px-3 py-1.5 rounded-full"
                  >
                    {val}
                  </span>
                ) : null
              )}
              <Link href="/jobs" className="text-xs text-ink-subtle hover:text-ink underline self-center">
                Clear all
              </Link>
            </div>
          )}

          {/* Job grid */}
          {jobs.length === 0 ? (
            <div className="card text-center py-24">
              <Briefcase size={40} className="mx-auto mb-4 text-ink-subtle/30" />
              <h3 className="font-display font-bold text-xl text-ink mb-2">No jobs found</h3>
              <p className="text-ink-subtle text-sm mb-6">Try different keywords or filters.</p>
              <Link href="/jobs" className="btn-primary">Clear filters</Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {jobs.map(job => (
                <JobCard key={job.id} job={job} />
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-12">
              {/* Previous button */}
              {page > 1 && (
                <Link href={buildPageUrl(page - 1)} className="btn-secondary px-4 py-2 flex items-center gap-1">
                  <ArrowLeft size={15} /> Previous
                </Link>
              )}

              {/* Page number buttons */}
              <div className="flex gap-1">
                {buildPageList().map((p, i) =>
                  p === 'ellipsis' ? (
                    <span
                      key={`ellipsis-${i}`}
                      className="w-9 h-9 flex items-center justify-center text-sm text-ink-subtle select-none"
                    >
                      …
                    </span>
                  ) : (
                    <Link
                      key={p}
                      href={buildPageUrl(p)}
                      className={`w-9 h-9 flex items-center justify-center rounded-xl text-sm font-medium transition-all ${
                        p === page
                          ? 'bg-ink text-white'
                          : 'bg-white border border-cream-border text-ink-subtle hover:border-ink/40'
                      }`}
                    >
                      {p}
                    </Link>
                  )
                )}
              </div>

              {/* Next button */}
              {page < totalPages && (
                <Link href={buildPageUrl(page + 1)} className="btn-secondary px-4 py-2 flex items-center gap-1">
                  Next <ArrowRight size={15} />
                </Link>
              )}
            </div>
          )}
        </div>
      </main>
    </>
  )
}