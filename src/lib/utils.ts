import { formatDistanceToNow, parseISO } from 'date-fns'

export function timeAgo(dateString: string): string {
  try {
    return formatDistanceToNow(parseISO(dateString), { addSuffix: true })
  } catch {
    return 'Recently'
  }
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .slice(0, 2)
    .map(w => w[0])
    .join('')
    .toUpperCase()
}

export function getSourceColor(source: string): string {
  const map: Record<string, string> = {
    LinkedIn: '#0A66C2',
    Naukri: '#FF7555',
    Indeed: '#2164F3',
    Company: '#10b981',
    JobFoundIt: '#8b5cf6',
  }
  return map[source] || '#6b7280'
}

export function getWorkModeBadge(mode: string) {
  const map: Record<string, { bg: string; text: string }> = {
    Remote: { bg: 'bg-emerald-100 text-emerald-800', text: 'Remote' },
    Hybrid: { bg: 'bg-amber-100 text-amber-800', text: 'Hybrid' },
    'On-site': { bg: 'bg-blue-100 text-blue-800', text: 'On-site' },
  }
  return map[mode] || { bg: 'bg-gray-100 text-gray-700', text: mode }
}

export function getJobTypeBadge(type: string) {
  const map: Record<string, string> = {
    'Full-time': 'bg-brand-100 text-brand-800',
    'Part-time': 'bg-purple-100 text-purple-800',
    'Contract': 'bg-pink-100 text-pink-800',
    'Internship': 'bg-cyan-100 text-cyan-800',
  }
  return map[type] || 'bg-gray-100 text-gray-700'
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim()
}

export function cn(...classes: (string | undefined | false)[]): string {
  return classes.filter(Boolean).join(' ')
}

export const EXPERIENCE_OPTIONS = ['All', 'Fresher', '0-2 years', '2-5 years', '5+ years']
export const WORK_MODE_OPTIONS = ['All', 'Remote', 'Hybrid', 'On-site']
export const JOB_TYPE_OPTIONS = ['All', 'Full-time', 'Part-time', 'Contract', 'Internship']

export const CATEGORY_ICONS: Record<string, string> = {
  Technology: '💻',
  Design: '🎨',
  Marketing: '📣',
  Finance: '💰',
  Sales: '📈',
  'HR & Talent': '👥',
  'Data & AI': '🤖',
  Product: '📦',
}
