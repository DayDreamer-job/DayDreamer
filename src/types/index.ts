export interface Job {
  id: string
  title: string
  company: string
  logo_url?: string
  location: string
  work_mode: 'Remote' | 'Hybrid' | 'On-site'
  job_type: 'Full-time' | 'Part-time' | 'Contract' | 'Internship'
  experience: string
  salary_min?: number
  salary_max?: number
  salary_text?: string
  description: string
  responsibilities?: string[]
  requirements?: string[]
  skills?: string[]
  apply_url: string
  apply_source: 'Company' | 'Naukri' | 'LinkedIn' | 'Indeed' | 'JobFoundIt'
  category: string
  is_featured: boolean
  is_active: boolean
  posted_at: string
  expires_at?: string
  views: number
  created_at: string
}

export interface Category {
  id: number
  name: string
  slug: string
  icon: string
  color: string
}

export interface JobFilters {
  search?: string
  category?: string
  work_mode?: string
  experience?: string
  job_type?: string
}

export type WorkMode = 'Remote' | 'Hybrid' | 'On-site' | 'All'
export type JobType = 'Full-time' | 'Part-time' | 'Contract' | 'Internship' | 'All'
export type ExperienceLevel = 'Fresher' | '1-3 years' | '3-5 years' | '5+ years' | 'All'
