import { MetadataRoute } from 'next'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

//baseUrl
const BASE_URL = 'https://jobs.newsmatrix.in'

const STATIC_PAGES: MetadataRoute.Sitemap = [
  { url: `${BASE_URL}/`,          lastModified: new Date(), changeFrequency: 'daily',   priority: 1.0 },
  { url: `${BASE_URL}/jobs`,      lastModified: new Date(), changeFrequency: 'daily',   priority: 0.95 },
  { url: `${BASE_URL}/about`,     lastModified: new Date(), changeFrequency: 'monthly', priority: 0.80 },
  { url: `${BASE_URL}/contact`,   lastModified: new Date(), changeFrequency: 'monthly', priority: 0.80 },
  { url: `${BASE_URL}/privacy`,   lastModified: new Date(), changeFrequency: 'yearly',  priority: 0.60 },
  { url: `${BASE_URL}/terms`,     lastModified: new Date(), changeFrequency: 'yearly',  priority: 0.60 },
]

const CATEGORY_PAGES: MetadataRoute.Sitemap = [
  'Technology', 'Design', 'Marketing', 'Finance', 'Sales', 'HR'
].map((cat) => ({
  url: `${BASE_URL}/jobs?category=${encodeURIComponent(cat)}`,
  lastModified: new Date(),
  changeFrequency: 'daily',
  priority: 0.90,
}))

const FILTER_PAGES: MetadataRoute.Sitemap = [
  // Job types
  ...['Full-time', 'Part-time', 'Contract', 'Internship', 'Freelance'].map((t) => ({
    url: `${BASE_URL}/jobs?job_type=${encodeURIComponent(t)}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.85,
  })),
  // Work modes
  ...['Remote', 'On-site', 'Hybrid'].map((m) => ({
    url: `${BASE_URL}/jobs?work_mode=${encodeURIComponent(m)}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.85,
  })),
  // Experience
  ...['Fresher', 'Entry-Level', 'Mid-Level', 'Senior', 'Executive'].map((e) => ({
    url: `${BASE_URL}/jobs?experience=${encodeURIComponent(e)}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.85,
  })),
  // Locations
  ...['Delhi', 'Mumbai', 'Bangalore', 'Hyderabad', 'Pune', 'Chennai', 'Kolkata'].map((l) => ({
    url: `${BASE_URL}/jobs?location=${encodeURIComponent(l)}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.85,
  })),
]

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const { data: jobs } = await supabase
    .from('jobs')
    .select('id, updated_at')

  const jobUrls: MetadataRoute.Sitemap = (jobs || []).map((job) => ({
    url: `${BASE_URL}/jobs/${job.id}`,
    lastModified: new Date(job.updated_at || Date.now()),
    changeFrequency: 'weekly',
    priority: 0.80,
  }))

  return [
    ...STATIC_PAGES,
    ...CATEGORY_PAGES,
    ...FILTER_PAGES,
    ...jobUrls,
  ]
}