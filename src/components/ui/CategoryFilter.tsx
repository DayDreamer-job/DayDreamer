'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { CATEGORY_ICONS } from '@/lib/utils'

const CATEGORIES = [
  'All',
  'Technology',
  'Design',
  'Marketing',
  'Finance',
  'Sales',
  'HR & Talent',
  'Data & AI',
  'Product',
]

export default function CategoryFilter() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const active = searchParams.get('category') || 'All'

  const handleClick = (cat: string) => {
    const params = new URLSearchParams(searchParams.toString())
    if (cat === 'All') {
      params.delete('category')
    } else {
      params.set('category', cat)
    }
    router.push(`/jobs?${params.toString()}`)
  }

  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
      {CATEGORIES.map(cat => {
        const isActive = active === cat
        const icon = cat === 'All' ? '✨' : CATEGORY_ICONS[cat] || '📁'

        return (
          <button
            key={cat}
            onClick={() => handleClick(cat)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium border whitespace-nowrap transition-all duration-200 ${
              isActive
                ? 'bg-ink text-white border-ink shadow-sm'
                : 'bg-white border-cream-border text-ink-subtle hover:border-ink/40 hover:text-ink'
            }`}
          >
            <span className="text-base leading-none">{icon}</span>
            {cat}
          </button>
        )
      })}
    </div>
  )
}
