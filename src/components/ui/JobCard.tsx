import Link from 'next/link'
import { MapPin, Clock, IndianRupee, ExternalLink, Star, Zap } from 'lucide-react'
import { Job } from '@/types'
import { timeAgo, getWorkModeBadge, getJobTypeBadge, getInitials } from '@/lib/utils'
import { cn } from '@/lib/utils'

interface JobCardProps {
  job: Job
  featured?: boolean
}

const SOURCE_COLORS: Record<string, string> = {
  LinkedIn: '#0A66C2',
  Naukri: '#FF7555',
  Indeed: '#2164F3',
  Company: '#059669',
  JobFoundIt: '#7c3aed',
}

export default function JobCard({ job, featured = false }: JobCardProps) {
  const workMode = getWorkModeBadge(job.work_mode)
  const jobType = getJobTypeBadge(job.job_type)
  const sourceColor = SOURCE_COLORS[job.apply_source] || '#6b7280'

  return (
    <Link href={`/jobs/${job.id}`} className="block group">
      <article
        className={cn(
          'relative bg-white border rounded-2xl p-5 transition-all duration-300',
          'hover:shadow-xl hover:shadow-ink/6 hover:-translate-y-1 hover:border-ink/20',
          featured
            ? 'border-brand-200 ring-1 ring-brand-100'
            : 'border-cream-border'
        )}
      >
        {/* Featured indicator */}
        {job.is_featured && (
          <div className="absolute -top-2.5 left-4 flex items-center gap-1 bg-brand-500 text-white text-xs font-semibold px-2.5 py-0.5 rounded-full">
            <Star size={10} fill="currentColor" />
            Featured
          </div>
        )}

        {/* Header */}
        <div className="flex items-start gap-3">
          {/* Company Logo / Initial */}
          <div className="flex-shrink-0">
            {job.logo_url ? (
              <img
                src={job.logo_url}
                alt={job.company}
                className="w-11 h-11 rounded-xl object-contain border border-cream-border bg-white p-0.5"
              />
            ) : (
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-ink-soft to-ink flex items-center justify-center text-white font-bold text-sm">
                {getInitials(job.company)}
              </div>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-ink text-sm leading-snug line-clamp-1 group-hover:text-brand-600 transition-colors">
              {job.title}
            </h3>
            <p className="text-ink-subtle text-xs mt-0.5 font-medium">{job.company}</p>
          </div>

          {/* Source badge */}
          <div
            className="flex-shrink-0 text-xs font-semibold px-2 py-0.5 rounded-full text-white"
            style={{ backgroundColor: sourceColor }}
          >
            {job.apply_source}
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-1.5 mt-3">
          <span className={`badge ${workMode.bg}`}>{workMode.text}</span>
          <span className={`badge ${jobType}`}>{job.job_type}</span>
          {job.experience && (
            <span className="badge bg-gray-100 text-gray-700">
              <Zap size={9} className="mr-0.5" />
              {job.experience}
            </span>
          )}
        </div>

        {/* Meta */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-3">
          <div className="flex items-center gap-1 text-xs text-ink-subtle">
            <MapPin size={11} className="flex-shrink-0" />
            <span className="truncate">{job.location}</span>
          </div>
          {job.salary_text && (
            <div className="flex items-center gap-1 text-xs text-ink-subtle">
              <IndianRupee size={11} />
              <span>{job.salary_text}</span>
            </div>
          )}
          <div className="flex items-center gap-1 text-xs text-ink-subtle ml-auto">
            <Clock size={11} />
            <span>{timeAgo(job.posted_at)}</span>
          </div>
        </div>

        {/* Skills preview */}
        {job.skills && job.skills.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3 pt-3 border-t border-cream-border">
            {job.skills.slice(0, 4).map(skill => (
              <span key={skill} className="text-xs px-2 py-0.5 bg-cream rounded-md text-ink-subtle font-mono">
                {skill}
              </span>
            ))}
            {job.skills.length > 4 && (
              <span className="text-xs px-2 py-0.5 text-ink-subtle">
                +{job.skills.length - 4} more
              </span>
            )}
          </div>
        )}

        {/* Apply CTA */}
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-cream-border">
          <span className="text-xs text-ink-subtle">{job.views || 0} views</span>
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-brand-600 group-hover:gap-2 transition-all">
            View & Apply
            <ExternalLink size={11} />
          </span>
        </div>
      </article>
    </Link>
  )
}
