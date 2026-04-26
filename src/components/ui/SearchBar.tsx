'use client'

import { useState, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Search, SlidersHorizontal, X } from 'lucide-react'
import { WORK_MODE_OPTIONS, JOB_TYPE_OPTIONS } from '@/lib/utils'

export default function SearchBar() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('search') || '')
  const [showFilters, setShowFilters] = useState(false)
  const [workMode, setWorkMode] = useState(searchParams.get('work_mode') || 'All')
  const [jobType, setJobType] = useState(searchParams.get('job_type') || 'All')

  const applyFilters = useCallback(() => {
    const params = new URLSearchParams()
    if (query) params.set('search', query)
    if (workMode !== 'All') params.set('work_mode', workMode)
    if (jobType !== 'All') params.set('job_type', jobType)
    router.push(`/jobs?${params.toString()}`)
  }, [query, workMode, jobType, router])

  const clearAll = () => {
    setQuery('')
    setWorkMode('All')
    setJobType('All')
    router.push('/jobs')
  }

  return (
    <div className="w-full max-w-3xl mx-auto">
      <div className="flex gap-2">
        {/* Search input */}
        <div className="relative flex-1">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-ink-subtle" />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && applyFilters()}
            placeholder="Search jobs, companies, skills..."
            className="w-full bg-white border border-cream-border rounded-xl pl-10 pr-4 py-3 text-sm text-ink placeholder:text-ink-subtle focus:outline-none focus:border-ink/30 focus:ring-2 focus:ring-ink/5 transition-all"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-subtle hover:text-ink transition-colors"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* Filter toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-3 rounded-xl border text-sm font-medium transition-all ${
            showFilters
              ? 'bg-ink text-white border-ink'
              : 'bg-white border-cream-border text-ink hover:border-ink/40'
          }`}
        >
          <SlidersHorizontal size={15} />
          <span className="hidden sm:inline">Filters</span>
        </button>

        {/* Search button */}
        <button
          onClick={applyFilters}
          className="btn-primary px-5 py-3 rounded-xl"
        >
          Search
        </button>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="mt-3 p-4 bg-white border border-cream-border rounded-xl shadow-sm animate-fade-up">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-ink-subtle uppercase tracking-wide mb-2 block">
                Work Mode
              </label>
              <div className="flex flex-wrap gap-1.5">
                {WORK_MODE_OPTIONS.map(mode => (
                  <button
                    key={mode}
                    onClick={() => setWorkMode(mode)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                      workMode === mode
                        ? 'bg-ink text-white border-ink'
                        : 'bg-cream border-cream-border text-ink-subtle hover:border-ink/40'
                    }`}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold text-ink-subtle uppercase tracking-wide mb-2 block">
                Job Type
              </label>
              <div className="flex flex-wrap gap-1.5">
                {JOB_TYPE_OPTIONS.map(type => (
                  <button
                    key={type}
                    onClick={() => setJobType(type)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                      jobType === type
                        ? 'bg-ink text-white border-ink'
                        : 'bg-cream border-cream-border text-ink-subtle hover:border-ink/40'
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="flex justify-between items-center mt-4 pt-3 border-t border-cream-border">
            <button
              onClick={clearAll}
              className="text-xs text-ink-subtle hover:text-ink transition-colors"
            >
              Clear all filters
            </button>
            <button onClick={applyFilters} className="btn-primary text-xs px-4 py-2">
              Apply Filters
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
