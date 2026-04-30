import { MetadataRoute } from 'next'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const { data: jobs } = await supabase
    .from('jobs')
    .select('id, updated_at')

  const jobUrls = (jobs || []).map((job) => ({
    url: `https://jobs.newsmatrix.in/jobs/${job.id}`,
    lastModified: new Date(job.updated_at || Date.now()),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }))

  return [
    {
      url: 'https://jobs.newsmatrix.in',
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 1.0,
    },
    {
      url: 'https://jobs.newsmatrix.in/jobs',
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 0.9,
    },
    ...jobUrls,
  ]
}