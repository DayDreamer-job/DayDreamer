import { createClient } from '@supabase/supabase-js'
import { Job, Category, JobFilters } from '@/types'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// ── Fetch jobs with filters ────────────────────────────────────
export async function getJobs(filters?: JobFilters, limit = 20, offset = 0) {
  let query = supabase
    .from('jobs')
    .select('*', { count: 'exact' })
    .eq('is_active', true)
    .order('is_featured', { ascending: false })
    .order('posted_at', { ascending: false })
    .range(offset, offset + limit - 1)

  if (filters?.search) {
    query = query.textSearch('fts', filters.search, { type: 'websearch' })
  }
  if (filters?.category && filters.category !== 'All') {
    query = query.eq('category', filters.category)
  }
  if (filters?.work_mode && filters.work_mode !== 'All') {
    query = query.eq('work_mode', filters.work_mode)
  }
  if (filters?.job_type && filters.job_type !== 'All') {
    query = query.eq('job_type', filters.job_type)
  }

  const { data, error, count } = await query
  if (error) throw error
  return { jobs: data as Job[], count }
}

// ── Fetch single job ──────────────────────────────────────────
export async function getJobById(id: string) {
  const { data, error } = await supabase
    .from('jobs')
    .select('*')
    .eq('id', id)
    .eq('is_active', true)
    .single()

  if (error) throw error
  return data as Job
}

// ── Fetch featured jobs ───────────────────────────────────────
export async function getFeaturedJobs(limit = 6) {
  const { data, error } = await supabase
    .from('jobs')
    .select('*')
    .eq('is_featured', true)
    .eq('is_active', true)
    .order('posted_at', { ascending: false })
    .limit(limit)

  if (error) throw error
  return data as Job[]
}

// ── Fetch job count ───────────────────────────────────────────
export async function getJobCount() {
  const { count, error } = await supabase
    .from('jobs')
    .select('*', { count: 'exact', head: true })
    .eq('is_active', true)

  if (error) return 0
  return count || 0
}

// ── Fetch categories ──────────────────────────────────────────
export async function getCategories() {
  const { data, error } = await supabase
    .from('categories')
    .select('*')
    .order('name')

  if (error) throw error
  return data as Category[]
}

// ── Increment views ───────────────────────────────────────────
export async function incrementJobViews(jobId: string) {
  await supabase.rpc('increment_job_views', { job_id: jobId })
}

// ── Get related jobs ──────────────────────────────────────────
export async function getRelatedJobs(category: string, excludeId: string, limit = 4) {
  const { data, error } = await supabase
    .from('jobs')
    .select('*')
    .eq('category', category)
    .eq('is_active', true)
    .neq('id', excludeId)
    .limit(limit)

  if (error) throw error
  return data as Job[]
}
